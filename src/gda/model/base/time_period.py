"""Path: src/gda/model/base/time_period.py

Temporal bounding primitives for historical entity lifecycles.

Operational Role:
    Defines TimePeriod representing date-bounded ranges across civil
    jurisdictions, physical sites, custodial repositories, and historical names.
    Enforces chronological sequence validity between establishment and
    dissolution or start and end dates.

Classes:
    TimePeriod: Value object bounding start and end EventDate instances.
"""

from __future__ import annotations

import re

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.errors import ModelFormatError, ModelRangeError
from gda.core.introspectable import IntrospectableMixin
from gda.model.atom.date import EventDate

__version__ = "1.0.0+build.1"

_YEAR_EXTRACT_PATTERN: re.Pattern[str] = re.compile(r"\b(\d{4})\b")


@dataclass(config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True))
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
        """Verify that end_date does not precede start_date when years are extractable."""
        start_match = _YEAR_EXTRACT_PATTERN.search(self.start_date.date.value)  # type: ignore[union-attr]
        end_match = _YEAR_EXTRACT_PATTERN.search(self.end_date.date.value)  # type: ignore[union-attr]

        if start_match and end_match:
            start_year = int(start_match.group(1))
            end_year = int(end_match.group(1))
            if end_year < start_year:
                raise ModelRangeError(
                    f"Conclusion year ({end_year}) cannot precede inception year ({start_year})."
                )

    @property
    def is_bounded(self) -> bool:
        """Return True if both start and end boundaries are defined."""
        return self.start_date is not None and self.end_date is not None

    def __str__(self) -> str:
        """Render concise human-readable date range description."""
        if self.start_date and self.end_date:
            return f"{self.start_date} - {self.end_date}"
        if self.start_date:
            return f"from {self.start_date}"
        return f"until {self.end_date}"

    def __repr__(self) -> str:
        return f"TimePeriod(start_date={self.start_date!r}, end_date={self.end_date!r})"
