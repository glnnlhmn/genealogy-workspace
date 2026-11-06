"""Path: src/gda/model/atom/date.py

Core atomic temporal primitives and historical calendar types using Pydantic dataclasses.

Operational Role:
    Encapsulates validated historical calendar points, dates, temporal modifiers,
    census enumeration years, and ISO 8601 timestamps with copy-on-write mutators,
    intrinsic calendar year extractions, serialization parity, and comparison protocols.

Architecture:
    - HistoricalYear: Validated integer year between 1000 and 2100.
    - CensusYear: Bounded federal decennial census year derived from CensusYearEnum.
    - DateModifier: Enumeration of standard genealogical date qualifiers.
    - DateString: Normalized, sanitized textual date string.
    - IsoTimestamp: Validated UTC ISO 8601 extended timestamp.
    - EventDate: Structured point-in-time event date atom with factory and mutators.
    - EventDateRange: Structured temporal interval (range or span) with bounds logic.
"""

from __future__ import annotations

import json
import re
from dataclasses import replace
from datetime import UTC, datetime
from enum import Enum, StrEnum
from functools import total_ordering
from typing import Any, ClassVar, Self

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

from gda.core.errors import ModelFormatError, ModelRangeError
from gda.core.introspectable import IntrospectableMixin
from gda.core.logging import GDALogger

__version__ = "1.0.0+build.9"

_logger = GDALogger(__name__)

_YEAR_REGEX: re.Pattern[str] = re.compile(r"\b(\d{4})\b")


@dataclass(config=ConfigDict(frozen=True, extra="forbid"))
class HistoricalYear(IntrospectableMixin):
    """Historical calendar year bounded strictly between 1000 and 2100."""

    value: int

    def __post_init__(self) -> None:
        if not (1000 <= self.value <= 2100):
            err_msg = f"HistoricalYear '{self.value}' out of range. Must be between 1000 and 2100."
            _logger.debug("HistoricalYear validation failed", details={"value": self.value})
            raise ModelRangeError(err_msg, details={"value": self.value})

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
            min_year, max_year = min(valid_years), max(valid_years)
            err_msg = (
                f"Invalid CensusYear '{self.value}'. Must be a valid US Federal Decennial "
                f"Census enumeration year ({min_year}..{max_year}, excluding 1890)."
            )
            _logger.debug("CensusYear validation failed", details={"value": self.value})
            raise ModelRangeError(err_msg, details={"value": self.value})

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


_MODIFIER_ALIASES: dict[str, DateModifier] = {
    "EXACT": DateModifier.EXACT,
    "ABT": DateModifier.ABOUT,
    "ABOUT": DateModifier.ABOUT,
    "BEF": DateModifier.BEFORE,
    "BEFORE": DateModifier.BEFORE,
    "AFT": DateModifier.AFTER,
    "AFTER": DateModifier.AFTER,
    "BET": DateModifier.BETWEEN,
    "BETWEEN": DateModifier.BETWEEN,
    "EST": DateModifier.ESTIMATED,
    "ESTIMATED": DateModifier.ESTIMATED,
    "CAL": DateModifier.CALCULATED,
    "CALCULATED": DateModifier.CALCULATED,
}


def _normalize_modifier(modifier: DateModifier | str | None) -> DateModifier | None:
    """Normalize string, enum, or alias into a valid DateModifier instance."""
    if modifier is None:
        return None
    if isinstance(modifier, DateModifier):
        return modifier
    token = str(modifier).strip().upper()
    if token in _MODIFIER_ALIASES:
        return _MODIFIER_ALIASES[token]
    raise ModelFormatError(f"Invalid DateModifier value: '{modifier}'.")


