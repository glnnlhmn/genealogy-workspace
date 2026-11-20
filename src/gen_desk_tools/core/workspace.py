"""Path: src/gen_desk_tools/core/workspace.py

Workspace root discovery, POSIX path normalization, and root containment guards.

Operational Role:
    Provides cross-platform path resolution primitives shared across all GenDesk
    Tools subpackages so Windows and POSIX environments evaluate workspace
    boundaries, relative paths, and directory traversal guards identically.

Functions:
    resolve_workspace_root: Locate the canonical workspace root directory.
    to_posix_rel: Convert a workspace path into a normalized POSIX relative string.
    ensure_within_root: Resolve a path and verify it does not escape the workspace root.
"""

from __future__ import annotations

from pathlib import Path

__version__ = "1.0.0+build.1"

__all__ = [
    "ensure_within_root",
    "resolve_workspace_root",
    "to_posix_rel",
]

ROOT_MARKERS: tuple[str, ...] = ("pyproject.toml", ".git")


def resolve_workspace_root(
    cfg_root: str | Path | None = None,
    start_dir: Path | None = None,
) -> Path:
    """Resolve the canonical workspace root directory.

    Ignores empty strings and '.' in cfg_root so default config values trigger
    upward marker discovery (pyproject.toml or .git) from start_dir or cwd.

    Raises:
        FileNotFoundError: If an explicit cfg_root does not exist or is not a directory.
    """
    anchor = (start_dir or Path.cwd()).resolve()

    # --- Explicit Root Override ---
    if cfg_root is not None and str(cfg_root).strip() not in ("", "."):
        candidate = Path(cfg_root)
        resolved = (
            candidate.resolve() if candidate.is_absolute() else (anchor / candidate).resolve()
        )
        if not resolved.is_dir():
            raise FileNotFoundError(f"Configured workspace root does not exist: {resolved}")
        return resolved

    # --- Upward Marker Discovery ---
    for directory in (anchor, *anchor.parents):
        if any((directory / marker).exists() for marker in ROOT_MARKERS):
            return directory

    return anchor


def to_posix_rel(path: Path, root: Path) -> str:
    """Convert a workspace path into a normalized forward-slash relative string.

    Raises:
        ValueError: If path resolves outside root.
    """
    resolved_root = root.resolve()
    resolved_path = ensure_within_root(path, resolved_root)
    return resolved_path.relative_to(resolved_root).as_posix()


def ensure_within_root(path: Path, root: Path) -> Path:
    """Resolve path (anchoring relative paths to root) and enforce root containment.

    Raises:
        ValueError: If the resolved path escapes root.
    """
    resolved_root = root.resolve()
    candidate = path if path.is_absolute() else resolved_root / path
    resolved_path = candidate.resolve()

    if not resolved_path.is_relative_to(resolved_root):
        raise ValueError(f"Path escapes workspace root ({resolved_root}): {resolved_path}")

    return resolved_path
