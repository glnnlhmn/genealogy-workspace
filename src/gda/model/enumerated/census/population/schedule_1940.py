"""Path: src/gda/model/enumerated/census/population/schedule_1940.py

Sixteenth U.S. Federal Population Schedule domain models (1940).

Operational Role:
    Models the 1940 Population Schedule introducing highest school grade completed,
    April 1, 1935 residence location, employment status, weeks worked in 1939,
    wage/salary income, and supplementary sample-line questions (lines 14 and 29).
"""

from __future__ import annotations

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.enums.fiscal import CitizenshipStatus, HomeOwnership
from gda.core.errors import ModelFormatError
from gda.model.enumerated.census.population.base import (
    PopulationLineEntry,
    PopulationScheduleRecord,
)

__version__ = "1.0.0+build.1"

__all__ = [
    "Population1940Entry",
    "PopulationSchedule1940",
]


@dataclass(
    repr=False,
    config=ConfigDict(kw_only=True, frozen=True, extra="forbid", strict=True),
)
class Population1940Entry(PopulationLineEntry):
    """Individual line entry for the 1940 U.S. Federal Population Schedule."""

    street_name_raw: str | None = Field(default=None, description="Urban street name.")
    house_number_raw: str | None = Field(default=None, description="Urban house number.")
    home_ownership: HomeOwnership | None = Field(
        default=None, description="Home owned ('O') or rented ('R')."
    )
    home_value_or_monthly_rent_raw: str | None = Field(
        default=None, description="Value of home or monthly rental."
    )
    lives_on_farm: bool | None = Field(
        default=None, description="Whether household lived on a farm."
    )
    relationship_to_head_raw: str | None = Field(
        default=None, description="Relationship to head of household."
    )
    color_raw: str | None = Field(default=None, description="Color or race.")
    marital_status_raw: str | None = Field(default=None, description="Marital status.")
    highest_grade_completed_raw: str | None = Field(
        default=None,
        description="Highest grade of school completed (e.g., '8', 'H-4', 'C-4').",
    )
    birthplace_raw: str | None = Field(default=None, description="Place of birth.")
    citizenship_status: CitizenshipStatus | None = Field(
        default=None, description="Citizenship of foreign born ('Na', 'Pa', 'Al', 'AmCit')."
    )
    residence_1935_raw: str | None = Field(
        default=None,
        description="Place of residence on April 1, 1935 (city/town, county, state).",
    )
    employment_status_raw: str | None = Field(
        default=None,
        description="At work ('Yes'), public emergency work, seeking work, or unable/housework.",
    )
    occupation_raw: str | None = Field(default=None, description="Current occupation.")
    industry_raw: str | None = Field(default=None, description="Current industry.")
    weeks_worked_1939: int | None = Field(
        default=None, ge=0, le=52, description="Number of weeks worked in 1939."
    )
    wage_salary_income_usd: int | None = Field(
        default=None, ge=0, description="Amount of money wages or salary received in 1939 (USD)."
    )
    is_sample_line: bool = Field(
        default=False,
        description="Flag indicating supplementary sample-line entry (Lines 14 and 29).",
    )
    father_birthplace_raw: str | None = Field(
        default=None, description="Father's birthplace (1940 sample-line question)."
    )
    mother_birthplace_raw: str | None = Field(
        default=None, description="Mother's birthplace (1940 sample-line question)."
    )
    usual_occupation_raw: str | None = Field(
        default=None, description="Usual occupation (1940 sample-line question)."
    )


@dataclass(
    repr=False,
    config=ConfigDict(kw_only=True, frozen=True, extra="forbid", strict=True),
)
class PopulationSchedule1940(PopulationScheduleRecord[Population1940Entry]):
    """Evidentiary 1940 U.S. Federal Population Schedule."""

    def __post_init__(self) -> None:
        """Enforce 1940 census year invariant."""
        super().__post_init__()

        if self.enumeration_year.value != 1940:
            raise ModelFormatError(
                f"PopulationSchedule1940 enumeration_year must be 1940, "
                f"got {self.enumeration_year.value}."
            )
