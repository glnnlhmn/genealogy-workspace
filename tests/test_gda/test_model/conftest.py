"""Path: tests/test_gda/test_model/conftest.py

Directory-scoped shared fixtures and factory builders for model tests.

Operational Role:
    Exposes hermetic golden fixtures, chronological timestamps, pre-populated
    6-note test bundles (3 RESEARCH, 2 DISCREPANCY, 1 PROOF), naming fixtures
    (NamePerson, NameThing, HistoricVariant), failure payloads, and factory callables
    across all model test suites (atom, base, entity, xref) in strict adherence
    to topic_test_harness.md.
"""

from __future__ import annotations

from typing import Any

import pytest

from gda.enums.archival import NoteType
from gda.enums.vital import HistoricNameType
from gda.model.atom.date import DateModifier, DateString, EventDate, IsoTimestamp
from gda.model.atom.id import IndividualID, SourceID
from gda.model.base.audit import AuditStamp
from gda.model.base.entity import BaseEntity
from gda.model.base.name import HistoricVariant, NamePerson, NameThing
from gda.model.base.note import Note
from gda.model.base.time_period import TimePeriod
from gda.model.base.tombstone import Tombstone

__version__ = "1.0.0+build.4"

__test__ = False  # Shield conftest from pytest discovery if imported directly


# ==============================================================================
# SECTION 1: TEMPORAL & IDENTIFIER PRIMITIVES
# ==============================================================================


@pytest.fixture
def golden_timestamp() -> IsoTimestamp:
    """Provide a canonical baseline ISO 8601 UTC timestamp."""
    return IsoTimestamp("2026-10-30T12:00:00Z")


@pytest.fixture
def advanced_timestamp() -> IsoTimestamp:
    """Provide a timestamp chronologically advancing after the golden timestamp."""
    return IsoTimestamp("2026-10-30T14:30:00Z")


@pytest.fixture
def golden_time_period() -> TimePeriod:
    """Provide a standard bounded TimePeriod."""
    return TimePeriod(
        start_date=EventDate(date=DateString("1751"), modifier=DateModifier.EXACT),
        end_date=EventDate(date=DateString("1810"), modifier=DateModifier.EXACT),
    )


@pytest.fixture
def golden_source_uuid() -> str:
    """Provide a valid canonical lowercase RFC 4122 UUIDv4 string."""
    return "00000000-0000-4000-8000-000000000001"


@pytest.fixture
def golden_source_uuid_2() -> str:
    """Provide a secondary valid canonical lowercase RFC 4122 UUIDv4 string."""
    return "00000000-0000-4000-8000-000000000002"


@pytest.fixture
def golden_source_id(golden_source_uuid: str) -> SourceID:
    """Provide a strongly-typed SourceID atom."""
    return SourceID(golden_source_uuid)


@pytest.fixture
def golden_guid() -> str:
    """Provide a valid canonical UUIDv4 surrogate identifier."""
    return "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"


# ==============================================================================
# SECTION 2: AUDIT & TOMBSTONE LIFECYCLE FIXTURES
# ==============================================================================


@pytest.fixture
def golden_audit(golden_timestamp: IsoTimestamp) -> AuditStamp:
    """Provide a clean baseline AuditStamp where created_at == updated_at."""
    return AuditStamp(created_at=golden_timestamp, updated_at=golden_timestamp)


@pytest.fixture
def modified_audit(
    golden_timestamp: IsoTimestamp, advanced_timestamp: IsoTimestamp
) -> AuditStamp:
    """Provide an AuditStamp with advanced updated_at for is_modified testing."""
    return AuditStamp(created_at=golden_timestamp, updated_at=advanced_timestamp)


@pytest.fixture
def active_tombstone() -> Tombstone[IndividualID]:
    """Provide a default active, non-deprecated Tombstone record."""
    return Tombstone[IndividualID]()


@pytest.fixture
def deprecated_tombstone(
    advanced_timestamp: IsoTimestamp,
) -> Tombstone[IndividualID]:
    """Provide a tombstoned record with a superseding identifier."""
    return Tombstone[IndividualID](
        is_deprecated=True,
        deprecated_at=advanced_timestamp,
        superseded_by=IndividualID("IND-000002"),
    )


# ==============================================================================
# SECTION 3: EMBEDDED NOTE FIXTURES & 6-NOTE BUNDLE (3 / 2 / 1)
# ==============================================================================


@pytest.fixture
def sample_note(golden_audit: AuditStamp, golden_source_uuid: str) -> Note:
    """Provide a single standard Note instance."""
    return Note.create(
        note_id="NOT-000001",
        note_type=NoteType.RESEARCH,
        text="Standard baseline research observation.",
        audit=golden_audit,
        title="Baseline Research Note",
        sources=[golden_source_uuid],
        tags=["vital", "nh"],
    )


