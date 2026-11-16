"""Path: src/gda/db/mapper/personas.py

Bidirectional SQLite row mappers for Individual and Family entities.

Operational Role:
    Translates Individual and Family domain models to and from flattened
    analytical rows in the individuals and families tables.
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from gda.core.enums.vital import UnionType
from gda.db.exceptions import EntityMappingError
from gda.db.mapper.base import (
    BaseRowMapper,
    _deserialize_notes,
    _deserialize_tombstone,
)
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import FamilyID, IndividualID
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate, TimePeriod
from gda.model.base.family import ChildLink, FamilyUnion
from gda.model.base.name import NamePerson
from gda.model.entity.family import Family
from gda.model.entity.individual import Individual

__version__ = "1.0.0+build.1"

__all__ = [
    "FamilyRowMapper",
    "IndividualRowMapper",
]


class IndividualRowMapper(BaseRowMapper[Individual]):
    """Bidirectional row mapper for Individual domain entities."""

    def __init__(self) -> None:
        """Initialize IndividualRowMapper."""
        super().__init__(Individual)

    def to_row(self, entity: Individual) -> dict[str, Any]:
        """Project Individual entity into individuals table row parameters."""
        birth_sort: str | None = entity.birth_date.date.value if entity.birth_date else None
        death_sort: str | None = entity.death_date.date.value if entity.death_date else None
        return {
            "id": entity.id.value,
            "canonical_urn": entity.canonical_urn,
            "raw_name": entity.name.raw,
            "canonical_name": entity.name.canonical,
            "prefix": entity.name.prefix,
            "given_name": entity.name.given,
            "middle_name": entity.name.middle,
            "surname": entity.name.surname,
            "suffix": entity.name.suffix,
            "married_names_json": json.dumps(list(entity.name.married), ensure_ascii=False),
            "aliases_json": json.dumps(list(entity.name.aliases), ensure_ascii=False),
            "alt_spellings_json": json.dumps(list(entity.name.alt_spellings), ensure_ascii=False),
            "name_comment": entity.name.comment,
            "gender": entity.gender.value,
            "is_deceased": 1 if entity.is_deceased else 0,
            "birth_year": entity.birth_year,
            "birth_date_sort": birth_sort,
            "birth_date_json": (
                json.dumps(entity.birth_date.to_dict(), ensure_ascii=False)
                if entity.birth_date
                else None
            ),
            "death_year": entity.death_year,
            "death_date_sort": death_sort,
            "death_date_json": (
                json.dumps(entity.death_date.to_dict(), ensure_ascii=False)
                if entity.death_date
                else None
            ),
            "birth_place_id": (entity.birth_place_id.value if entity.birth_place_id else None),
            "death_place_id": (entity.death_place_id.value if entity.death_place_id else None),
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

    def from_row(self, row: sqlite3.Row | dict[str, Any]) -> Individual:
        """Hydrate Individual entity from individuals table row."""
        try:
            data = dict(row)
            tombstone = _deserialize_tombstone(data, IndividualID)
            notes_list = _deserialize_notes(data.get("notes_json"))

            married = (
                json.loads(data["married_names_json"]) if data.get("married_names_json") else []
            )
            aliases = json.loads(data["aliases_json"]) if data.get("aliases_json") else []
            alt_spellings = (
                json.loads(data["alt_spellings_json"]) if data.get("alt_spellings_json") else []
            )

            name_obj = NamePerson(
                raw=data["raw_name"],
                canonical=data["canonical_name"],
                prefix=data.get("prefix"),
                given=data["given_name"],
                middle=data.get("middle_name"),
                surname=data.get("surname"),
                suffix=data.get("suffix"),
                married=married,
                aliases=aliases,
                alt_spellings=alt_spellings,
                comment=data.get("name_comment"),
            )

            b_date = (
                EventDate.from_dict(json.loads(data["birth_date_json"]))
                if data.get("birth_date_json")
                else None
            )
            d_date = (
                EventDate.from_dict(json.loads(data["death_date_json"]))
                if data.get("death_date_json")
                else None
            )

            return Individual.create(
                individual_id=IndividualID(data["id"]),
                name=name_obj,
                canonical_urn=data["canonical_urn"],
                gender=data.get("gender", "U"),
                birth_date=b_date,
                death_date=d_date,
                birth_place_id=data.get("birth_place_id"),
                death_place_id=data.get("death_place_id"),
                is_deceased=bool(data.get("is_deceased", 1)),
                audit=AuditStamp(
                    created_at=IsoTimestamp(data["created_at"]),
                    updated_at=IsoTimestamp(data["updated_at"]),
                ),
                tombstone=tombstone,
                notes=notes_list,
            )
        except Exception as err:
            raise EntityMappingError(
                f"Failed to map row to Individual: {err}",
                details={"entity": "Individual", "error": str(err)},
            ) from err


class FamilyRowMapper(BaseRowMapper[Family]):
    """Bidirectional row mapper for Family domain entities."""

    def __init__(self) -> None:
        """Initialize FamilyRowMapper."""
        super().__init__(Family)

    def to_row(self, entity: Family) -> dict[str, Any]:
        """Project Family entity into families table row parameters."""
        u_period = entity.union.period
        return {
            "id": entity.id.value,
            "canonical_urn": entity.canonical_urn,
            "union_type": entity.union.union_type.value,
            "dissolution_type": (
                entity.union.dissolution_type.value if entity.union.dissolution_type else None
            ),
            "start_date_json": (
                json.dumps(u_period.start_date.to_dict(), ensure_ascii=False)
                if u_period and u_period.start_date
                else None
            ),
            "end_date_json": (
                json.dumps(u_period.end_date.to_dict(), ensure_ascii=False)
                if u_period and u_period.end_date
                else None
            ),
            "partner_ids_json": json.dumps(
                [p.value for p in entity.partner_ids], ensure_ascii=False
            ),
            "children_json": json.dumps([c.to_dict() for c in entity.children], ensure_ascii=False),
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

    def from_row(self, row: sqlite3.Row | dict[str, Any]) -> Family:
        """Hydrate Family entity from families table row."""
        try:
            data = dict(row)
            tombstone = _deserialize_tombstone(data, FamilyID)
            notes_list = _deserialize_notes(data.get("notes_json"))

            start_date = (
                EventDate.from_dict(json.loads(data["start_date_json"]))
                if data.get("start_date_json")
                else None
            )
            end_date = (
                EventDate.from_dict(json.loads(data["end_date_json"]))
                if data.get("end_date_json")
                else None
            )
            period = (
                TimePeriod(start_date=start_date, end_date=end_date)
                if start_date is not None or end_date is not None
                else None
            )

            union_obj = FamilyUnion.create(
                union_type=data.get("union_type", UnionType.UNKNOWN),
                dissolution_type=data.get("dissolution_type"),
                period=period,
            )

            partner_ids = (
                json.loads(data["partner_ids_json"]) if data.get("partner_ids_json") else []
            )
            children_raw = json.loads(data["children_json"]) if data.get("children_json") else []
            children_objs = [ChildLink.from_dict(c) for c in children_raw if isinstance(c, dict)]

            return Family.create(
                family_id=FamilyID(data["id"]),
                canonical_urn=data["canonical_urn"],
                union=union_obj,
                partner_ids=partner_ids,
                children=children_objs,
                audit=AuditStamp(
                    created_at=IsoTimestamp(data["created_at"]),
                    updated_at=IsoTimestamp(data["updated_at"]),
                ),
                tombstone=tombstone,
                notes=notes_list,
            )
        except Exception as err:
            raise EntityMappingError(
                f"Failed to map row to Family: {err}",
                details={"entity": "Family", "error": str(err)},
            ) from err
