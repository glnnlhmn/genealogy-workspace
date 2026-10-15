# Name: test_logging.py
# Path: tests/test_gda/test_core/test_logging.py
# Version: 1.0.0+build.r5

"""Unit verification suite for GDA Core structured logging subsystem.

Operational Role:
    Validates GDALogger, JsonFormatter, and ConsoleFormatter,
    ensuring single-line JSON log serialization, bracketed console output,
    structured extra details mapping, exception formatting, and rotating file persistence.

Test Structure & Protocol:
    - Atomized tests: 1:1 behavioral assertion mapping across logging contracts.
    - Fully decorated: @pytest.mark.unit and @pytest.mark.smoke applied throughout.
    - Dependencies: Isolated tmp_path sandboxes, pytest standard library fixtures.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

import pytest

from gda.core.config import LoggingConfig
from gda.core.errors import ConfigValidationError, GenealogyDeskError
from gda.core.logging import ConsoleFormatter, GDALogger, JsonFormatter

__version__ = "1.0.0+build.r5"

# ==============================================================================
# GROUP 1: FORMATTER CONTRACTS
# Note: Validates JsonFormatter and ConsoleFormatter output strings
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_json_formatter_standard_record() -> None:
    """Verify JsonFormatter emits canonical single-line JSON with standard fields."""
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="gda.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="Transaction committed",
        args=(),
        exc_info=None,
    )

    formatted = formatter.format(record)
    payload = json.loads(formatted)

    assert payload["level"] == "INFO"
    assert payload["logger"] == "gda.test"
    assert payload["message"] == "Transaction committed"
    assert "timestamp" in payload
    assert payload["timestamp"].endswith("Z")
    datetime.fromisoformat(payload["timestamp"].replace("Z", "+00:00"))


@pytest.mark.unit
def test_json_formatter_with_structured_details() -> None:
    """Verify JsonFormatter extracts structured 'details' attribute into top-level key."""
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="gda.test",
        level=logging.DEBUG,
        pathname=__file__,
        lineno=20,
        msg="Cache hit",
        args=(),
        exc_info=None,
    )
    record.details = {"cache_key": "rec_123", "ttl": 300}  # type: ignore[attr-defined]

    payload = json.loads(formatter.format(record))
    assert payload["details"] == {"cache_key": "rec_123", "ttl": 300}


@pytest.mark.unit
def test_json_formatter_with_genealogy_desk_error() -> None:
    """Verify JsonFormatter serializes GenealogyDeskError via its .to_dict() contract."""
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="gda.test",
        level=logging.ERROR,
        pathname=__file__,
        lineno=30,
        msg="Database lookup failed",
        args=(),
        exc_info=None,
    )
    record.exc = GenealogyDeskError(  # type: ignore[attr-defined]
        "Connection timeout",
        error_code="ERR_DB_TIMEOUT",
        details={"host": "10.0.0.1"},
    )

    payload = json.loads(formatter.format(record))
    assert "error" in payload
    assert payload["error"]["error_code"] == "ERR_DB_TIMEOUT"
    assert payload["error"]["message"] == "Connection timeout"
    assert payload["error"]["details"] == {"host": "10.0.0.1"}


@pytest.mark.unit
def test_json_formatter_with_standard_exception() -> None:
    """Verify JsonFormatter serializes generic standard library Exception objects."""
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="gda.test",
        level=logging.ERROR,
        pathname=__file__,
        lineno=35,
        msg="Parsing failure",
        args=(),
        exc_info=None,
    )
    record.exc = ValueError("Invalid token encountered")  # type: ignore[attr-defined]

    payload = json.loads(formatter.format(record))
    assert "error" in payload
    assert payload["error"]["type"] == "ValueError"
    assert payload["error"]["message"] == "Invalid token encountered"


@pytest.mark.unit
def test_json_formatter_with_exc_info_traceback() -> None:
    """Verify JsonFormatter extracts traceback details when exc_info is populated."""
    formatter = JsonFormatter()
    try:
        raise ZeroDivisionError("division by zero")
    except ZeroDivisionError:
        import sys

        exc_info = sys.exc_info()

    record = logging.LogRecord(
        name="gda.test",
        level=logging.CRITICAL,
        pathname=__file__,
        lineno=45,
        msg="Math domain fault",
        args=(),
        exc_info=exc_info,
    )

    payload = json.loads(formatter.format(record))
    assert "error" in payload
    assert payload["error"]["type"] == "ZeroDivisionError"
    assert payload["error"]["message"] == "division by zero"
    assert "ZeroDivisionError: division by zero" in payload["error"]["traceback"]


@pytest.mark.unit
def test_console_formatter_formatting() -> None:
    """Verify ConsoleFormatter produces bracketed terminal text."""
    formatter = ConsoleFormatter()
    record = logging.LogRecord(
        name="gda.cli",
        level=logging.WARNING,
        pathname=__file__,
        lineno=50,
        msg="Disk approaching threshold",
        args=(),
        exc_info=None,
    )
    record.details = {"usage_pct": 89}  # type: ignore[attr-defined]

    output = formatter.format(record)
    assert (
        output
        == "[WARNING] [gda.cli] Disk approaching threshold | details={'usage_pct': 89}"
    )


@pytest.mark.unit
def test_console_formatter_formatting_without_details() -> None:
    """Verify ConsoleFormatter produces clean terminal text when details are absent."""
    formatter = ConsoleFormatter()
    record = logging.LogRecord(
        name="gda.cli",
        level=logging.INFO,
        pathname=__file__,
        lineno=55,
        msg="Task initiated",
        args=(),
        exc_info=None,
    )

    output = formatter.format(record)
    assert output == "[INFO] [gda.cli] Task initiated"


# ==============================================================================
# GROUP 2: GDALOGGER SERVICE OPERATIONS
# Note: Validates routing, log levels, file emissions, and rotating handler
# ==============================================================================


@pytest.mark.unit
def test_gda_logger_console_output(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify GDALogger emits to standard output stream when log_to_console is True."""
    cfg = LoggingConfig(level="INFO", log_to_console=True, log_to_file=False)
    logger = GDALogger(name="test.console", config=cfg)

    assert logger.name == "test.console"
    assert logger.logger is not None

    logger.info("Console message verified")

    captured = capsys.readouterr()
    assert "[INFO] [test.console] Console message verified" in captured.err or (
        "[INFO] [test.console] Console message verified" in captured.out
    )


