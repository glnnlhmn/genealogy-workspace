"""Path: src/gda/model/military/pension/bounty_land.py

Federal and state military bounty land warrant application and patent records.

Operational Role:
    Extends SourceRecord composite to represent military bounty land warrant
    applications, warrant certificates, statutory acreage entitlements, and
    patent assignments under Congressional Bounty Land Acts (1850, 1852, 1855).
"""

from __future__ import annotations

from typing import ClassVar

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.enums.military import BountyLandAct, PensionClaimantRole
from gda.core.enums.sources import SourceRecordCategory
from gda.core.errors import ModelFormatError
from gda.core.types import MAX_BOUNTY_LAND_ACREAGE
from gda.model.atom.id import IndividualID, LocationID, TranscriptID
from gda.model.atom.year import HistoricalYear
from gda.model.base.source import SourceRecord

__version__ = "2.1.0+build.1"

__all__ = ["BountyLandAct", "BountyLandWarrantRecord"]


@dataclass(
    repr=False,
    config=ConfigDict(kw_only=True, frozen=True, extra="forbid", strict=True),
)
class BountyLandWarrantRecord(SourceRecord):
    """Evidentiary military bounty land warrant application, certificate, or patent."""

    veteran_id: IndividualID = Field(
        ...,
        description="Canonical IndividualID of the veteran whose service justifies the warrant.",
    )
    veteran_name_raw: str = Field(
        ...,
        description="Verbatim transcribed name of the veteran from warrant files.",
    )
    warrantee_id: IndividualID = Field(
        ...,
        description="Canonical IndividualID of the warrantee (veteran, heir, or assignee).",
    )
    warrantee_name_raw: str = Field(
        ...,
        description="Verbatim transcribed name of the warrant recipient.",
    )
    claimant_role: PensionClaimantRole = Field(
        ...,
        description="Relationship role of the warrantee to the veteran.",
    )
    bounty_act: BountyLandAct = Field(
        ...,
        description="Statutory Congressional Act authorizing the warrant grant.",
    )
    warrant_number_raw: str = Field(
        ...,
        description="Verbatim bounty land warrant number issued by Pension/Land Office.",
    )
    acreage: int = Field(
        ...,
        ge=1,
        le=MAX_BOUNTY_LAND_ACREAGE,
        description="Number of acres granted (typically 40, 80, 120, or 160 acres).",
    )
    warrant_year: HistoricalYear = Field(
        ...,
        description="Calendar year the warrant was granted or patented.",
    )
    patent_land_office_raw: str | None = Field(
        default=None,
        description="Verbatim General Land Office (GLO) district where warrant was located.",
    )
    patent_location_id: LocationID | None = Field(
        default=None,
        description="Resolved civil jurisdiction LocationID of the patented land parcel.",
    )
    assignee_id: IndividualID | None = Field(
        default=None,
        description="Canonical IndividualID of assignee if warrant was sold or transferred.",
    )
    assignee_name_raw: str | None = Field(
        default=None,
        description="Verbatim name of assignee purchasing or locating the warrant.",
    )
    transcript_id: TranscriptID | None = Field(
        default=None,
        description="Decoupled TranscriptID linking warrant application or patent extract.",
    )

    EXPECTED_CATEGORY: ClassVar[SourceRecordCategory] = SourceRecordCategory.MILITARY

    def __post_init__(self) -> None:
        """Enforce domain category, text sanitization, and assignee coherence."""
        super().__post_init__()

        if self.record_category != self.EXPECTED_CATEGORY:
            raise ModelFormatError(
                f"BountyLandWarrantRecord requires category '{self.EXPECTED_CATEGORY.value}', "
                f"got '{self.record_category.value}'."
            )

        vet_name = self.veteran_name_raw.strip()
        if not vet_name:
            raise ModelFormatError(
                "BountyLandWarrantRecord 'veteran_name_raw' cannot be empty or whitespace."
            )
        if vet_name != self.veteran_name_raw:
            object.__setattr__(self, "veteran_name_raw", vet_name)

        warr_name = self.warrantee_name_raw.strip()
        if not warr_name:
            raise ModelFormatError(
                "BountyLandWarrantRecord 'warrantee_name_raw' cannot be empty or whitespace."
            )
        if warr_name != self.warrantee_name_raw:
            object.__setattr__(self, "warrantee_name_raw", warr_name)

        warr_num = self.warrant_number_raw.strip()
        if not warr_num:
            raise ModelFormatError(
                "BountyLandWarrantRecord 'warrant_number_raw' cannot be empty or whitespace."
            )
        if warr_num != self.warrant_number_raw:
            object.__setattr__(self, "warrant_number_raw", warr_num)

        if self.assignee_id is not None or self.assignee_name_raw is not None:
            assignee_str = self.assignee_name_raw.strip() if self.assignee_name_raw else ""
            if not assignee_str and self.assignee_id is None:
                raise ModelFormatError(
                    "BountyLandWarrantRecord requires non-empty assignee_name_raw "
                    "or assignee_id when specifying warrant assignment."
                )
            normalized_assignee = assignee_str or None
            if normalized_assignee != self.assignee_name_raw:
                object.__setattr__(self, "assignee_name_raw", normalized_assignee)

    def __str__(self) -> str:
        return (
            f"BountyLandWarrantRecord [{self.bounty_act.value}] Warrant#{self.warrant_number_raw} "
            f"({self.acreage} acres) - {self.warrantee_name_raw} ({self.warrant_year.value})"
        )

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(veteran_id={self.veteran_id!r}, "
            f"bounty_act={self.bounty_act!r}, warrant_number_raw={self.warrant_number_raw!r}, "
            f"acreage={self.acreage!r})"
        )