@dataclass(config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True))
class DateString(IntrospectableMixin):
    """Sanitized textual date string representation."""

    value: str

    def __post_init__(self) -> None:
        if not self.value.strip():
            err_msg = "DateString value cannot be empty or whitespace."
            _logger.debug("DateString validation failed: empty input")
            raise ModelFormatError(err_msg, details={"value": self.value})

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
            _logger.debug("IsoTimestamp validation failed", details={"value": self.value})
            raise ModelFormatError(err_msg, details={"value": self.value})

    @classmethod
    def now_utc(cls) -> IsoTimestamp:
        now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        return cls(value=now)

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"IsoTimestamp(value='{self.value}')"


@total_ordering
@dataclass(config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True))
class EventDate(IntrospectableMixin):
    """Structured event date atom combining DateString and optional modifier."""

    date: DateString
    modifier: DateModifier | None = None

    @property
    def year(self) -> int | None:
        """Extract four-digit calendar year if present in date text."""
        match = _YEAR_REGEX.search(self.date.value)
        return int(match.group(1)) if match else None

    @property
    def year_lower_bound(self) -> int | None:
        """Lower-bound calendar year for ordering and chronology."""
        return self.year

    @classmethod
    def create(
        cls,
        date: DateString | str,
        modifier: DateModifier | str | None = None,
    ) -> EventDate:
        """Factory constructor instantiating a validated EventDate."""
        resolved_date = date if isinstance(date, DateString) else DateString(date)
        resolved_mod = _normalize_modifier(modifier)
        return cls(date=resolved_date, modifier=resolved_mod)

    def update_date(self, date: DateString | str) -> Self:
        """Return a new immutable copy with updated date string."""
        resolved_date = date if isinstance(date, DateString) else DateString(date)
        return replace(self, date=resolved_date)

    def update_modifier(self, modifier: DateModifier | str | None) -> Self:
        """Return a new immutable copy with updated qualifier modifier."""
        resolved_mod = _normalize_modifier(modifier)
        return replace(self, modifier=resolved_mod)

    def to_dict(self) -> dict[str, Any]:
        """Serialize EventDate to a dictionary."""
        data: dict[str, Any] = {"date": self.date.value}
        if self.modifier is not None:
            data["modifier"] = self.modifier.value
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EventDate:
        """Deserialize a dictionary payload into an immutable EventDate."""
        if not isinstance(data, dict):
            raise ModelFormatError("EventDate payload must be a dictionary.")
        raw_date = data.get("date")
        if not raw_date or not str(raw_date).strip():
            raise ModelFormatError("Missing required field 'date' for EventDate.")
        return cls.create(date=str(raw_date), modifier=data.get("modifier"))

    def to_json(self) -> str:
        """Serialize EventDate to a JSON formatted string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_json(cls, payload: str) -> EventDate:
        """Deserialize a JSON string directly into an EventDate instance."""
        try:
            data = json.loads(payload)
        except Exception as exc:
            raise ModelFormatError(f"Failed to parse EventDate JSON: {exc}") from exc
        return cls.from_dict(data)

    def __str__(self) -> str:
        if self.modifier and self.modifier != DateModifier.EXACT:
            return f"{self.modifier.value} {self.date}"
        return str(self.date)

    def __repr__(self) -> str:
        mod_repr = f", modifier={self.modifier}" if self.modifier else ""
        return f"{self.__class__.__name__}(date={self.date!r}{mod_repr})"

    def __lt__(self, other: Any) -> bool:
        """Support chronological ordering comparisons."""
        if isinstance(other, EventDate):
            s_yr = self.year_lower_bound if self.year_lower_bound is not None else 9999
            o_yr = other.year_lower_bound if other.year_lower_bound is not None else 9999
            if s_yr != o_yr:
                return s_yr < o_yr
            return str(self.date) < str(other.date)
        return NotImplemented


@total_ordering
@dataclass(config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True))
class EventDateRange(IntrospectableMixin):
    """Structured temporal interval encompassing start and end dates."""

    start_date: EventDate
    end_date: EventDate
    modifier: DateModifier = DateModifier.BETWEEN

    @property
    def start_year(self) -> int | None:
        """Lower-bound calendar year of interval start."""
        return self.start_date.year

    @property
    def end_year(self) -> int | None:
        """Upper-bound calendar year of interval end."""
        return self.end_date.year

    @property
    def year_lower_bound(self) -> int | None:
        """Earliest bound calendar year."""
        return self.start_year if self.start_year is not None else self.end_year

    @classmethod
    def create(
        cls,
        start_date: EventDate | str,
        end_date: EventDate | str,
        modifier: DateModifier | str = DateModifier.BETWEEN,
    ) -> EventDateRange:
        """Factory constructor instantiating a validated EventDateRange."""
        s = start_date if isinstance(start_date, EventDate) else EventDate.create(start_date)
        e = end_date if isinstance(end_date, EventDate) else EventDate.create(end_date)
        m = _normalize_modifier(modifier) or DateModifier.BETWEEN
        return cls(start_date=s, end_date=e, modifier=m)

    def update_start(self, start_date: EventDate | str) -> Self:
        """Return a new immutable copy with updated start date."""
        s = start_date if isinstance(start_date, EventDate) else EventDate.create(start_date)
        return replace(self, start_date=s)

    def update_end(self, end_date: EventDate | str) -> Self:
        """Return a new immutable copy with updated end date."""
        e = end_date if isinstance(end_date, EventDate) else EventDate.create(end_date)
        return replace(self, end_date=e)

    def to_dict(self) -> dict[str, Any]:
        """Serialize EventDateRange to a dictionary."""
        return {
            "start_date": self.start_date.to_dict(),
            "end_date": self.end_date.to_dict(),
            "modifier": self.modifier.value,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EventDateRange:
        """Deserialize a dictionary payload into an immutable EventDateRange."""
        if not isinstance(data, dict):
            raise ModelFormatError("EventDateRange payload must be a dictionary.")
        s = data.get("start_date")
        e = data.get("end_date")
        if not s or not e:
            raise ModelFormatError("EventDateRange requires 'start_date' and 'end_date'.")
        s_date = EventDate.from_dict(s) if isinstance(s, dict) else EventDate.create(str(s))
        e_date = EventDate.from_dict(e) if isinstance(e, dict) else EventDate.create(str(e))
        return cls.create(
            start_date=s_date,
            end_date=e_date,
            modifier=data.get("modifier", DateModifier.BETWEEN),
        )

    def to_json(self) -> str:
        """Serialize EventDateRange to a JSON formatted string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_json(cls, payload: str) -> EventDateRange:
        """Deserialize a JSON string directly into an EventDateRange instance."""
        try:
            data = json.loads(payload)
        except Exception as exc:
            raise ModelFormatError(f"Failed to parse EventDateRange JSON: {exc}") from exc
        return cls.from_dict(data)

    def __str__(self) -> str:
        return f"{self.modifier.value} {self.start_date} AND {self.end_date}"

    def __repr__(self) -> str:
        return (
            f"EventDateRange(start_date={self.start_date!r}, "
            f"end_date={self.end_date!r}, modifier={self.modifier})"
        )

    def __lt__(self, other: Any) -> bool:
        """Support chronological ordering comparisons."""
        if isinstance(other, (EventDateRange, EventDate)):
            s_yr = self.year_lower_bound if self.year_lower_bound is not None else 9999
            o_yr = other.year_lower_bound if other.year_lower_bound is not None else 9999
            if s_yr != o_yr:
                return s_yr < o_yr
            return str(self.start_date) < str(getattr(other, "start_date", other))
        return NotImplemented


@dataclass(config=ConfigDict(frozen=True, extra="forbid"))
class BirthYear(HistoricalYear):
    """Specialized calendar year representing an individual's birth."""


@dataclass(config=ConfigDict(frozen=True, extra="forbid"))
class DeathYear(HistoricalYear):
    """Specialized calendar year representing an individual's death."""
