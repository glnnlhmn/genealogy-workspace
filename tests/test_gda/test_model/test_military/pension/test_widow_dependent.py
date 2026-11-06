"""Path: tests/test_gda/test_model/test_military/pension/test_widow_dependent.py

Atomized behavioral test suite for PensionWidowDependentRecord domain entity.

Operational Role:
    Verifies widow, minor orphan, and dependent parent pension claims, marriage
    chronology invariants, guardian appointments, and child schedules.

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
from gda.model.atom.id import IndividualID, LocationID, RepositoryID, SourceID
from gda.model.atom.urn import SourceURN
from gda.model.base.audit import AuditStamp
from gda.model.military.pension import (
    PensionClaimantRole,
    PensionPaymentAuthority,
    PensionWidowDependentRecord,
)

__version__ = "1.0.0+build.3"


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
    return SourceURN("URN:SRC:1895:US_PENSION:WIDOW_4412")


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
def test_pension_widow_smoke_valid_initialization(
    valid_source_id: SourceID,
    valid_pension_urn: SourceURN,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify minimal valid instantiation of PensionWidowDependentRecord."""
    rec = PensionWidowDependentRecord(
        source_id=valid_source_id,
        source_urn=valid_pension_urn,
        record_category=SourceRecordCategory.MILITARY,
        description="Widow pension claim certificate",
        repository_id=valid_repo_id,
        audit=valid_audit,
        veteran_id=IndividualID("IND-000001"),
        veteran_name_raw="Glenn D. Lehman",
        claimant_id=IndividualID("IND-000002"),
        claimant_name_raw="Martha Lehman",
        claimant_role=PensionClaimantRole.WIDOW,
        payment_authority=PensionPaymentAuthority.US_BUREAU_OF_PENSIONS,
        application_year=HistoricalYear(1895),
        application_number_raw="WO-512.901",
        certificate_number_raw="WC-399.112",
        veteran_death_year=HistoricalYear(1894),
        marriage_year=HistoricalYear(1866),
        minor_children_count=2,
        monthly_allowance_usd=12.0,
    )
    assert rec.claimant_role == PensionClaimantRole.WIDOW
    assert rec.marriage_year == HistoricalYear(1866)
    assert rec.veteran_death_year == HistoricalYear(1894)
    assert rec.minor_children_count == 2


# ==============================================================================
# GROUP 2: MINOR ORPHANS & REMARRIAGES
# ==============================================================================


