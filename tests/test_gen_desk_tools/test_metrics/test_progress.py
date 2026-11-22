"""Path: tests/test_gen_desk_tools/test_metrics/test_progress.py

Tests for ProgressReporter interface, stage streaming, fuzzing, and error handling.

Operational Role:
    Verifies ProgressReporter public interface, smoke lifecycle, Hypothesis
    boundary invariants, input validation errors, stage/close edge cases,
    and UTF-8 log persistence in gen_desk_tools.metrics.progress.
"""

from __future__ import annotations

import io
import re
from pathlib import Path
from typing import Any

import pytest
from hypothesis import given
from hypothesis import strategies as st

from gen_desk_tools.metrics import progress as progress_mod
from gen_desk_tools.metrics.progress import ProgressReporter

__version__ = "1.0.0+build.6"

_UTC_LINE_RE = re.compile(r"^\[\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z\] .+$")

# ==========================================================================
# GROUP 1: Smoke & Primary Entry Points
# Note: End-to-end stage lifecycle, counted progress, and error output.
# ==========================================================================


@pytest.mark.smoke
@pytest.mark.unit
def test_progress_reporter_emits_stage_progress_and_summary() -> None:
    """Verify stage start, counted percentage, finish, and error lines emit."""
    buf = io.StringIO()
    reporter = ProgressReporter(total_stages=2, stream=buf)

    reporter.start_stage("Radon")
    reporter.update("Scanning files", current=5, total=10)
    reporter.update("Hidden non-verbose note")
    reporter.debug("Hidden debug note")
    reporter.finish_stage("10 files")
    reporter.error("Sample failure")
    reporter.close()

    assert buf.getvalue().splitlines() == [
        "[1/2] Radon...",
        "  - Scanning files: 5/10 (50%)",
        "[1/2] Done (10 files)",
        "[ERROR] Sample failure",
    ]


# ==========================================================================
# GROUP 2: Core Logic & Happy Paths
# Note: Public module interface and verbose/debug diagnostic output.
# ==========================================================================


@pytest.mark.unit
def test_progress_module_exposes_expected_public_interface() -> None:
    """Verify progress module exports ProgressReporter with expected public methods."""
    assert progress_mod.__all__ == ["ProgressReporter"]
    expected_methods = {"start_stage", "update", "debug", "finish_stage", "error", "close"}
    assert expected_methods.issubset(set(dir(ProgressReporter)))


@pytest.mark.unit
def test_progress_reporter_verbose_and_debug_emit_extra_lines() -> None:
    """Verify verbose and debug flags emit uncounted updates and debug lines."""
    buf = io.StringIO()
    reporter = ProgressReporter(total_stages=1, stream=buf, verbose=True, debug=True)

    reporter.start_stage("Config")
    reporter.update("Loaded config.toml")
    reporter.debug("Cache miss")
    reporter.finish_stage()

    assert buf.getvalue().splitlines() == [
        "[1/1] Config...",
        "  - Loaded config.toml",
        "  [DEBUG] Cache miss",
        "[1/1] Done",
    ]


# ==========================================================================
# GROUP 3: Edge Cases & Boundary Conditions
# Note: Hypothesis fuzzing, debug-verbose coupling, and close idempotency.
# ==========================================================================


@pytest.mark.regression
@given(
    current=st.integers(min_value=-1000, max_value=1000),
    total=st.integers(min_value=-100, max_value=1000),
)
def test_progress_reporter_update_handles_arbitrary_counts_without_crashing(
    current: int,
    total: int,
) -> None:
    """Verify update() formats counted progress for positive totals and skips invalid totals."""
    buf = io.StringIO()
    reporter = ProgressReporter(total_stages=1, stream=buf)

    reporter.update("Item", current=current, total=total)
    output = buf.getvalue()

    if total > 0:
        expected_pct = int((current / total) * 100)
        assert f"  - Item: {current}/{total} ({expected_pct}%)" in output
    else:
        assert output == ""


