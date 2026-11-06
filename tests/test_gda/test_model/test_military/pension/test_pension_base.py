"""Path: tests/test_gda/test_model/test_military/pension/test_pension_base.py

Atomized behavioral test suite for MilitaryPensionRecord domain entity.

Operational Role:
    Verifies pension record instantiation invariants, claimant roles, certificate
    numbers, and identity consistency between veteran and claimant.

Test Structure & Protocol:
    - Atomized tests: 1:1 behavioral contract verification.
    - Fully decorated: Pytest marker taxonomy (@pytest.mark.unit, @pytest.mark.smoke, @pytest.mark.regression).
    - Synthetic baselines: Pure in-memory fixtures with isolated basetemp execution.
"""

from __future__ import annotations

import pytest

from gda.core.errors import ModelFormatError
from gda.enums.sources import SourceRecordCategory
from gda.model.atom.date import HistoricalYear, IsoTimestamp
from gda.model.atom.id import (
    IndividualID,
    LocationID,
    RepositoryID,
    SourceID,
    TranscriptID,
)
from gda.model.atom.urn import SourceURN
from gda.model.base.audit import AuditStamp
from gda.model.military.pension import (
    MilitaryPensionRecord,
    PensionClaimantRole,
    PensionPaymentAuthority,
)

__version__ = "1.0.0+build.1"


# ==============================================================================
# FIXTURES
# ==============================================================================


@pytest.fixture
def valid_audit() -> AuditStamp:
    """Return synthetic in-memory AuditStamp."""
    timestamp = IsoTimestamp("2026-01-01T00:00:00Z")
    return AuditStamp(created_at=timestamp, updated_at=timestamp)


@pytest.fixture
def valid_pension_urn() -> SourceURN:
    """Return synthetic SourceURN."""
    return SourceURN("URN:SRC:1890:US_PENSION:CW_VET_9012")


@pytest.fixture
def valid_repo_id() -> RepositoryID:
    """Return synthetic RepositoryID."""
    return RepositoryID("REP-000001")


@pytest.fixture
def valid_source_id() -> SourceID:
    """Return synthetic SourceID."""
    return SourceID("c9a646d3-9c61-4a70-8b14-c48c8b417c8d")


