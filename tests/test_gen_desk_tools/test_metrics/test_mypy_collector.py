"""Path: tests/test_gen_desk_tools/test_metrics/test_mypy_collector.py

Unit, regression, integration, and invariant tests for mypy_collector.

Operational Role:
    Verifies mypy stdout parsing, path normalization and batch matching,
    subprocess target discovery, GAP-08 timeout protection, RARE-05
    non-UTF-8 subprocess output handling, 4-tier logging emission, and
    frozen dataclass immutability.
"""

from __future__ import annotations

import dataclasses
import io
import logging
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from gen_desk_tools.metrics.collectors import mypy_collector as mypy_mod
from gen_desk_tools.metrics.collectors.mypy_collector import (
    MypyDiagnostic,
    MypyRunResult,
    parse_mypy_output,
    run_mypy_check,
)
from gen_desk_tools.metrics.config import BatchDefinition, load_config
from gen_desk_tools.metrics.progress import ProgressReporter

__version__ = "1.0.0+build.3"

_MYPY_LOGGER = "gen_desk_tools.metrics.collectors.mypy_collector"


# ==========================================================================
# GROUP 1: Smoke & Primary Entrypoints
# Note: End-to-end mypy invocation with target deduplication and progress.
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


# ==========================================================================
# GROUP 2: Core Logic & Happy Paths
# Note: Public interface exports and mypy line parsing across path formats.
# ==========================================================================


@pytest.mark.unit
def test_mypy_collector_exposes_expected_public_interface() -> None:
    """Verify mypy_collector exports its expected public symbols."""
    expected = {
        "MypyDiagnostic",
        "MypyRunResult",
        "parse_mypy_output",
        "run_mypy_check",
    }
    assert expected.issubset(set(mypy_mod.__all__))


@pytest.mark.unit
def test_parse_mypy_output_extracts_diagnostics_and_batches(tmp_path: Path) -> None:
    """Verify parse_mypy_output parses errors, notes, warnings, and path variants."""
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
# GROUP 3: Edge Cases & Boundary Conditions
# Note: Blank/summary-only output and missing batch target skip behavior.
# ==========================================================================


@pytest.mark.regression
def test_parse_mypy_output_handles_empty_and_summary_only_output(tmp_path: Path) -> None:
    """Verify parse_mypy_output returns empty tuple on blank or summary-only text."""
    assert parse_mypy_output("", tmp_path, ()) == ()
    assert parse_mypy_output("Success: no issues found in 5 source files\n", tmp_path, ()) == ()


@pytest.mark.unit
def test_run_mypy_check_skips_when_no_targets_exist(tmp_path: Path) -> None:
    """Verify run_mypy_check returns skipped result when no batch paths exist."""
    cfg = load_config(workspace_root=tmp_path, env={})
    batches = (BatchDefinition("B1", "gda", "T0", ("src/missing",), ()),)

    res = run_mypy_check(cfg, batches, progress=None)

    assert res.returncode == 0
    assert res.diagnostics == ()
    assert "skipped" in res.summary_note


# ==========================================================================
# GROUP 4: Error Handling & Validation Failures
# Note: OSError, GAP-08 subprocess TimeoutExpired, and RARE-05 encoding errors.
# ==========================================================================


@pytest.mark.regression
def test_run_mypy_check_handles_os_error_gracefully(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify run_mypy_check catches OSError, logs ERROR, and returns degraded result."""
    (tmp_path / "src" / "gda").mkdir(parents=True)
    cfg = load_config(workspace_root=tmp_path, env={})
    batches = (BatchDefinition("B1", "gda", "T0", ("src/gda",), ()),)

    def _boom(*_args: object, **_kwargs: object) -> None:
        raise OSError("missing binary")

    with caplog.at_level(logging.ERROR, logger=_MYPY_LOGGER):
        res = run_mypy_check(cfg, batches, progress=None, runner=_boom)

    assert res.returncode == 1
    assert "mypy unavailable" in res.summary_note
    assert any(r.levelname == "ERROR" for r in caplog.records)


@pytest.mark.regression
def test_run_mypy_check_handles_timeout_expired_gracefully(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify GAP-08: subprocess.TimeoutExpired logs ERROR and returns degraded result."""
    (tmp_path / "src" / "gda").mkdir(parents=True)
    cfg = load_config(workspace_root=tmp_path, env={})
    batches = (BatchDefinition("B1", "gda", "T0", ("src/gda",), ()),)

    def _hang(*_args: object, **_kwargs: object) -> None:
        raise subprocess.TimeoutExpired(cmd=["mypy"], timeout=60)

    with caplog.at_level(logging.ERROR, logger=_MYPY_LOGGER):
        res = run_mypy_check(cfg, batches, progress=None, runner=_hang)

    assert res.returncode == 1
    assert "timeout" in res.summary_note.lower() or "timed out" in res.summary_note.lower()
    assert any(r.levelname == "ERROR" for r in caplog.records)


@pytest.mark.regression
def test_run_mypy_check_handles_non_utf8_subprocess_output_gracefully(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify RARE-05: UnicodeDecodeError from non-UTF-8 output logs ERROR cleanly."""
    (tmp_path / "src" / "gda").mkdir(parents=True)
    cfg = load_config(workspace_root=tmp_path, env={})
    batches = (BatchDefinition("B1", "gda", "T0", ("src/gda",), ()),)

    def _bad_encoding(*_args: object, **_kwargs: object) -> None:
        raise UnicodeDecodeError("utf-8", b"\x80\x81", 0, 1, "invalid start byte")

    with caplog.at_level(logging.ERROR, logger=_MYPY_LOGGER):
        res = run_mypy_check(cfg, batches, progress=None, runner=_bad_encoding)

    assert res.returncode == 1
    assert "encoding" in res.summary_note.lower() or "decode" in res.summary_note.lower()
    assert any(r.levelname == "ERROR" for r in caplog.records)


# ==========================================================================
# GROUP 5: Filesystem, CLI & Integration
# Note: 4-tier logging emission (INFO, VERBOSE, DEBUG) via caplog.
# ==========================================================================


@pytest.mark.integration
def test_run_mypy_check_emits_info_verbose_and_debug_log_records(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify run_mypy_check emits INFO, VERBOSE, and DEBUG log records."""
    (tmp_path / "src" / "gda" / "core").mkdir(parents=True)
    cfg = load_config(workspace_root=tmp_path, env={})
    batches = (BatchDefinition("B1", "gda", "T0", ("src/gda/core",), ()),)

    def _fake_runner(*_args: object, **_kwargs: object) -> SimpleNamespace:
        return SimpleNamespace(stdout="", returncode=0)

    with caplog.at_level(logging.DEBUG, logger=_MYPY_LOGGER):
        run_mypy_check(cfg, batches, progress=None, runner=_fake_runner)

    levels = {record.levelname for record in caplog.records}
    assert {"INFO", "VERBOSE", "DEBUG"}.issubset(levels)


# ==========================================================================
# GROUP 6: Integrity & Invariants
# Note: Frozen dataclass immutability for MypyDiagnostic and MypyRunResult.
# ==========================================================================


@pytest.mark.integrity
def test_mypy_dataclasses_are_immutable() -> None:
    """Verify MypyDiagnostic and MypyRunResult reject in-place mutation."""
    diag = MypyDiagnostic("B1", "src/a.py", 1, "error", "misc", "Boom")
    result = MypyRunResult(diagnostics=(diag,), summary_note="ok", returncode=0)

    with pytest.raises(dataclasses.FrozenInstanceError):
        diag.severity = "warning"  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.returncode = 1  # type: ignore[misc]
