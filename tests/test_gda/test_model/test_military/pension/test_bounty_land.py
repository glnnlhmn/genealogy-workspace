"""Path: tests/test_gda/test_model/test_military/pension/test_bounty_land.py

Atomized behavioral test suite for BountyLandWarrantRecord domain entity.

Operational Role:
    Verifies federal bounty land warrant certificates, acreage allocations,
    statutory Congressional Act references, and assignee transfer linkages.

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
    BountyLandAct,
    BountyLandWarrantRecord,
    PensionClaimantRole,
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
def valid_bounty_urn() -> SourceURN:
    """Return synthetic SourceURN."""
    return SourceURN("URN:SRC:1855:GLO:BLW_10492")


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
def test_bounty_land_warrant_smoke_valid_initialization(
    valid_source_id: SourceID,
    valid_bounty_urn: SourceURN,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify minimal valid instantiation of BountyLandWarrantRecord."""
    rec = BountyLandWarrantRecord(
        source_id=valid_source_id,
        source_urn=valid_bounty_urn,
        record_category=SourceRecordCategory.MILITARY,
        description="War of 1812 Bounty Land Warrant Certificate",
        repository_id=valid_repo_id,
        audit=valid_audit,
        veteran_id=IndividualID("IND-000001"),
        veteran_name_raw="Glenn D. Lehman",
        warrantee_id=IndividualID("IND-000001"),
        warrantee_name_raw="Glenn D. Lehman",
        claimant_role=PensionClaimantRole.VETERAN,
        bounty_act=BountyLandAct.ACT_OF_1855,
        warrant_number_raw="BLW-10492",
        acreage=160,
        warrant_year=HistoricalYear(1855),
    )
    assert rec.warrant_number_raw == "BLW-10492"
    assert rec.acreage == 160
    assert rec.bounty_act == BountyLandAct.ACT_OF_1855
    assert rec.warrant_year == HistoricalYear(1855)
    assert rec.assignee_id is None
    assert "160 acres" in str(rec)
    assert "Glenn D. Lehman" in str(rec)


# ==============================================================================
# GROUP 2: ASSIGNEES & GLO PATENTS
# ==============================================================================


