"""Path: src/gda/model/source/other/miscellaneous.py

Flexible catch-all model for miscellaneous historical sources, ephemera, receipts, and untyped items.

Operational Role:
    Defines OtherMiscellaneousRecord (extending SourceRecord) to capture documentary
    evidence from fraternal/lodge records, membership rosters, ephemera, receipts,
    photographs, financial papers, and untyped manuscript items with open key-value
    custom_fields support (aligned with schemas/sources/other_miscellaneous.schema.json).
"""

from __future__ import annotations

import copy
import re
from typing import Any, ClassVar, cast

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.enums import coerce_enum
from gda.core.enums.sources import SourceRecordCategory, SourceRecordType
from gda.core.errors import ModelFormatError
from gda.core.types import URN_REGEXES
from gda.model.atom.id import LocationID, MediaID, RepositoryID, SourceID
from gda.model.atom.urn import ArchivalURN, SourceURN
from gda.model.base.association import AssociatedIndividual
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate
from gda.model.base.source import SourceRecord
from gda.model.base.tombstone import Tombstone

__version__ = "1.0.0+build.4"

__all__ = [
    "OtherMiscellaneousRecord",
]

_OTHER_CATEGORIES: frozenset[SourceRecordCategory] = frozenset(
    {
        SourceRecordCategory.OTHER,
        SourceRecordCategory.FRATERNAL,
        SourceRecordCategory.CIVIC,
        SourceRecordCategory.EPHEMERA,
        SourceRecordCategory.FINANCIAL,
    }
)

_OTHER_RECORD_TYPES: frozenset[SourceRecordType] = frozenset(
    {
        SourceRecordType.BIBLE_RECORD,
        SourceRecordType.DIARY,
        SourceRecordType.CORRESPONDENCE,
        SourceRecordType.FINANCIAL_RECORD,
        SourceRecordType.EPHEMERA_ITEM,
        SourceRecordType.PHOTO,
        SourceRecordType.LODGE_RECORD,
        SourceRecordType.MEMBERSHIP_ROSTER,
        SourceRecordType.RECEIPT,
        SourceRecordType.MISCELLANEOUS,
    }
)

_OTHER_URN_PATTERN: re.Pattern[str] = URN_REGEXES["OTHER"]


def _resolve_other_urn(raw: ArchivalURN | str) -> ArchivalURN:
    """Coerce a raw URN string into ArchivalURN (URN:OTHER:...) or SourceURN (URN:SRC:...)."""
    if isinstance(raw, ArchivalURN):
        return raw
    token = str(raw).strip()
    if token.startswith("URN:OTHER:"):
        if not _OTHER_URN_PATTERN.match(token):
            raise ModelFormatError(
                f"Invalid Other URN syntax: '{token}'. "
                "Must match 'URN:OTHER:<YEAR>:<JURISDICTION>:<LOCATOR>'."
            )
        return ArchivalURN(token)
    return SourceURN(token)


def _deserialize_event_date(raw: Any, field_name: str) -> EventDate:
    """Coerce an EventDate instance, dictionary, or compact date string."""
    if isinstance(raw, EventDate):
        return raw
    if isinstance(raw, (dict, str)):
        return EventDate.from_dict(raw)
    raise ModelFormatError(f"Invalid '{field_name}' payload: expected EventDate, dict, or str.")


