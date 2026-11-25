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

__version__ = "1.0.0+build.7"

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
def test_sync_to_google_sheets_updates_existing_and_creates_missing_tabs(tmp_path: Path) -> None:
    """Verify sync_to_google_sheets clears existing tabs, adds missing ones, and reports."""
    cfg = load_config(
        workspace_root=tmp_path,
        env={"GDA_METRICS_SHEET_URL": "https://docs.google.com/spreadsheets/d/test-id/edit"},
    )
    existing_ws = _FakeWorksheet("Master_Scorecard")
    sheet = _FakeSpreadsheet(existing={"Master_Scorecard": existing_ws})
    client = _FakeClient(spreadsheet=sheet)
    buf = io.StringIO()
    reporter = ProgressReporter(total_stages=1, stream=buf)
    payloads = {
        "Master_Scorecard": [["Batch", "Score"], ["B1", 100]],
        "Raw_Module_Telemetry": [["File", "LOC"], ["src/a.py", 12]],
    }

    url = sync_to_google_sheets(
        cfg,
        payloads,
        progress=reporter,
        client_factory=lambda _creds: client,
    )

    assert url == sheet.url
    assert client.opened_by == ("url", cfg.sheet_url)
    assert existing_ws.cleared is True
    assert existing_ws.rows == [["Batch", "Score"], ["B1", 100]]
    assert sheet.added_tabs == ["Raw_Module_Telemetry"]
    assert "Synced tab Raw_Module_Telemetry: 2/2 (100%)" in buf.getvalue()


# ==========================================================================
# GROUP 2: Core Logic & Happy Paths
# Note: Public interface exports, open_by_key fallback, and default gspread client.
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
def test_sync_to_google_sheets_opens_by_key_without_progress(tmp_path: Path) -> None:
    """Verify sync_to_google_sheets uses open_by_key when only sheet_id is provided."""
    cfg = load_config(workspace_root=tmp_path, env={"GDA_METRICS_SHEET_ID": "sheet_key_123"})
    sheet = _FakeSpreadsheet(url="https://docs.google.com/spreadsheets/d/sheet_key_123/edit")
    client = _FakeClient(spreadsheet=sheet)

    url = sync_to_google_sheets(
        cfg,
        {"Empty_Tab": []},
        progress=None,
        client_factory=lambda _creds: client,
    )

    assert url == sheet.url
    assert client.opened_by == ("key", "sheet_key_123")
    assert sheet.added_tabs == ["Empty_Tab"]