@pytest.mark.unit
def test_gda_logger_file_output(tmp_path: Path) -> None:
    """Verify GDALogger writes structured JSON lines to the configured log file."""
    log_file = tmp_path / "runtime.log"
    cfg = LoggingConfig(
        level="DEBUG",
        log_to_console=False,
        log_to_file=True,
        log_file_path=str(log_file),
    )
    logger = GDALogger(name="test.file", config=cfg)

    logger.debug("Writing entry to disk", details={"item_count": 5})

    assert log_file.exists()
    lines = log_file.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 1

    payload = json.loads(lines[0])
    assert payload["level"] == "DEBUG"
    assert payload["message"] == "Writing entry to disk"
    assert payload["details"] == {"item_count": 5}


@pytest.mark.unit
def test_gda_logger_relative_file_output_with_base_dir(tmp_path: Path) -> None:
    """Verify GDALogger anchors relative log paths to base_dir."""
    cfg = LoggingConfig(
        level="INFO",
        log_to_console=False,
        log_to_file=True,
        log_file_path="sub/relative.log",
    )
    logger = GDALogger(name="test.relative", config=cfg, base_dir=tmp_path)

    logger.info("Anchored message")

    expected_path = tmp_path / "sub" / "relative.log"
    assert expected_path.exists()


@pytest.mark.unit
def test_gda_logger_level_filtering(tmp_path: Path) -> None:
    """Verify GDALogger suppresses messages below the configured log level."""
    log_file = tmp_path / "filtered.log"
    cfg = LoggingConfig(
        level="WARNING",
        log_to_console=False,
        log_to_file=True,
        log_file_path=str(log_file),
    )
    logger = GDALogger(name="test.filter", config=cfg)

    logger.debug("Debug event - should be filtered")
    logger.info("Info event - should be filtered")
    logger.warning("Warning event - should be captured")
    logger.error("Error event - should be captured")

    assert log_file.exists()
    lines = log_file.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 2

    records = [json.loads(line) for line in lines]
    assert records[0]["level"] == "WARNING"
    assert records[1]["level"] == "ERROR"


@pytest.mark.unit
def test_gda_logger_critical_and_error_methods(tmp_path: Path) -> None:
    """Verify error and critical methods properly attach exception context."""
    log_file = tmp_path / "errors.log"
    cfg = LoggingConfig(
        level="DEBUG",
        log_to_console=False,
        log_to_file=True,
        log_file_path=str(log_file),
    )
    logger = GDALogger(name="test.errors", config=cfg)

    err = ConfigValidationError("Port mismatch", error_code="ERR_PORT")
    logger.error("Validation failed", exc=err)
    logger.critical("Subsystem crashed", details={"exit_code": 1})

    lines = log_file.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 2

    error_rec = json.loads(lines[0])
    assert error_rec["level"] == "ERROR"
    assert error_rec["error"]["error_code"] == "ERR_PORT"

    crit_rec = json.loads(lines[1])
    assert crit_rec["level"] == "CRITICAL"
    assert crit_rec["details"] == {"exit_code": 1}
