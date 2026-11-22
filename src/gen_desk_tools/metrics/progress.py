"""Path: src/gen_desk_tools/metrics/progress.py

Real-time stage and file progress reporter for gd_metrics.

Operational Role:
    Streams concise stage banners, intra-stage percentage updates, debug
    diagnostics, and error notices to stderr (or an injected TextIO stream),
    with optional UTC-timestamped UTF-8 file logging.

Classes:
    ProgressReporter: Stateful multi-stage progress and diagnostic sink.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import TextIO

__version__ = "1.0.0+build.3"

__all__ = ["ProgressReporter"]


class ProgressReporter:
    """Emit structured stage and item progress updates during telemetry runs.

    Args:
        total_stages: Positive count of pipeline stages announced in [n/total] prefixes.
        stream: Target output stream; defaults to sys.stderr when None.
        verbose: Emit non-counted intra-stage status messages when True.
        debug: Emit [DEBUG] lines and implicitly enable verbose updates when True.
        log_file: Optional UTF-8 append log path; parent directories are created automatically.

    Raises:
        TypeError: If total_stages is not a strict integer (rejects bool, float, str, None).
        ValueError: If total_stages is less than 1.
    """

    def __init__(
        self,
        total_stages: int,
        *,
        stream: TextIO | None = None,
        verbose: bool = False,
        debug: bool = False,
        log_file: Path | None = None,
    ) -> None:
        """Initialize the progress reporter and open the optional log sink."""
        # Reject booleans explicitly because bool subclasses int in Python.
        if isinstance(total_stages, bool) or not isinstance(total_stages, int):
            msg = f"total_stages must be an integer, got {type(total_stages).__name__}"
            raise TypeError(msg)
        if total_stages < 1:
            msg = "total_stages must be at least 1"
            raise ValueError(msg)
        self._total_stages = total_stages
        self._current_stage = 0
        self._stream: TextIO = sys.stderr if stream is None else stream
        # Debug mode implies verbose so diagnostic runs surface all intra-stage updates.
        self._verbose = verbose or debug
        self._debug = debug
        self._log_handle: TextIO | None = None
        if log_file is not None:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            self._log_handle = log_file.open("a", encoding="utf-8")

    def _emit(self, line: str) -> None:
        """Write a formatted line to the active stream and optional UTC log file."""
        self._stream.write(f"{line}\n")
        self._stream.flush()
        if self._log_handle is not None:
            stamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
            self._log_handle.write(f"[{stamp}] {line}\n")
            self._log_handle.flush()

    def start_stage(self, name: str) -> None:
        """Advance the stage counter and announce the start of name."""
        self._current_stage += 1
        self._emit(f"[{self._current_stage}/{self._total_stages}] {name}...")

    def update(
        self,
        message: str,
        *,
        current: int | None = None,
        total: int | None = None,
    ) -> None:
        """Emit an intra-stage progress update with optional percentage.

        Counted updates (current and positive total) always emit; plain text
        updates emit only when verbose or debug mode is active.
        """
        if current is not None and total is not None and total > 0:
            pct = int((current / total) * 100)
            self._emit(f"  - {message}: {current}/{total} ({pct}%)")
            return
        if self._verbose:
            self._emit(f"  - {message}")

    def debug(self, message: str) -> None:
        """Emit a debug diagnostic line when debug mode is enabled."""
        if self._debug:
            self._emit(f"  [DEBUG] {message}")

    def finish_stage(self, summary: str = "") -> None:
        """Announce completion of the current stage with an optional summary."""
        suffix = f" ({summary})" if summary else ""
        self._emit(f"[{self._current_stage}/{self._total_stages}] Done{suffix}")

    def error(self, message: str) -> None:
        """Emit an error status line."""
        self._emit(f"[ERROR] {message}")

    def close(self) -> None:
        """Close the underlying log file handle if open."""
        if self._log_handle is not None:
            self._log_handle.close()
            self._log_handle = None
