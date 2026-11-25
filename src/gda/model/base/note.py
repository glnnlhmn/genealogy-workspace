"""Path: src/gda/model/base/note.py

Embedded research note value object for entities and archival records.

Operational Role:
    Defines the immutable Note value object encapsulating categorized research
    commentary, proof arguments, and discrepancy observations with supporting
    SourceID citations, searchable tags, and AuditStamp lifecycle tracking.
"""

from __future__ import annotations

import json
from dataclasses import replace
from typing import Any

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.dates import utc_now_iso
from gda.core.enums import coerce_enum
from gda.core.enums.archival import NoteType
from gda.core.errors import ModelFormatError
from gda.core.introspectable import IntrospectableMixin
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import NoteID, SourceID
from gda.model.base.audit import AuditStamp
from gda.util.text import clean_unique_strings

__version__ = "1.0.0+build.5"

__all__ = [
    "Note",
]


def _coerce_note_type(value: NoteType | str) -> NoteType:
    """Resolve a NoteType enum member or string token."""
    if not isinstance(value, (NoteType, str)):
        raise ModelFormatError(
            f"Invalid NoteType type: expected NoteType or str, got {type(value).__name__}.",
            error_code="ERR_MODEL_FORMAT",
        )
    try:
        return coerce_enum(NoteType, value, field_name="note_type")
    except ModelFormatError as err:
        raise ModelFormatError(
            f"Invalid NoteType value: '{value}'.",
            error_code="ERR_MODEL_FORMAT",
            details={"note_type": str(value)},
        ) from err


def _deduplicate_sources(sources: list[SourceID | str] | None) -> list[SourceID]:
    """Coerce and deduplicate a list of SourceID or UUID string references in order."""
    if not sources:
        return []
    seen: set[SourceID] = set()
    result: list[SourceID] = []
    for item in sources:
        sid = item if isinstance(item, SourceID) else SourceID(str(item).strip())
        if sid not in seen:
            seen.add(sid)
            result.append(sid)
    return result


