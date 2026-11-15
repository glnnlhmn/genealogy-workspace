"""Path: tests/test_gda/test_model/conftest.py

Shared root pytest fixtures and canonical atom/base baselines for gda.model test suites.

Operational Role:
    Provides centralized, immutable, in-memory canonical AtomID, UUIDv4,
    HistoricalYear, IsoTimestamp, AuditStamp, Coordinates, TimePeriod, and
    negative validation fixtures inherited automatically across all
    tests/test_gda/test_model/* subpackages.
"""

from __future__ import annotations

from typing import Any

import pytest

from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import (
    DraftRecordID,
    FactID,
    FamilyID,
    IndividualID,
    LocationID,
    MediaID,
    NoteID,
    OrganizationID,
    RepositoryID,
    SiteID,
    SourceID,
)
from gda.model.atom.year import BirthYear, DeathYear, HistoricalYear
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate, TimePeriod
from gda.model.base.geo import Coordinates

__version__ = "1.0.0+build.11"

SAMPLE_SOURCE_UUID_1 = "11111111-1111-4111-8111-111111111111"
SAMPLE_SOURCE_UUID_2 = "22222222-2222-4222-8222-222222222222"
SAMPLE_MEDIA_UUID_1 = "aaaa1111-1111-4111-8111-111111111111"
SAMPLE_MEDIA_UUID_2 = "bbbb2222-2222-4222-8222-222222222222"


@pytest.fixture(scope="session")
def golden_timestamp() -> IsoTimestamp:
    """Return canonical baseline UTC timestamp fixture."""
    return IsoTimestamp("2026-10-16T12:00:00Z")


@pytest.fixture(scope="session")
def advanced_timestamp() -> IsoTimestamp:
    """Return canonical updated UTC timestamp fixture."""
    return IsoTimestamp("2026-10-16T14:30:00Z")


@pytest.fixture(scope="session")
def golden_audit(golden_timestamp: IsoTimestamp) -> AuditStamp:
    """Return canonical baseline AuditStamp fixture."""
    return AuditStamp(created_at=golden_timestamp, updated_at=golden_timestamp)


@pytest.fixture(scope="session")
def golden_time_period() -> TimePeriod:
    """Return canonical 1850-1900 TimePeriod fixture."""
    return TimePeriod(
        start_date=EventDate.create("1850-01-01"),
        end_date=EventDate.create("1900-12-31"),
    )


@pytest.fixture(scope="session")
def sample_coordinates() -> Coordinates:
    """Return canonical Concord, NH Coordinates fixture."""
    return Coordinates.create(43.2081, -71.5376)


@pytest.fixture(scope="session")
def golden_guid() -> str:
    """Return canonical lowercase UUIDv4 string."""
    return "a1b2c3d4-e5f6-4a1b-8c2d-3e4f5a6b7c8d"


@pytest.fixture(scope="session")
def golden_source_id() -> SourceID:
    """Return canonical golden SourceID."""
    return SourceID("a1b2c3d4-e5f6-4a1b-8c2d-3e4f5a6b7c8d")


@pytest.fixture(scope="session")
def golden_source_uuid() -> str:
    """Return primary golden UUIDv4 string for SourceID."""
    return "a1b2c3d4-e5f6-4a1b-8c2d-3e4f5a6b7c8d"


@pytest.fixture(scope="session")
def golden_source_uuid_2() -> str:
    """Return secondary golden UUIDv4 string for SourceID."""
    return "b2c3d4e5-f6a1-4b2c-9d3e-4f5a6b7c8d9e"


@pytest.fixture(scope="session")
def failure_note_payload_missing_keys() -> dict[str, Any]:
    """Return incomplete Note dictionary payload missing required keys."""
    return {"note_id": "NOT-000018"}


@pytest.fixture(scope="session")
def failure_note_blank_text() -> str:
    """Return whitespace-only string for negative validation checks."""
    return "   "


@pytest.fixture
def sample_fact_id() -> FactID:
    """Return canonical FactID('FID-000104')."""
    return FactID("FID-000104")


@pytest.fixture
def sample_individual_id() -> IndividualID:
    """Return canonical IndividualID('IND-000010')."""
    return IndividualID("IND-000010")


@pytest.fixture
def sample_family_id() -> FamilyID:
    """Return canonical FamilyID('FAM-000001')."""
    return FamilyID("FAM-000001")


@pytest.fixture
def sample_location_id() -> LocationID:
    """Return canonical LocationID('LOC-000001')."""
    return LocationID("LOC-000001")


@pytest.fixture
def sample_site_id() -> SiteID:
    """Return canonical SiteID('SID-000005')."""
    return SiteID("SID-000005")


@pytest.fixture
def sample_organization_id() -> OrganizationID:
    """Return canonical OrganizationID('ORG-000001')."""
    return OrganizationID("ORG-000001")


@pytest.fixture
def sample_repository_id() -> RepositoryID:
    """Return canonical RepositoryID('REP-000001')."""
    return RepositoryID("REP-000001")


@pytest.fixture
def sample_draft_record_id() -> DraftRecordID:
    """Return canonical DraftRecordID('DRF-000001')."""
    return DraftRecordID("DRF-000001")


@pytest.fixture
def sample_note_id() -> NoteID:
    """Return canonical NoteID('NOT-000001')."""
    return NoteID("NOT-000001")


@pytest.fixture
def sample_source_id() -> SourceID:
    """Return canonical SourceID UUIDv4."""
    return SourceID(SAMPLE_SOURCE_UUID_1)


@pytest.fixture
def sample_media_id() -> MediaID:
    """Return canonical MediaID UUIDv4."""
    return MediaID(SAMPLE_MEDIA_UUID_1)


@pytest.fixture
def sample_year() -> HistoricalYear:
    """Return canonical HistoricalYear(1878)."""
    return HistoricalYear(1878)


@pytest.fixture
def sample_birth_year() -> BirthYear:
    """Return canonical BirthYear(1844)."""
    return BirthYear(1844)


@pytest.fixture
def sample_death_year() -> DeathYear:
    """Return canonical DeathYear(1912)."""
    return DeathYear(1912)
