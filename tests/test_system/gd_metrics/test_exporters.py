"""Path: tests/test_system/gd_metrics/test_exporters.py

Unit and integration tests for system.gd_metrics.exporters.
"""

from __future__ import annotations

import importlib
import io
import json
from pathlib import Path
from typing import Any

import pytest

from system.gd_metrics.collectors.coverage_collector import FileCoverageMetrics
from system.gd_metrics.collectors.hygiene_collector import ModuleHygieneRecord
from system.gd_metrics.collectors.import_collector import ImportEdgeRecord
from system.gd_metrics.collectors.mypy_collector import MypyDiagnostic
from system.gd_metrics.collectors.pytest_analyzer import (
    ConftestFixtureRecord,
    FileMarkerSummary,
    PytestSuiteAnalysis,
)
from system.gd_metrics.collectors.radon_collector import (
    BatchRadonRollup,
    ComplexityHotspot,
    FileRadonMetrics,
)
from system.gd_metrics.collectors.ruff_collector import RuffDiagnostic
from system.gd_metrics.config import load_config
from system.gd_metrics.exporters.report_exporter import write_local_json_report
from system.gd_metrics.exporters.sheets_exporter import (
    TAB_NAMES,
    _default_gspread_client,
    build_sheet_payloads,
    sync_to_google_sheets,
)
from system.gd_metrics.progress import ProgressReporter

__version__ = "1.0.0+build.6"


class _FakeWorksheet:
    """In-memory worksheet double for hermetic Google Sheets tests."""

    def __init__(self, title: str) -> None:
        self.title = title
        self.cleared = False
        self.rows: list[list[Any]] = []

    def clear(self) -> None:
        self.cleared = True

    def update(self, rows: list[list[Any]]) -> None:
        self.rows = rows


class _FakeSpreadsheet:
    """In-memory spreadsheet double supporting existing and newly added tabs."""

    def __init__(self, url: str, existing: list[str] | None = None) -> None:
        self.url = url
        self.sheets: dict[str, _FakeWorksheet] = {
            name: _FakeWorksheet(name) for name in (existing or [])
        }

    def worksheet(self, name: str) -> _FakeWorksheet:
        if name not in self.sheets:
            raise KeyError(name)
        return self.sheets[name]

    def add_worksheet(self, title: str, rows: int, cols: int) -> _FakeWorksheet:
        ws = _FakeWorksheet(title)
        self.sheets[title] = ws
        return ws


class _FakeClient:
    """In-memory gspread client double."""

    def __init__(self, spreadsheet: _FakeSpreadsheet) -> None:
        self.spreadsheet = spreadsheet
        self.opened_by: str = ""

    def open_by_url(self, url: str) -> _FakeSpreadsheet:
        self.opened_by = f"url:{url}"
        return self.spreadsheet

    def open_by_key(self, key: str) -> _FakeSpreadsheet:
        self.opened_by = f"key:{key}"
        return self.spreadsheet


