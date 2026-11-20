"""Path: src/gen_desk_tools/radon_report/cli.py

Command-line interface entrypoint for GenDesk Radon Report (gdradon).

Operational Role:
    Exposes structure-aligned CLI flags (-m/--mode, --include-tests,
    --reports-dir, -n/--min-grade, -o/--output) alongside common GDT flags
    (-v/--verbose, --debug, --config, --root) to generate combined CC, MI,
    and RAW reports.

Functions:
    build_parser: Construct the ArgumentParser for gdradon.
    run: Execute the requested Radon report generation and return an exit code.
    main: Parse CLI arguments and exit with run()'s status code.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from gen_desk_tools.core.cli import add_common_args
from gen_desk_tools.core.config import load_gdt_config
from gen_desk_tools.core.logging import setup_tool_logger
from gen_desk_tools.core.workspace import resolve_workspace_root
from gen_desk_tools.radon_report.scanner import MODE_TARGETS, generate_radon_report

__version__ = "1.0.0+build.1"

__all__ = [
    "build_parser",
    "main",
    "run",
]


def build_parser() -> argparse.ArgumentParser:
    """Construct and return the ArgumentParser for gdradon."""
    parser = argparse.ArgumentParser(
        prog="gdradon",
        description="GenDesk Radon Report - Combined CC, MI, and RAW static analysis reports",
    )
    add_common_args(parser)
    parser.add_argument(
        "-m",
        "--mode",
        type=str,
        default="gd_tools",
        choices=sorted([*MODE_TARGETS, "all"]),
        help="Target subsystem mode (default: gd_tools).",
    )
    parser.add_argument(
        "--include-tests",
        action="store_true",
        help="Include matching test suite directories alongside source paths.",
    )
    parser.add_argument(
        "--reports-dir",
        type=Path,
        default=None,
        help="Destination directory for report output (defaults to config workspace.reports_dir).",
    )
    parser.add_argument(
        "-n",
        "--min-grade",
        type=str,
        default=None,
        help="Optional minimum/maximum Radon grade filter (-n) passed to cc/mi.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        help="Optional explicit output filename inside the report directory.",
    )
    return parser


def run(args: argparse.Namespace) -> int:
    """Execute the Radon report generator and return a POSIX exit code."""
    try:
        root = resolve_workspace_root(cfg_root=args.root)
        cfg = load_gdt_config(root_dir=root, config_path=args.config)
    except Exception as exc:
        print(f"[ERROR] Failed to load GDT configuration: {exc}", file=sys.stderr)
        return 1

    logger = setup_tool_logger("gdradon", root, cfg, verbose=args.verbose, debug=args.debug)
    reports_dir = (
        args.reports_dir
        if args.reports_dir is not None
        else Path(str(cfg.get("workspace", {}).get("reports_dir", "reports")))
    )

    try:
        report_path, line_count = generate_radon_report(
            mode=args.mode,
            include_tests=args.include_tests,
            workspace_root=root,
            reports_dir=reports_dir,
            min_grade=args.min_grade,
            output_filename=args.output,
        )
    except Exception as exc:
        logger.error("Failed to generate Radon report: %s", exc)
        print(f"[ERROR] Failed to generate Radon report: {exc}", file=sys.stderr)
        return 1

    logger.info("RADON_REPORT: %s (%d lines)", report_path, line_count)
    print(f"Radon report written to {report_path} ({line_count} lines).")
    return 0


def main(argv: list[str] | None = None) -> None:
    """Parse CLI arguments, execute gdradon, and exit with its status code."""
    parser = build_parser()
    args = parser.parse_args(argv)
    sys.exit(run(args))
