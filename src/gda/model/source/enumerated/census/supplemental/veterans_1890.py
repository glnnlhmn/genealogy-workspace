"""Path: src/gda/model/source/enumerated/census/supplemental/veterans_1890.py

1890 Special Schedule of Surviving Soldiers, Sailors, Marines, and Widows.

Operational Role:
    Models the 1890 Special Veterans Schedule capturing Union military unit,
    rank, enlistment/discharge dates, length of service, post office address,
    and wartime disability notations.
"""

from __future__ import annotations

from typing import ClassVar

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.constants import US_VETERANS_SCHEDULE_YEAR
from gda.core.enums.sources import SourceRecordType
from gda.core.errors import ModelFormatError
from gda.model.source.enumerated.census.base import CensusLineEntry, CensusScheduleRecord

__version__ = "1.0.0+build.2"

__all__ = [
    "Veterans1890Entry",
    "Veterans1890ScheduleRecord",
]


@dataclass(
    repr=False,
    config=ConfigDict(frozen=True, extra="forbid", strict=True),
    kw_only=True,
)
class Veterans1890Entry(CensusLineEntry):
    """Individual veteran or widow line entry on the 1890 Veterans Schedule."""

    widow_of_name_raw: str | None = Field(
        default=None,
        description="Verbatim name of deceased soldier if claimant is a surviving widow.",
    )
    rank_raw: str | None = Field(default=None, description="Military rank or naval rating.")
    company_raw: str | None = Field(
        default=None, description="Company or battery letter/designation."
    )
    regiment_or_vessel_raw: str | None = Field(
        default=None, description="Name of regiment, independent organization, or vessel."
    )
    enlistment_date_raw: str | None = Field(
        default=None, description="Verbatim date of enlistment or muster-in."
    )
    discharge_date_raw: str | None = Field(
        default=None, description="Verbatim date of discharge or muster-out."
    )
    service_length_raw: str | None = Field(
        default=None, description="Length of service in years, months, and days."
    )
    post_office_address_raw: str | None = Field(
        default=None, description="Post-office address of veteran or widow in June 1890."
    )
    disability_incurred_raw: str | None = Field(
        default=None, description="Verbatim wartime wound or disability incurred."
    )


@dataclass(
    repr=False,
    config=ConfigDict(frozen=True, extra="forbid", strict=True),
    kw_only=True,
)
class Veterans1890ScheduleRecord(CensusScheduleRecord[Veterans1890Entry]):
    """Evidentiary composite for the 1890 Special Veterans Schedule."""

    record_type: SourceRecordType = Field(
        default=SourceRecordType.VETERANS_SCHEDULE,
        description="Fixed VETERANS_SCHEDULE source record type.",
    )

    ALLOWED_RECORD_TYPES: ClassVar[frozenset[SourceRecordType]] = frozenset(
        {SourceRecordType.VETERANS_SCHEDULE}
    )

    def __post_init__(self) -> None:
        """Enforce 1890 enumeration year invariant."""
        super().__post_init__()

        if self.enumeration_year.value != US_VETERANS_SCHEDULE_YEAR:
            raise ModelFormatError(
                f"Veterans1890ScheduleRecord enumeration_year must be "
                f"{US_VETERANS_SCHEDULE_YEAR}, got {self.enumeration_year.value}."
            )
