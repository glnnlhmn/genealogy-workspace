"""Path: tests/test_gda/test_model/test_base/test_composites/test_note.py

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

__version__ = "1.1.0+build.2"


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

    with pytest.raises(ModelFormatError, match="Invalid NoteType value"):
        Note.create(note_id="NOT-000002", note_type="UNKNOWN_TYPE", text="Valid")

    with pytest.raises(ModelFormatError, match="Invalid NoteType type"):
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

    with pytest.raises(ModelFormatError, match="Invalid NoteType value"):
        original.update_type("BAD_TYPE")

    with pytest.raises(ModelFormatError, match="Invalid NoteType type"):
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

    # add_source
    with_added = original.add_source(s2)
    assert with_added.sources == [SourceID(s1), SourceID(s2)]
    assert with_added.add_source(s2) is with_added

    # remove_source
    with_removed = with_added.remove_source(s1)
    assert with_removed.sources == [SourceID(s2)]
    assert with_removed.remove_source("00000000-0000-4000-8000-000000000999") is with_removed

    # update_sources
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

    # add_tag
    with_tag = original.add_tag("concord")
    assert with_tag.tags == ["deed", "boundary", "concord"]
    assert with_tag.add_tag("concord") is with_tag

    # remove_tag
    removed_tag = with_tag.remove_tag("boundary")
    assert removed_tag.tags == ["deed", "concord"]
    assert removed_tag.remove_tag("nonexistent") is removed_tag

    # update_tags
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
            note_id=NoteID("NOT-000010"),
            note_type=NoteType.GENERAL,
            text="Valid text.",
            audit=golden_audit,
            sources=[golden_source_id, golden_source_id],
        )

    with pytest.raises(ModelFormatError, match="Note tags cannot contain empty or whitespace"):
        Note(
            note_id=NoteID("NOT-000010"),
            note_type=NoteType.GENERAL,
            text="Valid text.",
            audit=golden_audit,
            tags=["   "],
        )

    with pytest.raises(ModelFormatError, match="Duplicate tag entries detected"):
        Note(
            note_id=NoteID("NOT-000010"),
            note_type=NoteType.GENERAL,
            text="Valid text.",
            audit=golden_audit,
            tags=["census", "census"],
        )

    with pytest.raises(ValidationError):
        Note(
            note_id="NOT-000010",  # type: ignore[arg-type]
            note_type=NoteType.GENERAL,
            text="Valid text.",
            audit=golden_audit,
        )


@pytest.mark.unit
@pytest.mark.regression
def test_note_add_tag_empty_rejection(failure_note_blank_text: str) -> None:
    """Verify add_tag raises ModelFormatError on empty or whitespace tag."""
    note = Note.create(
        note_id="NOT-000011",
        note_type=NoteType.GENERAL,
        text="Valid text",
    )
    with pytest.raises(ModelFormatError, match="Note tag cannot be empty or whitespace."):
        note.add_tag(failure_note_blank_text)


@pytest.mark.unit
@pytest.mark.regression
def test_note_extra_fields_forbidden(golden_audit: AuditStamp) -> None:
    """Verify unexpected fields raise ValidationError under extra='forbid'."""
    with pytest.raises(ValidationError):
        Note(
            note_id=NoteID("NOT-000012"),
            note_type=NoteType.GENERAL,
            text="Valid text",
            audit=golden_audit,
            unexpected_field="disallowed",  # type: ignore[call-arg]
        )


@pytest.mark.unit
@pytest.mark.regression
def test_note_invalid_source_id_raises() -> None:
    """Verify adding or creating a note with malformed SourceID raises ModelFormatError."""
    with pytest.raises(ModelFormatError, match="Invalid UUIDv4 format"):
        Note.create(
            note_id="NOT-000013",
            note_type=NoteType.GENERAL,
            text="Valid text",
            sources=["NOT-A-UUID"],
        )

    note = Note.create(
        note_id="NOT-000014",
        note_type=NoteType.GENERAL,
        text="Valid text",
    )
    with pytest.raises(ModelFormatError, match="Invalid UUIDv4 format"):
        note.add_source("INVALID-SOURCE-ID")


@pytest.mark.unit
def test_note_introspection_contract() -> None:
    """Verify IntrospectableMixin .help() execution renders public members."""
    note = Note.create(
        note_id="NOT-000015",
        note_type=NoteType.GENERAL,
        text="Valid text",
    )
    help_text = note.help(as_str=True)
    assert help_text is not None
    assert "=== Note Public Directory ===" in help_text
    assert "update_text" in help_text
    assert "add_source" in help_text


# ==============================================================================
# GROUP 4: SERIALIZATION & DATA ENVELOPE INTEGRATION
# ==============================================================================


@pytest.mark.unit
def test_note_to_dict_and_from_dict_round_trip(
    golden_source_uuid: str, golden_source_uuid_2: str
) -> None:
    """Verify complete dictionary serialization and deserialization fidelity."""
    original = Note.create(
        note_id="NOT-000016",
        note_type=NoteType.PROOF,
        text="Indirect evidence resolves paternity.",
        title="Paternity Proof",
        sources=[golden_source_uuid, golden_source_uuid_2],
        tags=["dna", "probate"],
    )
    payload = original.to_dict()
    assert payload["note_id"] == "NOT-000016"
    assert payload["note_type"] == "PROOF"
    assert payload["title"] == "Paternity Proof"
    assert payload["sources"] == [golden_source_uuid, golden_source_uuid_2]
    assert payload["tags"] == ["dna", "probate"]

    restored = Note.from_dict(payload)
    assert restored == original

    # Direct AuditStamp instance intake
    audit_dict_payload = dict(payload)
    audit_dict_payload["audit"] = original.audit
    restored_from_obj = Note.from_dict(audit_dict_payload)
    assert restored_from_obj == original


@pytest.mark.unit
def test_note_to_json_and_from_json_round_trip() -> None:
    """Verify complete JSON string serialization and parsing fidelity."""
    original = Note.create(
        note_id="NOT-000017",
        note_type=NoteType.DISCREPANCY,
        text="Discrepancy observed between gravestone and family bible.",
    )
    json_str = original.to_json()
    assert isinstance(json_str, str)
    assert "NOT-000017" in json_str

    restored = Note.from_json(json_str)
    assert restored == original


@pytest.mark.unit
@pytest.mark.regression
def test_note_deserialization_errors(
    failure_note_payload_missing_keys: dict[str, Any],
) -> None:
    """Verify from_dict and from_json raise ModelFormatError on invalid payloads."""
    with pytest.raises(ModelFormatError, match="Note payload must be a dictionary."):
        Note.from_dict(["not", "a", "dict"])  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="Missing required fields for Note"):
        Note.from_dict(failure_note_payload_missing_keys)

    with pytest.raises(ModelFormatError, match="Note audit must be an AuditStamp"):
        Note.from_dict(
            {
                "note_id": "NOT-000019",
                "note_type": "GENERAL",
                "text": "Valid text",
                "audit": "not-a-dict",
            }
        )

    with pytest.raises(ModelFormatError, match="Audit dictionary missing created_at"):
        Note.from_dict(
            {
                "note_id": "NOT-000019",
                "note_type": "GENERAL",
                "text": "Valid text",
                "audit": {"created_at": "2026-10-30T10:00:00Z"},
            }
        )

    with pytest.raises(ModelFormatError, match="Failed to parse Note JSON string"):
        Note.from_json("invalid json string {")
