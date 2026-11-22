"""Path: tests/test_gen_desk_tools/test_metrics/conftest.py

Shared pytest fixtures and lightweight test doubles for gd_metrics suites.

Operational Role:
    Provides isolated workspace sandboxes, batch builders, in-memory Google
    Sheets doubles, and canonical 9-tab telemetry payloads reused across
    group-partitioned test modules under tests/test_gen_desk_tools/test_metrics/.

Classes:
    FakeWorksheet: In-memory worksheet double tracking clear() and update() calls.
    FakeSpreadsheet: In-memory spreadsheet double supporting existing and added tabs.
    FakeGspreadClient: In-memory gspread client double recording open calls.

Functions:
    make_batch: Construct a BatchDefinition with concise defaults for tests.
    build_sample_payloads: Assemble representative 9-tab telemetry matrices.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any

import pytest

from gen_desk_tools.metrics.collectors.coverage_collector import FileCoverageMetrics
from gen_desk_tools.metrics.collectors.hygiene_collector import ModuleHygieneRecord
from gen_desk_tools.metrics.collectors.import_collector import ImportEdgeRecord
from gen_desk_tools.metrics.collectors.mypy_collector import MypyDiagnostic
from gen_desk_tools.metrics.collectors.pytest_analyzer import (
    ConftestFixtureRecord,
    FileMarkerSummary,
    PytestSuiteAnalysis,
)
from gen_desk_tools.metrics.collectors.radon_collector import (
    BatchRadonRollup,
    ComplexityHotspot,
    FileRadonMetrics,
)
from gen_desk_tools.metrics.collectors.ruff_collector import RuffDiagnostic
from gen_desk_tools.metrics.config import BatchDefinition
from gen_desk_tools.metrics.exporters.payload_builders import build_sheet_payloads
from gen_desk_tools.metrics.progress import ProgressReporter

__version__ = "1.0.0+build.1"

__all__ = [
    "FakeGspreadClient",
    "FakeSpreadsheet",
    "FakeWorksheet",
    "build_sample_payloads",
    "make_batch",
    "metrics_workspace",
    "progress_buffer",
    "sample_payloads",
]


class FakeWorksheet:
    """In-memory worksheet double tracking clear and row update calls."""

    def __init__(self, title: str) -> None:
        self.title = title
        self.cleared = False
        self.rows: list[list[Any]] = []

    def clear(self) -> None:
        """Record that worksheet contents were cleared."""
        self.cleared = True

    def update(self, rows: list[list[Any]]) -> None:
        """Store written 2D row payload."""
        self.rows = rows


class FakeSpreadsheet:
    """In-memory spreadsheet double supporting existing and newly added tabs."""

    def __init__(self, url: str, existing: list[str] | None = None) -> None:
        self.url = url
        self.sheets: dict[str, FakeWorksheet] = {
            name: FakeWorksheet(name) for name in (existing or [])
        }

    def worksheet(self, name: str) -> FakeWorksheet:
        """Return an existing worksheet by title or raise KeyError."""
        if name not in self.sheets:
            raise KeyError(name)
        return self.sheets[name]

    def add_worksheet(self, title: str, rows: int, cols: int) -> FakeWorksheet:
        """Provision and register a new worksheet tab."""
        del rows, cols
        ws = FakeWorksheet(title)
        self.sheets[title] = ws
        return ws


class FakeGspreadClient:
    """In-memory gspread client double recording spreadsheet open requests."""

    def __init__(self, spreadsheet: FakeSpreadsheet) -> None:
        self.spreadsheet = spreadsheet
        self.opened_by: str = ""

    def open_by_url(self, url: str) -> FakeSpreadsheet:
        """Record URL open call and return the configured fake spreadsheet."""
        self.opened_by = f"url:{url}"
        return self.spreadsheet

    def open_by_key(self, key: str) -> FakeSpreadsheet:
        """Record key open call and return the configured fake spreadsheet."""
        self.opened_by = f"key:{key}"
        return self.spreadsheet


def make_batch(
    batch_id: str = "GDA-Batch-1",
    scope: str = "gda",
    tier: str = "Tier 0",
    paths: tuple[str, ...] = ("src/gda/core",),
    test_paths: tuple[str, ...] = ("tests/test_gda/test_core",),
) -> BatchDefinition:
    """Construct a BatchDefinition with concise defaults for test suites."""
    return BatchDefinition(
        id=batch_id,
        scope=scope,
        tier=tier,
        paths=paths,
        test_paths=test_paths,
    )


def build_sample_payloads() -> dict[str, list[list[Any]]]:
    """Assemble representative 9-tab telemetry matrices covering populated and empty batches."""
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


@pytest.fixture
def metrics_workspace(tmp_path: Path) -> Path:
    """Create an isolated temporary workspace with src/gen_desk_tools/ and tests/ directories."""
    (tmp_path / "src" / "gen_desk_tools").mkdir(parents=True)
    (tmp_path / "tests").mkdir(parents=True)
    return tmp_path


@pytest.fixture
def progress_buffer() -> tuple[io.StringIO, ProgressReporter]:
    """Return an in-memory StringIO stream paired with a verbose ProgressReporter."""
    stream = io.StringIO()
    reporter = ProgressReporter(total_stages=1, verbose=True, stream=stream)
    return stream, reporter


@pytest.fixture
def sample_payloads() -> dict[str, list[list[Any]]]:
    """Return canonical 9-tab telemetry matrices for exporter and payload tests."""
    return build_sample_payloads()
