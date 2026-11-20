"""Path: tests/test_gen_desk_tools/test_metrics/test_progress.py

Unit and integration tests for gen_desk_tools.metrics.progress.
"""

from __future__ import annotations

import io
from pathlib import Path

import pytest

from gen_desk_tools.metrics.progress import ProgressReporter

__version__ = "1.0.0+build.1"


# ==========================================================================
# GROUP 1: Validation & Stream Output
# Note: Verifies stage numbering, percentage formatting, and verbosity rules.
# ==========================================================================


@pytest.mark.regression
def test_progress_reporter_invalid_total_stages_raises_value_error() -> None:
    """Verify total_stages < 1 raises ValueError."""
    with pytest.raises(ValueError, match="total_stages must be at least 1"):
        ProgressReporter(total_stages=0)


@pytest.mark.smoke
@pytest.mark.unit
def test_progress_reporter_emits_stage_progress_and_summary() -> None:
    """Verify stage start, counted update, and finish emit expected lines."""
    buf = io.StringIO()
    reporter = ProgressReporter(total_stages=2, stream=buf)

    reporter.start_stage("Radon")
    reporter.update("Scanning files", current=5, total=10)
    reporter.update("Hidden non-verbose note")
    reporter.debug("Hidden debug note")
    reporter.finish_stage("10 files")
    reporter.error("Sample failure")
    reporter.close()

    output = buf.getvalue().splitlines()
    assert output == [
        "[1/2] Radon...",
        "  - Scanning files: 5/10 (50%)",
        "[1/2] Done (10 files)",
        "[ERROR] Sample failure",
    ]


@pytest.mark.unit
def test_progress_reporter_verbose_and_debug_emit_extra_lines() -> None:
    """Verify verbose and debug modes emit uncounted updates and debug lines."""
    buf = io.StringIO()
    reporter = ProgressReporter(total_stages=1, stream=buf, verbose=True, debug=True)

    reporter.start_stage("Config")
    reporter.update("Loaded config.toml")
    reporter.debug("Cache miss")
    reporter.finish_stage()

    output = buf.getvalue().splitlines()
    assert output == [
        "[1/1] Config...",
        "  - Loaded config.toml",
        "  [DEBUG] Cache miss",
        "[1/1] Done",
    ]


# ==========================================================================
# GROUP 2: UTF-8 File Logging
# Note: Verifies optional log_file creation and timestamped persistence.
# ==========================================================================


@pytest.mark.integration
def test_progress_reporter_writes_timestamped_utf8_log_file(tmp_path: Path) -> None:
    """Verify log_file receives timestamped lines and closes cleanly."""
    log_path = tmp_path / "logs" / "gd_metrics.log"
    buf = io.StringIO()
    reporter = ProgressReporter(total_stages=1, stream=buf, log_file=log_path)

    reporter.start_stage("Sync")
    reporter.finish_stage("ok")
    reporter.close()

    content = log_path.read_text(encoding="utf-8")
    assert "[1/1] Sync..." in content
    assert "[1/1] Done (ok)" in content
