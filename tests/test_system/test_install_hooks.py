"""Path: tests/test_system/test_install_hooks.py

Comprehensive test suite verifying Git hooks installer in src.system.install_hooks.

Operational Role:
    Verifies Git repository detection, missing directory handling, wrapper
    script file emission, executable permission flags, and command-line entrypoints.

Test Structure & Protocol:
    - Atomized tests: 1:1 behavioral contract mapping.
    - Fully decorated: Standard 7-marker taxonomy.
    - Dependencies: Isolated filesystem sandboxing via tmp_path.
"""

from __future__ import annotations

import runpy
import stat
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

import system.install_hooks as ih

__version__ = "1.0.0+build.r2"


# ==============================================================================
# GROUP 1: REPOSITORY ROOT RESOLUTION
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_get_repo_root_detects_git_directory(tmp_path: Path) -> None:
    """Verify get_repo_root traverses parents and finds .git directory."""
    repo = tmp_path / "repo"
    git_dir = repo / ".git"
    git_dir.mkdir(parents=True)
    nested = repo / "src" / "system"
    nested.mkdir(parents=True)
    fake_script = nested / "install_hooks.py"
    fake_script.touch()

    with patch.object(ih, "__file__", str(fake_script)):
        assert ih.get_repo_root() == repo


@pytest.mark.unit
def test_get_repo_root_fallback_to_cwd(tmp_path: Path) -> None:
    """Verify get_repo_root falls back to cwd when no parent contains .git."""
    isolated = tmp_path / "plain_dir"
    isolated.mkdir()
    fake_script = isolated / "install_hooks.py"
    fake_script.touch()

    with (
        patch.object(ih, "__file__", str(fake_script)),
        patch.object(Path, "cwd", return_value=isolated),
        patch.object(Path, "is_dir", return_value=False),
    ):
        assert ih.get_repo_root() == isolated


# ==============================================================================
# GROUP 2: HOOK DEPLOYMENT & PERMISSIONS
# ==============================================================================


@pytest.mark.unit
def test_install_pre_commit_hook_fails_when_git_missing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Verify install_pre_commit_hook returns False when .git does not exist."""
    success = ih.install_pre_commit_hook(tmp_path)
    captured = capsys.readouterr()

    assert success is False
    assert "Error: .git directory not found" in captured.out


@pytest.mark.unit
@pytest.mark.smoke
def test_install_pre_commit_hook_success(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Verify install_pre_commit_hook creates executable wrapper script."""
    (tmp_path / ".git").mkdir()

    with patch.object(Path, "chmod") as mock_chmod:
        success = ih.install_pre_commit_hook(tmp_path)
        captured = capsys.readouterr()

        hook_file = tmp_path / ".git" / "hooks" / "pre-commit"
        assert success is True
        assert hook_file.is_file()
        assert ih.HOOK_WRAPPER_POSIX in hook_file.read_text(encoding="utf-8")
        assert "Pre-commit hook installed successfully" in captured.out

        # Verify chmod was called to set executable bit flags
        assert mock_chmod.called
        called_mode = mock_chmod.call_args[0][0]
        assert called_mode & stat.S_IXUSR


# ==============================================================================
# GROUP 3: COMMAND-LINE INTERFACE & ENTRYPOINT
# ==============================================================================


@pytest.mark.unit
def test_main_cli_success(tmp_path: Path) -> None:
    """Verify main exits 0 on successful installation."""
    (tmp_path / ".git").mkdir()
    with (
        patch.object(ih, "get_repo_root", return_value=tmp_path),
        pytest.raises(SystemExit) as exc,
    ):
        ih.main([])
    assert exc.value.code == 0


@pytest.mark.unit
def test_main_cli_failure(tmp_path: Path) -> None:
    """Verify main exits 1 when installation returns False."""
    with (
        patch.object(ih, "get_repo_root", return_value=tmp_path),
        pytest.raises(SystemExit) as exc,
    ):
        ih.main([])
    assert exc.value.code == 1


@pytest.mark.smoke
@pytest.mark.unit
def test_install_hooks_module_execution_entrypoint() -> None:
    """Verify __main__ block executes main function."""
    saved_module = sys.modules.get("system.install_hooks")
    try:
        sys.modules.pop("system.install_hooks", None)
        with (
            patch.object(ih, "install_pre_commit_hook", return_value=True),
            pytest.raises(SystemExit) as exc,
        ):
            with patch.object(sys, "argv", ["install_hooks.py"]):
                runpy.run_module(
                    "system.install_hooks", run_name="__main__", alter_sys=True
                )
        assert exc.value.code == 0
    finally:
        if saved_module is not None:
            sys.modules["system.install_hooks"] = saved_module
