"""Path: src/gda/model/military/service/separation.py

Discharge separation certificates and release records (DD-214, WD AGO).

Operational Role:
    Extends MilitaryServiceRecord to represent evidentiary discharge certificates,
    separation reports (DD Form 214, DD Form 215, WD AGO 53-55, NAVPERS 553),
    service characterizations, separation codes, and terminal pay notations.
"""

from __future__ import annotations

from enum import StrEnum
from typing import ClassVar

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.errors import ModelFormatError
from gda.enums.sources import SourceRecordCategory
from gda.model.atom.id import LocationID
from gda.model.military.service.base import MilitaryServiceRecord

__version__ = "1.0.0+build.1"

__all__ = [
    "SeparationDischargeRecord",
    "SeparationFormType",
]


class SeparationFormType(StrEnum):
    """Statutory or administrative certificate form type."""

    DD_214 = "DD_214"
    DD_215 = "DD_215"
    WD_AGO_53_55 = "WD_AGO_53_55"
    NAVPERS_553 = "NAVPERS_553"
    NAVMC_78_PD = "NAVMC_78_PD"
    CERTIFICATE_OF_DISCHARGE = "CERTIFICATE_OF_DISCHARGE"
    OTHER = "OTHER"


@dataclass(
    config=ConfigDict(
        kw_only=True, frozen=True, extra="forbid", str_strip_whitespace=True
    )
)
class SeparationDischargeRecord(MilitaryServiceRecord):
    """Evidentiary military discharge, release, or certificate of separation."""

    form_type: SeparationFormType = Field(
        ...,
        description="Standardized separation certificate or form type.",
    )
    separation_reason_raw: str | None = Field(
        default=None,
        description="Transcribed narrative reason for discharge or release authority.",
    )
    separation_code_raw: str | None = Field(
        default=None,
        description="Standard Separation Program Number (SPN) or Separation Designator (SPD).",
    )
    reentry_code_raw: str | None = Field(
        default=None,
        description="Selective Service / Armed Forces Reenlistment Eligibility Code (RE Code).",
    )
    foreign_service_months: int | None = Field(
        default=None,
        ge=0,
        le=600,
        description="Cumulative creditable foreign/sea service in months.",
    )
    separation_facility_raw: str | None = Field(
        default=None,
        description="Verbatim military installation, separation center, or ship of release.",
    )
    separation_location_id: LocationID | None = Field(
        default=None,
        description="Resolved civil jurisdiction LocationID for the discharge station.",
    )
    decorations_raw: str | None = Field(
        default=None,
        description="Verbatim transcription of Block 13/24 awards and decorations list.",
    )
    travel_allowance_paid_usd: float | None = Field(
        default=None,
        ge=0.0,
        description="Final settlement travel/mileage reimbursement paid to place of entry.",
    )

    EXPECTED_CATEGORY: ClassVar[SourceRecordCategory] = SourceRecordCategory.MILITARY

    def __post_init__(self) -> None:
        """Enforce separation field hygiene and chronological release validation."""
        super().__post_init__()

        if self.separation_year is None:
            raise ModelFormatError(
                "SeparationDischargeRecord requires an explicit separation_year.",
                details={"service_record_id": str(self.service_record_id)},
            )
