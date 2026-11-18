"""Path: src/gda/model/base/source.py

Foundational documentary source citations, metadata headers, and base record models.

Operational Role:
    Defines SourceReference (evidentiary citation pointers with Quay certainty
    and confidence scoring), RecordMetadata (cataloging header envelopes), and
    SourceRecord (the kw_only=True base dataclass inherited by all 32 concrete
    documentary source models across the 12 archival domains).
"""

from __future__ import annotations

import dataclasses
import json
import sys
from dataclasses import replace
from enum import Enum
from typing import Any, Self

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.enums.sources import SourceRecordCategory
from gda.core.errors import ModelFormatError
from gda.core.introspectable import IntrospectableMixin
from gda.model.atom.id import AtomID, MediaID, RepositoryID, SourceID, UUIDv4Str
from gda.model.atom.scalar import ConfidenceScore, QuayScore
from gda.model.atom.urn import (
    ArchivalURN,
    CemeteryPlotUrn,
    CensusUrn,
    MilitaryDraftUrn,
    SourceURN,
    VitalCertificateUrn,
)
from gda.model.atom.year import HistoricalYear
from gda.model.base.association import AssociatedIndividual
from gda.model.base.audit import AuditStamp
from gda.model.base.tombstone import Tombstone
from gda.util.enums import coerce_enum

__version__ = "1.0.0+build.9"

__all__ = [
    "RecordMetadata",
    "SourceRecord",
    "SourceReference",
]

_BASE_SOURCE_RECORD_FIELDS: frozenset[str] = frozenset(
    {
        "source_id",
        "source_urn",
        "record_category",
        "description",
        "repository_id",
        "audit",
        "media_ids",
        "associated_people",
        "tombstone",
    }
)

_NID_TO_URN_CLASS: dict[str, type[ArchivalURN]] = {
    "SRC": SourceURN,
    "DRAFT": MilitaryDraftUrn,
    "CENSUS": CensusUrn,
    "VITAL": VitalCertificateUrn,
    "CEM": CemeteryPlotUrn,
}


def _coerce_source_record_category(
    value: SourceRecordCategory | str,
) -> SourceRecordCategory:
    """Resolve a SourceRecordCategory enum member or string token."""
    if not isinstance(value, (SourceRecordCategory, str)):
        raise ModelFormatError(
            f"Invalid SourceRecordCategory type: expected SourceRecordCategory or str, got {type(value).__name__}.",
            error_code="ERR_MODEL_FORMAT",
        )
    try:
        return coerce_enum(SourceRecordCategory, value, field_name="record_category")
    except ModelFormatError as err:
        raise ModelFormatError(
            f"Invalid SourceRecordCategory value: '{value}'.",
            error_code="ERR_MODEL_FORMAT",
            details={"record_category": str(value)},
        ) from err


def _resolve_archival_urn(value: ArchivalURN | str) -> ArchivalURN:
    """Resolve an ArchivalURN instance or raw URN string into its specific URN subclass."""
    if isinstance(value, ArchivalURN):
        return value
    clean = value.strip()
    parts = clean.split(":")
    urn_cls = _NID_TO_URN_CLASS.get(parts[1]) if len(parts) >= 2 else None
    if urn_cls is not None:
        return urn_cls(clean)
    return ArchivalURN(clean)


def _serialize_dataclass_instance(val: Any) -> dict[str, Any]:
    """Serialize a nested dataclass instance by omitting None and empty collections."""
    out: dict[str, Any] = {}
    for f in dataclasses.fields(val):
        sub_val = getattr(val, f.name)
        if sub_val is not None and not (isinstance(sub_val, (list, tuple)) and len(sub_val) == 0):
            out[f.name] = _serialize_subclass_field(sub_val)
    return out


