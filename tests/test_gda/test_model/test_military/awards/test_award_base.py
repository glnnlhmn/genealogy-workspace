"""Path: tests/test_gda/test_model/test_military/awards/test_award_base.py

Atomized behavioral test suite for MilitaryAwardRecord domain entity.

Operational Role:
    Verifies military awards, valor medals, general orders, citation narratives,
    posthumous indicators, string hygiene, and chronological action invariants.

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
from gda.model.military.awards import (
    AwardScope,
    MilitaryAwardRecord,
    MilitaryAwardTier,
)
from gda.model.military.service import MilitaryBranch

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


# ==============================================================================
# GROUP 1: SMOKE & GOLDEN PATH
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_military_award_smoke_valid_initialization(
    valid_source_id: SourceID,
    valid_award_urn: SourceURN,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify minimal valid instantiation of MilitaryAwardRecord."""
    rec = MilitaryAwardRecord(
        source_id=valid_source_id,
        source_urn=valid_award_urn,
        record_category=SourceRecordCategory.MILITARY,
        description="WWII Silver Star Award Citation",
        repository_id=valid_repo_id,
        audit=valid_audit,
        recipient_id=IndividualID("IND-000001"),
        recipient_name_raw="Glenn D. Lehman",
        award_name_raw="Silver Star",
        branch=MilitaryBranch.ARMY,
        award_tier=MilitaryAwardTier.SILVER_STAR,
        award_scope=AwardScope.VALOR_IN_COMBAT,
        award_year=HistoricalYear(1945),
    )
    assert rec.recipient_id == IndividualID("IND-000001")
    assert rec.recipient_name_raw == "Glenn D. Lehman"
    assert rec.award_name_raw == "Silver Star"
    assert rec.award_tier == MilitaryAwardTier.SILVER_STAR
    assert rec.award_scope == AwardScope.VALOR_IN_COMBAT
    assert rec.award_year == HistoricalYear(1945)
    assert rec.action_year is None
    assert rec.is_posthumous is False
    assert "Silver Star" in str(rec)
    assert "1945" in str(rec)


# ==============================================================================
# GROUP 2: OPTIONAL LINKAGES & POSTHUMOUS VALOR
# ==============================================================================


