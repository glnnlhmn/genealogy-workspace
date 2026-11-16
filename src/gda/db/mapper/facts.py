"""Path: src/gda/db/mapper/facts.py

Bidirectional SQLite row mapper for Fact domain entities.

Operational Role:
    Translates Fact domain models to and from flattened analytical rows in
    the facts table, deriving chronological sort keys and 4-digit calendar years.
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from gda.core.enums.core import FactType
from gda.db.exceptions import EntityMappingError
from gda.db.mapper.base import (
    BaseRowMapper,
    _deserialize_notes,
    _deserialize_tombstone,
    _extract_id_str,
    _extract_year_from_text,
)
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import FactID, FamilyID, IndividualID, LocationID, SiteID
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate, TimePeriod
from gda.model.base.source import SourceReference
from gda.model.entity.fact import Fact, FactParticipant

__version__ = "1.0.0+build.1"

__all__ = [
    "FactRowMapper",
]


class FactRowMapper(BaseRowMapper[Fact]):
    """Bidirectional row mapper for Fact domain entities."""

    def __init__(self) -> None:
        """Initialize FactRowMapper."""
        super().__init__(Fact)

    def to_row(self, entity: Fact) -> dict[str, Any]:
        """Project Fact entity into facts table row parameters."""
        fact_sort: str | None = None
        if isinstance(entity.date, EventDate):
            fact_sort = entity.date.date.value
        elif isinstance(entity.date, TimePeriod) and entity.date.start_date:
            fact_sort = entity.date.start_date.date.value

        fact_year = _extract_year_from_text(fact_sort)

        return {
            "id": entity.id.value,
            "canonical_urn": entity.canonical_urn,
            "fact_type": entity.fact_type.value,
            "title": entity.title,
            "primary_subject_id": entity.primary_subject_id.value,
            "fact_year": fact_year,
            "fact_date_sort": fact_sort,
            "date_json": (
                json.dumps(entity.date.to_dict(), ensure_ascii=False) if entity.date else None
            ),
            "location_id": entity.location_id.value if entity.location_id else None,
            "site_id": entity.site_id.value if entity.site_id else None,
            "value": entity.value,
            "description": entity.description,
            "narrative": entity.narrative,
            "participants_json": json.dumps(
                [p.to_dict() for p in entity.participants], ensure_ascii=False
            ),
            "citations_json": json.dumps(
                [c.to_dict() for c in entity.citations], ensure_ascii=False
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

    def from_row(self, row: sqlite3.Row | dict[str, Any]) -> Fact:
        """Hydrate Fact entity from facts table row."""
        try:
            data = dict(row)
            tombstone = _deserialize_tombstone(data, FactID)
            notes_list = _deserialize_notes(data.get("notes_json"))

            raw_subj = str(data["primary_subject_id"])
            subj_id: IndividualID | FamilyID = (
                FamilyID(raw_subj) if raw_subj.startswith("FAM-") else IndividualID(raw_subj)
            )

            date_obj = json.loads(data["date_json"]) if data.get("date_json") else None
            loc_str = _extract_id_str(data.get("location_id"))
            site_str = _extract_id_str(data.get("site_id"))

            part_raw = (
                json.loads(data["participants_json"]) if data.get("participants_json") else []
            )
            participants = [FactParticipant.from_dict(p) for p in part_raw if isinstance(p, dict)]

            cit_raw = json.loads(data["citations_json"]) if data.get("citations_json") else []
            citations = [SourceReference.from_dict(c) for c in cit_raw if isinstance(c, dict)]

            return Fact.create(
                fact_id=FactID(data["id"]),
                canonical_urn=data["canonical_urn"],
                fact_type=FactType(data["fact_type"]),
                title=data["title"],
                primary_subject_id=subj_id,
                date=date_obj,
                location_id=LocationID(loc_str) if loc_str else None,
                site_id=SiteID(site_str) if site_str else None,
                value=data.get("value"),
                description=data.get("description"),
                narrative=data.get("narrative"),
                participants=participants,
                citations=citations,
                audit=AuditStamp(
                    created_at=IsoTimestamp(data["created_at"]),
                    updated_at=IsoTimestamp(data["updated_at"]),
                ),
                tombstone=tombstone,
                notes=notes_list,
            )
        except Exception as err:
            raise EntityMappingError(
                f"Failed to map row to Fact: {err}",
                details={"entity": "Fact", "error": str(err)},
            ) from err
