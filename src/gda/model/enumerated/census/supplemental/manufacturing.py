"""Path: src/gda/model/enumerated/census/supplemental/manufacturing.py

Federal Census Products of Industry / Manufacturing Schedule models (1810-1880).

Operational Role:
    Models industrial establishments, proprietors, capital invested, workforce
    counts, wages, and annual manufactured product outputs.
"""

from __future__ import annotations

from typing import ClassVar

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.enums.sources import SourceRecordType
from gda.core.errors import ModelFormatError
from gda.core.types import US_MANUFACTURING_SCHEDULE_YEARS
from gda.model.enumerated.census.base import CensusLineEntry, CensusScheduleRecord

__version__ = "1.0.0+build.1"

__all__ = [
    "ManufacturingScheduleEntry",
    "ManufacturingScheduleRecord",
]


@dataclass(
    repr=False,
    config=ConfigDict(kw_only=True, frozen=True, extra="forbid", strict=True),
)
class ManufacturingScheduleEntry(CensusLineEntry):
    """Establishment or proprietor line entry on a Census Manufacturing Schedule."""

    business_or_product_raw: str | None = Field(
        default=None, description="Name of business, manufacture, or article produced."
    )
    capital_invested_usd: int | None = Field(
        default=None, ge=0, description="Capital invested in real and personal estate (USD)."
    )
    motive_power_raw: str | None = Field(
        default=None,
        description="Kind of motive power or machinery (e.g., 'Water', 'Steam', 'Hand').",
    )
    male_hands_count: int | None = Field(
        default=None, ge=0, description="Average number of male hands employed."
    )
    female_hands_count: int | None = Field(
        default=None, ge=0, description="Average number of female hands employed."
    )
    annual_wages_usd: int | None = Field(
        default=None, ge=0, description="Total annual amount paid in wages (USD)."
    )
    annual_product_value_usd: int | None = Field(
        default=None, ge=0, description="Total annual value of manufactured product (USD)."
    )


@dataclass(
    repr=False,
    config=ConfigDict(kw_only=True, frozen=True, extra="forbid", strict=True),
)
class ManufacturingScheduleRecord(CensusScheduleRecord[ManufacturingScheduleEntry]):
    """Evidentiary composite for Census Manufacturing Schedules (1810-1880)."""

    record_type: SourceRecordType = Field(
        default=SourceRecordType.MANUFACTURING_SCHEDULE,
        description="Fixed MANUFACTURING_SCHEDULE source record type.",
    )

    ALLOWED_RECORD_TYPES: ClassVar[frozenset[SourceRecordType]] = frozenset(
        {SourceRecordType.MANUFACTURING_SCHEDULE}
    )

    def __post_init__(self) -> None:
        """Enforce 1810-1880 manufacturing schedule year boundaries."""
        super().__post_init__()

        if self.enumeration_year.value not in US_MANUFACTURING_SCHEDULE_YEARS:
            raise ModelFormatError(
                f"ManufacturingScheduleRecord enumeration_year must be in "
                f"{sorted(US_MANUFACTURING_SCHEDULE_YEARS)}, got {self.enumeration_year.value}."
            )
