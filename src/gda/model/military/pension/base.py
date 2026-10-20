"""Path: src/gda/model/military/pension/base.py

Foundational military pension domain entity model.

Operational Role:
    Extends SourceRecord composite to represent military pension application files,
    certificate jackets, payment vouchers, and ledger registrations across federal
    and state pension administrations.
"""

from __future__ import annotations

from typing import ClassVar

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.errors import ModelFormatError
from gda.enums.sources import SourceRecordCategory
from gda.model.atom.date import HistoricalYear
from gda.model.atom.id import IndividualID, LocationID, TranscriptID
from gda.model.base.source_record import SourceRecord
from gda.model.military.pension import (
    PensionClaimantRole,
    PensionPaymentAuthority,
)

__version__ = "1.0.0+build.1"

__all__ = ["MilitaryPensionRecord"]


@dataclass(
    config=ConfigDict(
        kw_only=True, frozen=True, extra="forbid", str_strip_whitespace=True
    )
)
class MilitaryPensionRecord(SourceRecord):
    """Evidentiary military pension application, certificate, or payment ledger record."""

    veteran_id: IndividualID = Field(
        ...,
        description="Canonical IndividualID of the veteran whose service justifies the pension.",
    )
    veteran_name_raw: str = Field(
        ...,
        description="Verbatim transcribed name of the veteran from the pension jacket/file.",
    )
    claimant_id: IndividualID = Field(
        ...,
        description="Canonical IndividualID of the claimant (veteran, widow, or dependent).",
    )
    claimant_name_raw: str = Field(
        ...,
        description="Verbatim transcribed name of the person petitioning for the pension.",
    )
    claimant_role: PensionClaimantRole = Field(
        ...,
        description="Relationship role of the claimant to the veteran.",
    )
    payment_authority: PensionPaymentAuthority = Field(
        ...,
        description="Statutory authority or administration governing pension disbursement.",
    )
    application_year: HistoricalYear = Field(
        ...,
        description="Calendar year the initial pension application or declaration was executed.",
    )
    application_number_raw: str | None = Field(
        default=None,
        description="Verbatim application/docket/file number (SO, WO, etc.).",
    )
    certificate_number_raw: str | None = Field(
        default=None,
        description="Verbatim approved pension certificate number (SC, WC, etc.).",
    )
    law_or_act_raw: str | None = Field(
        default=None,
        description="Verbatim statutory congressional act under which claim was filed.",
    )
    service_unit_raw: str | None = Field(
        default=None,
        description="Verbatim regiment, company, ship, or station cited in pension declaration.",
    )
    application_location_raw: str | None = Field(
        default=None,
        description="Verbatim county, court, or city where declaration was sworn.",
    )
    application_location_id: LocationID | None = Field(
        default=None,
        description="Resolved civil jurisdiction LocationID where application was filed.",
    )
    transcript_id: TranscriptID | None = Field(
        default=None,
        description="Decoupled TranscriptID linking verbatim claimant depositions or affidavits.",
    )

    EXPECTED_CATEGORY: ClassVar[SourceRecordCategory] = SourceRecordCategory.MILITARY

    def __post_init__(self) -> None:
        """Enforce domain category, text sanitization, and identifier consistency."""
        super().__post_init__()

        if self.record_category != self.EXPECTED_CATEGORY:
            raise ModelFormatError(
                f"MilitaryPensionRecord requires category '{self.EXPECTED_CATEGORY.value}', "
                f"got '{self.record_category.value}'."
            )

        vet_name = self.veteran_name_raw.strip()
        if not vet_name:
            raise ModelFormatError(
                "MilitaryPensionRecord 'veteran_name_raw' cannot be empty or whitespace."
            )
        object.__setattr__(self, "veteran_name_raw", vet_name)

        clm_name = self.claimant_name_raw.strip()
        if not clm_name:
            raise ModelFormatError(
                "MilitaryPensionRecord 'claimant_name_raw' cannot be empty or whitespace."
            )
        object.__setattr__(self, "claimant_name_raw", clm_name)

        if (
            self.claimant_role == PensionClaimantRole.VETERAN
            and self.claimant_id != self.veteran_id
        ):
            raise ModelFormatError(
                f"When claimant_role is VETERAN, claimant_id ({self.claimant_id}) "
                f"must equal veteran_id ({self.veteran_id})."
            )

    def __str__(self) -> str:
        cert = (
            f" Cert#{self.certificate_number_raw}"
            if self.certificate_number_raw
            else ""
        )
        app = (
            f" App#{self.application_number_raw}" if self.application_number_raw else ""
        )
        return (
            f"MilitaryPensionRecord [{self.payment_authority.value}] {self.claimant_name_raw} "
            f"({self.claimant_role.value}) - Vet: {self.veteran_name_raw} "
            f"({self.application_year.value}){app}{cert}"
        )
