"""Path: src/gda/model/base/transcript.py

Archival text transcription and abstract composite value object.

Operational Role:
    Defines the immutable Transcript dataclass capturing verbatim documentary
    transcriptions, optional research abstracts, searchable keywords, text
    completeness quality, and handwriting/print legibility assessments.
"""

from __future__ import annotations

import json
from dataclasses import replace
from typing import Any

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.dates import utc_now_iso
from gda.core.enums.archival import Legibility, TextQuality
from gda.core.errors import ModelFormatError
from gda.core.introspectable import IntrospectableMixin
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import TranscriptID
from gda.model.base.audit import AuditStamp
from gda.util.enums import coerce_enum
from gda.util.text import clean_unique_strings

__version__ = "1.0.0+build.4"

__all__ = [
    "Legibility",
    "TextQuality",
    "Transcript",
]


def _coerce_text_quality(value: TextQuality | str) -> TextQuality:
    """Resolve a TextQuality enum member or string token."""
    if not isinstance(value, (TextQuality, str)):
        raise ModelFormatError(
            f"Invalid TextQuality type: expected TextQuality or str, got {type(value).__name__}.",
            error_code="ERR_MODEL_FORMAT",
        )
    try:
        return coerce_enum(TextQuality, value, field_name="text_quality")
    except ModelFormatError as err:
        raise ModelFormatError(
            f"Invalid TextQuality value: '{value}'.",
            error_code="ERR_MODEL_FORMAT",
            details={"text_quality": str(value)},
        ) from err


def _coerce_legibility(value: Legibility | str) -> Legibility:
    """Resolve a Legibility enum member or string token."""
    if not isinstance(value, (Legibility, str)):
        raise ModelFormatError(
            f"Invalid Legibility type: expected Legibility or str, got {type(value).__name__}.",
            error_code="ERR_MODEL_FORMAT",
        )
    try:
        return coerce_enum(Legibility, value, field_name="legibility")
    except ModelFormatError as err:
        raise ModelFormatError(
            f"Invalid Legibility value: '{value}'.",
            error_code="ERR_MODEL_FORMAT",
            details={"legibility": str(value)},
        ) from err


