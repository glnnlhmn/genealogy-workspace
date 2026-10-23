"""Path: src/gda/db/mapper.py

Bidirectional relational row-to-model mappers bridging SQLite and Pydantic entities.

Operational Role:
    Translates canonical Pydantic domain models (Location, Site, Individual, Family, Fact)
    into flat SQLite row parameter dictionaries (projecting relational query scalars and
    serializing complex composite structures to JSON) and reconstructs pure domain entities
    from database rows without relying on a third-party ORM.

Classes:
    BaseRowMapper: Generic mapping contract parameterized by entity type T.
    LocationRowMapper: Bidirectional mapper for Location entities.
    SiteRowMapper: Bidirectional mapper for Site entities.
    IndividualRowMapper: Bidirectional mapper for Individual entities.
    FamilyRowMapper: Bidirectional mapper for Family entities.
    FactRowMapper: Bidirectional mapper for Fact entities.
"""

from __future__ import annotations

import json
import re
import sqlite3
from abc import ABC, abstractmethod
from typing import Any

from pydantic import TypeAdapter

from gda.core.introspectable import IntrospectableMixin
from gda.db.exceptions import EntityMappingError
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import (
    AtomID,
    FactID,
    FamilyID,
    IndividualID,
    LocationID,
    SiteID,
)
from gda.model.entity.fact import Fact
from gda.model.entity.family import Family
from gda.model.entity.individual import Individual
from gda.model.entity.location import Location
from gda.model.entity.site import Site

__version__ = "1.0.0+build.15"

_YEAR_PATTERN: re.Pattern[str] = re.compile(r"\b(\d{4})\b")


def _extract_id_str(val: Any) -> str | None:
    """Extract plain ID string from raw string, dict dump, or AtomID."""
    if val is None:
        return None
    if isinstance(val, str):
        return val
    if isinstance(val, dict):
        return str(val.get("value", ""))
    if isinstance(val, AtomID):
        return str(val.value)
    return str(val)


def _extract_year_from_text(date_text: str | None) -> int | None:
    """Extract 4-digit calendar year from date text if present."""
    if not date_text:
        return None
    match = _YEAR_PATTERN.search(date_text)
    return int(match.group(1)) if match else None


class BaseRowMapper[T](IntrospectableMixin, ABC):
    """Abstract base contract for bidirectional SQLite row mapping."""

    def __init__(self, model_cls: type[T]) -> None:
        """Initialize row mapper with bound model class and Pydantic adapter.

        Args:
            model_cls: Concrete Pydantic domain entity class.
        """
        self._model_cls = model_cls
        self._adapter: TypeAdapter[T] = TypeAdapter(model_cls)

    @property
    def model_cls(self) -> type[T]:
        """Return the bound domain entity class."""
        return self._model_cls

    @abstractmethod
    def to_row(self, entity: T) -> dict[str, Any]:
        """Convert a pure domain entity into flat SQLite row parameters.

        Args:
            entity: Domain model instance.

        Returns:
            Dictionary mapping table column names to SQLite-compatible values.
        """

    @abstractmethod
    def from_row(self, row: sqlite3.Row | dict[str, Any]) -> T:
        """Reconstruct a pure domain entity from a SQLite row or dictionary.

        Args:
            row: SQLite row or dict matching table columns.

        Returns:
            Strongly-typed, fully validated domain model instance.

        Raises:
            EntityMappingError: On serialization or validation failure.
        """


