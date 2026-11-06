"""Path: tests/test_system/test_pre_commit.py

Test harness for staged-file and targeted pre-commit hook runner.
"""

from __future__ import annotations

import runpy
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

import system.hooks.pre_commit as pc
from system.hooks.pre_commit import (
    determine_test_targets,
    get_git_root,
    get_staged_files,
    main,
    run_ruff_checks,
    run_targeted_tests,
)

__version__ = "1.0.0+build.8"


# ==========================================================================
# GROUP 1: Git Root & Staged Files Discovery
# ==========================================================================


@pytest.mark.unit
def test_get_git_root_success(monkeypatch, tmp_path: Path):
    """Verify get_git_root returns resolved path from git rev-parse."""
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args=args[0], returncode=0, stdout=f"{tmp_path}\n"
        ),
    )
    root = get_git_root()
    assert root == tmp_path.resolve()


@pytest.mark.unit
def test_get_git_root_fallback_on_error(monkeypatch):
    """Verify get_git_root falls back to Path.cwd() when git command fails."""

    def raise_err(*args, **kwargs):
        raise subprocess.CalledProcessError(1, ["git", "rev-parse"])

    monkeypatch.setattr(subprocess, "run", raise_err)
    root = get_git_root()
    assert root == Path.cwd().resolve()


@pytest.mark.unit
def test_get_staged_files_returns_normalized_paths(monkeypatch, tmp_path: Path):
    """Verify get_staged_files returns normalized forward-slash relative paths."""
    git_output = "src\\gda\\core\\logging.py\ntests/test_gda/test_core.py\n"
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args=args[0], returncode=0, stdout=git_output
        ),
    )
    staged = get_staged_files(tmp_path)
    assert staged == ["src/gda/core/logging.py", "tests/test_gda/test_core.py"]


@pytest.mark.unit
def test_get_staged_files_error_returns_empty_list(monkeypatch, tmp_path: Path):
    """Verify get_staged_files returns an empty list when git diff fails."""

    def raise_err(*args, **kwargs):
        raise FileNotFoundError("git not found")

    monkeypatch.setattr(subprocess, "run", raise_err)
    staged = get_staged_files(tmp_path)
    assert staged == []


# ==========================================================================
# GROUP 2: Test Target Mapping & Filtering
# ==========================================================================


@pytest.mark.unit
def test_determine_test_targets_run_all(tmp_path: Path):
    """Verify run_all discovers all test_ subdirectories under tests/."""
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_gda").mkdir()
    (tests_dir / "test_system").mkdir()
    (tests_dir / "fixtures").mkdir()

    targets = determine_test_targets(tmp_path, run_all=True)
    assert targets == ["tests/test_gda", "tests/test_system"]


@pytest.mark.unit
def test_determine_test_targets_run_all_missing_tests_dir(tmp_path: Path):
    """Verify run_all returns empty list when tests directory does not exist."""
    targets = determine_test_targets(tmp_path, run_all=True)
    assert targets == []


@pytest.mark.unit
def test_determine_test_targets_explicit_targets(tmp_path: Path):
    """Verify explicit targets are mapped to tests/ directories."""
    explicit = ["tests/test_gda/test_core.py", "src/system/hooks", "gda", ""]
    targets = determine_test_targets(tmp_path, explicit_targets=explicit)
    assert "tests/test_gda/test_core.py" in targets
    assert "tests/test_system" in targets
    assert "tests/test_gda" in targets


@pytest.mark.unit
def test_determine_test_targets_explicit_empty_list(tmp_path: Path):
    """Verify empty explicit targets list bypasses loop cleanly."""
    targets = determine_test_targets(tmp_path, explicit_targets=[])
    assert targets == []


@pytest.mark.unit
def test_determine_test_targets_from_staged_files(tmp_path: Path):
    """Verify staged source and test files map to corresponding test targets."""
    staged = [
        "src/gda/core/logging.py",
        "tests/test_system/test_gsi.py",
        "docs/index.md",
    ]
    targets = determine_test_targets(tmp_path, staged_files=staged)
    assert "tests/test_gda" in targets
    assert "tests/test_system/test_gsi.py" in targets
    assert len(targets) == 2


