"""Path: src/gen_desk_tools/readme_gen/cli.py

Command-line interface entrypoint for GenDesk README Generator (gdrm).

Operational Role:
    Parses CLI arguments using shared gen_desk_tools.core flags alongside
    README-specific options (-t/--target, -f/--force, --packages-config) and
    dispatches to readme_gen.generator.run().

Functions:
    build_parser: Construct the ArgumentParser for gdrm.
    main: Parse CLI arguments and execute the generator.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from gen_desk_tools.core.cli import add_common_args
from gen_desk_tools.readme_gen.generator import run

__version__ = "1.0.0+build.2"

__all__ = [
    "build_parser",
    "main",
]


def build_parser() -> argparse.ArgumentParser:
    """Construct and return the ArgumentParser for gdrm."""
    parser = argparse.ArgumentParser(
        prog="gdrm",
        description="Dynamic AST-driven package README.md generator for GDA.",
    )
    add_common_args(parser)
    parser.add_argument(
        "target_pos",
        nargs="?",
        default=None,
        help="Optional scope alias or path prefix (e.g. 'src', 'gda', 'cli', 'src/gda/model').",
    )
    parser.add_argument(
        "-t",
        "--target",
        dest="target_opt",
        type=str,
        default=None,
        help="Optional named scope alias or package path prefix.",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Overwrite hand-edited README.md files without interactive prompting.",
    )
    parser.add_argument(
        "--packages-config",
        type=Path,
        default=None,
        help="Path to a custom TOML package manifest.",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    """Parse CLI arguments, invoke the README generator, and exit with its status code."""
    parser = build_parser()
    args = parser.parse_args(argv)

    target_selected = args.target_opt or args.target_pos
    exit_code = run(
        target=target_selected,
        force=args.force,
        verbose=args.verbose,
        debug=args.debug,
        root_dir=args.root,
        config_path=args.config,
        packages_config=args.packages_config,
    )
    sys.exit(exit_code)