class LocationRowMapper(BaseRowMapper[Location]):
    """Bidirectional row mapper for Location domain entities."""

    def __init__(self) -> None:
        """Initialize LocationRowMapper."""
        super().__init__(Location)

    def to_row(self, entity: Location) -> dict[str, Any]:
        """Project Location entity into locations table row parameters."""
        raw = self._adapter.dump_python(entity, mode="json")
        return {
            "id": entity.id.value,
            "canonical_urn": entity.canonical_urn,
            "name": entity.name,
            "category": entity.category.value,
            "parent_id": entity.parent_id.value if entity.parent_id else None,
            "is_primary_local_authority": 1 if entity.is_primary_local_authority else 0,
            "is_unincorporated": 1 if entity.is_unincorporated else 0,
            "coordinates_json": (
                json.dumps(raw["coordinates"]) if raw.get("coordinates") else None
            ),
            "period_json": json.dumps(raw["period"]) if raw.get("period") else None,
            "historical_names_json": (
                json.dumps(raw["historical_names"])
                if raw.get("historical_names")
                else None
            ),
            "alternate_names_json": (
                json.dumps(raw["alternate_names"])
                if raw.get("alternate_names")
                else None
            ),
            "associated_jurisdiction_ids_json": (
                json.dumps(
                    [_extract_id_str(i) for i in raw["associated_jurisdiction_ids"]]
                )
                if raw.get("associated_jurisdiction_ids")
                else None
            ),
            "predecessor_ids_json": (
                json.dumps([_extract_id_str(i) for i in raw["predecessor_ids"]])
                if raw.get("predecessor_ids")
                else None
            ),
            "successor_ids_json": (
                json.dumps([_extract_id_str(i) for i in raw["successor_ids"]])
                if raw.get("successor_ids")
                else None
            ),
            "is_deprecated": 1 if entity.is_deprecated else 0,
            "superseded_by": (
                entity.tombstone.superseded_by.value
                if entity.tombstone and entity.tombstone.superseded_by
                else None
            ),
            "notes_json": json.dumps(raw["notes"]) if raw.get("notes") else None,
            "created_at": entity.created_at.value,
            "updated_at": entity.updated_at.value,
        }

    def from_row(self, row: sqlite3.Row | dict[str, Any]) -> Location:
        """Hydrate Location entity from locations table row."""
        try:
            data = dict(row)
            pid_str = _extract_id_str(data.get("parent_id"))
            sup_str = _extract_id_str(data.get("superseded_by"))
            is_dep = bool(data.get("is_deprecated", 0))

            raw_assoc = (
                json.loads(data["associated_jurisdiction_ids_json"])
                if data.get("associated_jurisdiction_ids_json")
                else []
            )
            raw_pred = (
                json.loads(data["predecessor_ids_json"])
                if data.get("predecessor_ids_json")
                else []
            )
            raw_succ = (
                json.loads(data["successor_ids_json"])
                if data.get("successor_ids_json")
                else []
            )

            payload: dict[str, Any] = {
                "id": LocationID(_extract_id_str(data["id"]) or ""),
                "canonical_urn": data["canonical_urn"],
                "name": data["name"],
                "category": data["category"],
                "parent_id": LocationID(pid_str) if pid_str else None,
                "is_primary_local_authority": bool(
                    data.get("is_primary_local_authority", 0)
                ),
                "is_unincorporated": bool(data.get("is_unincorporated", 0)),
                "coordinates": (
                    json.loads(data["coordinates_json"])
                    if data.get("coordinates_json")
                    else None
                ),
                "period": json.loads(data["period_json"])
                if data.get("period_json")
                else None,
                "historical_names": (
                    json.loads(data["historical_names_json"])
                    if data.get("historical_names_json")
                    else []
                ),
                "alternate_names": (
                    json.loads(data["alternate_names_json"])
                    if data.get("alternate_names_json")
                    else []
                ),
                "associated_jurisdiction_ids": [
                    LocationID(_extract_id_str(jid) or "") for jid in raw_assoc
                ],
                "predecessor_ids": [
                    LocationID(_extract_id_str(pid) or "") for pid in raw_pred
                ],
                "successor_ids": [
                    LocationID(_extract_id_str(sid) or "") for sid in raw_succ
                ],
                "audit": {
                    "created_at": IsoTimestamp(data["created_at"]),
                    "updated_at": IsoTimestamp(data["updated_at"]),
                },
                "tombstone": {
                    "is_deprecated": is_dep,
                    "deprecated_at": IsoTimestamp(data["updated_at"])
                    if is_dep
                    else None,
                    "superseded_by": LocationID(sup_str) if sup_str else None,
                },
                "notes": json.loads(data["notes_json"])
                if data.get("notes_json")
                else [],
            }
            return self._adapter.validate_python(payload)
        except Exception as err:
            raise EntityMappingError(
                f"Failed to map row to Location: {err}",
                details={"entity": "Location", "error": str(err)},
            ) from err


