# Name: date.py
# Path: src/gda/model/atom/date.py

"""Core atomic temporal models and historical calendar primitives using Pydantic dataclasses.

Operational Role:
    Encapsulates validated historical calendar points, dates, temporal modifiers,
    census enumeration years, and ISO 8601 timestamps.

Architecture:
    - HistoricalYear: Validated integer year between 1000 and 2100.
    - CensusYear: Bounded federal decennial census year (1790..1950).
    - DateModifier: Enumeration of standard genealogical date qualifiers.
    - DateString: Normalized, sanitized textual date string.
    - IsoTimestamp: Validated UTC ISO 8601 extended timestamp.
    - EventDate: Structured point-in-time event date.
    - EventDateRange: Structured temporal interval (range or span).
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from enum import Enum, StrEnum
from typing import ClassVar

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

from gda.core.introspectable import IntrospectableMixin
from gda.core.logging import GDALogger
from gda.model.atom.errors import AtomFormatError, AtomRangeError

__version__ = "1.0.0+build.r4"

_logger = GDALogger(__name__)


@dataclass(config=ConfigDict(frozen=True, extra="forbid"))
class HistoricalYear(IntrospectableMixin):
    """Historical calendar year bounded strictly between 1000 and 2100."""

    value: int

    def __post_init__(self) -> None:
        if not (1000 <= self.value <= 2100):
            err_msg = f"HistoricalYear '{self.value}' out of range. Must be between 1000 and 2100."
            _logger.debug(
                "HistoricalYear validation failed", details={"value": self.value}
            )
            raise AtomRangeError(err_msg, details={"value": self.value})

    def __int__(self) -> int:
        return self.value

    def __repr__(self) -> str:
        return f"HistoricalYear(value={self.value})"


class CensusYearEnum(int, Enum):
    """Valid US Federal Decennial Census years (1790 to 1950)."""

    Y1790 = 1790
    Y1800 = 1800
    Y1810 = 1810
    Y1820 = 1820
    Y1830 = 1830
    Y1840 = 1840
    Y1850 = 1850
    Y1860 = 1860
    Y1870 = 1870
    Y1880 = 1880
    Y1900 = 1900
    Y1910 = 1910
    Y1920 = 1920
    Y1930 = 1930
    Y1940 = 1940
    Y1950 = 1950


@dataclass(config=ConfigDict(frozen=True, extra="forbid"))
class CensusYear(IntrospectableMixin):
    """Decennial census year matching US Federal enumeration schedules."""

    value: int

    def __post_init__(self) -> None:
        valid_years = {member.value for member in CensusYearEnum}
        if self.value not in valid_years:
            err_msg = (
                f"Invalid CensusYear '{self.value}'. Must be a valid US Federal Decennial "
                f"Census enumeration year (1790..1950, excluding 1890)."
            )
            _logger.debug("CensusYear validation failed", details={"value": self.value})
            raise AtomRangeError(err_msg, details={"value": self.value})

    def __int__(self) -> int:
        return self.value

    def __repr__(self) -> str:
        return f"CensusYear(value={self.value})"


class DateModifier(StrEnum):
    """Standardized genealogical date approximations and qualifiers."""

    EXACT = "EXACT"
    ABOUT = "ABT"
    BEFORE = "BEF"
    AFTER = "AFT"
    BETWEEN = "BET"
    ESTIMATED = "EST"
    CALCULATED = "CAL"


@dataclass(config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True))
class DateString(IntrospectableMixin):
    """Sanitized textual date string representation."""

    value: str

    def __post_init__(self) -> None:
        if not self.value.strip():
            err_msg = "DateString value cannot be empty or whitespace."
            _logger.debug("DateString validation failed: empty input")
            raise AtomFormatError(err_msg, details={"value": self.value})

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"DateString(value='{self.value}')"


@dataclass(config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True))
class IsoTimestamp(IntrospectableMixin):
    """Strict ISO 8601 UTC timestamp (YYYY-MM-DDTHH:MM:SSZ or with offset)."""

    value: str

    _PATTERN: ClassVar[re.Pattern[str]] = re.compile(
        r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
    )

    def __post_init__(self) -> None:
        if not self._PATTERN.match(self.value):
            err_msg = (
                f"Invalid IsoTimestamp format: '{self.value}'. "
                "Must match ISO 8601 extended format (e.g., '2026-10-16T12:00:00Z')."
            )
            _logger.debug(
                "IsoTimestamp validation failed", details={"value": self.value}
            )
            raise AtomFormatError(err_msg, details={"value": self.value})

    @classmethod
    def now_utc(cls) -> IsoTimestamp:
        now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        return cls(value=now)

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"IsoTimestamp(value='{self.value}')"


@dataclass(config=ConfigDict(frozen=True, extra="forbid"))
class EventDate(IntrospectableMixin):
    """Structured event date atom combining DateString and optional modifier."""

    date: DateString
    modifier: DateModifier | None = None

    def __str__(self) -> str:
        if self.modifier and self.modifier != DateModifier.EXACT:
            return f"{self.modifier.value} {self.date}"
        return str(self.date)

    def __repr__(self) -> str:
        mod_repr = f", modifier={self.modifier}" if self.modifier else ""
        return f"{self.__class__.__name__}(date={self.date!r}{mod_repr})"


@dataclass(config=ConfigDict(frozen=True, extra="forbid"))
class EventDateRange(IntrospectableMixin):
    """Structured temporal interval encompassing start and end dates."""

    start_date: EventDate
    end_date: EventDate
    modifier: DateModifier = DateModifier.BETWEEN

    def __str__(self) -> str:
        return f"{self.modifier.value} {self.start_date} AND {self.end_date}"

    def __repr__(self) -> str:
        return (
            f"EventDateRange(start_date={self.start_date!r}, "
            f"end_date={self.end_date!r}, modifier={self.modifier})"
        )


@dataclass(config=ConfigDict(frozen=True, extra="forbid"))
class BirthYear(HistoricalYear):
    """Specialized calendar year representing an individual's birth."""


@dataclass(config=ConfigDict(frozen=True, extra="forbid"))
class DeathYear(HistoricalYear):
    """Specialized calendar year representing an individual's death."""
