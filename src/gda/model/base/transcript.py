"""Path: src/gda/model/base/transcript.py

Full-text transcription and abstract representation using Pydantic dataclasses.

Operational Role:
    Defines the archival transcription envelope ('Transcript') capturing
    verbatim extractions, abstracts, legibility ratings, text quality grades,
    and associated audit metadata directly via composition.

Architecture:
    - TextQuality: Controlled enumeration for transcription accuracy.
    - Legibility: Controlled enumeration for physical record clarity.
    - Transcript: Pydantic dataclass validating transcription payloads.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.errors import ModelFormatError
from gda.core.introspectable import IntrospectableMixin
from gda.core.logging import GDALogger
from gda.model.atom.id import TranscriptID
from gda.model.base.audit import AuditStamp

__version__ = "1.0.0+build.3"

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
class Transcript(IntrospectableMixin):
    """Archival full-text transcription and abstract payload with direct audit composition."""

    transcript_id: TranscriptID
    verbatim_text: str
    audit: AuditStamp
    abstract: str | None = None
    keywords: list[str] = Field(default_factory=list)
    text_quality: TextQuality = TextQuality.VERBATIM
    legibility: Legibility = Legibility.CLEAR

    def __post_init__(self) -> None:
        if not self.verbatim_text.strip():
            err_msg = "Transcript verbatim_text cannot be empty."
            _logger.debug("Transcript verbatim_text validation failed")
            raise ModelFormatError(err_msg, details={"field": "verbatim_text"})

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
