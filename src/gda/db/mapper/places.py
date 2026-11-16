"""Path: src/gda/db/mapper/places.py

Bidirectional SQLite row mappers for Location and Site place entities.

Operational Role:
    Translates Location and Site domain models to and from flattened analytical
    rows in the locations and sites tables.
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from gda.core.enums.location import JurisdictionCategory
from gda.core.enums.site import SiteType
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
from gda.model.atom.geo import Latitude, Longitude
from gda.model.atom.id import LocationID, SiteID
from gda.model.base.address import Address
from gda.model.base.audit import AuditStamp
from gda.model.base.date import TimePeriod
from gda.model.base.geo import Coordinates
from gda.model.entity.location import Location
from gda.model.entity.site import Site

__version__ = "1.0.0+build.1"

__all__ = [
    "LocationRowMapper",
    "SiteRowMapper",
]


class LocationRowMapper(BaseRowMapper[Location]):
    """Bidirectional row mapper for Location domain entities."""

    def __init__(self) -> None:
        """Initialize LocationRowMapper."""
        super().__init__(Location)

    def to_row(self, entity: Location) -> dict[str, Any]:
        """Project Location entity into locations table row parameters."""
        return {
            "id": entity.id.value,
            "canonical_urn": entity.canonical_urn,
            **_serialize_name_thing(entity.name),
            "category": entity.category.value,
            "parent_id": entity.parent_id.value if entity.parent_id else None,
            "is_primary_local_authority": 1 if entity.is_primary_local_authority else 0,
            "is_unincorporated": 1 if entity.is_unincorporated else 0,
            "latitude": (entity.coordinates.latitude.value if entity.coordinates else None),
            "longitude": (entity.coordinates.longitude.value if entity.coordinates else None),
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

    def from_row(self, row: sqlite3.Row | dict[str, Any]) -> Location:
        """Hydrate Location entity from locations table row."""
        try:
            data = dict(row)
            pid_str = _extract_id_str(data.get("parent_id"))
            tombstone = _deserialize_tombstone(data, LocationID)
            notes_list = _deserialize_notes(data.get("notes_json"))
            name_obj = _deserialize_name_thing(data)

            coords_obj = (
                Coordinates(
                    latitude=Latitude(float(data["latitude"])),
                    longitude=Longitude(float(data["longitude"])),
                )
                if data.get("latitude") is not None and data.get("longitude") is not None
                else None
            )
            period_obj = (
                TimePeriod.from_dict(json.loads(data["period_json"]))
                if data.get("period_json")
                else None
            )
            preds = (
                json.loads(data["predecessor_ids_json"]) if data.get("predecessor_ids_json") else []
            )
            succs = json.loads(data["successor_ids_json"]) if data.get("successor_ids_json") else []

            return Location.create(
                location_id=LocationID(data["id"]),
                name=name_obj,
                category=JurisdictionCategory(data["category"]),
                canonical_urn=data["canonical_urn"],
                audit=AuditStamp(
                    created_at=IsoTimestamp(data["created_at"]),
                    updated_at=IsoTimestamp(data["updated_at"]),
                ),
                tombstone=tombstone,
                notes=notes_list,
                parent_id=LocationID(pid_str) if pid_str else None,
                predecessor_ids=preds,
                successor_ids=succs,
                is_primary_local_authority=bool(data.get("is_primary_local_authority", 0)),
                is_unincorporated=bool(data.get("is_unincorporated", 0)),
                period=period_obj,
                coordinates=coords_obj,
            )
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
        addr = entity.address
        addr_coords = addr.coordinates if addr else None
        return {
            "id": entity.id.value,
            "canonical_urn": entity.canonical_urn,
            **_serialize_name_thing(entity.name),
            "category": entity.category.value,
            "location_id": entity.location_id.value,
            "is_active": 1 if entity.is_active else 0,
            "address_line_1": addr.address_line_1 if addr else None,
            "address_line_2": addr.address_line_2 if addr else None,
            "address_city": addr.city if addr else None,
            "address_state": addr.state if addr else None,
            "address_postal_code": addr.postal_code if addr else None,
            "address_latitude": addr_coords.latitude.value if addr_coords else None,
            "address_longitude": addr_coords.longitude.value if addr_coords else None,
            "latitude": (entity.coordinates.latitude.value if entity.coordinates else None),
            "longitude": (entity.coordinates.longitude.value if entity.coordinates else None),
            "period_json": (
                json.dumps(entity.period.to_dict(), ensure_ascii=False) if entity.period else None
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

    def from_row(self, row: sqlite3.Row | dict[str, Any]) -> Site:
        """Hydrate Site entity from sites table row."""
        try:
            data = dict(row)
            tombstone = _deserialize_tombstone(data, SiteID)
            notes_list = _deserialize_notes(data.get("notes_json"))
            name_obj = _deserialize_name_thing(data)

            addr_obj: Address | None = None
            if data.get("address_line_1"):
                addr_coords = (
                    Coordinates(
                        latitude=Latitude(float(data["address_latitude"])),
                        longitude=Longitude(float(data["address_longitude"])),
                    )
                    if data.get("address_latitude") is not None
                    and data.get("address_longitude") is not None
                    else None
                )
                addr_obj = Address(
                    address_line_1=data["address_line_1"],
                    address_line_2=data.get("address_line_2"),
                    city=data.get("address_city"),
                    state=data.get("address_state"),
                    postal_code=data.get("address_postal_code"),
                    coordinates=addr_coords,
                )

            coords_obj = (
                Coordinates(
                    latitude=Latitude(float(data["latitude"])),
                    longitude=Longitude(float(data["longitude"])),
                )
                if data.get("latitude") is not None and data.get("longitude") is not None
                else None
            )
            period_obj = (
                TimePeriod.from_dict(json.loads(data["period_json"]))
                if data.get("period_json")
                else None
            )

            return Site.create(
                site_id=SiteID(data["id"]),
                name=name_obj,
                category=SiteType(data["category"]),
                canonical_urn=data["canonical_urn"],
                location_id=LocationID(data["location_id"]),
                is_active=bool(data.get("is_active", 1)),
                address=addr_obj,
                coordinates=coords_obj,
                period=period_obj,
                audit=AuditStamp(
                    created_at=IsoTimestamp(data["created_at"]),
                    updated_at=IsoTimestamp(data["updated_at"]),
                ),
                tombstone=tombstone,
                notes=notes_list,
            )
        except Exception as err:
            raise EntityMappingError(
                f"Failed to map row to Site: {err}",
                details={"entity": "Site", "error": str(err)},
            ) from err
