"""Path: src/gen_desk_tools/script_importer/cli.py

Command-line interface entrypoint for GenDesk Script Importer (gsi).

Operational Role:
    Registers shared gen_desk_tools.core CLI flags alongside -f/--force and
    -c/--clean, dispatching execution to script_importer.intake.run_intake().

Functions:
    build_parser: Construct the ArgumentParser for gsi.
    main: Parse CLI arguments and execute the intake pipeline.
"""

from __future__ import annotations

import argparse
import sys

from gen_desk_tools.core.cli import add_common_args
from gen_desk_tools.script_importer.intake import run_intake

__version__ = "1.0.0+build.2"

__all__ = [
    "build_parser",
    "main",
]


def build_parser() -> argparse.ArgumentParser:
    """Construct and return the ArgumentParser for gsi."""
    parser = argparse.ArgumentParser(
        prog="gsi",
        description="GenDesk Script Importer (gsi) - Hermetic Intake Automation",
    )
    add_common_args(parser)
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Bypass interactive overwrite and clean prompts (protected backups still run).",
    )
    parser.add_argument(
        "-c",
        "--clean",
        action="store_true",
        help="Prompt to delete unparseable staged files lacking valid headers from download/.",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    """Parse CLI arguments, invoke the intake pipeline, and exit with its status code."""
    parser = build_parser()
    args = parser.parse_args(argv)

    status = run_intake(
        force=args.force,
        clean=args.clean,
        verbose=args.verbose,
        debug=args.debug,
        root_dir=args.root,
        config_path=args.config,
    )
    sys.exit(status)