def _serialize_subclass_field(val: Any) -> Any:
    """Recursively serialize a subclass-specific field value into JSON-compatible primitives."""
    if hasattr(val, "to_dict") and callable(val.to_dict):
        return val.to_dict()
    if isinstance(val, Enum):
        return val.value
    if hasattr(val, "value") and not isinstance(val, (str, bytes, dict, list, tuple)):
        return val.value
    if dataclasses.is_dataclass(val) and not isinstance(val, type):
        return _serialize_dataclass_instance(val)
    if isinstance(val, (list, tuple)):
        return [_serialize_subclass_field(item) for item in val]
    return val


def _resolve_field_type(cls: type[Any], type_str: str) -> type[Any] | None:
    """Resolve a stringified type annotation within the defining class module's namespace."""
    base_token = type_str.split("|")[0].strip()
    for mro_cls in cls.__mro__:
        mod = sys.modules.get(mro_cls.__module__)
        if mod is not None and hasattr(mod, base_token):
            return getattr(mod, base_token)
    return None


def _coerce_subclass_field(cls: type[Any], type_str: str, raw_val: Any) -> Any:
    """Coerce a raw dictionary value into the target annotated type for a SourceRecord subclass."""
    if raw_val is None:
        return None

    target_cls = _resolve_field_type(cls, type_str)
    if target_cls is None or isinstance(raw_val, target_cls):
        return raw_val

    if isinstance(raw_val, dict) and dataclasses.is_dataclass(target_cls):
        sub_kwargs = {
            sf.name: _coerce_subclass_field(target_cls, str(sf.type), raw_val[sf.name])
            for sf in dataclasses.fields(target_cls)
            if sf.name in raw_val
        }
        return target_cls(**sub_kwargs)

    if issubclass(target_cls, Enum):
        return coerce_enum(target_cls, raw_val)

    if issubclass(
        target_cls,
        (AtomID, UUIDv4Str, ArchivalURN, HistoricalYear, QuayScore, ConfidenceScore),
    ):
        return target_cls(raw_val)

    return raw_val


def _deduplicate_media_ids(media_ids: list[MediaID | str] | None) -> list[MediaID]:
    """Coerce and deduplicate a list of MediaID or UUID string references."""
    resolved_media: list[MediaID] = []
    seen_mid: set[MediaID] = set()
    for item in media_ids or []:
        mid = item if isinstance(item, MediaID) else MediaID(str(item).strip())
        if mid not in seen_mid:
            seen_mid.add(mid)
            resolved_media.append(mid)
    return resolved_media


# ==============================================================================
# SECTION 1: EVIDENTIARY SOURCE REFERENCE CITATION (SourceReference)
# ==============================================================================


