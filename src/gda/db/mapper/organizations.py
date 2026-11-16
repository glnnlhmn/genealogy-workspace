"""Path: src/gda/db/mapper/organizations.py

Bidirectional SQLite row mapper for Organization domain entities.

Operational Role:
    Translates Organization domain models to and from flattened analytical
    rows in the organizations table.
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from gda.core.enums.orgs import OrganizationCategory
from gda.db.exceptions import EntityMappingError
from gda.db.mapper.base import (
    BaseRowMapper,
    _deserialize_name_thing,
    _deserialize_notes,
    _deserialize_tombstone,
    _extract_id_str,
    _serialize_name_thing,
)
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import LocationID, OrganizationID, SiteID
from gda.model.base.audit import AuditStamp
from gda.model.base.date import TimePeriod
from gda.model.entity.organization import Organization

__version__ = "1.0.0+build.1"

__all__ = [
    "OrganizationRowMapper",
]


class OrganizationRowMapper(BaseRowMapper[Organization]):
    """Bidirectional row mapper for Organization domain entities."""

    def __init__(self) -> None:
        """Initialize OrganizationRowMapper."""
        super().__init__(Organization)

    def to_row(self, entity: Organization) -> dict[str, Any]:
        """Project Organization entity into organizations table row parameters."""
        return {
            "id": entity.id.value,
            "canonical_urn": entity.canonical_urn,
            **_serialize_name_thing(entity.name),
            "category": entity.category.value,
            "parent_org_id": (entity.parent_org_id.value if entity.parent_org_id else None),
            "location_id": entity.location_id.value if entity.location_id else None,
            "meeting_site_id": (entity.meeting_site_id.value if entity.meeting_site_id else None),
            "is_active": 1 if entity.is_active else 0,
            "period_json": (
                json.dumps(entity.period.to_dict(), ensure_ascii=False) if entity.period else None
            ),
            "predecessor_ids_json": json.dumps(
                [p.value for p in entity.predecessor_ids], ensure_ascii=False
            ),
            "successor_ids_json": json.dumps(
                [s.value for s in entity.successor_ids], ensure_ascii=False
            ),
            "is_deprecated": 1 if entity.tombstone.is_deprecated else 0,
            "deprecated_at": (
                entity.tombstone.deprecated_at.value if entity.tombstone.deprecated_at else None
            ),
            "superseded_by": (
                entity.tombstone.superseded_by.value if entity.tombstone.superseded_by else None
            ),
            "notes_json": json.dumps([n.to_dict() for n in entity.notes], ensure_ascii=False),
            "created_at": entity.audit.created_at.value,
            "updated_at": entity.audit.updated_at.value,
        }

    def from_row(self, row: sqlite3.Row | dict[str, Any]) -> Organization:
        """Hydrate Organization entity from organizations table row."""
        try:
            data = dict(row)
            tombstone = _deserialize_tombstone(data, OrganizationID)
            notes_list = _deserialize_notes(data.get("notes_json"))
            name_obj = _deserialize_name_thing(data)

            parent_str = _extract_id_str(data.get("parent_org_id"))
            loc_str = _extract_id_str(data.get("location_id"))
            site_str = _extract_id_str(data.get("meeting_site_id"))

            period_obj = (
                TimePeriod.from_dict(json.loads(data["period_json"]))
                if data.get("period_json")
                else None
            )
            preds = (
                json.loads(data["predecessor_ids_json"]) if data.get("predecessor_ids_json") else []
            )
            succs = json.loads(data["successor_ids_json"]) if data.get("successor_ids_json") else []

            return Organization.create(
                org_id=OrganizationID(data["id"]),
                name=name_obj,
                category=OrganizationCategory(data["category"]),
                canonical_urn=data["canonical_urn"],
                parent_org_id=OrganizationID(parent_str) if parent_str else None,
                predecessor_ids=preds,
                successor_ids=succs,
                location_id=LocationID(loc_str) if loc_str else None,
                meeting_site_id=SiteID(site_str) if site_str else None,
                period=period_obj,
                is_active=bool(data.get("is_active", 1)),
                audit=AuditStamp(
                    created_at=IsoTimestamp(data["created_at"]),
                    updated_at=IsoTimestamp(data["updated_at"]),
                ),
                tombstone=tombstone,
                notes=notes_list,
            )
        except Exception as err:
            raise EntityMappingError(
                f"Failed to map row to Organization: {err}",
                details={"entity": "Organization", "error": str(err)},
            ) from err
