"""Path: tests/test_gda/test_model/test_base/test_note.py

Comprehensive test suite verifying Note and NoteType contracts.

Operational Role:
    Verifies that Note enforces valid NoteID identifiers, NoteType enums,
    non-empty text, AuditStamp composition, update_text helpers, and immutability.

Test Structure & Protocol:
    - Atomized tests: 1:1 behavioral contract mapping.
    - Fully decorated: Standard 7-marker taxonomy.
    - Zero production disk I/O.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from gda.core.errors import ModelFormatError
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import NoteID
from gda.model.base.audit import AuditStamp
from gda.model.base.note import Note, NoteType

__version__ = "1.0.0+build.5"


# ==============================================================================
# GROUP 1: NOTE CREATION & TEXT VALIDATION
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_note_valid_creation() -> None:
    """Verify Note instantiates with complete attributes."""
    nid = NoteID("NOT-000001")
    t1 = IsoTimestamp("2026-10-16T12:00:00Z")
    audit = AuditStamp(created_at=t1, updated_at=t1)

    note = Note(
        note_id=nid,
        note_type=NoteType.RESEARCH,
        text="Discrepancy noted in 1880 census enumeration.",
        audit=audit,
    )
    assert note.note_id == nid
    assert note.note_type == NoteType.RESEARCH
    assert note.text == "Discrepancy noted in 1880 census enumeration."
    assert note.audit == audit
    assert repr(note) == (
        "Note(note_id=NoteID(value='NOT-000001'), note_type=RESEARCH, "
        "text='Discrepancy noted in 1880 census enumeration.', "
        "audit=AuditStamp(created_at=IsoTimestamp(value='2026-10-16T12:00:00Z'), "
        "updated_at=IsoTimestamp(value='2026-10-16T12:00:00Z')))"
    )


@pytest.mark.unit
@pytest.mark.regression
@pytest.mark.parametrize("empty_text", ["", "   ", "\t\n"])
def test_note_empty_text_raises_error(empty_text: str) -> None:
    """Verify Note raises ModelFormatError if text is blank or whitespace."""
    nid = NoteID("NOT-000001")
    t1 = IsoTimestamp("2026-10-16T12:00:00Z")
    audit = AuditStamp(created_at=t1, updated_at=t1)

    with pytest.raises(ModelFormatError, match="text cannot be empty"):
        Note(
            note_id=nid,
            note_type=NoteType.GENERAL,
            text=empty_text,
            audit=audit,
        )


# ==============================================================================
# GROUP 2: UPDATE_TEXT HELPER & IMMUTABILITY
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_note_update_text_helper() -> None:
    """Verify .update_text() returns a new Note with refreshed text and audit."""
    nid = NoteID("NOT-000001")
    t1 = IsoTimestamp("2026-10-16T12:00:00Z")
    t2 = IsoTimestamp("2026-10-16T14:00:00Z")
    initial_audit = AuditStamp(created_at=t1, updated_at=t1)

    note = Note(
        note_id=nid,
        note_type=NoteType.CITATION,
        text="Original citation memo.",
        audit=initial_audit,
    )

    new_audit = initial_audit.touch(t2)
    updated_note = note.update_text("Corrected citation volume 42.", new_audit)

    assert updated_note is not note
    assert note.text == "Original citation memo."
    assert updated_note.text == "Corrected citation volume 42."
    assert updated_note.audit.updated_at == t2


@pytest.mark.unit
def test_note_immutability() -> None:
    """Verify Note is frozen and immutable."""
    nid = NoteID("NOT-000001")
    t1 = IsoTimestamp("2026-10-16T12:00:00Z")
    audit = AuditStamp(created_at=t1, updated_at=t1)

    note = Note(
        note_id=nid,
        note_type=NoteType.GENERAL,
        text="Fixed note text.",
        audit=audit,
    )
    with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
        note.text = "Attempted overwrite."  # type: ignore[misc]


@pytest.mark.unit
def test_note_type_enumeration_members() -> None:
    """Verify NoteType contains all standardized archival categories."""
    expected = {
        "RESEARCH",
        "CITATION",
        "TRANSCRIPTION",
        "DISCREPANCY",
        "ANALYSIS",
        "GENERAL",
    }
    actual = {m.value for m in NoteType}
    assert actual == expected


@pytest.mark.unit
def test_note_introspection() -> None:
    """Verify .help() renders member directory on Note."""
    nid = NoteID("NOT-000001")
    t1 = IsoTimestamp("2026-10-16T12:00:00Z")
    audit = AuditStamp(created_at=t1, updated_at=t1)

    note = Note(
        note_id=nid,
        note_type=NoteType.ANALYSIS,
        text="Analysis text.",
        audit=audit,
    )
    help_text = note.help(as_str=True)
    assert help_text is not None
    assert "=== Note Public Directory ===" in help_text
    assert "update_text" in help_text
