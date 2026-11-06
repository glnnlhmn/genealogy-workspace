"""Path: tests/test_system/test_install_hooks.py

Comprehensive test suite verifying Git hooks installer in src.system.install_hooks.

Operational Role:
    Verifies Git repository detection, missing directory handling, wrapper
    script file emission, executable permission flags, and command-line entrypoints.
"""

from __future__ import annotations

import runpy
import stat
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

import system.install_hooks as ih

__version__ = "1.0.0+build.11"


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

    with (
        patch.object(
            subprocess,
            "run",
            side_effect=subprocess.CalledProcessError(1, ["git"]),
        ),
        patch.object(Path, "cwd", return_value=nested),
    ):
        assert ih.get_repo_root() == repo


@pytest.mark.unit
def test_get_repo_root_via_subprocess_success(tmp_path: Path) -> None:
    """Verify get_repo_root resolves path via git rev-parse when available."""
    with patch.object(
        subprocess,
        "run",
        return_value=subprocess.CompletedProcess(
            args=["git"], returncode=0, stdout=f"{tmp_path}\n"
        ),
    ):
        assert ih.get_repo_root() == tmp_path.resolve()


@pytest.mark.unit
def test_get_repo_root_fallback_to_cwd(tmp_path: Path) -> None:
    """Verify get_repo_root falls back to cwd when no parent contains .git."""
    isolated = tmp_path / "plain_dir"
    isolated.mkdir()

    original_is_dir = Path.is_dir

    def mock_is_dir(self: Path) -> bool:
        if self.name == ".git":
            return False
        return original_is_dir(self)

    with (
        patch.object(
            subprocess,
            "run",
            side_effect=subprocess.CalledProcessError(1, ["git"]),
        ),
        patch.object(Path, "cwd", return_value=isolated),
        patch.object(Path, "is_dir", mock_is_dir),
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

        assert mock_chmod.called
        called_mode = mock_chmod.call_args[0][0]
        assert called_mode & stat.S_IXUSR


@pytest.mark.regression
def test_install_pre_commit_hook_os_error_handling(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Verify install_pre_commit_hook handles OSError gracefully."""
    (tmp_path / ".git").mkdir()
    with patch.object(Path, "write_text", side_effect=OSError("Disk write denied")):
        success = ih.install_pre_commit_hook(tmp_path)
        captured = capsys.readouterr()
        assert success is False
        assert "Disk write denied" in captured.out


@pytest.mark.unit
def test_install_pre_push_hook_fails_when_git_missing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Verify install_pre_push_hook returns False when .git does not exist."""
    success = ih.install_pre_push_hook(tmp_path)
    captured = capsys.readouterr()

    assert success is False
    assert "Error: .git directory not found" in captured.out


@pytest.mark.unit
def test_install_pre_push_hook_success(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Verify install_pre_push_hook creates executable pre-push wrapper script."""
    (tmp_path / ".git").mkdir()

    with patch.object(Path, "chmod") as mock_chmod:
        success = ih.install_pre_push_hook(tmp_path)
        captured = capsys.readouterr()

        hook_file = tmp_path / ".git" / "hooks" / "pre-push"
        assert success is True
        assert hook_file.is_file()
        assert ih.HOOK_WRAPPER_PRE_PUSH in hook_file.read_text(encoding="utf-8")
        assert "Pre-push hook installed successfully" in captured.out

        assert mock_chmod.called
        called_mode = mock_chmod.call_args[0][0]
        assert called_mode & stat.S_IXUSR


@pytest.mark.regression
def test_install_pre_push_hook_os_error_handling(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Verify install_pre_push_hook handles OSError gracefully."""
    (tmp_path / ".git").mkdir()
    with patch.object(Path, "write_text", side_effect=OSError("Disk write denied")):
        success = ih.install_pre_push_hook(tmp_path)
        captured = capsys.readouterr()
        assert success is False
        assert "Disk write denied" in captured.out


@pytest.mark.unit
def test_install_hooks_batch_success(tmp_path: Path) -> None:
    """Verify install_hooks deploys both hooks and returns paths."""
    (tmp_path / ".git").mkdir()
    installed = ih.install_hooks(workspace_root=tmp_path)
    assert len(installed) == 2
    assert any("pre-commit" in str(p) for p in installed)
    assert any("pre-push" in str(p) for p in installed)


@pytest.mark.regression
@pytest.mark.unit
def test_install_hooks_partial_commit_false_push_true(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Verify install_hooks skips pre-commit path when pre-commit install fails."""
    (tmp_path / ".git").mkdir()
    monkeypatch.setattr(ih, "install_pre_commit_hook", lambda root: False)
    monkeypatch.setattr(ih, "install_pre_push_hook", lambda root: True)

    installed = ih.install_hooks(workspace_root=tmp_path)
    assert len(installed) == 1
    assert "pre-push" in str(installed[0])


@pytest.mark.regression
@pytest.mark.unit
def test_install_hooks_partial_commit_true_push_false(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Verify install_hooks skips pre-push path when pre-push install fails."""
    (tmp_path / ".git").mkdir()
    monkeypatch.setattr(ih, "install_pre_commit_hook", lambda root: True)
    monkeypatch.setattr(ih, "install_pre_push_hook", lambda root: False)

    installed = ih.install_hooks(workspace_root=tmp_path)
    assert len(installed) == 1
    assert "pre-commit" in str(installed[0])


@pytest.mark.unit
def test_install_hooks_missing_git_raises_not_found(tmp_path: Path) -> None:
    """Verify install_hooks raises FileNotFoundError if .git directory is missing."""
    with pytest.raises(FileNotFoundError, match="Git root not found"):
        ih.install_hooks(workspace_root=tmp_path)


# ==============================================================================
# GROUP 3: COMMAND-LINE INTERFACE & BRANCH COVERAGE
# ==============================================================================


@pytest.mark.unit
def test_main_cli_success(tmp_path: Path) -> None:
    """Verify main exits 0 when both hooks install successfully."""
    (tmp_path / ".git").mkdir()
    with (
        patch.object(ih, "get_repo_root", return_value=tmp_path),
        patch.object(ih, "install_pre_commit_hook", return_value=True),
        patch.object(ih, "install_pre_push_hook", return_value=True),
        pytest.raises(SystemExit) as exc,
    ):
        ih.main([])
    assert exc.value.code == 0


@pytest.mark.unit
def test_main_cli_failure_commit_false(tmp_path: Path) -> None:
    """Verify main exits 1 when pre_commit fails."""
    with (
        patch.object(ih, "get_repo_root", return_value=tmp_path),
        patch.object(ih, "install_pre_commit_hook", return_value=False),
        pytest.raises(SystemExit) as exc,
    ):
        ih.main(["-v"])
    assert exc.value.code == 1


@pytest.mark.regression
@pytest.mark.unit
def test_main_cli_failure_push_false(tmp_path: Path) -> None:
    """Verify main exits 1 when pre_commit succeeds but pre_push fails."""
    with (
        patch.object(ih, "get_repo_root", return_value=tmp_path),
        patch.object(ih, "install_pre_commit_hook", return_value=True),
        patch.object(ih, "install_pre_push_hook", return_value=False),
        pytest.raises(SystemExit) as exc,
    ):
        ih.main([])
    assert exc.value.code == 1


@pytest.mark.smoke
@pytest.mark.unit
def test_install_hooks_module_execution_entrypoint() -> None:
    """Verify __main__ block dispatches main when executed directly."""
    saved_module = sys.modules.get("system.install_hooks")
    try:
        sys.modules.pop("system.install_hooks", None)
        with (
            patch.object(ih, "main", side_effect=SystemExit(0)),
            patch.object(sys, "argv", ["install_hooks.py"]),
            pytest.raises(SystemExit) as exc,
        ):
            runpy.run_module("system.install_hooks", run_name="__main__", alter_sys=True)
        assert exc.value.code == 0
    finally:
        if saved_module is not None:
            sys.modules["system.install_hooks"] = saved_module
