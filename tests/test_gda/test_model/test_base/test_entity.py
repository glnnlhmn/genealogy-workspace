"""Path: tests/test_gda/test_model/test_base/test_entity.py

Unit, regression, and integration test suite verifying BaseEntity contracts.

Operational Role:
    Verifies that EntityLifecycleMixin, BaseEntity, and BaseEntityGUID enforce
    AtomID and UUID identity typing, delegate audit and tombstone lifecycle states,
    manage embedded Note collections (add_note, delete_note, get_note, find_notes
    with filtering and sorting across all fields), execute copy-on-write mutators,
    and guarantee immutability.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from gda.enums.archival import NoteType
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import FactID, IndividualID, NoteID
from gda.model.base.audit import AuditStamp
from gda.model.base.entity import BaseEntity, BaseEntityGUID
from gda.model.base.note import Note
from gda.model.base.tombstone import Tombstone

__version__ = "1.1.0+build.9"


# ==============================================================================
# GROUP 1: BASEENTITY CREATION & DELEGATION
# Note: Verification of instantiation, property delegation, and embedded notes
# ==============================================================================


@pytest.mark.unit
def test_base_entity_default_creation(golden_audit: AuditStamp) -> None:
    """Verify BaseEntity instantiates with default tombstone and empty notes."""
    eid = IndividualID("IND-000001")
    entity: BaseEntity[IndividualID] = BaseEntity(id=eid, audit=golden_audit)

    assert entity.id == eid
    assert entity.audit == golden_audit
    assert entity.created_at == golden_audit.created_at
    assert entity.updated_at == golden_audit.updated_at
    assert entity.is_deprecated is False
    assert entity.superseded_by is None
    assert entity.has_notes is False
    assert entity.note_count == 0
    assert entity.notes == []
    assert "notes=[]" in repr(entity)


@pytest.mark.unit
def test_base_entity_deprecated_with_notes(
    golden_audit: AuditStamp, sample_note: Note
) -> None:
    """Verify BaseEntity with deprecated tombstone and embedded Note instance."""
    eid = IndividualID("IND-000001")
    tombstone = Tombstone[IndividualID](
        is_deprecated=True,
        deprecated_at=golden_audit.updated_at,
        superseded_by=IndividualID("IND-000002"),
    )

    entity: BaseEntity[IndividualID] = BaseEntity(
        id=eid,
        audit=golden_audit,
        tombstone=tombstone,
        notes=[sample_note],
    )
    assert entity.is_deprecated is True
    assert entity.superseded_by == IndividualID("IND-000002")
    assert entity.has_notes is True
    assert entity.note_count == 1
    assert entity.notes == [sample_note]


@pytest.mark.regression
def test_base_entity_superseded_by_type_mismatch_raises_type_error(
    golden_audit: AuditStamp,
) -> None:
    """Verify BaseEntity raises TypeError if superseded_by ID type conflicts with entity ID."""
    eid = IndividualID("IND-000001")
    conflicting_target = FactID("FID-000002")
    tombstone = Tombstone(
        is_deprecated=True,
        deprecated_at=golden_audit.created_at,
        superseded_by=conflicting_target,  # type: ignore[arg-type]
    )

    with pytest.raises(TypeError, match="superseded_by type mismatch"):
        BaseEntity(id=eid, audit=golden_audit, tombstone=tombstone)


# ==============================================================================
# GROUP 2: LIFECYCLE MUTATORS (TOUCH, DEPRECATE, RESTORE)
# Note: Verification of touch, deprecate, and restore copy-on-write transitions
# ==============================================================================


@pytest.mark.regression
def test_base_entity_touch_and_is_modified(
    golden_audit: AuditStamp, advanced_timestamp: IsoTimestamp
) -> None:
    """Verify touch returns an entity copy and is_modified flags true."""
    eid = IndividualID("IND-000001")
    entity = BaseEntity(id=eid, audit=golden_audit)
    assert entity.is_modified is False

    touched = entity.touch(advanced_timestamp)
    assert touched is not entity
    assert touched.id == entity.id
    assert touched.created_at == golden_audit.created_at
    assert touched.updated_at == advanced_timestamp
    assert touched.is_modified is True
    assert entity.is_modified is False


@pytest.mark.regression
def test_base_entity_deprecate_and_restore(
    golden_audit: AuditStamp, advanced_timestamp: IsoTimestamp
) -> None:
    """Verify deprecate and restore copy-on-write state cycles."""
    eid = IndividualID("IND-000001")
    succ_id = IndividualID("IND-000002")
    entity = BaseEntity(id=eid, audit=golden_audit)

    deprecated = entity.deprecate(superseded_by=succ_id, timestamp=advanced_timestamp)
    assert deprecated.is_deprecated is True
    assert deprecated.superseded_by == succ_id
    assert deprecated.updated_at == advanced_timestamp

    restore_ts = IsoTimestamp("2026-10-30T16:00:00Z")
    restored = deprecated.restore(timestamp=restore_ts)
    assert restored.is_deprecated is False
    assert restored.superseded_by is None
    assert restored.updated_at == restore_ts


# ==============================================================================
# GROUP 3: EMBEDDED NOTE CONTAINER METHODS & SORTING
# Note: Verification of add_note, delete_note, get_note, and find_notes sorting
# ==============================================================================


@pytest.mark.regression
def test_base_entity_add_note_monotonic_id(golden_audit: AuditStamp) -> None:
    """Verify add_note appends Note with monotonically increasing NoteID."""
    eid = IndividualID("IND-000001")
    entity = BaseEntity(id=eid, audit=golden_audit)

    with_note_1 = entity.add_note("First note memo.", note_type=NoteType.RESEARCH)
    assert with_note_1 is not entity
    assert with_note_1.note_count == 1
    assert with_note_1.notes[0].note_id == NoteID("NOT-000001")
    assert with_note_1.notes[0].text == "First note memo."

    with_note_2 = with_note_1.add_note("Second note memo.", note_type=NoteType.PROOF)
    assert with_note_2.note_count == 2
    assert with_note_2.notes[1].note_id == NoteID("NOT-000002")


@pytest.mark.regression
def test_base_entity_delete_note_gap_preservation(
    sample_entity_with_notes: BaseEntity[IndividualID],
) -> None:
    """Verify delete_note preserves sibling NoteIDs and avoids index compaction using pre-seeded bundle."""
    entity = sample_entity_with_notes
    assert entity.note_count == 6
    assert [str(n.note_id) for n in entity.notes] == [
        "NOT-000001",
        "NOT-000002",
        "NOT-000003",
        "NOT-000004",
        "NOT-000005",
        "NOT-000006",
    ]

    deleted = entity.delete_note("NOT-000004")
    assert [str(n.note_id) for n in deleted.notes] == [
        "NOT-000001",
        "NOT-000002",
        "NOT-000003",
        "NOT-000005",
        "NOT-000006",
    ]

    added_after = deleted.add_note("Note 7")
    assert [str(n.note_id) for n in added_after.notes] == [
        "NOT-000001",
        "NOT-000002",
        "NOT-000003",
        "NOT-000005",
        "NOT-000006",
        "NOT-000007",
    ]


@pytest.mark.regression
def test_base_entity_delete_nonexistent_note_no_op(
    sample_entity_with_notes: BaseEntity[IndividualID],
) -> None:
    """Verify deleting a non-existent note returns the same entity instance."""
    result = sample_entity_with_notes.delete_note("NOT-999999")
    assert result is sample_entity_with_notes


@pytest.mark.regression
def test_base_entity_get_note(
    sample_entity_with_notes: BaseEntity[IndividualID],
) -> None:
    """Verify get_note retrieves existing note by ID or returns None."""
    found = sample_entity_with_notes.get_note("NOT-000001")
    assert found is not None
    assert "Census records confirm" in found.text

    assert sample_entity_with_notes.get_note("NOT-999999") is None


@pytest.mark.regression
def test_base_entity_find_notes_filtering_and_sorting(
    sample_entity_with_notes: BaseEntity[IndividualID],
) -> None:
    """Verify find_notes filters and sorts across 6-note bundle distribution (3/2/1)."""
    entity = sample_entity_with_notes

    # 3 / 2 / 1 distribution verification
    assert len(entity.find_notes(note_type=NoteType.RESEARCH)) == 3
    assert len(entity.find_notes(note_type=NoteType.DISCREPANCY)) == 2
    assert len(entity.find_notes(note_type="PROOF")) == 1
    assert len(entity.find_notes(note_type=NoteType.GENERAL)) == 0

    # Tag and substring filters
    assert len(entity.find_notes(tag="census")) == 1
    assert len(entity.find_notes(text="merrimack")) == 1

    # Sort checks: note_type ascending & descending
    sorted_by_type = entity.find_notes(sort_by="note_type")
    assert [n.note_type.value for n in sorted_by_type] == [
        "DISCREPANCY",
        "DISCREPANCY",
        "PROOF",
        "RESEARCH",
        "RESEARCH",
        "RESEARCH",
    ]
    sorted_by_type_rev = entity.find_notes(sort_by="note_type", reverse=True)
    assert [n.note_type.value for n in sorted_by_type_rev] == [
        "RESEARCH",
        "RESEARCH",
        "RESEARCH",
        "PROOF",
        "DISCREPANCY",
        "DISCREPANCY",
    ]

    # Sort checks: title ascending & descending
    sorted_by_title = entity.find_notes(sort_by="title")
    assert sorted_by_title[0].title == "Birth Year Conflict"
    assert sorted_by_title[-1].title == "Surname Spelling Variance"

    sorted_by_title_rev = entity.find_notes(sort_by="title", reverse=True)
    assert sorted_by_title_rev[0].title == "Surname Spelling Variance"
    assert sorted_by_title_rev[-1].title == "Birth Year Conflict"

    # Sort checks: updated_at
    sorted_by_date = entity.find_notes(sort_by="updated_at")
    assert len(sorted_by_date) == 6

    # Sort checks: id ascending & descending
    sorted_by_id = entity.find_notes(sort_by="id")
    assert str(sorted_by_id[0].note_id) == "NOT-000001"
    sorted_by_id_rev = entity.find_notes(sort_by="id", reverse=True)
    assert str(sorted_by_id_rev[0].note_id) == "NOT-000006"

    # Unrecognized sort_by returns results in existing order
    unrecognized = entity.find_notes(sort_by="unrecognized")  # type: ignore[arg-type]
    assert len(unrecognized) == 6


# ==============================================================================
# GROUP 4: BASEENTITYGUID & SERIALIZATION
# Note: Verification of BaseEntityGUID operations and dictionary serialization
# ==============================================================================


@pytest.mark.unit
def test_base_entity_guid_valid_creation(
    golden_guid: str, golden_audit: AuditStamp
) -> None:
    """Verify BaseEntityGUID instantiates with string surrogate ID and delegates audit."""
    entity = BaseEntityGUID(id=golden_guid, audit=golden_audit)
    assert entity.id == golden_guid
    assert entity.audit == golden_audit
    assert entity.created_at == golden_audit.created_at
    assert entity.updated_at == golden_audit.updated_at
    assert entity.is_deprecated is False
    assert entity.notes == []
    assert "BaseEntityGUID" in repr(entity)


@pytest.mark.regression
def test_base_entity_guid_container_and_lifecycle_operations(
    golden_guid: str, golden_audit: AuditStamp
) -> None:
    """Verify BaseEntityGUID add_note, delete_note, get_note, and restore."""
    target_guid = "b2c3d4e5-f6a7-4b8c-9d0e-1f2a3b4c5d6e"
    entity = BaseEntityGUID(id=golden_guid, audit=golden_audit)

    with_note = entity.add_note("Digital artifact memo", note_type=NoteType.PROOF)
    assert with_note.note_count == 1
    assert with_note.notes[0].note_id == NoteID("NOT-000001")
    assert with_note.get_note("NOT-000001") is not None

    deleted = with_note.delete_note("NOT-000001")
    assert deleted.note_count == 0

    deprecated = entity.deprecate(superseded_by=target_guid)
    assert deprecated.is_deprecated is True
    assert deprecated.superseded_by == target_guid

    restored = deprecated.restore()
    assert restored.is_deprecated is False
    assert restored.superseded_by is None


@pytest.mark.regression
def test_base_entity_guid_superseded_by_type_mismatch_raises_type_error(
    golden_guid: str, golden_audit: AuditStamp
) -> None:
    """Verify BaseEntityGUID raises TypeError if superseded_by is not a string."""
    wrong_target = IndividualID("IND-000002")
    tombstone = Tombstone(
        is_deprecated=True,
        deprecated_at=golden_audit.created_at,
        superseded_by=wrong_target,  # type: ignore[arg-type]
    )

    with pytest.raises(TypeError, match="superseded_by type mismatch: expected str"):
        BaseEntityGUID(id=golden_guid, audit=golden_audit, tombstone=tombstone)


@pytest.mark.integration
def test_base_entity_to_dict_serialization(
    golden_audit: AuditStamp, sample_note: Note
) -> None:
    """Verify to_dict serialization converts entity and embedded notes into dictionary."""
    eid = IndividualID("IND-000001")
    entity = BaseEntity(id=eid, audit=golden_audit, notes=[sample_note])

    data = entity.to_dict()
    assert data["id"] == "IND-000001"
    assert data["audit"]["created_at"] == str(golden_audit.created_at)
    assert data["tombstone"]["is_deprecated"] is False
    assert len(data["notes"]) == 1
    assert data["notes"][0]["note_id"] == "NOT-000001"
    assert data["notes"][0]["text"] == sample_note.text


# ==============================================================================
# GROUP 5: IMMUTABILITY & INTROSPECTION
# Note: Verification of frozen immutability and introspection directory
# ==============================================================================


@pytest.mark.regression
def test_base_entity_immutability(golden_audit: AuditStamp) -> None:
    """Verify BaseEntity and BaseEntityGUID instances are frozen and immutable."""
    eid = IndividualID("IND-000001")
    entity = BaseEntity(id=eid, audit=golden_audit)

    with pytest.raises((FrozenInstanceError, TypeError)):
        entity.notes = []  # type: ignore[misc]


@pytest.mark.regression
def test_base_entity_introspection(golden_audit: AuditStamp) -> None:
    """Verify .help() renders member directory on BaseEntity and BaseEntityGUID."""
    eid = IndividualID("IND-000001")
    entity = BaseEntity(id=eid, audit=golden_audit)

    help_text = entity.help(as_str=True)
    assert help_text is not None
    assert "=== BaseEntity Public Directory ===" in help_text
    assert "add_note" in help_text
    assert "delete_note" in help_text
    assert "find_notes" in help_text
    assert "touch" in help_text
    assert "deprecate" in help_text
    assert "restore" in help_text
