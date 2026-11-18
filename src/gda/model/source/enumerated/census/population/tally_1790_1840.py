"""Path: src/gda/model/source/enumerated/census/population/tally_1790_1840.py

Pre-1850 U.S. Federal Population Schedule domain models (1790-1840).

Operational Role:
    Models head-of-household enumeration lines and demographic age/sex/status
    tally counts across the First through Sixth U.S. Censuses (1790-1840).
"""

from __future__ import annotations

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.errors import ModelFormatError
from gda.core.types import US_FEDERAL_CENSUS_TALLY_YEARS
from gda.model.source.enumerated.census.base import CensusLineEntry
from gda.model.source.enumerated.census.population.base import PopulationScheduleRecord

__version__ = "1.0.0+build.2"

__all__ = [
    "HouseholdTallyEntry",
    "PopulationSchedule1790_1840",
]


@dataclass(
    repr=False,
    config=ConfigDict(frozen=True, extra="forbid", strict=True),
    kw_only=True,
)
class HouseholdTallyEntry(CensusLineEntry):
    """Head-of-household line entry with demographic tally counts (1790-1840)."""

    free_white_males_under_16: int | None = Field(
        default=None,
        ge=0,
        description="Count of free white males under 16 (or summed child brackets).",
    )
    free_white_males_16_and_over: int | None = Field(
        default=None,
        ge=0,
        description="Count of free white males aged 16 and upwards (or summed adult brackets).",
    )
    free_white_females: int | None = Field(
        default=None,
        ge=0,
        description="Total count of free white females in the household.",
    )
    free_colored_persons: int | None = Field(
        default=None,
        ge=0,
        description="Count of all other free persons / free colored persons.",
    )
    enslaved_persons: int | None = Field(
        default=None,
        ge=0,
        description="Count of enslaved persons enumerated in the household.",
    )
    total_in_household: int | None = Field(
        default=None,
        ge=0,
        description="Total enumerated persons in the household.",
    )
    revolutionary_pensioners_count: int | None = Field(
        default=None,
        ge=0,
        description="Count of Revolutionary or military pensioners (1840 schedule).",
    )
    age_bracket_tallies: dict[str, int] = Field(
        default_factory=dict,
        description="Granular column-level age/sex tally map (e.g., {'FWM_20_30': 1}).",
    )


@dataclass(
    repr=False,
    config=ConfigDict(frozen=True, extra="forbid", strict=True),
    kw_only=True,
)
class PopulationSchedule1790_1840(PopulationScheduleRecord[HouseholdTallyEntry]):  # type: ignore[type-var]
    """Evidentiary U.S. Federal Population Schedule for 1790-1840 tally censuses."""

    def __post_init__(self) -> None:
        """Enforce 1790-1840 decennial census year boundaries."""
        super().__post_init__()

        if self.enumeration_year.value not in US_FEDERAL_CENSUS_TALLY_YEARS:
            raise ModelFormatError(
                f"PopulationSchedule1790_1840 enumeration_year must be in "
                f"{sorted(US_FEDERAL_CENSUS_TALLY_YEARS)}, got {self.enumeration_year.value}."
            )
