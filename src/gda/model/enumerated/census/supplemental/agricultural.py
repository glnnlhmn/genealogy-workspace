"""Path: src/gda/model/enumerated/census/supplemental/agricultural.py

Federal Census Productions of Agriculture Schedule domain models (1850-1880).

Operational Role:
    Models farm operator line entries, improved/unimproved acreage, farm cash
    valuations, livestock counts, and annual crop outputs.
"""

from __future__ import annotations

from typing import ClassVar

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.enums.sources import SourceRecordType
from gda.core.errors import ModelFormatError
from gda.core.types import US_AGRICULTURAL_SCHEDULE_YEARS
from gda.model.enumerated.census.base import CensusLineEntry, CensusScheduleRecord

__version__ = "1.0.0+build.1"

__all__ = [
    "AgriculturalScheduleEntry",
    "AgriculturalScheduleRecord",
]


@dataclass(
    repr=False,
    config=ConfigDict(kw_only=True, frozen=True, extra="forbid", strict=True),
)
class AgriculturalScheduleEntry(CensusLineEntry):
    """Farm proprietor/operator line entry on a Census Agricultural Schedule."""

    tenure_raw: str | None = Field(
        default=None,
        description="Farm tenure ('Owner', 'Rents for fixed money', 'Shares of products').",
    )
    improved_acres: int | None = Field(
        default=None, ge=0, description="Acres of improved/tilled land."
    )
    unimproved_acres: int | None = Field(
        default=None, ge=0, description="Acres of unimproved/woodland acreage."
    )
    farm_cash_value_usd: int | None = Field(
        default=None, ge=0, description="Cash value of farm in USD."
    )
    implements_value_usd: int | None = Field(
        default=None, ge=0, description="Value of farming implements and machinery in USD."
    )
    livestock_value_usd: int | None = Field(
        default=None, ge=0, description="Value of livestock in USD."
    )
    crop_summary_raw: str | None = Field(
        default=None, description="Summary of principal crops, bushels, and dairy outputs."
    )


@dataclass(
    repr=False,
    config=ConfigDict(kw_only=True, frozen=True, extra="forbid", strict=True),
)
class AgriculturalScheduleRecord(CensusScheduleRecord[AgriculturalScheduleEntry]):
    """Evidentiary composite for Census Agricultural Schedules (1850-1880)."""

    record_type: SourceRecordType = Field(
        default=SourceRecordType.AGRICULTURAL_SCHEDULE,
        description="Fixed AGRICULTURAL_SCHEDULE source record type.",
    )

    ALLOWED_RECORD_TYPES: ClassVar[frozenset[SourceRecordType]] = frozenset(
        {SourceRecordType.AGRICULTURAL_SCHEDULE}
    )

    def __post_init__(self) -> None:
        """Enforce 1850-1880 agricultural schedule year boundaries."""
        super().__post_init__()

        if self.enumeration_year.value not in US_AGRICULTURAL_SCHEDULE_YEARS:
            raise ModelFormatError(
                f"AgriculturalScheduleRecord enumeration_year must be in "
                f"{sorted(US_AGRICULTURAL_SCHEDULE_YEARS)}, got {self.enumeration_year.value}."
            )
