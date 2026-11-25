"""Path: tests/test_gda/test_core/test_core_logging.py

Comprehensive unit, regression, integration, and integrity test suite
for gda.core.logging.

Operational Role:
    Validates GDALogger, JsonFormatter, and ConsoleFormatter across single-line
    JSON log serialization, bracketed console output, structured extra details,
    exception/traceback formatting, rotating file persistence, Windows file-lock
    release (RARE-CORE-06), non-JSON-native error details (GAP-CORE-09), and
    hostile/circular payload resilience (RARE-CORE-04).

Test Structure & Protocol:
    - Atomized & parametrized tests: 1:1 behavioral contract mapping.
    - Fully decorated: 5-marker taxonomy (smoke, unit, regression, integration, integrity).
    - Dependencies: Isolated tmp_path sandboxes with explicit handler teardown.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

import gda.core.logging as log_mod
from gda.core.config import LoggingConfig
from gda.core.errors import ConfigValidationError, GenealogyDeskError
from gda.core.logging import ConsoleFormatter, GDALogger, JsonFormatter

__version__ = "1.0.0+build.10"


def _make_record(
    msg: str,
    *,
    name: str = "gda.test",
    level: int = logging.INFO,
    exc_info: Any = None,
    details: Any = None,
    exc: Exception | None = None,
) -> logging.LogRecord:
    """Build a LogRecord with optional structured details and exception attributes."""
    record = logging.LogRecord(
        name=name,
        level=level,
        pathname=__file__,
        lineno=1,
        msg=msg,
        args=(),
        exc_info=exc_info,
    )
    if details is not None:
        record.details = details
    if exc is not None:
        record.exc = exc
    return record


def _close_logger(gda_logger: GDALogger) -> None:
    """Close and detach all handlers on a GDALogger to release Windows file locks."""
    for handler in list(gda_logger.logger.handlers):
        handler.close()
        gda_logger.logger.removeHandler(handler)


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
def test_json_formatter_standard_record() -> None:
    """Verify JsonFormatter emits canonical single-line JSON with standard fields."""
    formatter = JsonFormatter()
    record = _make_record("Transaction committed", level=logging.INFO)
    payload = json.loads(formatter.format(record))

    assert payload["level"] == "INFO"
    assert payload["logger"] == "gda.test"
    assert payload["message"] == "Transaction committed"
    assert payload["timestamp"].endswith("Z")
    datetime.fromisoformat(payload["timestamp"].replace("Z", "+00:00"))


@pytest.mark.unit
def test_json_formatter_with_structured_details() -> None:
    """Verify JsonFormatter extracts structured 'details' attribute into top-level key."""
    formatter = JsonFormatter()
    record = _make_record(
        "Cache hit",
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
    level: int,
    msg: str,
    details: dict[str, Any] | None,
    expected: str,
) -> None:
    """Verify ConsoleFormatter produces bracketed terminal text with or without details."""
    formatter = ConsoleFormatter()
    record = _make_record(msg, name="gda.cli", level=level, details=details)
    assert formatter.format(record) == expected


@pytest.mark.unit
def test_gda_logger_console_output(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify GDALogger emits to standard stream when log_to_console is True."""
    cfg = LoggingConfig(level="INFO", log_to_console=True, log_to_file=False)
    logger = GDALogger(name="test.console", config=cfg)
    try:
        assert logger.name == "test.console"
        logger.info("Console message verified")
        captured = capsys.readouterr()
        assert "[INFO] [test.console] Console message verified" in (captured.err + captured.out)
    finally:
        _close_logger(logger)


# ==============================================================================
# GROUP 3: Edge Cases & Boundary Conditions
# Note: Single-line newline/unicode escaping (LOG-003) and idempotent handlers (LOG-002).
# ==============================================================================


@pytest.mark.regression
def test_json_formatter_special_characters_and_newlines() -> None:
    """Verify JsonFormatter serializes newlines and unicode onto a single line (LOG-003)."""
    formatter = JsonFormatter()
    record = _make_record("Line 1\nLine 2\tTabbed—Special Char: ñ", name="gda.special")
    formatted = formatter.format(record)
    assert "\n" not in formatted
    assert json.loads(formatted)["message"] == "Line 1\nLine 2\tTabbed—Special Char: ñ"


@pytest.mark.regression
def test_gda_logger_idempotent_handler_attachment() -> None:
    """Verify multiple GDALogger initializations do not stack duplicate handlers (LOG-002)."""
    cfg = LoggingConfig(log_to_console=True, log_to_file=False)
    logger1 = GDALogger("gda.idempotent", config=cfg)
    count_1 = len(logger1.logger.handlers)
    logger2 = GDALogger("gda.idempotent", config=cfg)
    count_2 = len(logger2.logger.handlers)
    _close_logger(logger2)
    assert count_1 == 1
    assert count_2 == 1


