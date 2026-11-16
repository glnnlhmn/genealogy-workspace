"""Path: src/gda/model/source/enumerated/census/population/schedule_1930.py

Fifteenth U.S. Federal Population Schedule domain models (1930).

Operational Role:
    Models the 1930 Population Schedule introducing home valuation/monthly rent,
    radio set ownership, farm residence flag, age at first marriage, and military
    veteran war code.
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
    "Population1930Entry",
    "PopulationSchedule1930",
]


@dataclass(
    repr=False,
    config=ConfigDict(kw_only=True, frozen=True, extra="forbid", strict=True),
)
class Population1930Entry(PopulationLineEntry):
    """Individual line entry for the 1930 U.S. Federal Population Schedule."""

    street_name_raw: str | None = Field(default=None, description="Urban street name.")
    house_number_raw: str | None = Field(default=None, description="Urban house number.")
    relationship_to_head_raw: str | None = Field(
        default=None, description="Relationship to head of family."
    )
    home_ownership: HomeOwnership | None = Field(
        default=None, description="Home owned ('O') or rented ('R')."
    )
    home_value_or_monthly_rent_raw: str | None = Field(
        default=None,
        description="Value of home if owned, or monthly rental if rented (1930 Column 8).",
    )
    has_radio_set: bool | None = Field(
        default=None, description="Whether household owned a radio set (1930 Column 9)."
    )
    lives_on_farm: bool | None = Field(
        default=None, description="Whether family lived on a farm (1930 Column 10)."
    )
    color_raw: str | None = Field(default=None, description="Color or race.")
    marital_status_raw: str | None = Field(default=None, description="Marital condition.")
    age_at_first_marriage: int | None = Field(
        default=None,
        ge=10,
        le=99,
        description="Age at first marriage (1930 Column 15).",
    )
    birthplace_raw: str | None = Field(default=None, description="Place of birth of person.")
    father_birthplace_raw: str | None = Field(default=None, description="Father's birthplace.")
    mother_birthplace_raw: str | None = Field(default=None, description="Mother's birthplace.")
    mother_tongue_raw: str | None = Field(
        default=None, description="Language spoken before coming to U.S."
    )
    immigration_year: int | None = Field(
        default=None, ge=1600, le=1930, description="Year of immigration to the United States."
    )
    citizenship_status: CitizenshipStatus | None = Field(
        default=None, description="Naturalization status ('Al', 'Pa', 'Na')."
    )
    occupation_raw: str | None = Field(default=None, description="Occupation.")
    industry_raw: str | None = Field(default=None, description="Industry.")
    veteran_war_code_raw: str | None = Field(
        default=None,
        description="Whether a veteran of U.S. military/naval forces and war ('WW', 'Sp', 'Civ').",
    )


@dataclass(
    repr=False,
    config=ConfigDict(kw_only=True, frozen=True, extra="forbid", strict=True),
)
class PopulationSchedule1930(PopulationScheduleRecord[Population1930Entry]):
    """Evidentiary 1930 U.S. Federal Population Schedule."""

    def __post_init__(self) -> None:
        """Enforce 1930 census year invariant."""
        super().__post_init__()

        if self.enumeration_year.value != 1930:
            raise ModelFormatError(
                f"PopulationSchedule1930 enumeration_year must be 1930, "
                f"got {self.enumeration_year.value}."
            )
