"""Path: src/gen_desk_tools/core/cli.py

Shared CLI argument registration and interactive confirmation helpers for GDT.

Operational Role:
    Provides uniform flag definitions (-v/--verbose, --debug, --config, --root)
    and yes/no stdin prompts so every GenDesk Tools command exposes a consistent
    terminal interface.

Functions:
    add_common_args: Register standard GDT CLI flags on an ArgumentParser.
    prompt_yes_no: Prompt the operator for a yes/no confirmation on stdin.
"""

from __future__ import annotations

import argparse
from pathlib import Path

__version__ = "1.0.0+build.1"

__all__ = [
    "add_common_args",
    "prompt_yes_no",
]


def add_common_args(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    """Attach -v/--verbose, --debug, --config, and --root flags to parser in place."""
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Emit detailed informational logs to stdout.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Emit debug-level diagnostics and tracebacks.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Optional path to an explicit TOML configuration override file.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Optional workspace root directory override.",
    )
    return parser


def prompt_yes_no(question: str, *, default: bool = False) -> bool:
    """Prompt the operator for a yes/no confirmation on stdin until valid input is entered.

    Args:
        default: Value returned when the operator presses Enter on an empty line.
    """
    suffix = " [Y/n]: " if default else " [y/N]: "

    while True:
        answer = input(f"{question}{suffix}").strip().lower()
        if not answer:
            return default
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
