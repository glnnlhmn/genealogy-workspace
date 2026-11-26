"""Path: tests/test_gda/test_core/test_core_logging.py

Comprehensive unit, regression, integration, and integrity test suite
for gda.core.logging.

Operational Role:
    Validates GDALogger, JsonFormatter, and ConsoleFormatter across single-line
    JSON log serialization, bracketed console output, structured extra details,
    exception/traceback formatting, rotating file persistence, Windows file-lock
    release, context manager lifecycle, non-JSON-native error details, and
    Hypothesis fuzzing against exotic/circular payloads.

Test Structure & Protocol:
    - Atomized & parametrized tests: 1:1 behavioral contract mapping.
    - Fully decorated: 5-marker taxonomy (smoke, unit, regression, integration, integrity).
    - Dependencies: Shared conftest.py fixtures (make_log_record, managed_gda_logger)
      and Hypothesis strategies (exotic_log_details).
"""

from __future__ import annotations

import json
import logging
import sys
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest
from hypothesis import given
from tests.test_gda.test_core.strategies import exotic_log_details

import gda.core.logging as log_mod
from gda.core.config import LoggingConfig
from gda.core.errors import ConfigValidationError, GenealogyDeskError
from gda.core.logging import ConsoleFormatter, GDALogger, JsonFormatter

__version__ = "1.0.0+build.11"


# ==============================================================================
# GROUP 1: Smoke & Primary Entrypoints
# Note: Single smoke contract check verifying gda.core.logging public exports.
# ==============================================================================


@pytest.mark.smoke
@pytest.mark.unit
def test_logging_exposes_expected_public_interface() -> None:
    """Verify gda.core.logging exports ConsoleFormatter, GDALogger, and JsonFormatter."""
    assert set(log_mod.__all__) == {"ConsoleFormatter", "GDALogger", "JsonFormatter"}


# ==============================================================================
# GROUP 2: Core Logic & Happy Paths
# Note: Canonical JSON/console formatting and console stream emission.
# ==============================================================================


@pytest.mark.unit
def test_json_formatter_standard_record(
    make_log_record: Callable[..., logging.LogRecord],
) -> None:
    """Verify JsonFormatter emits canonical single-line JSON with standard fields."""
    formatter = JsonFormatter()
    record = make_log_record(name="gda.test", msg="Transaction committed", level=logging.INFO)
    payload = json.loads(formatter.format(record))

    assert payload["level"] == "INFO"
    assert payload["logger"] == "gda.test"
    assert payload["message"] == "Transaction committed"
    assert payload["timestamp"].endswith("Z")
    datetime.fromisoformat(payload["timestamp"].replace("Z", "+00:00"))


@pytest.mark.unit
def test_json_formatter_with_structured_details(
    make_log_record: Callable[..., logging.LogRecord],
) -> None:
    """Verify JsonFormatter extracts structured 'details' attribute into top-level key."""
    formatter = JsonFormatter()
    record = make_log_record(
        name="gda.test",
        msg="Cache hit",
        level=logging.DEBUG,
        details={"cache_key": "rec_123", "ttl": 300},
    )
    payload = json.loads(formatter.format(record))
    assert payload["details"] == {"cache_key": "rec_123", "ttl": 300}


@pytest.mark.unit
@pytest.mark.parametrize(
    ("level", "msg", "details", "expected"),
    [
        (
            logging.WARNING,
            "Disk approaching threshold",
            {"usage_pct": 89},
            "[WARNING] [gda.cli] Disk approaching threshold | details={'usage_pct': 89}",
        ),
        (
            logging.INFO,
            "Task initiated",
            None,
            "[INFO] [gda.cli] Task initiated",
        ),
    ],
)
def test_console_formatter_formatting(
    make_log_record: Callable[..., logging.LogRecord],
    level: int,
    msg: str,
    details: dict[str, Any] | None,
    expected: str,
) -> None:
    """Verify ConsoleFormatter produces bracketed terminal text with or without details."""
    formatter = ConsoleFormatter()
    record = make_log_record(name="gda.cli", level=level, msg=msg, details=details)
    assert formatter.format(record) == expected


