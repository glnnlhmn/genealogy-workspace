"""Path: src/system/util/check_structure.py

Directory tree inspection utility for workspace auditing and reporting.

Operational Role:
    Traverses the workspace hierarchy, enforces configurable domain filtering
    (entire workspace, src-only, schemas-only, data-only, clean workspace),
    provides interactive exclusion toggles via a menu interface, and writes
    standardized directory tree listings to reports/.

Usage:
    python src/system/util/check_structure.py [--scope {all,src,src-no-tests,schemas,data,clean}]
                                              [--menu] [--level N] [--output PATH]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

__version__ = "1.0.0+build.4"

# Invariant system exclusions that are always skipped across all scans
MANDATORY_EXCLUSIONS: set[str] = {
    ".git",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "pytest_tmp",
    "temp",
}

# Optional diagnostic and ephemeral directories that can be toggled
TOGGLEABLE_EXCLUSIONS: set[str] = {
    "gtemp",
    "reports",
    "logs",
    "tests",
}

DEFAULT_REPORT_DIR: str = "reports"
DEFAULT_REPORT_FILE: str = "reports/GenDeskStructure.txt"


def resolve_workspace_root(root_arg: str | None = None) -> Path:
    """Resolve canonical repository root dynamically without hardcoded dependencies."""
    if root_arg and root_arg != ".":
        candidate = Path(root_arg).resolve()
        if candidate.is_dir():
            return candidate

    script_path = Path(__file__).resolve()
    for parent in script_path.parents:
        if (parent / "pyproject.toml").is_file():
            return parent

    return Path.cwd().resolve()


def build_tree(
    target_dir: Path,
    prefix: str = "",
    max_depth: int = 5,
    current_depth: int = 0,
    excluded_names: set[str] | None = None,
) -> list[str]:
    """Recursively collect sorted directory tree lines up to max_depth.

    Args:
        target_dir: Directory path to traverse.
        prefix: Display prefix representing path hierarchy.
        max_depth: Maximum recursion depth.
        current_depth: Current recursion depth tracker.
        excluded_names: Set of directory and file names to exclude.

    Returns:
        list[str]: Formatted relative path strings.
    """
    if current_depth >= max_depth:
        return []

    exclusions = MANDATORY_EXCLUSIONS.copy()
    if excluded_names:
        exclusions.update(excluded_names)

    lines: list[str] = []
    try:
        entries = sorted(target_dir.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
    except (PermissionError, FileNotFoundError):
        return lines

    for entry in entries:
        if entry.name in exclusions or entry.name.startswith("."):
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
                    excluded_names=exclusions,
                )
            )

    return lines


def generate_structure_report(
    scope: str = "src",
    workspace_root: Path | str = ".",
    max_depth: int = 5,
    excluded_names: set[str] | None = None,
    output_path: Path | str | None = None,
) -> tuple[Path, int]:
    """Generate workspace directory structure inspection report.

    Args:
        scope: Target domain ('all', 'src', 'src-no-tests', 'schemas', 'data', 'clean').
        workspace_root: Workspace root directory anchor.
        max_depth: Maximum recursion depth.
        excluded_names: Optional additional directory names to exclude.
        output_path: Explicit report destination file path.

    Returns:
        tuple[Path, int]: Written report Path and count of lines recorded.

    Raises:
        ValueError: If scope specification is unknown.
    """
    root = Path(workspace_root).resolve()
    active_exclusions = set(excluded_names or set())

    output_lines: list[str] = []

    if scope == "all":
        output_lines.append(".")
        output_lines.extend(
            build_tree(
                root,
                prefix=".",
                max_depth=max_depth,
                excluded_names=active_exclusions,
            )
        )
        default_file = "GenDeskStructureComplete.txt"

    elif scope == "clean":
        clean_exclusions = active_exclusions | {"gtemp", "reports", "logs"}
        output_lines.append(".")
        output_lines.extend(
            build_tree(
                root,
                prefix=".",
                max_depth=max_depth,
                excluded_names=clean_exclusions,
            )
        )
        default_file = "GenDeskStructureClean.txt"

    elif scope == "src":
        for target in ("src", "tests"):
            target_path = root / target
            if target_path.exists():
                output_lines.append(f"./{target}")
                output_lines.extend(
                    build_tree(
                        target_path,
                        prefix=f"./{target}",
                        max_depth=max_depth,
                        excluded_names=active_exclusions,
                    )
                )
        default_file = "GenDeskStructureSrcTests.txt"

    elif scope == "src-no-tests":
        target_path = root / "src"
        if target_path.exists():
            output_lines.append("./src")
            output_lines.extend(
                build_tree(
                    target_path,
                    prefix="./src",
                    max_depth=max_depth,
                    excluded_names=active_exclusions,
                )
            )
        default_file = "GenDeskStructureSrcOnly.txt"

    elif scope == "schemas":
        target_path = root / "schemas"
        if target_path.exists():
            output_lines.append("./schemas")
            output_lines.extend(
                build_tree(
                    target_path,
                    prefix="./schemas",
                    max_depth=max_depth,
                    excluded_names=active_exclusions,
                )
            )
        default_file = "GenDeskStructureSchemas.txt"

    elif scope == "data":
        target_path = root / "data"
        if target_path.exists():
            output_lines.append("./data")
            output_lines.extend(
                build_tree(
                    target_path,
                    prefix="./data",
                    max_depth=max_depth,
                    excluded_names=active_exclusions,
                )
            )
        default_file = "GenDeskStructureData.txt"

    else:
        raise ValueError(
            f"Unknown inspection scope: '{scope}'. "
            f"Expected: all, clean, src, src-no-tests, schemas, data."
        )

    destination = Path(output_path) if output_path else root / DEFAULT_REPORT_DIR / default_file
    destination.parent.mkdir(parents=True, exist_ok=True)

    report_payload = "\n".join(output_lines) + ("\n" if output_lines else "")
    destination.write_text(report_payload, encoding="utf-8")

    return destination, len(output_lines)


def run_interactive_menu() -> tuple[str, set[str]]:
    """Run terminal interactive menu to select target scope and toggle exclusions.

    Returns:
        tuple[str, set[str]]: Selected scope string and active excluded directory names.
    """
    selected_scope = "src"

    # Default toggle states: False = Included, True = Excluded
    toggles: dict[str, bool] = {
        "gtemp": True,
        "reports": False,
        "logs": True,
        "tests": False,
    }

    while True:
        print("\n=== Workspace Structure Inspection Menu ===")
        print(f"Target Scope: [{selected_scope}]")
        print("  1. Entire Workspace (all)")
        print("  2. Clean Workspace (excludes gtemp, reports, logs)")
        print("  3. Only src/ (with tests/)")
        print("  4. Only src/ (without tests/)")
        print("  5. Only schemas/")
        print("  6. Only data/")
        print("\nExclusion Toggles:")
        print(f"  g. Toggle gtemp/   [{'EXCLUDED' if toggles['gtemp'] else 'INCLUDED'}]")
        print(f"  r. Toggle reports/ [{'EXCLUDED' if toggles['reports'] else 'INCLUDED'}]")
        print(f"  l. Toggle logs/    [{'EXCLUDED' if toggles['logs'] else 'INCLUDED'}]")
        print(f"  t. Toggle tests/   [{'EXCLUDED' if toggles['tests'] else 'INCLUDED'}]")
        print("\nActions:")
        print("  <Enter> Generate Report")
        print("  q. Quit")

        try:
            choice = input("\nSelect option: ").strip().lower()
        except EOFError:
            choice = "q"

        if choice == "":
            break
        if choice in ("q", "quit"):
            sys.exit(0)
        elif choice == "1":
            selected_scope = "all"
        elif choice == "2":
            selected_scope = "clean"
        elif choice == "3":
            selected_scope = "src"
        elif choice == "4":
            selected_scope = "src-no-tests"
        elif choice == "5":
            selected_scope = "schemas"
        elif choice == "6":
            selected_scope = "data"
        elif choice == "g":
            toggles["gtemp"] = not toggles["gtemp"]
        elif choice == "r":
            toggles["reports"] = not toggles["reports"]
        elif choice == "l":
            toggles["logs"] = not toggles["logs"]
        elif choice == "t":
            toggles["tests"] = not toggles["tests"]
        else:
            print("Invalid selection. Please choose an option from the menu.")

    active_exclusions = {name for name, is_excluded in toggles.items() if is_excluded}
    return selected_scope, active_exclusions


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="check_structure",
        description="Audit and report repository workspace directory structure.",
    )
    parser.add_argument(
        "--scope",
        choices=["all", "clean", "src", "src-no-tests", "schemas", "data"],
        default="src",
        help="Inspection scope (default: 'src').",
    )
    parser.add_argument(
        "-m",
        "--menu",
        action="store_true",
        help="Launch interactive terminal menu with toggle controls.",
    )
    parser.add_argument(
        "--level",
        type=int,
        default=5,
        help="Maximum inspection directory depth (default: 5).",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        help="Optional explicit path to write output report file.",
    )
    parser.add_argument(
        "--root",
        type=str,
        default=None,
        help="Optional workspace root directory path anchor.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """CLI orchestrator entrypoint."""
    args = parse_args(argv)
    root = resolve_workspace_root(args.root)

    if args.menu:
        scope, exclusions = run_interactive_menu()
    else:
        scope = args.scope
        exclusions = set()

    try:
        report_file, lines_count = generate_structure_report(
            scope=scope,
            workspace_root=root,
            max_depth=args.level,
            excluded_names=exclusions,
            output_path=args.output,
        )
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Number of lines output: {lines_count}")
    print(f"Report file created: {report_file.as_posix()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
