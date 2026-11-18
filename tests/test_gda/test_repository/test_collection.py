"""Path: tests/test_gda/test_repository/test_collection.py

Unit and integration tests for BaseSourceCollection (src/gda/repository/collection.py).
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from gda.core.enums.core import Sex
from gda.core.enums.sources import SourceRecordType
from gda.core.enums.vital import BirthPlurality
from gda.db.session import DatabaseSessionManager
from gda.io.json import GDAJsonIO
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import IndividualID, LocationID, RepositoryID, SourceID
from gda.model.atom.urn import SourceURN
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate
from gda.model.base.tombstone import Tombstone
from gda.model.source.vital.birth import BirthRecord
from gda.repository.errors import (
    DuplicateRecordError,
    RecordNotFoundError,
    RepositoryError,
)
from gda.repository.vital.collection import BirthCollection


def _audit() -> AuditStamp:
    ts = IsoTimestamp("2026-01-01T00:00:00Z")
    return AuditStamp(created_at=ts, updated_at=ts)


def _make_birth(
    idx: int,
    urn_suffix: str | None = None,
    loc: str | None = "LOC-000001",
) -> BirthRecord:
    sfx = urn_suffix or f"BIR{idx:03d}"
    return BirthRecord(
        source_id=SourceID(f"00000000-0000-4000-8000-{idx:012d}"),
        source_urn=SourceURN(f"URN:SRC:1852:US_PA:{sfx}"),
        record_type=SourceRecordType.BIRTH_CERTIFICATE,
        description=f"Birth {idx}",
        repository_id=RepositoryID("REP-000001"),
        audit=_audit(),
        child_name_raw="John Lehman",
        date_of_birth=EventDate.from_dict("1852-01-03"),
        place_of_birth_raw="Carlisle, PA",
        child_id=IndividualID("IND-000001") if loc else None,
        place_of_birth_id=LocationID(loc) if loc else None,
        sex=Sex.MALE,
        plurality=BirthPlurality.SINGLE,
        is_stillborn=False,
    )


def test_base_source_collection_lifecycle_edit_graveyard_and_io(
    seeded_session: DatabaseSessionManager,
    tmp_path: Path,
) -> None:
    """Verify BaseSourceCollection add, edit, update, tombstone, undelete, resolve_active, DB, and JSON I/O."""

    class _BoundBirthCollection(BirthCollection):
        def _create_default_repository(self, session_manager=None):
            return super()._create_default_repository(session_manager or seeded_session)

    _ = _BoundBirthCollection.from_database()
    coll = BirthCollection.from_database(session_manager=seeded_session)
    assert len(coll) == 0
    assert coll.table_name == "vital_births"
    assert isinstance(coll.repository, object)
    assert coll.is_dirty is False

    b1 = _make_birth(1)
    b2 = _make_birth(2)
    b3_minimal = _make_birth(3, loc=None)

    coll.add(b1)
    coll.add(b2)
    coll.add(b3_minimal)
    assert len(coll) == 3
    assert len(list(coll)) == 3
    assert coll.is_dirty is True
    assert len(coll.dirty_records()) == 3
    assert coll.dirty_entities() == coll.dirty_records()
    assert len(coll.find_by_child("IND-000001")) == 2
    assert len(coll._records_for_ids([b1.source_id])) == 1

    # Lookup by SourceID, UUID string, URN, and non-matching types
    assert b1.source_id in coll
    assert b1.source_id.value in coll
    assert str(b1.source_urn.value) in coll
    assert 12345 not in coll
    assert "not-a-uuid" not in coll
    assert "00000000-0000-4000-8000-999999999999" not in coll
    assert coll[b1.source_id] == b1
    assert coll[str(b1.source_urn.value)] == b1
    assert coll.get(b1.source_id) == b1
    assert coll.get("missing") is None
    assert coll.get_any(SourceID("00000000-0000-4000-8000-999999999999")) is None
    assert coll.get_any("missing") is None

    with pytest.raises(RecordNotFoundError):
        _ = coll["00000000-0000-4000-8000-999999999999"]

    # Duplicate ID and duplicate URN detection
    with pytest.raises(DuplicateRecordError):
        coll.add(b1)
    with pytest.raises(DuplicateRecordError):
        coll.add(_make_birth(99, urn_suffix="BIR001"))

    # Edit record & verify re-indexing + audit touch
    edited_b1 = coll.edit(
        b1.source_id,
        description="Updated Birth 1",
        place_of_birth_id=LocationID("LOC-000002"),
    )
    assert edited_b1.description == "Updated Birth 1"
    assert len(coll.find_by_location("LOC-000001")) == 1
    assert len(coll.find_by_location("LOC-000002")) == 1

    # Explicit audit pass-through in edit()
    custom_audit = _audit()
    coll.edit(b1.source_id, audit=custom_audit)

    # Edit / update error branches
    with pytest.raises(RecordNotFoundError):
        coll.edit("00000000-0000-4000-8000-999999999999", description="Missing")
    with pytest.raises(RepositoryError, match="Cannot mutate primary key"):
        coll.edit(b1.source_id, source_id=b2.source_id)
    with pytest.raises(RecordNotFoundError):
        coll.update(_make_birth(99))
    with pytest.raises(DuplicateRecordError):
        coll.edit(b1.source_id, source_urn=b2.source_urn)

    # Graveyard & supersession lifecycle
    ok, msg = coll.can_tombstone("00000000-0000-4000-8000-999999999999")
    assert not ok and "does not exist" in (msg or "")
    ok, msg = coll.can_tombstone(b1.source_id, superseded_by=b1.source_id)
    assert not ok and "cannot be the record itself" in (msg or "")
    ok, msg = coll.can_tombstone(
        b1.source_id,
        superseded_by="00000000-0000-4000-8000-999999999999",
    )
    assert not ok and "does not exist" in (msg or "")

    with pytest.raises(RepositoryError, match="reason cannot be empty"):
        coll.soft_delete(b1.source_id, reason="   ")

    retired_b1 = coll.soft_delete(
        b1.source_id,
        reason="Superseded by cleaner scan",
        superseded_by=b2.source_id,
        deprecated_at="2026-02-01T00:00:00Z",
    )
    assert retired_b1.tombstone is not None and retired_b1.tombstone.is_deprecated
    assert len(coll) == 2
    assert len(list(coll)) == 2
    assert b1.source_id not in coll
    assert b1.source_id.value not in coll
    assert str(b1.source_urn.value) not in coll
    assert coll.get_any(b1.source_id) == retired_b1
    assert coll.get_any(b1.source_id.value) == retired_b1
    assert coll.get_any(str(b1.source_urn.value)) == retired_b1
    assert coll.get_any("URN:SRC:1852:US_PA:NONEXISTENT") is None
    assert len(coll.find_tombstoned()) == 1
    assert coll.resolve_active(b1.source_id) == coll[b2.source_id]

    # Edit a record that is already tombstoned
    coll.edit(b1.source_id, description="Still Tombstoned")

    # Cannot tombstone already tombstoned or point to tombstoned replacement
    with pytest.raises(RepositoryError, match="already tombstoned"):
        coll.soft_delete(b1.source_id)
    ok, msg = coll.can_tombstone(b2.source_id, superseded_by=b1.source_id)
    assert not ok and "itself tombstoned" in (msg or "")

    # Tombstone without replacement & test resolve_active error branches
    coll.soft_delete(
        b3_minimal.source_id,
        deprecated_at=IsoTimestamp("2026-02-01T00:00:00Z"),
    )
    with pytest.raises(RepositoryError, match="without a replacement"):
        coll.resolve_active(b3_minimal.source_id)
    with pytest.raises(RecordNotFoundError):
        coll.resolve_active("00000000-0000-4000-8000-999999999999")

    # Cycle detection in resolve_active
    cycle_tomb = Tombstone[SourceID](
        is_deprecated=True,
        deprecated_at=IsoTimestamp("2026-02-01T00:00:00Z"),
        superseded_by=b1.source_id,
    )
    coll.edit(b2.source_id, tombstone=cycle_tomb)
    with pytest.raises(RepositoryError, match="Supersession cycle"):
        coll.resolve_active(b1.source_id)

    # Undelete / restore checks
    ok, msg = coll.can_undelete("00000000-0000-4000-8000-999999999999")
    assert not ok
    coll.undelete(b2.source_id)
    with pytest.raises(RepositoryError, match="not tombstoned"):
        coll.restore(b2.source_id)

    # URN collision when restoring a tombstoned record
    b_dup_urn = _make_birth(4, urn_suffix="BIR001")
    coll.add(b_dup_urn)
    with pytest.raises(RepositoryError, match="already claimed"):
        coll.undelete(b1.source_id)
    coll.edit(b_dup_urn.source_id, source_urn=SourceURN("URN:SRC:1852:US_PA:BIR004"))
    coll.soft_delete(b_dup_urn.source_id)
    restored_b1 = coll.restore(b1.source_id)
    assert not restored_b1.tombstone.is_deprecated  # type: ignore[union-attr]

    # Adding an already-tombstoned record directly
    b5_tomb = dataclasses.replace(
        _make_birth(5),
        tombstone=Tombstone[SourceID](
            is_deprecated=True,
            deprecated_at=IsoTimestamp("2026-02-01T00:00:00Z"),
        ),
    )
    coll.add(b5_tomb)

    # Save to DB (dirty_only and full) & reload / refresh
    written = coll.save_to_db(session_manager=seeded_session, dirty_only=True)
    assert written == 5
    assert coll.is_dirty is False
    assert coll.save_to_db() == 5

    reloaded = BirthCollection.from_database(session_manager=seeded_session)
    assert reloaded.load_from_db(session_manager=seeded_session) == 5
    assert reloaded.refresh() == 5

    # Export and import JSON file (5 total: 2 active + 3 tombstoned)
    json_path = tmp_path / "births_export.json"
    exported_count = reloaded.export_file(json_path, include_graveyard=True)
    assert exported_count == 5
    active_only_path = tmp_path / "births_active.json"
    assert (
        reloaded.export_file(
            active_only_path,
            include_graveyard=False,
            create_backup=False,
        )
        == 2
    )

    fresh_coll = BirthCollection(repository=reloaded.repository)
    assert fresh_coll.import_file(json_path, mark_dirty=False) == 5
    assert fresh_coll.is_dirty is False
    assert fresh_coll.import_file(active_only_path, mark_dirty=False) == 2
    assert fresh_coll.is_dirty is False
    assert fresh_coll.import_file(json_path, mark_dirty=True) == 5
    assert fresh_coll.is_dirty is True

    bad_json = tmp_path / "bad.json"
    GDAJsonIO.write(bad_json, {"invalid": True})
    with pytest.raises(RepositoryError, match="Invalid source export payload"):
        fresh_coll.import_file(bad_json)
