"""Path: src/gda/model/base/source.py

Canonical source composites, citation pointers, and archival metadata headers.

Operational Role:
    Defines foundational evidentiary document and citation structures across the archive:
    - SourceReference: Citation pointer attaching archival sources to facts and assertions.
    - RecordMetadata: Administrative header envelope linking source UUIDs, URNs, and repositories.
    - SourceRecord: Canonical composite representing a primary archival document.
"""

from __future__ import annotations

import json
from dataclasses import replace
from typing import Any, Self

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.errors import ModelFormatError
from gda.core.introspectable import IntrospectableMixin
from gda.core.logging import GDALogger
from gda.enums.sources import SourceRecordCategory
from gda.model.atom.id import MediaID, RepositoryID, SourceID
from gda.model.atom.scalar import ConfidenceScore, QuayScore
from gda.model.atom.urn import ArchivalURN, SourceURN
from gda.model.base.association import AssociatedIndividual
from gda.model.base.audit import AuditStamp
from gda.model.base.tombstone import Tombstone

__version__ = "1.0.0+build.4"

__all__ = ["RecordMetadata", "SourceRecord", "SourceReference"]

_logger = GDALogger(__name__)


@dataclass(config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True))
class SourceReference(IntrospectableMixin):
    """Archival source pointer attaching evidence to assertions."""

    citation_text: str = Field(..., description="Documentary citation or entry description.")
    source_id: SourceID | None = Field(default=None, description="Linked archival SourceID UUID.")
    page_or_side: str | None = Field(default=None, description="Physical folio, page, or side.")
    quay: QuayScore | None = Field(
        default=None, description="Genealogical evidentiary certainty score (0..3)."
    )
    confidence: ConfidenceScore | None = Field(
        default=None, description="Algorithmic confidence float (0.0..1.0)."
    )

    def __post_init__(self) -> None:
        """Enforce non-empty citation text."""
        clean_text = self.citation_text.strip()
        if not clean_text:
            err_msg = "SourceReference citation_text cannot be empty."
            _logger.debug("SourceReference validation failed: empty citation_text")
            raise ModelFormatError(err_msg, details={"field": "citation_text"})
        object.__setattr__(self, "citation_text", clean_text)

    @classmethod
    def create(
        cls,
        citation_text: str,
        source_id: SourceID | str | None = None,
        page_or_side: str | None = None,
        quay: QuayScore | int | None = None,
        confidence: ConfidenceScore | float | None = None,
    ) -> SourceReference:
        """Factory constructor instantiating a validated SourceReference."""
        resolved_sid = (
            source_id
            if (source_id is None or isinstance(source_id, SourceID))
            else SourceID(source_id)
        )
        resolved_quay = quay if (quay is None or isinstance(quay, QuayScore)) else QuayScore(quay)
        resolved_conf = (
            confidence
            if (confidence is None or isinstance(confidence, ConfidenceScore))
            else ConfidenceScore(confidence)
        )
        clean_page = page_or_side.strip() if page_or_side is not None else None
        return cls(
            citation_text=citation_text,
            source_id=resolved_sid,
            page_or_side=clean_page,
            quay=resolved_quay,
            confidence=resolved_conf,
        )

    def update_citation(self, citation_text: str) -> Self:
        """Return a new immutable copy with updated citation text."""
        clean_text = citation_text.strip()
        if not clean_text:
            raise ModelFormatError("SourceReference citation_text cannot be empty.")
        if clean_text == self.citation_text:
            return self
        return replace(self, citation_text=clean_text)

    def update_source_id(self, source_id: SourceID | str | None) -> Self:
        """Return a new immutable copy with updated source identifier."""
        resolved = (
            source_id
            if (source_id is None or isinstance(source_id, SourceID))
            else SourceID(source_id)
        )
        if resolved == self.source_id:
            return self
        return replace(self, source_id=resolved)

    def update_page_or_side(self, page_or_side: str | None) -> Self:
        """Return a new immutable copy with updated folio/page designation."""
        clean = page_or_side.strip() if page_or_side is not None else None
        if clean == self.page_or_side:
            return self
        return replace(self, page_or_side=clean)

    def update_quay(self, quay: QuayScore | int | None) -> Self:
        """Return a new immutable copy with updated QuayScore."""
        resolved = quay if (quay is None or isinstance(quay, QuayScore)) else QuayScore(quay)
        if resolved == self.quay:
            return self
        return replace(self, quay=resolved)

    def update_confidence(self, confidence: ConfidenceScore | float | None) -> Self:
        """Return a new immutable copy with updated confidence score."""
        resolved = (
            confidence
            if (confidence is None or isinstance(confidence, ConfidenceScore))
            else ConfidenceScore(confidence)
        )
        if resolved == self.confidence:
            return self
        return replace(self, confidence=resolved)

    def to_dict(self) -> dict[str, Any]:
        """Serialize SourceReference to a dictionary."""
        data: dict[str, Any] = {"citation_text": self.citation_text}
        if self.source_id is not None:
            data["source_id"] = str(self.source_id)
        if self.page_or_side is not None:
            data["page_or_side"] = self.page_or_side
        if self.quay is not None:
            data["quay"] = int(self.quay)
        if self.confidence is not None:
            data["confidence"] = float(self.confidence)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SourceReference:
        """Deserialize a dictionary payload into an immutable SourceReference."""
        if not isinstance(data, dict):
            raise ModelFormatError("SourceReference payload must be a dictionary.")
        text = data.get("citation_text")
        if not text:
            raise ModelFormatError("Missing required field 'citation_text' for SourceReference.")
        return cls.create(
            citation_text=str(text),
            source_id=data.get("source_id"),
            page_or_side=data.get("page_or_side"),
            quay=data.get("quay"),
            confidence=data.get("confidence"),
        )

    def to_json(self) -> str:
        """Serialize SourceReference to a JSON formatted string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_json(cls, payload: str) -> SourceReference:
        """Deserialize a JSON string directly into a SourceReference instance."""
        try:
            data = json.loads(payload)
        except Exception as exc:
            raise ModelFormatError(f"Failed to parse SourceReference JSON string: {exc}") from exc
        return cls.from_dict(data)

    def __str__(self) -> str:
        """Render concise string representation of the source reference."""
        if self.page_or_side:
            return f"{self.citation_text} (p. {self.page_or_side})"
        return self.citation_text

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(citation_text='{self.citation_text}', "
            f"source_id={self.source_id!r}, page_or_side={self.page_or_side!r}, "
            f"quay={self.quay!r}, confidence={self.confidence!r})"
        )


@dataclass(config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True))
class RecordMetadata(IntrospectableMixin):
    """Archival record header uniting surrogate UUID, semantic URN, and category."""

    source_id: SourceID = Field(..., description="Canonical surrogate UUIDv4 SourceID.")
    source_urn: str = Field(..., description="Resolvable semantic archival URN string.")
    record_category: str = Field(..., description="Archival category classification token.")
    record_type: str = Field(..., description="Specific archival record type designation.")
    repository_id: RepositoryID | None = Field(
        default=None, description="Custodial repository foreign key."
    )

    def __post_init__(self) -> None:
        """Validate non-empty strings across envelope header fields."""
        if not isinstance(self.source_id, SourceID):
            raise TypeError(
                f"RecordMetadata 'source_id' must be SourceID, got {type(self.source_id).__name__}."
            )

        for field_name, value in (
            ("source_urn", self.source_urn),
            ("record_category", self.record_category),
            ("record_type", self.record_type),
        ):
            if not value.strip():
                err_msg = f"RecordMetadata '{field_name}' cannot be empty."
                _logger.debug("RecordMetadata validation failed", details={"field": field_name})
                raise ModelFormatError(err_msg, details={"field": field_name})

    @classmethod
    def create(
        cls,
        source_id: SourceID | str,
        source_urn: str,
        record_category: str,
        record_type: str,
        repository_id: RepositoryID | str | None = None,
    ) -> RecordMetadata:
        """Factory constructor instantiating a validated RecordMetadata."""
        resolved_sid = source_id if isinstance(source_id, SourceID) else SourceID(source_id)
        resolved_rep = (
            repository_id
            if (repository_id is None or isinstance(repository_id, RepositoryID))
            else RepositoryID(repository_id)
        )
        return cls(
            source_id=resolved_sid,
            source_urn=source_urn.strip(),
            record_category=record_category.strip(),
            record_type=record_type.strip(),
            repository_id=resolved_rep,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize RecordMetadata to a dictionary."""
        data: dict[str, Any] = {
            "source_id": str(self.source_id),
            "source_urn": self.source_urn,
            "record_category": self.record_category,
            "record_type": self.record_type,
        }
        if self.repository_id is not None:
            data["repository_id"] = str(self.repository_id)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RecordMetadata:
        """Deserialize a dictionary payload into an immutable RecordMetadata."""
        if not isinstance(data, dict):
            raise ModelFormatError("RecordMetadata payload must be a dictionary.")
        sid = data.get("source_id")
        urn = data.get("source_urn")
        cat = data.get("record_category")
        rtype = data.get("record_type")
        if not all((sid, urn, cat, rtype)):
            raise ModelFormatError(
                "RecordMetadata requires source_id, source_urn, record_category, and record_type."
            )
        return cls.create(
            source_id=str(sid),
            source_urn=str(urn),
            record_category=str(cat),
            record_type=str(rtype),
            repository_id=data.get("repository_id"),
        )

    def to_json(self) -> str:
        """Serialize RecordMetadata to a JSON formatted string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_json(cls, payload: str) -> RecordMetadata:
        """Deserialize a JSON string directly into a RecordMetadata instance."""
        try:
            data = json.loads(payload)
        except Exception as exc:
            raise ModelFormatError(f"Failed to parse RecordMetadata JSON string: {exc}") from exc
        return cls.from_dict(data)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(source_id={self.source_id!r}, "
            f"source_urn='{self.source_urn}', record_category='{self.record_category}', "
            f"record_type='{self.record_type}', repository_id={self.repository_id!r})"
        )


@dataclass(config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True))
class SourceRecord(IntrospectableMixin):
    """Canonical composite representing an evidentiary source document."""

    source_id: SourceID = Field(..., description="Surrogate UUIDv4 SourceID.")
    source_urn: ArchivalURN = Field(..., description="ArchivalURN semantic identifier.")
    record_category: SourceRecordCategory = Field(
        ..., description="Authoritative source category enum."
    )
    description: str = Field(..., description="Detailed textual description or abstract.")
    repository_id: RepositoryID = Field(..., description="Custodial repository foreign key.")
    audit: AuditStamp = Field(..., description="Lifecycle audit stamps.")
    media_ids: list[MediaID] = Field(
        default_factory=list, description="Attached media identifier array."
    )
    associated_people: list[AssociatedIndividual] = Field(
        default_factory=list, description="Collateral person entries."
    )
    tombstone: Tombstone | None = Field(
        default=None, description="Soft-deprecation tombstone metadata."
    )

    def __post_init__(self) -> None:
        """Enforce composite invariants on string boundaries and strongly-typed references."""
        desc = self.description.strip()
        if not desc:
            raise ModelFormatError(
                "SourceRecord 'description' cannot be empty or whitespace-only.",
                details={"source_id": str(self.source_id)},
            )
        object.__setattr__(self, "description", desc)

        if not isinstance(self.source_urn, ArchivalURN):
            raise ModelFormatError(
                f"SourceRecord 'source_urn' must be an instance of ArchivalURN, "
                f"got {type(self.source_urn).__name__}."
            )

        if not isinstance(self.repository_id, RepositoryID):
            raise ModelFormatError(
                f"SourceRecord 'repository_id' must be an instance of RepositoryID, "
                f"got {type(self.repository_id).__name__}."
            )

    @property
    def is_deprecated(self) -> bool:
        """Return whether the record is soft-deprecated via an attached tombstone."""
        return self.tombstone.is_deprecated if self.tombstone is not None else False

    @property
    def media_count(self) -> int:
        """Return the count of attached media references."""
        return len(self.media_ids)

    @property
    def participant_count(self) -> int:
        """Return the count of collateral associated individuals."""
        return len(self.associated_people)

    @classmethod
    def create(
        cls,
        source_id: SourceID | str,
        source_urn: ArchivalURN | str,
        record_category: SourceRecordCategory | str,
        description: str,
        repository_id: RepositoryID | str,
        audit: AuditStamp,
        media_ids: list[MediaID | str] | None = None,
        associated_people: list[AssociatedIndividual] | None = None,
        tombstone: Tombstone | None = None,
    ) -> SourceRecord:
        """Factory constructor instantiating a validated SourceRecord."""
        resolved_sid = source_id if isinstance(source_id, SourceID) else SourceID(source_id)
        resolved_rep = (
            repository_id
            if isinstance(repository_id, RepositoryID)
            else RepositoryID(repository_id)
        )
        resolved_cat = (
            record_category
            if isinstance(record_category, SourceRecordCategory)
            else SourceRecordCategory(record_category)
        )
        resolved_urn = (
            source_urn if isinstance(source_urn, ArchivalURN) else SourceURN(str(source_urn))
        )
        resolved_media = [m if isinstance(m, MediaID) else MediaID(m) for m in (media_ids or [])]
        return cls(
            source_id=resolved_sid,
            source_urn=resolved_urn,
            record_category=resolved_cat,
            description=description,
            repository_id=resolved_rep,
            audit=audit,
            media_ids=resolved_media,
            associated_people=associated_people or [],
            tombstone=tombstone,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize SourceRecord to a dictionary."""
        data: dict[str, Any] = {
            "source_id": str(self.source_id),
            "source_urn": str(self.source_urn),
            "record_category": self.record_category.value,
            "description": self.description,
            "repository_id": str(self.repository_id),
            "audit": {
                "created_at": str(self.audit.created_at),
                "updated_at": str(self.audit.updated_at),
            },
            "media_ids": [str(m) for m in self.media_ids],
            "associated_people": [p.to_dict() for p in self.associated_people],
        }
        if self.tombstone is not None:
            data["tombstone"] = {
                "is_deprecated": self.tombstone.is_deprecated,
                "deprecated_at": str(self.tombstone.deprecated_at)
                if self.tombstone.deprecated_at
                else None,
                "superseded_by": str(self.tombstone.superseded_by)
                if self.tombstone.superseded_by
                else None,
            }
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SourceRecord:
        """Deserialize a dictionary payload into an immutable SourceRecord."""
        if not isinstance(data, dict):
            raise ModelFormatError("SourceRecord payload must be a dictionary.")

        sid = data.get("source_id")
        raw_urn = data.get("source_urn")
        cat = data.get("record_category")
        desc = data.get("description")
        rep = data.get("repository_id")
        audit_payload = data.get("audit")

        if not all((sid, raw_urn, cat, desc, rep, audit_payload)):
            raise ModelFormatError(
                "SourceRecord requires source_id, source_urn, record_category, description, repository_id, and audit."
            )

        from gda.model.atom.date import IsoTimestamp

        audit_obj = AuditStamp(
            created_at=IsoTimestamp(audit_payload["created_at"]),
            updated_at=IsoTimestamp(audit_payload["updated_at"]),
        )

        tombstone_payload = data.get("tombstone")
        tombstone_obj: Tombstone | None = None
        if isinstance(tombstone_payload, dict):
            tombstone_obj = Tombstone(
                is_deprecated=tombstone_payload.get("is_deprecated", False),
                deprecated_at=(
                    IsoTimestamp(tombstone_payload["deprecated_at"])
                    if tombstone_payload.get("deprecated_at")
                    else None
                ),
                superseded_by=tombstone_payload.get("superseded_by"),
            )

        return cls.create(
            source_id=str(sid),
            source_urn=str(raw_urn),
            record_category=str(cat),
            description=str(desc),
            repository_id=str(rep),
            audit=audit_obj,
            media_ids=data.get("media_ids", []),
            associated_people=[
                AssociatedIndividual.from_dict(p) for p in data.get("associated_people", [])
            ],
            tombstone=tombstone_obj,
        )

    def to_json(self) -> str:
        """Serialize SourceRecord to a JSON formatted string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_json(cls, payload: str) -> SourceRecord:
        """Deserialize a JSON string directly into a SourceRecord instance."""
        try:
            data = json.loads(payload)
        except Exception as exc:
            raise ModelFormatError(f"Failed to parse SourceRecord JSON string: {exc}") from exc
        return cls.from_dict(data)

    def __str__(self) -> str:
        return f"SourceRecord [{self.record_category.value}] {self.source_urn} ({self.source_id})"