def _sample_payloads() -> dict[str, list[list[Any]]]:
    """Build representative telemetry payloads covering all 9 tabs and rollup states."""
    rollups = (
        BatchRadonRollup("B1", "gda", "T0", 2, 100, 50, 70, 10, 5, 10, 21.4, 3.5, 1, 1),
        BatchRadonRollup("B2", "cli", "T1", 1, 10, 5, 8, 1, 0, 1, 12.5, 1.0, 0, 0),
        BatchRadonRollup("B3", "ancestry_desk", "UI", 0, 0, 0, 0, 0, 0, 0, 0.0, 0.0, 0, 0),
    )
    hotspot = ComplexityHotspot("B1", "src/a.py", 12, "F", "heavy", 15, "C")
    file_metrics = (
        FileRadonMetrics(
            "B1",
            "src/a.py",
            80,
            40,
            60,
            8,
            4,
            8,
            20.0,
            15.0,
            "B",
            5.0,
            15,
            "C",
            "F heavy:12",
            1,
            (hotspot,),
        ),
        FileRadonMetrics(
            "B1",
            "src/b.py",
            20,
            10,
            10,
            2,
            1,
            2,
            30.0,
            80.0,
            "A",
            2.0,
            2,
            "A",
            "F ok:1",
            0,
            (),
        ),
        FileRadonMetrics(
            "B2",
            "src/c.py",
            10,
            5,
            8,
            1,
            0,
            1,
            12.5,
            90.0,
            "A",
            1.0,
            1,
            "A",
            "F simple:1",
            0,
            (),
        ),
    )
    cov_map = {
        "src/a.py": FileCoverageMetrics("src/a.py", 10, 9, "12", 4, 3, 90.0, 75.0, 85.7),
        "src/c.py": FileCoverageMetrics("src/c.py", 5, 5, "-", 0, 0, 100.0, 100.0, 100.0),
    }
    suite = PytestSuiteAnalysis(
        fixtures=(
            ConftestFixtureRecord(
                "tests/conftest.py",
                "tests",
                "db",
                4,
                "session",
                False,
                True,
                2,
                1,
                False,
                True,
                ("tests/sub/conftest.py",),
            ),
        ),
        marker_summaries=(
            FileMarkerSummary("B1", "tests/test_a.py", 3, 0, 2, 0, 0, 0, 3, (), True, ""),
        ),
        total_test_files=1,
        total_test_functions=3,
        total_unmarked_tests=0,
        total_unused_fixtures=0,
    )
    mypy_diags = (
        MypyDiagnostic("B1", "src/a.py", 10, "error", "assignment", "Bad type"),
        MypyDiagnostic("B1", "src/a.py", 11, "note", "", "Context"),
    )
    ruff_diags = (RuffDiagnostic("B1", "src/a.py", 10, 1, "E501", "Line too long", True),)
    hygiene = (
        ModuleHygieneRecord(
            "B1",
            "src/a.py",
            True,
            "1.0.0+build.1",
            True,
            True,
            True,
            True,
            True,
            ("NOT_IN_README",),
        ),
    )
    imports = (
        ImportEdgeRecord("B1", "gda.core.a", "gda.io.b", "gda.core", "gda.io", True, "Violation"),
    )
    return build_sheet_payloads(
        rollups,
        file_metrics,
        cov_map,
        suite,
        mypy_diagnostics=mypy_diags,
        ruff_diagnostics=ruff_diags,
        hygiene_records=hygiene,
        import_edges=imports,
    )


# ==========================================================================
# GROUP 1: Payload Construction & Local JSON Export
# Note: Verifies all 9 tab matrices, TOTAL row, N/A coverage, and JSON export.
# ==========================================================================


@pytest.mark.unit
def test_build_sheet_payloads_populates_all_nine_tabs_and_total_row() -> None:
    """Verify build_sheet_payloads creates all 9 tabs, N/A empty coverage, and TOTAL row."""
    payloads = _sample_payloads()

    assert tuple(payloads.keys()) == TAB_NAMES
    assert len(payloads["Master_Scorecard"]) == 5
    assert payloads["Master_Scorecard"][2][15] == "N/A"
    assert payloads["Master_Scorecard"][3][14] == "N/A"
    assert payloads["Master_Scorecard"][-1][0] == "TOTAL / WORKSPACE"
    assert len(payloads["Raw_Module_Telemetry"]) == 4
    assert len(payloads["CC_MI_Hotspots"]) == 3
    assert len(payloads["Test_Markers_Summary"]) == 2
    assert len(payloads["Conftest_Fixture_Map"]) == 2
    assert payloads["Conftest_Fixture_Map"][1][-1] == "tests/sub/conftest.py"
    assert len(payloads["Mypy_Diagnostics"]) == 3
    assert len(payloads["Ruff_Diagnostics"]) == 2
    assert len(payloads["Module_Hygiene_Audit"]) == 2
    assert len(payloads["Import_Dependency_Graph"]) == 2