@pytest.fixture
def six_note_bundle(golden_audit: AuditStamp, golden_source_uuid: str) -> list[Note]:
    """Provide a standardized 6-note bundle: 3 RESEARCH, 2 DISCREPANCY, 1 PROOF."""
    return [
        Note.create(
            note_id="NOT-000001",
            note_type=NoteType.RESEARCH,
            text="Census records confirm family residence in Merrimack County.",
            audit=golden_audit,
            title="Census Search 1880",
            sources=[golden_source_uuid],
            tags=["census", "merrimack"],
        ),
        Note.create(
            note_id="NOT-000002",
            note_type=NoteType.RESEARCH,
            text="Will mentions youngest son and land boundaries.",
            audit=golden_audit,
            title="Probate Will Inspection",
            sources=[golden_source_uuid],
            tags=["probate", "deed"],
        ),
        Note.create(
            note_id="NOT-000003",
            note_type=NoteType.RESEARCH,
            text="Grant index shows transfer of 100 acres in Bow.",
            audit=golden_audit,
            title="Land Grant Index",
            sources=[golden_source_uuid],
            tags=["land", "grant"],
        ),
        Note.create(
            note_id="NOT-000004",
            note_type=NoteType.DISCREPANCY,
            text="Gravestone date conflicts with town record by two years.",
            audit=golden_audit,
            title="Birth Year Conflict",
            sources=[golden_source_uuid],
            tags=["vital", "conflict"],
        ),
        Note.create(
            note_id="NOT-000005",
            note_type=NoteType.DISCREPANCY,
            text="Deed records spell surname with double 'n' rather than single.",
            audit=golden_audit,
            title="Surname Spelling Variance",
            sources=[golden_source_uuid],
            tags=["onomastic", "spelling"],
        ),
        Note.create(
            note_id="NOT-000006",
            note_type=NoteType.PROOF,
            text="Correlating tax roll and deed establishes parentage conclusively.",
            audit=golden_audit,
            title="Indirect Evidence Paternity Proof",
            sources=[golden_source_uuid],
            tags=["proof", "paternity"],
        ),
    ]


@pytest.fixture
def sample_entity_with_notes(
    golden_audit: AuditStamp, six_note_bundle: list[Note]
) -> BaseEntity[IndividualID]:
    """Provide a BaseEntity populated with the standardized 6-note bundle."""
    return BaseEntity[IndividualID](
        id=IndividualID("IND-000001"),
        audit=golden_audit,
        tombstone=Tombstone[IndividualID](),
        notes=six_note_bundle,
    )


# ==============================================================================
# SECTION 4: NAMING FIXTURES (NAMEPERSON, NAMETHING, HISTORICVARIANT)
# ==============================================================================


@pytest.fixture
def sample_name_person() -> NamePerson:
    """Provide a populated NamePerson instance."""
    return NamePerson.create(
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
        comment="Sixth President of the United States.",
    )


@pytest.fixture
def sample_historic_variant(golden_time_period: TimePeriod) -> HistoricVariant:
    """Provide a standard HistoricVariant instance."""
    return HistoricVariant.create(
        raw="Derryfield",
        name="Manchester",
        historic_name_type=HistoricNameType.HISTORICAL,
        valid_period=golden_time_period,
        comment="Chartered in 1751, renamed Manchester in 1810.",
    )


@pytest.fixture
def sample_name_thing(sample_historic_variant: HistoricVariant) -> NameThing:
    """Provide a populated NameThing instance with embedded historic variant."""
    return NameThing.create(
        raw="City of Manchester",
        canonical="Manchester",
        aliases=["Queen City"],
        alt_spellings=["Manchestir"],
        historic=[sample_historic_variant],
        comment="Largest city in New Hampshire.",
    )


# ==============================================================================
# SECTION 5: FAILURE PAYLOADS & DEFENSIVE BOUNDARIES
# ==============================================================================


@pytest.fixture
def failure_audit_inverted() -> dict[str, str]:
    """Provide an invalid audit timestamp dictionary where updated_at precedes created_at."""
    return {
        "created_at": "2026-10-30T14:00:00Z",
        "updated_at": "2026-10-30T10:00:00Z",
    }


@pytest.fixture
def failure_note_payload_missing_keys() -> dict[str, Any]:
    """Provide an incomplete dictionary missing mandatory note_type and audit keys."""
    return {
        "note_id": "NOT-000001",
        "text": "Incomplete note payload.",
    }


@pytest.fixture
def failure_note_blank_text() -> str:
    """Provide a whitespace-only string that must fail note text validation."""
    return "   \n\t  "
