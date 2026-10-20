"""Path: tests/test_gda/test_model/test_military/draft/test_modern_sss.py

Atomized behavioral test suite for ModernSelectiveServiceRecord domain entity.

Operational Role:
    Verifies modern Selective Service registration invariants, Vietnam lottery
    number constraints (1-366), post-1948 year boundaries, and SSS classifications.

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
from gda.model.atom.id import DraftRecordID, IndividualID, RepositoryID, SourceID
from gda.model.atom.urn import MilitaryDraftUrn
from gda.model.base.audit import AuditStamp
from gda.model.military.draft.base import DraftCardTier
from gda.model.military.draft.modern_sss import (
    ModernDraftEra,
    ModernSelectiveServiceRecord,
    SssClassification,
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
def valid_draft_urn() -> MilitaryDraftUrn:
    """Return synthetic MilitaryDraftUrn for modern SSS."""
    return MilitaryDraftUrn("URN:DRAFT:1970:NH_BOARD4:CARD_001")


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
def test_modern_sss_smoke_valid_initialization(
    valid_source_id: SourceID,
    valid_draft_urn: MilitaryDraftUrn,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify minimal valid instantiation of ModernSelectiveServiceRecord."""
    rec = ModernSelectiveServiceRecord(
        source_id=valid_source_id,
        source_urn=valid_draft_urn,
        record_category=SourceRecordCategory.MILITARY,
        description="Vietnam Era Selective Service Registration for Glenn Lehman",
        repository_id=valid_repo_id,
        audit=valid_audit,
        draft_record_id=DraftRecordID("DRF-000001"),
        registrant_id=IndividualID("IND-000001"),
        registrant_name_raw="Glenn Lehman",
        draft_year=HistoricalYear(1970),
        board_jurisdiction_raw="New Hampshire Local Board No. 4, Concord",
        card_tier=DraftCardTier.OTHER,
        draft_era=ModernDraftEra.VIETNAM_LOTTERY,
        lottery_sequence_number=195,
        classification=SssClassification.ONE_A,
    )
    assert rec.draft_era == ModernDraftEra.VIETNAM_LOTTERY
    assert rec.lottery_sequence_number == 195
    assert rec.classification == SssClassification.ONE_A
    assert "Glenn Lehman" in str(rec)


# ==============================================================================
# GROUP 2: POST-1980 CONTINUOUS REGISTRATION
# ==============================================================================


@pytest.mark.unit
def test_modern_sss_post_1980_registration(
    valid_source_id: SourceID,
    valid_draft_urn: MilitaryDraftUrn,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify ModernSelectiveServiceRecord handles continuous modern registrations."""
    rec = ModernSelectiveServiceRecord(
        source_id=valid_source_id,
        source_urn=valid_draft_urn,
        record_category=SourceRecordCategory.MILITARY,
        description="Post-1980 SSS Registration",
        repository_id=valid_repo_id,
        audit=valid_audit,
        draft_record_id=DraftRecordID("DRF-000002"),
        registrant_id=IndividualID("IND-000001"),
        registrant_name_raw="Glenn Lehman",
        draft_year=HistoricalYear(1980),
        board_jurisdiction_raw="Selective Service System National Headquarters",
        card_tier=DraftCardTier.OTHER,
        draft_era=ModernDraftEra.POST_1980_REGISTRATION,
        sss_number_raw="27-04-62-094",
        classification=SssClassification.UNCLASSIFIED,
    )
    assert rec.draft_era == ModernDraftEra.POST_1980_REGISTRATION
    assert rec.sss_number_raw == "27-04-62-094"
    assert rec.lottery_sequence_number is None


# ==============================================================================
# GROUP 3: BOUNDARY & VALIDATION REJECTIONS
# ==============================================================================


@pytest.mark.unit
@pytest.mark.regression
def test_modern_sss_pre_1948_fails(
    valid_source_id: SourceID,
    valid_draft_urn: MilitaryDraftUrn,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify ModelFormatError raised if draft_year is prior to 1948."""
    with pytest.raises(ModelFormatError, match="draft_year must be 1948 or later"):
        ModernSelectiveServiceRecord(
            source_id=valid_source_id,
            source_urn=valid_draft_urn,
            record_category=SourceRecordCategory.MILITARY,
            description="Pre-1948 year",
            repository_id=valid_repo_id,
            audit=valid_audit,
            draft_record_id=DraftRecordID("DRF-000001"),
            registrant_id=IndividualID("IND-000001"),
            registrant_name_raw="Glenn Lehman",
            draft_year=HistoricalYear(1945),
            board_jurisdiction_raw="Local Board",
            card_tier=DraftCardTier.OTHER,
            draft_era=ModernDraftEra.POST_WWII_1948,
        )


@pytest.mark.unit
@pytest.mark.regression
def test_modern_sss_lottery_number_outside_vietnam_era_fails(
    valid_source_id: SourceID,
    valid_draft_urn: MilitaryDraftUrn,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify ModelFormatError raised if lottery_sequence_number specified outside Vietnam era."""
    with pytest.raises(
        ModelFormatError, match="only applicable during the VIETNAM_LOTTERY era"
    ):
        ModernSelectiveServiceRecord(
            source_id=valid_source_id,
            source_urn=valid_draft_urn,
            record_category=SourceRecordCategory.MILITARY,
            description="Lottery number with invalid era",
            repository_id=valid_repo_id,
            audit=valid_audit,
            draft_record_id=DraftRecordID("DRF-000001"),
            registrant_id=IndividualID("IND-000001"),
            registrant_name_raw="Glenn Lehman",
            draft_year=HistoricalYear(1951),
            board_jurisdiction_raw="Local Board",
            card_tier=DraftCardTier.OTHER,
            draft_era=ModernDraftEra.KOREAN_WAR,
            lottery_sequence_number=45,
        )
