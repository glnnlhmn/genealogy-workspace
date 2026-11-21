"""Path: tests/test_gen_desk_tools/test_core/test_cli.py

Unit and regression tests for gen_desk_tools.core.cli.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from gen_desk_tools.core.cli import add_common_args, prompt_int_default, prompt_yes_no

__version__ = "1.0.0+build.2"

# ==========================================================================
# GROUP 1: Smoke & Common Argument Registration
# Note: Standard GDT CLI flags (-v, --debug, --config, --root, --prompts).
# ==========================================================================


@pytest.mark.smoke
@pytest.mark.unit
def test_add_common_args_registers_standard_gdt_flags() -> None:
    """Verify add_common_args registers verbose, debug, config, root, and prompts flags."""
    parser = add_common_args(argparse.ArgumentParser(prog="demo"))
    args = parser.parse_args(["-v", "--debug", "--config", "cfg.toml", "--root", "ws", "--prompts"])

    assert args.verbose is True
    assert args.debug is True
    assert args.config == Path("cfg.toml")
    assert args.root == Path("ws")
    assert args.prompts is True


# ==========================================================================
# GROUP 2: Interactive Prompt Helpers (prompt_yes_no & prompt_int_default)
# Note: Happy paths, defaults, invalid tokens, and EOF/KeyboardInterrupt safety.
# ==========================================================================


@pytest.mark.unit
@pytest.mark.parametrize(
    ("raw_input", "default", "expected"),
    [
        ("y", False, True),
        ("YES", False, True),
        ("n", True, False),
        ("No", True, False),
        ("", True, True),
        ("", False, False),
        ("maybe", True, True),
        ("maybe", False, False),
    ],
)
def test_prompt_yes_no_parses_responses_and_defaults(
    monkeypatch: pytest.MonkeyPatch,
    raw_input: str,
    default: bool,
    expected: bool,
) -> None:
    """Verify prompt_yes_no returns expected booleans for yes, no, blank, and unknown text."""
    monkeypatch.setattr("builtins.input", lambda _: raw_input)
    assert prompt_yes_no("Proceed?", default=default) is expected


@pytest.mark.regression
@pytest.mark.parametrize("exc_type", [EOFError, KeyboardInterrupt])
def test_prompt_yes_no_returns_default_on_eof_or_interrupt(
    monkeypatch: pytest.MonkeyPatch,
    exc_type: type[BaseException],
) -> None:
    """Verify prompt_yes_no safely returns default on EOFError or KeyboardInterrupt."""

    def _raise(_: str) -> str:
        raise exc_type()

    monkeypatch.setattr("builtins.input", _raise)
    assert prompt_yes_no("Proceed?", default=True) is True
    assert prompt_yes_no("Proceed?", default=False) is False


@pytest.mark.unit
@pytest.mark.parametrize(
    ("raw_input", "default", "minimum", "expected"),
    [
        ("15", 20, 1, 15),
        ("0", 20, 1, 1),
        ("-5", 20, 1, 1),
        ("", 20, 1, 20),
        ("not-a-number", 20, 1, 20),
    ],
)
def test_prompt_int_default_parses_clamps_and_falls_back(
    monkeypatch: pytest.MonkeyPatch,
    raw_input: str,
    default: int,
    minimum: int,
    expected: int,
) -> None:
    """Verify prompt_int_default parses integers, enforces minimum, and handles invalid input."""
    monkeypatch.setattr("builtins.input", lambda _: raw_input)
    assert prompt_int_default("Lines", default, minimum=minimum) == expected


@pytest.mark.regression
@pytest.mark.parametrize("exc_type", [EOFError, KeyboardInterrupt])
def test_prompt_int_default_returns_default_on_eof_or_interrupt(
    monkeypatch: pytest.MonkeyPatch,
    exc_type: type[BaseException],
) -> None:
    """Verify prompt_int_default safely returns default on EOFError or KeyboardInterrupt."""

    def _raise(_: str) -> str:
        raise exc_type()

    monkeypatch.setattr("builtins.input", _raise)
    assert prompt_int_default("Lines", 20, minimum=1) == 20
