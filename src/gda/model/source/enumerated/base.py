"""Path: src/gda/model/source/enumerated/base.py

Foundational enumerated and tabulated archival roll domain entity model.

Operational Role:
    Extends SourceRecord composite to represent systematic, tabulated archival
    rolls (census schedules, tax assessments, voter registers, and city directories).
    Enforces jurisdiction hygiene, enumeration year tracking, transcript linking,
    and canonical dictionary/JSON serialization.
"""

from __future__ import annotations

import dataclasses
import json
from enum import Enum
from typing import Any, Self

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.enums.fiscal import (
    CitizenshipStatus,
    HomeOwnership,
    ResidentialStatus,
    TaxpayerClassification,
)
from gda.core.enums.sources import SourceRecordCategory, SourceRecordType
from gda.core.errors import ModelFormatError
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import (
    IndividualID,
    LocationID,
    MediaID,
    RepositoryID,
    SourceID,
    TranscriptID,
)
from gda.model.atom.urn import ArchivalURN, CensusUrn, SourceURN
from gda.model.atom.year import HistoricalYear
from gda.model.base.association import AssociatedIndividual
from gda.model.base.audit import AuditStamp
from gda.model.base.source import SourceRecord
from gda.model.base.tombstone import Tombstone

__version__ = "1.0.0+build.5"

__all__ = [
    "EnumeratedRollRecord",
    "coerce_field_value",
    "serialize_primitive_value",
]

_ENUM_TYPES: dict[str, type[Enum]] = {
    "SourceRecordCategory": SourceRecordCategory,
    "SourceRecordType": SourceRecordType,
    "CitizenshipStatus": CitizenshipStatus,
    "HomeOwnership": HomeOwnership,
    "ResidentialStatus": ResidentialStatus,
    "TaxpayerClassification": TaxpayerClassification,
}


def serialize_primitive_value(val: Any) -> Any:
    """Recursively convert GDA atoms, enums, and nested containers into JSON-safe primitives."""
    if isinstance(val, Enum):
        return val.value
    if val is None or isinstance(val, (bool, int, float, str)):
        return val
    if hasattr(val, "to_dict"):
        return val.to_dict()
    if isinstance(val, (list, tuple)):
        return [serialize_primitive_value(item) for item in val]
    return str(val)


def coerce_field_value(type_str: str, raw: Any) -> Any:
    """Coerce a raw JSON-deserialized value into the target GDA atom or enum type."""
    if raw is None:
        return None

    clean_type = type_str.replace(" | None", "").replace("Optional[", "").rstrip("]").strip()

    if clean_type == "SourceID":
        return raw if isinstance(raw, SourceID) else SourceID(str(raw))
    if clean_type == "IndividualID":
        return raw if isinstance(raw, IndividualID) else IndividualID(str(raw))
    if clean_type == "LocationID":
        return raw if isinstance(raw, LocationID) else LocationID(str(raw))
    if clean_type == "TranscriptID":
        return raw if isinstance(raw, TranscriptID) else TranscriptID(str(raw))
    if clean_type == "RepositoryID":
        return raw if isinstance(raw, RepositoryID) else RepositoryID(str(raw))
    if clean_type == "CensusUrn":
        return raw if isinstance(raw, CensusUrn) else CensusUrn(str(raw))
    if clean_type == "ArchivalURN":
        text = str(raw)
        if text.startswith("URN:CENSUS:"):
            return CensusUrn(text)
        if text.startswith("URN:SRC:"):
            return SourceURN(text)
        return ArchivalURN(text)
    if clean_type == "HistoricalYear":
        return raw if isinstance(raw, HistoricalYear) else HistoricalYear(int(raw))
    if clean_type in _ENUM_TYPES:
        enum_cls = _ENUM_TYPES[clean_type]
        return raw if isinstance(raw, enum_cls) else enum_cls(str(raw))

    return raw


