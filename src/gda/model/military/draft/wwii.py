"""Path: src/gda/model/military/draft/wwii.py

World War II military draft registration card domain entity model.

Operational Role:
    Extends MilitaryDraftRecord for the 1940-1946 Selective Training and Service Act
    draft waves, including the 4th Registration ('Old Man's Draft'). Captures
    contact persons, telephone numbers, race, and physical metrics.
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

__all__ = ["WwiiDraftCardRecord", "WwiiDraftWave", "WwiiPhysicalMetrics"]


class WwiiDraftWave(StrEnum):
    """Selective Training and Service Act registration waves."""

    FIRST = "FIRST"  # Oct 16, 1940 (Ages 21-35)
    SECOND = "SECOND"  # July 1, 1941 (Age 21 attained)
    THIRD = "THIRD"  # Feb 16, 1942 (Ages 20-21, 35-44)
    FOURTH_OLD_MANS = "FOURTH_OLD_MANS"  # April 27, 1942 (Ages 45-64, not liable for military service)
    FIFTH = "FIFTH"  # June 30, 1942 (Ages 18-20)
    SIXTH = "SIXTH"  # Dec 1942 (Age 18 ongoing)


@dataclass(
    config=ConfigDict(
        kw_only=True, frozen=True, extra="forbid", str_strip_whitespace=True
    )
)
class WwiiPhysicalMetrics:
    """Physical description reported by the registrar on WWII Form 1/DSS Form 1."""

    race_verbatim: str | None = Field(
        default=None,
        description="Recorded race: White, Negro, Oriental, Indian, Filipino.",
    )
    height_inches: int | None = Field(
        default=None,
        ge=36,
        le=96,
        description="Recorded approximate height in total inches.",
    )
    weight_lbs: int | None = Field(
        default=None,
        ge=50,
        le=500,
        description="Recorded approximate weight in pounds.",
    )
    complexion: str | None = Field(
        default=None,
        description="Complexion description (e.g., Sallow, Light, Ruddy, Dark, Freckled).",
    )
    eye_color: str | None = Field(
        default=None,
        description="Recorded eye color.",
    )
    hair_color: str | None = Field(
        default=None,
        description="Recorded hair color.",
    )
    other_physical_characteristics: str | None = Field(
        default=None,
        description="Scars, tattoos, amputations, or identifying marks.",
    )


@dataclass(
    config=ConfigDict(
        kw_only=True, frozen=True, extra="forbid", str_strip_whitespace=True
    )
)
class WwiiDraftCardRecord(MilitaryDraftRecord):
    """Specialized evidentiary record for WWII Selective Service Draft Cards (1940-1946)."""

    draft_wave: WwiiDraftWave = Field(
        ...,
        description="Historical Selective Training and Service Act registration wave.",
    )
    serial_number: str | None = Field(
        default=None,
        description="Draft lottery serial number assigned by the local board.",
    )
    order_number: str | None = Field(
        default=None,
        description="Master draft lottery call order number.",
    )
    telephone_number_raw: str | None = Field(
        default=None,
        description="Registrant's telephone number as recorded on card.",
    )
    employer_name_raw: str | None = Field(
        default=None,
        description="Transcribed employer or business enterprise name.",
    )
    employer_address_raw: str | None = Field(
        default=None,
        description="Transcribed employer address or business location.",
    )
    contact_person_name_raw: str | None = Field(
        default=None,
        description="Name of person who will always know registrant's address.",
    )
    contact_person_relationship: str | None = Field(
        default=None,
        description="Relationship of contact person (e.g., Wife, Mother, Employer).",
    )
    contact_person_id: IndividualID | None = Field(
        default=None,
        description="Resolved IndividualID of the contact person if known.",
    )
    physical_metrics: WwiiPhysicalMetrics | None = Field(
        default=None,
        description="Registrar's physical description metrics from card reverse.",
    )

    VALID_YEARS: ClassVar[set[int]] = {1940, 1941, 1942, 1943, 1944, 1945, 1946}

    def __post_init__(self) -> None:
        """Enforce WWII wave consistency, tier constraints, and registration years."""
        super().__post_init__()

        if self.draft_year.value not in self.VALID_YEARS:
            raise ModelFormatError(
                f"WwiiDraftCardRecord draft_year must be between 1940 and 1946, "
                f"got {self.draft_year.value}."
            )

        if (
            self.draft_wave == WwiiDraftWave.FOURTH_OLD_MANS
            and self.card_tier != DraftCardTier.WWII_FOURTH
        ):
            raise ModelFormatError(
                "WwiiDraftCardRecord with FOURTH_OLD_MANS wave must specify card_tier WWII_FOURTH."
            )
