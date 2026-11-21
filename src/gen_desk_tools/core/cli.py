"""Path: src/gen_desk_tools/core/cli.py

Shared CLI argument registration and interactive confirmation helpers for GDT.

Operational Role:
    Provides standardized argparse flag registration (-v/--verbose, --debug,
    --config, --root, --prompts) and safe interactive prompt helpers shared
    across all GenDesk Tools subpackages and the interactive menu.

Functions:
    add_common_args: Register standard GDT CLI flags on an ArgumentParser.
    prompt_yes_no: Prompt the operator for a yes/no confirmation safely.
    prompt_int_default: Prompt for an integer value with a fallback default.
"""

from __future__ import annotations

import argparse
from pathlib import Path

__version__ = "1.0.0+build.2"

__all__ = [
    "add_common_args",
    "prompt_int_default",
    "prompt_yes_no",
]


def add_common_args(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    """Register standard GDT flags (-v/--verbose, --debug, --config, --root, --prompts)."""
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
    parser.add_argument(
        "--prompts",
        action="store_true",
        help="Enable interactive prompted input mode for menus and CLI tools.",
    )
    return parser


def prompt_yes_no(message: str, *, default: bool = False) -> bool:
    """Prompt the operator for a yes/no answer, returning default on empty input or EOF."""
    suffix = " [Y/n]: " if default else " [y/N]: "
    try:
        raw = input(f"{message}{suffix}").strip().lower()
    except (EOFError, KeyboardInterrupt):
        return default

    if not raw:
        return default
    if raw in ("y", "yes"):
        return True
    if raw in ("n", "no"):
        return False
    return default


def prompt_int_default(label: str, default: int, *, minimum: int = 1) -> int:
    """Prompt for an integer value, returning default on blank, invalid, or EOF input."""
    try:
        raw = input(f"{label} [{default}]: ").strip()
    except (EOFError, KeyboardInterrupt):
        return default

    if not raw:
        return default
    try:
        return max(minimum, int(raw))
    except ValueError:
        return default
