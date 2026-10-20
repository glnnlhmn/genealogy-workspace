"""Path: tests/test_gda/test_model/test_atom/test_urn.py

Atomized behavioral test suite for ArchivalURN hierarchy and domain URN value objects.

Operational Role:
    Verifies canonical URN syntax validation, regex patterns, case normalization,
    structural property decomposition, immutability, and exception handling across
    all specialized archival URN classes.

Test Structure & Protocol:
    - Atomized tests: 1:1 behavioral contract verification.
    - Fully decorated: Pytest marker taxonomy (@pytest.mark.unit, @pytest.mark.smoke, @pytest.mark.regression).
    - Synthetic baselines: Pure in-memory fixtures with zero disk I/O.
"""

from __future__ import annotations

from typing import ClassVar

import pytest

from gda.core.errors import ModelFormatError
from gda.model.atom.urn import (
    ArchivalURN,
    CemeteryPlotUrn,
    CensusUrn,
    MilitaryDraftUrn,
    SourceURN,
    VitalCertificateUrn,
)

__version__ = "1.0.0+build.2"


# ==============================================================================
# GROUP 1: BASE ARCHIVAL URN PROTOCOL & PROPERTIES
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_archival_urn_smoke_valid_initialization() -> None:
    """Verify minimal valid instantiation and representation of ArchivalURN."""
    urn = ArchivalURN("URN:GENERIC:SEGMENT_1:SEGMENT_2")
    assert str(urn) == "URN:GENERIC:SEGMENT_1:SEGMENT_2"
    assert repr(urn) == "ArchivalURN('URN:GENERIC:SEGMENT_1:SEGMENT_2')"
    assert urn.parts == ["URN", "GENERIC", "SEGMENT_1", "SEGMENT_2"]
    assert urn.nid == "GENERIC"


@pytest.mark.unit
def test_archival_urn_scheme_mismatch_fails() -> None:
    """Verify ModelFormatError raised when scheme does not match EXPECTED_SCHEME."""

    class MockCustomSchemeURN(ArchivalURN):
        EXPECTED_SCHEME: ClassVar[str] = "XURN"

    with pytest.raises(ModelFormatError, match="Invalid URN scheme 'URN'"):
        MockCustomSchemeURN("URN:GENERIC:SEGMENT_1")


@pytest.mark.unit
def test_archival_urn_nid_mismatch_fails() -> None:
    """Verify ModelFormatError raised when NID does not match EXPECTED_NID."""

    class MockCustomNidURN(ArchivalURN):
        EXPECTED_NID: ClassVar[str | None] = "EXPECTED_NID"

    with pytest.raises(ModelFormatError, match="Invalid URN namespace 'ACTUAL_NID'"):
        MockCustomNidURN("URN:ACTUAL_NID:SEGMENT_1")


@pytest.mark.unit
def test_archival_urn_empty_or_whitespace_fails() -> None:
    """Verify ModelFormatError raised for empty or whitespace-only URN strings."""
    with pytest.raises(ModelFormatError, match="Invalid ArchivalURN syntax"):
        ArchivalURN("")

    with pytest.raises(ModelFormatError, match="Invalid ArchivalURN syntax"):
        ArchivalURN("   ")


@pytest.mark.unit
def test_archival_urn_regex_malformed_fails() -> None:
    """Verify ModelFormatError raised when URN pattern fails regex contract."""
    with pytest.raises(ModelFormatError, match="Invalid ArchivalURN syntax"):
        ArchivalURN("NOT_A_URN")

    with pytest.raises(ModelFormatError, match="Invalid ArchivalURN syntax"):
        ArchivalURN("URN:")

    with pytest.raises(ModelFormatError, match="Invalid ArchivalURN syntax"):
        ArchivalURN("urn:lowercase:not:allowed")


