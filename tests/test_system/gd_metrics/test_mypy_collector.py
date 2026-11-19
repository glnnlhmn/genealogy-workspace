"""Path: tests/test_system/gd_metrics/test_mypy_collector.py

Unit and integration tests for system.gd_metrics.collectors.mypy_collector.
"""

from __future__ import annotations

import io
from pathlib import Path
from types import SimpleNamespace

import pytest

from system.gd_metrics.collectors.mypy_collector import (
    parse_mypy_output,
    run_mypy_check,
)
from system.gd_metrics.config import BatchDefinition, load_config
from system.gd_metrics.progress import ProgressReporter

__version__ = "1.0.0+build.2"


# ==========================================================================
# GROUP 1: Mypy Output Parsing & Path Normalization
# Note: Verifies relative, absolute, external paths, and unmatched lines.
# ==========================================================================


@pytest.mark.unit
def test_parse_mypy_output_extracts_diagnostics_and_batches(tmp_path: Path) -> None:
    """Verify parse_mypy_output parses errors, notes, and path variants."""
    batches = (BatchDefinition("B1", "gda", "T0", ("src/gda/core",), ()),)
    abs_in_ws = (tmp_path / "src" / "gda" / "core" / "a.py").as_posix()
    external_path = Path("/outside/other.py").resolve().as_posix()
    raw = (
        f"{abs_in_ws}:12:4: error: Incompatible types [assignment]\n"
        f"{external_path}:5: note: See docs\n"
        "src\\gda\\core\\b.py:20: warning: Unused ignore [unused-ignore]\n"
        "Found 1 error in 1 file\n"
    )

    result = parse_mypy_output(raw, tmp_path, batches)

    assert len(result) == 3
    assert result[0].batch_id == "B1"
    assert result[0].file_path == "src/gda/core/a.py"
    assert result[0].error_code == "assignment"
    assert result[1].batch_id == ""
    assert result[1].error_code == ""
    assert result[2].file_path == "src/gda/core/b.py"


# ==========================================================================
# GROUP 2: Subprocess Execution & Error Guards
# Note: Verifies target discovery, progress reporting, and OSError handling.
# ==========================================================================


@pytest.mark.smoke
@pytest.mark.integration
def test_run_mypy_check_executes_runner_and_reports_progress(tmp_path: Path) -> None:
    """Verify run_mypy_check invokes runner on existing targets and parses stdout."""
    target_dir = tmp_path / "src" / "gda" / "core"
    target_dir.mkdir(parents=True)
    cfg = load_config(workspace_root=tmp_path, env={})
    batches = (BatchDefinition("B1", "gda", "T0", ("src/gda/core", "src/gda/core"), ()),)
    buf = io.StringIO()
    reporter = ProgressReporter(total_stages=1, verbose=True, stream=buf)

    def _fake_runner(*_args: object, **_kwargs: object) -> SimpleNamespace:
        return SimpleNamespace(
            stdout="src/gda/core/x.py:3: error: Boom [misc]\n",
            returncode=1,
        )

    res = run_mypy_check(cfg, batches, progress=reporter, runner=_fake_runner)

    assert res.returncode == 1
    assert len(res.diagnostics) == 1
    assert "Running mypy static type check" in buf.getvalue()


@pytest.mark.unit
def test_run_mypy_check_skips_when_no_targets_exist(tmp_path: Path) -> None:
    """Verify run_mypy_check returns skipped result when no batch paths exist."""
    cfg = load_config(workspace_root=tmp_path, env={})
    batches = (BatchDefinition("B1", "gda", "T0", ("src/missing",), ()),)

    res = run_mypy_check(cfg, batches, progress=None)

    assert res.returncode == 0
    assert res.diagnostics == ()
    assert "skipped" in res.summary_note


@pytest.mark.regression
def test_run_mypy_check_handles_os_error_gracefully(tmp_path: Path) -> None:
    """Verify run_mypy_check catches OSError when mypy cannot be launched."""
    (tmp_path / "src" / "gda").mkdir(parents=True)
    cfg = load_config(workspace_root=tmp_path, env={})
    batches = (BatchDefinition("B1", "gda", "T0", ("src/gda",), ()),)

    def _boom(*_args: object, **_kwargs: object) -> None:
        raise OSError("missing binary")

    res = run_mypy_check(cfg, batches, progress=None, runner=_boom)

    assert res.returncode == 1
    assert "mypy unavailable" in res.summary_note