@dataclass(repr=False, config=ConfigDict(frozen=True, extra="forbid", strict=True))
class Note(IntrospectableMixin):
    """Immutable embedded research note value object."""

    note_id: NoteID = Field(..., description="Canonical NoteID (NOT-######).")
    note_type: NoteType = Field(..., description="Classification of the research note.")
    text: str = Field(..., description="Primary body text of the research note.")
    audit: AuditStamp = Field(..., description="Creation and modification timestamps.")
    title: str | None = Field(default=None, description="Optional concise note title.")
    sources: list[SourceID] = Field(
        default_factory=list,
        description="Supporting documentary SourceID references.",
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Normalized search and classification tags.",
    )

    def __post_init__(self) -> None:
        """Enforce non-empty text, non-blank optional title, and unique sources/tags."""
        if not self.text or not self.text.strip():
            raise ModelFormatError("Note text cannot be empty or whitespace.")
        if self.title is not None and not self.title.strip():
            raise ModelFormatError("Note title cannot be blank if provided.")

        seen_sources: set[SourceID] = set()
        for src in self.sources:
            if src in seen_sources:
                raise ModelFormatError(f"Duplicate SourceID entries detected: '{src}'.")
            seen_sources.add(src)

        seen_tags: set[str] = set()
        for tag in self.tags:
            if not tag or not tag.strip():
                raise ModelFormatError("Note tags cannot contain empty or whitespace strings.")
            if tag in seen_tags:
                raise ModelFormatError(f"Duplicate tag entries detected: '{tag}'.")
            seen_tags.add(tag)

    @property
    def value(self) -> str:
        """Expose underlying NoteID string value for uniform ID unwrapping."""
        return self.note_id.value

    @classmethod
    def create(
        cls,
        note_id: NoteID | str,
        text: str,
        note_type: NoteType | str = NoteType.GENERAL,
        *,
        audit: AuditStamp | None = None,
        title: str | None = None,
        sources: list[SourceID | str] | None = None,
        tags: list[str] | None = None,
    ) -> Note:
        """Factory constructor normalizing fields, deduplicating lists, and minting AuditStamp."""
        resolved_id = note_id if isinstance(note_id, NoteID) else NoteID(str(note_id).strip())
        resolved_type = _coerce_note_type(note_type)
        clean_text = text.strip() if isinstance(text, str) else ""
        clean_title = title.strip() if isinstance(title, str) and title.strip() else None
        resolved_audit = audit if audit is not None else AuditStamp.now()

        return cls(
            note_id=resolved_id,
            note_type=resolved_type,
            text=clean_text,
            audit=resolved_audit,
            title=clean_title,
            sources=_deduplicate_sources(sources),
            tags=clean_unique_strings(tags),
        )

    def _touch_audit(self, audit: AuditStamp | None) -> AuditStamp:
        """Return explicit audit override or touch current audit stamp."""
        if audit is not None:
            return audit
        return self.audit.touch(IsoTimestamp(utc_now_iso()))

    def update_text(self, text: str, *, audit: AuditStamp | None = None) -> Note:
        """Return a copy with updated note body text and touched audit."""
        clean = text.strip()
        return replace(self, text=clean, audit=self._touch_audit(audit))

    def update_type(self, note_type: NoteType | str, *, audit: AuditStamp | None = None) -> Note:
        """Return a copy with updated NoteType and touched audit."""
        resolved = _coerce_note_type(note_type)
        return replace(self, note_type=resolved, audit=self._touch_audit(audit))

    def update_title(self, title: str | None, *, audit: AuditStamp | None = None) -> Note:
        """Return a copy with updated or cleared title and touched audit."""
        clean = title.strip() if isinstance(title, str) and title.strip() else None
        return replace(self, title=clean, audit=self._touch_audit(audit))

    def update_sources(
        self,
        sources: list[SourceID | str],
        *,
        audit: AuditStamp | None = None,
    ) -> Note:
        """Replace the note's supporting sources list with deduplicated SourceIDs."""
        return replace(
            self,
            sources=_deduplicate_sources(sources),
            audit=self._touch_audit(audit),
        )

    def add_source(self, source_id: SourceID | str, *, audit: AuditStamp | None = None) -> Note:
        """Append a supporting SourceID if not already present."""
        sid = source_id if isinstance(source_id, SourceID) else SourceID(str(source_id).strip())
        if sid in self.sources:
            return self
        return replace(
            self,
            sources=[*self.sources, sid],
            audit=self._touch_audit(audit),
        )

    def remove_source(self, source_id: SourceID | str, *, audit: AuditStamp | None = None) -> Note:
        """Remove a supporting SourceID if present."""
        target_str = str(source_id).strip()
        filtered = [s for s in self.sources if s.value != target_str]
        if len(filtered) == len(self.sources):
            return self
        return replace(self, sources=filtered, audit=self._touch_audit(audit))

    def update_tags(self, tags: list[str], *, audit: AuditStamp | None = None) -> Note:
        """Replace the note's tags with a cleaned, deduplicated tag list."""
        return replace(
            self,
            tags=clean_unique_strings(tags),
            audit=self._touch_audit(audit),
        )

    def add_tag(self, tag: str, *, audit: AuditStamp | None = None) -> Note:
        """Append a tag if not already present."""
        clean = tag.strip() if isinstance(tag, str) else ""
        if not clean:
            raise ModelFormatError("Note tag cannot be empty or whitespace.")
        if clean in self.tags:
            return self
        return replace(self, tags=[*self.tags, clean], audit=self._touch_audit(audit))

    def remove_tag(self, tag: str, *, audit: AuditStamp | None = None) -> Note:
        """Remove a tag if present."""
        clean = tag.strip()
        if clean not in self.tags:
            return self
        return replace(
            self,
            tags=[t for t in self.tags if t != clean],
            audit=self._touch_audit(audit),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize Note to a dictionary."""
        return {
            "note_id": self.note_id.value,
            "note_type": self.note_type.value,
            "text": self.text,
            "title": self.title,
            "sources": [s.value for s in self.sources],
            "tags": list(self.tags),
            "audit": self.audit.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Note:
        """Rehydrate Note from a dictionary."""
        if not isinstance(data, dict):
            raise ModelFormatError("Note payload must be a dictionary.")

        required = {"note_id", "note_type", "text", "audit"}
        missing = required - set(data.keys())
        if missing:
            raise ModelFormatError(f"Missing required fields for Note: {sorted(missing)}")

        raw_audit = data["audit"]
        if isinstance(raw_audit, AuditStamp):
            resolved_audit = raw_audit
        elif isinstance(raw_audit, dict):
            if "created_at" not in raw_audit or "updated_at" not in raw_audit:
                raise ModelFormatError("Audit dictionary missing created_at or updated_at.")
            resolved_audit = AuditStamp.from_dict(raw_audit)
        else:
            raise ModelFormatError("Note audit must be an AuditStamp or dictionary.")

        return cls.create(
            note_id=data["note_id"],
            note_type=data["note_type"],
            text=data["text"],
            audit=resolved_audit,
            title=data.get("title"),
            sources=data.get("sources"),
            tags=data.get("tags"),
        )

    def to_json(self) -> str:
        """Serialize Note to a deterministic JSON string."""
        return json.dumps(self.to_dict(), sort_keys=True)

    @classmethod
    def from_json(cls, json_str: str) -> Note:
        """Deserialize Note from a JSON string."""
        try:
            payload = json.loads(json_str)
        except Exception as exc:
            raise ModelFormatError(f"Failed to parse Note JSON string: {exc}") from exc
        return cls.from_dict(payload)

    def __str__(self) -> str:
        if self.title:
            return f"[{self.note_type.value}] {self.title}: {self.text}"
        return f"[{self.note_type.value}] {self.text}"

    def __repr__(self) -> str:
        return (
            f"Note(note_id={self.note_id!r}, note_type={self.note_type!r}, "
            f"title={self.title!r}, text={self.text!r})"
        )