@pytest.mark.unit
def test_bounty_land_warrant_full_assignee_and_patent(
    valid_source_id: SourceID,
    valid_bounty_urn: SourceURN,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify BountyLandWarrantRecord preserves assignee transfers and GLO offices."""
    assignee_id = IndividualID("IND-000099")
    loc_id = LocationID("LOC-000044")
    trn_id = TranscriptID("e1a646d3-9c61-4a70-8b14-c48c8b417c8f")
    rec = BountyLandWarrantRecord(
        source_id=valid_source_id,
        source_urn=valid_bounty_urn,
        record_category=SourceRecordCategory.MILITARY,
        description="Assigned warrant located at Fort Des Moines Land Office",
        repository_id=valid_repo_id,
        audit=valid_audit,
        veteran_id=IndividualID("IND-000001"),
        veteran_name_raw="Glenn Lehman",
        warrantee_id=IndividualID("IND-000002"),
        warrantee_name_raw="Martha Lehman",
        claimant_role=PensionClaimantRole.WIDOW,
        bounty_act=BountyLandAct.ACT_OF_1850,
        warrant_number_raw="BLW-55120",
        acreage=80,
        warrant_year=HistoricalYear(1852),
        patent_land_office_raw="Fort Des Moines Land Office, Iowa",
        patent_location_id=loc_id,
        assignee_id=assignee_id,
        assignee_name_raw="Josiah Bartlett",
        transcript_id=trn_id,
    )
    assert rec.assignee_id == assignee_id
    assert rec.assignee_name_raw == "Josiah Bartlett"
    assert rec.patent_land_office_raw == "Fort Des Moines Land Office, Iowa"
    assert rec.patent_location_id == loc_id
    assert rec.transcript_id == trn_id


@pytest.mark.unit
def test_bounty_land_warrant_assignee_id_only(
    valid_source_id: SourceID,
    valid_bounty_urn: SourceURN,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify BountyLandWarrantRecord permits assignee_id without assignee_name_raw."""
    assignee_id = IndividualID("IND-000099")
    rec = BountyLandWarrantRecord(
        source_id=valid_source_id,
        source_urn=valid_bounty_urn,
        record_category=SourceRecordCategory.MILITARY,
        description="Assigned warrant with ID only",
        repository_id=valid_repo_id,
        audit=valid_audit,
        veteran_id=IndividualID("IND-000001"),
        veteran_name_raw="Glenn Lehman",
        warrantee_id=IndividualID("IND-000001"),
        warrantee_name_raw="Glenn Lehman",
        claimant_role=PensionClaimantRole.VETERAN,
        bounty_act=BountyLandAct.ACT_OF_1855,
        warrant_number_raw="BLW-10492",
        acreage=160,
        warrant_year=HistoricalYear(1855),
        assignee_id=assignee_id,
    )
    assert rec.assignee_id == assignee_id
    assert rec.assignee_name_raw is None


# ==============================================================================
# GROUP 3: BOUNDARY & VALIDATION REJECTIONS
# ==============================================================================


@pytest.mark.unit
@pytest.mark.regression
def test_bounty_land_warrant_invalid_category_fails(
    valid_source_id: SourceID,
    valid_bounty_urn: SourceURN,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify ModelFormatError raised if record_category is not MILITARY."""
    with pytest.raises(ModelFormatError, match="requires category 'MILITARY'"):
        BountyLandWarrantRecord(
            source_id=valid_source_id,
            source_urn=valid_bounty_urn,
            record_category=SourceRecordCategory.CENSUS,
            description="Mismatched category",
            repository_id=valid_repo_id,
            audit=valid_audit,
            veteran_id=IndividualID("IND-000001"),
            veteran_name_raw="Glenn Lehman",
            warrantee_id=IndividualID("IND-000001"),
            warrantee_name_raw="Glenn Lehman",
            claimant_role=PensionClaimantRole.VETERAN,
            bounty_act=BountyLandAct.ACT_OF_1855,
            warrant_number_raw="BLW-10492",
            acreage=160,
            warrant_year=HistoricalYear(1855),
        )


@pytest.mark.unit
@pytest.mark.regression
def test_bounty_land_warrant_empty_strings_fail(
    valid_source_id: SourceID,
    valid_bounty_urn: SourceURN,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify ModelFormatError raised if required raw strings are whitespace."""
    with pytest.raises(ModelFormatError, match="veteran_name_raw.*cannot be empty"):
        BountyLandWarrantRecord(
            source_id=valid_source_id,
            source_urn=valid_bounty_urn,
            record_category=SourceRecordCategory.MILITARY,
            description="Empty veteran name",
            repository_id=valid_repo_id,
            audit=valid_audit,
            veteran_id=IndividualID("IND-000001"),
            veteran_name_raw="   ",
            warrantee_id=IndividualID("IND-000001"),
            warrantee_name_raw="Glenn Lehman",
            claimant_role=PensionClaimantRole.VETERAN,
            bounty_act=BountyLandAct.ACT_OF_1855,
            warrant_number_raw="BLW-10492",
            acreage=160,
            warrant_year=HistoricalYear(1855),
        )

    with pytest.raises(ModelFormatError, match="warrantee_name_raw.*cannot be empty"):
        BountyLandWarrantRecord(
            source_id=valid_source_id,
            source_urn=valid_bounty_urn,
            record_category=SourceRecordCategory.MILITARY,
            description="Empty warrantee name",
            repository_id=valid_repo_id,
            audit=valid_audit,
            veteran_id=IndividualID("IND-000001"),
            veteran_name_raw="Glenn Lehman",
            warrantee_id=IndividualID("IND-000001"),
            warrantee_name_raw="   ",
            claimant_role=PensionClaimantRole.VETERAN,
            bounty_act=BountyLandAct.ACT_OF_1855,
            warrant_number_raw="BLW-10492",
            acreage=160,
            warrant_year=HistoricalYear(1855),
        )

    with pytest.raises(ModelFormatError, match="warrant_number_raw.*cannot be empty"):
        BountyLandWarrantRecord(
            source_id=valid_source_id,
            source_urn=valid_bounty_urn,
            record_category=SourceRecordCategory.MILITARY,
            description="Empty warrant number",
            repository_id=valid_repo_id,
            audit=valid_audit,
            veteran_id=IndividualID("IND-000001"),
            veteran_name_raw="Glenn Lehman",
            warrantee_id=IndividualID("IND-000001"),
            warrantee_name_raw="Glenn Lehman",
            claimant_role=PensionClaimantRole.VETERAN,
            bounty_act=BountyLandAct.ACT_OF_1855,
            warrant_number_raw="   ",
            acreage=160,
            warrant_year=HistoricalYear(1855),
        )


@pytest.mark.unit
@pytest.mark.regression
def test_bounty_land_warrant_empty_assignee_name_fails(
    valid_source_id: SourceID,
    valid_bounty_urn: SourceURN,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify ModelFormatError raised if assignee name is empty without an ID."""
    with pytest.raises(ModelFormatError, match="requires non-empty assignee_name_raw"):
        BountyLandWarrantRecord(
            source_id=valid_source_id,
            source_urn=valid_bounty_urn,
            record_category=SourceRecordCategory.MILITARY,
            description="Whitespace assignee name",
            repository_id=valid_repo_id,
            audit=valid_audit,
            veteran_id=IndividualID("IND-000001"),
            veteran_name_raw="Glenn Lehman",
            warrantee_id=IndividualID("IND-000001"),
            warrantee_name_raw="Glenn Lehman",
            claimant_role=PensionClaimantRole.VETERAN,
            bounty_act=BountyLandAct.ACT_OF_1855,
            warrant_number_raw="BLW-10492",
            acreage=160,
            warrant_year=HistoricalYear(1855),
            assignee_name_raw="   ",
        )
