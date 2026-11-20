"""Path: tests/test_gen_desk_tools/test_core/test_process.py

Unit, regression, and integration tests for gen_desk_tools.core.process.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from gen_desk_tools.core.process import CommandResult, run_command

__version__ = "1.0.0+build.1"

# ==========================================================================
# GROUP 1: Smoke & Primary Entrypoints
# Note: End-to-end real subprocess execution through run_command.
# ==========================================================================


@pytest.mark.smoke
@pytest.mark.integration
def test_run_command_executes_python_echo_and_captures_stdout(tmp_path: Path) -> None:
    """Verify run_command executes a real subprocess and captures UTF-8 stdout."""
    result = run_command([sys.executable, "-c", "print('hello-gdt')"], cwd=tmp_path)

    assert result.ok is True
    assert result.returncode == 0
    assert result.stdout.strip() == "hello-gdt"
    assert result.stderr == ""
    assert result.error == ""


# ==========================================================================
# GROUP 2: Core Logic & Happy Paths
# Note: In-memory runner injection, CommandResult.ok semantics, and None stream normalization.
# ==========================================================================


@pytest.mark.unit
def test_run_command_passes_expected_arguments_to_injected_runner(tmp_path: Path) -> None:
    """Verify run_command forwards command list, cwd, and UTF-8 capture flags to runner."""
    captured: dict[str, Any] = {}

    def fake_runner(cmd: list[str], **kwargs: Any) -> SimpleNamespace:
        captured["cmd"] = cmd
        captured["kwargs"] = kwargs
        return SimpleNamespace(returncode=0, stdout="ok\n", stderr="")

    result = run_command(("git", "status"), cwd=tmp_path, runner=fake_runner)

    assert result == CommandResult(
        command=("git", "status"),
        returncode=0,
        stdout="ok\n",
        stderr="",
        error="",
    )
    assert result.ok is True
    assert captured["cmd"] == ["git", "status"]
    assert captured["kwargs"]["cwd"] == tmp_path
    assert captured["kwargs"]["capture_output"] is True
    assert captured["kwargs"]["text"] is True
    assert captured["kwargs"]["encoding"] == "utf-8"
    assert captured["kwargs"]["check"] is False


@pytest.mark.unit
def test_run_command_normalizes_none_stdout_and_stderr_to_empty_strings() -> None:
    """Verify run_command converts None stdout/stderr from a runner into empty strings."""

    def fake_runner(cmd: list[str], **kwargs: Any) -> SimpleNamespace:
        return SimpleNamespace(returncode=0, stdout=None, stderr=None)

    result = run_command(["echo"], runner=fake_runner)

    assert result.ok is True
    assert result.stdout == ""
    assert result.stderr == ""


# ==========================================================================
# GROUP 3: Edge Cases & Error Handling
# Note: Non-zero exit codes and OSError launch failures.
# ==========================================================================


@pytest.mark.regression
def test_run_command_nonzero_exit_code_marks_result_not_ok() -> None:
    """Verify non-zero subprocess exit codes set ok=False while preserving stderr."""

    def fake_runner(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(cmd, returncode=2, stdout="", stderr="bad flag")

    result = run_command(["tool", "--bad"], runner=fake_runner)

    assert result.ok is False
    assert result.returncode == 2
    assert result.stderr == "bad flag"
    assert result.error == ""


@pytest.mark.regression
def test_run_command_os_error_returns_normalized_error_result() -> None:
    """Verify OSError during subprocess launch returns returncode=1 and error details."""

    def failing_runner(cmd: list[str], **kwargs: Any) -> Any:
        raise FileNotFoundError("executable not found")

    result = run_command(["missing-binary"], runner=failing_runner)

    assert result.ok is False
    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == ""
    assert "executable not found" in result.error
