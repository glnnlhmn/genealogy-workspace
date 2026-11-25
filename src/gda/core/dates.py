"""Path: src/gda/core/dates.py

Temporal parsing, ISO-8601 normalization, and date validation routines.

Operational Role:
    Provides canonical date parsing, extraction, and validation for year-only,
    year-month, and full date strings, as well as Zulu UTC timestamps, current
    clock helpers, and chronological age calculations between genealogical dates.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any

from gda.core.errors import ModelFormatError, ModelRangeError
from gda.core.types import (
    ISO_DATE_FMT,
    ISO_DATE_REGEX,
    ISO_TIMESTAMP_FMT,
    ISO_TIMESTAMP_REGEX,
    is_strict_int,
)

__version__ = "1.0.0+build.6"

__all__ = [
    "calculate_age_years",
    "format_utc_timestamp",
    "parse_iso_date_parts",
    "parse_iso_timestamp",
    "utc_now_iso",
    "utc_today_iso",
    "validate_iso_date",
    "validate_iso_timestamp",
]


def validate_iso_date(value: Any) -> bool:
    """Validate whether a value matches canonical ISO-8601 partial or full date patterns.

    Enforces both structural regex syntax ('YYYY', 'YYYY-MM', 'YYYY-MM-DD') and
    real Gregorian calendar day bounds (rejecting impossible dates such as
    February 30 or April 31).

    Args:
        value: Date string candidate to validate.

    Returns:
        True if value is a string matching canonical ISO date format and
        calendar bounds; False otherwise.
    """
    if not isinstance(value, str):
        return False

    cleaned = value.strip()
    if ISO_DATE_REGEX.match(cleaned) is None:
        return False

    parts = cleaned.split("-")
    if len(parts) == 3:
        try:
            date(int(parts[0]), int(parts[1]), int(parts[2]))
        except ValueError:
            return False

    return True


def validate_iso_timestamp(value: Any) -> bool:
    """Validate whether a value matches canonical ISO-8601 timestamp formats.

    Enforces both structural regex syntax and real Gregorian calendar/clock
    bounds (rejecting impossible dates such as '2026-02-30T12:00:00Z').

    Args:
        value: Timestamp string candidate to validate.

    Returns:
        True if value is a string matching canonical ISO timestamp format and
        calendar bounds; False otherwise.
    """
    if not isinstance(value, str):
        return False

    cleaned = value.strip()
    if ISO_TIMESTAMP_REGEX.match(cleaned) is None:
        return False

    try:
        datetime.fromisoformat(cleaned.replace("Z", "+00:00"))
    except ValueError:
        return False

    return True


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


def utc_now_iso() -> str:
    """Return the current UTC moment formatted as a canonical Zulu ISO-8601 timestamp.

    Returns:
        Canonical Zulu timestamp string (e.g., '2026-11-10T20:45:00Z').
    """
    return format_utc_timestamp()


def utc_today_iso() -> str:
    """Return today's UTC calendar date formatted as 'YYYY-MM-DD'.

    Returns:
        Canonical ISO-8601 calendar date string.
    """
    return datetime.now(UTC).strftime(ISO_DATE_FMT)


def parse_iso_timestamp(value: str) -> datetime:
    """Parse an ISO-8601 timestamp string into a UTC-aware datetime object.

    Args:
        value: Canonical ISO-8601 timestamp string candidate.

    Returns:
        Timezone-aware datetime object in UTC.

    Raises:
        ModelFormatError: If the input string is not a valid ISO-8601 timestamp.
    """
    if not validate_iso_timestamp(value):
        raise ModelFormatError(
            f"Invalid ISO timestamp format: '{value}'",
            details={"value": value},
        )
    clean = value.strip().replace("Z", "+00:00")
    return datetime.fromisoformat(clean).astimezone(UTC)


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
            details={"value": value},
        )

    parts = [int(p) for p in value.strip().split("-")]
    year = parts[0]
    month = parts[1] if len(parts) > 1 else None
    day = parts[2] if len(parts) > 2 else None
    return year, month, day


def _coerce_date_components(
    value: Any,
    field_label: str,
) -> tuple[int, int | None, int | None]:
    """Unwrap and parse a date representation into (year, month, day) components."""
    raw = value.value if hasattr(value, "value") and not isinstance(value, int) else value
    if is_strict_int(raw):
        return int(raw), None, None
    if isinstance(raw, str):
        return parse_iso_date_parts(raw)
    raise ModelFormatError(
        f"Unsupported {field_label} type: {type(value).__name__}",
        details={field_label.replace(" ", "_"): str(value)},
    )


def calculate_age_years(
    birth_date: Any,
    target_date: Any,
) -> int:
    """Calculate elapsed integer age in full completed years between birth and target date.

    Supports ISO date strings ('YYYY', 'YYYY-MM', 'YYYY-MM-DD'), integer calendar years
    (including IntEnum members), or atomic year/date representations exposing a .value
    attribute.

    Args:
        birth_date: Birth date representation (str, int, IntEnum, or atom).
        target_date: Death or event date representation (str, int, IntEnum, or atom).

    Returns:
        Completed integer years of age.

    Raises:
        ModelFormatError: If either date format cannot be resolved or parsed.
        ModelRangeError: If target_date chronologically precedes birth_date.
    """
    b_year, b_month, b_day = _coerce_date_components(birth_date, "birth date")
    d_year, d_month, d_day = _coerce_date_components(target_date, "target date")

    age = d_year - b_year
    if b_month is not None and d_month is not None:
        if (d_month < b_month) or (
            d_month == b_month and b_day is not None and d_day is not None and d_day < b_day
        ):
            age -= 1

    if age < 0:
        raise ModelRangeError(
            f"Target date '{target_date}' precedes birth date '{birth_date}'.",
            details={"birth_date": str(birth_date), "target_date": str(target_date)},
        )

    return age
