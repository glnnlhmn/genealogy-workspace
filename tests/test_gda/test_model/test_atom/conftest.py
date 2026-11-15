"""Path: tests/test_gda/test_model/test_atom/conftest.py

Shared pytest fixtures and test vectors for the gda.model.atom test suite.

Operational Role:
    Provides canonical valid atom fixtures, cross-type comparison pairs, and
    standardized invalid input vectors (booleans, non-primitives, padded whitespace)
    for in-memory unit, integrity, and regression testing across all atom modules.
"""

from __future__ import annotations

from typing import Any

import pytest

from gda.model.atom import (
    AhnentafelNumber,
    ArchivalURN,
    AtomID,
    BirthYear,
    CemeteryPlotUrn,
    CensusUrn,
    ConfidenceScore,
    DateString,
    DeathYear,
    DraftRecordID,
    FactID,
    FamilyID,
    GenderAtom,
    HistoricalYear,
    IndividualID,
    IsoTimestamp,
    Latitude,
    LocationID,
    Longitude,
    MediaID,
    MilitaryDraftUrn,
    NewsCategoryCode,
    NoteID,
    OrganizationID,
    PubCode,
    QuayScore,
    RepositoryID,
    ServiceRecordID,
    SiteID,
    SourceID,
    SourceURN,
    TranscriptID,
    UUIDv4Str,
    VitalCertificateUrn,
)

__version__ = "1.0.0+build.3"

# ==============================================================================
# SHARED INVALID INPUT VECTORS (Importable for @pytest.mark.parametrize)
# ==============================================================================

INVALID_BOOL_VALUES: tuple[bool, bool] = (True, False)
INVALID_NON_STRING_VALUES: tuple[Any, ...] = (None, 123, 45.6, True, False, ["item"], {"k": "v"})
INVALID_NON_NUMERIC_VALUES: tuple[Any, ...] = (None, "123", "45.6", True, False, [], {})
PADDED_WHITESPACE_SAMPLES: tuple[str, ...] = (" M", "M ", " M ", "\tM\n")


# ==============================================================================
# CANONICAL SINGLE-ATOM FIXTURES
# ==============================================================================


@pytest.fixture
def sample_individual_id() -> IndividualID:
    """Return canonical IndividualID fixture."""
    return IndividualID("IND-000001")


@pytest.fixture
def sample_fact_id() -> FactID:
    """Return canonical FactID fixture."""
    return FactID("FID-000001")


@pytest.fixture
def sample_uuid() -> UUIDv4Str:
    """Return canonical RFC 4122 lowercase UUIDv4Str fixture."""
    return UUIDv4Str("c9a646d3-9c61-4a70-8b14-c48c8b417c8d")


@pytest.fixture
def sample_source_id() -> SourceID:
    """Return canonical SourceID fixture."""
    return SourceID("c9a646d3-9c61-4a70-8b14-c48c8b417c8d")


@pytest.fixture
def sample_gender() -> GenderAtom:
    """Return canonical GenderAtom fixture."""
    return GenderAtom("M")


@pytest.fixture
def sample_birth_year() -> BirthYear:
    """Return canonical BirthYear fixture."""
    return BirthYear(1880)


@pytest.fixture
def sample_death_year() -> DeathYear:
    """Return canonical DeathYear fixture."""
    return DeathYear(1950)


@pytest.fixture
def sample_latitude() -> Latitude:
    """Return canonical Concord, NH Latitude fixture."""
    return Latitude(43.208136)


@pytest.fixture
def sample_longitude() -> Longitude:
    """Return canonical Concord, NH Longitude fixture."""
    return Longitude(-71.537572)


@pytest.fixture
def sample_date_string() -> DateString:
    """Return canonical genealogical DateString fixture."""
    return DateString("14 APR 1865")


@pytest.fixture
def sample_iso_timestamp() -> IsoTimestamp:
    """Return canonical UTC IsoTimestamp fixture."""
    return IsoTimestamp("2026-10-16T12:00:00Z")


@pytest.fixture
def sample_source_urn() -> SourceURN:
    """Return canonical SourceURN fixture."""
    return SourceURN("URN:SRC:1917:NH_MERRIMACK:DOC_000101")


# ==============================================================================
# COMPOSITE COLLECTION FIXTURES
# ==============================================================================


@pytest.fixture
def all_valid_atoms() -> list[Any]:
    """Return one valid instantiated object for every concrete atom class in gda.model.atom."""
    valid_uuid = "c9a646d3-9c61-4a70-8b14-c48c8b417c8d"
    return [
        AtomID("ABC-000001"),
        IndividualID("IND-000001"),
        FactID("FID-000001"),
        LocationID("LOC-000001"),
        SiteID("SID-000001"),
        FamilyID("FAM-000001"),
        NoteID("NOT-000001"),
        OrganizationID("ORG-000001"),
        RepositoryID("REP-000001"),
        DraftRecordID("DRF-000001"),
        UUIDv4Str(valid_uuid),
        SourceID(valid_uuid),
        MediaID(valid_uuid),
        ServiceRecordID(valid_uuid),
        TranscriptID(valid_uuid),
        GenderAtom("M"),
        HistoricalYear(1920),
        BirthYear(1865),
        DeathYear(1942),
        DateString("1920-01-01"),
        IsoTimestamp("2026-10-16T12:00:00Z"),
        Latitude(43.208136),
        Longitude(-71.537572),
        QuayScore(3),
        AhnentafelNumber(1),
        ConfidenceScore(0.95),
        PubCode("PUB_01"),
        NewsCategoryCode("OBIT"),
        ArchivalURN("URN:GENERIC:SEG1:SEG2"),
        SourceURN("URN:SRC:1917:NH_MERRIMACK:DOC_000101"),
        MilitaryDraftUrn("URN:DRAFT:1917:NH_MERRIMACK:CARD_001"),
        CensusUrn("URN:CENSUS:1920:NH_MERRIMACK:ED12_S04B_L02"),
        VitalCertificateUrn("URN:VITAL:BIRTH:1905:NH_CONCORD:CERT_00451"),
        CemeteryPlotUrn("URN:CEM:NH_BLOSSOM_HILL:SEC_A_LOT_12_G1"),
    ]


@pytest.fixture
def incompatible_atom_pairs() -> list[tuple[Any, Any]]:
    """Return pairs of distinct atom types that must raise TypeError on < ordering."""
    valid_uuid = "c9a646d3-9c61-4a70-8b14-c48c8b417c8d"
    return [
        (IndividualID("IND-000001"), FactID("FID-000001")),
        (IndividualID("IND-000001"), AtomID("IND-000002")),
        (SourceID(valid_uuid), MediaID(valid_uuid)),
        (Latitude(43.0), Longitude(-71.0)),
        (
            SourceURN("URN:SRC:1917:NH_MERRIMACK:DOC_1"),
            CensusUrn("URN:CENSUS:1920:NH_MERRIMACK:ED1"),
        ),
        (QuayScore(1), AhnentafelNumber(1)),
        (PubCode("PUB_A"), NewsCategoryCode("OBIT")),
        (DateString("2026-01-01"), IsoTimestamp("2026-01-01T00:00:00Z")),
    ]
