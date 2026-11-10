"""Path: src/gda/core/dates.py

Temporal parsing, ISO-8601 normalization, and date validation routines.

Operational Role:
    Provides canonical date parsing, extraction, and validation for year-only,
    year-month, and full date strings, as well as Zulu UTC and timezone-offset
    extended timestamps using canonical patterns defined in gda.core.types.
"""

from __future__ import annotations

from datetime import UTC, datetime

from gda.core.errors import ModelFormatError
from gda.core.types import (
    ISO_DATE_REGEX,
    ISO_TIMESTAMP_FMT,
    ISO_TIMESTAMP_REGEX,
)

__version__ = "1.0.0+build.1"

__all__ = [
    "format_utc_timestamp",
    "parse_iso_date_parts",
    "validate_iso_date",
    "validate_iso_timestamp",
]


def validate_iso_date(value: str) -> bool:
    """Validate whether a string matches canonical ISO-8601 partial or full date patterns.

    Args:
        value: Date string candidate to validate.

    Returns:
        True if string matches canonical ISO date format; False otherwise.
    """
    if not isinstance(value, str):
        return False
    return ISO_DATE_REGEX.match(value.strip()) is not None


def validate_iso_timestamp(value: str) -> bool:
    """Validate whether a string matches canonical ISO-8601 timestamp formats.

    Args:
        value: Timestamp string candidate to validate.

    Returns:
        True if string matches canonical ISO timestamp format; False otherwise.
    """
    if not isinstance(value, str):
        return False
    return ISO_TIMESTAMP_REGEX.match(value.strip()) is not None


def format_utc_timestamp(dt: datetime | None = None) -> str:
    """Format a datetime object into a canonical Zulu-formatted ISO-8601 timestamp string.

    Args:
        dt: Optional datetime object. If None, current UTC time is used.

    Returns:
        Zulu-formatted UTC timestamp string (e.g., '2026-11-10T20:45:00Z').
    """
    target = dt if dt is not None else datetime.now(UTC)
    if target.tzinfo is None:
        target = target.replace(tzinfo=UTC)
    else:
        target = target.astimezone(UTC)
    return target.strftime(ISO_TIMESTAMP_FMT)


def parse_iso_date_parts(value: str) -> tuple[int, int | None, int | None]:
    """Parse an ISO date string into its integer year, month, and day components.

    Args:
        value: Canonical ISO date string candidate.

    Returns:
        Tuple of (year, month or None, day or None).

    Raises:
        ModelFormatError: If the input string is not a valid ISO date pattern.
    """
    if not validate_iso_date(value):
        raise ModelFormatError(
            f"Invalid ISO date format: '{value}'",
            error_code="ERR_MODEL_FORMAT",
            details={"value": value},
        )

    parts = [int(p) for p in value.strip().split("-")]
    year = parts[0]
    month = parts[1] if len(parts) > 1 else None
    day = parts[2] if len(parts) > 2 else None
    return year, month, day
