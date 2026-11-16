"""Path: tests/test_gda/test_repository/conftest.py

Shared pytest fixtures for the gda.repository verification suite.

Operational Role:
    Centralizes the initialized SQLite DatabaseSessionManager (seeded_session)
    and reuses canonical atom/URN/audit fixtures from tests/test_gda/test_model/
    so all repository and collection test modules share consistent baselines.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from gda.db.schema import SchemaManager
from gda.db.session import DatabaseSessionManager
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import (
    DraftRecordID,
    IndividualID,
    LocationID,
    OrganizationID,
    RepositoryID,
    ServiceRecordID,
    SiteID,
    SourceID,
)
from gda.model.atom.urn import (
    CemeteryPlotUrn,
    CensusUrn,
    MilitaryDraftUrn,
    SourceURN,
    VitalCertificateUrn,
)
from gda.model.base.audit import AuditStamp

__version__ = "1.0.0+build.2"


@pytest.fixture
def golden_audit() -> AuditStamp:
    """Return a deterministic AuditStamp fixture for repository tests."""
    ts = IsoTimestamp("2026-01-01T00:00:00Z")
    return AuditStamp(created_at=ts, updated_at=ts)


@pytest.fixture
def valid_repo_id() -> RepositoryID:
    """Return canonical RepositoryID('REP-000001')."""
    return RepositoryID("REP-000001")


@pytest.fixture
def valid_source_id() -> SourceID:
    """Return canonical SourceID UUIDv4."""
    return SourceID("c9a646d3-9c61-4a70-8b14-c48c8b417c8d")


@pytest.fixture
def sample_individual_id() -> IndividualID:
    """Return canonical IndividualID('IND-000001')."""
    return IndividualID("IND-000001")


@pytest.fixture
def sample_location_id() -> LocationID:
    """Return canonical LocationID('LOC-000001')."""
    return LocationID("LOC-000001")


@pytest.fixture
def sample_site_id() -> SiteID:
    """Return canonical SiteID('SID-000001')."""
    return SiteID("SID-000001")


@pytest.fixture
def sample_organization_id() -> OrganizationID:
    """Return canonical OrganizationID('ORG-000001')."""
    return OrganizationID("ORG-000001")


@pytest.fixture
def valid_draft_record_id() -> DraftRecordID:
    """Return canonical DraftRecordID('DRF-000001')."""
    return DraftRecordID("DRF-000001")


@pytest.fixture
def valid_service_record_id() -> ServiceRecordID:
    """Return canonical ServiceRecordID."""
    return ServiceRecordID("a1a646d3-9c61-4a70-8b14-c48c8b417c8a")


@pytest.fixture
def canonical_source_urn() -> SourceURN:
    """Return canonical SourceURN fixture for documentary records."""
    return SourceURN("URN:SRC:1900:NH_MERRIMACK:DOC_000101")


@pytest.fixture
def canonical_vital_birth_urn() -> VitalCertificateUrn:
    """Return canonical VitalCertificateUrn fixture."""
    return VitalCertificateUrn("URN:VITAL:BIRTH:1880:NH_CONCORD:CERT_00101")


@pytest.fixture
def canonical_cemetery_plot_urn() -> CemeteryPlotUrn:
    """Return canonical CemeteryPlotUrn fixture."""
    return CemeteryPlotUrn("URN:CEM:NH_BLOSSOM_HILL:SEC_A_LOT_12_G1")


@pytest.fixture
def canonical_census_urn() -> CensusUrn:
    """Return canonical CensusUrn fixture."""
    return CensusUrn("URN:CENSUS:1920:NH_MERRIMACK:ED12_S04B_L02")


@pytest.fixture
def canonical_military_draft_urn() -> MilitaryDraftUrn:
    """Return canonical MilitaryDraftUrn fixture."""
    return MilitaryDraftUrn("URN:DRAFT:1917:NH_MERRIMACK:CARD_001")


@pytest.fixture
def seeded_session(tmp_path: Path) -> DatabaseSessionManager:
    """Provision an initialized SQLite DB with core FK reference rows."""
    db_file = tmp_path / "repository_test.db"
    session = DatabaseSessionManager(db_path=db_file)
    SchemaManager(session_manager=session).init_db()

    with session.transaction() as tx:
        tx.execute(
            """
            INSERT INTO locations (
                id, canonical_urn, raw_name, canonical_name, category, created_at, updated_at
            ) VALUES
            ('LOC-000001', 'urn:gda:loc:us:pa:cumberland', 'Cumberland County', 'Cumberland County', 'COUNTY_EQUIVALENT', '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z'),
            ('LOC-000002', 'urn:gda:loc:us:pa:lancaster', 'Lancaster County', 'Lancaster County', 'COUNTY_EQUIVALENT', '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z');
            """
        )
        tx.execute(
            """
            INSERT INTO sites (
                id, canonical_urn, raw_name, canonical_name, category,
                location_id, created_at, updated_at
            ) VALUES (
                'SID-000001', 'urn:gda:site:us:pa:cumberland:zion_s000001',
                'Zion Lutheran Cemetery', 'Zion Lutheran Cemetery', 'CEMETERY',
                'LOC-000001', '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z'
            );
            """
        )
        tx.execute(
            """
            INSERT INTO organizations (
                id, canonical_urn, raw_name, canonical_name, category,
                location_id, meeting_site_id, created_at, updated_at
            ) VALUES (
                'ORG-000001', 'urn:gda:org:pa:zion_lutheran',
                'Zion Lutheran Church', 'Zion Lutheran Church', 'RELIGIOUS',
                'LOC-000001', 'SID-000001',
                '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z'
            );
            """
        )
        for idx, (given, sur, sex) in enumerate(
            [("John", "Lehman", "MALE"), ("Mary", "Miller", "FEMALE")],
            start=1,
        ):
            tx.execute(
                """
                INSERT INTO individuals (
                    id, canonical_urn, raw_name, canonical_name,
                    given_name, surname, gender, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z');
                """,
                (
                    f"IND-{idx:06d}",
                    f"urn:gda:ind:{idx:06d}",
                    f"{given} {sur}",
                    f"{given} {sur}",
                    given,
                    sur,
                    sex,
                ),
            )
    return session