class SiteRowMapper(BaseRowMapper[Site]):
    """Bidirectional row mapper for Site domain entities."""

    def __init__(self) -> None:
        """Initialize SiteRowMapper."""
        super().__init__(Site)

    def to_row(self, entity: Site) -> dict[str, Any]:
        """Project Site entity into sites table row parameters."""
        raw = self._adapter.dump_python(entity, mode="json")
        return {
            "id": entity.id.value,
            "canonical_urn": entity.canonical_urn,
            "name": entity.name,
            "category": entity.category.value,
            "location_id": entity.location_id.value,
            "is_active": 1 if entity.is_active else 0,
            "address_json": json.dumps(raw["address"]) if raw.get("address") else None,
            "coordinates_json": (
                json.dumps(raw["coordinates"]) if raw.get("coordinates") else None
            ),
            "period_json": json.dumps(raw["period"]) if raw.get("period") else None,
            "historical_names_json": (
                json.dumps(raw["historical_names"])
                if raw.get("historical_names")
                else None
            ),
            "alternate_names_json": (
                json.dumps(raw["alternate_names"])
                if raw.get("alternate_names")
                else None
            ),
            "is_deprecated": 1 if entity.is_deprecated else 0,
            "superseded_by": (
                entity.tombstone.superseded_by.value
                if entity.tombstone and entity.tombstone.superseded_by
                else None
            ),
            "notes_json": json.dumps(raw["notes"]) if raw.get("notes") else None,
            "created_at": entity.created_at.value,
            "updated_at": entity.updated_at.value,
        }

    def from_row(self, row: sqlite3.Row | dict[str, Any]) -> Site:
        """Hydrate Site entity from sites table row."""
        try:
            data = dict(row)
            sup_str = _extract_id_str(data.get("superseded_by"))
            loc_str = _extract_id_str(data["location_id"]) or ""
            is_dep = bool(data.get("is_deprecated", 0))

            payload: dict[str, Any] = {
                "id": SiteID(_extract_id_str(data["id"]) or ""),
                "canonical_urn": data["canonical_urn"],
                "name": data["name"],
                "category": data["category"],
                "location_id": LocationID(loc_str),
                "is_active": bool(data.get("is_active", 1)),
                "address": json.loads(data["address_json"])
                if data.get("address_json")
                else None,
                "coordinates": (
                    json.loads(data["coordinates_json"])
                    if data.get("coordinates_json")
                    else None
                ),
                "period": json.loads(data["period_json"])
                if data.get("period_json")
                else None,
                "historical_names": (
                    json.loads(data["historical_names_json"])
                    if data.get("historical_names_json")
                    else []
                ),
                "alternate_names": (
                    json.loads(data["alternate_names_json"])
                    if data.get("alternate_names_json")
                    else []
                ),
                "audit": {
                    "created_at": IsoTimestamp(data["created_at"]),
                    "updated_at": IsoTimestamp(data["updated_at"]),
                },
                "tombstone": {
                    "is_deprecated": is_dep,
                    "deprecated_at": IsoTimestamp(data["updated_at"])
                    if is_dep
                    else None,
                    "superseded_by": SiteID(sup_str) if sup_str else None,
                },
                "notes": json.loads(data["notes_json"])
                if data.get("notes_json")
                else [],
            }
            return self._adapter.validate_python(payload)
        except Exception as err:
            raise EntityMappingError(
                f"Failed to map row to Site: {err}",
                details={"entity": "Site", "error": str(err)},
            ) from err


