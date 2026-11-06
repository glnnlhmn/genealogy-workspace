"""Path: tests/test_system/test_pre_push.py

Comprehensive test suite verifying Git pre-push hook in src.system.hooks.pre_push.

Operational Role:
    Verifies protected branch rejection ('main', 'master'), clean feature branch
    validation, test marker enforcement, subprocess execution wrappers, and
    CLI module entrypoint behavior with 100.00% statement and branch coverage.
"""

from __future__ import annotations

import runpy
import subprocess
import sys
from unittest.mock import patch

import pytest

import system.hooks.pre_push as pp

__version__ = "1.0.0+build.9"


# ==============================================================================
# GROUP 1: BRANCH INSPECTION & PROTECTED BRANCH ENFORCEMENT
# ==============================================================================


@pytest.mark.unit
def test_get_current_branch_success() -> None:
    """Verify get_current_branch extracts branch name from git rev-parse."""
    with patch.object(
        subprocess,
        "run",
        return_value=subprocess.CompletedProcess(
            args=["git"], returncode=0, stdout="feature/archive-refactor\n"
        ),
    ):
        assert pp.get_current_branch() == "feature/archive-refactor"


@pytest.mark.regression
def test_get_current_branch_failure_returns_unknown() -> None:
    """Verify get_current_branch returns 'unknown' when git rev-parse fails."""
    with patch.object(
        subprocess,
        "run",
        side_effect=subprocess.CalledProcessError(1, ["git"]),
    ):
        assert pp.get_current_branch() == "unknown"


@pytest.mark.regression
def test_get_current_branch_os_error_returns_unknown() -> None:
    """Verify get_current_branch returns 'unknown' when subprocess raises OSError."""
    with patch.object(
        subprocess,
        "run",
        side_effect=OSError("Git not found"),
    ):
        assert pp.get_current_branch() == "unknown"


@pytest.mark.regression
def test_get_current_branch_empty_stdout_returns_unknown() -> None:
    """Verify get_current_branch returns 'unknown' when stdout is whitespace."""
    with patch.object(
        subprocess,
        "run",
        return_value=subprocess.CompletedProcess(args=["git"], returncode=0, stdout="   \n"),
    ):
        assert pp.get_current_branch() == "unknown"


@pytest.mark.unit
@pytest.mark.parametrize("branch", ["main", "master"])
def test_validate_branch_rejects_protected_branches(
    branch: str, capsys: pytest.CaptureFixture[str]
) -> None:
    """Verify validate_branch returns False and prints error for protected branches."""
    assert pp.validate_branch(branch) is False
    captured = capsys.readouterr()
    assert f"Direct push to protected branch '{branch}' is prohibited" in captured.out


@pytest.mark.unit
@pytest.mark.parametrize("branch", ["feature/models", "bugfix/issue-12", "unknown"])
def test_validate_branch_permits_unprotected_branches(branch: str) -> None:
    """Verify validate_branch returns True for feature branches and unknown states."""
    assert pp.validate_branch(branch) is True


# ==============================================================================
# GROUP 2: PRE-PUSH VALIDATION SUITE EXECUTION
# ==============================================================================


@pytest.mark.unit
def test_run_pre_push_suite_all_pass() -> None:
    """Verify run_pre_push_suite returns True when all test commands succeed."""
    with patch.object(
        subprocess,
        "run",
        return_value=subprocess.CompletedProcess(args=["pytest"], returncode=0),
    ):
        assert pp.run_pre_push_suite(verbose=True) is True


@pytest.mark.regression
def test_run_pre_push_suite_first_command_fails() -> None:
    """Verify run_pre_push_suite returns False immediately if a command fails."""
    with patch.object(
        subprocess,
        "run",
        return_value=subprocess.CompletedProcess(args=["pytest"], returncode=1),
    ):
        assert pp.run_pre_push_suite(verbose=False) is False


@pytest.mark.regression
def test_run_pre_push_suite_subprocess_error_handled() -> None:
    """Verify run_pre_push_suite returns False when subprocess raises exception."""
    with patch.object(
        subprocess,
        "run",
        side_effect=OSError("Command not found"),
    ):
        assert pp.run_pre_push_suite(verbose=False) is False


# ==============================================================================
# GROUP 3: COMMAND-LINE ENTRYPOINT & DISPATCH
# ==============================================================================


@pytest.mark.unit
def test_main_cli_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify main returns 0 when branch is allowed and test suite passes."""
    monkeypatch.setattr(pp, "get_current_branch", lambda: "feature/safe")
    monkeypatch.setattr(pp, "run_pre_push_suite", lambda verbose=False: True)

    exit_code = pp.main(["-v"])
    assert exit_code == 0


@pytest.mark.unit
def test_main_cli_protected_branch_exit_code_1(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify main exits 1 when called on a protected branch."""
    monkeypatch.setattr(pp, "get_current_branch", lambda: "main")

    with pytest.raises(SystemExit) as exc:
        pp.main([])
    assert exc.value.code == 1


@pytest.mark.unit
def test_main_cli_test_suite_failure_exit_code_1(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify main exits 1 when pre-push test suites fail."""
    monkeypatch.setattr(pp, "get_current_branch", lambda: "feature/safe")
    monkeypatch.setattr(pp, "run_pre_push_suite", lambda verbose=False: False)

    with pytest.raises(SystemExit) as exc:
        pp.main([])
    assert exc.value.code == 1


@pytest.mark.smoke
@pytest.mark.unit
def test_pre_push_module_main_entrypoint() -> None:
    """Verify __main__ block dispatches main correctly without environment side effects."""
    saved_module = sys.modules.get("system.hooks.pre_push")

    def mock_subprocess_run(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        if "rev-parse" in cmd:
            return subprocess.CompletedProcess(
                args=cmd, returncode=0, stdout="feature/safe\n", stderr=""
            )
        return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")

    try:
        sys.modules.pop("system.hooks.pre_push", None)
        with (
            patch.object(subprocess, "run", side_effect=mock_subprocess_run),
            patch.object(sys, "argv", ["pre_push.py"]),
            pytest.raises(SystemExit) as exc,
        ):
            runpy.run_module("system.hooks.pre_push", run_name="__main__", alter_sys=True)
        assert exc.value.code == 0
    finally:
        if saved_module is not None:
            sys.modules["system.hooks.pre_push"] = saved_module
