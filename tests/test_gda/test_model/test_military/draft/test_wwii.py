"""Path: tests/test_gda/test_model/test_military/draft/test_wwii.py

Atomized behavioral test suite for WwiiDraftCardRecord domain entity.

Operational Role:
    Verifies WWII draft registration invariants, wave classifications, contact person
    linkages, physical metrics (inches/lbs), and 1940-1946 registration year boundaries.

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
from gda.model.military.draft.wwii import (
    WwiiDraftCardRecord,
    WwiiDraftWave,
    WwiiPhysicalMetrics,
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
    """Return synthetic MilitaryDraftUrn for WWII."""
    return MilitaryDraftUrn("URN:DRAFT:1942:NH_MERRIMACK:CARD_001")


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
def test_wwii_draft_card_smoke_valid_initialization(
    valid_source_id: SourceID,
    valid_draft_urn: MilitaryDraftUrn,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify minimal valid instantiation of WwiiDraftCardRecord golden path."""
    rec = WwiiDraftCardRecord(
        source_id=valid_source_id,
        source_urn=valid_draft_urn,
        record_category=SourceRecordCategory.MILITARY,
        description="WWII Fourth Registration (Old Man's Draft) Card for Glenn Lehman",
        repository_id=valid_repo_id,
        audit=valid_audit,
        draft_record_id=DraftRecordID("DRF-000001"),
        registrant_id=IndividualID("IND-000001"),
        registrant_name_raw="Glenn D. Lehman",
        draft_year=HistoricalYear(1942),
        board_jurisdiction_raw="Merrimack County Local Board No. 1",
        card_tier=DraftCardTier.WWII_FOURTH,
        draft_wave=WwiiDraftWave.FOURTH_OLD_MANS,
    )
    assert rec.draft_wave == WwiiDraftWave.FOURTH_OLD_MANS
    assert rec.card_tier == DraftCardTier.WWII_FOURTH
    assert rec.draft_year == HistoricalYear(1942)
    assert rec.physical_metrics is None
    assert "Glenn D. Lehman" in str(rec)


# ==============================================================================
# GROUP 2: CONTACT PERSON & PHYSICAL METRICS
# ==============================================================================


@pytest.mark.unit
def test_wwii_draft_card_full_metrics_and_contact(
    valid_source_id: SourceID,
    valid_draft_urn: MilitaryDraftUrn,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify WwiiDraftCardRecord captures physical metrics and contact person."""
    contact_id = IndividualID("IND-000002")
    metrics = WwiiPhysicalMetrics(
        race_verbatim="White",
        height_inches=70,
        weight_lbs=165,
        complexion="Ruddy",
        eye_color="Brown",
        hair_color="Brown",
        other_physical_characteristics="Appendectomy scar",
    )
    rec = WwiiDraftCardRecord(
        source_id=valid_source_id,
        source_urn=valid_draft_urn,
        record_category=SourceRecordCategory.MILITARY,
        description="WWII First Wave Registration Card",
        repository_id=valid_repo_id,
        audit=valid_audit,
        draft_record_id=DraftRecordID("DRF-000002"),
        registrant_id=IndividualID("IND-000001"),
        registrant_name_raw="Glenn Lehman",
        draft_year=HistoricalYear(1940),
        board_jurisdiction_raw="Merrimack County Board 1",
        card_tier=DraftCardTier.OTHER,
        draft_wave=WwiiDraftWave.FIRST,
        serial_number="2145",
        order_number="104",
        contact_person_name_raw="Mary Lehman",
        contact_person_relationship="Wife",
        contact_person_id=contact_id,
        physical_metrics=metrics,
    )
    assert rec.serial_number == "2145"
    assert rec.contact_person_id == contact_id
    assert rec.physical_metrics is not None
    assert rec.physical_metrics.height_inches == 70
    assert rec.physical_metrics.weight_lbs == 165


# ==============================================================================
# GROUP 3: BOUNDARY & VALIDATION REJECTIONS
# ==============================================================================


@pytest.mark.unit
@pytest.mark.regression
def test_wwii_draft_card_invalid_year_fails(
    valid_source_id: SourceID,
    valid_draft_urn: MilitaryDraftUrn,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify ModelFormatError raised if draft_year outside 1940-1946."""
    with pytest.raises(
        ModelFormatError, match="draft_year must be between 1940 and 1946"
    ):
        WwiiDraftCardRecord(
            source_id=valid_source_id,
            source_urn=valid_draft_urn,
            record_category=SourceRecordCategory.MILITARY,
            description="Out of period year",
            repository_id=valid_repo_id,
            audit=valid_audit,
            draft_record_id=DraftRecordID("DRF-000001"),
            registrant_id=IndividualID("IND-000001"),
            registrant_name_raw="Glenn Lehman",
            draft_year=HistoricalYear(1917),
            board_jurisdiction_raw="Merrimack County Board 1",
            card_tier=DraftCardTier.OTHER,
            draft_wave=WwiiDraftWave.FIRST,
        )


@pytest.mark.unit
@pytest.mark.regression
def test_wwii_draft_card_tier_mismatch_fails(
    valid_source_id: SourceID,
    valid_draft_urn: MilitaryDraftUrn,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify ModelFormatError raised when FOURTH_OLD_MANS wave lacks WWII_FOURTH tier."""
    with pytest.raises(ModelFormatError, match="must specify card_tier WWII_FOURTH"):
        WwiiDraftCardRecord(
            source_id=valid_source_id,
            source_urn=valid_draft_urn,
            record_category=SourceRecordCategory.MILITARY,
            description="Tier mismatch",
            repository_id=valid_repo_id,
            audit=valid_audit,
            draft_record_id=DraftRecordID("DRF-000001"),
            registrant_id=IndividualID("IND-000001"),
            registrant_name_raw="Glenn Lehman",
            draft_year=HistoricalYear(1942),
            board_jurisdiction_raw="Merrimack County Board 1",
            card_tier=DraftCardTier.OTHER,
            draft_wave=WwiiDraftWave.FOURTH_OLD_MANS,
        )
