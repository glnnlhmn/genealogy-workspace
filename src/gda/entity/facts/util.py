"""Path: src/gda/entity/facts/util.py

Fact persistence, graveyard lifecycle operations, and serialization routines.

Operational Role:
    Provides collection-level fact persistence routines using FactRowMapper,
    import/export routines operating on formatted JSON payloads (preserving
    audit and tombstone metadata), and safe tombstone/undelete lifecycle
    operators on Facts collection instances.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from gda.core.dates import utc_now_iso
from gda.entity.facts.errors import FactValidationError
from gda.io.json import GDAJsonIO
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import FactID, FamilyID, IndividualID, LocationID, SiteID
from gda.model.base.audit import AuditStamp
from gda.model.base.note import Note
from gda.model.base.source import SourceReference
from gda.model.base.tombstone import Tombstone
from gda.model.entity.fact import Fact, FactParticipant
from gda.util.text import clean_string

if TYPE_CHECKING:
    from gda.db.session import DatabaseSessionManager
    from gda.entity.facts.collection import Facts
    from gda.entity.families.collection import Families
    from gda.entity.individuals.collection import Individuals
    from gda.entity.locations.collection import Locations
    from gda.entity.sites.collection import Sites

__version__ = "1.0.0+build.2"

__all__ = [
    "can_tombstone",
    "can_undelete",
    "export_file",
    "import_file",
    "load_from_db",
    "save_to_db",
    "tombstone_fact",
    "undelete_fact",
]


def _resolve_subject_id(val: IndividualID | FamilyID | str) -> IndividualID | FamilyID:
    """Resolve raw subject identifier into an IndividualID or FamilyID."""
    if isinstance(val, (IndividualID, FamilyID)):
        return val
    raw = str(val).strip()
    if raw.startswith("FAM-"):
        return FamilyID(raw)
    return IndividualID(raw)


def can_tombstone(
    collection: Facts,
    fact_id: FactID | str,
    superseded_by: FactID | str | None = None,
) -> tuple[bool, str | None]:
    """Verify whether a fact can be safely retired without violating integrity."""
    target_id = FactID(str(fact_id))
    target = collection._registry.get(target_id)
    if not target:
        return False, f"Fact '{target_id}' does not exist in collection."

    if target.tombstone.is_deprecated:
        return False, f"Fact '{target_id}' is already tombstoned."

    if superseded_by:
        replacement_id = FactID(str(superseded_by))
        if replacement_id == target_id:
            return False, f"Replacement entity '{replacement_id}' cannot be the entity itself."

        replacement = collection._registry.get(replacement_id)
        if not replacement:
            return False, f"Replacement entity '{replacement_id}' does not exist in collection."

        if replacement.tombstone.is_deprecated:
            return False, f"Replacement entity '{replacement_id}' is itself tombstoned."

    return True, None


def tombstone_fact(
    collection: Facts,
    fact_id: FactID | str,
    reason: str,
    superseded_by: FactID | str | None = None,
) -> Fact:
    """Atomically retire a fact entity and update the registry."""
    ok, error_msg = can_tombstone(
        collection=collection,
        fact_id=fact_id,
        superseded_by=superseded_by,
    )
    if not ok:
        raise FactValidationError(error_msg or "Cannot tombstone fact.")

    target_id = FactID(str(fact_id))
    target = collection._registry[target_id]
    replacement_id = FactID(str(superseded_by)) if superseded_by else None

    _ = clean_string(reason)
    retired = target.deprecate(superseded_by=replacement_id).mark_dirty()

    collection._registry[retired.id] = retired
    return retired


def can_undelete(
    collection: Facts,
    fact_id: FactID | str,
    locations_collection: Locations | None = None,
    sites_collection: Sites | None = None,
    individuals_collection: Individuals | None = None,
    families_collection: Families | None = None,
) -> tuple[bool, str | None]:
    """Verify whether a tombstoned fact can be safely restored to active status."""
    target_id = FactID(str(fact_id))
    target = collection._registry.get(target_id)
    if not target:
        return False, f"Fact '{target_id}' does not exist in collection."

    if not target.tombstone.is_deprecated:
        return False, f"Fact '{target_id}' is not tombstoned."

    if isinstance(target.primary_subject_id, IndividualID) and individuals_collection is not None:
        if target.primary_subject_id not in individuals_collection:
            return (
                False,
                f"Cannot undelete fact '{target_id}'; primary subject individual "
                f"'{target.primary_subject_id}' is missing or tombstoned.",
            )
    elif isinstance(target.primary_subject_id, FamilyID) and families_collection is not None:
        if target.primary_subject_id not in families_collection:
            return (
                False,
                f"Cannot undelete fact '{target_id}'; primary subject family "
                f"'{target.primary_subject_id}' is missing or tombstoned.",
            )

    if individuals_collection is not None:
        for pid in target.participant_ids:
            if pid not in individuals_collection:
                return (
                    False,
                    f"Cannot undelete fact '{target_id}'; participant individual "
                    f"'{pid}' is missing or tombstoned.",
                )

    if locations_collection is not None and target.location_id is not None:
        if target.location_id not in locations_collection:
            return (
                False,
                f"Cannot undelete fact '{target_id}'; governing location "
                f"'{target.location_id}' is missing or tombstoned.",
            )

    if sites_collection is not None and target.site_id is not None:
        if target.site_id not in sites_collection:
            return (
                False,
                f"Cannot undelete fact '{target_id}'; venue site "
                f"'{target.site_id}' is missing or tombstoned.",
            )

    return True, None


def undelete_fact(
    collection: Facts,
    fact_id: FactID | str,
    locations_collection: Locations | None = None,
    sites_collection: Sites | None = None,
    individuals_collection: Individuals | None = None,
    families_collection: Families | None = None,
) -> Fact:
    """Atomically restore a tombstoned fact back to active status."""
    ok, error_msg = can_undelete(
        collection=collection,
        fact_id=fact_id,
        locations_collection=locations_collection,
        sites_collection=sites_collection,
        individuals_collection=individuals_collection,
        families_collection=families_collection,
    )
    if not ok:
        raise FactValidationError(error_msg or "Cannot undelete fact.")

    target_id = FactID(str(fact_id))
    target = collection._registry[target_id]

    active_fact = target.restore().mark_dirty()
    collection._registry[active_fact.id] = active_fact
    return active_fact


def load_from_db(
    collection: Facts,
    session_manager: DatabaseSessionManager | None = None,
) -> int:
    """Load all fact records from the SQLite database directly into the collection."""
    from gda.db.mapper import FactRowMapper
    from gda.db.schema import SchemaManager
    from gda.db.session import DatabaseSessionManager

    session = session_manager or DatabaseSessionManager()
    schema_mgr = SchemaManager(session_manager=session)
    schema_mgr.init_db()

    mapper = FactRowMapper()
    loaded_count = 0

    with session.get_connection() as conn:
        cursor = conn.execute("SELECT * FROM facts ORDER BY id")
        for row in cursor.fetchall():
            entity = mapper.from_row(row)
            collection.add(entity)
            loaded_count += 1

    collection.mark_clean()
    return loaded_count


def save_to_db(
    collection: Facts,
    session_manager: DatabaseSessionManager | None = None,
) -> int:
    """Commit collection entities to the SQLite database and mark the collection clean."""
    from gda.db.mapper import FactRowMapper
    from gda.db.schema import SchemaManager
    from gda.db.session import DatabaseSessionManager

    session = session_manager or DatabaseSessionManager()
    schema_mgr = SchemaManager(session_manager=session)
    schema_mgr.init_db()

    mapper = FactRowMapper()
    written = 0

    with session.transaction() as tx:
        for entity in collection.iter_all():
            row_dict = mapper.to_row(entity)
            columns = ", ".join(row_dict.keys())
            placeholders = ", ".join(f":{k}" for k in row_dict)
            tx.execute(
                f"INSERT OR REPLACE INTO facts ({columns}) VALUES ({placeholders})",
                row_dict,
            )
            written += 1

    collection.mark_clean()
    return written


def import_file(collection: Facts, path: Path | str) -> int:
    """Import facts from a formatted JSON file, preserving audit and tombstone state."""
    json_path = Path(path)
    if not json_path.exists():
        return 0

    payload = GDAJsonIO.read(json_path)
    facts_list = payload.get("facts", [])
    now = IsoTimestamp(utc_now_iso())
    default_audit = AuditStamp(created_at=now, updated_at=now)
    audit_dict = {"created_at": str(now), "updated_at": str(now)}

    for item in facts_list:
        fact_id = FactID(item["id"])
        subject_id = _resolve_subject_id(item["primary_subject_id"])
        location_id = LocationID(item["location_id"]) if item.get("location_id") else None
        site_id = SiteID(item["site_id"]) if item.get("site_id") else None

        embedded_notes: list[Note] = []
        for n in item.get("notes", []):
            if isinstance(n, Note):
                embedded_notes.append(n)
            elif isinstance(n, dict):
                note_dict = dict(n)
                if "audit" not in note_dict:
                    note_dict["audit"] = audit_dict
                embedded_notes.append(Note.from_dict(note_dict))

        participants_list: list[FactParticipant | dict[str, Any]] = []
        for p in item.get("participants", []):
            if isinstance(p, (FactParticipant, dict)):
                participants_list.append(p)

        citations_list: list[SourceReference | dict[str, Any]] = []
        for c in item.get("citations", []):
            if isinstance(c, (SourceReference, dict)):
                citations_list.append(c)

        raw_audit = item.get("audit")
        audit_obj = (
            AuditStamp(
                created_at=IsoTimestamp(raw_audit["created_at"]),
                updated_at=IsoTimestamp(raw_audit["updated_at"]),
            )
            if isinstance(raw_audit, dict)
            else default_audit
        )
        raw_tomb = item.get("tombstone")
        tomb_obj = (
            Tombstone[FactID](
                is_deprecated=bool(raw_tomb.get("is_deprecated", False)),
                deprecated_at=(
                    IsoTimestamp(raw_tomb["deprecated_at"])
                    if raw_tomb.get("deprecated_at")
                    else None
                ),
                superseded_by=(
                    FactID(str(raw_tomb["superseded_by"]))
                    if raw_tomb.get("superseded_by")
                    else None
                ),
            )
            if isinstance(raw_tomb, dict)
            else Tombstone[FactID]()
        )

        fact = Fact.create(
            fact_id=fact_id,
            canonical_urn=item["canonical_urn"],
            fact_type=item["fact_type"],
            title=item["title"],
            primary_subject_id=subject_id,
            date=item.get("date"),
            location_id=location_id,
            site_id=site_id,
            value=item.get("value"),
            description=item.get("description"),
            narrative=item.get("narrative"),
            participants=participants_list,
            citations=citations_list,
            audit=audit_obj,
            notes=embedded_notes,
            tombstone=tomb_obj,
        )
        collection.add(fact)

    return len(facts_list)


def export_file(
    collection: Facts,
    path: Path | str,
    include_graveyard: bool = True,
) -> int:
    """Export fact records from the collection to a formatted JSON file."""
    entities = list(collection.iter_all() if include_graveyard else collection)
    out_list: list[dict[str, Any]] = [f.to_dict() for f in entities]

    payload = {
        "schema_version": "1.0.0",
        "record_type": "fact_export",
        "total_count": len(out_list),
        "facts": out_list,
    }

    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    GDAJsonIO.write(dest, payload)
    return len(out_list)
