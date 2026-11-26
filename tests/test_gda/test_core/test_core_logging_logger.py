"""Path: tests/test_gda/test_core/test_core_logging_logger.py

Unit, regression, and integration tests for GDALogger lifecycle and sinks.

Operational Role:
    Validates GDALogger console emission, idempotent handler attachment,
    rotating file persistence, base_dir path anchoring, log level filtering,
    explicit close() and context-manager teardown, Windows file-lock release,
    and root logger propagation isolation.

Test Structure & Protocol:
    - Atomized tests: 1:1 behavioral contract mapping.
    - Fully decorated: 5-marker taxonomy (smoke, unit, regression, integration, integrity).
    - Dependencies: Shared conftest.py fixture (managed_gda_logger).
"""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

import pytest

import gda.core.logging as log_mod
from gda.core.config import LoggingConfig
from gda.core.errors import ConfigValidationError
from gda.core.logging import GDALogger

__version__ = "1.0.0+build.1"


# ==============================================================================
# GROUP 1: Smoke & Primary Entrypoints
# Note: Verifies GDALogger export and basic console emission.
# ==============================================================================


@pytest.mark.smoke
@pytest.mark.unit
def test_gda_logger_exported_and_emits_console_output(
    capsys: pytest.CaptureFixture[str],
    managed_gda_logger: Callable[[str, LoggingConfig | None], GDALogger],
) -> None:
    """Verify GDALogger is exported and emits to standard stream when enabled."""
    assert "GDALogger" in log_mod.__all__
    cfg = LoggingConfig(level="INFO", log_to_console=True, log_to_file=False)
    logger = managed_gda_logger("test.console", cfg)
    assert logger.name == "test.console"
    logger.info("Console message verified")
    captured = capsys.readouterr()
    assert "[INFO] [test.console] Console message verified" in (captured.err + captured.out)


# ==============================================================================
# GROUP 3: Edge Cases & Boundary Conditions
# Note: Idempotent handler attachment across repeated logger initialization.
# ==============================================================================


@pytest.mark.regression
def test_gda_logger_idempotent_handler_attachment(
    managed_gda_logger: Callable[[str, LoggingConfig | None], GDALogger],
) -> None:
    """Verify multiple GDALogger initializations do not stack duplicate handlers."""
    cfg = LoggingConfig(log_to_console=True, log_to_file=False)
    logger1 = managed_gda_logger("gda.idempotent", cfg)
    count_1 = len(logger1.logger.handlers)
    logger2 = managed_gda_logger("gda.idempotent", cfg)
    count_2 = len(logger2.logger.handlers)
    assert count_1 == 1
    assert count_2 == 1


# ==============================================================================
# GROUP 5: Filesystem, CLI & Integration
# Note: File emissions, base_dir anchoring, rollover, close(), and context manager.
# ==============================================================================


@pytest.mark.integration
def test_gda_logger_file_output_and_base_dir_anchoring(
    tmp_path: Path,
    managed_gda_logger: Callable[[str, LoggingConfig | None], GDALogger],
) -> None:
    """Verify GDALogger writes JSON lines to explicit and base_dir-anchored log files."""
    log_file = tmp_path / "runtime.log"
    cfg = LoggingConfig(
        level="DEBUG",
        log_to_console=False,
        log_to_file=True,
        log_file_path=str(log_file),
    )
    logger = managed_gda_logger("test.file", cfg)
    logger.debug("Writing entry to disk", details={"item_count": 5})

    payload = json.loads(log_file.read_text(encoding="utf-8").strip())
    assert payload["level"] == "DEBUG"
    assert payload["details"] == {"item_count": 5}

    rel_cfg = LoggingConfig(
        level="INFO",
        log_to_console=False,
        log_to_file=True,
        log_file_path="sub/relative.log",
    )
    with GDALogger(name="test.relative", config=rel_cfg, base_dir=tmp_path) as rel_logger:
        rel_logger.info("Anchored message")
    assert (tmp_path / "sub" / "relative.log").exists()


