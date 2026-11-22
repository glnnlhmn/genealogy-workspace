"""Path: tests/test_gen_desk_tools/test_metrics/test_cli.py

Unit and integration tests for gen_desk_tools.metrics.cli and __main__.
"""

from __future__ import annotations

import importlib
import runpy
import sys
from pathlib import Path
from typing import Any

import pytest

from gen_desk_tools.metrics.cli import main

__version__ = "1.0.0+build.4"


class _DummyWorksheet:
    """Minimal worksheet double for CLI end-to-end sync tests."""

    def clear(self) -> None:
        return None

    def update(self, _rows: list[list[Any]]) -> None:
        return None


class _DummySpreadsheet:
    """Minimal spreadsheet double for CLI end-to-end sync tests."""

    url = "https://sheets.local/cli"

    def worksheet(self, _name: str) -> _DummyWorksheet:
        return _DummyWorksheet()


class _DummyClient:
    """Minimal gspread client double for CLI end-to-end sync tests."""

    def open_by_url(self, _url: str) -> _DummySpreadsheet:
        return _DummySpreadsheet()


# ==========================================================================
# GROUP 1: CLI End-to-End Execution & Flags
# Note: Verifies offline mode, skip flags, Google Sheets sync, and __main__.
# ==========================================================================


@pytest.mark.smoke
@pytest.mark.integration
def test_cli_main_runs_full_pipeline_with_sheets_and_skip_flags(tmp_path: Path) -> None:
    """Verify main() executes all 7 stages with mocked Sheets sync and skip flags."""
    (tmp_path / "src" / "gda" / "core").mkdir(parents=True)
    (tmp_path / "src" / "gda" / "core" / "mod.py").write_text("x = 1\n", encoding="utf-8")
    cfg_dir = tmp_path / "src" / "gen_desk_tools" / "metrics"
    cfg_dir.mkdir(parents=True)
    (cfg_dir / "metrics.toml").write_text(
        '[telemetry]\ndefault_scopes = ["gda"]\nsync_sheets_by_default = true\n'
        '[[batches]]\nid = "GDA-Batch-1"\nscope = "gda"\ntier = "T0"\n'
        'paths = ["src/gda/core"]\ntest_paths = ["tests/test_gda/test_core"]\n',
        encoding="utf-8",
    )

    exit_code = main(
        [
            "--root",
            str(tmp_path),
            "--scope",
            "gda",
            "--batch",
            "GDA-Batch-1",
            "--sheet-url",
            "https://sheets.local/cli",
            "--no-pytest",
            "--no-mypy",
            "--no-ruff",
            "-v",
        ],
        client_factory=lambda _creds: _DummyClient(),
    )

    assert exit_code == 0
    assert (tmp_path / "reports" / "gd_metrics_report.json").exists()


@pytest.mark.integration
def test_cli_main_runs_with_all_collectors_and_no_sheets_no_local_report(tmp_path: Path) -> None:
    """Verify main() executes pytest, mypy, and ruff stages when skip flags are omitted."""
    cfg_file = tmp_path / "custom.toml"
    cfg_file.write_text(
        "[telemetry]\nwrite_local_report = false\nsync_sheets_by_default = false\n",
        encoding="utf-8",
    )

    exit_code = main(
        [
            "--root",
            str(tmp_path),
            "--config",
            str(cfg_file),
            "--no-sheets",
        ]
    )

    assert exit_code == 0
    assert not (tmp_path / "reports" / "gd_metrics_report.json").exists()


@pytest.mark.unit
def test_module_main_import_does_not_trigger_cli() -> None:
    """Verify importing gen_desk_tools.metrics.__main__ does not invoke main()."""
    sys.modules.pop("gen_desk_tools.metrics.__main__", None)
    mod = importlib.import_module("gen_desk_tools.metrics.__main__")
    assert hasattr(mod, "main")


@pytest.mark.integration
def test_module_main_guard_executes_cleanly_via_runpy(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Verify python -m gen_desk_tools.metrics executes cleanly via __main__.py."""
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "gd_metrics",
            "--root",
            str(tmp_path),
            "--no-sheets",
            "--no-pytest",
            "--no-mypy",
            "--no-ruff",
        ],
    )
    sys.modules.pop("gen_desk_tools.metrics.__main__", None)
    with pytest.raises(SystemExit) as exc_info:
        runpy.run_module("gen_desk_tools.metrics", run_name="__main__")
    assert exc_info.value.code == 0
