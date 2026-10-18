"""Path: src/system/check_structure.py

Directory tree inspection utility for workspace auditing and reporting.

Operational Role:
    Traverses the workspace hierarchy, ignores transient caches and virtual
    environments, and emits an aligned directory tree. Supports filtered
    default scanning (src/ and tests/) or full root-down inspection via flags.
    Writes silently to default report files without emitting tree content
    to stdout.

Usage:
    python src/system/check_structure.py [--all] [--level N] [--output PATH]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

__version__ = "0.0.1+build.r4"

# Paths ignored during traversal
IGNORED_DIRS: set[str] = {
    ".git",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "gtemp",
    "pytest_tmp",
    "temp",
}

DEFAULT_FILTERED_REPORT: str = "reports/GenDeskStructure.txt"
DEFAULT_COMPLETE_REPORT: str = "reports/GenDeskStructureComplete.txt"


def build_tree(
    target_dir: Path,
    prefix: str = "",
    max_depth: int = 5,
    current_depth: int = 0,
) -> list[str]:
    """Recursively collect sorted directory lines up to max_depth.

    Args:
        target_dir: Directory to traverse.
        prefix: Path prefix for formatting output.
        max_depth: Maximum directory depth to inspect.
        current_depth: Current recursion depth.

    Returns:
        List of formatted path strings.
    """
    if current_depth >= max_depth:
        return []

    lines: list[str] = []
    try:
        entries = sorted(
            target_dir.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())
        )
    except (PermissionError, FileNotFoundError):
        return lines

    for entry in entries:
        if entry.name in IGNORED_DIRS or entry.name.startswith("."):
            continue

        relative_str = f"{prefix}/{entry.name}" if prefix else f"./{entry.name}"
        lines.append(relative_str)

        if entry.is_dir():
            lines.extend(
                build_tree(
                    entry,
                    prefix=relative_str,
                    max_depth=max_depth,
                    current_depth=current_depth + 1,
                )
            )

    return lines


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        argv: Optional argument list for testing.

    Returns:
        Parsed argument namespace.
    """
    parser = argparse.ArgumentParser(
        description="Audit and report repository directory structure."
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Inspect from workspace root down. Default checks only src/ and tests/.",
    )
    parser.add_argument(
        "--level",
        type=int,
        default=5,
        help="Maximum inspection depth (default: 5).",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        help="Optional explicit path to write output report file.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Execute repository structure inspection.

    Args:
        argv: Command-line arguments.

    Returns:
        Process exit code.
    """
    args = parse_args(argv)
    root = Path.cwd()

    output_lines: list[str] = []

    if args.all:
        output_lines.append(".")
        output_lines.extend(build_tree(root, prefix=".", max_depth=args.level))
        default_target = DEFAULT_COMPLETE_REPORT
    else:
        for target in ("src", "tests"):
            target_path = root / target
            if target_path.exists():
                output_lines.append(f"./{target}")
                output_lines.extend(
                    build_tree(target_path, prefix=f"./{target}", max_depth=args.level)
                )
        default_target = DEFAULT_FILTERED_REPORT

    destination = Path(args.output) if args.output else root / default_target
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(output_lines) + "\n", encoding="utf-8")

    print(f"Report created: {destination.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