@pytest.mark.unit
def test_gda_logger_console_output(
    capsys: pytest.CaptureFixture[str],
    managed_gda_logger: Callable[[str, LoggingConfig | None], GDALogger],
) -> None:
    """Verify GDALogger emits to standard stream when log_to_console is True."""
    cfg = LoggingConfig(level="INFO", log_to_console=True, log_to_file=False)
    logger = managed_gda_logger("test.console", cfg)
    assert logger.name == "test.console"
    logger.info("Console message verified")
    captured = capsys.readouterr()
    assert "[INFO] [test.console] Console message verified" in (captured.err + captured.out)


# ==============================================================================
# GROUP 3: Edge Cases & Boundary Conditions
# Note: Single-line newline/unicode escaping and idempotent handler attachment.
# ==============================================================================


@pytest.mark.regression
def test_json_formatter_special_characters_and_newlines(
    make_log_record: Callable[..., logging.LogRecord],
) -> None:
    """Verify JsonFormatter serializes newlines and unicode onto a single line."""
    formatter = JsonFormatter()
    record = make_log_record(
        name="gda.special",
        msg="Line 1\nLine 2\tTabbed—Special Char: ñ",
    )
    formatted = formatter.format(record)
    assert "\n" not in formatted
    assert json.loads(formatted)["message"] == "Line 1\nLine 2\tTabbed—Special Char: ñ"


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
# GROUP 4: Error Handling & Validation Failures
# Note: Exception serialization (JSON & Console) and hostile payload resilience.
# ==============================================================================


@pytest.mark.regression
def test_json_formatter_with_genealogy_desk_error(
    make_log_record: Callable[..., logging.LogRecord],
) -> None:
    """Verify JsonFormatter serializes GenealogyDeskError via its .to_dict() contract."""
    formatter = JsonFormatter()
    err = GenealogyDeskError(
        "Connection timeout",
        error_code="ERR_DB_TIMEOUT",
        details={"host": "10.0.0.1"},
    )
    record = make_log_record(name="gda.test", msg="DB lookup failed", exc=err)
    payload = json.loads(formatter.format(record))
    assert payload["error"]["error_code"] == "ERR_DB_TIMEOUT"
    assert payload["error"]["message"] == "Connection timeout"
    assert payload["error"]["details"] == {"host": "10.0.0.1"}


@pytest.mark.regression
def test_json_formatter_with_standard_exception(
    make_log_record: Callable[..., logging.LogRecord],
) -> None:
    """Verify JsonFormatter serializes generic standard library Exception objects."""
    formatter = JsonFormatter()
    record = make_log_record(
        name="gda.test",
        msg="Parsing failure",
        level=logging.ERROR,
        exc=ValueError("Invalid token"),
    )
    payload = json.loads(formatter.format(record))
    assert payload["error"]["type"] == "ValueError"
    assert payload["error"]["message"] == "Invalid token"


@pytest.mark.regression
def test_json_formatter_with_exc_info_traceback(
    make_log_record: Callable[..., logging.LogRecord],
) -> None:
    """Verify JsonFormatter extracts traceback details when exc_info is populated."""
    formatter = JsonFormatter()
    try:
        raise ZeroDivisionError("division by zero")
    except ZeroDivisionError:
        exc_info = sys.exc_info()

    record = make_log_record(
        name="gda.test",
        msg="Math domain fault",
        level=logging.CRITICAL,
        exc_info=exc_info,
    )
    payload = json.loads(formatter.format(record))
    assert payload["error"]["type"] == "ZeroDivisionError"
    assert payload["error"]["message"] == "division by zero"
    assert "ZeroDivisionError: division by zero" in payload["error"]["traceback"]


