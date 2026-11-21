"""Path: src/gen_desk_tools/structure/scanner.py

Directory tree scanner and report generator for GenDesk Structure (gd-struct).

Operational Role:
    Traverses workspace directories or Git-tracked/unignored files up to a
    configured depth (default 7), filters mandatory noise directories, and
    writes standardized tree reports atomically into the configured reports/
    directory via gen_desk_tools.core primitives.

Functions:
    build_tree: Recursively collect sorted directory tree lines up to max_depth.
    build_git_tree: Collect non-gitignored workspace paths via git ls-files.
    generate_structure_report: Generate and write a structure report for a target mode.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from gen_desk_tools.core.backup import atomic_write_text
from gen_desk_tools.core.process import run_command
from gen_desk_tools.core.workspace import (
    MANDATORY_EXCLUSIONS as CORE_EXCLUSIONS,
)
from gen_desk_tools.core.workspace import (
    MODE_TARGETS,
    resolve_report_path,
)

__version__ = "1.0.0+build.3"

__all__ = [
    "DEFAULT_MAX_DEPTH",
    "MANDATORY_EXCLUSIONS",
    "MODE_TARGETS",
    "build_git_tree",
    "build_tree",
    "generate_structure_report",
]

DEFAULT_MAX_DEPTH: int = 7

MANDATORY_EXCLUSIONS: frozenset[str] = CORE_EXCLUSIONS | frozenset({"pytest_tmp", "temp"})


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
    """Collect sorted non-gitignored workspace paths up to max_depth via git ls-files.

    Raises:
        RuntimeError: If git ls-files fails or git is unavailable.
    """
    res = run_command(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=workspace_root,
        runner=subprocess.run,
    )
    if not res.ok:
        detail = res.error or res.stderr.strip() or f"exit code {res.returncode}"
        raise RuntimeError(f"Failed to query git-tracked/unignored files: {detail}")

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
    """Generate a workspace structure report and write it atomically to reports_dir."""
    root = Path(workspace_root).resolve()
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

    report_path = resolve_report_path(root, {}, filename, override_dir=Path(reports_dir))
    content = "\n".join(output_lines) + ("\n" if output_lines else "")
    atomic_write_text(report_path, content)
    return report_path, len(output_lines)
