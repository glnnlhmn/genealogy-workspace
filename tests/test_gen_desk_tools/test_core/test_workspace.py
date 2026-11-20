"""Path: tests/test_gen_desk_tools/test_core/test_workspace.py

Unit, regression, and integration tests for gen_desk_tools.core.workspace.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from gen_desk_tools.core.workspace import (
    ensure_within_root,
    resolve_workspace_root,
    to_posix_rel,
)

__version__ = "1.0.0+build.1"

# ==========================================================================
# GROUP 1: Smoke & Primary Entrypoints
# Note: End-to-end root discovery from a nested workspace subdirectory.
# ==========================================================================


@pytest.mark.smoke
@pytest.mark.integration
def test_resolve_workspace_root_nested_subdir_finds_pyproject_marker(
    gdt_workspace: Path,
) -> None:
    """Verify resolve_workspace_root walks upward to the directory containing pyproject.toml."""
    nested = gdt_workspace / "src" / "gen_desk_tools"
    assert resolve_workspace_root(start_dir=nested) == gdt_workspace.resolve()


# ==========================================================================
# GROUP 2: Core Logic & Happy Paths
# Note: Standard root overrides, POSIX path conversion, and containment checks.
# ==========================================================================


@pytest.mark.unit
def test_resolve_workspace_root_explicit_absolute_path_returns_target(
    tmp_path: Path,
) -> None:
    """Verify an explicit absolute cfg_root directory is returned directly."""
    custom_root = tmp_path / "custom_repo"
    custom_root.mkdir()
    assert resolve_workspace_root(cfg_root=custom_root) == custom_root.resolve()


@pytest.mark.unit
def test_resolve_workspace_root_explicit_relative_path_resolves_against_start_dir(
    tmp_path: Path,
) -> None:
    """Verify an explicit relative cfg_root resolves relative to start_dir."""
    sub_root = tmp_path / "workspace_a"
    sub_root.mkdir()
    assert resolve_workspace_root(cfg_root="workspace_a", start_dir=tmp_path) == sub_root.resolve()


@pytest.mark.unit
def test_to_posix_rel_relative_path_returns_forward_slash_string(
    gdt_workspace: Path,
) -> None:
    """Verify relative workspace paths normalize to POSIX forward-slash strings."""
    rel = Path("src") / "gen_desk_tools" / "core" / "workspace.py"
    assert to_posix_rel(rel, gdt_workspace) == "src/gen_desk_tools/core/workspace.py"


@pytest.mark.unit
def test_to_posix_rel_absolute_path_returns_forward_slash_string(
    gdt_workspace: Path,
) -> None:
    """Verify absolute paths inside the workspace normalize to POSIX relative strings."""
    target = gdt_workspace / "src" / "gda" / "core.py"
    assert to_posix_rel(target, gdt_workspace) == "src/gda/core.py"


@pytest.mark.unit
def test_ensure_within_root_valid_relative_path_returns_resolved_path(
    gdt_workspace: Path,
) -> None:
    """Verify ensure_within_root resolves relative paths anchored to the workspace root."""
    resolved = ensure_within_root(Path("logs/tool.log"), gdt_workspace)
    assert resolved == (gdt_workspace / "logs" / "tool.log").resolve()


# ==========================================================================
# GROUP 3: Edge Cases & Boundary Conditions
# Note: Blank/dot cfg_root fallbacks, .git marker discovery, and markerless dirs.
# ==========================================================================


@pytest.mark.regression
def test_resolve_workspace_root_dot_or_blank_triggers_marker_discovery(
    gdt_workspace: Path,
) -> None:
    """Verify '.' and blank cfg_root values fall through to upward marker discovery."""
    nested = gdt_workspace / "src" / "gda"
    assert resolve_workspace_root(cfg_root=".", start_dir=nested) == gdt_workspace.resolve()
    assert resolve_workspace_root(cfg_root="   ", start_dir=nested) == gdt_workspace.resolve()


@pytest.mark.regression
def test_resolve_workspace_root_git_marker_without_pyproject(tmp_path: Path) -> None:
    """Verify .git acts as a valid workspace root sentinel when pyproject.toml is absent."""
    repo = tmp_path / "git_only_repo"
    nested = repo / "a" / "b"
    nested.mkdir(parents=True)
    (repo / ".git").mkdir()

    assert resolve_workspace_root(start_dir=nested) == repo.resolve()


@pytest.mark.regression
def test_resolve_workspace_root_no_markers_falls_back_to_start_dir(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify resolve_workspace_root returns the anchor directory when no markers exist."""
    isolated = tmp_path / "orphan_dir"
    isolated.mkdir()
    # Patch Path.cwd so the default start_dir=None branch is also exercised hermetically
    monkeypatch.chdir(isolated)

    assert resolve_workspace_root() == isolated.resolve()


# ==========================================================================
# GROUP 4: Error Handling & Validation Failures
# Note: Missing explicit roots and directory-traversal escape guards.
# ==========================================================================


@pytest.mark.regression
def test_resolve_workspace_root_missing_explicit_path_raises_file_not_found(
    tmp_path: Path,
) -> None:
    """Verify a nonexistent explicit cfg_root raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError, match="Configured workspace root does not exist"):
        resolve_workspace_root(cfg_root=tmp_path / "does_not_exist")


@pytest.mark.regression
def test_ensure_within_root_parent_traversal_raises_value_error(
    gdt_workspace: Path,
) -> None:
    """Verify relative parent traversal escaping the workspace root raises ValueError."""
    with pytest.raises(ValueError, match="Path escapes workspace root"):
        ensure_within_root(Path("../../outside.txt"), gdt_workspace)


@pytest.mark.regression
def test_to_posix_rel_outside_root_raises_value_error(
    gdt_workspace: Path,
    tmp_path: Path,
) -> None:
    """Verify to_posix_rel rejects absolute paths outside the workspace root."""
    external = tmp_path.parent / "external_file.py"
    with pytest.raises(ValueError, match="Path escapes workspace root"):
        to_posix_rel(external, gdt_workspace)
