"""Path: src/system/gd_metrics/progress.py

Real-time stage and file progress reporter for gd_metrics.

Streams concise status updates to stderr (or a custom TextIO stream) and
optionally writes timestamped UTF-8 diagnostic logs to a file under logs/.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import TextIO

__version__ = "1.0.0+build.1"

__all__ = ["ProgressReporter"]


class ProgressReporter:
    """Emit structured stage and item progress updates during telemetry runs."""

    def __init__(
        self,
        total_stages: int,
        *,
        stream: TextIO | None = None,
        verbose: bool = False,
        debug: bool = False,
        log_file: Path | None = None,
    ) -> None:
        """Initialize the progress reporter and optional log sink."""
        if total_stages < 1:
            msg = "total_stages must be at least 1"
            raise ValueError(msg)
        self._total_stages = total_stages
        self._current_stage = 0
        self._stream: TextIO = sys.stderr if stream is None else stream
        self._verbose = verbose or debug
        self._debug = debug
        self._log_handle: TextIO | None = None
        if log_file is not None:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            self._log_handle = log_file.open("a", encoding="utf-8")

    def _emit(self, line: str) -> None:
        """Write a formatted line to the active stream and optional log file."""
        self._stream.write(f"{line}\n")
        self._stream.flush()
        if self._log_handle is not None:
            stamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
            self._log_handle.write(f"[{stamp}] {line}\n")
            self._log_handle.flush()

    def start_stage(self, name: str) -> None:
        """Advance to the next stage and announce its start."""
        self._current_stage += 1
        self._emit(f"[{self._current_stage}/{self._total_stages}] {name}...")

    def update(
        self,
        message: str,
        *,
        current: int | None = None,
        total: int | None = None,
    ) -> None:
        """Emit an intra-stage progress update with optional percentage."""
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
        """Announce completion of the current stage."""
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