# ==============================================================================
# GROUP 1: SMOKE & GOLDEN PATH
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_military_pension_smoke_valid_initialization(
    valid_source_id: SourceID,
    valid_pension_urn: SourceURN,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify minimal valid instantiation of MilitaryPensionRecord."""
    rec = MilitaryPensionRecord(
        source_id=valid_source_id,
        source_urn=valid_pension_urn,
        record_category=SourceRecordCategory.MILITARY,
        description="Civil War Invalid Pension Declaration for Glenn Lehman",
        repository_id=valid_repo_id,
        audit=valid_audit,
        veteran_id=IndividualID("IND-000001"),
        veteran_name_raw="Glenn D. Lehman",
        claimant_id=IndividualID("IND-000001"),
        claimant_name_raw="Glenn D. Lehman",
        claimant_role=PensionClaimantRole.VETERAN,
        payment_authority=PensionPaymentAuthority.US_BUREAU_OF_PENSIONS,
        application_year=HistoricalYear(1890),
        application_number_raw="SO-982.102",
        certificate_number_raw="SC-741.002",
    )
    assert rec.veteran_id == IndividualID("IND-000001")
    assert rec.claimant_id == IndividualID("IND-000001")
    assert rec.claimant_role == PensionClaimantRole.VETERAN
    assert rec.payment_authority == PensionPaymentAuthority.US_BUREAU_OF_PENSIONS
    assert rec.application_year == HistoricalYear(1890)
    assert rec.application_number_raw == "SO-982.102"
    assert rec.certificate_number_raw == "SC-741.002"
    assert "Glenn D. Lehman" in str(rec)
    assert "SC-741.002" in str(rec)


# ==============================================================================
# GROUP 2: OPTIONAL ATTRIBUTES & THIRD-PARTY CLAIMANTS
# ==============================================================================


@pytest.mark.unit
def test_military_pension_full_attributes_widow_claim(
    valid_source_id: SourceID,
    valid_pension_urn: SourceURN,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify MilitaryPensionRecord allows distinct claimant and optional metadata."""
    loc_id = LocationID("LOC-000012")
    trn_id = TranscriptID("e1a646d3-9c61-4a70-8b14-c48c8b417c8f")
    rec = MilitaryPensionRecord(
        source_id=valid_source_id,
        source_urn=valid_pension_urn,
        record_category=SourceRecordCategory.MILITARY,
        description="Widow pension claim file",
        repository_id=valid_repo_id,
        audit=valid_audit,
        veteran_id=IndividualID("IND-000001"),
        veteran_name_raw="Glenn Lehman",
        claimant_id=IndividualID("IND-000002"),
        claimant_name_raw="Martha Lehman",
        claimant_role=PensionClaimantRole.WIDOW,
        payment_authority=PensionPaymentAuthority.US_BUREAU_OF_PENSIONS,
        application_year=HistoricalYear(1898),
        application_number_raw="WO-412.301",
        law_or_act_raw="Act of June 27, 1890",
        service_unit_raw="Co. E, 1st NH Heavy Artillery",
        application_location_raw="Concord, Merrimack Co., NH",
        application_location_id=loc_id,
        transcript_id=trn_id,
    )
    assert rec.claimant_id == IndividualID("IND-000002")
    assert rec.claimant_name_raw == "Martha Lehman"
    assert rec.service_unit_raw == "Co. E, 1st NH Heavy Artillery"
    assert rec.application_location_id == loc_id
    assert rec.transcript_id == trn_id


# ==============================================================================
# GROUP 3: BOUNDARY & VALIDATION REJECTIONS
# ==============================================================================


@pytest.mark.unit
@pytest.mark.regression
def test_military_pension_invalid_category_fails(
    valid_source_id: SourceID,
    valid_pension_urn: SourceURN,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify ModelFormatError raised if record_category is not MILITARY."""
    with pytest.raises(ModelFormatError, match="requires category 'MILITARY'"):
        MilitaryPensionRecord(
            source_id=valid_source_id,
            source_urn=valid_pension_urn,
            record_category=SourceRecordCategory.CENSUS,
            description="Mismatched category",
            repository_id=valid_repo_id,
            audit=valid_audit,
            veteran_id=IndividualID("IND-000001"),
            veteran_name_raw="Glenn Lehman",
            claimant_id=IndividualID("IND-000001"),
            claimant_name_raw="Glenn Lehman",
            claimant_role=PensionClaimantRole.VETERAN,
            payment_authority=PensionPaymentAuthority.US_BUREAU_OF_PENSIONS,
            application_year=HistoricalYear(1890),
        )


@pytest.mark.unit
@pytest.mark.regression
def test_military_pension_veteran_role_mismatched_id_fails(
    valid_source_id: SourceID,
    valid_pension_urn: SourceURN,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify ModelFormatError raised if claimant_role is VETERAN but IDs differ."""
    with pytest.raises(ModelFormatError, match="must equal veteran_id"):
        MilitaryPensionRecord(
            source_id=valid_source_id,
            source_urn=valid_pension_urn,
            record_category=SourceRecordCategory.MILITARY,
            description="Mismatched veteran claimant",
            repository_id=valid_repo_id,
            audit=valid_audit,
            veteran_id=IndividualID("IND-000001"),
            veteran_name_raw="Glenn Lehman",
            claimant_id=IndividualID("IND-000002"),
            claimant_name_raw="Glenn Lehman",
            claimant_role=PensionClaimantRole.VETERAN,
            payment_authority=PensionPaymentAuthority.US_BUREAU_OF_PENSIONS,
            application_year=HistoricalYear(1890),
        )


@pytest.mark.unit
@pytest.mark.regression
def test_military_pension_empty_names_fail(
    valid_source_id: SourceID,
    valid_pension_urn: SourceURN,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify ModelFormatError raised if raw names are empty or whitespace."""
    with pytest.raises(ModelFormatError, match="veteran_name_raw.*cannot be empty"):
        MilitaryPensionRecord(
            source_id=valid_source_id,
            source_urn=valid_pension_urn,
            record_category=SourceRecordCategory.MILITARY,
            description="Empty veteran name",
            repository_id=valid_repo_id,
            audit=valid_audit,
            veteran_id=IndividualID("IND-000001"),
            veteran_name_raw="   ",
            claimant_id=IndividualID("IND-000001"),
            claimant_name_raw="Glenn Lehman",
            claimant_role=PensionClaimantRole.VETERAN,
            payment_authority=PensionPaymentAuthority.US_BUREAU_OF_PENSIONS,
            application_year=HistoricalYear(1890),
        )

    with pytest.raises(ModelFormatError, match="claimant_name_raw.*cannot be empty"):
        MilitaryPensionRecord(
            source_id=valid_source_id,
            source_urn=valid_pension_urn,
            record_category=SourceRecordCategory.MILITARY,
            description="Empty claimant name",
            repository_id=valid_repo_id,
            audit=valid_audit,
            veteran_id=IndividualID("IND-000001"),
            veteran_name_raw="Glenn Lehman",
            claimant_id=IndividualID("IND-000001"),
            claimant_name_raw="   ",
            claimant_role=PensionClaimantRole.VETERAN,
            payment_authority=PensionPaymentAuthority.US_BUREAU_OF_PENSIONS,
            application_year=HistoricalYear(1890),
        )
