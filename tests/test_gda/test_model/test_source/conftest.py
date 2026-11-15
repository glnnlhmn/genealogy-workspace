"""Path: tests/test_gda/test_model/test_source/conftest.py

Shared pytest fixtures for the gda.model.source documentary record test suites.

Operational Role:
    Provides shared canonical SourceURN, VitalCertificateUrn, CemeteryPlotUrn,
    CensusUrn, and MilitaryDraftUrn fixtures for all 12 domain record test
    suites under tests/test_gda/test_model/test_source/. Inherited AtomID,
    UUIDv4Str, HistoricalYear, AuditStamp, and TimePeriod fixtures are provided
    by tests/test_gda/test_model/conftest.py.
"""

from __future__ import annotations

import pytest

from gda.model.atom.urn import (
    CemeteryPlotUrn,
    CensusUrn,
    MilitaryDraftUrn,
    SourceURN,
    VitalCertificateUrn,
)

__version__ = "1.0.0+build.1"


@pytest.fixture(scope="session")
def canonical_source_urn() -> SourceURN:
    """Return canonical SourceURN fixture for general documentary records."""
    return SourceURN("URN:SRC:1900:NH_MERRIMACK:DOC_000101")


@pytest.fixture(scope="session")
def canonical_vital_birth_urn() -> VitalCertificateUrn:
    """Return canonical VitalCertificateUrn fixture for birth records."""
    return VitalCertificateUrn("URN:VITAL:BIRTH:1880:NH_CONCORD:CERT_00101")


@pytest.fixture(scope="session")
def canonical_cemetery_plot_urn() -> CemeteryPlotUrn:
    """Return canonical CemeteryPlotUrn fixture for cemetery records."""
    return CemeteryPlotUrn("URN:CEM:NH_BLOSSOM_HILL:SEC_A_LOT_12_G1")


@pytest.fixture(scope="session")
def canonical_census_urn() -> CensusUrn:
    """Return canonical CensusUrn fixture for enumerated census schedules."""
    return CensusUrn("URN:CENSUS:1920:NH_MERRIMACK:ED12_S04B_L02")


@pytest.fixture(scope="session")
def canonical_military_draft_urn() -> MilitaryDraftUrn:
    """Return canonical MilitaryDraftUrn fixture for military draft cards."""
    return MilitaryDraftUrn("URN:DRAFT:1917:NH_MERRIMACK:CARD_001")
