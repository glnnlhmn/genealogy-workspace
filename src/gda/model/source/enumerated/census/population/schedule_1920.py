"""Path: src/gda/model/source/enumerated/census/population/schedule_1920.py

Fourteenth U.S. Federal Population Schedule domain models (1920).

Operational Role:
    Models the 1920 Population Schedule introducing exact year of naturalization
    and mother tongue columns for the individual, father, and mother.
"""

from __future__ import annotations

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.enums.fiscal import CitizenshipStatus, HomeOwnership
from gda.core.errors import ModelFormatError
from gda.model.source.enumerated.census.population.base import (
    PopulationLineEntry,
    PopulationScheduleRecord,
)

__version__ = "1.0.0+build.1"

__all__ = [
    "Population1920Entry",
    "PopulationSchedule1920",
]


@dataclass(
    repr=False,
    config=ConfigDict(kw_only=True, frozen=True, extra="forbid", strict=True),
)
class Population1920Entry(PopulationLineEntry):
    """Individual line entry for the 1920 U.S. Federal Population Schedule."""

    street_name_raw: str | None = Field(default=None, description="Urban street name.")
    house_number_raw: str | None = Field(default=None, description="Urban house number.")
    relationship_to_head_raw: str | None = Field(
        default=None, description="Relationship to head of family."
    )
    home_ownership: HomeOwnership | None = Field(
        default=None, description="Home owned or rented, free or mortgaged."
    )
    color_raw: str | None = Field(default=None, description="Color or race.")
    marital_status_raw: str | None = Field(default=None, description="Marital condition.")
    immigration_year: int | None = Field(
        default=None, ge=1600, le=1920, description="Year of immigration to the United States."
    )
    citizenship_status: CitizenshipStatus | None = Field(
        default=None, description="Naturalization status ('Al', 'Pa', 'Na')."
    )
    naturalization_year: int | None = Field(
        default=None,
        ge=1776,
        le=1920,
        description="Year of naturalization (introduced on the 1920 schedule).",
    )
    birthplace_raw: str | None = Field(default=None, description="Place of birth of person.")
    mother_tongue_raw: str | None = Field(
        default=None, description="Mother tongue of person (1920 Column 20)."
    )
    father_birthplace_raw: str | None = Field(default=None, description="Father's birthplace.")
    father_mother_tongue_raw: str | None = Field(
        default=None, description="Father's mother tongue (1920 Column 22)."
    )
    mother_birthplace_raw: str | None = Field(default=None, description="Mother's birthplace.")
    mother_mother_tongue_raw: str | None = Field(
        default=None, description="Mother's mother tongue (1920 Column 24)."
    )
    occupation_raw: str | None = Field(
        default=None, description="Trade, profession, or particular kind of work."
    )
    industry_raw: str | None = Field(
        default=None, description="Industry, business, or establishment in which at work."
    )
    employment_class_raw: str | None = Field(
        default=None,
        description="Employer ('Emp'), Salary/wage worker ('W'), or Own account ('OA').",
    )


@dataclass(
    repr=False,
    config=ConfigDict(kw_only=True, frozen=True, extra="forbid", strict=True),
)
class PopulationSchedule1920(PopulationScheduleRecord[Population1920Entry]):
    """Evidentiary 1920 U.S. Federal Population Schedule."""

    def __post_init__(self) -> None:
        """Enforce 1920 census year invariant."""
        super().__post_init__()

        if self.enumeration_year.value != 1920:
            raise ModelFormatError(
                f"PopulationSchedule1920 enumeration_year must be 1920, "
                f"got {self.enumeration_year.value}."
            )
