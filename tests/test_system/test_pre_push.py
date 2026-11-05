"""Path: tests/test_system/test_pre_push.py

Test harness for pre-push Git hook orchestrator.
"""

from __future__ import annotations

import runpy
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

import system.hooks.pre_push as pp
from system.hooks.pre_push import (
    get_current_branch,
    main,
    run_pre_push,
)

__version__ = "1.0.0+build.8"


# ==========================================================================
# GROUP 1: Branch Inspection & Protection
# ==========================================================================


@pytest.mark.unit
def test_get_current_branch_returns_stdout(monkeypatch, tmp_path: Path):
    """Verify get_current_branch retrieves and strips the current Git branch name."""
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args=args[0], returncode=0, stdout="feature/my-branch\n"
        ),
    )
    branch = get_current_branch(tmp_path)
    assert branch == "feature/my-branch"


@pytest.mark.unit
def test_get_current_branch_returns_empty_on_error(monkeypatch, tmp_path: Path):
    """Verify get_current_branch safely returns an empty string on error."""

    def raise_err(*args, **kwargs):
        raise subprocess.CalledProcessError(1, ["git"])

    monkeypatch.setattr(subprocess, "run", raise_err)
    assert get_current_branch(tmp_path) == ""


@pytest.mark.regression
def test_run_pre_push_rejects_protected_branch_without_override(
    monkeypatch, tmp_path: Path, capsys
):
    """Verify pushing directly to a protected branch is rejected with return code 1."""
    monkeypatch.setattr("system.hooks.pre_push.get_current_branch", lambda root: "main")

    exit_code = run_pre_push(repo_root=tmp_path, allow_protected=False)
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Direct push to protected branch 'main' is prohibited" in captured.out


@pytest.mark.unit
def test_run_pre_push_allows_protected_branch_with_explicit_override(monkeypatch, tmp_path: Path):
    """Verify pushing to a protected branch succeeds when allow_protected=True and tests skipped."""
    monkeypatch.setattr("system.hooks.pre_push.get_current_branch", lambda root: "main")

    exit_code = run_pre_push(repo_root=tmp_path, allow_protected=True, skip_tests=True)
    assert exit_code == 0


# ==========================================================================
# GROUP 2: Test Suite Execution & Enforcement
# ==========================================================================


@pytest.mark.integration
def test_run_pre_push_fails_on_test_failure(monkeypatch, tmp_path: Path, capsys):
    """Verify pre-push runner fails and prevents push when the test suite fails."""
    monkeypatch.setattr("system.hooks.pre_push.get_current_branch", lambda root: "feature/schema")
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args=args[0], returncode=2),
    )

    exit_code = run_pre_push(repo_root=tmp_path, skip_tests=False)
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "Test suite failure detected prior to remote push" in captured.out


@pytest.mark.integration
def test_run_pre_push_succeeds_when_tests_pass(monkeypatch, tmp_path: Path, capsys):
    """Verify pre-push runner succeeds when pytest exits with 0."""
    monkeypatch.setattr("system.hooks.pre_push.get_current_branch", lambda root: "feature/schema")
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args=args[0], returncode=0),
    )

    exit_code = run_pre_push(repo_root=tmp_path, skip_tests=False)
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Pre-push checks passed successfully" in captured.out


# ==========================================================================
# GROUP 3: CLI Gateway & Smoke Execution
# ==========================================================================


@pytest.mark.smoke
def test_main_cli_execution(monkeypatch):
    """Verify CLI main entrypoint executes correctly with arguments."""
    monkeypatch.setattr(
        "system.hooks.pre_push.run_pre_push",
        lambda allow_protected, skip_tests: 0,
    )

    with pytest.raises(SystemExit) as exc:
        main(["--skip-tests", "--allow-protected", "-v"])
    assert exc.value.code == 0


@pytest.mark.smoke
@pytest.mark.unit
def test_pre_push_module_main_entrypoint():
    """Verify pre_push __main__ block dispatches cleanly when executed as a module."""
    saved_module = sys.modules.get("system.hooks.pre_push")
    try:
        sys.modules.pop("system.hooks.pre_push", None)
        with (
            patch.object(pp, "main", side_effect=SystemExit(0)),
            patch.object(sys, "argv", ["pre_push.py", "--skip-tests"]),
            pytest.raises(SystemExit) as exc,
        ):
            runpy.run_module("system.hooks.pre_push", run_name="__main__", alter_sys=True)
        assert exc.value.code == 0
    finally:
        if saved_module is not None:
            sys.modules["system.hooks.pre_push"] = saved_module
