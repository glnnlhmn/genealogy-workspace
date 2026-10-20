"""Path: src/gda/model/military/draft/civil_war.py

Civil War military draft and enrollment record domain entity model.

Operational Role:
    Extends MilitaryDraftRecord to capture enrollment under the 1863 US Enrollment
    Act and Confederate conscription acts. Enforces enrollment class structures,
    congressional district allocations, substitute provisions, and commutation payments.
"""

from __future__ import annotations

from enum import StrEnum
from typing import ClassVar

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.errors import ModelFormatError
from gda.model.atom.id import IndividualID
from gda.model.military.draft.base import DraftCardTier, MilitaryDraftRecord

__version__ = "1.0.0+build.1"

__all__ = [
    "CivilWarConscriptionAllegiance",
    "CivilWarDraftRecord",
    "CivilWarEnrollmentClass",
]


class CivilWarConscriptionAllegiance(StrEnum):
    """Allegiance authority governing the draft enrollment."""

    UNION = "UNION"
    CONFEDERATE = "CONFEDERATE"


class CivilWarEnrollmentClass(StrEnum):
    """Statutory enrollment classification under the Conscription/Enrollment Acts."""

    CLASS_1 = "CLASS_1"  # Unmarried men ages 20-45; married men ages 20-35
    CLASS_2 = "CLASS_2"  # Married men over age 35
    VOLUNTEER_EXEMPT = "VOLUNTEER_EXEMPT"  # Already in service or honorably discharged
    CONFEDERATE_GENERAL = "CONFEDERATE_GENERAL"  # Standard Confederate conscript class


@dataclass(
    config=ConfigDict(
        kw_only=True, frozen=True, extra="forbid", str_strip_whitespace=True
    )
)
class CivilWarDraftRecord(MilitaryDraftRecord):
    """Evidentiary draft enrollment record from the American Civil War (1862-1865)."""

    allegiance: CivilWarConscriptionAllegiance = Field(
        default=CivilWarConscriptionAllegiance.UNION,
        description="Conscription authority (UNION or CONFEDERATE).",
    )
    enrollment_class: CivilWarEnrollmentClass = Field(
        default=CivilWarEnrollmentClass.CLASS_1,
        description="Statutory conscription class under the Enrollment Act.",
    )
    congressional_district: str | None = Field(
        default=None,
        description="Federal or Confederate congressional district designation.",
    )
    subdistrict_verbatim: str | None = Field(
        default=None,
        description="Local enrollment sub-district, ward, or township heading.",
    )
    former_military_service: str | None = Field(
        default=None,
        description="Prior regiment, company, or naval service recorded on roll.",
    )
    commutation_paid: bool = Field(
        default=False,
        description="Whether the $300 commutation fee was paid to avoid service.",
    )
    substitute_provided: bool = Field(
        default=False,
        description="Whether a designated substitute was furnished.",
    )
    substitute_individual_id: IndividualID | None = Field(
        default=None,
        description="Resolved IndividualID of the hired substitute (if known).",
    )
    substitute_name_raw: str | None = Field(
        default=None,
        description="Transcribed raw name of the furnished substitute.",
    )

    VALID_TIERS: ClassVar[set[DraftCardTier]] = {DraftCardTier.OTHER}

    def __post_init__(self) -> None:
        """Enforce Civil War enrollment year boundaries and substitution rules."""
        super().__post_init__()

        if not (1862 <= self.draft_year.value <= 1865):
            raise ModelFormatError(
                f"CivilWarDraftRecord draft_year must be between 1862 and 1865, "
                f"got {self.draft_year.value}."
            )

        if self.substitute_provided and not (
            self.substitute_individual_id
            or (self.substitute_name_raw and self.substitute_name_raw.strip())
        ):
            raise ModelFormatError(
                "CivilWarDraftRecord requires substitute_name_raw or substitute_individual_id "
                "when substitute_provided is True."
            )
