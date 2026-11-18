"""Path: src/gda/entity/organizations/util.py

Organization persistence, graveyard lifecycle operations, and serialization routines.

Operational Role:
    Provides collection-level organization persistence routines using
    OrganizationRowMapper, import/export routines operating on formatted JSON
    payloads (preserving audit and tombstone state), and safe tombstone/undelete
    lifecycle operators on Organizations collection instances.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import TYPE_CHECKING, Any

from gda.core.dates import utc_now_iso
from gda.core.enums.orgs import OrganizationCategory
from gda.core.enums.vital import HistoricNameType
from gda.entity.organizations.errors import (
    OrganizationHierarchyError,
    OrganizationValidationError,
)
from gda.io.json import GDAJsonIO
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import LocationID, OrganizationID, SiteID
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate, TimePeriod
from gda.model.base.name import NameThing
from gda.model.base.note import Note
from gda.model.base.tombstone import Tombstone
from gda.model.entity.organization import Organization
from gda.util.text import clean_string

if TYPE_CHECKING:
    from gda.db.session import DatabaseSessionManager
    from gda.entity.locations.collection import Locations
    from gda.entity.organizations.collection import Organizations
    from gda.entity.sites.collection import Sites

__version__ = "1.0.0+build.4"

__all__ = [
    "can_tombstone",
    "can_undelete",
    "export_file",
    "import_file",
    "load_from_db",
    "save_to_db",
    "tombstone_organization",
    "undelete_organization",
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


def can_tombstone(
    collection: Organizations,
    org_id: OrganizationID | str,
    superseded_by: OrganizationID | str | None = None,
) -> tuple[bool, str | None]:
    """Verify whether an organization can be safely retired without violating integrity."""
    target_id = OrganizationID(str(org_id))
    target = collection._registry.get(target_id)
    if not target:
        return False, f"Organization '{target_id}' does not exist in collection."

    if target.tombstone.is_deprecated:
        return False, f"Organization '{target_id}' is already tombstoned."

    active_children = [
        child.id
        for child in collection
        if child.parent_org_id == target_id and not child.tombstone.is_deprecated
    ]

    if active_children and not superseded_by:
        children_preview = ", ".join(str(cid) for cid in active_children[:3])
        if len(active_children) > 3:
            children_preview += f", ... ({len(active_children)} total)"
        return (
            False,
            f"Cannot tombstone organization '{target_id}' because it has active child "
            f"organizations [{children_preview}] and no replacement 'superseded_by' was specified.",
        )

    if superseded_by:
        replacement_id = OrganizationID(str(superseded_by))
        if replacement_id == target_id:
            return False, f"Replacement entity '{replacement_id}' cannot be the entity itself."

        replacement = collection._registry.get(replacement_id)
        if not replacement:
            return False, f"Replacement entity '{replacement_id}' does not exist in collection."

        if replacement.tombstone.is_deprecated:
            return False, f"Replacement entity '{replacement_id}' is itself tombstoned."

        if replacement.category != target.category:
            return (
                False,
                f"Replacement entity '{replacement_id}' [{replacement.category.value}] "
                f"must match the organization category of target '{target_id}' [{target.category.value}].",
            )

    return True, None


def tombstone_organization(
    collection: Organizations,
    org_id: OrganizationID | str,
    reason: str,
    superseded_by: OrganizationID | str | None = None,
) -> Organization:
    """Atomically retire an organization, reparent active child chapters if needed, and update registry."""
    ok, error_msg = can_tombstone(
        collection=collection,
        org_id=org_id,
        superseded_by=superseded_by,
    )
    if not ok:
        raise OrganizationHierarchyError(error_msg or "Cannot tombstone organization.")

    target_id = OrganizationID(str(org_id))
    target = collection._registry[target_id]
    replacement_id = OrganizationID(str(superseded_by)) if superseded_by else None

    if replacement_id:
        active_children = [
            child
            for child in collection
            if child.parent_org_id == target_id and not child.tombstone.is_deprecated
        ]
        for child in active_children:
            reparented = dataclasses.replace(child, parent_org_id=replacement_id).mark_dirty()
            collection._registry[reparented.id] = reparented
            collection._parent_index[target_id].discard(reparented.id)
            collection._parent_index[replacement_id].add(reparented.id)
        if not collection._parent_index[target_id]:
            del collection._parent_index[target_id]

    _ = clean_string(reason)
    retired = target.deprecate(superseded_by=replacement_id).mark_dirty()

    collection._registry[retired.id] = retired
    return retired


def can_undelete(
    collection: Organizations,
    org_id: OrganizationID | str,
    locations_collection: Locations | None = None,
    sites_collection: Sites | None = None,
) -> tuple[bool, str | None]:
    """Verify whether a tombstoned organization can be safely restored to active status."""
    target_id = OrganizationID(str(org_id))
    target = collection._registry.get(target_id)
    if not target:
        return False, f"Organization '{target_id}' does not exist in collection."

    if not target.tombstone.is_deprecated:
        return False, f"Organization '{target_id}' is not tombstoned."

    if target.parent_org_id is not None:
        if target.parent_org_id not in collection:
            return (
                False,
                f"Cannot undelete organization '{target_id}'; parent organization "
                f"'{target.parent_org_id}' is missing or tombstoned.",
            )

    if locations_collection is not None and target.location_id is not None:
        if target.location_id not in locations_collection:
            return (
                False,
                f"Cannot undelete organization '{target_id}'; governing location "
                f"'{target.location_id}' is missing or tombstoned.",
            )

    if sites_collection is not None and target.meeting_site_id is not None:
        if target.meeting_site_id not in sites_collection:
            return (
                False,
                f"Cannot undelete organization '{target_id}'; meeting site "
                f"'{target.meeting_site_id}' is missing or tombstoned.",
            )

    return True, None


def undelete_organization(
    collection: Organizations,
    org_id: OrganizationID | str,
    locations_collection: Locations | None = None,
    sites_collection: Sites | None = None,
) -> Organization:
    """Atomically restore a tombstoned organization back to active status."""
    ok, error_msg = can_undelete(
        collection=collection,
        org_id=org_id,
        locations_collection=locations_collection,
        sites_collection=sites_collection,
    )
    if not ok:
        raise OrganizationValidationError(error_msg or "Cannot undelete organization.")

    target_id = OrganizationID(str(org_id))
    target = collection._registry[target_id]

    active_org = target.restore().mark_dirty()
    collection._registry[active_org.id] = active_org
    return active_org


def load_from_db(
    collection: Organizations,
    session_manager: DatabaseSessionManager | None = None,
) -> int:
    """Load all organization records from the SQLite database directly into the collection."""
    from gda.db.mapper import OrganizationRowMapper
    from gda.db.schema import SchemaManager
    from gda.db.session import DatabaseSessionManager

    session = session_manager or DatabaseSessionManager()
    schema_mgr = SchemaManager(session_manager=session)
    schema_mgr.init_db()

    mapper = OrganizationRowMapper()
    loaded_count = 0

    with session.get_connection() as conn:
        cursor = conn.execute("SELECT * FROM organizations ORDER BY id")
        for row in cursor.fetchall():
            entity = mapper.from_row(row)
            collection.add(entity)
            loaded_count += 1

    collection.mark_clean()
    return loaded_count


def save_to_db(
    collection: Organizations,
    session_manager: DatabaseSessionManager | None = None,
) -> int:
    """Commit collection entities to the SQLite database and mark the collection clean."""
    from gda.db.mapper import OrganizationRowMapper
    from gda.db.schema import SchemaManager
    from gda.db.session import DatabaseSessionManager

    session = session_manager or DatabaseSessionManager()
    schema_mgr = SchemaManager(session_manager=session)
    schema_mgr.init_db()

    mapper = OrganizationRowMapper()
    written = 0

    with session.transaction() as tx:
        for entity in collection.iter_all():
            row_dict = mapper.to_row(entity)
            columns = ", ".join(row_dict.keys())
            placeholders = ", ".join(f":{k}" for k in row_dict)
            tx.execute(
                f"INSERT OR REPLACE INTO organizations ({columns}) VALUES ({placeholders})",
                row_dict,
            )
            written += 1

    collection.mark_clean()
    return written


def _append_org_historical_variant(name_obj: NameThing, h: dict[str, Any]) -> NameThing:
    """Append a historical name variant dictionary to NameThing."""
    h_raw = str(h.get("raw") or h.get("raw_name", ""))
    h_canonical = str(h.get("canonical") or h.get("canonical_name") or h_raw)
    h_type_raw = h.get("historic_name_type") or h.get("status", HistoricNameType.HISTORICAL)
    h_type = (
        h_type_raw if isinstance(h_type_raw, HistoricNameType) else HistoricNameType(h_type_raw)
    )
    return name_obj.add_historic_variant(
        raw=h_raw,
        name=h_canonical,
        historic_name_type=h_type,
    )


def _parse_imported_org_name(item: dict[str, Any]) -> NameThing:
    """Reconstruct NameThing with aliases and historical variants from an org export dict."""
    raw_name_val = item.get("name", "")
    if isinstance(raw_name_val, dict):
        name_obj = NameThing.from_dict(raw_name_val)
    else:
        name_obj = NameThing.create(raw=str(raw_name_val), canonical=str(raw_name_val))

    raw_historical = item.get("historical_names", [])
    if raw_historical and not name_obj.historic:
        for h in raw_historical:
            if isinstance(h, dict):
                name_obj = _append_org_historical_variant(name_obj, h)

    for alias in item.get("alternate_names") or item.get("aliases") or []:
        if alias not in name_obj.aliases:
            name_obj = name_obj.add_alias(alias)

    return name_obj


def _parse_imported_org_notes(
    raw_notes: list[Any],
    default_audit_dict: dict[str, str],
) -> list[Note]:
    """Hydrate embedded Note list from raw JSON organization note items."""
    embedded_notes: list[Note] = []
    for n in raw_notes:
        if isinstance(n, Note):
            embedded_notes.append(n)
        elif isinstance(n, dict):
            note_dict = dict(n)
            if "audit" not in note_dict:
                note_dict["audit"] = default_audit_dict
            embedded_notes.append(Note.from_dict(note_dict))
    return embedded_notes


def import_file(collection: Organizations, path: Path | str) -> int:
    """Import organizations from a formatted JSON file, preserving audit and tombstone state."""
    json_path = Path(path)
    if not json_path.exists():
        return 0

    payload = GDAJsonIO.read(json_path)
    orgs_list = payload.get("organizations", [])
    now = IsoTimestamp(utc_now_iso())
    default_audit = AuditStamp(created_at=now, updated_at=now)
    audit_dict = default_audit.to_dict()

    for item in orgs_list:
        raw_audit = item.get("audit")
        raw_tomb = item.get("tombstone")
        org = Organization.create(
            org_id=OrganizationID(item["id"]),
            audit=(
                AuditStamp.from_dict(raw_audit) if isinstance(raw_audit, dict) else default_audit
            ),
            name=_parse_imported_org_name(item),
            category=OrganizationCategory(item["category"]),
            canonical_urn=item["canonical_urn"],
            parent_org_id=(
                OrganizationID(item["parent_org_id"]) if item.get("parent_org_id") else None
            ),
            predecessor_ids=[OrganizationID(p) for p in item.get("predecessor_ids", [])],
            successor_ids=[OrganizationID(s) for s in item.get("successor_ids", [])],
            location_id=LocationID(item["location_id"]) if item.get("location_id") else None,
            meeting_site_id=(
                SiteID(item["meeting_site_id"]) if item.get("meeting_site_id") else None
            ),
            period=_parse_time_period(item.get("period")),
            is_active=item.get("is_active", True),
            notes=_parse_imported_org_notes(item.get("notes", []), audit_dict),
            tombstone=(
                Tombstone.from_dict(raw_tomb, id_cls=OrganizationID)
                if isinstance(raw_tomb, dict)
                else Tombstone[OrganizationID]()
            ),
        )
        collection.add(org)

    return len(orgs_list)


def export_file(
    collection: Organizations,
    path: Path | str,
    include_graveyard: bool = True,
    *,
    create_backup: bool = False,
    backup_dir: Path | str | None = None,
) -> int:
    """Export organization records from the collection to a formatted JSON file."""
    entities = list(collection.iter_all() if include_graveyard else collection)
    out_list: list[dict[str, Any]] = []

    for o in entities:
        hist_list = [
            {
                "raw": h.raw,
                "canonical": h.name,
                "historic_name_type": h.historic_name_type.value,
            }
            for h in o.name.historic
        ]
        notes_list = [n.to_dict() for n in o.notes]

        item: dict[str, Any] = {
            "id": str(o.id),
            "name": o.name.to_dict(),
            "category": o.category.value,
            "canonical_urn": o.canonical_urn,
            "parent_org_id": str(o.parent_org_id) if o.parent_org_id else None,
            "predecessor_ids": [str(p) for p in o.predecessor_ids],
            "successor_ids": [str(s) for s in o.successor_ids],
            "location_id": str(o.location_id) if o.location_id else None,
            "meeting_site_id": str(o.meeting_site_id) if o.meeting_site_id else None,
            "is_active": o.is_active,
            "period": (
                {
                    "start_date": str(o.period.start_date) if o.period.start_date else None,
                    "end_date": str(o.period.end_date) if o.period.end_date else None,
                }
                if o.period
                else None
            ),
            "alternate_names": list(o.aliases),
            "historical_names": hist_list,
            "notes": notes_list,
            "audit": o.audit.to_dict(),
            "tombstone": o.tombstone.to_dict(),
        }
        out_list.append(item)

    payload = {
        "schema_version": "1.0.0",
        "record_type": "organization_export",
        "total_count": len(out_list),
        "organizations": out_list,
    }

    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    GDAJsonIO.write(
        dest,
        payload,
        create_backup=create_backup,
        backup_dir=backup_dir,
    )
    return len(out_list)
