"""Path: src/gda/model/military/service/base.py

Foundational military service record domain entity model.

Operational Role:
    Extends SourceRecord composite to represent military service events, including
    enlistments, muster rolls, Compiled Military Service Records (CMSR), and discharge
    separation certificates across historical conflicts and armed service branches.
"""

from __future__ import annotations

from typing import ClassVar

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.errors import ModelFormatError
from gda.enums.sources import SourceRecordCategory
from gda.model.atom.date import HistoricalYear
from gda.model.atom.id import IndividualID, LocationID, ServiceRecordID, TranscriptID
from gda.model.base.source_record import SourceRecord
from gda.model.military.service import (
    MilitaryBranch,
    SeparationCharacter,
    ServiceComponent,
)

__version__ = "1.0.0+build.4"

__all__ = ["MilitaryServiceRecord"]


@dataclass(
    config=ConfigDict(
        kw_only=True, frozen=True, extra="forbid", str_strip_whitespace=True
    )
)
class MilitaryServiceRecord(SourceRecord):
    """Evidentiary military active service, enlistment, or discharge separation record."""

    service_record_id: ServiceRecordID = Field(
        ...,
        description="Canonical military service record identifier (UUIDv4).",
    )
    veteran_id: IndividualID = Field(
        ...,
        description="Canonical IndividualID of the enlisted or commissioned servicemember.",
    )
    veteran_name_raw: str = Field(
        ...,
        description="Verbatim transcribed name of the servicemember from the roll/form.",
    )
    branch: MilitaryBranch = Field(
        ...,
        description="Armed force branch (e.g., ARMY, NAVY, CONTINENTAL_ARMY).",
    )
    service_component: ServiceComponent = Field(
        default=ServiceComponent.REGULAR,
        description="Service component (REGULAR, VOLUNTEER, NATIONAL_GUARD, etc.).",
    )
    unit_designation_raw: str = Field(
        ...,
        description="Verbatim company, regiment, battalion, ship, or squadron designation.",
    )
    rank_raw: str = Field(
        ...,
        description="Recorded rank or rate (e.g., 'Private', 'Corporal', 'Seaman 1st Class').",
    )
    service_number_raw: str | None = Field(
        default=None,
        description="Military service serial number (MOS/SSN/Serial) if assigned.",
    )
    enlistment_year: HistoricalYear | None = Field(
        default=None,
        description="Calendar year of enlistment, induction, or commissioning.",
    )
    separation_year: HistoricalYear | None = Field(
        default=None,
        description="Calendar year of muster-out, discharge, or end of active service.",
    )
    separation_character: SeparationCharacter = Field(
        default=SeparationCharacter.HONORABLE,
        description="Character of service release or discharge.",
    )
    enlistment_location_raw: str | None = Field(
        default=None,
        description="Verbatim place of muster-in or enlistment rendezvous.",
    )
    enlistment_location_id: LocationID | None = Field(
        default=None,
        description="Resolved civil jurisdiction LocationID for enlistment site.",
    )
    transcript_id: TranscriptID | None = Field(
        default=None,
        description="Decoupled TranscriptID linking full service or separation text extract.",
    )

    EXPECTED_CATEGORY: ClassVar[SourceRecordCategory] = SourceRecordCategory.MILITARY

    def __post_init__(self) -> None:
        """Enforce domain category, chronological order, and raw text hygiene."""
        super().__post_init__()

        if self.record_category != self.EXPECTED_CATEGORY:
            raise ModelFormatError(
                f"MilitaryServiceRecord requires category '{self.EXPECTED_CATEGORY.value}', "
                f"got '{self.record_category.value}'."
            )

        vet_name = self.veteran_name_raw.strip()
        if not vet_name:
            raise ModelFormatError(
                "MilitaryServiceRecord 'veteran_name_raw' cannot be empty or whitespace.",
                details={"service_record_id": str(self.service_record_id)},
            )
        object.__setattr__(self, "veteran_name_raw", vet_name)

        unit_raw = self.unit_designation_raw.strip()
        if not unit_raw:
            raise ModelFormatError(
                "MilitaryServiceRecord 'unit_designation_raw' cannot be empty or whitespace.",
                details={"service_record_id": str(self.service_record_id)},
            )
        object.__setattr__(self, "unit_designation_raw", unit_raw)

        rank_str = self.rank_raw.strip()
        if not rank_str:
            raise ModelFormatError(
                "MilitaryServiceRecord 'rank_raw' cannot be empty or whitespace.",
                details={"service_record_id": str(self.service_record_id)},
            )
        object.__setattr__(self, "rank_raw", rank_str)

        self._validate_chronology()

    def _validate_chronology(self) -> None:
        """Validate chronological coherence between enlistment and separation."""
        if self.enlistment_year is None or self.separation_year is None:
            return

        if self.separation_year.value < self.enlistment_year.value:
            raise ModelFormatError(
                f"separation_year ({self.separation_year.value}) cannot precede "
                f"enlistment_year ({self.enlistment_year.value}).",
                details={
                    "enlistment_year": self.enlistment_year.value,
                    "separation_year": self.separation_year.value,
                },
            )

    def __str__(self) -> str:
        enl = self.enlistment_year.value if self.enlistment_year else "?"
        sep = self.separation_year.value if self.separation_year else "?"
        return (
            f"MilitaryServiceRecord [{self.branch.value}] {self.rank_raw} {self.veteran_name_raw} - "
            f"{self.unit_designation_raw} ({enl}-{sep})"
        )