@dataclass(repr=False, config=ConfigDict(frozen=True, extra="forbid", strict=True))
class Transcript(IntrospectableMixin):
    """Immutable archival transcription and abstract value object."""

    transcript_id: TranscriptID = Field(..., description="Canonical UUIDv4 TranscriptID.")
    verbatim_text: str = Field(..., description="Exact verbatim transcription text.")
    audit: AuditStamp = Field(..., description="Creation and modification timestamps.")
    abstract: str | None = Field(default=None, description="Optional concise research abstract.")
    keywords: list[str] = Field(
        default_factory=list,
        description="Searchable subject or surname keywords.",
    )
    text_quality: TextQuality = Field(
        default=TextQuality.VERBATIM,
        description="Completeness tier of the transcription.",
    )
    legibility: Legibility = Field(
        default=Legibility.CLEAR,
        description="Physical legibility of the underlying source script.",
    )

    def __post_init__(self) -> None:
        """Enforce non-empty verbatim_text, non-blank abstract, and unique keywords."""
        if not self.verbatim_text or not self.verbatim_text.strip():
            raise ModelFormatError("Transcript verbatim_text cannot be empty or whitespace.")
        if self.abstract is not None and not self.abstract.strip():
            raise ModelFormatError("Transcript abstract cannot be blank if provided.")

        seen_kw: set[str] = set()
        for kw in self.keywords:
            if not kw or not kw.strip():
                raise ModelFormatError("Transcript keywords cannot contain empty strings.")
            if kw in seen_kw:
                raise ModelFormatError(f"Duplicate keyword entries detected: '{kw}'.")
            seen_kw.add(kw)

    @property
    def word_count(self) -> int:
        """Return total whitespace-delimited word count of verbatim_text."""
        return len(self.verbatim_text.split())

    @classmethod
    def create(
        cls,
        transcript_id: TranscriptID | str,
        verbatim_text: str,
        *,
        audit: AuditStamp | None = None,
        abstract: str | None = None,
        keywords: list[str] | None = None,
        text_quality: TextQuality | str = TextQuality.VERBATIM,
        legibility: Legibility | str = Legibility.CLEAR,
    ) -> Transcript:
        """Factory constructor normalizing strings, deduplicating keywords, and coercing enums."""
        resolved_id = (
            transcript_id
            if isinstance(transcript_id, TranscriptID)
            else TranscriptID(str(transcript_id).strip())
        )
        clean_text = verbatim_text.strip() if isinstance(verbatim_text, str) else ""
        clean_abs = abstract.strip() if isinstance(abstract, str) and abstract.strip() else None
        resolved_audit = audit if audit is not None else AuditStamp.now()

        return cls(
            transcript_id=resolved_id,
            verbatim_text=clean_text,
            audit=resolved_audit,
            abstract=clean_abs,
            keywords=clean_unique_strings(keywords),
            text_quality=_coerce_text_quality(text_quality),
            legibility=_coerce_legibility(legibility),
        )

    def update_text(self, verbatim_text: str) -> Transcript:
        """Return a copy with updated verbatim_text and touched audit."""
        clean = verbatim_text.strip()
        return replace(
            self,
            verbatim_text=clean,
            audit=self.audit.touch(IsoTimestamp(utc_now_iso())),
        )

    def update_abstract(self, abstract: str | None) -> Transcript:
        """Return a copy with updated or cleared abstract and touched audit."""
        clean = abstract.strip() if isinstance(abstract, str) and abstract.strip() else None
        if clean == self.abstract:
            return self
        return replace(
            self,
            abstract=clean,
            audit=self.audit.touch(IsoTimestamp(utc_now_iso())),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize Transcript to a dictionary."""
        data: dict[str, Any] = {
            "transcript_id": self.transcript_id.value,
            "verbatim_text": self.verbatim_text,
            "keywords": list(self.keywords),
            "text_quality": self.text_quality.value,
            "legibility": self.legibility.value,
            "audit": self.audit.to_dict(),
        }
        if self.abstract is not None:
            data["abstract"] = self.abstract
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Transcript:
        """Rehydrate Transcript from a dictionary."""
        if not isinstance(data, dict):
            raise ModelFormatError("Transcript payload must be a dictionary.")

        required = {"transcript_id", "verbatim_text", "audit"}
        missing = required - set(data.keys())
        if missing:
            raise ModelFormatError(f"Missing required fields for Transcript: {sorted(missing)}")

        raw_audit = data["audit"]
        if isinstance(raw_audit, AuditStamp):
            resolved_audit = raw_audit
        elif isinstance(raw_audit, dict):
            if "created_at" not in raw_audit or "updated_at" not in raw_audit:
                raise ModelFormatError("Audit dictionary missing created_at or updated_at.")
            resolved_audit = AuditStamp.from_dict(raw_audit)
        else:
            raise ModelFormatError("Transcript audit must be an AuditStamp or dictionary.")

        return cls.create(
            transcript_id=data["transcript_id"],
            verbatim_text=data["verbatim_text"],
            audit=resolved_audit,
            abstract=data.get("abstract"),
            keywords=data.get("keywords"),
            text_quality=data.get("text_quality", TextQuality.VERBATIM),
            legibility=data.get("legibility", Legibility.CLEAR),
        )

    def to_json(self) -> str:
        """Serialize Transcript to a deterministic JSON string."""
        return json.dumps(self.to_dict(), sort_keys=True)

    @classmethod
    def from_json(cls, json_str: str) -> Transcript:
        """Deserialize Transcript from a JSON string."""
        try:
            payload = json.loads(json_str)
        except Exception as exc:
            raise ModelFormatError(f"Failed to parse Transcript JSON string: {exc}") from exc
        return cls.from_dict(payload)

    def __str__(self) -> str:
        if len(self.verbatim_text) > 60:
            return f"{self.verbatim_text[:57]}..."
        return self.verbatim_text

    def __repr__(self) -> str:
        return (
            f"Transcript(transcript_id={self.transcript_id!r}, "
            f"text_quality={self.text_quality!r}, legibility={self.legibility!r}, "
            f"word_count={self.word_count})"
        )
