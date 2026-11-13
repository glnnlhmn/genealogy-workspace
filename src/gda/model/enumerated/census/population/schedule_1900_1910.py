"""Path: src/gda/model/enumerated/census/population/schedule_1900_1910.py

Twelfth and Thirteenth U.S. Federal Population Schedule domain models (1900, 1910).

Operational Role:
    Models the 1900 and 1910 Population Schedules capturing exact birth month/year
    (1900), years married, children born/living, immigration year, naturalization
    status, spoken language/mother tongue, home tenure, and 1910 Civil War veteran codes.
"""

from __future__ import annotations

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.enums.fiscal import CitizenshipStatus, HomeOwnership
from gda.core.errors import ModelFormatError
from gda.core.types import US_FEDERAL_CENSUS_1900_1910_YEARS
from gda.model.enumerated.census.population.base import (
    PopulationLineEntry,
    PopulationScheduleRecord,
)

__version__ = "1.0.0+build.1"

__all__ = [
    "Population1900_1910Entry",
    "PopulationSchedule1900_1910",
]


@dataclass(
    repr=False,
    config=ConfigDict(kw_only=True, frozen=True, extra="forbid", strict=True),
)
class Population1900_1910Entry(PopulationLineEntry):
    """Individual line entry for 1900 and 1910 U.S. Federal Population Schedules."""

    street_name_raw: str | None = Field(default=None, description="Urban street name.")
    house_number_raw: str | None = Field(default=None, description="Urban house number.")
    relationship_to_head_raw: str | None = Field(
        default=None, description="Verbatim relationship to head of family."
    )
    color_raw: str | None = Field(default=None, description="Verbatim color or race.")
    birth_month_raw: str | None = Field(
        default=None,
        description="Month of birth recorded on the 1900 schedule (e.g., 'May', 'Oct').",
    )
    birth_year_raw: str | None = Field(
        default=None,
        description="Year of birth recorded on the 1900 schedule (e.g., '1864').",
    )
    marital_status_raw: str | None = Field(
        default=None,
        description="Marital status ('S', 'M', 'M1', 'M2', 'Wd', 'D').",
    )
    years_married: int | None = Field(
        default=None,
        ge=0,
        le=99,
        description="Number of years of present marriage.",
    )
    mother_of_how_many_children: int | None = Field(
        default=None,
        ge=0,
        le=30,
        description="Total children born to mother.",
    )
    number_of_children_living: int | None = Field(
        default=None,
        ge=0,
        le=30,
        description="Number of those children still living on census day.",
    )
    birthplace_raw: str | None = Field(default=None, description="Person's birthplace.")
    father_birthplace_raw: str | None = Field(default=None, description="Father's birthplace.")
    mother_birthplace_raw: str | None = Field(default=None, description="Mother's birthplace.")
    immigration_year: int | None = Field(
        default=None,
        ge=1600,
        le=1910,
        description="Year of immigration to the United States.",
    )
    years_in_us: int | None = Field(
        default=None,
        ge=0,
        le=120,
        description="Number of years resident in the United States (1900 schedule).",
    )
    citizenship_status: CitizenshipStatus | None = Field(
        default=None,
        description="Normalized citizenship/naturalization status ('AL', 'PA', 'NA').",
    )
    occupation_raw: str | None = Field(
        default=None, description="Trade, profession, or particular kind of work."
    )
    industry_raw: str | None = Field(
        default=None, description="General nature of industry, business, or establishment (1910)."
    )
    spoken_language_raw: str | None = Field(
        default=None, description="Whether able to speak English or language spoken."
    )
    home_ownership: HomeOwnership | None = Field(
        default=None, description="Home owned or rented, free or mortgaged."
    )
    farm_or_house: str | None = Field(
        default=None, description="Farm ('F') or House ('H') tenure indicator."
    )
    civil_war_survivor_code: str | None = Field(
        default=None,
        description="1910 Column 30 survivor indicator ('UA', 'UN', 'CA', 'CN').",
    )


@dataclass(
    repr=False,
    config=ConfigDict(kw_only=True, frozen=True, extra="forbid", strict=True),
)
class PopulationSchedule1900_1910(PopulationScheduleRecord[Population1900_1910Entry]):
    """Evidentiary 1900 and 1910 U.S. Federal Population Schedules."""

    def __post_init__(self) -> None:
        """Enforce 1900 or 1910 decennial census year invariant."""
        super().__post_init__()

        if self.enumeration_year.value not in US_FEDERAL_CENSUS_1900_1910_YEARS:
            raise ModelFormatError(
                f"PopulationSchedule1900_1910 enumeration_year must be in "
                f"{sorted(US_FEDERAL_CENSUS_1900_1910_YEARS)}, got {self.enumeration_year.value}."
            )
