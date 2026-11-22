"""Path: tests/test_gen_desk_tools/test_metrics/test_sheets_exporter.py

Unit, regression, integration, and invariant tests for sheets_exporter.

Operational Role:
    Verifies Google Sheets synchronization, URL/key routing, missing-tab
    provisioning, default gspread service-account/OAuth client selection,
    GAP-01 target-not-found diagnostics, GAP-02 auth/permission handling,
    GAP-03 transient retry and partial-sync reporting, GAP-04
    worksheet-lookup error discrimination, RARE-04 50k-char cell truncation,
    empty-tab safety, and 4-tier logging emission.
"""

from __future__ import annotations

import io
import logging
import sys
import types
from pathlib import Path
from typing import Any

import pytest

from gen_desk_tools.metrics.config import load_config
from gen_desk_tools.metrics.exporters import sheets_exporter as sheets_mod
from gen_desk_tools.metrics.exporters.sheets_exporter import sync_to_google_sheets
from gen_desk_tools.metrics.progress import ProgressReporter

__version__ = "1.0.0+build.6"

_SHEETS_LOGGER = "gen_desk_tools.metrics.exporters.sheets_exporter"


class _WorksheetNotFoundError(Exception):
    """Test double matching gspread.exceptions.WorksheetNotFound by class name."""


_WorksheetNotFoundError.__name__ = "WorksheetNotFound"


class _SpreadsheetNotFoundError(Exception):
    """Test double matching gspread.exceptions.SpreadsheetNotFound by class name."""


_SpreadsheetNotFoundError.__name__ = "SpreadsheetNotFound"


class _FakeWorksheet:
    """In-memory worksheet double recording clear and update calls."""

    def __init__(self, title: str, fail_updates: list[Exception] | None = None) -> None:
        self.title = title
        self.cleared = False
        self.rows: list[list[Any]] = []
        self._fail_updates = list(fail_updates or [])
        self.update_attempts = 0

    def clear(self) -> None:
        self.cleared = True

    def update(self, rows: list[list[Any]]) -> None:
        self.update_attempts += 1
        if self._fail_updates:
            raise self._fail_updates.pop(0)
        self.rows = rows


class _FakeSpreadsheet:
    """In-memory spreadsheet double supporting existing and newly created tabs."""

    def __init__(
        self,
        url: str = "https://docs.google.com/spreadsheets/d/test-id/edit",
        existing: dict[str, _FakeWorksheet] | None = None,
        worksheet_error: Exception | None = None,
    ) -> None:
        self.url = url
        self.worksheets: dict[str, _FakeWorksheet] = dict(existing or {})
        self.added_tabs: list[str] = []
        self._worksheet_error = worksheet_error

    def worksheet(self, title: str) -> _FakeWorksheet:
        if self._worksheet_error is not None:
            raise self._worksheet_error
        if title not in self.worksheets:
            raise _WorksheetNotFoundError(title)
        return self.worksheets[title]

    def add_worksheet(self, *, title: str, rows: int, cols: int) -> _FakeWorksheet:
        assert rows >= 1
        assert cols >= 1
        ws = _FakeWorksheet(title)
        self.worksheets[title] = ws
        self.added_tabs.append(title)
        return ws


class _FakeClient:
    """In-memory gspread client double supporting open_by_url and open_by_key."""

    def __init__(
        self,
        spreadsheet: _FakeSpreadsheet | None = None,
        open_error: Exception | None = None,
    ) -> None:
        self.spreadsheet = spreadsheet or _FakeSpreadsheet()
        self.open_error = open_error
        self.opened_by: tuple[str, str] | None = None

    def open_by_url(self, url: str) -> _FakeSpreadsheet:
        self.opened_by = ("url", url)
        if self.open_error is not None:
            raise self.open_error
        return self.spreadsheet

    def open_by_key(self, key: str) -> _FakeSpreadsheet:
        self.opened_by = ("key", key)
        if self.open_error is not None:
            raise self.open_error
        return self.spreadsheet


def _install_fake_gspread(
    monkeypatch: pytest.MonkeyPatch,
    client: _FakeClient,
    calls: list[tuple[str, str]],
) -> None:
    """Register a fake gspread module in sys.modules for testing _default_gspread_client."""
    mod = types.ModuleType("gspread")

    def _service_account(filename: str) -> _FakeClient:
        calls.append(("service_account", filename))
        return client

    def _oauth() -> _FakeClient:
        calls.append(("oauth", ""))
        return client

    mod.service_account = _service_account  # type: ignore[attr-defined]
    mod.oauth = _oauth  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "gspread", mod)


