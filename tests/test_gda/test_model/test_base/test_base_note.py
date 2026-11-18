"""Path: tests/test_gda/test_model/test_base/test_base_note.py

Unit, regression, and integration test suite verifying the Note value object.

Operational Role:
    Verifies immutable initialization, NoteType enforcement, AuditStamp
    synchronization, copy-on-write mutators for all fields (text, type, title,
    sources, tags), introspection discovery, defensive edge boundaries, and
    serialization round-trips with 100% statement and branch coverage.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from typing import Any

import pytest
from pydantic import ValidationError

from gda.core.enums.archival import NoteType
from gda.core.errors import ModelFormatError
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import NoteID, SourceID
from gda.model.base.audit import AuditStamp
from gda.model.base.note import Note

__version__ = "1.0.0+build.4"


# ==============================================================================
# GROUP 1: INITIALIZATION & FACTORY METHODS
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_note_instantiation_complete(golden_audit: AuditStamp, golden_source_id: SourceID) -> None:
    """Verify Note instantiates with all explicit attributes."""
    note = Note(
        note_id=NoteID("NOT-000001"),
        note_type=NoteType.RESEARCH,
        text="Investigate probate records in Merrimack County.",
        audit=golden_audit,
        title="Probate Search",
        sources=[golden_source_id],
        tags=["probate", "nh"],
    )
    assert note.note_id == NoteID("NOT-000001")
    assert note.note_type == NoteType.RESEARCH
    assert note.text == "Investigate probate records in Merrimack County."
    assert note.title == "Probate Search"
    assert note.sources == [golden_source_id]
    assert note.tags == ["probate", "nh"]
    assert note.audit == golden_audit
    assert note.value == "NOT-000001"
    assert (
        str(note) == "[RESEARCH] Probate Search: Investigate probate records in Merrimack County."
    )
    assert "NOT-000001" in repr(note)


@pytest.mark.unit
@pytest.mark.smoke
def test_note_create_factory_defaults() -> None:
    """Verify Note.create applies default AuditStamp, deduplicates, and normalizes strings."""
    note = Note.create(
        note_id="NOT-000002",
        note_type="proof",
        text="  Proof summary for land transaction.  ",
    )
    assert note.note_id == NoteID("NOT-000002")
    assert note.note_type == NoteType.PROOF
    assert note.text == "Proof summary for land transaction."
    assert note.title is None
    assert note.sources == []
    assert note.tags == []
    assert str(note) == "[PROOF] Proof summary for land transaction."
    assert isinstance(note.audit, AuditStamp)

    with pytest.raises(ModelFormatError, match="Invalid NoteType"):
        Note.create(note_id="NOT-000002", note_type="UNKNOWN_TYPE", text="Valid")

    with pytest.raises(ModelFormatError, match="Invalid NoteType"):
        Note.create(note_id="NOT-000002", note_type=123, text="Valid")  # type: ignore[arg-type]


# ==============================================================================
# GROUP 2: MUTABILITY & COPY-ON-WRITE SEMANTICS
# ==============================================================================


@pytest.mark.unit
def test_note_frozen_immutability(sample_note: Note) -> None:
    """Verify modifying attributes on an existing Note raises FrozenInstanceError."""
    with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
        sample_note.text = "Attempted in-place modification."  # type: ignore[misc]


@pytest.mark.unit
def test_note_update_text_returns_new_instance(
    golden_audit: AuditStamp, advanced_timestamp: IsoTimestamp
) -> None:
    """Verify update_text produces a distinct copy with new text and updated audit."""
    original = Note.create(
        note_id="NOT-000004",
        note_type=NoteType.RESEARCH,
        text="First hypothesis.",
        audit=golden_audit,
        title="Hypothesis A",
    )
    custom_audit = AuditStamp(created_at=golden_audit.created_at, updated_at=advanced_timestamp)
    updated = original.update_text("Revised hypothesis.", audit=custom_audit)

    assert updated is not original
    assert updated.note_id == original.note_id
    assert updated.text == "Revised hypothesis."
    assert updated.title == original.title
    assert updated.note_type == original.note_type
    assert updated.audit == custom_audit

    auto_touched = original.update_text("Second text update.")
    assert auto_touched.audit is not original.audit


@pytest.mark.unit
def test_note_update_type_returns_new_instance(
    golden_audit: AuditStamp, advanced_timestamp: IsoTimestamp
) -> None:
    """Verify update_type produces a distinct copy with new NoteType and updated audit."""
    original = Note.create(
        note_id="NOT-000005",
        note_type=NoteType.RESEARCH,
        text="Identified conflict in census dates.",
        audit=golden_audit,
    )
    updated = original.update_type("discrepancy")

    assert updated is not original
    assert updated.note_id == original.note_id
    assert updated.note_type == NoteType.DISCREPANCY
    assert updated.text == original.text
    assert updated.audit is not original.audit

    custom_audit = AuditStamp(created_at=golden_audit.created_at, updated_at=advanced_timestamp)
    updated_explicit_audit = original.update_type(NoteType.PROOF, audit=custom_audit)
    assert updated_explicit_audit.audit == custom_audit

    with pytest.raises(ModelFormatError, match="Invalid NoteType"):
        original.update_type("BAD_TYPE")

    with pytest.raises(ModelFormatError, match="Invalid NoteType"):
        original.update_type(99)  # type: ignore[arg-type]


@pytest.mark.unit
def test_note_update_title_returns_new_instance(golden_audit: AuditStamp) -> None:
    """Verify update_title updates title and allows clearing to None."""
    original = Note.create(
        note_id="NOT-000006",
        note_type=NoteType.GENERAL,
        text="Note text.",
        audit=golden_audit,
        title="Initial Title",
    )
    updated = original.update_title("Revised Title")
    assert updated.title == "Revised Title"
    assert updated.audit is not original.audit

    cleared = updated.update_title(None)
    assert cleared.title is None


@pytest.mark.unit
def test_note_sources_copy_on_write_mutators(
    golden_source_uuid: str, golden_source_uuid_2: str
) -> None:
    """Verify update_sources, add_source, and remove_source mutators."""
    s1 = golden_source_uuid
    s2 = golden_source_uuid_2
    s3 = "00000000-0000-4000-8000-000000000003"
    s4 = "00000000-0000-4000-8000-000000000004"

    original = Note.create(
        note_id="NOT-000007",
        note_type=NoteType.PROOF,
        text="Evidentiary proof note.",
        sources=[s1, s1],
    )
    assert original.sources == [SourceID(s1)]

    with_added = original.add_source(s2)
    assert with_added.sources == [SourceID(s1), SourceID(s2)]
    assert with_added.add_source(s2) is with_added

    with_removed = with_added.remove_source(s1)
    assert with_removed.sources == [SourceID(s2)]
    assert with_removed.remove_source("00000000-0000-4000-8000-000000000999") is with_removed

    replaced = with_removed.update_sources([s3, s3, s4])
    assert replaced.sources == [SourceID(s3), SourceID(s4)]


@pytest.mark.unit
def test_note_tags_copy_on_write_mutators() -> None:
    """Verify update_tags, add_tag, and remove_tag mutators."""
    original = Note.create(
        note_id="NOT-000008",
        note_type=NoteType.RESEARCH,
        text="Investigate boundary line.",
        tags=["deed", "deed", "boundary"],
    )
    assert original.tags == ["deed", "boundary"]

    with_tag = original.add_tag("concord")
    assert with_tag.tags == ["deed", "boundary", "concord"]
    assert with_tag.add_tag("concord") is with_tag

    with pytest.raises(ModelFormatError, match="Note tag cannot be empty"):
        with_tag.add_tag("   ")

    removed_tag = with_tag.remove_tag("boundary")
    assert removed_tag.tags == ["deed", "concord"]
    assert removed_tag.remove_tag("nonexistent") is removed_tag

    replaced = removed_tag.update_tags(["survey", "survey", "map"])
    assert replaced.tags == ["survey", "map"]


# ==============================================================================
# GROUP 3: DEFENSIVE BOUNDARIES & VALIDATION REJECTION
# ==============================================================================


@pytest.mark.unit
@pytest.mark.regression
def test_note_direct_init_invariants_and_strict_mode(
    golden_audit: AuditStamp,
    golden_source_id: SourceID,
    failure_note_blank_text: str,
) -> None:
    """Verify direct Note() rejects blank text/title, duplicate sources/tags, and non-strict types."""
    with pytest.raises(ModelFormatError, match="Note text cannot be empty or whitespace"):
        Note(
            note_id=NoteID("NOT-000009"),
            note_type=NoteType.GENERAL,
            text=failure_note_blank_text,
            audit=golden_audit,
        )

    with pytest.raises(ModelFormatError, match="Note title cannot be blank if provided"):
        Note(
            note_id=NoteID("NOT-000010"),
            note_type=NoteType.GENERAL,
            text="Valid text.",
            audit=golden_audit,
            title=failure_note_blank_text,
        )

    with pytest.raises(ModelFormatError, match="Duplicate SourceID entries detected"):
        Note(
            note_id=NoteID("NOT-000011"),
            note_type=NoteType.GENERAL,
            text="Valid text.",
            audit=golden_audit,
            sources=[golden_source_id, golden_source_id],
        )

    with pytest.raises(ModelFormatError, match="Note tags cannot contain empty"):
        Note(
            note_id=NoteID("NOT-000012"),
            note_type=NoteType.GENERAL,
            text="Valid text.",
            audit=golden_audit,
            tags=["valid", "   "],
        )

    with pytest.raises(ModelFormatError, match="Duplicate tag entries detected"):
        Note(
            note_id=NoteID("NOT-000013"),
            note_type=NoteType.GENERAL,
            text="Valid text.",
            audit=golden_audit,
            tags=["dup", "dup"],
        )

    with pytest.raises(ValidationError):
        Note(
            note_id="NOT-000014",  # type: ignore[arg-type]
            note_type=NoteType.GENERAL,
            text="Strict mode rejects raw string note_id.",
            audit=golden_audit,
        )


# ==============================================================================
# GROUP 4: SERIALIZATION & INTROSPECTION
# ==============================================================================


@pytest.mark.unit
def test_note_dict_and_json_roundtrip(
    sample_note: Note,
    failure_note_payload_missing_keys: dict[str, Any],
) -> None:
    """Verify Note.to_dict, from_dict, to_json, and from_json round-trips and error paths."""
    d = sample_note.to_dict()
    assert Note.from_dict(d) == sample_note

    d_with_audit_obj = dict(d)
    d_with_audit_obj["audit"] = sample_note.audit
    assert Note.from_dict(d_with_audit_obj) == sample_note

    raw_json = sample_note.to_json()
    assert Note.from_json(raw_json) == sample_note

    with pytest.raises(ModelFormatError, match="Note payload must be a dictionary"):
        Note.from_dict(["not-a-dict"])  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="Missing required fields for Note"):
        Note.from_dict(failure_note_payload_missing_keys)

    bad_audit_dict = dict(d)
    bad_audit_dict["audit"] = {"created_at": "2026-10-16T12:00:00Z"}
    with pytest.raises(ModelFormatError, match="Audit dictionary missing"):
        Note.from_dict(bad_audit_dict)

    bad_audit_type = dict(d)
    bad_audit_type["audit"] = "not-an-audit"
    with pytest.raises(ModelFormatError, match="Note audit must be an AuditStamp or dictionary"):
        Note.from_dict(bad_audit_type)

    with pytest.raises(ModelFormatError, match="Failed to parse Note JSON string"):
        Note.from_json("{invalid_json")


@pytest.mark.unit
def test_note_introspection_help(sample_note: Note) -> None:
    """Verify Note inherits IntrospectableMixin.help()."""
    help_text = sample_note.help(as_str=True)
    assert help_text is not None
    assert "Note Public Directory" in help_text
