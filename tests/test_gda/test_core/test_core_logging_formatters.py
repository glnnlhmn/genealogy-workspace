"""Path: tests/test_gda/test_core/test_core_logging_formatters.py

Unit, regression, and property-based tests for JsonFormatter and ConsoleFormatter.

Operational Role:
    Validates JsonFormatter and ConsoleFormatter across single-line JSON
    serialization, bracketed console text, structured details, exception and
    traceback formatting, circular/non-serializable fallback handling, and
    Hypothesis fuzzing against exotic detail payloads.

Test Structure & Protocol:
    - Atomized & parametrized tests: 1:1 behavioral contract mapping.
    - Fully decorated: 5-marker taxonomy (smoke, unit, regression, integrity).
    - Dependencies: Shared conftest.py fixtures (make_log_record) and
      Hypothesis strategies (exotic_log_details).
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
from gda.core.errors import GenealogyDeskError
from gda.core.logging import ConsoleFormatter, JsonFormatter

__version__ = "1.0.0+build.1"


# ==============================================================================
# GROUP 1: Smoke & Primary Entrypoints
# Note: Verifies formatter exports and basic JSON/console rendering.
# ==============================================================================


@pytest.mark.smoke
@pytest.mark.unit
def test_logging_formatters_exported_from_core_logging() -> None:
    """Verify ConsoleFormatter and JsonFormatter are exported by gda.core.logging."""
    assert {"ConsoleFormatter", "JsonFormatter"}.issubset(set(log_mod.__all__))


# ==============================================================================
# GROUP 2: Core Logic & Happy Paths
# Note: Canonical JSON and console formatting with and without details.
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


# ==============================================================================
# GROUP 3: Edge Cases & Boundary Conditions
# Note: Single-line newline and Unicode escaping in JSON formatter.
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
# GROUP 6: Integrity & Invariants
# Note: Hypothesis fuzzing against exotic detail payloads.
# ==============================================================================


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
