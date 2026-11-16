"""Path: src/gda/model/source/enumerated/census/population/schedule_1950.py

Seventeenth U.S. Federal Population Schedule domain models (1950).

Operational Role:
    Models the 1950 Population Schedule (Form P1) capturing street/avenue,
    house/serial number, farm residence, hours worked last week, occupation/industry,
    and 1950 sample-line questions (1949 residence, parents' birthplaces, veteran status).
"""

from __future__ import annotations

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.enums.fiscal import CitizenshipStatus
from gda.core.errors import ModelFormatError
from gda.model.source.enumerated.census.population.base import (
    PopulationLineEntry,
    PopulationScheduleRecord,
)

__version__ = "1.0.0+build.1"

__all__ = [
    "Population1950Entry",
    "PopulationSchedule1950",
]


@dataclass(
    repr=False,
    config=ConfigDict(kw_only=True, frozen=True, extra="forbid", strict=True),
)
class Population1950Entry(PopulationLineEntry):
    """Individual line entry for the 1950 U.S. Federal Population Schedule (Form P1)."""

    street_name_raw: str | None = Field(
        default=None, description="Name of street, avenue, or road."
    )
    house_number_raw: str | None = Field(
        default=None, description="House number and apartment number."
    )
    lives_on_farm: bool | None = Field(
        default=None, description="Is this house on a farm (or ranch)?"
    )
    relationship_to_head_raw: str | None = Field(
        default=None, description="Relationship to head of household."
    )
    race_raw: str | None = Field(
        default=None, description="Race ('W', 'Neg', 'Ind', 'Chi', 'Jap', 'Fil')."
    )
    marital_status_raw: str | None = Field(
        default=None, description="Marital status ('Mar', 'Wd', 'D', 'Sep', 'Nev')."
    )
    birthplace_raw: str | None = Field(
        default=None, description="State or foreign country of birth."
    )
    citizenship_status: CitizenshipStatus | None = Field(
        default=None, description="If foreign born, naturalized status ('Yes', 'No', 'AP')."
    )
    hours_worked_last_week: int | None = Field(
        default=None, ge=0, le=168, description="Hours worked during the preceding week."
    )
    occupation_raw: str | None = Field(default=None, description="Kind of work done.")
    industry_raw: str | None = Field(default=None, description="Kind of business or industry.")
    employment_class_raw: str | None = Field(
        default=None, description="Class of worker ('P', 'G', 'O', 'NP')."
    )
    is_sample_line: bool = Field(
        default=False,
        description="Flag indicating 1950 sample-line entry (Lines 4, 9, 14, 19, 24, 29).",
    )
    residence_1949_raw: str | None = Field(
        default=None, description="Was person living in same house/county a year ago (1949)?"
    )
    father_birthplace_raw: str | None = Field(
        default=None, description="Father's birthplace (1950 sample-line question)."
    )
    mother_birthplace_raw: str | None = Field(
        default=None, description="Mother's birthplace (1950 sample-line question)."
    )
    highest_grade_completed_raw: str | None = Field(
        default=None, description="Highest grade of school attended/finished (1950 sample line)."
    )
    veteran_service_raw: str | None = Field(
        default=None,
        description="Ever serve in U.S. Armed Forces (WWII, WWI, Other) (1950 sample line).",
    )


@dataclass(
    repr=False,
    config=ConfigDict(kw_only=True, frozen=True, extra="forbid", strict=True),
)
class PopulationSchedule1950(PopulationScheduleRecord[Population1950Entry]):
    """Evidentiary 1950 U.S. Federal Population Schedule."""

    def __post_init__(self) -> None:
        """Enforce 1950 census year invariant."""
        super().__post_init__()

        if self.enumeration_year.value != 1950:
            raise ModelFormatError(
                f"PopulationSchedule1950 enumeration_year must be 1950, "
                f"got {self.enumeration_year.value}."
            )
