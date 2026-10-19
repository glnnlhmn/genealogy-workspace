"""Path: src/gda/model/entity/individual.py

Genealogical individual entity model extending BaseEntity[IndividualID].
"""

from __future__ import annotations

import re
from typing import ClassVar

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.errors import ModelFormatError, ModelRangeError
from gda.model.atom.date import EventDate, EventDateRange
from gda.model.atom.id import IndividualID, LocationID, SiteID
from gda.model.base.entity import BaseEntity
from gda.model.base.name import CanonicalName, HistoricalName

__version__ = "1.0.0+build.5"

__all__ = ["Individual"]

_INDIVIDUAL_ID_PATTERN: re.Pattern[str] = re.compile(r"^IND-\d{6,}$")
_INDIVIDUAL_URN_PATTERN: re.Pattern[str] = re.compile(r"^urn:gda:ind:[a-z0-9_:\-]+$")
_YEAR_EXTRACT_PATTERN: re.Pattern[str] = re.compile(r"\b(\d{4})\b")


def _extract_year_lower_bound(
    date_val: EventDate | EventDateRange | None,
) -> int | None:
    """Extract lower-bound four-digit calendar year from an EventDate or EventDateRange."""
    if date_val is None:
        return None
    raw_date_str = (
        date_val.start_date.date.value
        if isinstance(date_val, EventDateRange)
        else date_val.date.value
    )
    match = _YEAR_EXTRACT_PATTERN.search(raw_date_str)
    return int(match.group(1)) if match else None


@dataclass(config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True))
class Individual(BaseEntity[IndividualID]):
    """Genealogical individual record capturing intrinsic identity, vital bounds, and anchors."""

    name: CanonicalName = Field(
        ..., description="Standard structured name for primary identity."
    )
    canonical_urn: str = Field(
        ...,
        description="Deterministic lookup URN (e.g., 'urn:gda:ind:smith_john_1842').",
    )
    sex: str = Field(
        default="U",
        description="Biological sex indicator ('M', 'F', 'U', or descriptive token).",
    )
    birth_date: EventDate | EventDateRange | None = Field(
        default=None,
        description="Point date or date range for birth/baptism with modifier support.",
    )
    death_date: EventDate | EventDateRange | None = Field(
        default=None,
        description="Point date or date range for death/burial with modifier support.",
    )
    birth_place_id: LocationID | SiteID | None = Field(
        default=None,
        description="Jurisdiction (LOC) or physical venue (SID) of vital origin.",
    )
    death_place_id: LocationID | SiteID | None = Field(
        default=None,
        description="Jurisdiction (LOC) or physical venue (SID) of vital conclusion.",
    )
    is_deceased: bool = Field(
        default=True,
        description="Death status flag; distinguishes confirmed deceased from living individuals.",
    )
    historical_names: list[HistoricalName] = Field(
        default_factory=list,
        description="Date-bounded historical naming variants, aliases, or married surnames.",
    )
    alternate_names: list[str] = Field(
        default_factory=list,
        description="Colloquial nicknames, vernacular spellings, or informal aliases.",
    )

    _ID_PATTERN: ClassVar[re.Pattern[str]] = _INDIVIDUAL_ID_PATTERN
    _URN_PATTERN: ClassVar[re.Pattern[str]] = _INDIVIDUAL_URN_PATTERN

    def __post_init__(self) -> None:
        """Enforce domain invariants, regex formatting, and boundary guards."""
        super().__post_init__()

        if not isinstance(self.id, IndividualID):
            raise TypeError(
                f"Individual 'id' must be an instance of IndividualID, got {type(self.id).__name__}."
            )

        raw_id = self.id.value
        if not self._ID_PATTERN.match(raw_id):
            raise ModelFormatError(
                f"Invalid IndividualID format: '{raw_id}'. Must match 'IND-######'."
            )

        if not self._URN_PATTERN.match(self.canonical_urn):
            raise ModelFormatError(
                f"Invalid canonical_urn format: '{self.canonical_urn}'. "
                "Must match 'urn:gda:ind:<slug>'."
            )

        if (
            self.tombstone.is_deprecated
            and self.tombstone.superseded_by is not None
            and self.tombstone.superseded_by.value == raw_id
        ):
            raise ModelFormatError("Individual cannot be superseded by itself.")

        if not self.is_deceased:
            if self.death_date is not None:
                raise ModelFormatError(
                    "Individual cannot define death_date while is_deceased is False."
                )
            if self.death_place_id is not None:
                raise ModelFormatError(
                    "Individual cannot define death_place_id while is_deceased is False."
                )

        b_year = self.birth_year
        d_year = self.death_year
        if b_year is not None and d_year is not None and d_year < b_year:
            raise ModelRangeError(
                f"Death year ({d_year}) cannot precede birth year ({b_year}).",
                details={"birth_year": b_year, "death_year": d_year},
            )

        seen_historical: set[tuple[str, str | None, str]] = set()
        for hn in self.historical_names:
            key = (hn.raw_name, hn.canonical_name, hn.status.value)
            if key in seen_historical:
                raise ModelFormatError("Duplicate entries found in historical_names.")
            seen_historical.add(key)

        if len(self.alternate_names) != len(set(self.alternate_names)):
            raise ModelFormatError("Duplicate entries found in alternate_names.")

    @property
    def display_name(self) -> str:
        """Expose standard display name derived from primary structured name."""
        return self.name.full_name

    @property
    def birth_year(self) -> int | None:
        """Extract lower-bound birth year."""
        return _extract_year_lower_bound(self.birth_date)

    @property
    def death_year(self) -> int | None:
        """Extract lower-bound death year."""
        return _extract_year_lower_bound(self.death_date)

    @property
    def approximate_age(self) -> int | None:
        """Calculate estimated lifespan duration in calendar years."""
        b_year = self.birth_year
        d_year = self.death_year
        if b_year is not None and d_year is not None:
            return d_year - b_year
        return None

    @property
    def sort_key(self) -> tuple[str, str, int, str]:
        """Deterministic Register Sort: (surname, given, birth_year_lower_bound, id)."""
        surname_key = (self.name.surname or "").lower()
        given_key = (self.name.given or "").lower()
        birth_year_key = self.birth_year if self.birth_year is not None else 9999
        return (surname_key, given_key, birth_year_key, self.id.value)

    def __str__(self) -> str:
        """Render concise human-readable individual summary."""
        dates: list[str] = []
        if self.birth_date:
            dates.append(f"b. {self.birth_date}")
        if self.death_date:
            dates.append(f"d. {self.death_date}")
        elif not self.is_deceased:
            dates.append("living")
        elif dates:
            dates.append("d. unk")

        span_str = f" ({', '.join(dates)})" if dates else ""
        return f"{self.display_name} [{self.sex}]{span_str} ({self.id.value})"
