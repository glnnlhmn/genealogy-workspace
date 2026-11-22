"""Path: tests/test_gen_desk_tools/test_core/test_logging.py

Unit, regression, and integration tests for gen_desk_tools.core.logging.

Operational Role:
    Verifies the 4-tier logging contract (ERROR, INFO, VERBOSE=15, DEBUG),
    handler threshold routing, repeated-call idempotency, UTF-8 persistence,
    unwritable log-directory errors, and append-mode behavior.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pytest

from gen_desk_tools.core import logging as core_logging
from gen_desk_tools.core.logging import VERBOSE, setup_tool_logger

__version__ = "1.0.0+build.2"


@contextmanager
def _managed_logger(
    name: str,
    root_dir: Path,
    cfg: dict[str, Any],
    *,
    verbose: bool = False,
    debug: bool = False,
) -> Iterator[logging.Logger]:
    """Yield a configured tool logger and close all handlers on exit (Windows-safe)."""
    logger = setup_tool_logger(name, root_dir, cfg, verbose=verbose, debug=debug)
    try:
        yield logger
    finally:
        for handler in list(logger.handlers):
            handler.close()
            logger.removeHandler(handler)


# ==========================================================================
# GROUP 1: Smoke & Primary Entrypoints
# Note: End-to-end 4-tier emission to logs/<name>.log and stdout.
# ==========================================================================


@pytest.mark.smoke
@pytest.mark.integration
def test_setup_tool_logger_emits_all_four_tiers_to_file_and_stdout(
    gdt_workspace: Path,
    gdt_config: dict[str, Any],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify ERROR, INFO, VERBOSE, and DEBUG all reach the log file and stdout."""
    with _managed_logger("gdt_smoke", gdt_workspace, gdt_config, debug=True) as logger:
        logger.error("err msg")
        logger.info("info msg")
        logger.log(VERBOSE, "verbose msg")
        logger.debug("debug msg")

    content = (gdt_workspace / "logs" / "gdt_smoke.log").read_text(encoding="utf-8")
    out = capsys.readouterr().out
    for tag in ("ERROR", "INFO", "VERBOSE", "DEBUG"):
        assert tag in content
        assert tag in out


# ==========================================================================
# GROUP 2: Core Logic & Happy Paths
# Note: Public interface, VERBOSE=15 registration, and threshold routing.
# ==========================================================================


@pytest.mark.unit
def test_core_logging_exposes_expected_public_interface_and_verbose_level() -> None:
    """Verify core.logging exports VERBOSE=15 and registers its level name."""
    assert {"VERBOSE", "setup_tool_logger"}.issubset(set(core_logging.__all__))
    assert VERBOSE == 15
    assert logging.getLevelName(VERBOSE) == "VERBOSE"


@pytest.mark.integration
def test_setup_tool_logger_default_mode_sets_warning_console_and_info_file(
    gdt_workspace: Path,
    gdt_config: dict[str, Any],
) -> None:
    """Verify default flags configure WARNING on stdout and INFO in the log file."""
    with _managed_logger("gdt_default", gdt_workspace, gdt_config) as logger:
        file_handler, console_handler = logger.handlers
        assert file_handler.level == logging.INFO
        assert console_handler.level == logging.WARNING
        assert logger.propagate is False


@pytest.mark.integration
def test_setup_tool_logger_verbose_flag_sets_verbose_console_level(
    gdt_workspace: Path,
    gdt_config: dict[str, Any],
) -> None:
    """Verify verbose=True lowers the stdout handler threshold to VERBOSE (15)."""
    with _managed_logger("gdt_verbose", gdt_workspace, gdt_config, verbose=True) as logger:
        assert logger.handlers[1].level == VERBOSE


@pytest.mark.integration
def test_setup_tool_logger_accepts_verbose_in_config_log_level(
    gdt_workspace: Path,
    gdt_config: dict[str, Any],
) -> None:
    """Verify logging.log_level='VERBOSE' configures the file handler to VERBOSE."""
    cfg = {**gdt_config, "logging": {"log_level": "VERBOSE"}}
    with _managed_logger("gdt_cfg_verbose", gdt_workspace, cfg) as logger:
        assert logger.handlers[0].level == VERBOSE


# ==========================================================================
# GROUP 3: Edge Cases & Boundary Conditions
# Note: Flag precedence, handler reset, fallback levels, empty/nested cfg, UTF-8.
# ==========================================================================


