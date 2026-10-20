"""Path: src/gda/model/military/awards/base.py

Military awards, decorations, citations, and campaign medal entity records.

Operational Role:
    Extends SourceRecord composite to represent military awards, valor decorations
    (Medal of Honor, Silver Star, Purple Heart), campaign medals, commendation ribbons,
    General Orders, citation narratives, and posthumous awards.
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
from gda.model.military.awards import (
    AwardScope,
    MilitaryAwardTier,
)
from gda.model.military.service import MilitaryBranch

__version__ = "1.0.0+build.1"

__all__ = ["MilitaryAwardRecord"]


@dataclass(
    config=ConfigDict(
        kw_only=True, frozen=True, extra="forbid", str_strip_whitespace=True
    )
)
class MilitaryAwardRecord(SourceRecord):
    """Evidentiary military medal, decoration, or citation award record."""

    recipient_id: IndividualID = Field(
        ...,
        description="Canonical IndividualID of the awarded servicemember.",
    )
    recipient_name_raw: str = Field(
        ...,
        description="Verbatim transcribed name of the award recipient from citation/roll.",
    )
    award_name_raw: str = Field(
        ...,
        description="Verbatim official name of the award, medal, or decoration.",
    )
    branch: MilitaryBranch = Field(
        ...,
        description="Armed branch under which the action or service was performed.",
    )
    award_tier: MilitaryAwardTier = Field(
        ...,
        description="Precedence or tier classification of the decoration.",
    )
    award_scope: AwardScope = Field(
        ...,
        description="Scope or criteria governing the award (VALOR, MERIT, CAMPAIGN, SERVICE).",
    )
    award_year: HistoricalYear = Field(
        ...,
        description="Calendar year the award was authorized, announced, or presented.",
    )
    action_year: HistoricalYear | None = Field(
        default=None,
        description="Calendar year of the heroic deed, engagement, or qualifying service.",
    )
    general_order_raw: str | None = Field(
        default=None,
        description="Verbatim General Order, Department of Defense, or Executive Order number.",
    )
    issuing_authority_raw: str | None = Field(
        default=None,
        description="Verbatim command headquarters or official issuing the decoration.",
    )
    is_posthumous: bool = Field(
        default=False,
        description="Flag indicating the award was conferred posthumously.",
    )
    action_location_raw: str | None = Field(
        default=None,
        description="Verbatim geographical location of the qualifying action or engagement.",
    )
    action_location_id: LocationID | None = Field(
        default=None,
        description="Resolved civil jurisdiction LocationID of the qualifying action.",
    )
    transcript_id: TranscriptID | None = Field(
        default=None,
        description="Decoupled TranscriptID linking full verbatim citation narrative text.",
    )

    EXPECTED_CATEGORY: ClassVar[SourceRecordCategory] = SourceRecordCategory.MILITARY

    def __post_init__(self) -> None:
        """Enforce domain category, text sanitization, and chronological order."""
        super().__post_init__()

        if self.record_category != self.EXPECTED_CATEGORY:
            raise ModelFormatError(
                f"MilitaryAwardRecord requires category '{self.EXPECTED_CATEGORY.value}', "
                f"got '{self.record_category.value}'."
            )

        name = self.recipient_name_raw.strip()
        if not name:
            raise ModelFormatError(
                "MilitaryAwardRecord 'recipient_name_raw' cannot be empty or whitespace."
            )
        object.__setattr__(self, "recipient_name_raw", name)

        award = self.award_name_raw.strip()
        if not award:
            raise ModelFormatError(
                "MilitaryAwardRecord 'award_name_raw' cannot be empty or whitespace."
            )
        object.__setattr__(self, "award_name_raw", award)

        if self.action_year is not None:
            if self.award_year.value < self.action_year.value:
                raise ModelFormatError(
                    f"award_year ({self.award_year.value}) cannot precede "
                    f"action_year ({self.action_year.value})."
                )

        if self.general_order_raw is not None:
            go = self.general_order_raw.strip()
            if not go:
                raise ModelFormatError(
                    "MilitaryAwardRecord 'general_order_raw' cannot be empty or whitespace."
                )
            object.__setattr__(self, "general_order_raw", go)

        if self.issuing_authority_raw is not None:
            auth = self.issuing_authority_raw.strip()
            if not auth:
                raise ModelFormatError(
                    "MilitaryAwardRecord 'issuing_authority_raw' cannot be empty or whitespace."
                )
            object.__setattr__(self, "issuing_authority_raw", auth)

        if self.action_location_raw is not None:
            loc = self.action_location_raw.strip()
            if not loc:
                raise ModelFormatError(
                    "MilitaryAwardRecord 'action_location_raw' cannot be empty or whitespace."
                )
            object.__setattr__(self, "action_location_raw", loc)

    def __str__(self) -> str:
        post = " (Posthumous)" if self.is_posthumous else ""
        return (
            f"MilitaryAwardRecord [{self.award_tier.value}] {self.award_name_raw}{post} -> "
            f"{self.recipient_name_raw} ({self.award_year.value})"
        )