@pytest.mark.unit
def test_determine_test_targets_empty_staged_files(tmp_path: Path):
    """Verify empty staged files list returns empty test targets list."""
    targets = determine_test_targets(tmp_path, staged_files=[])
    assert targets == []


# ==========================================================================
# GROUP 3: Ruff Verification Runners
# ==========================================================================


@pytest.mark.unit
def test_run_ruff_checks_empty_list_returns_zero(tmp_path: Path):
    """Verify run_ruff_checks returns 0 when no files are passed."""
    assert run_ruff_checks(tmp_path, []) == 0


@pytest.mark.integration
def test_run_ruff_checks_format_failure(monkeypatch, tmp_path: Path, capsys):
    """Verify run_ruff_checks returns non-zero when ruff format fails."""
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args=args[0], returncode=1),
    )
    code = run_ruff_checks(tmp_path, ["src/gda/core.py"])
    captured = capsys.readouterr()
    assert code == 1
    assert "Ruff formatting check failed" in captured.out


@pytest.mark.integration
def test_run_ruff_checks_lint_failure(monkeypatch, tmp_path: Path, capsys):
    """Verify run_ruff_checks returns non-zero when ruff check fails after formatting passes."""

    def mock_run(cmd, *args, **kwargs):
        if "format" in cmd:
            return subprocess.CompletedProcess(args=cmd, returncode=0)
        return subprocess.CompletedProcess(args=cmd, returncode=2)

    monkeypatch.setattr(subprocess, "run", mock_run)
    code = run_ruff_checks(tmp_path, ["src/gda/core.py"])
    captured = capsys.readouterr()
    assert code == 2
    assert "Ruff lint inspection failed" in captured.out


@pytest.mark.integration
def test_run_ruff_checks_all_pass(monkeypatch, tmp_path: Path):
    """Verify run_ruff_checks returns 0 when both format and lint succeed."""
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args=args[0], returncode=0),
    )
    assert run_ruff_checks(tmp_path, ["src/gda/core.py"]) == 0


# ==========================================================================
# GROUP 4: Targeted Test Dispatcher
# ==========================================================================


@pytest.mark.unit
def test_run_targeted_tests_empty_targets_returns_zero(tmp_path: Path, capsys):
    """Verify run_targeted_tests skips when targets list is empty."""
    code = run_targeted_tests(tmp_path, [])
    captured = capsys.readouterr()
    assert code == 0
    assert "No test targets mapped" in captured.out


@pytest.mark.unit
def test_run_targeted_tests_missing_on_disk_skips(tmp_path: Path, capsys):
    """Verify run_targeted_tests skips when targets do not exist on disk."""
    code = run_targeted_tests(tmp_path, ["tests/test_missing"])
    captured = capsys.readouterr()
    assert code == 0
    assert "Targeted test directories not found" in captured.out


@pytest.mark.integration
def test_run_targeted_tests_executes_pytest(monkeypatch, tmp_path: Path, capsys):
    """Verify run_targeted_tests executes pytest for existing targets."""
    target_dir = tmp_path / "tests" / "test_gda"
    target_dir.mkdir(parents=True)

    executed_cmd: list[str] = []

    def mock_run(cmd, *args, **kwargs):
        executed_cmd.extend(cmd)
        return subprocess.CompletedProcess(args=cmd, returncode=0)

    monkeypatch.setattr(subprocess, "run", mock_run)
    code = run_targeted_tests(tmp_path, ["tests/test_gda"])
    captured = capsys.readouterr()
    assert code == 0
    assert "Running targeted tests: tests/test_gda" in captured.out
    assert any("smoke or unit" in part for part in executed_cmd)