@pytest.mark.integration
def test_gda_logger_level_filtering_and_error_methods(
    tmp_path: Path,
    managed_gda_logger: Callable[[str, LoggingConfig | None], GDALogger],
) -> None:
    """Verify level filtering and structured error/critical attachment on disk."""
    log_file = tmp_path / "filtered.log"
    cfg = LoggingConfig(
        level="WARNING",
        log_to_console=False,
        log_to_file=True,
        log_file_path=str(log_file),
    )
    logger = managed_gda_logger("test.filter", cfg)
    logger.debug("Filtered debug")
    logger.info("Filtered info")
    logger.warning("Captured warning")
    logger.error(
        "Validation failed",
        exc=ConfigValidationError("Port mismatch", error_code="ERR_PORT"),
    )
    logger.critical("Subsystem crashed", details={"exit_code": 1})

    records = [json.loads(line) for line in log_file.read_text(encoding="utf-8").splitlines()]
    assert [r["level"] for r in records] == ["WARNING", "ERROR", "CRITICAL"]
    assert records[1]["error"]["error_code"] == "ERR_PORT"
    assert records[2]["details"] == {"exit_code": 1}


@pytest.mark.integration
def test_rotating_file_handler_rollover_bounds(
    tmp_path: Path,
    managed_gda_logger: Callable[[str, LoggingConfig | None], GDALogger],
) -> None:
    """Verify RotatingFileHandler triggers rollover and retains backup_count files."""
    log_file = tmp_path / "rollover.log"
    cfg = LoggingConfig(
        level="INFO",
        log_to_console=False,
        log_to_file=True,
        log_file_path=str(log_file),
        max_bytes=1024,
        backup_count=2,
    )
    logger = managed_gda_logger("gda.rollover", cfg)
    payload = "X" * 400
    for idx in range(10):
        logger.info(f"Entry {idx}: {payload}")

    assert log_file.exists()
    assert (tmp_path / "rollover.log.1").exists()


@pytest.mark.integration
@pytest.mark.regression
def test_gda_logger_close_and_context_manager_release_handlers(tmp_path: Path) -> None:
    """Verify GDALogger.close() and with-block exit close handlers and release file locks."""
    log_file = tmp_path / "ctx_lock.log"
    cfg = LoggingConfig(
        level="INFO",
        log_to_console=False,
        log_to_file=True,
        log_file_path=str(log_file),
    )

    # Explicit close()
    logger = GDALogger("gda.explicit_close", config=cfg)
    assert len(logger.logger.handlers) == 1
    logger.info("Before explicit close")
    logger.close()
    assert len(logger.logger.handlers) == 0
    log_file.unlink()
    assert not log_file.exists()

    # Context manager closes handlers even when body raises an exception
    with pytest.raises(RuntimeError, match="abort"), GDALogger("gda.ctx_close", config=cfg) as log:
        assert len(log.logger.handlers) == 1
        log.info("Inside context")
        raise RuntimeError("abort")

    assert len(log.logger.handlers) == 0
    log_file.unlink()
    assert not log_file.exists()


@pytest.mark.integration
@pytest.mark.regression
def test_gda_logger_releases_windows_file_handles_for_unlink(tmp_path: Path) -> None:
    """Verify re-initializing GDALogger closes prior file handlers so unlink succeeds."""
    log_file = tmp_path / "release_lock.log"
    file_cfg = LoggingConfig(
        level="INFO",
        log_to_console=False,
        log_to_file=True,
        log_file_path=str(log_file),
    )
    logger = GDALogger("gda.windows_lock", config=file_cfg)
    logger.info("Acquire file handle")

    console_only = LoggingConfig(level="INFO", log_to_console=False, log_to_file=False)
    logger_reset = GDALogger("gda.windows_lock", config=console_only)
    logger_reset.close()

    log_file.unlink()
    assert not log_file.exists()


# ==============================================================================
# GROUP 6: Integrity & Invariants
# Note: Root logger isolation invariant.
# ==============================================================================


@pytest.mark.integrity
@pytest.mark.unit
def test_gda_logger_disables_root_propagation(
    managed_gda_logger: Callable[[str, LoggingConfig | None], GDALogger],
) -> None:
    """Verify GDALogger disables propagation to prevent duplicate root logger emissions."""
    cfg = LoggingConfig(log_to_console=False, log_to_file=False)
    logger = managed_gda_logger("gda.propagation_check", cfg)
    assert logger.logger.propagate is False
