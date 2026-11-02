"""Path: src/gda/entity/locations/util.py

Authoritative jurisdictional hierarchy construction, graveyard lifecycle, and persistence.

Operational Role:
    Provides collection-level jurisdiction hierarchy builders, safe tombstone
    and graveyard lifecycle operators, and SQLite/filesystem persistence routines
    operating on Locations instances. Delegates low-level text cleaning, URN slugging,
    and ID minting to gda.util.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import TYPE_CHECKING, Any

from gda.core.errors import ModelFormatError
from gda.entity.locations.errors import LocationHierarchyError
from gda.enums.core import SmartIDPrefix
from gda.enums.location import JurisdictionCategory
from gda.enums.vital import HistoricNameType
from gda.io.json import GDAJsonIO
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import LocationID
from gda.model.base.audit import AuditStamp
from gda.model.base.name import NameThing
from gda.model.base.note import Note
from gda.model.base.tombstone import Tombstone
from gda.model.entity.location import Location
from gda.util.ids import extract_max_smart_id, mint_smart_id
from gda.util.text import clean_string, slugify
from gda.util.tombstone import stamp_tombstone

if TYPE_CHECKING:
    from gda.entity.locations.collection import Locations

__version__ = "1.0.0+build.39"

__all__ = [
    "build_jurisdiction_hierarchy",
    "can_tombstone",
    "clean_string",
    "export_file",
    "import_file",
    "load_from_db",
    "save_to_db",
    "slugify",
    "tombstone_location",
]


def _slugify_segment(val: str) -> str:
    """Delegate to gda.util.text.slugify configured for single URN path segments."""
    return slugify(val, delimiter="_")


def _get_or_create_node(
    collection: Locations,
    name: str,
    category: JurisdictionCategory,
    canonical_urn: str,
    parent_id: LocationID | None = None,
    is_primary_local_authority: bool = False,
    is_unincorporated: bool = False,
) -> Location:
    """Retrieve an existing location by URN or mint, create, and register a new Location."""
    existing = collection.get(canonical_urn)
    if existing:
        return existing

    next_num = (
        extract_max_smart_id(collection._registry.keys(), prefix=SmartIDPrefix.LOC) + 1
    )
    loc_id = LocationID(mint_smart_id(SmartIDPrefix.LOC, next_num))

    now = IsoTimestamp.now_utc()
    name_obj = NameThing.create(raw=name, canonical=name)

    loc = Location.create(
        location_id=loc_id,
        audit=AuditStamp(created_at=now, updated_at=now),
        name=name_obj,
        category=category,
        canonical_urn=canonical_urn,
        parent_id=parent_id,
        is_primary_local_authority=is_primary_local_authority,
        is_unincorporated=is_unincorporated,
        notes=[],
        tombstone=Tombstone[LocationID](),
    )
    collection.add(loc)
    return loc


def build_jurisdiction_hierarchy(
    collection: Locations,
    country: str,
    state: str | None = None,
    county: str | None = None,
    township: str | None = None,
    local: str | None = None,
) -> Location:
    """Build or resolve descending jurisdictional tiers enforcing structural rules."""
    c = clean_string(country)
    s = clean_string(state)
    co = clean_string(county)
    twp = clean_string(township)
    loc = clean_string(local)

    if not c:
        raise ModelFormatError("Location hierarchy must contain a country.")
    if (co or twp or loc) and not s:
        raise ModelFormatError("Cannot attach sub-tiers to country without state.")
    if twp and not co:
        raise ModelFormatError("Cannot attach township without county.")

    c_urn = f"urn:gda:loc:{_slugify_segment(c)}"
    c_loc = _get_or_create_node(
        collection=collection,
        name=c,
        category=JurisdictionCategory.COUNTRY,
        canonical_urn=c_urn,
    )

    if not s:
        return c_loc

    s_urn = f"{c_loc.canonical_urn}:{_slugify_segment(s)}"
    s_loc = _get_or_create_node(
        collection=collection,
        name=s,
        category=JurisdictionCategory.STATOID,
        canonical_urn=s_urn,
        parent_id=c_loc.id,
    )

    if not co:
        if loc:
            loc_urn = f"{s_loc.canonical_urn}:{_slugify_segment(loc)}"
            return _get_or_create_node(
                collection=collection,
                name=loc,
                category=JurisdictionCategory.MUNICIPALITY,
                canonical_urn=loc_urn,
                parent_id=s_loc.id,
            )
        return s_loc

    co_urn = f"{s_loc.canonical_urn}:{_slugify_segment(co)}"
    co_loc = _get_or_create_node(
        collection=collection,
        name=co,
        category=JurisdictionCategory.COUNTY_EQUIVALENT,
        canonical_urn=co_urn,
        parent_id=s_loc.id,
    )

    if not twp:
        if loc:
            loc_urn = f"{co_loc.canonical_urn}:{_slugify_segment(loc)}"
            return _get_or_create_node(
                collection=collection,
                name=loc,
                category=JurisdictionCategory.MUNICIPALITY,
                canonical_urn=loc_urn,
                parent_id=co_loc.id,
            )
        return co_loc

    twp_urn = f"{co_loc.canonical_urn}:{_slugify_segment(twp)}"
    twp_loc = _get_or_create_node(
        collection=collection,
        name=twp,
        category=JurisdictionCategory.CIVIL_TOWNSHIP,
        canonical_urn=twp_urn,
        parent_id=co_loc.id,
        is_primary_local_authority=True,
    )

    if not loc:
        return twp_loc

    loc_urn = f"{twp_loc.canonical_urn}:{_slugify_segment(loc)}"
    return _get_or_create_node(
        collection=collection,
        name=loc,
        category=JurisdictionCategory.MUNICIPALITY,
        canonical_urn=loc_urn,
        parent_id=twp_loc.id,
    )


def can_tombstone(
    collection: Locations,
    loc_id: LocationID | str,
    superseded_by: LocationID | str | None = None,
) -> tuple[bool, str | None]:
    """Verify whether an entity can be safely retired without violating graph integrity."""
    target_id = LocationID(str(loc_id))
    target = collection._registry.get(target_id)
    if not target:
        return False, f"Location '{target_id}' does not exist in collection."

    if target.tombstone.is_deprecated:
        return False, f"Location '{target_id}' is already tombstoned."

    active_children = [
        child.id
        for child in collection
        if child.parent_id == target_id and not child.tombstone.is_deprecated
    ]

    if active_children and not superseded_by:
        children_preview = ", ".join(str(cid) for cid in active_children[:3])
        if len(active_children) > 3:
            children_preview += f", ... ({len(active_children)} total)"
        return (
            False,
            f"Cannot tombstone location '{target_id}' because it has active child "
            f"jurisdictions [{children_preview}] and no replacement 'superseded_by' was specified.",
        )

    if superseded_by:
        replacement_id = LocationID(str(superseded_by))
        if replacement_id == target_id:
            return (
                False,
                f"Replacement entity '{replacement_id}' cannot be the entity itself.",
            )

        replacement = collection._registry.get(replacement_id)
        if not replacement:
            return (
                False,
                f"Replacement entity '{replacement_id}' does not exist in collection.",
            )

        if replacement.tombstone.is_deprecated:
            return (
                False,
                f"Replacement entity '{replacement_id}' is itself tombstoned.",
            )

        if replacement.category != target.category:
            return (
                False,
                f"Replacement entity '{replacement_id}' [{replacement.category.value}] "
                f"must match the jurisdiction tier of target '{target_id}' [{target.category.value}].",
            )

    return True, None


def tombstone_location(
    collection: Locations,
    loc_id: LocationID | str,
    reason: str,
    superseded_by: LocationID | str | None = None,
) -> Location:
    """Atomically retire an entity, reparent active children if needed, and update registry."""
    ok, error_msg = can_tombstone(
        collection=collection,
        loc_id=loc_id,
        superseded_by=superseded_by,
    )
    if not ok:
        raise LocationHierarchyError(error_msg or "Cannot tombstone location.")

    target_id = LocationID(str(loc_id))
    target = collection._registry[target_id]
    replacement_id = LocationID(str(superseded_by)) if superseded_by else None

    if replacement_id:
        active_children = [
            child
            for child in collection
            if child.parent_id == target_id and not child.tombstone.is_deprecated
        ]
        for child in active_children:
            reparented = dataclasses.replace(child, parent_id=replacement_id)
            collection._registry[reparented.id] = reparented

    retired = stamp_tombstone(
        entity=target,
        reason=reason,
        superseded_by=replacement_id,
    )

    collection._registry[retired.id] = retired
    return retired


def load_from_db(collection: Locations) -> int:
    """Load all location records from the SQLite database directly into the collection."""
    from gda.db.mapper import LocationRowMapper
    from gda.db.schema import SchemaManager
    from gda.db.session import DatabaseSessionManager

    session = DatabaseSessionManager()
    schema_mgr = SchemaManager(session_manager=session)
    schema_mgr.init_db()

    mapper = LocationRowMapper()
    loaded_count = 0

    with session.get_connection() as conn:
        cursor = conn.execute("SELECT * FROM locations ORDER BY id")
        for row in cursor.fetchall():
            entity = mapper.from_row(row)
            collection.add(entity)
            loaded_count += 1

    collection.mark_clean()
    return loaded_count


def save_to_db(collection: Locations) -> int:
    """Commit collection entities to the SQLite database and mark the collection clean."""
    from gda.db.mapper import LocationRowMapper
    from gda.db.schema import SchemaManager
    from gda.db.session import DatabaseSessionManager

    session = DatabaseSessionManager()
    schema_mgr = SchemaManager(session_manager=session)
    schema_mgr.init_db()

    mapper = LocationRowMapper()
    written = 0

    with session.transaction() as tx:
        for entity in collection.iter_all():
            row_dict = mapper.to_row(entity)
            columns = ", ".join(row_dict.keys())
            placeholders = ", ".join(f":{k}" for k in row_dict)
            tx.execute(
                f"INSERT OR REPLACE INTO locations ({columns}) VALUES ({placeholders})",
                row_dict,
            )
            written += 1

    collection.mark_clean()
    return written


def import_file(collection: Locations, path: Path | str) -> int:
    """Import locations from formatted JSON file, load into memory, and save to database."""
    json_path = Path(path)
    if not json_path.exists():
        return 0

    payload = GDAJsonIO.read(json_path)
    locations_list = payload.get("locations", [])
    now = IsoTimestamp.now_utc()

    for item in locations_list:
        loc_id = LocationID(item["id"])
        parent_id = LocationID(item["parent_id"]) if item.get("parent_id") else None

        raw_name_val = item.get("name", "")
        if isinstance(raw_name_val, dict):
            name_obj = NameThing.from_dict(raw_name_val)
        else:
            raw_clean = str(raw_name_val).strip()
            name_obj = NameThing.create(raw=raw_clean, canonical=raw_clean)

        raw_historical = item.get("historical_names", [])
        if raw_historical:
            existing_variants = {
                (h.raw, h.name, h.historic_name_type) for h in name_obj.historic
            }
            for h in raw_historical:
                if isinstance(h, dict):
                    h_raw = h.get("raw") or h.get("raw_name", "")
                    h_canonical = h.get("canonical") or h.get("canonical_name", h_raw)
                    h_type_raw = h.get("historic_name_type") or h.get(
                        "status", HistoricNameType.HISTORICAL
                    )
                    h_type = (
                        h_type_raw
                        if isinstance(h_type_raw, HistoricNameType)
                        else HistoricNameType(h_type_raw)
                    )
                    if (h_raw, h_canonical, h_type) not in existing_variants:
                        name_obj = name_obj.add_historic_variant(
                            raw=h_raw,
                            name=h_canonical,
                            historic_name_type=h_type,
                        )
                        existing_variants.add((h_raw, h_canonical, h_type))

        raw_aliases = item.get("alternate_names") or item.get("aliases") or []
        for alias in raw_aliases:
            clean_alias = clean_string(alias)
            if clean_alias and clean_alias not in name_obj.aliases:
                name_obj = name_obj.add_alias(clean_alias)

        raw_notes = item.get("notes", [])
        embedded_notes: list[Note] = []
        for n in raw_notes:
            if isinstance(n, Note):
                embedded_notes.append(n)
            elif isinstance(n, dict):
                embedded_notes.append(Note.from_dict(n))

        loc = Location.create(
            location_id=loc_id,
            audit=AuditStamp(created_at=now, updated_at=now),
            name=name_obj,
            category=JurisdictionCategory(item["category"]),
            canonical_urn=item["canonical_urn"],
            parent_id=parent_id,
            is_primary_local_authority=item.get("is_primary_local_authority", False),
            is_unincorporated=item.get("is_unincorporated", False),
            notes=embedded_notes,
            tombstone=Tombstone[LocationID](),
        )
        collection.add(loc)

    return len(locations_list)


def export_file(
    collection: Locations,
    path: Path | str,
    include_graveyard: bool = True,
) -> int:
    """Export location records from the collection to a formatted JSON file."""
    entities = list(collection.iter_all() if include_graveyard else collection)
    out_list: list[dict[str, Any]] = []

    for e in entities:
        hist_list = [
            {
                "raw": h.raw,
                "canonical": h.name,
                "historic_name_type": h.historic_name_type.value,
            }
            for h in e.name.historic
        ]
        notes_list = [n.to_dict() for n in e.notes]

        item: dict[str, Any] = {
            "id": str(e.id),
            "name": e.name.to_dict(),
            "category": e.category.value,
            "canonical_urn": e.canonical_urn,
            "parent_id": str(e.parent_id) if e.parent_id else None,
            "is_primary_local_authority": e.is_primary_local_authority,
            "is_unincorporated": e.is_unincorporated,
            "alternate_names": list(e.aliases),
            "historical_names": hist_list,
            "notes": notes_list,
        }
        out_list.append(item)

    payload = {
        "schema_version": "1.0.0",
        "record_type": "location_export",
        "total_count": len(out_list),
        "locations": out_list,
    }

    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    GDAJsonIO.write(dest, payload)
    return len(out_list)
