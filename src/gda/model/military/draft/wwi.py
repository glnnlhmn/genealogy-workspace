"""Path: src/gda/model/military/draft/wwi.py

World War I military draft registration card domain entity model.

Operational Role:
    Extends MilitaryDraftRecord for the 1917-1918 US draft registrations (First,
    Second, and Third waves). Enforces card format invariants, marital status,
    citizenship classifications, and physical description registrar extracts.
"""

from __future__ import annotations

from enum import StrEnum
from typing import ClassVar

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.errors import ModelFormatError
from gda.model.military.draft.base import DraftCardTier, MilitaryDraftRecord

__version__ = "1.0.0+build.1"

__all__ = ["WwiCitizenshipStatus", "WwiDraftCardRecord", "WwiPhysicalDescription"]


class WwiCitizenshipStatus(StrEnum):
    """Controlled classification of citizenship declared on WWI registration cards."""

    NATIVE_BORN = "NATIVE_BORN"
    NATURALIZED_CITIZEN = "NATURALIZED_CITIZEN"
    ALIEN_DECLARED = "ALIEN_DECLARED"  # Declarant (First Papers filed)
    NON_DECLARANT = "NON_DECLARANT"
    UNKNOWN = "UNKNOWN"


@dataclass(
    config=ConfigDict(
        kw_only=True, frozen=True, extra="forbid", str_strip_whitespace=True
    )
)
class WwiPhysicalDescription:
    """Registrar's physical description recorded on the reverse of the WWI card."""

    height_description: str | None = Field(
        default=None,
        description="Recorded stature: 'Short', 'Medium', or 'Tall'.",
    )
    build_description: str | None = Field(
        default=None,
        description="Recorded frame: 'Slender', 'Medium', or 'Stout'.",
    )
    eye_color: str | None = Field(
        default=None,
        description="Recorded eye color (e.g., 'Blue', 'Brown', 'Gray', 'Hazel').",
    )
    hair_color: str | None = Field(
        default=None,
        description="Recorded hair color (e.g., 'Dark', 'Light', 'Brown', 'Auburn').",
    )
    baldness: bool = Field(
        default=False,
        description="Whether registrar marked the subject as bald.",
    )
    physical_disqualifications: str | None = Field(
        default=None,
        description="Verbatim remarks on physical disabilities, loss of limb, or sight.",
    )


@dataclass(
    config=ConfigDict(
        kw_only=True, frozen=True, extra="forbid", str_strip_whitespace=True
    )
)
class WwiDraftCardRecord(MilitaryDraftRecord):
    """Specialized evidentiary record for WWI Draft Registration Cards (1917-1918)."""

    citizenship: WwiCitizenshipStatus = Field(
        default=WwiCitizenshipStatus.UNKNOWN,
        description="Citizenship or alienage declaration recorded on front of card.",
    )
    occupation_verbatim: str | None = Field(
        default=None,
        description="Transcribed trade, profession, or occupation.",
    )
    employer_verbatim: str | None = Field(
        default=None,
        description="Transcribed employer or business firm name.",
    )
    employer_location_raw: str | None = Field(
        default=None,
        description="Place of employment or business address recorded.",
    )
    nearest_relative_raw: str | None = Field(
        default=None,
        description="Nearest relative or dependent name and address (Waves 2 and 3).",
    )
    father_birthplace_raw: str | None = Field(
        default=None,
        description="Father's recorded birthplace (Wave 2 cards only).",
    )
    claim_exemption: bool = Field(
        default=False,
        description="Whether exemption from military service was formally claimed.",
    )
    exemption_grounds_raw: str | None = Field(
        default=None,
        description="Transcribed reason or grounds for claiming draft exemption.",
    )
    physical_description: WwiPhysicalDescription | None = Field(
        default=None,
        description="Registrar's observation report on reverse of card.",
    )

    VALID_TIERS: ClassVar[set[DraftCardTier]] = {
        DraftCardTier.WWI_FIRST,
        DraftCardTier.WWI_SECOND,
        DraftCardTier.WWI_THIRD,
    }

    def __post_init__(self) -> None:
        """Enforce WWI tier restrictions and registration year boundaries."""
        super().__post_init__()

        if self.card_tier not in self.VALID_TIERS:
            raise ModelFormatError(
                f"WwiDraftCardRecord requires card_tier in {[t.value for t in self.VALID_TIERS]}, "
                f"got '{self.card_tier.value}'."
            )

        if self.draft_year.value not in {1917, 1918}:
            raise ModelFormatError(
                f"WwiDraftCardRecord draft_year must be 1917 or 1918, got {self.draft_year.value}."
            )