# ==========================================================================
# GROUP 1: Smoke & Primary Entry Points
# Note: End-to-end sync updating existing tabs, creating missing ones, progress.
# ==========================================================================


@pytest.mark.smoke
@pytest.mark.integration
def test_sync_to_google_sheets_updates_existing_and_creates_missing_tabs(
    tmp_path: Path,
) -> None:
    """Verify sync_to_google_sheets clears existing tabs, adds missing tabs, and reports progress."""
    existing_ws = _FakeWorksheet("Master_Scorecard")
    sheet = _FakeSpreadsheet(existing={"Master_Scorecard": existing_ws})
    client = _FakeClient(spreadsheet=sheet)
    cfg = load_config(
        workspace_root=tmp_path,
        env={"GDA_METRICS_SHEET_URL": "https://docs.google.com/spreadsheets/d/abc/edit"},
    )
    payloads: dict[str, list[list[Any]]] = {
        "Master_Scorecard": [["Batch", "Files"], ["B1", 3]],
        "New_Tab": [["Col1"], ["Val1"]],
    }
    buf = io.StringIO()
    reporter = ProgressReporter(total_stages=1, stream=buf)

    resolved_url = sync_to_google_sheets(
        cfg,
        payloads,
        progress=reporter,
        client_factory=lambda _creds: client,
    )

    assert resolved_url == sheet.url
    assert client.opened_by == ("url", "https://docs.google.com/spreadsheets/d/abc/edit")
    assert existing_ws.cleared is True
    assert existing_ws.rows == [["Batch", "Files"], ["B1", 3]]
    assert "New_Tab" in sheet.added_tabs
    assert "Synced tab New_Tab: 2/2 (100%)" in buf.getvalue()


# ==========================================================================
# GROUP 2: Core Logic & Happy Paths
# Note: Public interface exports, open_by_key routing, default gspread client.
# ==========================================================================


@pytest.mark.unit
def test_sheets_exporter_exposes_expected_public_interface() -> None:
    """Verify sheets_exporter exports its expected public symbols."""
    expected = {
        "TAB_NAMES",
        "build_sheet_payloads",
        "sync_to_google_sheets",
    }
    assert expected.issubset(set(sheets_mod.__all__))


@pytest.mark.unit
def test_sync_to_google_sheets_opens_by_key_when_url_unset(tmp_path: Path) -> None:
    """Verify sync_to_google_sheets falls back to open_by_key when only sheet_id is set."""
    client = _FakeClient()
    cfg = load_config(
        workspace_root=tmp_path,
        env={"GDA_METRICS_SHEET_ID": "sheet-key-123"},
    )

    sync_to_google_sheets(
        cfg,
        {"Tab1": [["Header"]]},
        progress=None,
        client_factory=lambda _creds: client,
    )

    assert client.opened_by == ("key", "sheet-key-123")