@pytest.mark.integration
def test_write_local_json_report_writes_valid_utf8_json(tmp_path: Path) -> None:
    """Verify write_local_json_report creates reports/gd_metrics_report.json."""
    cfg = load_config(workspace_root=tmp_path, env={})
    payloads = _sample_payloads()

    out_path = write_local_json_report(cfg, payloads)

    data = json.loads(out_path.read_text(encoding="utf-8"))
    assert out_path.name == "gd_metrics_report.json"
    assert set(data["tabs"].keys()) == set(TAB_NAMES)


# ==========================================================================
# GROUP 2: Direct Google Sheets Sync & Client Factory
# Note: Verifies URL/key opening, tab creation/clearing, and error guards.
# ==========================================================================


@pytest.mark.regression
def test_sync_to_google_sheets_missing_target_raises_value_error(tmp_path: Path) -> None:
    """Verify sync_to_google_sheets raises ValueError when no sheet URL/ID is configured."""
    cfg = load_config(workspace_root=tmp_path, env={})

    with pytest.raises(ValueError, match="requires sheet_url or sheet_id"):
        sync_to_google_sheets(cfg, _sample_payloads())


@pytest.mark.smoke
@pytest.mark.integration
def test_sync_to_google_sheets_opens_by_url_and_syncs_tabs(tmp_path: Path) -> None:
    """Verify sync_to_google_sheets updates existing tabs and creates missing ones."""
    cfg = load_config(
        workspace_root=tmp_path,
        env={"GDA_METRICS_SHEET_URL": "https://docs.google.com/spreadsheets/d/demo"},
    )
    sheet = _FakeSpreadsheet(cfg.sheet_url, existing=["Master_Scorecard"])
    client = _FakeClient(sheet)
    buf = io.StringIO()
    reporter = ProgressReporter(total_stages=1, stream=buf)

    url = sync_to_google_sheets(
        cfg,
        _sample_payloads(),
        progress=reporter,
        client_factory=lambda _creds: client,
    )

    assert url == cfg.sheet_url
    assert client.opened_by == f"url:{cfg.sheet_url}"
    assert sheet.sheets["Master_Scorecard"].cleared is True
    assert set(sheet.sheets.keys()) == set(TAB_NAMES)
    assert "Synced tab Import_Dependency_Graph: 9/9 (100%)" in buf.getvalue()


@pytest.mark.unit
def test_sync_to_google_sheets_opens_by_key_without_progress(tmp_path: Path) -> None:
    """Verify sync_to_google_sheets falls back to open_by_key when only sheet_id is set."""
    cfg = load_config(workspace_root=tmp_path, env={"GDA_METRICS_SHEET_ID": "sheet_123"})
    sheet = _FakeSpreadsheet("https://sheets.local/sheet_123")
    client = _FakeClient(sheet)

    url = sync_to_google_sheets(
        cfg,
        _sample_payloads(),
        progress=None,
        client_factory=lambda _creds: client,
    )

    assert url == "https://sheets.local/sheet_123"
    assert client.opened_by == "key:sheet_123"


@pytest.mark.unit
def test_default_gspread_client_dispatches_service_account_and_oauth(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify _default_gspread_client selects service_account or oauth based on creds path."""
    calls: list[str] = []

    class _FakeGspreadModule:
        @staticmethod
        def service_account(filename: str) -> str:
            calls.append(f"sa:{filename}")
            return "sa_client"

        @staticmethod
        def oauth() -> str:
            calls.append("oauth")
            return "oauth_client"

    monkeypatch.setattr(importlib, "import_module", lambda _name: _FakeGspreadModule)

    assert _default_gspread_client("/creds.json") == "sa_client"
    assert _default_gspread_client("") == "oauth_client"
    assert calls == ["sa:/creds.json", "oauth"]
