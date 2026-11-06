"""Path: tests/test_gda/test_model/test_military/pension/test_veteran_claim.py

Atomized behavioral test suite for PensionVeteranClaimRecord domain entity.

Operational Role:
    Verifies invalid veteran disability claims, monthly allowance metrics,
    disability percentages, and surgeon board evaluations.

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
from gda.model.atom.id import IndividualID, RepositoryID, SourceID
from gda.model.atom.urn import SourceURN
from gda.model.base.audit import AuditStamp
from gda.model.military.pension import (
    PensionClaimantRole,
    PensionPaymentAuthority,
    PensionVeteranClaimRecord,
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
    return SourceURN("URN:SRC:1885:US_PENSION:DIS_CLAIM_10")


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
def test_pension_veteran_claim_smoke_valid_initialization(
    valid_source_id: SourceID,
    valid_pension_urn: SourceURN,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify minimal valid instantiation of PensionVeteranClaimRecord."""
    rec = PensionVeteranClaimRecord(
        source_id=valid_source_id,
        source_urn=valid_pension_urn,
        record_category=SourceRecordCategory.MILITARY,
        description="Invalid disability pension certificate",
        repository_id=valid_repo_id,
        audit=valid_audit,
        veteran_id=IndividualID("IND-000001"),
        veteran_name_raw="Glenn D. Lehman",
        claimant_id=IndividualID("IND-000001"),
        claimant_name_raw="Glenn D. Lehman",
        claimant_role=PensionClaimantRole.VETERAN,
        payment_authority=PensionPaymentAuthority.US_BUREAU_OF_PENSIONS,
        application_year=HistoricalYear(1885),
        application_number_raw="SO-410.291",
        certificate_number_raw="SC-302.119",
        disability_description_raw="Gunshot wound to left shoulder received at Cold Harbor",
        monthly_allowance_usd=12.0,
        disability_rating_percentage=50,
        examining_surgeon_raw="Dr. Charles P. Bancroft",
    )
    assert rec.claimant_role == PensionClaimantRole.VETERAN
    assert rec.disability_rating_percentage == 50
    assert rec.monthly_allowance_usd == 12.0
    assert rec.examining_surgeon_raw == "Dr. Charles P. Bancroft"
    assert "Cold Harbor" in str(rec.disability_description_raw)


# ==============================================================================
# GROUP 2: BOUNDARY & VALIDATION REJECTIONS
# ==============================================================================


@pytest.mark.unit
@pytest.mark.regression
def test_pension_veteran_claim_invalid_claimant_role_fails(
    valid_source_id: SourceID,
    valid_pension_urn: SourceURN,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify ModelFormatError raised if claimant_role is not VETERAN."""
    with pytest.raises(ModelFormatError, match="requires claimant_role 'VETERAN'"):
        PensionVeteranClaimRecord(
            source_id=valid_source_id,
            source_urn=valid_pension_urn,
            record_category=SourceRecordCategory.MILITARY,
            description="Widow filed under veteran claim",
            repository_id=valid_repo_id,
            audit=valid_audit,
            veteran_id=IndividualID("IND-000001"),
            veteran_name_raw="Glenn Lehman",
            claimant_id=IndividualID("IND-000002"),
            claimant_name_raw="Martha Lehman",
            claimant_role=PensionClaimantRole.WIDOW,
            payment_authority=PensionPaymentAuthority.US_BUREAU_OF_PENSIONS,
            application_year=HistoricalYear(1885),
        )
