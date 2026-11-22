"""Path: tests/test_gen_desk_tools/test_metrics/test_ruff_collector.py

Unit, regression, integration, and invariant tests for ruff_collector.

Operational Role:
    Verifies Ruff JSON parsing, path normalization and batch matching,
    subprocess target discovery, GAP-08 timeout protection, RARE-05
    non-UTF-8 subprocess output handling, 4-tier logging emission, and
    frozen dataclass immutability.
"""

from __future__ import annotations

import dataclasses
import io
import json
import logging
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from gen_desk_tools.metrics.collectors import ruff_collector as ruff_mod
from gen_desk_tools.metrics.collectors.ruff_collector import (
    RuffDiagnostic,
    RuffRunResult,
    parse_ruff_json,
    run_ruff_check,
)
from gen_desk_tools.metrics.config import BatchDefinition, load_config
from gen_desk_tools.metrics.progress import ProgressReporter

__version__ = "1.0.0+build.3"

_RUFF_LOGGER = "gen_desk_tools.metrics.collectors.ruff_collector"


# ==========================================================================
# GROUP 1: Smoke & Primary Entrypoints
# Note: End-to-end ruff check invocation with progress reporting.
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


# ==========================================================================
# GROUP 2: Core Logic & Happy Paths
# Note: Public interface exports and Ruff JSON parsing across path formats.
# ==========================================================================


@pytest.mark.unit
def test_ruff_collector_exposes_expected_public_interface() -> None:
    """Verify ruff_collector exports its expected public symbols."""
    expected = {
        "RuffDiagnostic",
        "RuffRunResult",
        "parse_ruff_json",
        "run_ruff_check",
    }
    assert expected.issubset(set(ruff_mod.__all__))


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


# ==========================================================================
# GROUP 3: Edge Cases & Boundary Conditions
# Note: Blank/malformed JSON and missing batch target skip behavior.
# ==========================================================================


@pytest.mark.regression
def test_parse_ruff_json_handles_empty_and_invalid_json(tmp_path: Path) -> None:
    """Verify parse_ruff_json returns empty tuple on blank or invalid JSON."""
    assert parse_ruff_json("   ", tmp_path, ()) == ()
    assert parse_ruff_json("{bad json", tmp_path, ()) == ()


@pytest.mark.unit
def test_run_ruff_check_skips_when_no_targets_exist(tmp_path: Path) -> None:
    """Verify run_ruff_check returns skipped result when no batch paths exist."""
    cfg = load_config(workspace_root=tmp_path, env={})
    batches = (BatchDefinition("B1", "gda", "T0", ("src/missing",), ()),)

    res = run_ruff_check(cfg, batches, progress=None)

    assert res.returncode == 0
    assert "skipped" in res.summary_note


# ==========================================================================
# GROUP 4: Error Handling & Validation Failures
# Note: OSError, GAP-08 subprocess TimeoutExpired, and RARE-05 encoding errors.
# ==========================================================================


@pytest.mark.regression
def test_run_ruff_check_handles_os_error_gracefully(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify run_ruff_check catches OSError, logs ERROR, and returns degraded result."""
    (tmp_path / "src" / "gda").mkdir(parents=True)
    cfg = load_config(workspace_root=tmp_path, env={})
    batches = (BatchDefinition("B1", "gda", "T0", ("src/gda",), ()),)

    def _boom(*_args: object, **_kwargs: object) -> None:
        raise OSError("missing binary")

    with caplog.at_level(logging.ERROR, logger=_RUFF_LOGGER):
        res = run_ruff_check(cfg, batches, progress=None, runner=_boom)

    assert res.returncode == 1
    assert "ruff unavailable" in res.summary_note
    assert any(r.levelname == "ERROR" for r in caplog.records)


@pytest.mark.regression
def test_run_ruff_check_handles_timeout_expired_gracefully(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify GAP-08: subprocess.TimeoutExpired logs ERROR and returns degraded result."""
    (tmp_path / "src" / "gda").mkdir(parents=True)
    cfg = load_config(workspace_root=tmp_path, env={})
    batches = (BatchDefinition("B1", "gda", "T0", ("src/gda",), ()),)

    def _hang(*_args: object, **_kwargs: object) -> None:
        raise subprocess.TimeoutExpired(cmd=["ruff"], timeout=30)

    with caplog.at_level(logging.ERROR, logger=_RUFF_LOGGER):
        res = run_ruff_check(cfg, batches, progress=None, runner=_hang)

    assert res.returncode == 1
    assert "timeout" in res.summary_note.lower() or "timed out" in res.summary_note.lower()
    assert any(r.levelname == "ERROR" for r in caplog.records)


@pytest.mark.regression
def test_run_ruff_check_handles_non_utf8_subprocess_output_gracefully(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify RARE-05: UnicodeDecodeError from CP1252/non-UTF-8 output logs ERROR cleanly."""
    (tmp_path / "src" / "gda").mkdir(parents=True)
    cfg = load_config(workspace_root=tmp_path, env={})
    batches = (BatchDefinition("B1", "gda", "T0", ("src/gda",), ()),)

    def _bad_encoding(*_args: object, **_kwargs: object) -> None:
        raise UnicodeDecodeError("utf-8", b"\x80\x81", 0, 1, "invalid start byte")

    with caplog.at_level(logging.ERROR, logger=_RUFF_LOGGER):
        res = run_ruff_check(cfg, batches, progress=None, runner=_bad_encoding)

    assert res.returncode == 1
    assert "encoding" in res.summary_note.lower() or "decode" in res.summary_note.lower()
    assert any(r.levelname == "ERROR" for r in caplog.records)


# ==========================================================================
# GROUP 5: Filesystem, CLI & Integration
# Note: 4-tier logging emission (INFO, VERBOSE, DEBUG) via caplog.
# ==========================================================================


@pytest.mark.integration
def test_run_ruff_check_emits_info_verbose_and_debug_log_records(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify run_ruff_check emits INFO, VERBOSE, and DEBUG log records."""
    (tmp_path / "src" / "gda" / "core").mkdir(parents=True)
    cfg = load_config(workspace_root=tmp_path, env={})
    batches = (BatchDefinition("B1", "gda", "T0", ("src/gda/core",), ()),)

    def _fake_runner(*_args: object, **_kwargs: object) -> SimpleNamespace:
        return SimpleNamespace(stdout="[]", returncode=0)

    with caplog.at_level(logging.DEBUG, logger=_RUFF_LOGGER):
        run_ruff_check(cfg, batches, progress=None, runner=_fake_runner)

    levels = {record.levelname for record in caplog.records}
    assert {"INFO", "VERBOSE", "DEBUG"}.issubset(levels)


# ==========================================================================
# GROUP 6: Integrity & Invariants
# Note: Frozen dataclass immutability for RuffDiagnostic and RuffRunResult.
# ==========================================================================


@pytest.mark.integrity
def test_ruff_dataclasses_are_immutable() -> None:
    """Verify RuffDiagnostic and RuffRunResult reject in-place mutation."""
    diag = RuffDiagnostic("B1", "src/a.py", 1, 1, "F401", "Unused import", True)
    result = RuffRunResult(diagnostics=(diag,), summary_note="ok", returncode=0)

    with pytest.raises(dataclasses.FrozenInstanceError):
        diag.fixable = False  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.returncode = 1  # type: ignore[misc]