# ==============================================================================
# GROUP 2: SOURCE URN GOLDEN PATH & PROPERTIES
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_source_urn_golden_path_and_properties() -> None:
    """Verify valid instantiation, string format, and property accessors of SourceURN."""
    urn = SourceURN("URN:SRC:1917:NH_MERRIMACK:DOC_000101")
    assert str(urn) == "URN:SRC:1917:NH_MERRIMACK:DOC_000101"
    assert urn.year == 1917
    assert urn.jurisdiction == "NH_MERRIMACK"
    assert urn.locator == "DOC_000101"
    assert urn.nid == "SRC"


@pytest.mark.unit
def test_source_urn_equality_and_hashing() -> None:
    """Verify SourceURN implements value equality and set hashability."""
    urn1 = SourceURN("URN:SRC:1863:CIVIL_WAR:DRAFT_001")
    urn2 = SourceURN("URN:SRC:1863:CIVIL_WAR:DRAFT_001")
    urn3 = SourceURN("URN:SRC:1863:CIVIL_WAR:DRAFT_002")

    assert urn1 == urn2
    assert urn1 != urn3
    assert hash(urn1) == hash(urn2)
    assert len({urn1, urn2, urn3}) == 2


@pytest.mark.unit
def test_source_urn_whitespace_stripping() -> None:
    """Verify SourceURN trims surrounding whitespace upon instantiation."""
    urn = SourceURN("   URN:SRC:1850:FEDERAL_CENSUS:P312   ")
    assert urn.value == "URN:SRC:1850:FEDERAL_CENSUS:P312"


@pytest.mark.unit
@pytest.mark.regression
def test_source_urn_syntax_violations_fail() -> None:
    """Verify ModelFormatError raised when SourceURN violates regex pattern."""
    with pytest.raises(ModelFormatError, match="Invalid SourceURN syntax"):
        SourceURN("URN:SRC:191:TOO_SHORT_YEAR:LOC")

    with pytest.raises(ModelFormatError, match="Invalid SourceURN syntax"):
        SourceURN("URN:SRC:1917:lowercase_jurisdiction:LOC")


# ==============================================================================
# GROUP 3: MILITARY DRAFT URN
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_military_draft_urn_golden_path_and_properties() -> None:
    """Verify valid instantiation and property accessors of MilitaryDraftUrn."""
    urn = MilitaryDraftUrn("URN:DRAFT:1917:NH_MERRIMACK:CARD_001")
    assert str(urn) == "URN:DRAFT:1917:NH_MERRIMACK:CARD_001"
    assert urn.draft_year == 1917
    assert urn.jurisdiction == "NH_MERRIMACK"
    assert urn.card_locator == "CARD_001"
    assert urn.nid == "DRAFT"


@pytest.mark.unit
def test_military_draft_urn_subclasses_archival_urn() -> None:
    """Verify MilitaryDraftUrn is an instance of ArchivalURN and supports dict hashing."""
    urn1 = MilitaryDraftUrn("URN:DRAFT:1942:WWII_FOURTH_WAVE:A_9921")
    urn2 = MilitaryDraftUrn("URN:DRAFT:1942:WWII_FOURTH_WAVE:A_9921")
    assert isinstance(urn1, ArchivalURN)
    assert {urn1: "card"}[urn2] == "card"


@pytest.mark.unit
@pytest.mark.regression
def test_military_draft_urn_syntax_mismatch_fails() -> None:
    """Verify ModelFormatError raised when MilitaryDraftUrn syntax is invalid."""
    with pytest.raises(ModelFormatError, match="Invalid MilitaryDraftUrn syntax"):
        MilitaryDraftUrn("URN:SRC:1917:SELECTIVE_SERVICE:0001")

    with pytest.raises(ModelFormatError, match="Invalid MilitaryDraftUrn syntax"):
        MilitaryDraftUrn("urn:draft:1917:nh_merrimack:card_001")


