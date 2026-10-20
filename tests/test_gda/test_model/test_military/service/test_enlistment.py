"""Path: tests/test_gda/test_model/test_military/service/test_enlistment.py

Atomized behavioral test suite for EnlistmentMusterRecord domain entity.

Operational Role:
    Verifies enlistment contracts, muster rolls, CMSR jacket structures,
    term length constraints, bounties, and substitute linkages.

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
from gda.model.atom.id import IndividualID, RepositoryID, ServiceRecordID, SourceID
from gda.model.atom.urn import SourceURN
from gda.model.base.audit import AuditStamp
from gda.model.military.service.base import (
    MilitaryBranch,
    SeparationCharacter,
    ServiceComponent,
)
from gda.model.military.service.enlistment import (
    EnlistmentMusterRecord,
    MusterRollType,
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
def valid_service_urn() -> SourceURN:
    """Return synthetic SourceURN."""
    return SourceURN("URN:SRC:1862:NH_MUSTER:VOL1_P102")


@pytest.fixture
def valid_repo_id() -> RepositoryID:
    """Return synthetic RepositoryID."""
    return RepositoryID("REP-000001")


@pytest.fixture
def valid_source_id() -> SourceID:
    """Return synthetic SourceID."""
    return SourceID("c9a646d3-9c61-4a70-8b14-c48c8b417c8d")


@pytest.fixture
def valid_service_record_id() -> ServiceRecordID:
    """Return synthetic ServiceRecordID."""
    return ServiceRecordID("a1a646d3-9c61-4a70-8b14-c48c8b417c8a")


# ==============================================================================
# GROUP 1: SMOKE & GOLDEN PATH
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_enlistment_muster_smoke_valid_initialization(
    valid_source_id: SourceID,
    valid_service_urn: SourceURN,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
    valid_service_record_id: ServiceRecordID,
) -> None:
    """Verify minimal valid instantiation of EnlistmentMusterRecord."""
    rec = EnlistmentMusterRecord(
        source_id=valid_source_id,
        source_urn=valid_service_urn,
        record_category=SourceRecordCategory.MILITARY,
        description="Muster-in roll for Glenn Lehman",
        repository_id=valid_repo_id,
        audit=valid_audit,
        service_record_id=valid_service_record_id,
        veteran_id=IndividualID("IND-000001"),
        veteran_name_raw="Glenn D. Lehman",
        branch=MilitaryBranch.ARMY,
        service_component=ServiceComponent.VOLUNTEER,
        unit_designation_raw="Co. B, 2nd New Hampshire Volunteer Infantry",
        rank_raw="Private",
        enlistment_year=HistoricalYear(1861),
        separation_year=HistoricalYear(1864),
        roll_type=MusterRollType.MUSTER_IN,
    )
    assert rec.roll_type == MusterRollType.MUSTER_IN
    assert rec.enlistment_term_months is None
    assert rec.bounty_paid_usd is None
    assert rec.substitute_for_id is None
    assert "Private" in str(rec)


# ==============================================================================
# GROUP 2: BOUNTIES, TERMS & SUBSTITUTES
# ==============================================================================


@pytest.mark.unit
def test_enlistment_muster_full_bounty_and_substitute(
    valid_source_id: SourceID,
    valid_service_urn: SourceURN,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
    valid_service_record_id: ServiceRecordID,
) -> None:
    """Verify EnlistmentMusterRecord preserves bounty, credit, and substitute data."""
    sub_principal_id = IndividualID("IND-000099")
    rec = EnlistmentMusterRecord(
        source_id=valid_source_id,
        source_urn=valid_service_urn,
        record_category=SourceRecordCategory.MILITARY,
        description="Substitute enlistment roll entry",
        repository_id=valid_repo_id,
        audit=valid_audit,
        service_record_id=valid_service_record_id,
        veteran_id=IndividualID("IND-000001"),
        veteran_name_raw="Glenn Lehman",
        branch=MilitaryBranch.ARMY,
        service_component=ServiceComponent.VOLUNTEER,
        unit_designation_raw="Co. E, 14th New Hampshire Volunteers",
        rank_raw="Private",
        enlistment_year=HistoricalYear(1863),
        separation_year=HistoricalYear(1865),
        separation_character=SeparationCharacter.HONORABLE,
        roll_type=MusterRollType.ENLISTMENT_CONTRACT,
        enlistment_term_months=36,
        muster_officer_raw="Capt. William H. Chaffin",
        bounty_paid_usd=100.0,
        bounty_due_usd=200.0,
        credited_town_or_ward_raw="Concord, Ward 4",
        substitute_for_id=sub_principal_id,
        substitute_for_name_raw="Ebenezer Sargent",
    )
    assert rec.enlistment_term_months == 36
    assert rec.muster_officer_raw == "Capt. William H. Chaffin"
    assert rec.bounty_paid_usd == 100.0
    assert rec.bounty_due_usd == 200.0
    assert rec.credited_town_or_ward_raw == "Concord, Ward 4"
    assert rec.substitute_for_id == sub_principal_id
    assert rec.substitute_for_name_raw == "Ebenezer Sargent"


@pytest.mark.unit
def test_enlistment_muster_substitute_id_only(
    valid_source_id: SourceID,
    valid_service_urn: SourceURN,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
    valid_service_record_id: ServiceRecordID,
) -> None:
    """Verify EnlistmentMusterRecord permits substitute_for_id without name."""
    sub_principal_id = IndividualID("IND-000099")
    rec = EnlistmentMusterRecord(
        source_id=valid_source_id,
        source_urn=valid_service_urn,
        record_category=SourceRecordCategory.MILITARY,
        description="Substitute with resolved ID only",
        repository_id=valid_repo_id,
        audit=valid_audit,
        service_record_id=valid_service_record_id,
        veteran_id=IndividualID("IND-000001"),
        veteran_name_raw="Glenn Lehman",
        branch=MilitaryBranch.ARMY,
        unit_designation_raw="Co. A",
        rank_raw="Private",
        roll_type=MusterRollType.CMSR_JACKET,
        substitute_for_id=sub_principal_id,
    )
    assert rec.substitute_for_id == sub_principal_id
    assert rec.substitute_for_name_raw is None


# ==============================================================================
# GROUP 3: BOUNDARY & VALIDATION REJECTIONS
# ==============================================================================


@pytest.mark.unit
@pytest.mark.regression
def test_enlistment_muster_empty_substitute_name_fails(
    valid_source_id: SourceID,
    valid_service_urn: SourceURN,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
    valid_service_record_id: ServiceRecordID,
) -> None:
    """Verify ModelFormatError raised when substitute name is empty without an ID."""
    with pytest.raises(
        ModelFormatError, match="requires non-empty substitute_for_name_raw"
    ):
        EnlistmentMusterRecord(
            source_id=valid_source_id,
            source_urn=valid_service_urn,
            record_category=SourceRecordCategory.MILITARY,
            description="Empty substitute name",
            repository_id=valid_repo_id,
            audit=valid_audit,
            service_record_id=valid_service_record_id,
            veteran_id=IndividualID("IND-000001"),
            veteran_name_raw="Glenn Lehman",
            branch=MilitaryBranch.ARMY,
            unit_designation_raw="Co. A",
            rank_raw="Private",
            roll_type=MusterRollType.MUSTER_IN,
            substitute_for_name_raw="   ",
        )
