"""Path: src/gen_desk_tools/structure/cli.py

Command-line interface entrypoint for GenDesk Structure (gd-struct).

Operational Role:
    Registers shared gen_desk_tools.core CLI flags alongside target mode flags
    (--gd, --ancestry-desk, --gd-tools, -s/--system, --cli, --src, -a/--all,
    -g/--git), -t/--tests, -l/--level (default 7), and --reports-dir.

Functions:
    build_parser: Construct the ArgumentParser for gd-struct.
    resolve_mode: Determine the active target mode from parsed arguments.
    run: Execute structure report generation and return a POSIX exit code.
    main: Parse CLI arguments and exit with run()'s status code.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from gen_desk_tools.core.cli import add_common_args
from gen_desk_tools.core.config import load_gdt_config
from gen_desk_tools.core.workspace import resolve_workspace_root
from gen_desk_tools.structure.scanner import DEFAULT_MAX_DEPTH, generate_structure_report

__version__ = "1.0.0+build.2"

__all__ = [
    "build_parser",
    "main",
    "resolve_mode",
    "run",
]


def build_parser() -> argparse.ArgumentParser:
    """Construct and return the ArgumentParser for gd-struct."""
    parser = argparse.ArgumentParser(
        prog="gd-struct",
        description="GenDesk Structure (gd-struct) - Workspace directory tree reporter.",
    )
    add_common_args(parser)

    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--gd",
        dest="mode",
        action="store_const",
        const="gda",
        help="Scan src/gda (default).",
    )
    mode_group.add_argument(
        "--ancestry-desk",
        dest="mode",
        action="store_const",
        const="ancestry_desk",
        help="Scan src/ancestry_desk.",
    )
    mode_group.add_argument(
        "--gd-tools",
        dest="mode",
        action="store_const",
        const="gd_tools",
        help="Scan src/gen_desk_tools.",
    )
    mode_group.add_argument(
        "-s",
        "--system",
        dest="mode",
        action="store_const",
        const="system",
        help="Scan src/system.",
    )
    mode_group.add_argument(
        "--cli",
        dest="mode",
        action="store_const",
        const="cli",
        help="Scan src/cli.",
    )
    mode_group.add_argument(
        "--src",
        dest="mode",
        action="store_const",
        const="src",
        help="Scan all of src/.",
    )
    mode_group.add_argument(
        "-a",
        "--all",
        dest="mode",
        action="store_const",
        const="all",
        help="Scan entire workspace (excluding mandatory cache/VCS dirs).",
    )
    mode_group.add_argument(
        "-g",
        "--git",
        dest="mode",
        action="store_const",
        const="git",
        help="Scan all workspace files not ignored by .gitignore.",
    )

    parser.add_argument(
        "-t",
        "--tests",
        action="store_true",
        help="Include matching tests/ directory alongside source targets.",
    )
    parser.add_argument(
        "-l",
        "--level",
        type=int,
        default=DEFAULT_MAX_DEPTH,
        help=f"Maximum directory depth (default: {DEFAULT_MAX_DEPTH}).",
    )
    parser.add_argument(
        "--reports-dir",
        type=Path,
        default=None,
        help="Destination directory for report output (defaults to config workspace.reports_dir).",
    )
    return parser


def resolve_mode(args: argparse.Namespace) -> str:
    """Return the selected mode, defaulting to 'gda' when no target flag is set."""
    return str(args.mode) if args.mode else "gda"


def run(args: argparse.Namespace) -> int:
    """Execute structure report generation and return a POSIX exit code."""
    try:
        root = resolve_workspace_root(cfg_root=args.root)
        cfg = load_gdt_config(root_dir=root, config_path=args.config)
    except Exception as exc:
        print(f"[ERROR] Failed to load GDT configuration: {exc}", file=sys.stderr)
        return 1

    reports_dir = (
        args.reports_dir
        if args.reports_dir is not None
        else Path(str(cfg.get("workspace", {}).get("reports_dir", "reports")))
    )
    mode = resolve_mode(args)

    try:
        report_file, lines_count = generate_structure_report(
            mode=mode,
            include_tests=bool(args.tests),
            workspace_root=root,
            reports_dir=reports_dir,
            max_depth=int(args.level),
        )
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Number of lines output: {lines_count}")
    print(f"Report file created: {report_file.as_posix()}")
    return 0


def main(argv: list[str] | None = None) -> None:
    """Parse CLI arguments, execute gd-struct, and exit with its status code."""
    parser = build_parser()
    args = parser.parse_args(argv)
    sys.exit(run(args))
