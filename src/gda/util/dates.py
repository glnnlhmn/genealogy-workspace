# Name: dates.py
# Path: src/gda/util/dates.py

"""ISO date and timestamp format definitions, regex patterns, and string validators.

Operational Role:
    Provides stateless validation predicates for ISO 8601 calendar dates and
    extended timestamps using canonical patterns defined in gda.types.primitives.

Note:
    PRERELEASE: Module is under active development (version 0.0.1+build.1).
"""

from __future__ import annotations

from gda.types.primitives import (
    ISO_DATE_FMT,
    ISO_DATE_PATTERN,
    ISO_DATE_REGEX,
    ISO_MONTH_FMT,
    ISO_TIMESTAMP_FMT,
    ISO_TIMESTAMP_PATTERN,
    ISO_TIMESTAMP_REGEX,
    ISO_YEAR_FMT,
)

__version__ = "0.0.1+build.1"

__all__ = [
    "ISO_DATE_FMT",
    "ISO_DATE_PATTERN",
    "ISO_DATE_REGEX",
    "ISO_MONTH_FMT",
    "ISO_TIMESTAMP_FMT",
    "ISO_TIMESTAMP_PATTERN",
    "ISO_TIMESTAMP_REGEX",
    "ISO_YEAR_FMT",
    "is_iso_date",
    "is_iso_timestamp",
]


def is_iso_date(val: str | None) -> bool:
    """Verify whether a string conforms to ISO calendar date formats (YYYY, YYYY-MM, YYYY-MM-DD).

    Args:
        val: Candidate string to inspect.

    Returns:
        True if string matches ISO calendar date syntax; False otherwise.
    """
    if not val or not isinstance(val, str):
        return False
    return bool(ISO_DATE_REGEX.match(val.strip()))


def is_iso_timestamp(val: str | None) -> bool:
    """Verify whether a string conforms to ISO 8601 extended timestamp format.

    Args:
        val: Candidate string to inspect.

    Returns:
        True if string matches ISO timestamp syntax; False otherwise.
    """
    if not val or not isinstance(val, str):
        return False
    return bool(ISO_TIMESTAMP_REGEX.match(val.strip()))
