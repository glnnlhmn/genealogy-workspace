"""Path: tests/test_gda/test_model/test_base/test_comp_envelopes/conftest.py

Shared pytest fixtures for Batch 3 (tier-2 composite & entity envelope) models.

Operational Role:
    Provides canonical Note, SourceURN, and seeded BaseEntity note-distribution
    fixtures for in-memory unit and regression testing across source, entity, and
    envelope modules. Tier-0 and Batch-1 primitives are inherited from
    tests/test_gda/test_model/test_base/conftest.py.
"""

from __future__ import annotations

import pytest

from gda.core.enums.archival import NoteType
from gda.model.atom.id import IndividualID, NoteID
from gda.model.atom.urn import SourceURN
from gda.model.base.audit import AuditStamp
from gda.model.base.entity import BaseEntity
from gda.model.base.note import Note

__version__ = "1.1.0+build.1"


@pytest.fixture
def sample_source_urn() -> SourceURN:
    """Return canonical synthetic SourceURN."""
    return SourceURN("URN:SRC:1880:NH_MERRIMACK:DOC_000101")


@pytest.fixture
def sample_note(golden_audit: AuditStamp) -> Note:
    """Return canonical Note fixture."""
    return Note(
        note_id=NoteID("NOT-000001"),
        note_type=NoteType.RESEARCH,
        text="Baseline archival research note.",
        audit=golden_audit,
        title="Baseline Note",
    )


@pytest.fixture
def sample_entity_with_notes(golden_audit: AuditStamp) -> BaseEntity[IndividualID]:
    """Return BaseEntity seeded with 6 notes in a 3 RESEARCH / 2 DISCREPANCY / 1 PROOF distribution."""
    notes = [
        Note(
            note_id=NoteID("NOT-000001"),
            note_type=NoteType.RESEARCH,
            text="Census records confirm residence in Bow.",
            title="Census Residence",
            tags=["census", "bow"],
            audit=golden_audit,
        ),
        Note(
            note_id=NoteID("NOT-000002"),
            note_type=NoteType.DISCREPANCY,
            text="Birth year differs between 1870 and 1880 schedules.",
            title="Birth Year Conflict",
            tags=["census"],
            audit=golden_audit,
        ),
        Note(
            note_id=NoteID("NOT-000003"),
            note_type=NoteType.PROOF,
            text="Probate administration establishes filial link.",
            title="Filial Proof Argument",
            tags=["probate"],
            audit=golden_audit,
        ),
        Note(
            note_id=NoteID("NOT-000004"),
            note_type=NoteType.RESEARCH,
            text="Deed index shows land transfer in Merrimack County.",
            title="Deed Transfer",
            tags=["deed"],
            audit=golden_audit,
        ),
        Note(
            note_id=NoteID("NOT-000005"),
            note_type=NoteType.DISCREPANCY,
            text="Gravestone spelling diverges from vital register.",
            title="Surname Spelling Variance",
            tags=["cemetery"],
            audit=golden_audit,
        ),
        Note(
            note_id=NoteID("NOT-000006"),
            note_type=NoteType.RESEARCH,
            text="Town meeting minutes list highway surveyor appointment.",
            title="Civic Appointment",
            tags=["civic"],
            audit=golden_audit,
        ),
    ]
    return BaseEntity(id=IndividualID("IND-000001"), audit=golden_audit, notes=notes)
