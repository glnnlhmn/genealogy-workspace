"""Path: src/gda/model/military/draft/modern_sss.py

Post-WWII and modern Selective Service System (SSS) draft registration model.

Operational Role:
    Extends MilitaryDraftRecord for the Selective Service Act of 1948, Korean War,
    Vietnam War draft lottery eras, and post-1980 continuous registration mandates.
    Enforces lottery sequence numbers, SSS numbers, and classification status.
"""

from __future__ import annotations

from enum import StrEnum
from typing import ClassVar

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.errors import ModelFormatError
from gda.model.military.draft.base import DraftCardTier, MilitaryDraftRecord

__version__ = "1.0.0+build.1"

__all__ = ["ModernDraftEra", "ModernSelectiveServiceRecord", "SssClassification"]


class ModernDraftEra(StrEnum):
    """Statutory draft administration era under modern Selective Service."""

    POST_WWII_1948 = "POST_WWII_1948"  # Selective Service Act of 1948
    KOREAN_WAR = "KOREAN_WAR"  # 1950-1953
    VIETNAM_LOTTERY = "VIETNAM_LOTTERY"  # 1969-1975 (Lottery Drawings)
    POST_1980_REGISTRATION = (
        "POST_1980_REGISTRATION"  # July 1980 onward (Proclamation 4771)
    )


class SssClassification(StrEnum):
    """Selective service board classification designation."""

    ONE_A = "1-A"  # Available for unrestricted military service
    ONE_A_O = (
        "1-A-O"  # Conscientious objector available for noncombatant military service
    )
    ONE_O = "1-O"  # Conscientious objector available for civilian alternate service
    ONE_D = "1-D"  # Member of reserve component or student in ROTC
    TWO_S = "2-S"  # Student deferment
    THREE_A = "3-A"  # Extreme hardship deferment to dependents
    FOUR_F = (
        "4-F"  # Registrant unqualified for military service (physical/mental/moral)
    )
    UNCLASSIFIED = "UNCLASSIFIED"


@dataclass(
    config=ConfigDict(
        kw_only=True, frozen=True, extra="forbid", str_strip_whitespace=True
    )
)
class ModernSelectiveServiceRecord(MilitaryDraftRecord):
    """Evidentiary draft record under the modern Selective Service System (1948-present)."""

    draft_era: ModernDraftEra = Field(
        ...,
        description="Historical Selective Service administration era.",
    )
    sss_number_raw: str | None = Field(
        default=None,
        description="Selective Service Number formatted as State-Board-Year-Sequence (e.g. 27-4-52-101).",
    )
    lottery_sequence_number: int | None = Field(
        default=None,
        ge=1,
        le=366,
        description="Vietnam era random draft sequence number (1-366).",
    )
    classification: SssClassification = Field(
        default=SssClassification.UNCLASSIFIED,
        description="Local board military readiness classification.",
    )
    classification_date_raw: str | None = Field(
        default=None,
        description="Date action taken by the local board on classification.",
    )

    VALID_TIERS: ClassVar[set[DraftCardTier]] = {DraftCardTier.OTHER}

    def __post_init__(self) -> None:
        """Enforce modern Selective Service registration year boundaries."""
        super().__post_init__()

        if self.draft_year.value < 1948:
            raise ModelFormatError(
                f"ModernSelectiveServiceRecord draft_year must be 1948 or later, "
                f"got {self.draft_year.value}."
            )

        if (
            self.lottery_sequence_number is not None
            and self.draft_era != ModernDraftEra.VIETNAM_LOTTERY
        ):
            raise ModelFormatError(
                "lottery_sequence_number is only applicable during the VIETNAM_LOTTERY era."
            )
