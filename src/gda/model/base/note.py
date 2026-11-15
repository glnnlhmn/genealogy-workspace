"""Path: src/gda/model/base/note.py

Archival research note representation using Pydantic dataclasses.

Operational Role:
    Defines the discrete, immutable research note value object ('Note').
    Captures textual research memos, proof arguments, discrepancy debriefs,
    and associated archival sources anchored by NoteID and AuditStamp.

Architecture:
    - NoteType: Authoritatively imported from gda.core.enums.archival.
    - Note: Strict frozen Pydantic dataclass validating research note records.
"""

from __future__ import annotations

import json
from dataclasses import replace
from typing import Any

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.dates import utc_now_iso
from gda.core.enums.archival import NoteType
from gda.core.errors import ModelFormatError
from gda.core.introspectable import IntrospectableMixin
from gda.core.logging import GDALogger
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import NoteID, SourceID
from gda.model.base.audit import AuditStamp

__version__ = "1.0.0+build.1"

__all__ = ["Note"]

_logger = GDALogger(__name__)


@dataclass(repr=False, config=ConfigDict(frozen=True, extra="forbid", strict=True))
class Note(IntrospectableMixin):
    """Archival research note capturing categorized textual memos, titles, sources, and tags."""

    note_id: NoteID
    note_type: NoteType
    text: str
    audit: AuditStamp
    title: str | None = None
    sources: list[SourceID] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate string fields, non-empty memo text, and uniqueness invariants."""
        if not self.text.strip():
            err_msg = "Note text cannot be empty or whitespace."
            _logger.debug(
                "Note text validation failed",
                details={"note_id": str(self.note_id)},
            )
            raise ModelFormatError(err_msg, details={"note_id": str(self.note_id)})

        if self.title is not None and not self.title.strip():
            err_msg = "Note title cannot be blank if provided."
            _logger.debug(
                "Note title validation failed",
                details={"note_id": str(self.note_id)},
            )
            raise ModelFormatError(err_msg, details={"note_id": str(self.note_id)})

        if len(self.sources) != len(set(self.sources)):
            raise ModelFormatError(
                "Duplicate SourceID entries detected in Note sources.",
                details={"note_id": str(self.note_id)},
            )

        if any(not t.strip() for t in self.tags):
            raise ModelFormatError(
                "Note tags cannot contain empty or whitespace strings.",
                details={"note_id": str(self.note_id)},
            )

        if len(self.tags) != len(set(self.tags)):
            raise ModelFormatError(
                "Duplicate tag entries detected in Note tags.",
                details={"note_id": str(self.note_id)},
            )

    @property
    def value(self) -> str:
        """Expose canonical identifier string value for duck-typed ID extractors."""
        return self.note_id.value

    @classmethod
    def create(
        cls,
        note_id: NoteID | str,
        note_type: NoteType | str,
        text: str,
        audit: AuditStamp | None = None,
        title: str | None = None,
        sources: list[SourceID | str] | None = None,
        tags: list[str] | None = None,
    ) -> Note:
        """Factory method minting an initial Note instance with synchronized AuditStamp."""
        validated_note_id = note_id if isinstance(note_id, NoteID) else NoteID(note_id)
        if isinstance(note_type, NoteType):
            validated_note_type = note_type
        elif isinstance(note_type, str):
            try:
                validated_note_type = NoteType(note_type.strip().upper())
            except ValueError as exc:
                raise ModelFormatError(f"Invalid NoteType value: '{note_type}'.") from exc
        else:
            raise ModelFormatError(f"Invalid NoteType type: {type(note_type).__name__}.")

        if audit is not None:
            validated_audit = audit
        else:
            now_ts = IsoTimestamp(utc_now_iso())
            validated_audit = AuditStamp(created_at=now_ts, updated_at=now_ts)

        validated_sources: list[SourceID] = []
        if sources:
            for s in sources:
                sid = s if isinstance(s, SourceID) else SourceID(s)
                if sid not in validated_sources:
                    validated_sources.append(sid)

        validated_tags: list[str] = []
        if tags:
            for t in tags:
                clean = t.strip() if t else ""
                if clean and clean not in validated_tags:
                    validated_tags.append(clean)

        clean_title = title.strip() if title and title.strip() else None

        return cls(
            note_id=validated_note_id,
            note_type=validated_note_type,
            text=text.strip() if isinstance(text, str) else text,
            audit=validated_audit,
            title=clean_title,
            sources=validated_sources,
            tags=validated_tags,
        )

    def _touch_audit(self, audit: AuditStamp | None) -> AuditStamp:
        """Advance updated_at timestamp on the current audit stamp."""
        if audit is not None:
            return audit
        return self.audit.touch(IsoTimestamp(utc_now_iso()))

    def update_text(self, text: str, audit: AuditStamp | None = None) -> Note:
        """Return a new immutable Note instance with updated text and refreshed AuditStamp."""
        clean = text.strip() if isinstance(text, str) else text
        return replace(self, text=clean, audit=self._touch_audit(audit))

    def update_type(self, note_type: NoteType | str, audit: AuditStamp | None = None) -> Note:
        """Return a new immutable Note instance with updated NoteType and refreshed AuditStamp."""
        if isinstance(note_type, NoteType):
            validated_type = note_type
        elif isinstance(note_type, str):
            try:
                validated_type = NoteType(note_type.strip().upper())
            except ValueError as exc:
                raise ModelFormatError(f"Invalid NoteType value: '{note_type}'.") from exc
        else:
            raise ModelFormatError(f"Invalid NoteType type: {type(note_type).__name__}.")
        return replace(self, note_type=validated_type, audit=self._touch_audit(audit))

    def update_title(self, title: str | None, audit: AuditStamp | None = None) -> Note:
        """Return a new immutable Note instance with updated title and refreshed AuditStamp."""
        clean_title = title.strip() if title and title.strip() else None
        return replace(self, title=clean_title, audit=self._touch_audit(audit))

    def update_sources(
        self,
        sources: list[SourceID | str],
        audit: AuditStamp | None = None,
    ) -> Note:
        """Return a new immutable Note instance with replaced sources and refreshed AuditStamp."""
        validated_sources: list[SourceID] = []
        for s in sources:
            sid = s if isinstance(s, SourceID) else SourceID(s)
            if sid not in validated_sources:
                validated_sources.append(sid)
        return replace(self, sources=validated_sources, audit=self._touch_audit(audit))

    def add_source(self, source_id: SourceID | str, audit: AuditStamp | None = None) -> Note:
        """Return a new immutable Note instance appending a unique source."""
        validated_source = source_id if isinstance(source_id, SourceID) else SourceID(source_id)
        if validated_source in self.sources:
            return self
        return replace(
            self,
            sources=[*self.sources, validated_source],
            audit=self._touch_audit(audit),
        )

    def remove_source(self, source_id: SourceID | str, audit: AuditStamp | None = None) -> Note:
        """Return a new immutable Note instance with the specified source removed."""
        target_str = str(source_id)
        filtered = [s for s in self.sources if str(s) != target_str]
        if len(filtered) == len(self.sources):
            return self
        return replace(self, sources=filtered, audit=self._touch_audit(audit))

    def update_tags(self, tags: list[str], audit: AuditStamp | None = None) -> Note:
        """Return a new immutable Note instance with replaced tags and refreshed AuditStamp."""
        clean_tags: list[str] = []
        for t in tags:
            clean = t.strip() if t else ""
            if clean and clean not in clean_tags:
                clean_tags.append(clean)
        return replace(self, tags=clean_tags, audit=self._touch_audit(audit))

    def add_tag(self, tag: str, audit: AuditStamp | None = None) -> Note:
        """Return a new immutable Note instance appending a unique non-empty tag."""
        clean_tag = tag.strip() if isinstance(tag, str) else ""
        if not clean_tag:
            raise ModelFormatError("Note tag cannot be empty or whitespace.")
        if clean_tag in self.tags:
            return self
        return replace(self, tags=[*self.tags, clean_tag], audit=self._touch_audit(audit))

    def remove_tag(self, tag: str, audit: AuditStamp | None = None) -> Note:
        """Return a new immutable Note instance with the specified tag removed."""
        clean_tag = tag.strip() if isinstance(tag, str) else ""
        filtered = [t for t in self.tags if t != clean_tag]
        if len(filtered) == len(self.tags):
            return self
        return replace(self, tags=filtered, audit=self._touch_audit(audit))

    def to_dict(self) -> dict[str, Any]:
        """Serialize note instance to a JSON-compatible dictionary."""
        data: dict[str, Any] = {
            "note_id": str(self.note_id),
            "note_type": self.note_type.value,
            "text": self.text,
            "audit": {
                "created_at": str(self.audit.created_at),
                "updated_at": str(self.audit.updated_at),
            },
            "sources": [str(s) for s in self.sources],
            "tags": list(self.tags),
        }
        if self.title is not None:
            data["title"] = self.title
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Note:
        """Deserialize a dictionary payload into an immutable Note instance."""
        if not isinstance(data, dict):
            raise ModelFormatError("Note payload must be a dictionary.")

        required_keys = {"note_id", "note_type", "text", "audit"}
        missing_keys = required_keys - set(data.keys())
        if missing_keys:
            raise ModelFormatError(
                f"Missing required fields for Note: {sorted(missing_keys)}",
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
            raise ModelFormatError("Note audit must be an AuditStamp or valid dictionary payload.")

        return cls.create(
            note_id=data["note_id"],
            note_type=data["note_type"],
            text=data["text"],
            audit=audit_stamp,
            title=data.get("title"),
            sources=data.get("sources"),
            tags=data.get("tags"),
        )

    def to_json(self) -> str:
        """Serialize note instance to a JSON formatted string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_json(cls, payload: str) -> Note:
        """Deserialize a JSON string directly into a Note instance."""
        try:
            data = json.loads(payload)
        except Exception as exc:
            raise ModelFormatError(f"Failed to parse Note JSON string: {exc}") from exc
        return cls.from_dict(data)

    def __str__(self) -> str:
        if self.title:
            return f"[{self.note_type.value}] {self.title}: {self.text}"
        return f"[{self.note_type.value}] {self.text}"

    def __repr__(self) -> str:
        """Produce a canonical string representation."""
        return (
            f"Note(note_id={self.note_id!r}, note_type={self.note_type}, "
            f"text={self.text!r}, title={self.title!r}, sources={self.sources!r}, "
            f"tags={self.tags!r}, audit={self.audit!r})"
        )