@pytest.mark.unit
def test_pension_minor_orphan_guardian_claim(
    valid_source_id: SourceID,
    valid_pension_urn: SourceURN,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify PensionWidowDependentRecord supports minor orphan guardian claims."""
    guardian_id = IndividualID("IND-000005")
    loc_id = LocationID("LOC-000022")
    rec = PensionWidowDependentRecord(
        source_id=valid_source_id,
        source_urn=valid_pension_urn,
        record_category=SourceRecordCategory.MILITARY,
        description="Minor child pension executed by guardian",
        repository_id=valid_repo_id,
        audit=valid_audit,
        veteran_id=IndividualID("IND-000001"),
        veteran_name_raw="Glenn Lehman",
        claimant_id=IndividualID("IND-000003"),
        claimant_name_raw="Franklin Lehman",
        claimant_role=PensionClaimantRole.MINOR_CHILD,
        payment_authority=PensionPaymentAuthority.US_BUREAU_OF_PENSIONS,
        application_year=HistoricalYear(1896),
        guardian_id=guardian_id,
        guardian_name_raw="Horace Greeley",
        marriage_year=HistoricalYear(1866),
        marriage_location_raw="Concord, NH",
        marriage_location_id=loc_id,
    )
    assert rec.guardian_id == guardian_id
    assert rec.guardian_name_raw == "Horace Greeley"
    assert rec.claimant_role == PensionClaimantRole.MINOR_CHILD


@pytest.mark.unit
def test_pension_remarried_widow_valid_chronology(
    valid_source_id: SourceID,
    valid_pension_urn: SourceURN,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify PensionWidowDependentRecord permits valid remarriage sequence."""
    rec = PensionWidowDependentRecord(
        source_id=valid_source_id,
        source_urn=valid_pension_urn,
        record_category=SourceRecordCategory.MILITARY,
        description="Remarried widow restoration application",
        repository_id=valid_repo_id,
        audit=valid_audit,
        veteran_id=IndividualID("IND-000001"),
        veteran_name_raw="Glenn Lehman",
        claimant_id=IndividualID("IND-000002"),
        claimant_name_raw="Martha Lehman-Smith",
        claimant_role=PensionClaimantRole.REMARRIED_WIDOW,
        payment_authority=PensionPaymentAuthority.US_BUREAU_OF_PENSIONS,
        application_year=HistoricalYear(1901),
        marriage_year=HistoricalYear(1866),
        veteran_death_year=HistoricalYear(1894),
        remarriage_year=HistoricalYear(1898),
    )
    assert rec.claimant_role == PensionClaimantRole.REMARRIED_WIDOW
    assert rec.remarriage_year == HistoricalYear(1898)
    assert rec.marriage_year == HistoricalYear(1866)


# ==============================================================================
# GROUP 3: BOUNDARY & VALIDATION REJECTIONS
# ==============================================================================


@pytest.mark.unit
@pytest.mark.regression
def test_pension_widow_invalid_claimant_role_fails(
    valid_source_id: SourceID,
    valid_pension_urn: SourceURN,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify ModelFormatError raised if claimant_role is VETERAN."""
    with pytest.raises(ModelFormatError, match="requires claimant_role in"):
        PensionWidowDependentRecord(
            source_id=valid_source_id,
            source_urn=valid_pension_urn,
            record_category=SourceRecordCategory.MILITARY,
            description="Veteran filed under widow model",
            repository_id=valid_repo_id,
            audit=valid_audit,
            veteran_id=IndividualID("IND-000001"),
            veteran_name_raw="Glenn Lehman",
            claimant_id=IndividualID("IND-000001"),
            claimant_name_raw="Glenn Lehman",
            claimant_role=PensionClaimantRole.VETERAN,
            payment_authority=PensionPaymentAuthority.US_BUREAU_OF_PENSIONS,
            application_year=HistoricalYear(1895),
        )


@pytest.mark.unit
@pytest.mark.regression
def test_pension_widow_chronology_violations_fail(
    valid_source_id: SourceID,
    valid_pension_urn: SourceURN,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify ModelFormatError raised if death or remarriage precede marriage."""
    # Veteran death precedes marriage
    with pytest.raises(ModelFormatError, match="cannot precede marriage_year"):
        PensionWidowDependentRecord(
            source_id=valid_source_id,
            source_urn=valid_pension_urn,
            record_category=SourceRecordCategory.MILITARY,
            description="Death before marriage",
            repository_id=valid_repo_id,
            audit=valid_audit,
            veteran_id=IndividualID("IND-000001"),
            veteran_name_raw="Glenn Lehman",
            claimant_id=IndividualID("IND-000002"),
            claimant_name_raw="Martha Lehman",
            claimant_role=PensionClaimantRole.WIDOW,
            payment_authority=PensionPaymentAuthority.US_BUREAU_OF_PENSIONS,
            application_year=HistoricalYear(1895),
            marriage_year=HistoricalYear(1870),
            veteran_death_year=HistoricalYear(1865),
        )

    # Remarriage precedes marriage
    with pytest.raises(ModelFormatError, match="cannot precede marriage_year"):
        PensionWidowDependentRecord(
            source_id=valid_source_id,
            source_urn=valid_pension_urn,
            record_category=SourceRecordCategory.MILITARY,
            description="Remarriage before marriage",
            repository_id=valid_repo_id,
            audit=valid_audit,
            veteran_id=IndividualID("IND-000001"),
            veteran_name_raw="Glenn Lehman",
            claimant_id=IndividualID("IND-000002"),
            claimant_name_raw="Martha Lehman",
            claimant_role=PensionClaimantRole.REMARRIED_WIDOW,
            payment_authority=PensionPaymentAuthority.US_BUREAU_OF_PENSIONS,
            application_year=HistoricalYear(1895),
            marriage_year=HistoricalYear(1870),
            remarriage_year=HistoricalYear(1868),
        )