# ==============================================================================
# GROUP 4: Error Handling & Validation Failures
# Note: Exception serialization, GAP-CORE-09, and RARE-CORE-04 resilience checks.
# ==============================================================================


@pytest.mark.regression
def test_json_formatter_with_genealogy_desk_error() -> None:
    """Verify JsonFormatter serializes GenealogyDeskError via its .to_dict() contract."""
    formatter = JsonFormatter()
    err = GenealogyDeskError(
        "Connection timeout",
        error_code="ERR_DB_TIMEOUT",
        details={"host": "10.0.0.1"},
    )
    payload = json.loads(formatter.format(_make_record("DB lookup failed", exc=err)))
    assert payload["error"]["error_code"] == "ERR_DB_TIMEOUT"
    assert payload["error"]["message"] == "Connection timeout"
    assert payload["error"]["details"] == {"host": "10.0.0.1"}


@pytest.mark.regression
def test_json_formatter_with_standard_exception() -> None:
    """Verify JsonFormatter serializes generic standard library Exception objects."""
    formatter = JsonFormatter()
    record = _make_record("Parsing failure", level=logging.ERROR, exc=ValueError("Invalid token"))
    payload = json.loads(formatter.format(record))
    assert payload["error"]["type"] == "ValueError"
    assert payload["error"]["message"] == "Invalid token"


@pytest.mark.regression
def test_json_formatter_with_exc_info_traceback() -> None:
    """Verify JsonFormatter extracts traceback details when exc_info is populated."""
    formatter = JsonFormatter()
    try:
        raise ZeroDivisionError("division by zero")
    except ZeroDivisionError:
        exc_info = sys.exc_info()

    record = _make_record("Math domain fault", level=logging.CRITICAL, exc_info=exc_info)
    payload = json.loads(formatter.format(record))
    assert payload["error"]["type"] == "ZeroDivisionError"
    assert payload["error"]["message"] == "division by zero"
    assert "ZeroDivisionError: division by zero" in payload["error"]["traceback"]


@pytest.mark.regression
def test_json_formatter_serializes_non_json_native_error_details() -> None:
    """Verify JsonFormatter safely serializes Path and set values in error details (GAP-CORE-09)."""
    formatter = JsonFormatter()
    err = GenealogyDeskError(
        "Archive read fault",
        error_code="ERR_ARCHIVE_READ",
        details={"path": Path("data/archive.db"), "tags": {"a", "b"}},
    )
    formatted = formatter.format(_make_record("Archive error", level=logging.ERROR, exc=err))
    assert "\n" not in formatted
    payload = json.loads(formatted)
    assert payload["error"]["error_code"] == "ERR_ARCHIVE_READ"


@pytest.mark.regression
def test_json_formatter_handles_non_serializable_object_in_details() -> None:
    """Verify JsonFormatter degrades gracefully on arbitrary objects in details (RARE-CORE-04)."""

    class _OpaqueToken:
        def __repr__(self) -> str:
            return "<OpaqueToken>"

    formatter = JsonFormatter()
    record = _make_record("Opaque detail", details={"token": _OpaqueToken()})
    formatted = formatter.format(record)
    assert "\n" not in formatted
    assert "details" in json.loads(formatted)


@pytest.mark.regression
def test_json_formatter_handles_circular_reference_in_details() -> None:
    """Verify JsonFormatter degrades gracefully on self-referential dict details (RARE-CORE-04)."""
    cyclic: dict[str, Any] = {}
    cyclic["self"] = cyclic

    formatter = JsonFormatter()
    record = _make_record("Cyclic detail", details=cyclic)
    formatted = formatter.format(record)
    assert "\n" not in formatted
    assert json.loads(formatted)["message"] == "Cyclic detail"


@pytest.mark.regression
def test_json_formatter_handles_circular_reference_in_error_details() -> None:
    """Verify circular references inside GenealogyDeskError.details degrade safely."""
    cyclic: dict[str, Any] = {"label": "loop"}
    cyclic["self"] = cyclic
    err = GenealogyDeskError("Cyclic error payload", details=cyclic)

    formatter = JsonFormatter()
    record = _make_record("Error with circular details", level=logging.ERROR, exc=err)
    formatted = formatter.format(record)
    assert "\n" not in formatted
    parsed = json.loads(formatted)
    assert parsed["message"] == "Error with circular details"
    assert "details" not in parsed
    assert "error" in parsed
    assert "Cyclic error payload" in parsed["error"]


