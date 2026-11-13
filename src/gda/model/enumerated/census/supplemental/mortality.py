"""Path: src/gda/model/enumerated/census/supplemental/mortality.py

Federal and state Census Mortality Schedule domain models (1850-1885).

Operational Role:
    Models non-population Mortality Schedules recording persons who died
    during the twelve months preceding the census enumeration date.
"""

from __future__ import annotations

from typing import ClassVar

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.enums.sources import SourceRecordType
from gda.core.errors import ModelFormatError
from gda.core.types import US_MORTALITY_SCHEDULE_YEARS
from gda.model.enumerated.census.base import CensusLineEntry, CensusScheduleRecord

__version__ = "1.0.0+build.1"

__all__ = [
    "MortalityScheduleEntry",
    "MortalityScheduleRecord",
]


@dataclass(
    repr=False,
    config=ConfigDict(kw_only=True, frozen=True, extra="forbid", strict=True),
)
class MortalityScheduleEntry(CensusLineEntry):
    """Individual decedent line entry on a Census Mortality Schedule."""

    color_raw: str | None = Field(default=None, description="Verbatim color/race notation.")
    marital_status_raw: str | None = Field(
        default=None, description="Marital condition at time of death ('M', 'W', 'S')."
    )
    birthplace_raw: str | None = Field(default=None, description="State or country of birth.")
    father_birthplace_raw: str | None = Field(
        default=None, description="Father's birthplace (1880 mortality schedule)."
    )
    mother_birthplace_raw: str | None = Field(
        default=None, description="Mother's birthplace (1880 mortality schedule)."
    )
    month_of_death_raw: str | None = Field(
        default=None, description="Calendar month in which death occurred (e.g., 'Jan', 'Oct')."
    )
    occupation_raw: str | None = Field(
        default=None, description="Profession, occupation, or trade."
    )
    cause_of_death_raw: str | None = Field(
        default=None, description="Verbatim disease or cause of death."
    )
    illness_duration_raw: str | None = Field(
        default=None, description="Number of days or weeks ill before death."
    )
    attending_physician_raw: str | None = Field(
        default=None, description="Name of physician attending decedent (1880 schedule)."
    )


@dataclass(
    repr=False,
    config=ConfigDict(kw_only=True, frozen=True, extra="forbid", strict=True),
)
class MortalityScheduleRecord(CensusScheduleRecord[MortalityScheduleEntry]):
    """Evidentiary composite for Census Mortality Schedules (1850-1885)."""

    record_type: SourceRecordType = Field(
        default=SourceRecordType.MORTALITY_SCHEDULE,
        description="Fixed MORTALITY_SCHEDULE source record type.",
    )

    ALLOWED_RECORD_TYPES: ClassVar[frozenset[SourceRecordType]] = frozenset(
        {SourceRecordType.MORTALITY_SCHEDULE}
    )

    def __post_init__(self) -> None:
        """Enforce 1850-1885 mortality schedule year boundaries."""
        super().__post_init__()

        if self.enumeration_year.value not in US_MORTALITY_SCHEDULE_YEARS:
            raise ModelFormatError(
                f"MortalityScheduleRecord enumeration_year must be in "
                f"{sorted(US_MORTALITY_SCHEDULE_YEARS)}, got {self.enumeration_year.value}."
            )
