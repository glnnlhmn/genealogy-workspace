# Name: transcript.py
# Path: src/gda/model/base/transcript.py

"""Full-text transcription and abstract model using Pydantic dataclasses.

Operational Role:
    Defines the archival transcription envelope ('TranscriptModel') capturing
    verbatim extractions, abstracts, legibility ratings, text quality grades,
    and associated audit metadata. Identified by a UUIDv4 TranscriptID.

Architecture:
    - TextQuality: Controlled enumeration for transcription accuracy.
    - Legibility: Controlled enumeration for physical record clarity.
    - TranscriptModel: Pydantic dataclass validating transcription payloads.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.logging import GDALogger
from gda.model.atom.errors import AtomFormatError
from gda.model.atom.id import TranscriptID
from gda.model.base.auditable import AuditableModel

__version__ = "1.0.0+build.r2"

_logger = GDALogger(__name__)


class TextQuality(StrEnum):
    """Controlled classification of transcription accuracy."""

    VERBATIM = "VERBATIM"
    PARTIAL = "PARTIAL"
    ABSTRACT = "ABSTRACT"
    DAMAGED = "DAMAGED"
    ILLEGIBLE = "ILLEGIBLE"


class Legibility(StrEnum):
    """Controlled classification of primary document legibility."""

    CLEAR = "CLEAR"
    FADED = "FADED"
    TORN = "TORN"
    STAINED = "STAINED"
    POOR_HANDWRITING = "POOR_HANDWRITING"
    PARTIALLY_ILLEGIBLE = "PARTIALLY_ILLEGIBLE"
    ILLEGIBLE = "ILLEGIBLE"


@dataclass(config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True))
class TranscriptModel(AuditableModel):
    """Archival full-text transcription and abstract payload."""

    transcript_id: TranscriptID
    verbatim_text: str
    abstract: str | None = None
    keywords: list[str] = Field(default_factory=list)
    text_quality: TextQuality = TextQuality.VERBATIM
    legibility: Legibility = Legibility.CLEAR

    def __post_init__(self) -> None:
        if not self.verbatim_text.strip():
            err_msg = "TranscriptModel verbatim_text cannot be empty."
            _logger.debug("TranscriptModel verbatim_text validation failed")
            raise AtomFormatError(err_msg, details={"field": "verbatim_text"})

    @property
    def word_count(self) -> int:
        return len(self.verbatim_text.split())

    def __str__(self) -> str:
        if len(self.verbatim_text) > 60:
            return f"{self.verbatim_text[:57]}..."
        return self.verbatim_text

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(transcript_id={self.transcript_id!r}, "
            f"words={self.word_count}, quality={self.text_quality}, "
            f"legibility={self.legibility}, audit={self.audit!r})"
        )
