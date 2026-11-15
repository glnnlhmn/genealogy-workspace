"""Path: tests/test_gda/test_model/test_source/test_military/conftest.py

Shared pytest fixtures for the gda.model.source.military test suite.

Operational Role:
    Centralizes shared domain fixtures across all gda.model.source.military
    unit and contract tests.
"""

from __future__ import annotations

import pytest

from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import (
    DraftRecordID,
    RepositoryID,
    ServiceRecordID,
    SourceID,
)
from gda.model.atom.urn import MilitaryDraftUrn, SourceURN
from gda.model.base.audit import AuditStamp

__version__ = "1.0.0+build.1"


@pytest.fixture
def valid_audit() -> AuditStamp:
    """Return synthetic in-memory AuditStamp."""
    timestamp = IsoTimestamp("2026-01-01T00:00:00Z")
    return AuditStamp(created_at=timestamp, updated_at=timestamp)


@pytest.fixture
def valid_award_urn() -> SourceURN:
    """Return synthetic SourceURN."""
    return SourceURN("URN:SRC:1945:WAR_DEPT:GO_112_AWD")


@pytest.fixture
def valid_repo_id() -> RepositoryID:
    """Return synthetic RepositoryID."""
    return RepositoryID("REP-000001")


@pytest.fixture
def valid_source_id() -> SourceID:
    """Return synthetic SourceID."""
    return SourceID("c9a646d3-9c61-4a70-8b14-c48c8b417c8d")


@pytest.fixture
def valid_casualty_urn() -> SourceURN:
    """Return synthetic SourceURN."""
    return SourceURN("URN:SRC:1945:VA:NAT_CEM_BURIAL_102")


@pytest.fixture
def valid_draft_urn() -> MilitaryDraftUrn:
    """Return synthetic MilitaryDraftUrn for Civil War enrollment."""
    return MilitaryDraftUrn("URN:DRAFT:1863:NH_DIST2:ROLL_001")


@pytest.fixture
def valid_draft_record_id() -> DraftRecordID:
    """Return synthetic DraftRecordID conforming to AtomID prefix DRF."""
    return DraftRecordID("DRF-000001")


@pytest.fixture
def valid_bounty_urn() -> SourceURN:
    """Return synthetic SourceURN."""
    return SourceURN("URN:SRC:1855:GLO:BLW_10492")


@pytest.fixture
def valid_pension_urn() -> SourceURN:
    """Return synthetic SourceURN."""
    return SourceURN("URN:SRC:1890:US_PENSION:CW_VET_9012")


@pytest.fixture
def valid_service_urn() -> SourceURN:
    """Return synthetic SourceURN."""
    return SourceURN("URN:SRC:1862:NH_MUSTER:VOL1_P102")


@pytest.fixture
def valid_service_record_id() -> ServiceRecordID:
    """Return synthetic ServiceRecordID."""
    return ServiceRecordID("a1a646d3-9c61-4a70-8b14-c48c8b417c8a")
