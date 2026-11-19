"""Path: tests/test_system/gd_metrics/test_ruff_collector.py

Unit and integration tests for system.gd_metrics.collectors.ruff_collector.
"""

from __future__ import annotations

import io
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from system.gd_metrics.collectors.ruff_collector import (
    parse_ruff_json,
    run_ruff_check,
)
from system.gd_metrics.config import BatchDefinition, load_config
from system.gd_metrics.progress import ProgressReporter

__version__ = "1.0.0+build.2"


# ==========================================================================
# GROUP 1: Ruff JSON Parsing & Edge Cases
# Note: Verifies valid JSON items, empty output, and malformed JSON guards.
# ==========================================================================


@pytest.mark.unit
def test_parse_ruff_json_extracts_findings_and_batches(tmp_path: Path) -> None:
    """Verify parse_ruff_json parses relative, absolute, and external filenames."""
    batches = (BatchDefinition("B1", "gda", "T0", ("src/gda/core",), ()),)
    abs_in_ws = (tmp_path / "src" / "gda" / "core" / "a.py").as_posix()
    external_path = Path("/outside/other.py").resolve().as_posix()
    payload = json.dumps(
        [
            {
                "filename": abs_in_ws,
                "location": {"row": 10, "column": 1},
                "code": "E501",
                "message": "Line too long",
                "fix": {"applicability": "safe"},
            },
            {
                "filename": external_path,
                "location": {"row": 2, "column": 3},
                "code": "F401",
                "message": "Unused import",
                "fix": None,
            },
            {
                "filename": "src\\gda\\core\\b.py",
                "location": {"row": 4, "column": 1},
                "code": "D100",
                "message": "Missing docstring",
            },
        ]
    )

    result = parse_ruff_json(payload, tmp_path, batches)

    assert len(result) == 3
    assert result[0].batch_id == "B1"
    assert result[0].fixable is True
    assert result[1].batch_id == ""
    assert result[1].fixable is False
    assert result[2].file_path == "src/gda/core/b.py"


@pytest.mark.regression
def test_parse_ruff_json_handles_empty_and_invalid_json(tmp_path: Path) -> None:
    """Verify parse_ruff_json returns empty tuple on blank or invalid JSON."""
    assert parse_ruff_json("   ", tmp_path, ()) == ()
    assert parse_ruff_json("{bad json", tmp_path, ()) == ()


# ==========================================================================
# GROUP 2: Subprocess Execution & Error Guards
# Note: Verifies target discovery, progress reporting, and OSError handling.
# ==========================================================================


@pytest.mark.smoke
@pytest.mark.integration
def test_run_ruff_check_executes_runner_and_reports_progress(tmp_path: Path) -> None:
    """Verify run_ruff_check invokes runner on existing targets and parses JSON."""
    (tmp_path / "src" / "gda" / "core").mkdir(parents=True)
    cfg = load_config(workspace_root=tmp_path, env={})
    batches = (BatchDefinition("B1", "gda", "T0", ("src/gda/core", "src/gda/core"), ()),)
    buf = io.StringIO()
    reporter = ProgressReporter(total_stages=1, verbose=True, stream=buf)

    def _fake_runner(*_args: object, **_kwargs: object) -> SimpleNamespace:
        return SimpleNamespace(stdout="[]", returncode=0)

    res = run_ruff_check(cfg, batches, progress=reporter, runner=_fake_runner)

    assert res.returncode == 0
    assert res.diagnostics == ()
    assert "Running ruff lint check" in buf.getvalue()


@pytest.mark.unit
def test_run_ruff_check_skips_when_no_targets_exist(tmp_path: Path) -> None:
    """Verify run_ruff_check returns skipped result when no batch paths exist."""
    cfg = load_config(workspace_root=tmp_path, env={})
    batches = (BatchDefinition("B1", "gda", "T0", ("src/missing",), ()),)

    res = run_ruff_check(cfg, batches, progress=None)

    assert res.returncode == 0
    assert "skipped" in res.summary_note


@pytest.mark.regression
def test_run_ruff_check_handles_os_error_gracefully(tmp_path: Path) -> None:
    """Verify run_ruff_check catches OSError when ruff cannot be launched."""
    (tmp_path / "src" / "gda").mkdir(parents=True)
    cfg = load_config(workspace_root=tmp_path, env={})
    batches = (BatchDefinition("B1", "gda", "T0", ("src/gda",), ()),)

    def _boom(*_args: object, **_kwargs: object) -> None:
        raise OSError("missing binary")

    res = run_ruff_check(cfg, batches, progress=None, runner=_boom)

    assert res.returncode == 1
    assert "ruff unavailable" in res.summary_note
