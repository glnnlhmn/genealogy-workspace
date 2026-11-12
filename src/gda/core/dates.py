"""Path: src/gda/core/dates.py

Temporal parsing, ISO-8601 normalization, and date validation routines.

Operational Role:
    Provides canonical date parsing, extraction, and validation for year-only,
    year-month, and full date strings, as well as Zulu UTC timestamps, current
    clock helpers, and chronological age calculations between genealogical dates.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from gda.core.errors import ModelFormatError, ModelRangeError
from gda.core.types import (
    ISO_DATE_REGEX,
    ISO_TIMESTAMP_FMT,
    ISO_TIMESTAMP_REGEX,
)

__version__ = "1.0.0+build.3"

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
    return datetime.now(UTC).strftime("%Y-%m-%d")


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
            error_code="ERR_MODEL_FORMAT",
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
            error_code="ERR_MODEL_FORMAT",
            details={"value": value},
        )

    parts = [int(p) for p in value.strip().split("-")]
    year = parts[0]
    month = parts[1] if len(parts) > 1 else None
    day = parts[2] if len(parts) > 2 else None
    return year, month, day


def calculate_age_years(
    birth_date: Any,
    target_date: Any,
) -> int:
    """Calculate elapsed integer age in full completed years between birth and target date.

    Supports ISO date strings ('YYYY', 'YYYY-MM', 'YYYY-MM-DD'), integer calendar years,
    or atomic year/date representations exposing an integer or value attribute.

    Args:
        birth_date: Birth date representation (str, int, or atom).
        target_date: Death or event date representation (str, int, or atom).

    Returns:
        Completed integer years of age.

    Raises:
        ModelFormatError: If either date format cannot be resolved or parsed.
        ModelRangeError: If target_date chronologically precedes birth_date.
    """
    # Extract raw value if an atom was passed
    b_raw = birth_date.value if hasattr(birth_date, "value") else birth_date
    t_raw = target_date.value if hasattr(target_date, "value") else target_date

    # Resolve birthdate components
    if type(b_raw) is int:
        b_year, b_month, b_day = b_raw, None, None
    elif isinstance(b_raw, str):
        b_year, b_month, b_day = parse_iso_date_parts(b_raw)
    else:
        raise ModelFormatError(
            f"Unsupported birth date type: expected int or ISO str, got {type(b_raw).__name__}.",
            error_code="ERR_MODEL_FORMAT",
            details={"birth_date": str(birth_date)},
        )

    # Resolve target date components
    if type(t_raw) is int:
        t_year, t_month, t_day = t_raw, None, None
    elif isinstance(t_raw, str):
        t_year, t_month, t_day = parse_iso_date_parts(t_raw)
    else:
        raise ModelFormatError(
            f"Unsupported target date type: expected int or ISO str, got {type(t_raw).__name__}.",
            error_code="ERR_MODEL_FORMAT",
            details={"target_date": str(target_date)},
        )

    age = t_year - b_year
    if age < 0:
        raise ModelRangeError(
            f"Target date '{target_date}' cannot chronologically precede birth date '{birth_date}'.",
            error_code="ERR_MODEL_RANGE",
            details={"birth_date": str(birth_date), "target_date": str(target_date)},
        )

    # If both dates define months, check if the birthday anniversary has occurred yet
    if b_month is not None and t_month is not None:
        b_day_eff = b_day if b_day is not None else 1
        t_day_eff = t_day if t_day is not None else 1
        if (t_month, t_day_eff) < (b_month, b_day_eff):
            age -= 1

    return age
