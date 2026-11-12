"""Path: tests/test_gda/test_model/test_entity/conftest.py

Shared pytest fixtures for the gda.model.entity test suite.
"""

from __future__ import annotations

import pytest

from gda.core.enums.archival import NoteType
from gda.core.enums.date import DateModifier
from gda.model.atom.date import DateString, IsoTimestamp
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate, TimePeriod
from gda.model.base.note import Note

__version__ = "1.0.0+build.2"


@pytest.fixture(scope="session")
def golden_timestamp() -> IsoTimestamp:
    """Provide a canonical UTC timestamp fixture."""
    return IsoTimestamp("2026-10-18T12:00:00Z")


@pytest.fixture(scope="session")
def golden_audit(golden_timestamp: IsoTimestamp) -> AuditStamp:
    """Provide a canonical AuditStamp fixture."""
    return AuditStamp(created_at=golden_timestamp, updated_at=golden_timestamp)


@pytest.fixture
def golden_time_period() -> TimePeriod:
    """Provide a bounded historical TimePeriod fixture."""
    return TimePeriod(
        start_date=EventDate(date=DateString("1850-01-01"), modifier=DateModifier.EXACT),
        end_date=EventDate(date=DateString("1900-12-31"), modifier=DateModifier.EXACT),
    )


@pytest.fixture
def six_note_bundle() -> list[Note]:
    """Provide a 6-note research bundle spanning multiple NoteType categories."""
    return [
        Note.create(
            note_id="NOT-000001",
            text="Census records confirm residence in Merrimack County.",
            title="Census Residence",
            note_type=NoteType.RESEARCH,
            tags=["census", "merrimack"],
        ),
        Note.create(
            note_id="NOT-000002",
            text="Tombstone inscription lists birth year as 1841 instead of 1842.",
            title="Birth Year Conflict",
            note_type=NoteType.DISCREPANCY,
            tags=["headstone", "conflict"],
        ),
        Note.create(
            note_id="NOT-000003",
            text="Town clerk register verified in Bow archive.",
            title="Register Proof",
            note_type=NoteType.PROOF,
            tags=["bow", "vital"],
        ),
        Note.create(
            note_id="NOT-000004",
            text="Tax inventory lists 40 acres of improved land.",
            title="Tax Assessment",
            note_type=NoteType.RESEARCH,
            tags=["tax", "census"],
        ),
        Note.create(
            note_id="NOT-000005",
            text="Surname spelled Smyth on militia muster roll.",
            title="Surname Spelling Variance",
            note_type=NoteType.DISCREPANCY,
            tags=["spelling", "militia"],
        ),
        Note.create(
            note_id="NOT-000006",
            text="Probate docket names surviving spouse and children.",
            title="Probate Docket",
            note_type=NoteType.RESEARCH,
            tags=["probate"],
        ),
    ]
