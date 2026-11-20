"""Path: src/gen_desk_tools/structure/scanner.py

Directory tree scanner and report generator for GenDesk Structure (gd-struct).

Operational Role:
    Traverses workspace directories or Git-tracked/unignored files up to a
    configured depth (default 7), filters mandatory noise directories, and
    writes standardized tree reports into the configured reports/ directory.

Functions:
    build_tree: Recursively collect sorted directory tree lines up to max_depth.
    build_git_tree: Collect non-gitignored workspace paths via git ls-files.
    generate_structure_report: Generate and write a structure report for a target mode.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

__version__ = "1.0.0+build.1"

__all__ = [
    "DEFAULT_MAX_DEPTH",
    "MANDATORY_EXCLUSIONS",
    "MODE_TARGETS",
    "build_git_tree",
    "build_tree",
    "generate_structure_report",
]

DEFAULT_MAX_DEPTH: int = 7

MANDATORY_EXCLUSIONS: frozenset[str] = frozenset(
    {
        ".git",
        ".pytest_cache",
        ".ruff_cache",
        ".venv",
        "__pycache__",
        "pytest_tmp",
        "temp",
    }
)

# Maps mode name -> (source relative path, matching tests relative path)
MODE_TARGETS: dict[str, tuple[str, str]] = {
    "gda": ("src/gda", "tests/test_gda"),
    "ancestry_desk": ("src/ancestry_desk", "tests/test_ancestry_desk"),
    "gd_tools": ("src/gen_desk_tools", "tests/test_gen_desk_tools"),
    "system": ("src/system", "tests/test_system"),
    "cli": ("src/cli", "tests/test_cli"),
    "src": ("src", "tests"),
}


def build_tree(
    target_dir: Path,
    prefix: str = "",
    max_depth: int = DEFAULT_MAX_DEPTH,
    current_depth: int = 0,
    excluded_names: set[str] | None = None,
) -> list[str]:
    """Recursively collect sorted directory tree lines up to max_depth."""
    if current_depth >= max_depth:
        return []

    exclusions = set(MANDATORY_EXCLUSIONS)
    if excluded_names:
        exclusions.update(excluded_names)

    try:
        entries = sorted(target_dir.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
    except (PermissionError, FileNotFoundError):
        return []

    lines: list[str] = []
    for entry in entries:
        if entry.name in exclusions or entry.name.startswith("."):
            continue

        rel_str = f"{prefix}/{entry.name}" if prefix else f"./{entry.name}"
        lines.append(rel_str)

        if entry.is_dir():
            lines.extend(
                build_tree(
                    entry,
                    prefix=rel_str,
                    max_depth=max_depth,
                    current_depth=current_depth + 1,
                    excluded_names=exclusions,
                )
            )
    return lines


def build_git_tree(
    workspace_root: Path,
    max_depth: int = DEFAULT_MAX_DEPTH,
) -> list[str]:
    """Collect sorted non-gitignored workspace paths up to max_depth via git ls-files."""
    try:
        res = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
            cwd=str(workspace_root),
            capture_output=True,
            text=True,
            check=True,
        )
    except (subprocess.CalledProcessError, OSError) as exc:
        raise RuntimeError(f"Failed to query git-tracked/unignored files: {exc}") from exc

    paths: set[str] = set()
    for raw_line in res.stdout.splitlines():
        rel = raw_line.strip().replace("\\", "/")
        if not rel:
            continue
        parts = rel.split("/")
        limit = min(len(parts), max_depth)
        for depth in range(1, limit + 1):
            paths.add("./" + "/".join(parts[:depth]))

    return sorted(paths)


def generate_structure_report(
    mode: str = "gda",
    *,
    include_tests: bool = False,
    workspace_root: Path | str = ".",
    reports_dir: Path | str = "reports",
    max_depth: int = DEFAULT_MAX_DEPTH,
) -> tuple[Path, int]:
    """Generate a workspace structure report and write it to reports_dir."""
    root = Path(workspace_root).resolve()
    out_dir = Path(reports_dir)
    resolved_out = out_dir if out_dir.is_absolute() else (root / out_dir)
    resolved_out.mkdir(parents=True, exist_ok=True)

    output_lines: list[str] = []

    if mode == "all":
        output_lines.append(".")
        output_lines.extend(build_tree(root, prefix=".", max_depth=max_depth))
        filename = "GenDeskStructure_all.txt"
    elif mode == "git":
        output_lines.append(".")
        output_lines.extend(build_git_tree(root, max_depth=max_depth))
        filename = "GenDeskStructure_git.txt"
    elif mode in MODE_TARGETS:
        src_rel, test_rel = MODE_TARGETS[mode]
        targets = [src_rel, test_rel] if include_tests else [src_rel]
        for rel in targets:
            target_path = root / rel
            if target_path.exists():
                output_lines.append(f"./{rel}")
                output_lines.extend(build_tree(target_path, prefix=f"./{rel}", max_depth=max_depth))
        suffix = "_tests" if include_tests else ""
        filename = f"GenDeskStructure_{mode}{suffix}.txt"
    else:
        valid = ", ".join(sorted([*MODE_TARGETS, "all", "git"]))
        raise ValueError(f"Unknown structure mode: '{mode}'. Expected one of: {valid}.")

    report_path = resolved_out / filename
    payload = "\n".join(output_lines) + ("\n" if output_lines else "")
    report_path.write_text(payload, encoding="utf-8")
    return report_path, len(output_lines)