class IndividualRowMapper(BaseRowMapper[Individual]):
    """Bidirectional row mapper for Individual domain entities."""

    def __init__(self) -> None:
        """Initialize IndividualRowMapper."""
        super().__init__(Individual)

    def to_row(self, entity: Individual) -> dict[str, Any]:
        """Project Individual entity into individuals table row parameters."""
        raw = self._adapter.dump_python(entity, mode="json")

        birth_date_sort = None
        if entity.birth_date is not None:
            birth_date_sort = (
                entity.birth_date.start_date.date.value
                if hasattr(entity.birth_date, "start_date")
                else entity.birth_date.date.value
            )

        death_date_sort = None
        if entity.death_date is not None:
            death_date_sort = (
                entity.death_date.start_date.date.value
                if hasattr(entity.death_date, "start_date")
                else entity.death_date.date.value
            )

        return {
            "id": entity.id.value,
            "canonical_urn": entity.canonical_urn,
            "raw_name": entity.name.raw_name,
            "given_name": entity.name.given,
            "middle_name": entity.name.middle,
            "surname": entity.name.surname,
            "suffix": entity.name.suffix,
            "maiden_name": entity.name.maiden_name,
            "sex": entity.sex,
            "is_deceased": 1 if entity.is_deceased else 0,
            "birth_year": entity.birth_year,
            "birth_date_sort": birth_date_sort,
            "birth_date_json": (
                json.dumps(raw["birth_date"]) if raw.get("birth_date") else None
            ),
            "death_year": entity.death_year,
            "death_date_sort": death_date_sort,
            "death_date_json": (
                json.dumps(raw["death_date"]) if raw.get("death_date") else None
            ),
            "birth_place_id": (
                entity.birth_place_id.value if entity.birth_place_id else None
            ),
            "death_place_id": (
                entity.death_place_id.value if entity.death_place_id else None
            ),
            "historical_names_json": (
                json.dumps(raw["historical_names"])
                if raw.get("historical_names")
                else None
            ),
            "alternate_names_json": (
                json.dumps(raw["alternate_names"])
                if raw.get("alternate_names")
                else None
            ),
            "is_deprecated": 1 if entity.is_deprecated else 0,
            "superseded_by": (
                entity.tombstone.superseded_by.value
                if entity.tombstone and entity.tombstone.superseded_by
                else None
            ),
            "notes_json": json.dumps(raw["notes"]) if raw.get("notes") else None,
            "created_at": entity.created_at.value,
            "updated_at": entity.updated_at.value,
        }

    def from_row(self, row: sqlite3.Row | dict[str, Any]) -> Individual:
        """Hydrate Individual entity from individuals table row."""
        try:
            data = dict(row)
            name_obj: dict[str, Any] = {
                "raw_name": data["raw_name"],
                "given": data.get("given_name"),
                "middle": data.get("middle_name"),
                "surname": data.get("surname"),
                "suffix": data.get("suffix"),
                "maiden_name": data.get("maiden_name"),
            }
            b_place = _extract_id_str(data.get("birth_place_id"))
            bp = (
                LocationID(b_place)
                if b_place and b_place.startswith("LOC")
                else (SiteID(b_place) if b_place else None)
            )

            d_place = _extract_id_str(data.get("death_place_id"))
            dp = (
                LocationID(d_place)
                if d_place and d_place.startswith("LOC")
                else (SiteID(d_place) if d_place else None)
            )

            sup_str = _extract_id_str(data.get("superseded_by"))
            is_dep = bool(data.get("is_deprecated", 0))

            payload: dict[str, Any] = {
                "id": IndividualID(_extract_id_str(data["id"]) or ""),
                "name": name_obj,
                "canonical_urn": data["canonical_urn"],
                "sex": data.get("sex", "U"),
                "is_deceased": bool(data.get("is_deceased", 1)),
                "birth_date": (
                    json.loads(data["birth_date_json"])
                    if data.get("birth_date_json")
                    else None
                ),
                "death_date": (
                    json.loads(data["death_date_json"])
                    if data.get("death_date_json")
                    else None
                ),
                "birth_place_id": bp,
                "death_place_id": dp,
                "historical_names": (
                    json.loads(data["historical_names_json"])
                    if data.get("historical_names_json")
                    else []
                ),
                "alternate_names": (
                    json.loads(data["alternate_names_json"])
                    if data.get("alternate_names_json")
                    else []
                ),
                "audit": {
                    "created_at": IsoTimestamp(data["created_at"]),
                    "updated_at": IsoTimestamp(data["updated_at"]),
                },
                "tombstone": {
                    "is_deprecated": is_dep,
                    "deprecated_at": IsoTimestamp(data["updated_at"])
                    if is_dep
                    else None,
                    "superseded_by": IndividualID(sup_str) if sup_str else None,
                },
                "notes": json.loads(data["notes_json"])
                if data.get("notes_json")
                else [],
            }
            return self._adapter.validate_python(payload)
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
        raw = self._adapter.dump_python(entity, mode="json")
        return {
            "id": entity.id.value,
            "canonical_urn": entity.canonical_urn,
            "union_json": json.dumps(raw["union"]),
            "partner_ids_json": json.dumps(
                [_extract_id_str(pid) for pid in raw.get("partner_ids", [])]
            ),
            "children_json": json.dumps(raw["children"]),
            "is_deprecated": 1 if entity.is_deprecated else 0,
            "superseded_by": (
                entity.tombstone.superseded_by.value
                if entity.tombstone and entity.tombstone.superseded_by
                else None
            ),
            "notes_json": json.dumps(raw["notes"]) if raw.get("notes") else None,
            "created_at": entity.created_at.value,
            "updated_at": entity.updated_at.value,
        }

    def from_row(self, row: sqlite3.Row | dict[str, Any]) -> Family:
        """Hydrate Family entity from families table row."""
        try:
            data = dict(row)
            sup_str = _extract_id_str(data.get("superseded_by"))
            is_dep = bool(data.get("is_deprecated", 0))
            raw_partners = (
                json.loads(data["partner_ids_json"])
                if data.get("partner_ids_json")
                else []
            )

            payload: dict[str, Any] = {
                "id": FamilyID(_extract_id_str(data["id"]) or ""),
                "canonical_urn": data["canonical_urn"],
                "union": json.loads(data["union_json"]),
                "partner_ids": [
                    IndividualID(_extract_id_str(pid) or "") for pid in raw_partners
                ],
                "children": json.loads(data["children_json"]),
                "audit": {
                    "created_at": IsoTimestamp(data["created_at"]),
                    "updated_at": IsoTimestamp(data["updated_at"]),
                },
                "tombstone": {
                    "is_deprecated": is_dep,
                    "deprecated_at": IsoTimestamp(data["updated_at"])
                    if is_dep
                    else None,
                    "superseded_by": FamilyID(sup_str) if sup_str else None,
                },
                "notes": json.loads(data["notes_json"])
                if data.get("notes_json")
                else [],
            }
            return self._adapter.validate_python(payload)
        except Exception as err:
            raise EntityMappingError(
                f"Failed to map row to Family: {err}",
                details={"entity": "Family", "error": str(err)},
            ) from err