# ==============================================================================
# GROUP 4: CENSUS URN
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_census_urn_golden_path_and_properties() -> None:
    """Verify valid instantiation and property accessors of CensusUrn."""
    urn = CensusUrn("URN:CENSUS:1920:NH_MERRIMACK:ED12_S04B_L02")
    assert str(urn) == "URN:CENSUS:1920:NH_MERRIMACK:ED12_S04B_L02"
    assert urn.census_year == 1920
    assert urn.jurisdiction == "NH_MERRIMACK"
    assert urn.enumeration_locator == "ED12_S04B_L02"
    assert urn.nid == "CENSUS"


@pytest.mark.unit
@pytest.mark.regression
def test_census_urn_syntax_mismatch_fails() -> None:
    """Verify ModelFormatError raised when CensusUrn syntax is invalid."""
    with pytest.raises(ModelFormatError, match="Invalid CensusUrn syntax"):
        CensusUrn("URN:CENSUS:YEAR_NOT_NUM:JURIS:LOC")

    with pytest.raises(ModelFormatError, match="Invalid CensusUrn syntax"):
        CensusUrn("URN:POPULATION:1920:NH_MERRIMACK:ED12")


# ==============================================================================
# GROUP 5: VITAL CERTIFICATE URN
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_vital_certificate_urn_golden_path_and_properties() -> None:
    """Verify valid instantiation and property accessors across vital event types."""
    # BIRTH
    urn_birth = VitalCertificateUrn("URN:VITAL:BIRTH:1905:NH_CONCORD:CERT_00451")
    assert urn_birth.event_type == "BIRTH"
    assert urn_birth.certificate_year == 1905
    assert urn_birth.jurisdiction == "NH_CONCORD"
    assert urn_birth.certificate_number == "CERT_00451"
    assert urn_birth.nid == "VITAL"

    # MARRIAGE
    urn_marr = VitalCertificateUrn("URN:VITAL:MARRIAGE:1925:NH_BOW:M_1102")
    assert urn_marr.event_type == "MARRIAGE"
    assert urn_marr.certificate_year == 1925

    # DEATH
    urn_death = VitalCertificateUrn("URN:VITAL:DEATH:1960:NH_CONCORD:D_9981")
    assert urn_death.event_type == "DEATH"
    assert urn_death.certificate_year == 1960


@pytest.mark.unit
@pytest.mark.regression
def test_vital_certificate_urn_invalid_event_type_fails() -> None:
    """Verify ModelFormatError raised when event_type is not BIRTH, MARRIAGE, or DEATH."""
    with pytest.raises(ModelFormatError, match="Invalid VitalCertificateUrn syntax"):
        VitalCertificateUrn("URN:VITAL:DIVORCE:1930:NH_CONCORD:CERT_01")

    with pytest.raises(ModelFormatError, match="Invalid VitalCertificateUrn syntax"):
        VitalCertificateUrn("URN:VITAL:BAPTISM:1880:NH_CONCORD:CERT_02")


# ==============================================================================
# GROUP 6: CEMETERY PLOT URN
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_cemetery_plot_urn_golden_path_and_properties() -> None:
    """Verify valid instantiation and property accessors of CemeteryPlotUrn."""
    urn = CemeteryPlotUrn("URN:CEM:NH_BLOSSOM_HILL:SEC_A_LOT_12_G1")
    assert str(urn) == "URN:CEM:NH_BLOSSOM_HILL:SEC_A_LOT_12_G1"
    assert urn.facility_code == "NH_BLOSSOM_HILL"
    assert urn.plot_locator == "SEC_A_LOT_12_G1"
    assert urn.nid == "CEM"


@pytest.mark.unit
@pytest.mark.regression
def test_cemetery_plot_urn_syntax_violations_fail() -> None:
    """Verify ModelFormatError raised when CemeteryPlotUrn syntax is invalid."""
    with pytest.raises(ModelFormatError, match="Invalid CemeteryPlotUrn syntax"):
        CemeteryPlotUrn("URN:CEM:lowercase_facility:plot_01")

    with pytest.raises(ModelFormatError, match="Invalid CemeteryPlotUrn syntax"):
        CemeteryPlotUrn("URN:BURIAL:NH_BLOSSOM_HILL:SEC_A")