# ==========================================================================
# GROUP 5: CLI Main Entrypoint Dispatching
# ==========================================================================


@pytest.mark.smoke
def test_main_cli_staged_no_files_exits_zero(monkeypatch, tmp_path: Path):
    """Verify main exits 0 when no staged files are found."""
    monkeypatch.setattr("system.hooks.pre_commit.get_git_root", lambda: tmp_path)
    monkeypatch.setattr("system.hooks.pre_commit.get_staged_files", lambda root: [])

    with pytest.raises(SystemExit) as exc:
        main([])
    assert exc.value.code == 0


@pytest.mark.unit
def test_main_cli_ruff_failure_exits_with_code(monkeypatch, tmp_path: Path):
    """Verify main exits with ruff returncode if ruff checks fail."""
    monkeypatch.setattr("system.hooks.pre_commit.get_git_root", lambda: tmp_path)
    monkeypatch.setattr("system.hooks.pre_commit.run_ruff_checks", lambda root, targets: 1)

    with pytest.raises(SystemExit) as exc:
        main(["--all"])
    assert exc.value.code == 1


@pytest.mark.unit
def test_main_cli_no_tests_flag_bypasses_pytest(monkeypatch, tmp_path: Path):
    """Verify --no-tests flag exits 0 immediately after ruff checks."""
    monkeypatch.setattr("system.hooks.pre_commit.get_git_root", lambda: tmp_path)
    monkeypatch.setattr("system.hooks.pre_commit.run_ruff_checks", lambda root, targets: 0)

    with pytest.raises(SystemExit) as exc:
        main(["--all", "--no-tests"])
    assert exc.value.code == 0


@pytest.mark.integration
def test_main_cli_full_run_with_target_failure(monkeypatch, tmp_path: Path):
    """Verify main exits with test status if pytest fails on explicit targets."""
    monkeypatch.setattr("system.hooks.pre_commit.get_git_root", lambda: tmp_path)
    monkeypatch.setattr("system.hooks.pre_commit.run_ruff_checks", lambda root, targets: 0)
    monkeypatch.setattr("system.hooks.pre_commit.determine_test_targets", lambda **kw: ["t"])
    monkeypatch.setattr("system.hooks.pre_commit.run_targeted_tests", lambda root, targets: 3)

    with pytest.raises(SystemExit) as exc:
        main(["-t", "src/system"])
    assert exc.value.code == 3


@pytest.mark.integration
def test_main_cli_full_run_success(monkeypatch, tmp_path: Path):
    """Verify main completes successfully when all checks pass."""
    monkeypatch.setattr("system.hooks.pre_commit.get_git_root", lambda: tmp_path)
    monkeypatch.setattr("system.hooks.pre_commit.get_staged_files", lambda root: ["src/a.py"])
    monkeypatch.setattr("system.hooks.pre_commit.run_ruff_checks", lambda root, targets: 0)
    monkeypatch.setattr("system.hooks.pre_commit.determine_test_targets", lambda **kw: ["t"])
    monkeypatch.setattr("system.hooks.pre_commit.run_targeted_tests", lambda root, targets: 0)

    with pytest.raises(SystemExit) as exc:
        main([])
    assert exc.value.code == 0


@pytest.mark.smoke
@pytest.mark.unit
def test_pre_commit_module_main_entrypoint():
    """Verify pre_commit __main__ block dispatches cleanly when executed as a module."""
    saved_module = sys.modules.get("system.hooks.pre_commit")
    try:
        sys.modules.pop("system.hooks.pre_commit", None)
        with (
            patch.object(pc, "main", side_effect=SystemExit(0)),
            patch.object(sys, "argv", ["pre_commit.py", "--no-tests"]),
            pytest.raises(SystemExit) as exc,
        ):
            runpy.run_module("system.hooks.pre_commit", run_name="__main__", alter_sys=True)
        assert exc.value.code == 0
    finally:
        if saved_module is not None:
            sys.modules["system.hooks.pre_commit"] = saved_module
