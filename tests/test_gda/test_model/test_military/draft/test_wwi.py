"""Path: tests/test_gda/test_model/test_military/draft/test_wwi.py

Atomized behavioral test suite for WwiDraftCardRecord domain entity.

Operational Role:
    Verifies WWI registration card invariants, wave/tier restrictions, physical
    description sub-entities, and draft year boundaries (1917-1918).

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
from gda.model.military.draft.wwi import (
    WwiCitizenshipStatus,
    WwiDraftCardRecord,
    WwiPhysicalDescription,
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
    """Return synthetic MilitaryDraftUrn for WWI."""
    return MilitaryDraftUrn("URN:DRAFT:1917:NH_MERRIMACK:CARD_001")


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
def test_wwi_draft_card_smoke_valid_initialization(
    valid_source_id: SourceID,
    valid_draft_urn: MilitaryDraftUrn,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify minimal valid instantiation of WwiDraftCardRecord golden path."""
    rec = WwiDraftCardRecord(
        source_id=valid_source_id,
        source_urn=valid_draft_urn,
        record_category=SourceRecordCategory.MILITARY,
        description="WWI First Wave Draft Card for Glenn Lehman",
        repository_id=valid_repo_id,
        audit=valid_audit,
        draft_record_id=DraftRecordID("DRF-000001"),
        registrant_id=IndividualID("IND-000001"),
        registrant_name_raw="Glenn D. Lehman",
        draft_year=HistoricalYear(1917),
        board_jurisdiction_raw="Merrimack County, NH - Local Board 1",
        card_tier=DraftCardTier.WWI_FIRST,
    )
    assert rec.card_tier == DraftCardTier.WWI_FIRST
    assert rec.draft_year == HistoricalYear(1917)
    assert rec.citizenship == WwiCitizenshipStatus.UNKNOWN
    assert rec.claim_exemption is False
    assert rec.physical_description is None
    assert "WWI_FIRST" in str(rec)


# ==============================================================================
# GROUP 2: DETAILED PHYSICAL DESCRIPTIONS & FIELD EXTRACTIONS
# ==============================================================================


@pytest.mark.unit
def test_wwi_draft_card_full_extractions(
    valid_source_id: SourceID,
    valid_draft_urn: MilitaryDraftUrn,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify WwiDraftCardRecord preserves granular WWI transcriptive fields."""
    phys = WwiPhysicalDescription(
        height_description="Tall",
        build_description="Slender",
        eye_color="Blue",
        hair_color="Brown",
        baldness=False,
        physical_disqualifications="Loss of index finger on left hand",
    )
    rec = WwiDraftCardRecord(
        source_id=valid_source_id,
        source_urn=valid_draft_urn,
        record_category=SourceRecordCategory.MILITARY,
        description="WWI Third Wave Registration",
        repository_id=valid_repo_id,
        audit=valid_audit,
        draft_record_id=DraftRecordID("DRF-000002"),
        registrant_id=IndividualID("IND-000002"),
        registrant_name_raw="Glenn Lehman",
        draft_year=HistoricalYear(1918),
        board_jurisdiction_raw="Merrimack County Board 1",
        card_tier=DraftCardTier.WWI_THIRD,
        citizenship=WwiCitizenshipStatus.NATIVE_BORN,
        occupation_verbatim="Machinist",
        employer_verbatim="Concord Foundry Co.",
        employer_location_raw="Concord, NH",
        nearest_relative_raw="Mary Lehman (Wife), Concord, NH",
        claim_exemption=True,
        exemption_grounds_raw="Dependent wife and child",
        physical_description=phys,
    )
    assert rec.occupation_verbatim == "Machinist"
    assert rec.claim_exemption is True
    assert rec.physical_description is not None
    assert rec.physical_description.eye_color == "Blue"
    assert rec.physical_description.height_description == "Tall"


# ==============================================================================
# GROUP 3: BOUNDARY & VALIDATION REJECTIONS
# ==============================================================================


@pytest.mark.unit
@pytest.mark.regression
def test_wwi_draft_card_invalid_tier_fails(
    valid_source_id: SourceID,
    valid_draft_urn: MilitaryDraftUrn,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify ModelFormatError raised if card_tier is not a valid WWI round."""
    with pytest.raises(ModelFormatError, match="requires card_tier in"):
        WwiDraftCardRecord(
            source_id=valid_source_id,
            source_urn=valid_draft_urn,
            record_category=SourceRecordCategory.MILITARY,
            description="Mismatched tier",
            repository_id=valid_repo_id,
            audit=valid_audit,
            draft_record_id=DraftRecordID("DRF-000001"),
            registrant_id=IndividualID("IND-000001"),
            registrant_name_raw="Glenn Lehman",
            draft_year=HistoricalYear(1917),
            board_jurisdiction_raw="Merrimack County Board 1",
            card_tier=DraftCardTier.WWII_FOURTH,
        )


@pytest.mark.unit
@pytest.mark.regression
def test_wwi_draft_card_invalid_year_fails(
    valid_source_id: SourceID,
    valid_draft_urn: MilitaryDraftUrn,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify ModelFormatError raised if draft_year is not 1917 or 1918."""
    with pytest.raises(ModelFormatError, match="draft_year must be 1917 or 1918"):
        WwiDraftCardRecord(
            source_id=valid_source_id,
            source_urn=valid_draft_urn,
            record_category=SourceRecordCategory.MILITARY,
            description="Invalid year for WWI",
            repository_id=valid_repo_id,
            audit=valid_audit,
            draft_record_id=DraftRecordID("DRF-000001"),
            registrant_id=IndividualID("IND-000001"),
            registrant_name_raw="Glenn Lehman",
            draft_year=HistoricalYear(1942),
            board_jurisdiction_raw="Merrimack County Board 1",
            card_tier=DraftCardTier.WWI_FIRST,
        )