@pytest.mark.unit
def test_military_award_full_attributes_and_posthumous(
    valid_source_id: SourceID,
    valid_award_urn: SourceURN,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify MilitaryAwardRecord preserves general orders, posthumous flag, and location."""
    loc_id = LocationID("LOC-000155")
    trn_id = TranscriptID("e1a646d3-9c61-4a70-8b14-c48c8b417c8f")
    rec = MilitaryAwardRecord(
        source_id=valid_source_id,
        source_urn=valid_award_urn,
        record_category=SourceRecordCategory.MILITARY,
        description="Medal of Honor General Order Citation",
        repository_id=valid_repo_id,
        audit=valid_audit,
        recipient_id=IndividualID("IND-000001"),
        recipient_name_raw="Glenn Lehman",
        award_name_raw="Medal of Honor",
        branch=MilitaryBranch.ARMY,
        award_tier=MilitaryAwardTier.MEDAL_OF_HONOR,
        award_scope=AwardScope.VALOR_IN_COMBAT,
        award_year=HistoricalYear(1946),
        action_year=HistoricalYear(1944),
        general_order_raw="War Department General Orders No. 71",
        issuing_authority_raw="Headquarters, First United States Army",
        is_posthumous=True,
        action_location_raw="St. Lo, Normandy, France",
        action_location_id=loc_id,
        transcript_id=trn_id,
    )
    assert rec.action_year == HistoricalYear(1944)
    assert rec.general_order_raw == "War Department General Orders No. 71"
    assert rec.issuing_authority_raw == "Headquarters, First United States Army"
    assert rec.is_posthumous is True
    assert rec.action_location_raw == "St. Lo, Normandy, France"
    assert rec.action_location_id == loc_id
    assert rec.transcript_id == trn_id
    assert "(Posthumous)" in str(rec)


@pytest.mark.unit
def test_military_award_same_action_and_award_year(
    valid_source_id: SourceID,
    valid_award_urn: SourceURN,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify MilitaryAwardRecord permits action_year to equal award_year."""
    rec = MilitaryAwardRecord(
        source_id=valid_source_id,
        source_urn=valid_award_urn,
        record_category=SourceRecordCategory.MILITARY,
        description="Immediate Purple Heart presentation",
        repository_id=valid_repo_id,
        audit=valid_audit,
        recipient_id=IndividualID("IND-000001"),
        recipient_name_raw="Glenn Lehman",
        award_name_raw="Purple Heart",
        branch=MilitaryBranch.ARMY,
        award_tier=MilitaryAwardTier.PURPLE_HEART,
        award_scope=AwardScope.WOUND_IN_ACTION,
        award_year=HistoricalYear(1944),
        action_year=HistoricalYear(1944),
    )
    assert rec.action_year == rec.award_year


# ==============================================================================
# GROUP 3: BOUNDARY & VALIDATION REJECTIONS
# ==============================================================================


@pytest.mark.unit
@pytest.mark.regression
def test_military_award_invalid_category_fails(
    valid_source_id: SourceID,
    valid_award_urn: SourceURN,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify ModelFormatError raised if record_category is not MILITARY."""
    with pytest.raises(ModelFormatError, match="requires category 'MILITARY'"):
        MilitaryAwardRecord(
            source_id=valid_source_id,
            source_urn=valid_award_urn,
            record_category=SourceRecordCategory.CENSUS,
            description="Mismatched category",
            repository_id=valid_repo_id,
            audit=valid_audit,
            recipient_id=IndividualID("IND-000001"),
            recipient_name_raw="Glenn Lehman",
            award_name_raw="Silver Star",
            branch=MilitaryBranch.ARMY,
            award_tier=MilitaryAwardTier.SILVER_STAR,
            award_scope=AwardScope.VALOR_IN_COMBAT,
            award_year=HistoricalYear(1945),
        )


@pytest.mark.unit
@pytest.mark.regression
def test_military_award_chronology_inverted_fails(
    valid_source_id: SourceID,
    valid_award_urn: SourceURN,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify ModelFormatError raised if award_year precedes action_year."""
    with pytest.raises(ModelFormatError, match="cannot precede action_year"):
        MilitaryAwardRecord(
            source_id=valid_source_id,
            source_urn=valid_award_urn,
            record_category=SourceRecordCategory.MILITARY,
            description="Inverted award dates",
            repository_id=valid_repo_id,
            audit=valid_audit,
            recipient_id=IndividualID("IND-000001"),
            recipient_name_raw="Glenn Lehman",
            award_name_raw="Bronze Star",
            branch=MilitaryBranch.ARMY,
            award_tier=MilitaryAwardTier.BRONZE_STAR,
            award_scope=AwardScope.MERITORIOUS_SERVICE,
            award_year=HistoricalYear(1943),
            action_year=HistoricalYear(1944),
        )


@pytest.mark.unit
@pytest.mark.regression
def test_military_award_empty_required_strings_fail(
    valid_source_id: SourceID,
    valid_award_urn: SourceURN,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify ModelFormatError raised if recipient_name_raw or award_name_raw is whitespace."""
    with pytest.raises(ModelFormatError, match="recipient_name_raw.*cannot be empty"):
        MilitaryAwardRecord(
            source_id=valid_source_id,
            source_urn=valid_award_urn,
            record_category=SourceRecordCategory.MILITARY,
            description="Empty recipient name",
            repository_id=valid_repo_id,
            audit=valid_audit,
            recipient_id=IndividualID("IND-000001"),
            recipient_name_raw="   ",
            award_name_raw="Silver Star",
            branch=MilitaryBranch.ARMY,
            award_tier=MilitaryAwardTier.SILVER_STAR,
            award_scope=AwardScope.VALOR_IN_COMBAT,
            award_year=HistoricalYear(1945),
        )

    with pytest.raises(ModelFormatError, match="award_name_raw.*cannot be empty"):
        MilitaryAwardRecord(
            source_id=valid_source_id,
            source_urn=valid_award_urn,
            record_category=SourceRecordCategory.MILITARY,
            description="Empty award name",
            repository_id=valid_repo_id,
            audit=valid_audit,
            recipient_id=IndividualID("IND-000001"),
            recipient_name_raw="Glenn Lehman",
            award_name_raw="   ",
            branch=MilitaryBranch.ARMY,
            award_tier=MilitaryAwardTier.SILVER_STAR,
            award_scope=AwardScope.VALOR_IN_COMBAT,
            award_year=HistoricalYear(1945),
        )


@pytest.mark.unit
@pytest.mark.regression
def test_military_award_empty_optional_strings_fail(
    valid_source_id: SourceID,
    valid_award_urn: SourceURN,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify ModelFormatError raised if optional strings are provided as whitespace."""
    with pytest.raises(ModelFormatError, match="general_order_raw.*cannot be empty"):
        MilitaryAwardRecord(
            source_id=valid_source_id,
            source_urn=valid_award_urn,
            record_category=SourceRecordCategory.MILITARY,
            description="Empty GO test",
            repository_id=valid_repo_id,
            audit=valid_audit,
            recipient_id=IndividualID("IND-000001"),
            recipient_name_raw="Glenn Lehman",
            award_name_raw="Silver Star",
            branch=MilitaryBranch.ARMY,
            award_tier=MilitaryAwardTier.SILVER_STAR,
            award_scope=AwardScope.VALOR_IN_COMBAT,
            award_year=HistoricalYear(1945),
            general_order_raw="   ",
        )

    with pytest.raises(
        ModelFormatError, match="issuing_authority_raw.*cannot be empty"
    ):
        MilitaryAwardRecord(
            source_id=valid_source_id,
            source_urn=valid_award_urn,
            record_category=SourceRecordCategory.MILITARY,
            description="Empty authority test",
            repository_id=valid_repo_id,
            audit=valid_audit,
            recipient_id=IndividualID("IND-000001"),
            recipient_name_raw="Glenn Lehman",
            award_name_raw="Silver Star",
            branch=MilitaryBranch.ARMY,
            award_tier=MilitaryAwardTier.SILVER_STAR,
            award_scope=AwardScope.VALOR_IN_COMBAT,
            award_year=HistoricalYear(1945),
            issuing_authority_raw="   ",
        )

    with pytest.raises(ModelFormatError, match="action_location_raw.*cannot be empty"):
        MilitaryAwardRecord(
            source_id=valid_source_id,
            source_urn=valid_award_urn,
            record_category=SourceRecordCategory.MILITARY,
            description="Empty action location test",
            repository_id=valid_repo_id,
            audit=valid_audit,
            recipient_id=IndividualID("IND-000001"),
            recipient_name_raw="Glenn Lehman",
            award_name_raw="Silver Star",
            branch=MilitaryBranch.ARMY,
            award_tier=MilitaryAwardTier.SILVER_STAR,
            award_scope=AwardScope.VALOR_IN_COMBAT,
            award_year=HistoricalYear(1945),
            action_location_raw="   ",
        )