@pytest.mark.unit
def test_sync_to_google_sheets_uses_default_gspread_service_account_and_oauth(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify _default_gspread_client uses service_account when creds are set and oauth otherwise."""
    client = _FakeClient()
    calls: list[tuple[str, str]] = []
    _install_fake_gspread(monkeypatch, client, calls)

    creds_file = tmp_path / "creds.json"
    creds_file.write_text("{}", encoding="utf-8")

    cfg_sa = load_config(
        workspace_root=tmp_path,
        env={
            "GDA_METRICS_SHEET_URL": "https://docs.google.com/spreadsheets/d/abc/edit",
            "GDA_METRICS_GOOGLE_CREDS": str(creds_file),
        },
    )
    sync_to_google_sheets(cfg_sa, {"Tab1": [["A"]]})

    cfg_oauth = load_config(
        workspace_root=tmp_path,
        env={"GDA_METRICS_SHEET_URL": "https://docs.google.com/spreadsheets/d/abc/edit"},
    )
    sync_to_google_sheets(cfg_oauth, {"Tab1": [["A"]]})

    assert calls == [("service_account", str(creds_file)), ("oauth", "")]


# ==========================================================================
# GROUP 3: Edge Cases & Boundary Conditions
# Note: RARE-04 oversized cell truncation and empty tab payload safety.
# ==========================================================================


@pytest.mark.regression
def test_sync_to_google_sheets_truncates_cells_exceeding_sheets_limit(
    tmp_path: Path,
) -> None:
    """Verify RARE-04: cell values exceeding 50,000 chars are truncated before API update."""
    sheet = _FakeSpreadsheet()
    client = _FakeClient(spreadsheet=sheet)
    cfg = load_config(
        workspace_root=tmp_path,
        env={"GDA_METRICS_SHEET_URL": "https://docs.google.com/spreadsheets/d/abc/edit"},
    )
    oversized = "x" * 60_000

    sync_to_google_sheets(
        cfg,
        {"Raw_Module_Telemetry": [["Missing Lines"], [oversized]]},
        progress=None,
        client_factory=lambda _creds: client,
    )

    written_cell = sheet.worksheets["Raw_Module_Telemetry"].rows[1][0]
    assert isinstance(written_cell, str)
    assert len(written_cell) <= 50_000
    assert written_cell.endswith("...[truncated]")


@pytest.mark.regression
def test_sync_to_google_sheets_handles_empty_tab_rows_without_index_error(
    tmp_path: Path,
) -> None:
    """Verify creating a missing tab with an empty row list does not raise IndexError."""
    sheet = _FakeSpreadsheet()
    client = _FakeClient(spreadsheet=sheet)
    cfg = load_config(
        workspace_root=tmp_path,
        env={"GDA_METRICS_SHEET_URL": "https://docs.google.com/spreadsheets/d/abc/edit"},
    )

    sync_to_google_sheets(
        cfg,
        {"Empty_Tab": []},
        progress=None,
        client_factory=lambda _creds: client,
    )

    assert "Empty_Tab" in sheet.added_tabs


# ==========================================================================
# GROUP 4: Error Handling & Validation Failures
# Note: Missing target, GAP-01 not found, GAP-02 auth/403, GAP-03 retry, GAP-04 lookup.
# ==========================================================================


@pytest.mark.regression
def test_sync_to_google_sheets_requires_sheet_url_or_id(tmp_path: Path) -> None:
    """Verify missing sheet_url and sheet_id raises ValueError immediately."""
    cfg = load_config(workspace_root=tmp_path, env={})

    with pytest.raises(ValueError, match="sheet_url or sheet_id"):
        sync_to_google_sheets(cfg, {"Tab1": [["A"]]})


@pytest.mark.regression
def test_sync_to_google_sheets_reports_spreadsheet_not_found_cleanly(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify GAP-01: SpreadsheetNotFound logs ERROR and raises actionable RuntimeError."""
    client = _FakeClient(open_error=_SpreadsheetNotFoundError("not found"))
    cfg = load_config(
        workspace_root=tmp_path,
        env={"GDA_METRICS_SHEET_URL": "https://docs.google.com/spreadsheets/d/missing/edit"},
    )

    with (
        caplog.at_level(logging.ERROR, logger=_SHEETS_LOGGER),
        pytest.raises(RuntimeError, match="not found"),
    ):
        sync_to_google_sheets(
            cfg,
            {"Tab1": [["A"]]},
            client_factory=lambda _creds: client,
        )

    assert any(r.levelname == "ERROR" for r in caplog.records)


@pytest.mark.regression
def test_sync_to_google_sheets_reports_permission_error_with_guidance(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify GAP-02: PermissionError on auth/open logs ERROR with authorization guidance."""
    cfg = load_config(
        workspace_root=tmp_path,
        env={"GDA_METRICS_SHEET_URL": "https://docs.google.com/spreadsheets/d/private/edit"},
    )

    def _denied_factory(_creds: str) -> Any:
        raise PermissionError("403 Forbidden: insufficient permissions")

    with (
        caplog.at_level(logging.ERROR, logger=_SHEETS_LOGGER),
        pytest.raises(RuntimeError, match="permission|credentials|access"),
    ):
        sync_to_google_sheets(cfg, {"Tab1": [["A"]]}, client_factory=_denied_factory)

    assert any(r.levelname == "ERROR" for r in caplog.records)


@pytest.mark.regression
def test_sync_to_google_sheets_reraises_unexpected_open_error(tmp_path: Path) -> None:
    """Verify non-auth, non-not-found exceptions during open propagate without masking."""
    client = _FakeClient(open_error=ValueError("malformed spreadsheet response"))
    cfg = load_config(
        workspace_root=tmp_path,
        env={"GDA_METRICS_SHEET_URL": "https://docs.google.com/spreadsheets/d/abc/edit"},
    )

    with pytest.raises(ValueError, match="malformed spreadsheet response"):
        sync_to_google_sheets(
            cfg,
            {"Tab1": [["A"]]},
            client_factory=lambda _creds: client,
        )


@pytest.mark.regression
def test_sync_to_google_sheets_retries_transient_timeout_and_succeeds(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify GAP-03: transient TimeoutError during ws.update retries and succeeds."""
    monkeypatch.setattr("time.sleep", lambda _s: None)
    flaky_ws = _FakeWorksheet("Tab1", fail_updates=[TimeoutError("429 rate limit")])
    sheet = _FakeSpreadsheet(existing={"Tab1": flaky_ws})
    client = _FakeClient(spreadsheet=sheet)
    cfg = load_config(
        workspace_root=tmp_path,
        env={"GDA_METRICS_SHEET_URL": "https://docs.google.com/spreadsheets/d/abc/edit"},
    )

    sync_to_google_sheets(
        cfg,
        {"Tab1": [["Header"], ["Row"]]},
        client_factory=lambda _creds: client,
    )

    assert flaky_ws.update_attempts == 2
    assert flaky_ws.rows == [["Header"], ["Row"]]


@pytest.mark.regression
def test_sync_to_google_sheets_reports_partial_sync_after_retry_exhaustion(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify GAP-03: persistent TimeoutError logs ERROR and raises partial-sync RuntimeError."""
    monkeypatch.setattr("time.sleep", lambda _s: None)
    ok_ws = _FakeWorksheet("Tab1")
    dead_ws = _FakeWorksheet(
        "Tab2",
        fail_updates=[TimeoutError("t1"), TimeoutError("t2"), TimeoutError("t3")],
    )
    sheet = _FakeSpreadsheet(existing={"Tab1": ok_ws, "Tab2": dead_ws})
    client = _FakeClient(spreadsheet=sheet)
    cfg = load_config(
        workspace_root=tmp_path,
        env={"GDA_METRICS_SHEET_URL": "https://docs.google.com/spreadsheets/d/abc/edit"},
    )

    with (
        caplog.at_level(logging.ERROR, logger=_SHEETS_LOGGER),
        pytest.raises(RuntimeError, match="Tab2"),
    ):
        sync_to_google_sheets(
            cfg,
            {"Tab1": [["A"]], "Tab2": [["B"]]},
            client_factory=lambda _creds: client,
        )

    assert any(r.levelname == "ERROR" and "Tab2" in r.message for r in caplog.records)


@pytest.mark.regression
def test_sync_to_google_sheets_does_not_mask_permission_error_as_missing_tab(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify GAP-04: PermissionError on .worksheet() surfaces root cause without add_worksheet."""
    sheet = _FakeSpreadsheet(worksheet_error=PermissionError("403 denied on worksheet"))
    client = _FakeClient(spreadsheet=sheet)
    cfg = load_config(
        workspace_root=tmp_path,
        env={"GDA_METRICS_SHEET_URL": "https://docs.google.com/spreadsheets/d/abc/edit"},
    )

    with (
        caplog.at_level(logging.ERROR, logger=_SHEETS_LOGGER),
        pytest.raises(RuntimeError, match="permission|403|denied"),
    ):
        sync_to_google_sheets(
            cfg,
            {"Master_Scorecard": [["A"]]},
            client_factory=lambda _creds: client,
        )

    assert sheet.added_tabs == []
    assert any(r.levelname == "ERROR" for r in caplog.records)


# ==========================================================================
# GROUP 5: Filesystem, CLI & Integration
# Note: 4-tier logging emission (INFO, VERBOSE, DEBUG) via caplog.
# ==========================================================================


@pytest.mark.integration
def test_sync_to_google_sheets_emits_info_verbose_and_debug_log_records(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify sync_to_google_sheets emits INFO, VERBOSE, and DEBUG log records."""
    client = _FakeClient()
    cfg = load_config(
        workspace_root=tmp_path,
        env={"GDA_METRICS_SHEET_URL": "https://docs.google.com/spreadsheets/d/abc/edit"},
    )

    with caplog.at_level(logging.DEBUG, logger=_SHEETS_LOGGER):
        sync_to_google_sheets(
            cfg,
            {"Tab1": [["Header"], ["Row"]]},
            client_factory=lambda _creds: client,
        )

    levels = {record.levelname for record in caplog.records}
    assert {"INFO", "VERBOSE", "DEBUG"}.issubset(levels)
