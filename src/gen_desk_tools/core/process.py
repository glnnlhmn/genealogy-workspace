"""Path: src/gen_desk_tools/core/process.py

Standardized subprocess execution wrapper for GenDesk Tools.

Operational Role:
    Provides a uniform, testable subprocess interface shared across GenDesk
    Tools subpackages (git queries, pytest coverage, mypy, and Ruff) so command
    invocation, UTF-8 text capture, and OSError launch failures are handled
    consistently.

Classes:
    CommandResult: Immutable normalized result of a subprocess execution.

Functions:
    run_command: Execute an external command and return a CommandResult.
"""

from __future__ import annotations

import subprocess
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

__version__ = "1.0.0+build.2"

__all__ = [
    "CommandResult",
    "run_command",
]


@dataclass(frozen=True)
class CommandResult:
    """Normalized outcome of an external subprocess command execution."""

    command: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str
    error: str = ""

    @property
    def ok(self) -> bool:
        """Return True when the command exited with code 0 and no launch error."""
        return self.returncode == 0 and not self.error


def run_command(
    command: Sequence[str],
    *,
    cwd: Path | None = None,
    runner: Callable[..., Any] = subprocess.run,
) -> CommandResult:
    """Execute an external command and return a normalized CommandResult.

    Captures UTF-8 text stdout and stderr with check=False and converts OSError
    launch failures (e.g., missing executables) into a CommandResult with
    returncode=1 and a populated error string.

    Args:
        command: Executable and argument sequence.
        cwd: Optional working directory for the subprocess.
        runner: Subprocess callable (defaults to subprocess.run) for testing.
    """
    cmd_tuple = tuple(str(part) for part in command)
    try:
        proc = runner(
            list(cmd_tuple),
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
    except OSError as exc:
        return CommandResult(
            command=cmd_tuple,
            returncode=1,
            stdout="",
            stderr="",
            error=str(exc),
        )

    stdout_val = getattr(proc, "stdout", None)
    stderr_val = getattr(proc, "stderr", None)
    return CommandResult(
        command=cmd_tuple,
        returncode=int(proc.returncode),
        stdout=str(stdout_val or ""),
        stderr=str(stderr_val or ""),
    )
