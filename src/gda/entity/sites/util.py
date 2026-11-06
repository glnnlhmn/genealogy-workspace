"""Path: src/gda/entity/sites/util.py

Site persistence, graveyard lifecycle operations, and serialization routines.

Operational Role:
    Provides collection-level site persistence routines using SiteRowMapper,
    import/export routines operating on formatted JSON payloads, and safe
    tombstone/undelete lifecycle operators on Sites collection instances.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from gda.entity.sites.errors import SiteValidationError
from gda.enums.site import SiteType
from gda.enums.vital import HistoricNameType
from gda.io.json import GDAJsonIO
from gda.model.atom.date import EventDate, IsoTimestamp
from gda.model.atom.id import LocationID, SiteID
from gda.model.base.address import Address
from gda.model.base.audit import AuditStamp
from gda.model.base.name import NameThing
from gda.model.base.note import Note
from gda.model.base.time_period import TimePeriod
from gda.model.base.tombstone import Tombstone
from gda.model.entity.site import Site
from gda.util.tombstone import stamp_tombstone

if TYPE_CHECKING:
    from gda.entity.locations.collection import Locations
    from gda.entity.sites.collection import Sites

__version__ = "1.0.0+build.7"

__all__ = [
    "can_tombstone",
    "can_undelete",
    "export_file",
    "import_file",
    "load_from_db",
    "save_to_db",
    "tombstone_site",
    "undelete_site",
]


def _parse_event_date(val: Any) -> EventDate | None:
    """Resolve an incoming raw value to an EventDate or None."""
    if val is None:
        return None
    if isinstance(val, EventDate):
        return val
    if isinstance(val, dict):
        return EventDate.from_dict(val)
    return EventDate.create(str(val))


def _parse_time_period(raw: Any) -> TimePeriod | None:
    """Safely deserialize raw dictionary or object representation into a TimePeriod."""
    if isinstance(raw, TimePeriod):
        return raw
    if not isinstance(raw, dict):
        return None

    start_obj = _parse_event_date(raw.get("start_date"))
    end_obj = _parse_event_date(raw.get("end_date"))

    if start_obj is None and end_obj is None:
        return None

    return TimePeriod(start_date=start_obj, end_date=end_obj)


def _export_coordinates(site: Site) -> dict[str, float] | None:
    """Extract coordinates mapping if defined on the site."""
    if site.coordinates is None:
        return None
    return {
        "latitude": site.coordinates.latitude.value,
        "longitude": site.coordinates.longitude.value,
    }


def can_tombstone(
    collection: Sites,
    site_id: SiteID | str,
    superseded_by: SiteID | str | None = None,
) -> tuple[bool, str | None]:
    """Verify whether a site can be safely retired without violating integrity.

    Args:
        collection: In-memory Sites collection.
        site_id: Unique Site identifier to inspect.
        superseded_by: Optional replacement SiteID.

    Returns:
        Tuple of (is_valid, error_message_or_none).
    """
    target_id = SiteID(str(site_id))
    target = collection._registry.get(target_id)
    if not target:
        return False, f"Site '{target_id}' does not exist in collection."

    if target.tombstone.is_deprecated:
        return False, f"Site '{target_id}' is already tombstoned."

    if superseded_by:
        replacement_id = SiteID(str(superseded_by))
        if replacement_id == target_id:
            return False, f"Replacement entity '{replacement_id}' cannot be the entity itself."

        replacement = collection._registry.get(replacement_id)
        if not replacement:
            return False, f"Replacement entity '{replacement_id}' does not exist in collection."

        if replacement.tombstone.is_deprecated:
            return False, f"Replacement entity '{replacement_id}' is itself tombstoned."

    return True, None


def tombstone_site(
    collection: Sites,
    site_id: SiteID | str,
    reason: str,
    superseded_by: SiteID | str | None = None,
) -> Site:
    """Atomically retire a site entity and update the registry.

    Args:
        collection: In-memory Sites collection.
        site_id: Target Site identifier.
        reason: Justification for retirement.
        superseded_by: Optional replacement Site identifier.

    Returns:
        The retired Site instance.

    Raises:
        SiteValidationError: If the site cannot be tombstoned.
    """
    ok, error_msg = can_tombstone(
        collection=collection,
        site_id=site_id,
        superseded_by=superseded_by,
    )
    if not ok:
        raise SiteValidationError(error_msg or "Cannot tombstone site.")

    target_id = SiteID(str(site_id))
    target = collection._registry[target_id]
    replacement_id = SiteID(str(superseded_by)) if superseded_by else None

    retired = stamp_tombstone(
        entity=target,
        reason=reason,
        superseded_by=replacement_id,
    )

    collection._registry[retired.id] = retired
    return retired


def can_undelete(
    collection: Sites,
    site_id: SiteID | str,
    locations_collection: Locations | None = None,
) -> tuple[bool, str | None]:
    """Verify whether a tombstoned site can be safely restored to active status.

    Args:
        collection: In-memory Sites collection.
        site_id: Target Site identifier.
        locations_collection: Optional Locations collection to verify governing jurisdiction.

    Returns:
        Tuple of (is_valid, error_message_or_none).
    """
    target_id = SiteID(str(site_id))
    target = collection._registry.get(target_id)
    if not target:
        return False, f"Site '{target_id}' does not exist in collection."

    if not target.tombstone.is_deprecated:
        return False, f"Site '{target_id}' is not tombstoned."

    if locations_collection is not None:
        if target.location_id not in locations_collection:
            return (
                False,
                f"Cannot undelete site '{target_id}'; governing location "
                f"'{target.location_id}' is missing or tombstoned.",
            )

    return True, None


def undelete_site(
    collection: Sites,
    site_id: SiteID | str,
    locations_collection: Locations | None = None,
) -> Site:
    """Atomically restore a tombstoned site back to active status.

    Args:
        collection: In-memory Sites collection.
        site_id: Target Site identifier.
        locations_collection: Optional Locations collection to verify governing jurisdiction.

    Returns:
        The reactivated Site instance.

    Raises:
        SiteValidationError: If the site cannot be safely undeleted.
    """
    ok, error_msg = can_undelete(
        collection=collection,
        site_id=site_id,
        locations_collection=locations_collection,
    )
    if not ok:
        raise SiteValidationError(error_msg or "Cannot undelete site.")

    target_id = SiteID(str(site_id))
    target = collection._registry[target_id]

    now = IsoTimestamp.now_utc()
    active_site = Site.create(
        site_id=target.id,
        name=target.name,
        category=target.category,
        canonical_urn=target.canonical_urn,
        location_id=target.location_id,
        audit=target.audit.touch(now),
        tombstone=Tombstone[SiteID](),
        notes=list(target.notes),
        address=target.address,
        coordinates=target.coordinates,
        period=target.period,
        is_active=target.is_active,
    ).mark_dirty()

    collection._registry[active_site.id] = active_site
    return active_site


def load_from_db(collection: Sites) -> int:
    """Load all site records from the SQLite database directly into the collection.

    Args:
        collection: In-memory Sites collection to populate.

    Returns:
        Count of site records loaded.
    """
    from gda.db.mapper import SiteRowMapper
    from gda.db.schema import SchemaManager
    from gda.db.session import DatabaseSessionManager

    session = DatabaseSessionManager()
    schema_mgr = SchemaManager(session_manager=session)
    schema_mgr.init_db()

    mapper = SiteRowMapper()
    loaded_count = 0

    with session.get_connection() as conn:
        cursor = conn.execute("SELECT * FROM sites ORDER BY id")
        for row in cursor.fetchall():
            entity = mapper.from_row(row)
            collection.add(entity)
            loaded_count += 1

    collection.mark_clean()
    return loaded_count


def save_to_db(collection: Sites) -> int:
    """Commit collection entities to the SQLite database and mark the collection clean.

    Args:
        collection: In-memory Sites collection to persist.

    Returns:
        Count of records written.
    """
    from gda.db.mapper import SiteRowMapper
    from gda.db.schema import SchemaManager
    from gda.db.session import DatabaseSessionManager

    session = DatabaseSessionManager()
    schema_mgr = SchemaManager(session_manager=session)
    schema_mgr.init_db()

    mapper = SiteRowMapper()
    written = 0

    with session.transaction() as tx:
        for entity in collection.iter_all():
            row_dict = mapper.to_row(entity)
            columns = ", ".join(row_dict.keys())
            placeholders = ", ".join(f":{k}" for k in row_dict)
            tx.execute(
                f"INSERT OR REPLACE INTO sites ({columns}) VALUES ({placeholders})",
                row_dict,
            )
            written += 1

    collection.mark_clean()
    return written


def import_file(collection: Sites, path: Path | str) -> int:
    """Import sites from a formatted JSON file, load into memory, and add to collection.

    Args:
        collection: In-memory Sites collection.
        path: Path to the JSON source file.

    Returns:
        Count of site entities successfully imported.
    """
    json_path = Path(path)
    if not json_path.exists():
        return 0

    payload = GDAJsonIO.read(json_path)
    sites_list = payload.get("sites", [])
    now = IsoTimestamp.now_utc()

    for item in sites_list:
        site_id = SiteID(item["id"])
        location_id = LocationID(item["location_id"])

        raw_name_val = item.get("name", "")
        if isinstance(raw_name_val, dict):
            name_obj = NameThing.from_dict(raw_name_val)
        else:
            name_obj = NameThing.create(raw=str(raw_name_val), canonical=str(raw_name_val))

        raw_historical = item.get("historical_names", [])
        if raw_historical:
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
                    name_obj = name_obj.add_historic_variant(
                        raw=h_raw,
                        name=h_canonical,
                        historic_name_type=h_type,
                    )

        for alias in item.get("alternate_names") or item.get("aliases") or []:
            name_obj = name_obj.add_alias(alias)

        embedded_notes: list[Note] = []
        for n in item.get("notes", []):
            if isinstance(n, Note):
                embedded_notes.append(n)
            else:
                embedded_notes.append(Note.from_dict(n))

        raw_addr = item.get("address")
        addr_obj = Address.from_dict(raw_addr) if isinstance(raw_addr, dict) else None
        period_obj = _parse_time_period(item.get("period"))

        site = Site.create(
            site_id=site_id,
            audit=AuditStamp(created_at=now, updated_at=now),
            name=name_obj,
            category=SiteType(item["category"]),
            canonical_urn=item["canonical_urn"],
            location_id=location_id,
            address=addr_obj,
            period=period_obj,
            is_active=item.get("is_active", True),
            notes=embedded_notes,
            tombstone=Tombstone[SiteID](),
        )
        collection.add(site)

    return len(sites_list)


def export_file(
    collection: Sites,
    path: Path | str,
    include_graveyard: bool = True,
) -> int:
    """Export site records from the collection to a formatted JSON file.

    Args:
        collection: In-memory Sites collection.
        path: Destination filesystem path.
        include_graveyard: True to include tombstoned records in output.

    Returns:
        Count of site records exported.
    """
    entities = list(collection.iter_all() if include_graveyard else collection)
    out_list: list[dict[str, Any]] = []

    for s in entities:
        hist_list = [
            {
                "raw": h.raw,
                "canonical": h.name,
                "historic_name_type": h.historic_name_type.value,
            }
            for h in s.name.historic
        ]
        notes_list = [n.to_dict() for n in s.notes]

        item: dict[str, Any] = {
            "id": str(s.id),
            "name": s.name.to_dict(),
            "category": s.category.value,
            "canonical_urn": s.canonical_urn,
            "location_id": str(s.location_id),
            "is_active": s.is_active,
            "address": s.address.to_dict() if s.address else None,
            "coordinates": _export_coordinates(s),
            "period": (
                {
                    "start_date": str(s.period.start_date) if s.period.start_date else None,
                    "end_date": str(s.period.end_date) if s.period.end_date else None,
                }
                if s.period
                else None
            ),
            "alternate_names": list(s.aliases),
            "historical_names": hist_list,
            "notes": notes_list,
        }
        out_list.append(item)

    payload = {
        "schema_version": "1.0.0",
        "record_type": "site_export",
        "total_count": len(out_list),
        "sites": out_list,
    }

    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    GDAJsonIO.write(dest, payload)
    return len(out_list)
