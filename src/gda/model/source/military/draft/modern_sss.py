"""Path: src/gda/model/source/military/draft/modern_sss.py

Post-WWII and modern Selective Service System (SSS) draft registration model.

Operational Role:
    Extends MilitaryDraftRecord for the Selective Service Act of 1948, Korean War,
    Vietnam War draft lottery eras, and post-1980 continuous registration mandates.
    Enforces lottery sequence numbers, SSS numbers, and classification status.
"""

from __future__ import annotations

from typing import ClassVar

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.enums.military import DraftCardTier, ModernDraftEra, SssClassification
from gda.core.errors import ModelFormatError
from gda.core.types import (
    MAX_VIETNAM_LOTTERY_NUMBER,
    MIN_VIETNAM_LOTTERY_NUMBER,
    MODERN_SSS_MIN_YEAR,
)
from gda.model.source.military.draft.base import MilitaryDraftRecord

__version__ = "1.0.0+build.2"

__all__ = ["ModernDraftEra", "ModernSelectiveServiceRecord", "SssClassification"]


@dataclass(
    repr=False,
    config=ConfigDict(frozen=True, extra="forbid", strict=True),
    kw_only=True,
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
        ge=MIN_VIETNAM_LOTTERY_NUMBER,
        le=MAX_VIETNAM_LOTTERY_NUMBER,
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

    VALID_TIERS: ClassVar[frozenset[DraftCardTier]] = frozenset({DraftCardTier.OTHER})

    def __post_init__(self) -> None:
        """Enforce modern Selective Service registration year boundaries."""
        super().__post_init__()

        if self.draft_year.value < MODERN_SSS_MIN_YEAR:
            raise ModelFormatError(
                f"ModernSelectiveServiceRecord draft_year must be {MODERN_SSS_MIN_YEAR} or later, "
                f"got {self.draft_year.value}."
            )

        if (
            self.lottery_sequence_number is not None
            and self.draft_era != ModernDraftEra.VIETNAM_LOTTERY
        ):
            raise ModelFormatError(
                "lottery_sequence_number is only applicable during the VIETNAM_LOTTERY era."
            )