@pytest.mark.unit
def test_sync_to_google_sheets_uses_default_gspread_client_for_service_account_and_oauth(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify default client factory selects service_account or oauth based on creds path."""
    calls: list[tuple[str, str]] = []
    client = _FakeClient()
    _install_fake_gspread(monkeypatch, client, calls)

    cfg_sa = load_config(
        workspace_root=tmp_path,
        env={
            "GDA_METRICS_SHEET_ID": "key_sa",
            "GDA_METRICS_GOOGLE_CREDS": "/creds/sa.json",
        },
    )
    sync_to_google_sheets(cfg_sa, {"Tab1": [["A"]]})

    cfg_oauth = load_config(workspace_root=tmp_path, env={"GDA_METRICS_SHEET_ID": "key_oauth"})
    sync_to_google_sheets(cfg_oauth, {"Tab1": [["A"]]})

    assert calls == [("service_account", "/creds/sa.json"), ("oauth", "")]


# ==========================================================================
# GROUP 3: Edge Cases & Boundary Conditions
# Note: RARE-04 50,000-character cell truncation and untyped exception passthrough.
# ==========================================================================


@pytest.mark.regression
def test_sync_to_google_sheets_truncates_cells_exceeding_50k_chars(tmp_path: Path) -> None:
    """Verify RARE-04: cell strings exceeding 50,000 chars are truncated cleanly."""
    cfg = load_config(workspace_root=tmp_path, env={"GDA_METRICS_SHEET_ID": "key_big"})
    sheet = _FakeSpreadsheet()
    client = _FakeClient(spreadsheet=sheet)
    huge_text = "x" * 60_000

    sync_to_google_sheets(
        cfg,
        {"Tab1": [[huge_text, 42]]},
        client_factory=lambda _creds: client,
    )

    written_cell = sheet.worksheets["Tab1"].rows[0][0]
    assert len(written_cell) == 50_000
    assert written_cell.endswith("...[truncated]")
    assert sheet.worksheets["Tab1"].rows[0][1] == 42


# ==========================================================================
# GROUP 4: Error Handling & Validation Failures
# Note: GAP-01 missing sheet, GAP-02 auth/permission, GAP-03 retry, GAP-04 lookup.
# ==========================================================================


@pytest.mark.regression
def test_sync_to_google_sheets_requires_target_url_or_id(tmp_path: Path) -> None:
    """Verify missing sheet_url and sheet_id raises ValueError before opening client."""
    cfg = load_config(workspace_root=tmp_path, env={})

    with pytest.raises(ValueError, match="requires sheet_url or sheet_id"):
        sync_to_google_sheets(cfg, {"Tab1": [["A"]]})


@pytest.mark.regression
def test_sync_to_google_sheets_reports_target_not_found_for_missing_spreadsheet(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify GAP-01: SpreadsheetNotFound logs ERROR and raises actionable RuntimeError."""
    cfg = load_config(workspace_root=tmp_path, env={"GDA_METRICS_SHEET_ID": "missing_id"})
    client = _FakeClient(open_error=_SpreadsheetNotFoundError("not found"))

    with (
        caplog.at_level(logging.ERROR, logger=_SHEETS_LOGGER),
        pytest.raises(RuntimeError, match="Target Google Sheet not found: missing_id"),
    ):
        sync_to_google_sheets(cfg, {"Tab1": [["A"]]}, client_factory=lambda _creds: client)

    assert any(r.levelname == "ERROR" for r in caplog.records)


@pytest.mark.regression
@pytest.mark.parametrize(
    ("open_exc", "expected_suffix"),
    [
        (FileNotFoundError("creds missing"), " (creds missing)"),
        (PermissionError("403 Forbidden"), " (403 Forbidden)"),
        (PermissionError(), ""),
    ],
)
def test_sync_to_google_sheets_reports_auth_and_permission_failures(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
    open_exc: Exception,
    expected_suffix: str,
) -> None:
    """Verify GAP-02: missing creds or 403/PermissionError logs ERROR without empty ()."""
    cfg = load_config(workspace_root=tmp_path, env={"GDA_METRICS_SHEET_ID": "denied_id"})
    client = _FakeClient(open_error=open_exc)

    with (
        caplog.at_level(logging.ERROR, logger=_SHEETS_LOGGER),
        pytest.raises(
            RuntimeError,
            match="Google Sheets authorization failed for denied_id",
        ) as exc_info,
    ):
        sync_to_google_sheets(cfg, {"Tab1": [["A"]]}, client_factory=lambda _creds: client)

    err_msg = str(exc_info.value)
    assert err_msg.endswith(f"verify credentials and edit permissions{expected_suffix}")
    assert "()" not in err_msg
    assert any(r.levelname == "ERROR" for r in caplog.records)


@pytest.mark.regression
def test_sync_to_google_sheets_extracts_cause_detail_when_permission_error_is_empty(
    tmp_path: Path,
) -> None:
    """Verify chained APIError cause detail is surfaced when PermissionError message is empty."""
    cfg = load_config(workspace_root=tmp_path, env={"GDA_METRICS_SHEET_ID": "denied_id"})
    chained_exc = PermissionError()
    chained_exc.__cause__ = RuntimeError("APIError: [403]: The caller does not have permission")
    client = _FakeClient(open_error=chained_exc)

    with pytest.raises(
        RuntimeError,
        match=r"verify credentials and edit permissions \(APIError: \[403\]: The caller does not have permission\)",
    ):
        sync_to_google_sheets(cfg, {"Tab1": [["A"]]}, client_factory=lambda _creds: client)


@pytest.mark.regression
def test_sync_to_google_sheets_surfaces_non_missing_worksheet_errors(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify GAP-04: real API/permission errors on .worksheet() are not masked as missing tabs."""
    cfg = load_config(workspace_root=tmp_path, env={"GDA_METRICS_SHEET_ID": "key_err"})
    sheet = _FakeSpreadsheet(worksheet_error=PermissionError("403 APIError"))
    client = _FakeClient(spreadsheet=sheet)

    with (
        caplog.at_level(logging.ERROR, logger=_SHEETS_LOGGER),
        pytest.raises(RuntimeError, match="Failed to access worksheet 'Tab1'"),
    ):
        sync_to_google_sheets(cfg, {"Tab1": [["A"]]}, client_factory=lambda _creds: client)

    assert sheet.added_tabs == []


@pytest.mark.regression
def test_sync_to_google_sheets_retries_transient_update_errors_and_reports_partial_sync(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify GAP-03: transient update errors retry and persistent failure reports partial sync."""
    monkeypatch.setattr("time.sleep", lambda _s: None)
    cfg = load_config(workspace_root=tmp_path, env={"GDA_METRICS_SHEET_ID": "key_retry"})
    ws1 = _FakeWorksheet("Tab1", fail_updates=[TimeoutError("transient timeout")])
    ws2 = _FakeWorksheet(
        "Tab2",
        fail_updates=[
            ConnectionError("drop 1"),
            ConnectionError("drop 2"),
            ConnectionError("drop 3"),
        ],
    )
    sheet = _FakeSpreadsheet(existing={"Tab1": ws1, "Tab2": ws2})
    client = _FakeClient(spreadsheet=sheet)

    with (
        caplog.at_level(logging.DEBUG, logger=_SHEETS_LOGGER),
        pytest.raises(
            RuntimeError,
            match="Partial Google Sheets sync failure on tab 'Tab2' after 3 attempts \\(1/2 tabs synced\\)",
        ),
    ):
        sync_to_google_sheets(
            cfg,
            {"Tab1": [["ok"]], "Tab2": [["fail"]]},
            client_factory=lambda _creds: client,
        )

    assert ws1.update_attempts == 2
    assert ws2.update_attempts == 3
    assert any(r.levelname == "ERROR" for r in caplog.records)


@pytest.mark.regression
def test_sync_to_google_sheets_propagates_unexpected_open_exceptions(tmp_path: Path) -> None:
    """Verify non-auth/non-not-found client errors propagate directly."""
    cfg = load_config(workspace_root=tmp_path, env={"GDA_METRICS_SHEET_ID": "key_boom"})
    client = _FakeClient(open_error=ValueError("unexpected client state"))

    with pytest.raises(ValueError, match="unexpected client state"):
        sync_to_google_sheets(cfg, {"Tab1": [["A"]]}, client_factory=lambda _creds: client)


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
    cfg = load_config(workspace_root=tmp_path, env={"GDA_METRICS_SHEET_ID": "key_logs"})
    client = _FakeClient()

    with caplog.at_level(logging.DEBUG, logger=_SHEETS_LOGGER):
        sync_to_google_sheets(cfg, {"Tab1": [["A"]]}, client_factory=lambda _creds: client)

    levels = {record.levelname for record in caplog.records}
    assert {"INFO", "VERBOSE", "DEBUG"}.issubset(levels)
