"""Path: src/gda/model/base/transcript.py

Full-text transcription and abstract representation using Pydantic dataclasses.

Operational Role:
    Defines the archival transcription envelope ('Transcript') capturing
    verbatim extractions, abstracts, legibility ratings, text quality grades,
    and associated audit metadata directly via composition.

Architecture:
    - TextQuality, Legibility: Authoritatively imported from gda.core.enums.archival.
    - Transcript: Strict immutable Pydantic dataclass validating transcription payloads.
"""

from __future__ import annotations

import json
from dataclasses import replace
from typing import Any

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.enums.archival import Legibility, TextQuality
from gda.core.errors import ModelFormatError
from gda.core.introspectable import IntrospectableMixin
from gda.core.logging import GDALogger
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import TranscriptID
from gda.model.base.audit import AuditStamp

__version__ = "1.0.0+build.1"

__all__ = ["Legibility", "TextQuality", "Transcript"]

_logger = GDALogger(__name__)


@dataclass(repr=False, config=ConfigDict(frozen=True, extra="forbid", strict=True))
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

        if self.abstract is not None and not self.abstract.strip():
            raise ModelFormatError(
                "Transcript abstract cannot be blank if provided.",
                details={"field": "abstract"},
            )

        if any(not kw.strip() for kw in self.keywords):
            raise ModelFormatError(
                "Transcript keywords cannot contain empty or whitespace strings.",
                details={"field": "keywords"},
            )

        if len(self.keywords) != len(set(self.keywords)):
            raise ModelFormatError(
                "Duplicate keyword entries detected in Transcript keywords.",
                details={"field": "keywords"},
            )

    @property
    def word_count(self) -> int:
        """Return token word count of verbatim_text."""
        return len(self.verbatim_text.split())

    @classmethod
    def create(
        cls,
        transcript_id: TranscriptID | str,
        verbatim_text: str,
        audit: AuditStamp | None = None,
        abstract: str | None = None,
        keywords: list[str] | None = None,
        text_quality: TextQuality | str = TextQuality.VERBATIM,
        legibility: Legibility | str = Legibility.CLEAR,
    ) -> Transcript:
        """Factory constructor instantiating a validated Transcript."""
        resolved_id = (
            transcript_id
            if isinstance(transcript_id, TranscriptID)
            else TranscriptID(transcript_id)
        )
        if isinstance(text_quality, TextQuality):
            resolved_quality = text_quality
        elif isinstance(text_quality, str):
            try:
                resolved_quality = TextQuality(text_quality.strip().upper())
            except ValueError as exc:
                raise ModelFormatError(f"Invalid TextQuality value: '{text_quality}'.") from exc
        else:
            raise ModelFormatError(f"Invalid TextQuality type: {type(text_quality).__name__}.")

        if isinstance(legibility, Legibility):
            resolved_legibility = legibility
        elif isinstance(legibility, str):
            try:
                resolved_legibility = Legibility(legibility.strip().upper())
            except ValueError as exc:
                raise ModelFormatError(f"Invalid Legibility value: '{legibility}'.") from exc
        else:
            raise ModelFormatError(f"Invalid Legibility type: {type(legibility).__name__}.")

        resolved_audit = audit if audit is not None else AuditStamp.now()
        clean_abstract = abstract.strip() if abstract and abstract.strip() else None

        clean_keywords: list[str] = []
        if keywords:
            for kw in keywords:
                clean = kw.strip() if kw else ""
                if clean and clean not in clean_keywords:
                    clean_keywords.append(clean)

        return cls(
            transcript_id=resolved_id,
            verbatim_text=verbatim_text.strip()
            if isinstance(verbatim_text, str)
            else verbatim_text,
            audit=resolved_audit,
            abstract=clean_abstract,
            keywords=clean_keywords,
            text_quality=resolved_quality,
            legibility=resolved_legibility,
        )

    def update_text(self, verbatim_text: str, audit: AuditStamp | None = None) -> Transcript:
        """Return a new immutable copy with updated verbatim_text and refreshed audit."""
        clean = verbatim_text.strip() if isinstance(verbatim_text, str) else verbatim_text
        next_audit = audit if audit is not None else self.audit.touch()
        return replace(self, verbatim_text=clean, audit=next_audit)

    def update_abstract(self, abstract: str | None, audit: AuditStamp | None = None) -> Transcript:
        """Return a new immutable copy with updated abstract and refreshed audit."""
        clean = abstract.strip() if abstract and abstract.strip() else None
        if clean == self.abstract:
            return self
        next_audit = audit if audit is not None else self.audit.touch()
        return replace(self, abstract=clean, audit=next_audit)

    def to_dict(self) -> dict[str, Any]:
        """Serialize Transcript instance to a dictionary."""
        data: dict[str, Any] = {
            "transcript_id": str(self.transcript_id),
            "verbatim_text": self.verbatim_text,
            "keywords": list(self.keywords),
            "text_quality": self.text_quality.value,
            "legibility": self.legibility.value,
            "audit": {
                "created_at": str(self.audit.created_at),
                "updated_at": str(self.audit.updated_at),
            },
        }
        if self.abstract is not None:
            data["abstract"] = self.abstract
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Transcript:
        """Deserialize a dictionary payload into an immutable Transcript instance."""
        if not isinstance(data, dict):
            raise ModelFormatError("Transcript payload must be a dictionary.")

        required_keys = {"transcript_id", "verbatim_text", "audit"}
        missing_keys = required_keys - set(data.keys())
        if missing_keys:
            raise ModelFormatError(
                f"Missing required fields for Transcript: {sorted(missing_keys)}",
                details={"missing": sorted(missing_keys)},
            )

        audit_raw = data["audit"]
        if isinstance(audit_raw, AuditStamp):
            audit_stamp = audit_raw
        elif isinstance(audit_raw, dict):
            if "created_at" not in audit_raw or "updated_at" not in audit_raw:
                raise ModelFormatError("Audit dictionary missing created_at or updated_at.")
            audit_stamp = AuditStamp(
                created_at=IsoTimestamp(audit_raw["created_at"]),
                updated_at=IsoTimestamp(audit_raw["updated_at"]),
            )
        else:
            raise ModelFormatError(
                "Transcript audit must be an AuditStamp or valid dictionary payload."
            )

        return cls.create(
            transcript_id=data["transcript_id"],
            verbatim_text=data["verbatim_text"],
            audit=audit_stamp,
            abstract=data.get("abstract"),
            keywords=data.get("keywords"),
            text_quality=data.get("text_quality", TextQuality.VERBATIM),
            legibility=data.get("legibility", Legibility.CLEAR),
        )

    def to_json(self) -> str:
        """Serialize Transcript instance to a JSON formatted string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_json(cls, payload: str) -> Transcript:
        """Deserialize a JSON string directly into a Transcript instance."""
        try:
            data = json.loads(payload)
        except Exception as exc:
            raise ModelFormatError(f"Failed to parse Transcript JSON string: {exc}") from exc
        return cls.from_dict(data)

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