@dataclass(
    repr=False,
    config=ConfigDict(kw_only=True, frozen=True, extra="forbid", strict=True),
)
class EnumeratedRollRecord(SourceRecord):
    """Base evidentiary composite for tabulated and enumerated archival rolls."""

    enumeration_year: HistoricalYear = Field(
        ...,
        description="Calendar year the enumeration, assessment, or directory canvass occurred.",
    )
    jurisdiction_raw: str = Field(
        ...,
        description="Verbatim civil jurisdiction, district, or municipality heading.",
    )
    jurisdiction_id: LocationID | None = Field(
        default=None,
        description="Resolved civil jurisdiction LocationID for the enumerated roll.",
    )
    enumerator_or_assessor_raw: str | None = Field(
        default=None,
        description="Verbatim name of the enumerator, assessor, or compiler.",
    )
    transcript_id: TranscriptID | None = Field(
        default=None,
        description="Decoupled TranscriptID linking verbatim schedule or roll transcription.",
    )

    def __post_init__(self) -> None:
        """Enforce raw jurisdiction and enumerator string hygiene."""
        super().__post_init__()

        jur = self.jurisdiction_raw.strip()
        if not jur:
            raise ModelFormatError(
                "EnumeratedRollRecord 'jurisdiction_raw' cannot be empty or whitespace.",
                details={"source_id": str(self.source_id)},
            )
        if jur != self.jurisdiction_raw:
            object.__setattr__(self, "jurisdiction_raw", jur)

        if self.enumerator_or_assessor_raw is not None:
            enum_name = self.enumerator_or_assessor_raw.strip()
            if not enum_name:
                raise ModelFormatError(
                    "EnumeratedRollRecord 'enumerator_or_assessor_raw' cannot be empty or whitespace.",
                    details={"source_id": str(self.source_id)},
                )
            if enum_name != self.enumerator_or_assessor_raw:
                object.__setattr__(self, "enumerator_or_assessor_raw", enum_name)

    def to_dict(self) -> dict[str, Any]:
        """Serialize EnumeratedRollRecord and subclass fields to a dictionary."""
        data = super().to_dict()
        base_keys = set(data.keys())
        for f in dataclasses.fields(self):
            if f.name in base_keys:
                continue
            val = getattr(self, f.name)
            data[f.name] = serialize_primitive_value(val)
        return data

    @classmethod
    def _parse_base_source_kwargs(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Extract and coerce canonical SourceRecord header fields from a payload dict."""
        if not isinstance(data, dict):
            raise ModelFormatError(f"{cls.__name__} payload must be a dictionary.")

        sid = data.get("source_id")
        raw_urn = data.get("source_urn")
        cat = data.get("record_category")
        desc = data.get("description")
        rep = data.get("repository_id")
        audit_payload = data.get("audit")

        if not all((sid, raw_urn, cat, desc, rep, audit_payload)):
            raise ModelFormatError(
                f"{cls.__name__} requires source_id, source_urn, record_category, description, repository_id, and audit."
            )

        urn_str = str(raw_urn)
        if isinstance(raw_urn, ArchivalURN):
            urn_obj: ArchivalURN = raw_urn
        elif urn_str.startswith("URN:CENSUS:"):
            urn_obj = CensusUrn(urn_str)
        elif urn_str.startswith("URN:SRC:"):
            urn_obj = SourceURN(urn_str)
        else:
            urn_obj = ArchivalURN(urn_str)

        if isinstance(audit_payload, AuditStamp):
            audit_obj = audit_payload
        elif isinstance(audit_payload, dict):
            audit_obj = AuditStamp(
                created_at=IsoTimestamp(audit_payload["created_at"]),
                updated_at=IsoTimestamp(audit_payload["updated_at"]),
            )
        else:
            raise ModelFormatError(f"{cls.__name__} audit must be an AuditStamp or dictionary.")

        tombstone_payload = data.get("tombstone")
        tombstone_obj: Tombstone[SourceID] | None = None
        if isinstance(tombstone_payload, dict):
            raw_sup = tombstone_payload.get("superseded_by")
            sup_id = (
                raw_sup
                if (raw_sup is None or isinstance(raw_sup, SourceID))
                else SourceID(str(raw_sup))
            )
            tombstone_obj = Tombstone[SourceID](
                is_deprecated=tombstone_payload.get("is_deprecated", False),
                deprecated_at=(
                    IsoTimestamp(tombstone_payload["deprecated_at"])
                    if tombstone_payload.get("deprecated_at")
                    else None
                ),
                superseded_by=sup_id,
            )

        cat_obj = (
            cat
            if isinstance(cat, SourceRecordCategory)
            else SourceRecordCategory(str(cat).strip().upper())
        )

        return {
            "source_id": sid if isinstance(sid, SourceID) else SourceID(str(sid)),
            "source_urn": urn_obj,
            "record_category": cat_obj,
            "description": str(desc),
            "repository_id": rep if isinstance(rep, RepositoryID) else RepositoryID(str(rep)),
            "audit": audit_obj,
            "media_ids": [
                m if isinstance(m, MediaID) else MediaID(str(m)) for m in data.get("media_ids", [])
            ],
            "associated_people": [
                p if isinstance(p, AssociatedIndividual) else AssociatedIndividual.from_dict(p)
                for p in data.get("associated_people", [])
            ],
            "tombstone": tombstone_obj,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Deserialize a dictionary payload into an immutable EnumeratedRollRecord subclass."""
        kwargs = cls._parse_base_source_kwargs(data)
        base_keys = set(kwargs.keys())

        for f in dataclasses.fields(cls):
            if f.name in base_keys or f.name not in data:
                continue
            kwargs[f.name] = coerce_field_value(str(f.type), data[f.name])

        return cls(**kwargs)

    def to_json(self) -> str:
        """Serialize roll record to a JSON formatted string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_json(cls, payload: str) -> Self:
        """Deserialize a JSON string directly into an immutable roll record."""
        try:
            data = json.loads(payload)
        except Exception as exc:
            raise ModelFormatError(f"Failed to parse {cls.__name__} JSON string: {exc}") from exc
        return cls.from_dict(data)

    def __str__(self) -> str:
        return (
            f"{self.__class__.__name__} [{self.record_category.value}] "
            f"{self.jurisdiction_raw} ({self.enumeration_year.value}) - {self.source_urn}"
        )

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(source_id={self.source_id!r}, "
            f"enumeration_year={self.enumeration_year!r}, "
            f"jurisdiction_raw={self.jurisdiction_raw!r})"
        )
