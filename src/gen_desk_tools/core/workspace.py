"""Path: src/gen_desk_tools/core/workspace.py

Workspace root discovery, POSIX path normalization, file discovery, and report routing.

Operational Role:
    Provides cross-platform path resolution primitives and canonical subsystem
    target mappings shared across all GenDesk Tools subpackages so Windows and
    POSIX environments evaluate workspace boundaries, relative paths,
    exclusion-aware file discovery, and report output directories identically.

Functions:
    resolve_workspace_root: Locate the canonical workspace root directory.
    to_posix_rel: Convert a workspace path into a normalized POSIX relative string.
    ensure_within_root: Resolve a path and verify it does not escape the workspace root.
    iter_workspace_files: Return sorted files under a path excluding cache/VCS dirs.
    resolve_report_path: Resolve a report output path under the configured reports_dir.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

__version__ = "1.0.0+build.4"

__all__ = [
    "MANDATORY_EXCLUSIONS",
    "MODE_TARGETS",
    "ensure_within_root",
    "iter_workspace_files",
    "resolve_report_path",
    "resolve_workspace_root",
    "to_posix_rel",
]

ROOT_MARKERS: tuple[str, ...] = ("pyproject.toml", ".git")

# Canonical mode -> (source relative path, matching tests relative path)
MODE_TARGETS: dict[str, tuple[str, str]] = {
    "gda": ("src/gda", "tests/test_gda"),
    "ancestry_desk": ("src/ancestry_desk", "tests/test_ancestry_desk"),
    "gd_tools": ("src/gen_desk_tools", "tests/test_gen_desk_tools"),
    "system": ("src/system", "tests/test_system"),
    "cli": ("src/cli", "tests/test_cli"),
    "src": ("src", "tests"),
}

MANDATORY_EXCLUSIONS: frozenset[str] = frozenset(
    {
        ".git",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".tox",
        ".venv",
        "__pycache__",
        "node_modules",
    }
)


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


def _matches_workspace_file(
    item: Path,
    target: Path,
    suffixes: tuple[str, ...] | None,
    exclusions: frozenset[str],
) -> bool:
    """Return True if item is a non-excluded file matching suffixes."""
    if not item.is_file():
        return False
    if item != target and any(part in exclusions for part in item.relative_to(target).parts):
        return False
    return suffixes is None or item.suffix in suffixes


def iter_workspace_files(
    target: Path,
    *,
    suffixes: tuple[str, ...] | None = None,
    exclusions: frozenset[str] = MANDATORY_EXCLUSIONS,
) -> tuple[Path, ...]:
    """Return sorted files under target while filtering excluded directory names.

    Returns an empty tuple when target does not exist. When target is a single
    file, returns (target,) if it matches suffixes (or suffixes is None).

    Args:
        suffixes: Optional tuple of allowed file suffixes (e.g., (".py",)).
        exclusions: Directory or path component names to skip during traversal.
    """
    if not target.exists():
        return ()

    if target.is_file():
        return (target,) if _matches_workspace_file(target, target, suffixes, exclusions) else ()

    found = [
        item
        for item in target.rglob("*")
        if _matches_workspace_file(item, target, suffixes, exclusions)
    ]
    return tuple(sorted(found))


def resolve_report_path(
    root: Path,
    cfg: Mapping[str, Any],
    filename: str,
    *,
    override_dir: Path | None = None,
    create_dir: bool = True,
) -> Path:
    """Resolve a report output path under the configured reports directory.

    Uses override_dir when provided (anchoring relative overrides to root),
    otherwise reads workspace.reports_dir from cfg (defaulting to "reports").

    Args:
        override_dir: Optional directory override bypassing cfg["workspace"]["reports_dir"].
        create_dir: When True, creates the destination directory if it does not exist.
    """
    if override_dir is not None:
        report_dir = override_dir if override_dir.is_absolute() else root / override_dir
    else:
        reports_rel = str(cfg.get("workspace", {}).get("reports_dir", "reports"))
        report_dir = root / reports_rel

    if create_dir:
        report_dir.mkdir(parents=True, exist_ok=True)

    return report_dir / filename