# ==============================================================================
# GROUP 5: Filesystem, CLI & Integration
# Note: File emissions, base_dir anchoring, level filtering, rollover, and RARE-CORE-06.
# ==============================================================================


@pytest.mark.integration
def test_gda_logger_file_output_and_base_dir_anchoring(tmp_path: Path) -> None:
    """Verify GDALogger writes JSON lines to explicit and base_dir-anchored log files."""
    log_file = tmp_path / "runtime.log"
    cfg = LoggingConfig(
        level="DEBUG",
        log_to_console=False,
        log_to_file=True,
        log_file_path=str(log_file),
    )
    logger = GDALogger(name="test.file", config=cfg)
    try:
        logger.debug("Writing entry to disk", details={"item_count": 5})
    finally:
        _close_logger(logger)

    payload = json.loads(log_file.read_text(encoding="utf-8").strip())
    assert payload["level"] == "DEBUG"
    assert payload["details"] == {"item_count": 5}

    rel_cfg = LoggingConfig(
        level="INFO",
        log_to_console=False,
        log_to_file=True,
        log_file_path="sub/relative.log",
    )
    rel_logger = GDALogger(name="test.relative", config=rel_cfg, base_dir=tmp_path)
    try:
        rel_logger.info("Anchored message")
    finally:
        _close_logger(rel_logger)
    assert (tmp_path / "sub" / "relative.log").exists()


@pytest.mark.integration
def test_gda_logger_level_filtering_and_error_methods(tmp_path: Path) -> None:
    """Verify level filtering and structured error/critical attachment on disk."""
    log_file = tmp_path / "filtered.log"
    cfg = LoggingConfig(
        level="WARNING",
        log_to_console=False,
        log_to_file=True,
        log_file_path=str(log_file),
    )
    logger = GDALogger(name="test.filter", config=cfg)
    try:
        logger.debug("Filtered debug")
        logger.info("Filtered info")
        logger.warning("Captured warning")
        logger.error(
            "Validation failed",
            exc=ConfigValidationError("Port mismatch", error_code="ERR_PORT"),
        )
        logger.critical("Subsystem crashed", details={"exit_code": 1})
    finally:
        _close_logger(logger)

    records = [json.loads(line) for line in log_file.read_text(encoding="utf-8").splitlines()]
    assert [r["level"] for r in records] == ["WARNING", "ERROR", "CRITICAL"]
    assert records[1]["error"]["error_code"] == "ERR_PORT"
    assert records[2]["details"] == {"exit_code": 1}


@pytest.mark.integration
def test_rotating_file_handler_rollover_bounds(tmp_path: Path) -> None:
    """Verify RotatingFileHandler triggers rollover and retains backup_count files (LOG-001)."""
    log_file = tmp_path / "rollover.log"
    cfg = LoggingConfig(
        level="INFO",
        log_to_console=False,
        log_to_file=True,
        log_file_path=str(log_file),
        max_bytes=1024,
        backup_count=2,
    )
    logger = GDALogger("gda.rollover", config=cfg)
    try:
        payload = "X" * 400
        for idx in range(10):
            logger.info(f"Entry {idx}: {payload}")
    finally:
        _close_logger(logger)

    assert log_file.exists()
    assert (tmp_path / "rollover.log.1").exists()


@pytest.mark.integration
@pytest.mark.regression
def test_gda_logger_releases_windows_file_handles_for_unlink(tmp_path: Path) -> None:
    """Verify re-initializing GDALogger closes prior file handlers so unlink succeeds (RARE-CORE-06)."""
    log_file = tmp_path / "release_lock.log"
    file_cfg = LoggingConfig(
        level="INFO",
        log_to_console=False,
        log_to_file=True,
        log_file_path=str(log_file),
    )
    logger = GDALogger("gda.windows_lock", config=file_cfg)
    logger.info("Acquire file handle")

    # Re-initializing on the same logger name without file logging must close the old handle
    console_only = LoggingConfig(level="INFO", log_to_console=False, log_to_file=False)
    logger_reset = GDALogger("gda.windows_lock", config=console_only)
    _close_logger(logger_reset)

    log_file.unlink()
    assert not log_file.exists()


# ==============================================================================
# GROUP 6: Integrity & Invariants
# Note: Root logger isolation invariant.
# ==============================================================================


@pytest.mark.integrity
@pytest.mark.unit
def test_gda_logger_disables_root_propagation() -> None:
    """Verify GDALogger disables propagation to prevent duplicate root logger emissions."""
    cfg = LoggingConfig(log_to_console=False, log_to_file=False)
    logger = GDALogger("gda.propagation_check", config=cfg)
    try:
        assert logger.logger.propagate is False
    finally:
        _close_logger(logger)
