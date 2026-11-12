"""Path: tests/test_gda/test_model/test_base/test_composites/conftest.py

Shared pytest fixtures for Batch 2 (tier-1 composite) value objects.

Operational Role:
    Provides canonical Note, Media, Transcript, NamePerson, HistoricVariant,
    and NameThing fixtures for in-memory unit and regression testing across
    gda.model.base composite modules. Tier-0 and Batch-1 primitives are inherited
    from tests/test_gda/test_model/test_base/conftest.py.
"""

from __future__ import annotations

from typing import Any

import pytest

from gda.core.enums.archival import DocumentSide, Legibility, NoteType, TextQuality
from gda.core.enums.vital import HistoricNameType
from gda.model.atom.id import MediaID, NoteID, TranscriptID
from gda.model.base.audit import AuditStamp
from gda.model.base.date import TimePeriod
from gda.model.base.media import Media
from gda.model.base.name import HistoricVariant, NamePerson, NameThing
from gda.model.base.note import Note
from gda.model.base.transcript import Transcript

__version__ = "1.1.0+build.1"


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
    return "   \t\n  "


@pytest.fixture
def failure_note_payload_missing_keys() -> dict[str, Any]:
    """Return incomplete Note dictionary payload missing required keys."""
    return {"note_id": "NOT-000018", "text": "Incomplete note"}
