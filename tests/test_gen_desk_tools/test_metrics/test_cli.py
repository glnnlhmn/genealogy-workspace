"""Path: tests/test_gen_desk_tools/test_metrics/test_cli.py

Unit, regression, integration, and invariant tests for gen_desk_tools.metrics.cli and __main__.

Operational Role:
    Verifies CLI argument parsing, 7-stage telemetry pipeline orchestration,
    __main__ import/runpy behavior, GAP-05 pre-flight validation before
    expensive stages execute, RARE-03 isolated multi-run execution, 4-tier
    diagnostic logging, and progress log handle cleanup on errors.
"""

from __future__ import annotations

import importlib
import logging
import runpy
import sys
from pathlib import Path
from typing import Any

import pytest

from gen_desk_tools.metrics import cli as cli_mod
from gen_desk_tools.metrics.cli import main, run_pipeline
from gen_desk_tools.metrics.config import load_config
from gen_desk_tools.metrics.progress import ProgressReporter

__version__ = "1.0.0+build.5"

_CLI_LOGGER = "gen_desk_tools.metrics.cli"


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
# GROUP 1: Smoke & Primary Entrypoints
# Note: CLI end-to-end pipeline, skip flags, Sheets sync, and __main__.
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


# ==========================================================================
# GROUP 2: Core Logic & Happy Paths
# Note: Public interface exports and RARE-03 isolated multi-run execution.
# ==========================================================================


@pytest.mark.unit
def test_cli_module_exposes_expected_public_interface() -> None:
    """Verify cli exports build_parser, main, and run_pipeline in __all__."""
    expected = {"build_parser", "main", "run_pipeline"}
    assert expected.issubset(set(cli_mod.__all__))


@pytest.mark.integration
def test_cli_main_supports_isolated_basetemp_across_multiple_runs(tmp_path: Path) -> None:
    """Verify RARE-03: separate workspace/basetemp runs isolate outputs cleanly."""
    run_a = tmp_path / "run_a"
    run_b = tmp_path / "run_b"
    run_a.mkdir()
    run_b.mkdir()

    cfg_a = run_a / "metrics.toml"
    cfg_b = run_b / "metrics.toml"
    cfg_a.write_text(
        '[telemetry]\nsync_sheets_by_default = false\nlocal_report_dir = "out_a"\n'
        'pytest_basetemp = "basetemp_a"\n',
        encoding="utf-8",
    )
    cfg_b.write_text(
        '[telemetry]\nsync_sheets_by_default = false\nlocal_report_dir = "out_b"\n'
        'pytest_basetemp = "basetemp_b"\n',
        encoding="utf-8",
    )

    code_a = main(
        ["--root", str(run_a), "--config", str(cfg_a), "--no-pytest", "--no-mypy", "--no-ruff"]
    )
    code_b = main(
        ["--root", str(run_b), "--config", str(cfg_b), "--no-pytest", "--no-mypy", "--no-ruff"]
    )

    assert code_a == 0
    assert code_b == 0
    assert (run_a / "out_a" / "gd_metrics_report.json").is_file()
    assert (run_b / "out_b" / "gd_metrics_report.json").is_file()
    assert not (run_a / "out_b" / "gd_metrics_report.json").exists()


# ==========================================================================
# GROUP 4: Error Handling & Validation Failures
# Note: GAP-05 pre-flight validation before expensive stages execute.
# ==========================================================================


@pytest.mark.regression
def test_cli_main_fails_fast_before_collectors_when_sheets_enabled_without_target(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify GAP-05: missing sheet_url/sheet_id halts before Radon/collectors run."""
    called_stages: list[str] = []

    def _boom_radon(*_args: Any, **_kwargs: Any) -> Any:
        called_stages.append("radon")
        raise AssertionError("Radon collector should not run when GAP-05 pre-flight fails")

    monkeypatch.setattr(cli_mod, "collect_radon_metrics", _boom_radon)

    with caplog.at_level(logging.ERROR, logger=_CLI_LOGGER):
        exit_code = main(
            [
                "--root",
                str(tmp_path),
                "--no-pytest",
                "--no-mypy",
                "--no-ruff",
            ]
        )

    assert exit_code != 0
    assert called_stages == []
    assert any(r.levelname == "ERROR" for r in caplog.records)


# ==========================================================================
# GROUP 5: Filesystem, CLI & Integration
# Note: 4-tier logging emission and log handle cleanup on pipeline failure.
# ==========================================================================


@pytest.mark.integration
def test_cli_main_emits_info_verbose_and_debug_log_records(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify cli main() emits INFO, VERBOSE, and DEBUG records during a run."""
    with caplog.at_level(logging.DEBUG, logger=_CLI_LOGGER):
        exit_code = main(
            [
                "--root",
                str(tmp_path),
                "--no-sheets",
                "--no-pytest",
                "--no-mypy",
                "--no-ruff",
                "-v",
                "--debug",
            ]
        )

    assert exit_code == 0
    levels = {record.levelname for record in caplog.records}
    assert {"INFO", "VERBOSE", "DEBUG"}.issubset(levels)


@pytest.mark.regression
def test_cli_main_closes_progress_reporter_when_pipeline_raises(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify progress.close() is invoked even if run_pipeline raises an exception."""
    closed: list[bool] = []
    orig_close = ProgressReporter.close

    def _tracked_close(self: ProgressReporter) -> None:
        closed.append(True)
        orig_close(self)

    def _fail_batches(_cfg: Any) -> Any:
        raise RuntimeError("stage 1 failure")

    monkeypatch.setattr(ProgressReporter, "close", _tracked_close)
    monkeypatch.setattr(cli_mod, "resolve_batches", _fail_batches)

    cfg = load_config(workspace_root=tmp_path, env={})
    assert cfg.workspace_root == tmp_path.resolve()

    with pytest.raises(RuntimeError, match="stage 1 failure"):
        main(
            [
                "--root",
                str(tmp_path),
                "--no-sheets",
                "--no-pytest",
                "--no-mypy",
                "--no-ruff",
            ]
        )

    assert closed == [True]
    assert callable(run_pipeline)
