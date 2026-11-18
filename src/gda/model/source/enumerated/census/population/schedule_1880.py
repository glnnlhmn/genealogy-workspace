"""Path: src/gda/model/source/enumerated/census/population/schedule_1880.py

Tenth U.S. Federal Population Schedule domain models (1880).

Operational Role:
    Models the 1880 Population Schedule introducing urban street/house numbers,
    explicit relationship to head of household, marital status, unemployment months,
    sickness/disability notations, and parents' exact birthplaces.
"""

from __future__ import annotations

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.errors import ModelFormatError
from gda.model.source.enumerated.census.population.base import (
    PopulationLineEntry,
    PopulationScheduleRecord,
)

__version__ = "1.0.0+build.2"

__all__ = [
    "Population1880Entry",
    "PopulationSchedule1880",
]


@dataclass(
    repr=False,
    config=ConfigDict(frozen=True, extra="forbid", strict=True),
    kw_only=True,
)
class Population1880Entry(PopulationLineEntry):
    """Individual line entry for the 1880 U.S. Federal Population Schedule."""

    street_name_raw: str | None = Field(
        default=None,
        description="Street name recorded in the left margin on urban 1880 schedules.",
    )
    house_number_raw: str | None = Field(
        default=None,
        description="Street house number recorded on urban 1880 schedules.",
    )
    color_raw: str | None = Field(
        default=None,
        description="Verbatim color/race notation ('W', 'B', 'Mu', 'C', 'I').",
    )
    relationship_to_head_raw: str | None = Field(
        default=None,
        description="Verbatim relationship to head of family (e.g., 'Wife', 'Son', 'Boarder').",
    )
    marital_status_raw: str | None = Field(
        default=None,
        description="Verbatim civil condition ('S', 'M', 'W', 'D').",
    )
    married_within_year: bool = Field(
        default=False,
        description="Flag indicating person was married during the census year.",
    )
    occupation_raw: str | None = Field(
        default=None,
        description="Verbatim profession, occupation, or trade.",
    )
    months_unemployed: int | None = Field(
        default=None,
        ge=0,
        le=12,
        description="Number of months unemployed during the census year.",
    )
    illness_or_disability_raw: str | None = Field(
        default=None,
        description="Verbatim sickness, temporary disability, or infirmity noted on census day.",
    )
    attended_school: bool = Field(
        default=False,
        description="Flag indicating school attendance within the census year.",
    )
    cannot_read_write: bool = Field(
        default=False,
        description="Flag indicating inability to read or write.",
    )
    birthplace_raw: str | None = Field(
        default=None,
        description="Verbatim place of birth of the enumerated person.",
    )
    father_birthplace_raw: str | None = Field(
        default=None,
        description="Verbatim place of birth of the person's father.",
    )
    mother_birthplace_raw: str | None = Field(
        default=None,
        description="Verbatim place of birth of the person's mother.",
    )


@dataclass(
    repr=False,
    config=ConfigDict(frozen=True, extra="forbid", strict=True),
    kw_only=True,
)
class PopulationSchedule1880(PopulationScheduleRecord[Population1880Entry]):
    """Evidentiary 1880 U.S. Federal Population Schedule."""

    def __post_init__(self) -> None:
        """Enforce 1880 census year invariant."""
        super().__post_init__()

        if self.enumeration_year.value != 1880:
            raise ModelFormatError(
                f"PopulationSchedule1880 enumeration_year must be 1880, "
                f"got {self.enumeration_year.value}."
            )