@dataclass(
    repr=False,
    config=ConfigDict(frozen=True, extra="forbid", strict=True),
    kw_only=True,
)
class OtherMiscellaneousRecord(SourceRecord):
    """Flexible archival record for ephemera, receipts, lodge items, and unclassified sources."""

    record_category: SourceRecordCategory = Field(
        default=SourceRecordCategory.OTHER,
        description="High-level archival domain category (OTHER, FRATERNAL, CIVIC, EPHEMERA, FINANCIAL).",
    )
    record_type: SourceRecordType = Field(
        default=SourceRecordType.MISCELLANEOUS,
        description="Specific miscellaneous item classification.",
    )
    item_date: EventDate = Field(
        ...,
        description="Date or estimated date of the item, receipt, or ephemera.",
    )
    organization_or_entity_name: str | None = Field(
        default=None,
        description="Issuing lodge, society, merchant, or entity name if applicable.",
    )
    organization_location_id: LocationID | None = Field(
        default=None,
        description="Resolved canonical LocationID for the issuing entity or item origin.",
    )
    custom_fields: dict[str, Any] = Field(
        default_factory=dict,
        description="Open key-value dictionary for domain-specific attributes not yet modeled.",
    )
    item_note: str | None = Field(
        default=None,
        description="Contextual or physical description note for the miscellaneous item.",
    )

    ALLOWED_CATEGORIES: ClassVar[frozenset[SourceRecordCategory]] = _OTHER_CATEGORIES
    ALLOWED_RECORD_TYPES: ClassVar[frozenset[SourceRecordType]] = _OTHER_RECORD_TYPES

    def __post_init__(self) -> None:
        """Enforce category and record_type bounds."""
        super().__post_init__()

        if self.record_category not in self.ALLOWED_CATEGORIES:
            raise ModelFormatError(
                f"{self.__class__.__name__} requires record_category in "
                f"{sorted(c.value for c in self.ALLOWED_CATEGORIES)}, "
                f"got '{self.record_category.value}'."
            )

        if self.record_type not in self.ALLOWED_RECORD_TYPES:
            raise ModelFormatError(
                f"{self.__class__.__name__} requires record_type in "
                f"{sorted(t.value for t in self.ALLOWED_RECORD_TYPES)}, "
                f"got '{self.record_type.value}'."
            )

    @classmethod
    def create(  # type: ignore[override]
        cls,
        source_id: SourceID | str,
        source_urn: ArchivalURN | str,
        description: str,
        repository_id: RepositoryID | str,
        item_date: EventDate | dict[str, Any] | str,
        record_category: SourceRecordCategory | str = SourceRecordCategory.OTHER,
        record_type: SourceRecordType | str = SourceRecordType.MISCELLANEOUS,
        organization_or_entity_name: str | None = None,
        organization_location_id: LocationID | str | None = None,
        custom_fields: dict[str, Any] | None = None,
        item_note: str | None = None,
        audit: AuditStamp | None = None,
        media_ids: list[MediaID | str] | None = None,
        associated_people: list[AssociatedIndividual] | None = None,
        tombstone: Tombstone[SourceID] | None = None,
    ) -> OtherMiscellaneousRecord:
        """Factory constructor instantiating a validated OtherMiscellaneousRecord."""
        resolved_sid = source_id if isinstance(source_id, SourceID) else SourceID(source_id)
        resolved_urn = _resolve_other_urn(source_urn)
        resolved_rep = (
            repository_id
            if isinstance(repository_id, RepositoryID)
            else RepositoryID(repository_id)
        )
        res_cat = coerce_enum(SourceRecordCategory, record_category, field_name="record_category")
        res_type = coerce_enum(SourceRecordType, record_type, field_name="record_type")
        res_org_loc = (
            organization_location_id
            if (
                organization_location_id is None or isinstance(organization_location_id, LocationID)
            )
            else LocationID(organization_location_id)
        )
        res_date = _deserialize_event_date(item_date, "item_date")
        res_custom = copy.deepcopy(custom_fields) if custom_fields is not None else {}

        resolved_audit = audit if audit is not None else AuditStamp.now()
        resolved_media = [m if isinstance(m, MediaID) else MediaID(m) for m in (media_ids or [])]

        return cls(
            source_id=resolved_sid,
            source_urn=resolved_urn,
            record_category=res_cat,
            record_type=res_type,
            description=description.strip() if isinstance(description, str) else description,
            repository_id=resolved_rep,
            audit=resolved_audit,
            media_ids=resolved_media,
            associated_people=associated_people or [],
            tombstone=tombstone,
            item_date=res_date,
            organization_or_entity_name=organization_or_entity_name,
            organization_location_id=res_org_loc,
            custom_fields=res_custom,
            item_note=item_note,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize OtherMiscellaneousRecord to a dictionary."""
        data = super().to_dict()
        data["custom_fields"] = copy.deepcopy(self.custom_fields)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> OtherMiscellaneousRecord:
        """Deserialize a dictionary payload into an OtherMiscellaneousRecord."""
        if not isinstance(data, dict):
            raise ModelFormatError("OtherMiscellaneousRecord payload must be a dictionary.")

        sid = data.get("source_id")
        raw_urn = data.get("source_urn")
        desc = data.get("description")
        rep = data.get("repository_id")
        audit_payload = data.get("audit")
        raw_item_dt = data.get("item_date")

        if not all((sid, raw_urn, desc, rep, audit_payload, raw_item_dt)):
            raise ModelFormatError(
                "OtherMiscellaneousRecord requires source_id, source_urn, description, "
                "repository_id, audit, and item_date."
            )

        raw_custom = data.get("custom_fields", {})
        if not isinstance(raw_custom, dict):
            raise ModelFormatError("OtherMiscellaneousRecord 'custom_fields' must be a dictionary.")

        if not isinstance(audit_payload, (AuditStamp, dict)):
            raise ModelFormatError(
                "OtherMiscellaneousRecord audit must be an AuditStamp or dictionary."
            )
        audit_obj = AuditStamp.from_dict(audit_payload)

        tombstone_payload = data.get("tombstone")
        tombstone_obj = (
            Tombstone.from_dict(tombstone_payload, id_cls=SourceID)
            if isinstance(tombstone_payload, dict)
            else None
        )

        return cls.create(
            source_id=str(sid),
            source_urn=str(raw_urn),
            description=str(desc),
            repository_id=str(rep),
            item_date=cast(Any, raw_item_dt),
            record_category=data.get("record_category", SourceRecordCategory.OTHER),
            record_type=data.get("record_type", SourceRecordType.MISCELLANEOUS),
            organization_or_entity_name=data.get("organization_or_entity_name"),
            organization_location_id=data.get("organization_location_id"),
            custom_fields=raw_custom,
            item_note=data.get("item_note"),
            audit=audit_obj,
            media_ids=data.get("media_ids", []),
            associated_people=[
                AssociatedIndividual.from_dict(p) for p in data.get("associated_people", [])
            ],
            tombstone=tombstone_obj,
        )

    def __str__(self) -> str:
        return f"OtherMiscellaneousRecord [{self.record_type.value}] {self.description}"