@pytest.mark.regression
def test_setup_tool_logger_debug_flag_overrides_verbose_flag(
    gdt_workspace: Path,
    gdt_config: dict[str, Any],
) -> None:
    """Verify debug=True wins over verbose=True and lowers both handlers to DEBUG."""
    with _managed_logger("gdt_dbg", gdt_workspace, gdt_config, verbose=True, debug=True) as logger:
        assert logger.handlers[0].level == logging.DEBUG
        assert logger.handlers[1].level == logging.DEBUG


@pytest.mark.regression
def test_setup_tool_logger_replaces_existing_handlers_on_repeated_calls(
    gdt_workspace: Path,
    gdt_config: dict[str, Any],
) -> None:
    """Verify repeated calls for the same logger name do not accumulate duplicate handlers."""
    first = setup_tool_logger("gdt_repeat", gdt_workspace, gdt_config)
    with _managed_logger("gdt_repeat", gdt_workspace, gdt_config, verbose=True) as second:
        assert first is second
        assert len(second.handlers) == 2


@pytest.mark.regression
def test_setup_tool_logger_invalid_level_name_falls_back_to_info(
    gdt_workspace: Path,
    gdt_config: dict[str, Any],
) -> None:
    """Verify an unrecognized logging.log_level string falls back safely to INFO."""
    bad_cfg = {**gdt_config, "logging": {"log_level": "NOT_A_LEVEL"}}
    with _managed_logger("gdt_bad_level", gdt_workspace, bad_cfg) as logger:
        assert logger.handlers[0].level == logging.INFO


@pytest.mark.regression
def test_setup_tool_logger_empty_cfg_and_nested_logs_dir(gdt_workspace: Path) -> None:
    """Verify empty cfg defaults to logs/ and nested logs_dir creates parent dirs."""
    with _managed_logger("gdt_empty", gdt_workspace, {}):
        assert (gdt_workspace / "logs" / "gdt_empty.log").is_file()

    nested_cfg = {"workspace": {"logs_dir": "a/b/logs"}}
    with _managed_logger("gdt_nested", gdt_workspace, nested_cfg):
        assert (gdt_workspace / "a" / "b" / "logs" / "gdt_nested.log").is_file()


@pytest.mark.regression
@pytest.mark.integration
def test_setup_tool_logger_writes_utf8_non_ascii_characters(
    gdt_workspace: Path,
    gdt_config: dict[str, Any],
) -> None:
    """Verify UTF-8 file handler persists non-ASCII characters cleanly on Windows."""
    with _managed_logger("gdt_utf8", gdt_workspace, gdt_config) as logger:
        logger.info("Müller — José")

    assert "Müller — José" in (gdt_workspace / "logs" / "gdt_utf8.log").read_text(encoding="utf-8")


# ==========================================================================
# GROUP 4: Error Handling & Validation Failures
# Note: Unwritable log directory path.
# ==========================================================================


@pytest.mark.regression
@pytest.mark.integration
def test_setup_tool_logger_unwritable_logs_dir_file_raises_os_error(
    gdt_workspace: Path,
    gdt_config: dict[str, Any],
) -> None:
    """Verify pointing workspace.logs_dir at an existing regular file raises OSError."""
    (gdt_workspace / "blocked_logs").write_text("file", encoding="utf-8")
    bad_cfg = {**gdt_config, "workspace": {"logs_dir": "blocked_logs"}}

    with pytest.raises(OSError):
        setup_tool_logger("gdt_err", gdt_workspace, bad_cfg)


# ==========================================================================
# GROUP 5: Filesystem, CLI & Integration
# Note: Persistent append-mode behavior across separate logger sessions.
# ==========================================================================


@pytest.mark.integration
def test_setup_tool_logger_appends_across_separate_runs(
    gdt_workspace: Path,
    gdt_config: dict[str, Any],
) -> None:
    """Verify consecutive logger sessions append to logs/<name>.log without truncating."""
    for msg in ("run-one", "run-two"):
        with _managed_logger("gdt_append", gdt_workspace, gdt_config) as logger:
            logger.info(msg)

    text = (gdt_workspace / "logs" / "gdt_append.log").read_text(encoding="utf-8")
    assert "run-one" in text
    assert "run-two" in text
