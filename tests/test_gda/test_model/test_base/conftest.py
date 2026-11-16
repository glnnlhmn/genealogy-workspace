"""Path: tests/test_gda/test_model/test_base/conftest.py

Shared pytest fixtures for the gda.model.base test suite.

Operational Role:
    Provides composite value object, temporal, onomastic, note, media,
    transcript, source, and entity envelope fixtures for gda.model.base.
"""

from __future__ import annotations

from typing import Any

import pytest

from gda.core.enums.archival import DocumentSide, Legibility, NoteType, TextQuality
from gda.core.enums.date import DateModifier
from gda.core.enums.vital import HistoricNameType
from gda.model.atom.date import DateString, IsoTimestamp
from gda.model.atom.id import IndividualID, MediaID, NoteID, SiteID, TranscriptID
from gda.model.atom.urn import SourceURN
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate, TimePeriod
from gda.model.base.entity import BaseEntity
from gda.model.base.media import Media
from gda.model.base.name import HistoricVariant, NamePerson, NameThing
from gda.model.base.note import Note
from gda.model.base.transcript import Transcript

__version__ = "1.0.0+build.3"


@pytest.fixture(scope="session")
def golden_time_period() -> TimePeriod:
    """Return canonical 1751-1810 TimePeriod fixture for gda.model.base composites."""
    return TimePeriod(
        start_date=EventDate(date=DateString("1751"), modifier=DateModifier.EXACT),
        end_date=EventDate(date=DateString("1810"), modifier=DateModifier.EXACT),
    )


@pytest.fixture
def sample_individual_id() -> IndividualID:
    """Return canonical IndividualID."""
    return IndividualID("IND-000101")


@pytest.fixture
def failure_blank_text() -> str:
    """Return whitespace-only string for negative validation checks."""
    return " \t\n "


@pytest.fixture
def ts_created() -> IsoTimestamp:
    """Return canonical creation IsoTimestamp."""
    return IsoTimestamp("2026-10-16T10:00:00Z")


@pytest.fixture
def ts_updated() -> IsoTimestamp:
    """Return canonical updated IsoTimestamp strictly after ts_created."""
    return IsoTimestamp("2026-10-16T12:00:00Z")


@pytest.fixture
def sample_audit(ts_created: IsoTimestamp) -> AuditStamp:
    """Return synchronized AuditStamp."""
    return AuditStamp(created_at=ts_created, updated_at=ts_created)


@pytest.fixture
def sample_site_id() -> SiteID:
    """Return canonical SiteID."""
    return SiteID("SID-000888")


@pytest.fixture
def event_date_1850() -> EventDate:
    """Return exact EventDate for 1850."""
    return EventDate(date=DateString("1850"), modifier=DateModifier.EXACT)


@pytest.fixture
def event_date_1910() -> EventDate:
    """Return exact EventDate for 1910."""
    return EventDate(date=DateString("1910"), modifier=DateModifier.EXACT)


@pytest.fixture
def sample_note(golden_audit: AuditStamp) -> Note:
    """Return canonical Note fixture."""
    return Note(
        note_id=NoteID("NOT-000003"),
        note_type=NoteType.GENERAL,
        text="Baseline archival note text.",
        audit=golden_audit,
    )


@pytest.fixture
def sample_media(golden_audit: AuditStamp) -> Media:
    """Return canonical Media fixture."""
    return Media(
        media_id=MediaID("a1b2c3d4-e5f6-4a1b-8c2d-3e4f5a6b7c8d"),
        file_name="census_1880_page_12.jpg",
        mime_type="image/jpeg",
        audit=golden_audit,
        side=DocumentSide.FRONT,
        description="1880 Federal Census scan",
    )


@pytest.fixture
def sample_transcript(golden_audit: AuditStamp) -> Transcript:
    """Return canonical Transcript fixture."""
    return Transcript(
        transcript_id=TranscriptID("11111111-1111-4111-8111-111111111111"),
        verbatim_text="In the name of God, Amen. I, John Doe...",
        audit=golden_audit,
        text_quality=TextQuality.VERBATIM,
        legibility=Legibility.CLEAR,
    )


@pytest.fixture
def sample_name_person() -> NamePerson:
    """Return fully populated NamePerson fixture."""
    return NamePerson(
        raw="Col. John Quincy Adams Jr.",
        canonical="John Quincy Adams Jr.",
        prefix="Col.",
        given="John",
        middle="Quincy",
        surname="Adams",
        suffix="Jr.",
        married=["Adams-Smith"],
        aliases=["Old Man Eloquent"],
        alt_spellings=["Addams"],
    )


@pytest.fixture
def sample_historic_variant(golden_time_period: TimePeriod) -> HistoricVariant:
    """Return canonical HistoricVariant fixture."""
    return HistoricVariant(
        raw="Derryfield",
        name="Manchester",
        historic_name_type=HistoricNameType.HISTORICAL,
        valid_period=golden_time_period,
        comment="Chartered in 1751, renamed Manchester in 1810.",
    )


@pytest.fixture
def sample_name_thing(sample_historic_variant: HistoricVariant) -> NameThing:
    """Return canonical NameThing fixture."""
    return NameThing(
        raw="City of Manchester",
        canonical="Manchester",
        aliases=["Queen City"],
        alt_spellings=["Manchestir"],
        historic=[sample_historic_variant],
    )


@pytest.fixture
def failure_note_blank_text() -> str:
    """Return whitespace-only string for negative validation checks."""
    return " \t\n "


@pytest.fixture
def failure_note_payload_missing_keys() -> dict[str, Any]:
    """Return incomplete Note dictionary payload missing required keys."""
    return {"note_id": "NOT-000018", "text": "Incomplete note"}


@pytest.fixture
def sample_source_urn() -> SourceURN:
    """Return canonical synthetic SourceURN."""
    return SourceURN("URN:SRC:1880:NH_MERRIMACK:DOC_000101")


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