@pytest.mark.regression
@pytest.mark.unit
def test_console_formatter_renders_attached_exc_and_exc_info(
    make_log_record: Callable[..., logging.LogRecord],
) -> None:
    """Verify ConsoleFormatter renders attached exc and exc_info traceback details."""
    formatter = ConsoleFormatter()

    gda_err = GenealogyDeskError("Disk full", error_code="ERR_DISK_FULL")
    rec_gda = make_log_record(name="gda.cli", level=logging.ERROR, msg="Write failed", exc=gda_err)
    out_gda = formatter.format(rec_gda)
    assert "[ERROR] [gda.cli] Write failed" in out_gda
    assert "ERR_DISK_FULL" in out_gda
    assert "Disk full" in out_gda

    rec_std = make_log_record(
        name="gda.cli",
        level=logging.ERROR,
        msg="Parse failed",
        exc=ValueError("Bad token"),
    )
    out_std = formatter.format(rec_std)
    assert "ValueError" in out_std
    assert "Bad token" in out_std

    try:
        raise RuntimeError("boom")
    except RuntimeError:
        exc_info = sys.exc_info()
    rec_tb = make_log_record(
        name="gda.cli",
        level=logging.CRITICAL,
        msg="Unhandled fault",
        exc_info=exc_info,
    )
    out_tb = formatter.format(rec_tb)
    assert "RuntimeError: boom" in out_tb


@pytest.mark.regression
def test_json_formatter_serializes_non_json_native_error_details(
    make_log_record: Callable[..., logging.LogRecord],
) -> None:
    """Verify JsonFormatter safely serializes Path and set values in error details."""
    formatter = JsonFormatter()
    err = GenealogyDeskError(
        "Archive read fault",
        error_code="ERR_ARCHIVE_READ",
        details={"path": Path("data/archive.db"), "tags": {"a", "b"}},
    )
    record = make_log_record(name="gda.test", msg="Archive error", level=logging.ERROR, exc=err)
    formatted = formatter.format(record)
    assert "\n" not in formatted
    payload = json.loads(formatted)
    assert payload["error"]["error_code"] == "ERR_ARCHIVE_READ"


@pytest.mark.regression
def test_json_formatter_handles_non_serializable_object_in_details(
    make_log_record: Callable[..., logging.LogRecord],
) -> None:
    """Verify JsonFormatter degrades gracefully on arbitrary objects in details."""

    class _OpaqueToken:
        def __repr__(self) -> str:
            return "<OpaqueToken>"

    formatter = JsonFormatter()
    record = make_log_record(
        name="gda.test", msg="Opaque detail", details={"token": _OpaqueToken()}
    )
    formatted = formatter.format(record)
    assert "\n" not in formatted
    assert "details" in json.loads(formatted)


@pytest.mark.regression
def test_json_formatter_handles_circular_reference_in_details(
    make_log_record: Callable[..., logging.LogRecord],
) -> None:
    """Verify JsonFormatter degrades gracefully on self-referential dict details."""
    cyclic: dict[str, Any] = {}
    cyclic["self"] = cyclic

    formatter = JsonFormatter()
    record = make_log_record(name="gda.test", msg="Cyclic detail", details=cyclic)
    formatted = formatter.format(record)
    assert "\n" not in formatted
    assert json.loads(formatted)["message"] == "Cyclic detail"


@pytest.mark.regression
def test_json_formatter_handles_circular_reference_in_error_details(
    make_log_record: Callable[..., logging.LogRecord],
) -> None:
    """Verify circular references inside GenealogyDeskError.details degrade safely."""
    cyclic: dict[str, Any] = {"label": "loop"}
    cyclic["self"] = cyclic
    err = GenealogyDeskError("Cyclic error payload", details=cyclic)

    formatter = JsonFormatter()
    record = make_log_record(
        name="gda.test",
        msg="Error with circular details",
        level=logging.ERROR,
        exc=err,
    )
    formatted = formatter.format(record)
    assert "\n" not in formatted
    parsed = json.loads(formatted)
    assert parsed["message"] == "Error with circular details"
    assert "details" not in parsed
    assert "error" in parsed
    assert "Cyclic error payload" in parsed["error"]


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
# Note: Root logger isolation invariant and Hypothesis exotic-details fuzzing.
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


@pytest.mark.integrity
@pytest.mark.unit
@given(details=exotic_log_details())
def test_json_formatter_fuzz_exotic_details_always_valid_single_line_json(
    details: dict[str, Any],
) -> None:
    """Verify JsonFormatter always emits valid single-line JSON for exotic detail payloads."""
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="gda.fuzz",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="Fuzz payload",
        args=(),
        exc_info=None,
    )
    record.details = details
    formatted = formatter.format(record)
    assert "\n" not in formatted
    parsed = json.loads(formatted)
    assert parsed["message"] == "Fuzz payload"
