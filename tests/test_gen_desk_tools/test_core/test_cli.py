"""Path: tests/test_gen_desk_tools/test_core/test_cli.py

Unit and regression tests for gen_desk_tools.core.cli.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from gen_desk_tools.core.cli import add_common_args, prompt_yes_no

__version__ = "1.0.0+build.1"

# ==========================================================================
# GROUP 1: Smoke & Primary Entrypoints
# Note: Standard GDT flag registration and parsing on ArgumentParser.
# ==========================================================================


@pytest.mark.smoke
@pytest.mark.unit
def test_add_common_args_registers_and_parses_standard_flags() -> None:
    """Verify add_common_args attaches -v, --debug, --config, and --root cleanly."""
    parser = add_common_args(argparse.ArgumentParser(prog="gdt-test"))
    args = parser.parse_args(["-v", "--debug", "--config", "custom.toml", "--root", "/tmp/repo"])

    assert args.verbose is True
    assert args.debug is True
    assert args.config == Path("custom.toml")
    assert args.root == Path("/tmp/repo")


# ==========================================================================
# GROUP 2: Core Logic & Happy Paths
# Note: Default flag values and standard yes/no interactive responses.
# ==========================================================================


@pytest.mark.unit
def test_add_common_args_default_values_when_omitted() -> None:
    """Verify standard flags default to False/None when no CLI arguments are supplied."""
    parser = add_common_args(argparse.ArgumentParser(prog="gdt-test"))
    args = parser.parse_args([])

    assert args.verbose is False
    assert args.debug is False
    assert args.config is None
    assert args.root is None


@pytest.mark.unit
@pytest.mark.parametrize("raw_input", ["y", "yes", "YES", "  y  "])
def test_prompt_yes_no_affirmative_responses_return_true(
    raw_input: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify affirmative stdin inputs return True."""
    monkeypatch.setattr("builtins.input", lambda _prompt: raw_input)
    assert prompt_yes_no("Proceed?") is True


@pytest.mark.unit
@pytest.mark.parametrize("raw_input", ["n", "no", "NO", "  n  "])
def test_prompt_yes_no_negative_responses_return_false(
    raw_input: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify negative stdin inputs return False."""
    monkeypatch.setattr("builtins.input", lambda _prompt: raw_input)
    assert prompt_yes_no("Proceed?", default=True) is False


# ==========================================================================
# GROUP 3: Edge Cases & Boundary Conditions
# Note: Empty-input defaults and reprompting after unrecognized input.
# ==========================================================================


@pytest.mark.regression
def test_prompt_yes_no_empty_input_respects_default_flag(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify pressing Enter on an empty line returns the configured default value."""
    monkeypatch.setattr("builtins.input", lambda _prompt: "")
    assert prompt_yes_no("Proceed?", default=False) is False
    assert prompt_yes_no("Proceed?", default=True) is True


@pytest.mark.regression
def test_prompt_yes_no_reprompts_until_valid_input(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify unrecognized responses loop until the operator enters y or n."""
    responses = iter(["maybe", "123", "yes"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(responses))

    assert prompt_yes_no("Proceed?") is True
