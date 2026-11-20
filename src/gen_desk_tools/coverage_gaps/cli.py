"""Path: src/gen_desk_tools/coverage_gaps/cli.py

Command-line interface entrypoint for GenDesk Coverage Gaps (gaps).

Operational Role:
    Registers shared gen_desk_tools.core CLI flags alongside file_path,
    optional gap range, -g/--gap-range, and -o/--output-dir, dispatching
    extraction to coverage_gaps.extractor.generate_gap_report().

Functions:
    build_parser: Construct the ArgumentParser for gaps.
    run: Execute parsed gaps extraction and return a POSIX exit code.
    main: Parse CLI arguments and exit with run()'s status code.
"""

from __future__ import annotations

import argparse
import sys

from gen_desk_tools.core.cli import add_common_args
from gen_desk_tools.core.config import load_gdt_config
from gen_desk_tools.core.workspace import resolve_workspace_root
from gen_desk_tools.coverage_gaps.extractor import generate_gap_report

__version__ = "1.0.0+build.1"

__all__ = [
    "build_parser",
    "main",
    "run",
]


def build_parser() -> argparse.ArgumentParser:
    """Construct and return the ArgumentParser for gaps."""
    parser = argparse.ArgumentParser(
        prog="gaps",
        description="GenDesk Coverage Gaps (gaps) - Extract line-numbered source context into reports/.",
    )
    add_common_args(parser)
    parser.add_argument(
        "file_path",
        type=str,
        help="Target source file path relative to repository root (or absolute).",
    )
    parser.add_argument(
        "gap",
        nargs="?",
        default=None,
        help="Optional line range (e.g. '110-120', '222->226', or '67'). Omit for full file.",
    )
    parser.add_argument(
        "-g",
        "--gap-range",
        type=str,
        default=None,
        dest="flag_gap",
        help="Alternative flag for line range.",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=str,
        default=None,
        help="Destination directory for reports (defaults to configured reports_dir).",
    )
    return parser


def run(args: argparse.Namespace) -> int:
    """Execute coverage gap extraction and return a POSIX exit code."""
    try:
        root = resolve_workspace_root(cfg_root=args.root)
        cfg = load_gdt_config(root_dir=root, config_path=args.config)
    except Exception as exc:
        print(f"[ERROR] Failed to load GDT configuration: {exc}", file=sys.stderr)
        return 1

    output_dir = args.output_dir or str(cfg.get("workspace", {}).get("reports_dir", "reports"))
    gap_input = args.flag_gap if args.flag_gap is not None else args.gap

    try:
        report_file, lines_count = generate_gap_report(
            file_path=args.file_path,
            gap_arg=gap_input,
            output_dir=output_dir,
            workspace_root=root,
        )
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Number of lines output: {lines_count}")
    print(f"Report file created: {report_file.as_posix()}")
    return 0


def main(argv: list[str] | None = None) -> None:
    """Parse CLI arguments, execute gaps, and exit with its status code."""
    parser = build_parser()
    args = parser.parse_args(argv)
    sys.exit(run(args))
