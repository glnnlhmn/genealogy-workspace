"""Path: src/gda/entity/individuals/util.py

Individual persistence, graveyard lifecycle operations, and serialization routines.

Operational Role:
    Provides collection-level individual persistence routines using
    IndividualRowMapper, import/export routines operating on formatted JSON
    payloads (preserving audit and tombstone metadata), and safe
    tombstone/undelete lifecycle operators on Individuals collection instances.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from gda.core.dates import utc_now_iso
from gda.entity.individuals.errors import IndividualValidationError
from gda.io.json import GDAJsonIO
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import IndividualID, LocationID, SiteID
from gda.model.base.audit import AuditStamp
from gda.model.base.name import NamePerson
from gda.model.base.note import Note
from gda.model.base.tombstone import Tombstone
from gda.model.entity.individual import Individual
from gda.util.text import clean_string

if TYPE_CHECKING:
    from gda.db.session import DatabaseSessionManager
    from gda.entity.individuals.collection import Individuals
    from gda.entity.locations.collection import Locations
    from gda.entity.sites.collection import Sites

__version__ = "1.0.0+build.3"

__all__ = [
    "can_tombstone",
    "can_undelete",
    "export_file",
    "import_file",
    "load_from_db",
    "save_to_db",
    "tombstone_individual",
    "undelete_individual",
]


def _check_place_ref(
    place_id: LocationID | SiteID | None,
    label: str,
    target_id: IndividualID,
    locations_collection: Locations | None,
    sites_collection: Sites | None,
) -> str | None:
    """Validate an optional LocationID or SiteID place reference against active collections."""
    if place_id is None:
        return None
    if isinstance(place_id, LocationID):
        if locations_collection is not None and place_id not in locations_collection:
            return (
                f"Cannot undelete individual '{target_id}'; {label} location "
                f"'{place_id}' is missing or tombstoned."
            )
    elif isinstance(place_id, SiteID):
        if sites_collection is not None and place_id not in sites_collection:
            return (
                f"Cannot undelete individual '{target_id}'; {label} site "
                f"'{place_id}' is missing or tombstoned."
            )
    return None


def can_tombstone(
    collection: Individuals,
    individual_id: IndividualID | str,
    superseded_by: IndividualID | str | None = None,
) -> tuple[bool, str | None]:
    """Verify whether an individual can be safely retired without violating integrity."""
    target_id = IndividualID(str(individual_id))
    target = collection._registry.get(target_id)
    if not target:
        return False, f"Individual '{target_id}' does not exist in collection."

    if target.tombstone.is_deprecated:
        return False, f"Individual '{target_id}' is already tombstoned."

    if superseded_by:
        replacement_id = IndividualID(str(superseded_by))
        if replacement_id == target_id:
            return False, f"Replacement entity '{replacement_id}' cannot be the entity itself."

        replacement = collection._registry.get(replacement_id)
        if not replacement:
            return False, f"Replacement entity '{replacement_id}' does not exist in collection."

        if replacement.tombstone.is_deprecated:
            return False, f"Replacement entity '{replacement_id}' is itself tombstoned."

    return True, None


def tombstone_individual(
    collection: Individuals,
    individual_id: IndividualID | str,
    reason: str,
    superseded_by: IndividualID | str | None = None,
) -> Individual:
    """Atomically retire an individual entity and update the registry."""
    ok, error_msg = can_tombstone(
        collection=collection,
        individual_id=individual_id,
        superseded_by=superseded_by,
    )
    if not ok:
        raise IndividualValidationError(error_msg or "Cannot tombstone individual.")

    target_id = IndividualID(str(individual_id))
    target = collection._registry[target_id]
    replacement_id = IndividualID(str(superseded_by)) if superseded_by else None

    _ = clean_string(reason)
    retired = target.deprecate(superseded_by=replacement_id).mark_dirty()

    collection._registry[retired.id] = retired
    return retired


def can_undelete(
    collection: Individuals,
    individual_id: IndividualID | str,
    locations_collection: Locations | None = None,
    sites_collection: Sites | None = None,
) -> tuple[bool, str | None]:
    """Verify whether a tombstoned individual can be safely restored to active status."""
    target_id = IndividualID(str(individual_id))
    target = collection._registry.get(target_id)
    if not target:
        return False, f"Individual '{target_id}' does not exist in collection."

    if not target.tombstone.is_deprecated:
        return False, f"Individual '{target_id}' is not tombstoned."

    birth_err = _check_place_ref(
        target.birth_place_id,
        "birth place",
        target_id,
        locations_collection,
        sites_collection,
    )
    if birth_err:
        return False, birth_err

    death_err = _check_place_ref(
        target.death_place_id,
        "death place",
        target_id,
        locations_collection,
        sites_collection,
    )
    if death_err:
        return False, death_err

    return True, None


def undelete_individual(
    collection: Individuals,
    individual_id: IndividualID | str,
    locations_collection: Locations | None = None,
    sites_collection: Sites | None = None,
) -> Individual:
    """Atomically restore a tombstoned individual back to active status."""
    ok, error_msg = can_undelete(
        collection=collection,
        individual_id=individual_id,
        locations_collection=locations_collection,
        sites_collection=sites_collection,
    )
    if not ok:
        raise IndividualValidationError(error_msg or "Cannot undelete individual.")

    target_id = IndividualID(str(individual_id))
    target = collection._registry[target_id]

    active_ind = target.restore().mark_dirty()
    collection._registry[active_ind.id] = active_ind
    return active_ind


def load_from_db(
    collection: Individuals,
    session_manager: DatabaseSessionManager | None = None,
) -> int:
    """Load all individual records from the SQLite database directly into the collection."""
    from gda.db.mapper import IndividualRowMapper
    from gda.db.schema import SchemaManager
    from gda.db.session import DatabaseSessionManager

    session = session_manager or DatabaseSessionManager()
    schema_mgr = SchemaManager(session_manager=session)
    schema_mgr.init_db()

    mapper = IndividualRowMapper()
    loaded_count = 0

    with session.get_connection() as conn:
        cursor = conn.execute("SELECT * FROM individuals ORDER BY id")
        for row in cursor.fetchall():
            entity = mapper.from_row(row)
            collection.add(entity)
            loaded_count += 1

    collection.mark_clean()
    return loaded_count


def save_to_db(
    collection: Individuals,
    session_manager: DatabaseSessionManager | None = None,
) -> int:
    """Commit collection entities to the SQLite database and mark the collection clean."""
    from gda.db.mapper import IndividualRowMapper
    from gda.db.schema import SchemaManager
    from gda.db.session import DatabaseSessionManager

    session = session_manager or DatabaseSessionManager()
    schema_mgr = SchemaManager(session_manager=session)
    schema_mgr.init_db()

    mapper = IndividualRowMapper()
    written = 0

    with session.transaction() as tx:
        for entity in collection.iter_all():
            row_dict = mapper.to_row(entity)
            columns = ", ".join(row_dict.keys())
            placeholders = ", ".join(f":{k}" for k in row_dict)
            tx.execute(
                f"INSERT OR REPLACE INTO individuals ({columns}) VALUES ({placeholders})",
                row_dict,
            )
            written += 1

    collection.mark_clean()
    return written


def import_file(collection: Individuals, path: Path | str) -> int:
    """Import individuals from a formatted JSON file, preserving audit and tombstone state."""
    json_path = Path(path)
    if not json_path.exists():
        return 0

    payload = GDAJsonIO.read(json_path)
    individuals_list = payload.get("individuals", [])
    now = IsoTimestamp(utc_now_iso())
    default_audit = AuditStamp(created_at=now, updated_at=now)
    audit_dict = default_audit.to_dict()

    for item in individuals_list:
        ind_id = IndividualID(item["id"])
        raw_name_val = item.get("name", "")
        if isinstance(raw_name_val, dict):
            name_obj = NamePerson.from_dict(raw_name_val)
        else:
            tokens = str(raw_name_val).strip().split()
            if len(tokens) >= 2:
                name_obj = NamePerson.create(
                    raw=str(raw_name_val).strip(),
                    given=" ".join(tokens[:-1]),
                    surname=tokens[-1],
                )
            else:
                name_obj = NamePerson.create(raw=str(raw_name_val).strip(), given=tokens[0])

        for alias in item.get("alternate_names") or item.get("aliases") or []:
            if alias not in name_obj.aliases:
                name_obj = name_obj.add_alias(alias)

        for married in item.get("married_names") or []:
            if married not in name_obj.married:
                name_obj = name_obj.add_married(married)

        embedded_notes: list[Note] = []
        for n in item.get("notes", []):
            if isinstance(n, Note):
                embedded_notes.append(n)
            elif isinstance(n, dict):
                note_dict = dict(n)
                if "audit" not in note_dict:
                    note_dict["audit"] = audit_dict
                embedded_notes.append(Note.from_dict(note_dict))

        raw_audit = item.get("audit")
        audit_obj = (
            AuditStamp.from_dict(raw_audit) if isinstance(raw_audit, dict) else default_audit
        )
        raw_tomb = item.get("tombstone")
        tomb_obj = (
            Tombstone.from_dict(raw_tomb, id_cls=IndividualID)
            if isinstance(raw_tomb, dict)
            else Tombstone[IndividualID]()
        )

        ind = Individual.create(
            individual_id=ind_id,
            name=name_obj,
            canonical_urn=item["canonical_urn"],
            gender=item.get("gender") or item.get("sex"),
            birth_date=item.get("birth_date"),
            death_date=item.get("death_date"),
            birth_place_id=item.get("birth_place_id"),
            death_place_id=item.get("death_place_id"),
            is_deceased=item.get("is_deceased", True),
            audit=audit_obj,
            notes=embedded_notes,
            tombstone=tomb_obj,
        )
        collection.add(ind)

    return len(individuals_list)


def export_file(
    collection: Individuals,
    path: Path | str,
    include_graveyard: bool = True,
    *,
    create_backup: bool = False,
    backup_dir: Path | str | None = None,
) -> int:
    """Export individual records from the collection to a formatted JSON file."""
    entities = list(collection.iter_all() if include_graveyard else collection)
    out_list: list[dict[str, Any]] = [ind.to_dict() for ind in entities]

    payload = {
        "schema_version": "1.0.0",
        "record_type": "individual_export",
        "total_count": len(out_list),
        "individuals": out_list,
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