@dataclass(repr=False, config=ConfigDict(frozen=True, extra="forbid", strict=True))
class SourceReference(IntrospectableMixin):
    """Evidentiary citation reference linking assertions to documentary sources."""

    citation_text: str = Field(..., description="Formatted bibliographic or archival citation.")
    source_id: SourceID | None = Field(
        default=None,
        description="Optional UUIDv4 identifier of the backing SourceRecord.",
    )
    page_or_side: str | None = Field(
        default=None,
        description="Optional page, folio, sheet, or image side locator.",
    )
    quay: QuayScore | None = Field(
        default=None,
        description="Optional GEDCOM Quay evidentiary certainty score (0-3).",
    )
    confidence: ConfidenceScore | None = Field(
        default=None,
        description="Optional normalized confidence score (0.0-1.0).",
    )

    def __post_init__(self) -> None:
        """Enforce non-empty citation_text and non-blank page_or_side."""
        if not self.citation_text or not self.citation_text.strip():
            raise ModelFormatError("SourceReference citation_text cannot be empty or whitespace.")
        if self.page_or_side is not None and not self.page_or_side.strip():
            raise ModelFormatError("SourceReference page_or_side cannot be blank if provided.")

    @classmethod
    def create(
        cls,
        citation_text: str,
        *,
        source_id: SourceID | str | None = None,
        page_or_side: str | None = None,
        quay: QuayScore | int | None = None,
        confidence: ConfidenceScore | float | None = None,
    ) -> SourceReference:
        """Factory constructor normalizing strings and wrapping optional atoms."""
        clean_cite = citation_text.strip() if isinstance(citation_text, str) else ""
        if not clean_cite:
            raise ModelFormatError("SourceReference citation_text cannot be empty or whitespace.")

        base = cls(citation_text=clean_cite)
        return (
            base.update_source_id(source_id)
            .update_page_or_side(page_or_side)
            .update_quay(quay)
            .update_confidence(confidence)
        )

    def update_citation(self, citation_text: str) -> SourceReference:
        """Return a copy with updated citation_text."""
        clean = citation_text.strip()
        if not clean:
            raise ModelFormatError("SourceReference citation_text cannot be empty or whitespace.")
        if clean == self.citation_text:
            return self
        return replace(self, citation_text=clean)

    def update_source_id(self, source_id: SourceID | str | None) -> SourceReference:
        """Return a copy with updated or cleared source_id."""
        resolved = (
            source_id
            if isinstance(source_id, SourceID) or source_id is None
            else SourceID(str(source_id).strip())
        )
        if resolved == self.source_id:
            return self
        return replace(self, source_id=resolved)

    def update_page_or_side(self, page_or_side: str | None) -> SourceReference:
        """Return a copy with updated or cleared page_or_side."""
        clean = (
            page_or_side.strip() if isinstance(page_or_side, str) and page_or_side.strip() else None
        )
        if clean == self.page_or_side:
            return self
        return replace(self, page_or_side=clean)

    def update_quay(self, quay: QuayScore | int | None) -> SourceReference:
        """Return a copy with updated or cleared QuayScore."""
        resolved = quay if isinstance(quay, QuayScore) or quay is None else QuayScore(int(quay))
        if resolved == self.quay:
            return self
        return replace(self, quay=resolved)

    def update_confidence(self, confidence: ConfidenceScore | float | None) -> SourceReference:
        """Return a copy with updated or cleared ConfidenceScore."""
        resolved = (
            confidence
            if isinstance(confidence, ConfidenceScore) or confidence is None
            else ConfidenceScore(float(confidence))
        )
        if resolved == self.confidence:
            return self
        return replace(self, confidence=resolved)

    def to_dict(self) -> dict[str, Any]:
        """Serialize SourceReference to a dictionary, omitting None fields."""
        data: dict[str, Any] = {"citation_text": self.citation_text}
        if self.source_id is not None:
            data["source_id"] = self.source_id.value
        if self.page_or_side is not None:
            data["page_or_side"] = self.page_or_side
        if self.quay is not None:
            data["quay"] = self.quay.value
        if self.confidence is not None:
            data["confidence"] = self.confidence.value
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SourceReference:
        """Rehydrate SourceReference from a dictionary."""
        if not isinstance(data, dict):
            raise ModelFormatError("SourceReference payload must be a dictionary.")
        if "citation_text" not in data:
            raise ModelFormatError("Missing required field 'citation_text' in SourceReference.")

        return cls.create(
            citation_text=data["citation_text"],
            source_id=data.get("source_id"),
            page_or_side=data.get("page_or_side"),
            quay=data.get("quay"),
            confidence=data.get("confidence"),
        )

    def to_json(self) -> str:
        """Serialize SourceReference to a deterministic JSON string."""
        return json.dumps(self.to_dict(), sort_keys=True)

    @classmethod
    def from_json(cls, json_str: str) -> SourceReference:
        """Deserialize SourceReference from a JSON string."""
        try:
            payload = json.loads(json_str)
        except Exception as exc:
            raise ModelFormatError(f"Failed to parse SourceReference JSON string: {exc}") from exc
        return cls.from_dict(payload)

    def __str__(self) -> str:
        if self.page_or_side:
            return f"{self.citation_text} (p. {self.page_or_side})"
        return self.citation_text

    def __repr__(self) -> str:
        return (
            f"SourceReference(citation_text={self.citation_text!r}, "
            f"source_id={self.source_id!r}, page_or_side={self.page_or_side!r})"
        )