class FactRowMapper(BaseRowMapper[Fact]):
    """Bidirectional row mapper for Fact domain entities."""

    def __init__(self) -> None:
        """Initialize FactRowMapper."""
        super().__init__(Fact)

    def to_row(self, entity: Fact) -> dict[str, Any]:
        """Project Fact entity into facts table row parameters."""
        raw = self._adapter.dump_python(entity, mode="json")

        fact_date_sort = None
        if entity.date is not None:
            fact_date_sort = (
                entity.date.date.value
                if hasattr(entity.date, "date")
                else entity.date.start_date.date.value
            )

        fact_year = _extract_year_from_text(fact_date_sort)

        return {
            "id": entity.id.value,
            "canonical_urn": entity.canonical_urn,
            "fact_type": entity.fact_type.value,
            "title": entity.title,
            "primary_subject_id": entity.primary_subject_id.value,
            "fact_year": fact_year,
            "fact_date_sort": fact_date_sort,
            "date_json": json.dumps(raw["date"]) if raw.get("date") else None,
            "location_id": entity.location_id.value if entity.location_id else None,
            "site_id": entity.site_id.value if entity.site_id else None,
            "value": entity.value,
            "description": entity.description,
            "narrative": entity.narrative,
            "participants_json": (
                json.dumps(raw["participants"]) if raw.get("participants") else None
            ),
            "citations_json": (
                json.dumps(raw["citations"]) if raw.get("citations") else None
            ),
            "is_deprecated": 1 if entity.is_deprecated else 0,
            "superseded_by": (
                entity.tombstone.superseded_by.value
                if entity.tombstone and entity.tombstone.superseded_by
                else None
            ),
            "notes_json": json.dumps(raw["notes"]) if raw.get("notes") else None,
            "created_at": entity.created_at.value,
            "updated_at": entity.updated_at.value,
        }

    def from_row(self, row: sqlite3.Row | dict[str, Any]) -> Fact:
        """Hydrate Fact entity from facts table row."""
        try:
            data = dict(row)
            subj = _extract_id_str(data["primary_subject_id"]) or ""
            subj_id = (
                IndividualID(subj)
                if subj.startswith("IND")
                else (FamilyID(subj) if subj.startswith("FAM") else IndividualID(subj))
            )

            loc_str = _extract_id_str(data.get("location_id"))
            site_str = _extract_id_str(data.get("site_id"))
            sup_str = _extract_id_str(data.get("superseded_by"))
            is_dep = bool(data.get("is_deprecated", 0))

            payload: dict[str, Any] = {
                "id": FactID(_extract_id_str(data["id"]) or ""),
                "canonical_urn": data["canonical_urn"],
                "fact_type": data["fact_type"],
                "title": data["title"],
                "primary_subject_id": subj_id,
                "date": json.loads(data["date_json"])
                if data.get("date_json")
                else None,
                "location_id": LocationID(loc_str) if loc_str else None,
                "site_id": SiteID(site_str) if site_str else None,
                "value": data.get("value"),
                "description": data.get("description"),
                "narrative": data.get("narrative"),
                "participants": (
                    json.loads(data["participants_json"])
                    if data.get("participants_json")
                    else []
                ),
                "citations": (
                    json.loads(data["citations_json"])
                    if data.get("citations_json")
                    else []
                ),
                "audit": {
                    "created_at": IsoTimestamp(data["created_at"]),
                    "updated_at": IsoTimestamp(data["updated_at"]),
                },
                "tombstone": {
                    "is_deprecated": is_dep,
                    "deprecated_at": IsoTimestamp(data["updated_at"])
                    if is_dep
                    else None,
                    "superseded_by": FactID(sup_str) if sup_str else None,
                },
                "notes": json.loads(data["notes_json"])
                if data.get("notes_json")
                else [],
            }
            return self._adapter.validate_python(payload)
        except Exception as err:
            raise EntityMappingError(
                f"Failed to map row to Fact: {err}",
                details={"entity": "Fact", "error": str(err)},
            ) from err


_REGISTRY: dict[type[Any], BaseRowMapper[Any]] = {
    Location: LocationRowMapper(),
    Site: SiteRowMapper(),
    Individual: IndividualRowMapper(),
    Family: FamilyRowMapper(),
    Fact: FactRowMapper(),
}


def get_mapper[T](entity_cls: type[T]) -> BaseRowMapper[T]:
    """Retrieve the registered BaseRowMapper for a domain entity class.

    Args:
        entity_cls: Domain entity class (Location, Site, Individual, Family, Fact).

    Returns:
        Configured BaseRowMapper instance.

    Raises:
        EntityMappingError: If entity_cls is not registered.
    """
    if entity_cls not in _REGISTRY:
        raise EntityMappingError(
            f"No registered row mapper for domain class '{entity_cls.__name__}'.",
            details={"entity_class": entity_cls.__name__},
        )
    return _REGISTRY[entity_cls]
