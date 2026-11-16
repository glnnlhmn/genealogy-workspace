"""Path: src/gda/model/base/date.py

Composite historical event dates and temporal bounding ranges.

Operational Role:
    Defines EventDate (combining a validated DateString with a canonical DateModifier
    and optional range end_date for BETWEEN assertions) and TimePeriod (bounding
    inception and conclusion EventDate instances with full year/month/day sequence
    validation). Replaces the standalone time_period.py module.

Classes:
    EventDate: Genealogical date assertion with approximation modifier and optional range end.
    TimePeriod: Value object bounding start and end EventDate instances.
"""

from __future__ import annotations

import json
from typing import Any

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.dates import parse_iso_date_parts
from gda.core.enums.date import DateModifier, normalize_modifier
from gda.core.errors import ModelFormatError, ModelRangeError
from gda.core.introspectable import IntrospectableMixin
from gda.model.atom.date import DateString

__version__ = "1.0.0+build.2"

__all__ = ["EventDate", "TimePeriod"]


def _date_sort_key(date_atom: DateString) -> tuple[int, int, int]:
    """Extract comparable (year, month, day) key from a validated DateString."""
    year, month, day = parse_iso_date_parts(date_atom.value)
    return (year, month or 0, day or 0)


@dataclass(repr=False, config=ConfigDict(frozen=True, extra="forbid", strict=True))
class EventDate(IntrospectableMixin):
    """Genealogical event date assertion combining DateString and DateModifier."""

    date: DateString = Field(..., description="Primary historical date expression.")
    modifier: DateModifier = Field(
        default=DateModifier.EXACT,
        description="Genealogical approximation or range qualifier.",
    )
    end_date: DateString | None = Field(
        default=None,
        description="Upper bound date expression when modifier is DateModifier.BETWEEN.",
    )

    def __post_init__(self) -> None:
        """Enforce BETWEEN range invariants and chronological ordering."""
        if self.modifier == DateModifier.BETWEEN and self.end_date is None:
            raise ModelFormatError(
                "EventDate with modifier BETWEEN requires an end_date.",
                details={"modifier": self.modifier.value, "date": str(self.date)},
            )
        if self.modifier != DateModifier.BETWEEN and self.end_date is not None:
            raise ModelFormatError(
                f"EventDate end_date is only valid when modifier is BETWEEN, got {self.modifier.value}.",
                details={"modifier": self.modifier.value, "end_date": str(self.end_date)},
            )
        if self.end_date is not None:
            start_key = _date_sort_key(self.date)
            end_key = _date_sort_key(self.end_date)
            if end_key < start_key:
                raise ModelRangeError(
                    f"EventDate end_date ({self.end_date}) cannot precede date ({self.date}).",
                    details={"date": str(self.date), "end_date": str(self.end_date)},
                )

    @classmethod
    def create(
        cls,
        date: DateString | str,
        modifier: DateModifier | str | None = DateModifier.EXACT,
        end_date: DateString | str | None = None,
    ) -> EventDate:
        """Factory constructor parsing string tokens and GEDCOM modifiers into EventDate."""
        if isinstance(date, DateString):
            resolved_date = date
        elif isinstance(date, str):
            raw_token = date.strip()
            if not raw_token:
                raise ModelFormatError("EventDate 'date' cannot be empty or whitespace.")
            parts = raw_token.split(maxsplit=1)
            inferred_mod: DateModifier | None = None
            if len(parts) == 2 and modifier in (None, DateModifier.EXACT):
                try:
                    inferred_mod = normalize_modifier(parts[0])
                except ValueError:
                    inferred_mod = None
            if inferred_mod is not None and inferred_mod != DateModifier.EXACT:
                modifier = inferred_mod
                resolved_date = DateString(parts[1].strip())
            else:
                resolved_date = DateString(raw_token)
        else:
            raise ModelFormatError(
                f"Invalid EventDate 'date' type: expected DateString or str, got {type(date).__name__}."
            )

        try:
            resolved_mod = normalize_modifier(modifier) or DateModifier.EXACT
        except ValueError as exc:
            raise ModelFormatError(str(exc)) from exc

        resolved_end: DateString | None = None
        if end_date is not None:
            if isinstance(end_date, DateString):
                resolved_end = end_date
            elif isinstance(end_date, str):
                clean_end = end_date.strip()
                resolved_end = DateString(clean_end) if clean_end else None
            else:
                raise ModelFormatError(
                    f"Invalid EventDate 'end_date' type: expected DateString or str, got {type(end_date).__name__}."
                )

        return cls(date=resolved_date, modifier=resolved_mod, end_date=resolved_end)

    def to_dict(self) -> dict[str, Any]:
        """Serialize EventDate to a dictionary."""
        data: dict[str, Any] = {
            "date": self.date.value,
            "modifier": self.modifier.value,
        }
        if self.end_date is not None:
            data["end_date"] = self.end_date.value
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any] | str) -> EventDate:
        """Deserialize a dictionary payload or compact date string into an EventDate."""
        if isinstance(data, str):
            return cls.create(data)
        if not isinstance(data, dict):
            raise ModelFormatError("EventDate payload must be a dictionary or string.")
        raw_date = data.get("date")
        if not raw_date:
            raise ModelFormatError("Missing required field 'date' for EventDate.")
        return cls.create(
            date=str(raw_date),
            modifier=data.get("modifier", DateModifier.EXACT),
            end_date=data.get("end_date"),
        )

    def to_json(self) -> str:
        """Serialize EventDate to a JSON formatted string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_json(cls, payload: str) -> EventDate:
        """Deserialize a JSON string directly into an EventDate instance."""
        try:
            data = json.loads(payload)
        except Exception as exc:
            raise ModelFormatError(f"Failed to parse EventDate JSON string: {exc}") from exc
        return cls.from_dict(data)

    def __str__(self) -> str:
        """Render canonical GEDCOM-aligned date expression."""
        if self.modifier == DateModifier.EXACT:
            return self.date.value
        if self.modifier == DateModifier.BETWEEN and self.end_date is not None:
            return f"BET {self.date.value} AND {self.end_date.value}"
        return f"{self.modifier.value} {self.date.value}"

    def __repr__(self) -> str:
        end_repr = f", end_date={self.end_date!r}" if self.end_date is not None else ""
        return f"EventDate(date={self.date!r}, modifier={self.modifier}{end_repr})"


@dataclass(repr=False, config=ConfigDict(frozen=True, extra="forbid", strict=True))
class TimePeriod(IntrospectableMixin):
    """Bounded historical temporal range tracking inception and conclusion dates."""

    start_date: EventDate | None = Field(
        default=None, description="Inception, establishment, or erection date."
    )
    end_date: EventDate | None = Field(
        default=None, description="Dissolution, closure, or decommissioning date."
    )

    def __post_init__(self) -> None:
        """Validate temporal existence and sequence integrity."""
        if self.start_date is None and self.end_date is None:
            raise ModelFormatError(
                "TimePeriod must define at least one boundary date (start_date or end_date)."
            )

        if self.start_date is not None and self.end_date is not None:
            self._validate_chronological_sequence()

    def _validate_chronological_sequence(self) -> None:
        """Verify that end_date does not precede start_date."""
        assert self.start_date is not None
        assert self.end_date is not None
        start_key = _date_sort_key(self.start_date.date)
        end_key = _date_sort_key(self.end_date.date)

        if end_key < start_key:
            raise ModelRangeError(
                f"Conclusion date ({self.end_date}) cannot precede inception date ({self.start_date}).",
                details={
                    "start_date": str(self.start_date),
                    "end_date": str(self.end_date),
                },
            )

    @property
    def is_bounded(self) -> bool:
        """Return True if both start and end boundaries are defined."""
        return self.start_date is not None and self.end_date is not None

    def to_dict(self) -> dict[str, Any]:
        """Serialize TimePeriod to a dictionary."""
        return {
            "start_date": self.start_date.to_dict() if self.start_date is not None else None,
            "end_date": self.end_date.to_dict() if self.end_date is not None else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TimePeriod:
        """Deserialize a dictionary payload into an immutable TimePeriod."""
        if not isinstance(data, dict):
            raise ModelFormatError("TimePeriod payload must be a dictionary.")
        raw_start = data.get("start_date")
        raw_end = data.get("end_date")
        start_ev = (
            raw_start
            if isinstance(raw_start, EventDate)
            else (EventDate.from_dict(raw_start) if raw_start else None)
        )
        end_ev = (
            raw_end
            if isinstance(raw_end, EventDate)
            else (EventDate.from_dict(raw_end) if raw_end else None)
        )
        return cls(start_date=start_ev, end_date=end_ev)

    def to_json(self) -> str:
        """Serialize TimePeriod to a JSON formatted string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_json(cls, payload: str) -> TimePeriod:
        """Deserialize a JSON string directly into a TimePeriod instance."""
        try:
            data = json.loads(payload)
        except Exception as exc:
            raise ModelFormatError(f"Failed to parse TimePeriod JSON string: {exc}") from exc
        return cls.from_dict(data)

    def __str__(self) -> str:
        """Render concise human-readable date range description."""
        if self.start_date and self.end_date:
            return f"{self.start_date} - {self.end_date}"
        if self.start_date:
            return f"from {self.start_date}"
        return f"until {self.end_date}"

    def __repr__(self) -> str:
        return f"TimePeriod(start_date={self.start_date!r}, end_date={self.end_date!r})"
