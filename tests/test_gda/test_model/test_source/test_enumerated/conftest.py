"""Path: tests/test_gda/test_model/test_source/test_enumerated/conftest.py

Shared pytest fixtures for the gda.model.source.enumerated test suite.

Operational Role:
    Centralizes shared domain fixtures across all gda.model.source.enumerated
    unit and contract tests.
"""

from __future__ import annotations

import pytest

from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import RepositoryID, SourceID
from gda.model.atom.urn import CensusUrn, SourceURN
from gda.model.base.audit import AuditStamp

__version__ = "1.0.0+build.1"


@pytest.fixture
def valid_audit() -> AuditStamp:
    """Return synthetic in-memory AuditStamp."""
    ts = IsoTimestamp("2026-01-01T00:00:00Z")
    return AuditStamp(created_at=ts, updated_at=ts)


@pytest.fixture
def valid_repo_id() -> RepositoryID:
    """Return synthetic RepositoryID."""
    return RepositoryID("REP-000001")


@pytest.fixture
def valid_source_id() -> SourceID:
    """Return synthetic SourceID."""
    return SourceID("c9a646d3-9c61-4a70-8b14-c48c8b417c8d")


@pytest.fixture
def valid_sheet_urn() -> CensusUrn:
    """Return synthetic sheet-level CensusUrn."""
    return CensusUrn("URN:CENSUS:1880:NH_MERRIMACK:ED178_S12A")


@pytest.fixture
def valid_dir_urn() -> SourceURN:
    """Return synthetic directory SourceURN."""
    return SourceURN("URN:SRC:1925:NH_CONCORD:CITY_DIR_P214")


@pytest.fixture
def valid_tax_urn() -> SourceURN:
    """Return synthetic tax SourceURN."""
    return SourceURN("URN:SRC:1807:PA_CUMBERLAND:TAX_HOPEWELL_P14")


@pytest.fixture
def valid_census_urn() -> CensusUrn:
    """Return synthetic CensusUrn."""
    return CensusUrn("URN:CENSUS:1880:NH_MERRIMACK:ED178_S12A")