@pytest.mark.regression
@given(
    total_stages=st.integers(min_value=1, max_value=25),
    stage_names=st.lists(st.text(min_size=1, max_size=30), min_size=1, max_size=10),
)
def test_progress_reporter_stage_sequence_emits_monotonic_banners(
    total_stages: int,
    stage_names: list[str],
) -> None:
    """Verify repeated start_stage and finish_stage calls emit sequential stage indices."""
    buf = io.StringIO()
    reporter = ProgressReporter(total_stages=total_stages, stream=buf)

    for idx, name in enumerate(stage_names, start=1):
        reporter.start_stage(name)
        reporter.finish_stage()
        assert f"[{idx}/{total_stages}] {name}..." in buf.getvalue()
        assert f"[{idx}/{total_stages}] Done" in buf.getvalue()


@pytest.mark.regression
def test_progress_reporter_debug_mode_implies_verbose_updates() -> None:
    """Verify debug=True enables uncounted update messages even when verbose=False."""
    # Debug mode sets self._verbose = verbose or debug so diagnostic runs see updates.
    buf = io.StringIO()
    reporter = ProgressReporter(total_stages=1, stream=buf, verbose=False, debug=True)

    reporter.update("Diagnostic step")

    assert "  - Diagnostic step" in buf.getvalue()


@pytest.mark.regression
def test_progress_reporter_close_called_twice_is_idempotent(tmp_path: Path) -> None:
    """Verify calling close() repeatedly closes the handle once and stays safe."""
    log_path = tmp_path / "logs" / "repeat.log"
    buf = io.StringIO()
    reporter = ProgressReporter(total_stages=1, stream=buf, log_file=log_path)
    # Capture underlying handle before close() clears the reference.
    handle = reporter._log_handle
    assert handle is not None

    reporter.close()
    reporter.close()

    assert handle.closed is True
    assert reporter._log_handle is None
    assert log_path.exists()


# ==========================================================================
# GROUP 4: Error Handling & Validation Failures
# Note: Non-positive stage counts, invalid types, and unwritable logs.
# ==========================================================================


@pytest.mark.regression
@pytest.mark.parametrize("bad_stages", [0, -1, -5])
def test_progress_reporter_non_positive_total_stages_raises_value_error(bad_stages: int) -> None:
    """Verify total_stages < 1 raises ValueError across zero and negative values."""
    with pytest.raises(ValueError, match="total_stages must be at least 1"):
        ProgressReporter(total_stages=bad_stages)


@pytest.mark.regression
@pytest.mark.parametrize(
    "bad_type_stages",
    ["a", "1", "@", "$", "!", "", None, 1.5, -2.5, True, False],
)
def test_progress_reporter_invalid_type_total_stages_raises_error(
    bad_type_stages: Any,
) -> None:
    """Verify non-integer, symbol, float, or boolean total_stages values are rejected."""
    # Strengthened contract: floats and booleans must fail alongside non-comparable types.
    with pytest.raises((TypeError, ValueError)):
        ProgressReporter(total_stages=bad_type_stages)


@pytest.mark.regression
@pytest.mark.integration
def test_progress_reporter_unwritable_log_path_raises_clean_os_error(tmp_path: Path) -> None:
    """Verify opening an unwritable directory as log_file raises OSError cleanly."""
    # Point log_file at an existing directory so open() fails on all platforms.
    blocked_dir = tmp_path / "logs_dir"
    blocked_dir.mkdir()
    buf = io.StringIO()

    with pytest.raises(OSError):
        ProgressReporter(total_stages=1, stream=buf, log_file=blocked_dir)


# ==========================================================================
# GROUP 5: Filesystem, CLI & Integration
# Note: UTF-8 log file creation, UTC timestamps, and handle cleanup.
# ==========================================================================


@pytest.mark.integration
def test_progress_reporter_writes_timestamped_utf8_log_file(tmp_path: Path) -> None:
    """Verify log_file creates parent folders, formats UTC lines, and closes."""
    log_path = tmp_path / "logs" / "gd_metrics.log"
    buf = io.StringIO()
    reporter = ProgressReporter(total_stages=1, stream=buf, log_file=log_path)

    reporter.start_stage("Sync")
    reporter.finish_stage("ok")
    reporter.close()

    lines = log_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert all(_UTC_LINE_RE.match(line) for line in lines)
    assert lines[0].endswith("] [1/1] Sync...")
    assert lines[1].endswith("] [1/1] Done (ok)")
