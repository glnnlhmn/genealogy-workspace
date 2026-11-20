"""Path: tests/test_gen_desk_tools/test_core/test_logging.py

Unit, regression, and integration tests for gen_desk_tools.core.logging.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pytest

from gen_desk_tools.core.logging import setup_tool_logger

__version__ = "1.0.0+build.1"


def _close_handlers(logger: logging.Logger) -> None:
    """Close and detach all handlers so Windows tmp_path cleanup never hits file locks."""
    for handler in list(logger.handlers):
        handler.close()
        logger.removeHandler(handler)


# ==========================================================================
# GROUP 1: Smoke & Primary Entrypoints
# Note: Dual-handler logger creation writing to logs/<name>.log and stdout.
# ==========================================================================


@pytest.mark.smoke
@pytest.mark.integration
def test_setup_tool_logger_writes_utf8_file_log_and_stdout(
    gdt_workspace: Path,
    gdt_config: dict[str, Any],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify setup_tool_logger routes messages to logs/<name>.log and stdout."""
    logger = setup_tool_logger("gdt_smoke", gdt_workspace, gdt_config, verbose=True)
    try:
        logger.info("Smoke check message")
    finally:
        _close_handlers(logger)

    log_file = gdt_workspace / "logs" / "gdt_smoke.log"
    assert log_file.is_file()
    assert "Smoke check message" in log_file.read_text(encoding="utf-8")
    assert "INFO: Smoke check message" in capsys.readouterr().out


# ==========================================================================
# GROUP 2: Core Logic & Happy Paths
# Note: Default, verbose, and debug console/file threshold configuration.
# ==========================================================================


@pytest.mark.integration
def test_setup_tool_logger_default_mode_sets_warning_console_and_info_file(
    gdt_workspace: Path,
    gdt_config: dict[str, Any],
) -> None:
    """Verify default flags configure WARNING on stdout and INFO in the log file."""
    logger = setup_tool_logger("gdt_default", gdt_workspace, gdt_config)
    try:
        file_handler, console_handler = logger.handlers
        assert file_handler.level == logging.INFO
        assert console_handler.level == logging.WARNING
        assert logger.propagate is False
    finally:
        _close_handlers(logger)


@pytest.mark.integration
def test_setup_tool_logger_debug_flag_sets_debug_on_both_handlers(
    gdt_workspace: Path,
    gdt_config: dict[str, Any],
) -> None:
    """Verify debug=True lowers both file and console handlers to DEBUG."""
    logger = setup_tool_logger("gdt_debug", gdt_workspace, gdt_config, debug=True)
    try:
        file_handler, console_handler = logger.handlers
        assert file_handler.level == logging.DEBUG
        assert console_handler.level == logging.DEBUG
    finally:
        _close_handlers(logger)


# ==========================================================================
# GROUP 3: Edge Cases & Boundary Conditions
# Note: Repeated logger initialization and invalid configured log levels.
# ==========================================================================


@pytest.mark.regression
def test_setup_tool_logger_replaces_existing_handlers_on_repeated_calls(
    gdt_workspace: Path,
    gdt_config: dict[str, Any],
) -> None:
    """Verify repeated calls for the same logger name do not accumulate duplicate handlers."""
    logger_first = setup_tool_logger("gdt_repeat", gdt_workspace, gdt_config)
    logger_second = setup_tool_logger("gdt_repeat", gdt_workspace, gdt_config, verbose=True)
    try:
        assert logger_first is logger_second
        assert len(logger_second.handlers) == 2
    finally:
        _close_handlers(logger_second)


@pytest.mark.regression
def test_setup_tool_logger_invalid_level_name_falls_back_to_info(
    gdt_workspace: Path,
    gdt_config: dict[str, Any],
) -> None:
    """Verify an unrecognized logging.log_level string falls back safely to INFO."""
    bad_cfg = {**gdt_config, "logging": {"log_level": "NOT_A_LEVEL"}}
    logger = setup_tool_logger("gdt_bad_level", gdt_workspace, bad_cfg)
    try:
        file_handler = logger.handlers[0]
        assert file_handler.level == logging.INFO
    finally:
        _close_handlers(logger)
