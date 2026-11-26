"""Path: src/gda/model/source/enumerated/census/population/schedule_1850_1870.py

Mid-century U.S. Federal Population Schedule domain models (1850, 1860, 1870).

Operational Role:
    Models individual-level enumerations introduced in 1850 through 1870,
    including real and personal estate valuations, birthplace, school attendance,
    literacy, and 1870 foreign-born parent indicators.
"""

from __future__ import annotations

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.constants import US_FEDERAL_CENSUS_1850_1870_YEARS
from gda.core.errors import ModelFormatError
from gda.model.source.enumerated.census.population.base import (
    PopulationLineEntry,
    PopulationScheduleRecord,
)

__version__ = "1.0.0+build.2"

__all__ = [
    "Population1850_1870Entry",
    "PopulationSchedule1850_1870",
]


@dataclass(
    repr=False,
    config=ConfigDict(frozen=True, extra="forbid", strict=True),
    kw_only=True,
)
class Population1850_1870Entry(PopulationLineEntry):
    """Individual line entry for 1850, 1860, and 1870 Federal Population Schedules."""

    color_raw: str | None = Field(
        default=None,
        description="Verbatim color/race notation ('W', 'B', 'M', 'C', 'I').",
    )
    occupation_raw: str | None = Field(
        default=None,
        description="Verbatim profession, occupation, or trade.",
    )
    real_estate_value_usd: int | None = Field(
        default=None,
        ge=0,
        description="Value of real estate owned in USD.",
    )
    personal_estate_value_usd: int | None = Field(
        default=None,
        ge=0,
        description="Value of personal estate owned in USD (1860 & 1870).",
    )
    birthplace_raw: str | None = Field(
        default=None,
        description="Verbatim state, territory, or country of birth.",
    )
    father_foreign_born: bool | None = Field(
        default=None,
        description="Flag indicating father was of foreign birth (1870 schedule).",
    )
    mother_foreign_born: bool | None = Field(
        default=None,
        description="Flag indicating mother was of foreign birth (1870 schedule).",
    )
    married_within_year: bool = Field(
        default=False,
        description="Flag indicating person was married within the census year.",
    )
    attended_school: bool = Field(
        default=False,
        description="Flag indicating person attended school within the census year.",
    )
    cannot_read_write: bool = Field(
        default=False,
        description="Flag indicating person over age 20/10 could not read or write.",
    )


@dataclass(
    repr=False,
    config=ConfigDict(frozen=True, extra="forbid", strict=True),
    kw_only=True,
)
class PopulationSchedule1850_1870(PopulationScheduleRecord[Population1850_1870Entry]):
    """Evidentiary U.S. Federal Population Schedule for 1850, 1860, and 1870."""

    def __post_init__(self) -> None:
        """Enforce 1850-1870 decennial census year boundaries."""
        super().__post_init__()

        if self.enumeration_year.value not in US_FEDERAL_CENSUS_1850_1870_YEARS:
            raise ModelFormatError(
                f"PopulationSchedule1850_1870 enumeration_year must be in "
                f"{sorted(US_FEDERAL_CENSUS_1850_1870_YEARS)}, got {self.enumeration_year.value}."
            )
