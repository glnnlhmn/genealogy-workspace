"""Path: src/gda/model/atom/date.py

Atomic temporal value primitives for calendar dates and UTC timestamps.

Operational Role:
    Defines immutable, self-validating wrapper classes for genealogical date
    strings (DateString) and ISO-8601 UTC timestamps (IsoTimestamp). Enforces
    strict outer-whitespace normalization, Gregorian calendar day validity on
    ISO-formatted dates, and homogeneous total ordering.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from gda.core.dates import validate_iso_date, validate_iso_timestamp
from gda.core.errors import ModelFormatError
from gda.core.introspectable import IntrospectableMixin

__version__ = "1.0.0+build.5"

__all__ = [
    "DateString",
    "IsoTimestamp",
]

# Detects numeric ISO-shaped date candidates (e.g., 1880-02-30 or 1880-13-01)
_NUMERIC_ISO_CANDIDATE_REGEX: re.Pattern[str] = re.compile(r"^\d{4}-\d{1,2}(-\d{1,2})?$")


@dataclass(frozen=True)
class DateString(IntrospectableMixin):
    """Immutable atomic wrapper for normalized genealogical date expressions.

    Accepts canonical ISO dates ('YYYY', 'YYYY-MM', 'YYYY-MM-DD') as well as
    GEDCOM-style historical expressions ('14 APR 1865', 'ABT 1850'). When the
    string matches an ISO numeric date structure, real Gregorian calendar bounds
    are verified via validate_iso_date().

    Attributes:
        value: Non-empty, whitespace-trimmed date string.
    """

    value: str

    def __post_init__(self) -> None:
        """Validate non-empty trimmed string and Gregorian bounds on ISO dates."""
        if not isinstance(self.value, str) or not self.value or self.value != self.value.strip():
            raise ModelFormatError(
                f"Invalid DateString: '{self.value}' must be a non-empty, trimmed string.",
                error_code="ERR_MODEL_FORMAT",
                details={"value": self.value},
            )

        # Enforce real calendar day/month bounds when formatted as a numeric YYYY-MM[-DD] string
        if _NUMERIC_ISO_CANDIDATE_REGEX.match(self.value) and not validate_iso_date(self.value):
            raise ModelFormatError(
                f"Invalid DateString calendar value: '{self.value}'.",
                error_code="ERR_MODEL_FORMAT",
                details={"value": self.value},
            )

    def __str__(self) -> str:
        return self.value

    def __eq__(self, other: object) -> bool:
        if isinstance(other, DateString):
            return self.value == other.value
        if isinstance(other, str):
            return self.value == other
        return False

    def __hash__(self) -> int:
        return hash(self.value)

    def __lt__(self, other: Any) -> bool:
        if isinstance(other, DateString):
            return self.value < other.value
        return NotImplemented


@dataclass(frozen=True)
class IsoTimestamp(IntrospectableMixin):
    """Immutable atomic wrapper for canonical ISO-8601 timestamps.

    Attributes:
        value: Validated ISO-8601 timestamp string (e.g., '2026-10-16T12:00:00Z').
    """

    value: str

    def __post_init__(self) -> None:
        """Validate canonical ISO-8601 timestamp syntax without outer whitespace."""
        if (
            not isinstance(self.value, str)
            or self.value != self.value.strip()
            or not validate_iso_timestamp(self.value)
        ):
            raise ModelFormatError(
                f"Invalid IsoTimestamp format: '{self.value}'.",
                error_code="ERR_MODEL_FORMAT",
                details={"value": self.value},
            )

    def __str__(self) -> str:
        return self.value

    def __eq__(self, other: object) -> bool:
        if isinstance(other, IsoTimestamp):
            return self.value == other.value
        if isinstance(other, str):
            return self.value == other
        return False

    def __hash__(self) -> int:
        return hash(self.value)

    def __lt__(self, other: Any) -> bool:
        if isinstance(other, IsoTimestamp):
            return self.value < other.value
        return NotImplemented