# ==============================================================================
# SECTION 2: RECORD CATALOGING METADATA HEADER (RecordMetadata)
# ==============================================================================


@dataclass(repr=False, config=ConfigDict(frozen=True, extra="forbid", strict=True))
class RecordMetadata(IntrospectableMixin):
    """Cataloging header envelope for documentary source records."""

    source_id: SourceID = Field(..., description="Canonical UUIDv4 SourceID.")
    source_urn: str = Field(..., description="Archival URN string.")
    record_category: str = Field(..., description="Top-level archival category token.")
    record_type: str = Field(..., description="Specific documentary record type token.")
    repository_id: RepositoryID | None = Field(
        default=None,
        description="Optional holding RepositoryID (REP-######).",
    )

    def __post_init__(self) -> None:
        """Enforce non-empty string tokens across URN, category, and type."""
        for label, val in (
            ("source_urn", self.source_urn),
            ("record_category", self.record_category),
            ("record_type", self.record_type),
        ):
            if not val or not val.strip():
                raise ModelFormatError(f"RecordMetadata '{label}' cannot be empty or whitespace.")

    @classmethod
    def create(
        cls,
        source_id: SourceID | str,
        source_urn: str,
        record_category: str,
        record_type: str,
        *,
        repository_id: RepositoryID | str | None = None,
    ) -> RecordMetadata:
        """Factory constructor normalizing tokens and wrapping IDs."""
        resolved_sid = (
            source_id if isinstance(source_id, SourceID) else SourceID(str(source_id).strip())
        )
        resolved_repo = (
            repository_id
            if isinstance(repository_id, RepositoryID) or repository_id is None
            else RepositoryID(str(repository_id).strip())
        )
        return cls(
            source_id=resolved_sid,
            source_urn=source_urn.strip(),
            record_category=record_category.strip(),
            record_type=record_type.strip(),
            repository_id=resolved_repo,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize RecordMetadata to a dictionary."""
        data: dict[str, Any] = {
            "source_id": self.source_id.value,
            "source_urn": self.source_urn,
            "record_category": self.record_category,
            "record_type": self.record_type,
        }
        if self.repository_id is not None:
            data["repository_id"] = self.repository_id.value
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RecordMetadata:
        """Rehydrate RecordMetadata from a dictionary."""
        if not isinstance(data, dict):
            raise ModelFormatError("RecordMetadata payload must be a dictionary.")

        required = {"source_id", "source_urn", "record_category", "record_type"}
        if not required.issubset(data.keys()):
            raise ModelFormatError(
                "RecordMetadata payload requires source_id, source_urn, record_category, and record_type."
            )

        return cls.create(
            source_id=data["source_id"],
            source_urn=data["source_urn"],
            record_category=data["record_category"],
            record_type=data["record_type"],
            repository_id=data.get("repository_id"),
        )

    def to_json(self) -> str:
        """Serialize RecordMetadata to a deterministic JSON string."""
        return json.dumps(self.to_dict(), sort_keys=True)

    @classmethod
    def from_json(cls, json_str: str) -> RecordMetadata:
        """Deserialize RecordMetadata from a JSON string."""
        try:
            payload = json.loads(json_str)
        except Exception as exc:
            raise ModelFormatError(f"Failed to parse RecordMetadata JSON string: {exc}") from exc
        return cls.from_dict(payload)

    def __str__(self) -> str:
        return f"RecordMetadata [{self.record_category}/{self.record_type}] {self.source_urn}"

    def __repr__(self) -> str:
        return (
            f"RecordMetadata(source_id={self.source_id!r}, source_urn={self.source_urn!r}, "
            f"record_category={self.record_category!r}, record_type={self.record_type!r})"
        )


# ==============================================================================
# SECTION 3: FOUNDATIONAL DOCUMENTARY SOURCE RECORD (SourceRecord)
# ==============================================================================


@dataclass(
    repr=False,
    config=ConfigDict(frozen=True, extra="forbid", strict=True),
    kw_only=True,
)
class SourceRecord(IntrospectableMixin):
    """Foundational documentary source record base class across all 12 archival domains."""

    source_id: SourceID = Field(..., description="Canonical UUIDv4 SourceID.")
    source_urn: ArchivalURN = Field(..., description="Validated domain-specific ArchivalURN.")
    record_category: SourceRecordCategory = Field(
        ...,
        description="High-level documentary archival category.",
    )
    description: str = Field(..., description="Concise archival description of the source.")
    repository_id: RepositoryID = Field(..., description="Holding RepositoryID (REP-######).")
    audit: AuditStamp = Field(..., description="Record creation and modification timestamps.")
    media_ids: list[MediaID] = Field(
        default_factory=list,
        description="Attached digital scan or image MediaIDs.",
    )
    associated_people: list[AssociatedIndividual] = Field(
        default_factory=list,
        description="Secondary witnesses, informants, or officials named in the record.",
    )
    tombstone: Tombstone[SourceID] | None = Field(
        default=None,
        description="Optional deprecation and supersession state.",
    )

    def __post_init__(self) -> None:
        """Enforce non-empty description and unique media_ids."""
        if not self.description or not self.description.strip():
            raise ModelFormatError("SourceRecord description cannot be empty or whitespace.")

        seen_media: set[MediaID] = set()
        for mid in self.media_ids:
            if mid in seen_media:
                raise ModelFormatError(f"Duplicate MediaID in SourceRecord: '{mid}'.")
            seen_media.add(mid)

    @property
    def is_deprecated(self) -> bool:
        """Return True if tombstone is present and marked deprecated."""
        return bool(self.tombstone and self.tombstone.is_deprecated)

    @property
    def media_count(self) -> int:
        """Return count of attached digital MediaIDs."""
        return len(self.media_ids)

    @property
    def participant_count(self) -> int:
        """Return count of associated individuals."""
        return len(self.associated_people)

    @classmethod
    def _normalize_base_kwargs(
        cls,
        *,
        source_id: SourceID | str,
        source_urn: ArchivalURN | str,
        record_category: SourceRecordCategory | str,
        description: str,
        repository_id: RepositoryID | str,
        audit: AuditStamp | None = None,
        media_ids: list[MediaID | str] | None = None,
        associated_people: list[AssociatedIndividual | dict[str, Any]] | None = None,
        tombstone: Tombstone[SourceID] | dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Normalize and validate base SourceRecord parameters for .create() factories."""
        resolved_sid = (
            source_id if isinstance(source_id, SourceID) else SourceID(str(source_id).strip())
        )
        resolved_urn = _resolve_archival_urn(source_urn)
        resolved_cat = _coerce_source_record_category(record_category)
        clean_desc = description.strip() if isinstance(description, str) else ""
        if not clean_desc:
            raise ModelFormatError("SourceRecord description cannot be empty or whitespace.")

        resolved_repo = (
            repository_id
            if isinstance(repository_id, RepositoryID)
            else RepositoryID(str(repository_id).strip())
        )
        resolved_audit = audit if audit is not None else AuditStamp.now()
        resolved_people = [
            person
            if isinstance(person, AssociatedIndividual)
            else AssociatedIndividual.from_dict(person)
            for person in (associated_people or [])
        ]
        resolved_tomb = (
            Tombstone.from_dict(tombstone, id_cls=SourceID) if tombstone is not None else None
        )

        return {
            "source_id": resolved_sid,
            "source_urn": resolved_urn,
            "record_category": resolved_cat,
            "description": clean_desc,
            "repository_id": resolved_repo,
            "audit": resolved_audit,
            "media_ids": _deduplicate_media_ids(media_ids),
            "associated_people": resolved_people,
            "tombstone": resolved_tomb,
        }

    @classmethod
    def create(
        cls,
        source_id: SourceID | str,
        source_urn: ArchivalURN | str,
        record_category: SourceRecordCategory | str,
        description: str,
        repository_id: RepositoryID | str,
        audit: AuditStamp | None = None,
        *,
        media_ids: list[MediaID | str] | None = None,
        associated_people: list[AssociatedIndividual | dict[str, Any]] | None = None,
        tombstone: Tombstone[SourceID] | dict[str, Any] | None = None,
    ) -> SourceRecord:
        """Factory constructor for base SourceRecord instances."""
        base_kwargs = cls._normalize_base_kwargs(
            source_id=source_id,
            source_urn=source_urn,
            record_category=record_category,
            description=description,
            repository_id=repository_id,
            audit=audit,
            media_ids=media_ids,
            associated_people=associated_people,
            tombstone=tombstone,
        )
        return cls(**base_kwargs)

    def to_dict(self) -> dict[str, Any]:
        """Serialize SourceRecord and any concrete subclass fields to a dictionary."""
        data: dict[str, Any] = {
            "source_id": self.source_id.value,
            "source_urn": self.source_urn.value,
            "record_category": self.record_category.value,
            "description": self.description,
            "repository_id": self.repository_id.value,
            "audit": self.audit.to_dict(),
            "media_ids": [m.value for m in self.media_ids],
            "associated_people": [p.to_dict() for p in self.associated_people],
        }
        if self.tombstone is not None:
            data["tombstone"] = self.tombstone.to_dict()

        for f in dataclasses.fields(self):
            if f.name in _BASE_SOURCE_RECORD_FIELDS:
                continue
            val = getattr(self, f.name)
            if val is None or (isinstance(val, (list, tuple)) and len(val) == 0):
                continue
            data[f.name] = _serialize_subclass_field(val)

        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Rehydrate SourceRecord or a concrete subclass from a dictionary."""
        if not isinstance(data, dict):
            raise ModelFormatError(f"{cls.__name__} payload must be a dictionary.")

        required = {"source_id", "source_urn", "record_category", "description", "repository_id"}
        if not required.issubset(data.keys()):
            raise ModelFormatError(
                f"{cls.__name__} payload requires source_id, source_urn, record_category, description, and repository_id."
            )

        raw_audit = data.get("audit")
        if raw_audit is None or isinstance(raw_audit, AuditStamp):
            resolved_audit = raw_audit
        elif isinstance(raw_audit, dict):
            resolved_audit = AuditStamp.from_dict(raw_audit)
        else:
            raise ModelFormatError(f"{cls.__name__} audit must be an AuditStamp or dictionary.")

        base_kwargs = cls._normalize_base_kwargs(
            source_id=data["source_id"],
            source_urn=data["source_urn"],
            record_category=data["record_category"],
            description=data["description"],
            repository_id=data["repository_id"],
            audit=resolved_audit,
            media_ids=data.get("media_ids"),
            associated_people=data.get("associated_people"),
            tombstone=data.get("tombstone"),
        )

        for f in dataclasses.fields(cls):
            if f.name in _BASE_SOURCE_RECORD_FIELDS or f.name not in data:
                continue
            base_kwargs[f.name] = _coerce_subclass_field(cls, str(f.type), data[f.name])

        return cls(**base_kwargs)

    def to_json(self) -> str:
        """Serialize SourceRecord to a deterministic JSON string."""
        return json.dumps(self.to_dict(), sort_keys=True)

    @classmethod
    def from_json(cls, json_str: str) -> Self:
        """Deserialize SourceRecord or a concrete subclass from a JSON string."""
        try:
            payload = json.loads(json_str)
        except Exception as exc:
            raise ModelFormatError(f"Failed to parse {cls.__name__} JSON string: {exc}") from exc
        return cls.from_dict(payload)

    def __str__(self) -> str:
        return f"{self.__class__.__name__} [{self.record_category.value}] {self.source_urn.value}: {self.description}"

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(source_id={self.source_id!r}, "
            f"source_urn={self.source_urn!r}, record_category={self.record_category!r})"
        )
