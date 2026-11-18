"""Path: src/gda/entity/families/util.py

Family persistence, graveyard lifecycle operations, and serialization routines.

Operational Role:
    Provides collection-level family persistence routines using FamilyRowMapper,
    import/export routines operating on formatted JSON payloads (preserving
    audit and tombstone metadata), and safe tombstone/undelete lifecycle
    operators on Families collection instances.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from gda.core.dates import utc_now_iso
from gda.entity.families.errors import FamilyValidationError
from gda.io.json import GDAJsonIO
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import FamilyID
from gda.model.base.audit import AuditStamp
from gda.model.base.family import ChildLink
from gda.model.base.note import Note
from gda.model.base.tombstone import Tombstone
from gda.model.entity.family import Family
from gda.util.text import clean_string

if TYPE_CHECKING:
    from gda.db.session import DatabaseSessionManager
    from gda.entity.families.collection import Families
    from gda.entity.individuals.collection import Individuals

__version__ = "1.0.0+build.3"

__all__ = [
    "can_tombstone",
    "can_undelete",
    "export_file",
    "import_file",
    "load_from_db",
    "save_to_db",
    "tombstone_family",
    "undelete_family",
]


def can_tombstone(
    collection: Families,
    family_id: FamilyID | str,
    superseded_by: FamilyID | str | None = None,
) -> tuple[bool, str | None]:
    """Verify whether a family unit can be safely retired without violating integrity."""
    target_id = FamilyID(str(family_id))
    target = collection._registry.get(target_id)
    if not target:
        return False, f"Family '{target_id}' does not exist in collection."

    if target.tombstone.is_deprecated:
        return False, f"Family '{target_id}' is already tombstoned."

    if superseded_by:
        replacement_id = FamilyID(str(superseded_by))
        if replacement_id == target_id:
            return False, f"Replacement entity '{replacement_id}' cannot be the entity itself."

        replacement = collection._registry.get(replacement_id)
        if not replacement:
            return False, f"Replacement entity '{replacement_id}' does not exist in collection."

        if replacement.tombstone.is_deprecated:
            return False, f"Replacement entity '{replacement_id}' is itself tombstoned."

    return True, None


def tombstone_family(
    collection: Families,
    family_id: FamilyID | str,
    reason: str,
    superseded_by: FamilyID | str | None = None,
) -> Family:
    """Atomically retire a family entity and update the registry."""
    ok, error_msg = can_tombstone(
        collection=collection,
        family_id=family_id,
        superseded_by=superseded_by,
    )
    if not ok:
        raise FamilyValidationError(error_msg or "Cannot tombstone family.")

    target_id = FamilyID(str(family_id))
    target = collection._registry[target_id]
    replacement_id = FamilyID(str(superseded_by)) if superseded_by else None

    _ = clean_string(reason)
    retired = target.deprecate(superseded_by=replacement_id).mark_dirty()

    collection._registry[retired.id] = retired
    return retired


def can_undelete(
    collection: Families,
    family_id: FamilyID | str,
    individuals_collection: Individuals | None = None,
) -> tuple[bool, str | None]:
    """Verify whether a tombstoned family can be safely restored to active status."""
    target_id = FamilyID(str(family_id))
    target = collection._registry.get(target_id)
    if not target:
        return False, f"Family '{target_id}' does not exist in collection."

    if not target.tombstone.is_deprecated:
        return False, f"Family '{target_id}' is not tombstoned."

    if individuals_collection is not None:
        for pid in target.partner_ids:
            if pid not in individuals_collection:
                return (
                    False,
                    f"Cannot undelete family '{target_id}'; partner individual "
                    f"'{pid}' is missing or tombstoned.",
                )
        for cid in target.child_ids:
            if cid not in individuals_collection:
                return (
                    False,
                    f"Cannot undelete family '{target_id}'; child individual "
                    f"'{cid}' is missing or tombstoned.",
                )

    return True, None


def undelete_family(
    collection: Families,
    family_id: FamilyID | str,
    individuals_collection: Individuals | None = None,
) -> Family:
    """Atomically restore a tombstoned family back to active status."""
    ok, error_msg = can_undelete(
        collection=collection,
        family_id=family_id,
        individuals_collection=individuals_collection,
    )
    if not ok:
        raise FamilyValidationError(error_msg or "Cannot undelete family.")

    target_id = FamilyID(str(family_id))
    target = collection._registry[target_id]

    active_fam = target.restore().mark_dirty()
    collection._registry[active_fam.id] = active_fam
    return active_fam


def load_from_db(
    collection: Families,
    session_manager: DatabaseSessionManager | None = None,
) -> int:
    """Load all family records from the SQLite database directly into the collection."""
    from gda.db.mapper import FamilyRowMapper
    from gda.db.schema import SchemaManager
    from gda.db.session import DatabaseSessionManager

    session = session_manager or DatabaseSessionManager()
    schema_mgr = SchemaManager(session_manager=session)
    schema_mgr.init_db()

    mapper = FamilyRowMapper()
    loaded_count = 0

    with session.get_connection() as conn:
        cursor = conn.execute("SELECT * FROM families ORDER BY id")
        for row in cursor.fetchall():
            entity = mapper.from_row(row)
            collection.add(entity)
            loaded_count += 1

    collection.mark_clean()
    return loaded_count


def save_to_db(
    collection: Families,
    session_manager: DatabaseSessionManager | None = None,
) -> int:
    """Commit collection entities to the SQLite database and mark the collection clean."""
    from gda.db.mapper import FamilyRowMapper
    from gda.db.schema import SchemaManager
    from gda.db.session import DatabaseSessionManager

    session = session_manager or DatabaseSessionManager()
    schema_mgr = SchemaManager(session_manager=session)
    schema_mgr.init_db()

    mapper = FamilyRowMapper()
    written = 0

    with session.transaction() as tx:
        for entity in collection.iter_all():
            row_dict = mapper.to_row(entity)
            columns = ", ".join(row_dict.keys())
            placeholders = ", ".join(f":{k}" for k in row_dict)
            tx.execute(
                f"INSERT OR REPLACE INTO families ({columns}) VALUES ({placeholders})",
                row_dict,
            )
            written += 1

    collection.mark_clean()
    return written


def import_file(collection: Families, path: Path | str) -> int:
    """Import families from a formatted JSON file, preserving audit and tombstone state."""
    json_path = Path(path)
    if not json_path.exists():
        return 0

    payload = GDAJsonIO.read(json_path)
    families_list = payload.get("families", [])
    now = IsoTimestamp(utc_now_iso())
    default_audit = AuditStamp(created_at=now, updated_at=now)
    audit_dict = default_audit.to_dict()

    for item in families_list:
        fam_id = FamilyID(item["id"])

        embedded_notes: list[Note] = []
        for n in item.get("notes", []):
            if isinstance(n, Note):
                embedded_notes.append(n)
            elif isinstance(n, dict):
                note_dict = dict(n)
                if "audit" not in note_dict:
                    note_dict["audit"] = audit_dict
                embedded_notes.append(Note.from_dict(note_dict))

        children_list: list[ChildLink | tuple[Any, Any] | dict[str, Any]] = []
        for c in item.get("children", []):
            if isinstance(c, (ChildLink, tuple, dict)):
                children_list.append(c)

        raw_audit = item.get("audit")
        audit_obj = (
            AuditStamp.from_dict(raw_audit) if isinstance(raw_audit, dict) else default_audit
        )
        raw_tomb = item.get("tombstone")
        tomb_obj = (
            Tombstone.from_dict(raw_tomb, id_cls=FamilyID)
            if isinstance(raw_tomb, dict)
            else Tombstone[FamilyID]()
        )

        fam = Family.create(
            family_id=fam_id,
            canonical_urn=item["canonical_urn"],
            partner_ids=item.get("partner_ids", []),
            children=children_list,
            union=item.get("union"),
            audit=audit_obj,
            notes=embedded_notes,
            tombstone=tomb_obj,
        )
        collection.add(fam)

    return len(families_list)


def export_file(
    collection: Families,
    path: Path | str,
    include_graveyard: bool = True,
    *,
    create_backup: bool = False,
    backup_dir: Path | str | None = None,
) -> int:
    """Export family records from the collection to a formatted JSON file."""
    entities = list(collection.iter_all() if include_graveyard else collection)
    out_list: list[dict[str, Any]] = [fam.to_dict() for fam in entities]

    payload = {
        "schema_version": "1.0.0",
        "record_type": "family_export",
        "total_count": len(out_list),
        "families": out_list,
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
