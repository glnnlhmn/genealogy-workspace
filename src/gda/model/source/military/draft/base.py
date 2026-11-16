"""Path: src/gda/model/source/military/draft/base.py

Domain entity model representing military conscription registration records.

Operational Role:
    Extends SourceRecord composite to represent WWI, WWII, colonial, Civil War,
    and modern draft registration cards. Enforces registration round boundaries,
    board jurisdiction capture, raw-versus-resolved name preservation, and
    transcript asset decoupling.
"""

from __future__ import annotations

from typing import ClassVar

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.enums.military import DraftCardTier
from gda.core.enums.sources import SourceRecordCategory
from gda.core.errors import ModelFormatError
from gda.model.atom.id import DraftRecordID, IndividualID, LocationID, TranscriptID
from gda.model.atom.urn import MilitaryDraftUrn
from gda.model.atom.year import HistoricalYear
from gda.model.base.source import SourceRecord

__version__ = "1.0.0+build.1"

__all__ = ["DraftCardTier", "MilitaryDraftRecord"]


@dataclass(
    repr=False,
    config=ConfigDict(kw_only=True, frozen=True, extra="forbid", strict=True),
)
class MilitaryDraftRecord(SourceRecord):
    """Evidentiary draft registration card record across historical eras."""

    draft_record_id: DraftRecordID = Field(
        ...,
        description="Canonical military draft record identifier (DRF-######).",
    )
    registrant_id: IndividualID = Field(
        ...,
        description="Canonical IndividualID of the registered person.",
    )
    registrant_name_raw: str = Field(
        ...,
        description="Verbatim transcribed name of the registrant as written on the card.",
    )
    draft_year: HistoricalYear = Field(
        ...,
        description="Discrete calendar year of registration (e.g., 1917, 1918, 1942).",
    )
    board_jurisdiction_raw: str = Field(
        ...,
        description="Verbatim text of the local draft board or exemption district.",
    )
    card_tier: DraftCardTier = Field(
        default=DraftCardTier.OTHER,
        description="Specific draft registration wave or card format tier.",
    )
    board_location_id: LocationID | None = Field(
        default=None,
        description="Optional resolved civil jurisdiction LocationID for the board.",
    )
    transcript_id: TranscriptID | None = Field(
        default=None,
        description="Decoupled TranscriptID linking the verbatim card transcription.",
    )

    EXPECTED_CATEGORY: ClassVar[SourceRecordCategory] = SourceRecordCategory.MILITARY

    def __post_init__(self) -> None:
        """Enforce domain constraints, raw-string hygiene, and URN specialization."""
        super().__post_init__()

        if self.record_category != self.EXPECTED_CATEGORY:
            raise ModelFormatError(
                f"MilitaryDraftRecord requires category '{self.EXPECTED_CATEGORY.value}', "
                f"got '{self.record_category.value}'."
            )

        if not isinstance(self.source_urn, MilitaryDraftUrn):
            raise ModelFormatError(
                f"MilitaryDraftRecord 'source_urn' must be a MilitaryDraftUrn, "
                f"got {type(self.source_urn).__name__}."
            )

        raw_name = self.registrant_name_raw.strip()
        if not raw_name:
            raise ModelFormatError(
                "MilitaryDraftRecord 'registrant_name_raw' cannot be empty or whitespace.",
                details={"draft_record_id": str(self.draft_record_id)},
            )
        if raw_name != self.registrant_name_raw:
            object.__setattr__(self, "registrant_name_raw", raw_name)

        board_raw = self.board_jurisdiction_raw.strip()
        if not board_raw:
            raise ModelFormatError(
                "MilitaryDraftRecord 'board_jurisdiction_raw' cannot be empty or whitespace.",
                details={"draft_record_id": str(self.draft_record_id)},
            )
        if board_raw != self.board_jurisdiction_raw:
            object.__setattr__(self, "board_jurisdiction_raw", board_raw)

    def __str__(self) -> str:
        return (
            f"MilitaryDraftRecord [{self.card_tier.value}] {self.registrant_name_raw} "
            f"({self.draft_year}) - {self.source_urn}"
        )

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(draft_record_id={self.draft_record_id!r}, "
            f"registrant_id={self.registrant_id!r}, draft_year={self.draft_year!r}, "
            f"card_tier={self.card_tier!r})"
        )
