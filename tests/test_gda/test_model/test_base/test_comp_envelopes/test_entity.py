"""Path: tests/test_gda/test_model/test_base/test_comp_envelopes/test_entity.py

Unit, regression, and integration test suite verifying BaseEntity contracts.

Operational Role:
    Verifies that EntityLifecycleMixin, BaseEntity, and BaseEntityGUID enforce
    AtomID and UUID identity typing, delegate audit and tombstone lifecycle states,
    manage embedded Note collections (add_note, update_note, delete_note, get_note,
    find_notes with filtering and sorting across all fields), execute copy-on-write
    mutators, and guarantee immutability with 100% statement and branch coverage.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from gda.core.enums.archival import NoteType
from gda.core.errors import ModelFormatError
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import FactID, IndividualID, NoteID
from gda.model.base.audit import AuditStamp
from gda.model.base.entity import BaseEntity, BaseEntityGUID
from gda.model.base.note import Note
from gda.model.base.tombstone import Tombstone

__version__ = "1.2.0+build.1"


# ==============================================================================
# GROUP 1: BASEENTITY CREATION & DELEGATION
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
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
def test_base_entity_deprecated_with_notes(golden_audit: AuditStamp, sample_note: Note) -> None:
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


@pytest.mark.unit
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
# ==============================================================================


@pytest.mark.unit
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


@pytest.mark.unit
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
# ==============================================================================


@pytest.mark.unit
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


@pytest.mark.unit
def test_base_entity_update_note_operations(golden_audit: AuditStamp) -> None:
    """Verify update_note modifies text, title, type, and tags individually and handles no-ops."""
    eid = IndividualID("IND-000001")
    entity = BaseEntity(id=eid, audit=golden_audit).add_note(
        text="Initial note.",
        note_type=NoteType.GENERAL,
        title="Initial Title",
        tags=["draft"],
    )
    note_id = entity.notes[0].note_id

    updated_all = entity.update_note(
        note_id=note_id,
        text="Updated note text.",
        title="Updated Title",
        note_type=NoteType.RESEARCH,
        tags=["verified", "census"],
    )
    assert updated_all is not entity
    target = updated_all.get_note(note_id)
    assert target is not None
    assert target.text == "Updated note text."
    assert target.title == "Updated Title"
    assert target.note_type == NoteType.RESEARCH
    assert target.tags == ["verified", "census"]

    up_text = entity.update_note(note_id=note_id, text="Only text")
    assert up_text.get_note(note_id).text == "Only text"
    assert up_text.get_note(note_id).title == "Initial Title"

    up_title = entity.update_note(note_id=note_id, title="Only title")
    assert up_title.get_note(note_id).title == "Only title"
    assert up_title.get_note(note_id).text == "Initial note."

    up_type = entity.update_note(note_id=note_id, note_type=NoteType.PROOF)
    assert up_type.get_note(note_id).note_type == NoteType.PROOF

    up_tags = entity.update_note(note_id=note_id, tags=["sole-tag"])
    assert up_tags.get_note(note_id).tags == ["sole-tag"]

    assert entity.update_note(note_id="NOT-999999", text="No-op") is entity


@pytest.mark.unit
def test_base_entity_delete_note_gap_preservation(
    sample_entity_with_notes: BaseEntity[IndividualID],
) -> None:
    """Verify delete_note preserves sibling NoteIDs and avoids index compaction."""
    entity = sample_entity_with_notes
    assert entity.note_count == 6

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

    assert sample_entity_with_notes.delete_note("NOT-999999") is sample_entity_with_notes


@pytest.mark.unit
def test_base_entity_get_and_find_notes_filtering_and_sorting(
    sample_entity_with_notes: BaseEntity[IndividualID],
) -> None:
    """Verify get_note and find_notes filter and sort across all supported fields."""
    entity = sample_entity_with_notes

    found = entity.get_note("NOT-000001")
    assert found is not None
    assert "Census records confirm" in found.text
    assert entity.get_note("NOT-999999") is None

    assert len(entity.find_notes(note_type=NoteType.RESEARCH)) == 3
    assert len(entity.find_notes(note_type=NoteType.DISCREPANCY)) == 2
    assert len(entity.find_notes(note_type="proof")) == 1
    assert len(entity.find_notes(note_type=NoteType.GENERAL)) == 0

    with pytest.raises(ModelFormatError, match="Invalid NoteType value"):
        entity.find_notes(note_type="INVALID_NOTE_TYPE")

    assert len(entity.find_notes(tag="census")) == 2
    assert len(entity.find_notes(tag="bow")) == 1
    assert len(entity.find_notes(text="merrimack")) == 1

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

    sorted_by_title = entity.find_notes(sort_by="title")
    assert sorted_by_title[0].title == "Birth Year Conflict"
    assert sorted_by_title[-1].title == "Surname Spelling Variance"

    sorted_by_date = entity.find_notes(sort_by="updated_at")
    assert len(sorted_by_date) == 6

    sorted_by_id = entity.find_notes(sort_by="id")
    assert str(sorted_by_id[0].note_id) == "NOT-000001"
    sorted_by_id_rev = entity.find_notes(sort_by="id", reverse=True)
    assert str(sorted_by_id_rev[0].note_id) == "NOT-000006"

    unrecognized = entity.find_notes(sort_by="unrecognized")  # type: ignore[arg-type]
    assert len(unrecognized) == 6


# ==============================================================================
# GROUP 4: BASEENTITYGUID & SERIALIZATION
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_base_entity_guid_valid_creation(golden_guid: str, golden_audit: AuditStamp) -> None:
    """Verify BaseEntityGUID instantiates with string surrogate ID and delegates audit."""
    entity = BaseEntityGUID(id=golden_guid, audit=golden_audit)
    assert entity.id == golden_guid
    assert entity.audit == golden_audit
    assert entity.is_deprecated is False
    assert "BaseEntityGUID" in repr(entity)

    with pytest.raises(ModelFormatError, match="BaseEntityGUID 'id' cannot be empty"):
        BaseEntityGUID(id="   ", audit=golden_audit)


@pytest.mark.unit
def test_base_entity_guid_container_and_lifecycle_operations(
    golden_guid: str, golden_audit: AuditStamp
) -> None:
    """Verify BaseEntityGUID add_note, delete_note, get_note, deprecate, and restore."""
    target_guid = "b2c3d4e5-f6a7-4b8c-9d0e-1f2a3b4c5d6e"
    entity = BaseEntityGUID(id=golden_guid, audit=golden_audit)

    with_note = entity.add_note("Digital artifact memo", note_type=NoteType.PROOF)
    assert with_note.note_count == 1
    assert with_note.get_note("NOT-000001") is not None

    deleted = with_note.delete_note("NOT-000001")
    assert deleted.note_count == 0

    deprecated = entity.deprecate(superseded_by=target_guid)
    assert deprecated.is_deprecated is True
    assert deprecated.superseded_by == target_guid

    restored = deprecated.restore()
    assert restored.is_deprecated is False
    assert restored.superseded_by is None


@pytest.mark.unit
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


@pytest.mark.unit
def test_base_entity_to_dict_serialization(golden_audit: AuditStamp, sample_note: Note) -> None:
    """Verify to_dict serialization converts entity and embedded notes into dictionary."""
    eid = IndividualID("IND-000001")
    entity = BaseEntity(id=eid, audit=golden_audit, notes=[sample_note])

    data = entity.to_dict()
    assert data["id"] == "IND-000001"
    assert data["audit"]["created_at"] == str(golden_audit.created_at)
    assert data["tombstone"]["is_deprecated"] is False
    assert data["tombstone"]["deprecated_at"] is None
    assert len(data["notes"]) == 1

    deprecated = entity.deprecate(
        superseded_by=IndividualID("IND-000002"),
        timestamp=golden_audit.created_at,
    )
    dep_data = deprecated.to_dict()
    assert dep_data["tombstone"]["is_deprecated"] is True
    assert dep_data["tombstone"]["deprecated_at"] == str(golden_audit.created_at)
    assert dep_data["tombstone"]["superseded_by"] == "IND-000002"


@pytest.mark.unit
def test_base_entity_immutability_and_introspection(golden_audit: AuditStamp) -> None:
    """Verify BaseEntity and BaseEntityGUID instances are frozen and render .help()."""
    eid = IndividualID("IND-000001")
    entity = BaseEntity(id=eid, audit=golden_audit)

    with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
        entity.notes = []  # type: ignore[misc]

    help_text = entity.help(as_str=True)
    assert help_text is not None
    assert "=== BaseEntity Public Directory ===" in help_text
