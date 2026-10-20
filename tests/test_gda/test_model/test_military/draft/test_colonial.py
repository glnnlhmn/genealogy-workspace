"""Path: tests/test_gda/test_model/test_military/draft/test_colonial.py

Atomized behavioral test suite for ColonialMilitiaRecord domain entity.

Operational Role:
    Verifies colonial and Revolutionary War militia enrollment invariants, substitute
    provisions, militia classification tiers, and 1607-1815 registration boundaries.

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
from gda.model.military.draft.colonial import (
    ColonialMilitiaClass,
    ColonialMilitiaRecord,
    ColonialWarPeriod,
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
    """Return synthetic MilitaryDraftUrn for colonial muster roll."""
    return MilitaryDraftUrn("URN:DRAFT:1776:NH_CONCORD:ROLL_001")


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
def test_colonial_militia_smoke_valid_initialization(
    valid_source_id: SourceID,
    valid_draft_urn: MilitaryDraftUrn,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify minimal valid instantiation of ColonialMilitiaRecord golden path."""
    rec = ColonialMilitiaRecord(
        source_id=valid_source_id,
        source_urn=valid_draft_urn,
        record_category=SourceRecordCategory.MILITARY,
        description="1776 Trainband Muster Roll for Concord, NH",
        repository_id=valid_repo_id,
        audit=valid_audit,
        draft_record_id=DraftRecordID("DRF-000001"),
        registrant_id=IndividualID("IND-000001"),
        registrant_name_raw="Glenn Lehman",
        draft_year=HistoricalYear(1776),
        board_jurisdiction_raw="Town of Concord, Province of New Hampshire",
        card_tier=DraftCardTier.OTHER,
        colony_or_state_raw="Province of New Hampshire",
    )
    assert rec.conflict_period == ColonialWarPeriod.REVOLUTIONARY_WAR
    assert rec.militia_class == ColonialMilitiaClass.TRAINBAND
    assert rec.colony_or_state_raw == "Province of New Hampshire"
    assert rec.substitute_provided is False
    assert "Glenn Lehman" in str(rec)


# ==============================================================================
# GROUP 2: DETAILED REGIMENTAL DATA & SUBSTITUTES
# ==============================================================================


@pytest.mark.unit
def test_colonial_militia_substitute_and_unit_details(
    valid_source_id: SourceID,
    valid_draft_urn: MilitaryDraftUrn,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify ColonialMilitiaRecord handles unit hierarchy, equipment, and substitutes."""
    sub_id = IndividualID("IND-000002")
    rec = ColonialMilitiaRecord(
        source_id=valid_source_id,
        source_urn=valid_draft_urn,
        record_category=SourceRecordCategory.MILITARY,
        description="Revolutionary War Class Levy with Substitute",
        repository_id=valid_repo_id,
        audit=valid_audit,
        draft_record_id=DraftRecordID("DRF-000002"),
        registrant_id=IndividualID("IND-000001"),
        registrant_name_raw="Glenn Lehman",
        draft_year=HistoricalYear(1781),
        board_jurisdiction_raw="Merrimack County Committee of Safety",
        card_tier=DraftCardTier.OTHER,
        colony_or_state_raw="State of New Hampshire",
        conflict_period=ColonialWarPeriod.REVOLUTIONARY_WAR,
        militia_class=ColonialMilitiaClass.TOWN_CLASS,
        regiment_verbatim="Col. Stickney's 11th Regiment of Militia",
        company_officer_raw="Capt. Benjamin Emery",
        equipment_readiness_raw="Equipped with musket, bayonet, 24 cartridges",
        substitute_provided=True,
        substitute_individual_id=sub_id,
        substitute_name_raw="Ebenezer Virgin",
    )
    assert rec.regiment_verbatim == "Col. Stickney's 11th Regiment of Militia"
    assert rec.company_officer_raw == "Capt. Benjamin Emery"
    assert rec.substitute_individual_id == sub_id
    assert rec.substitute_name_raw == "Ebenezer Virgin"


# ==============================================================================
# GROUP 3: BOUNDARY & VALIDATION REJECTIONS
# ==============================================================================


@pytest.mark.unit
@pytest.mark.regression
def test_colonial_militia_invalid_year_fails(
    valid_source_id: SourceID,
    valid_draft_urn: MilitaryDraftUrn,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify ModelFormatError raised if draft_year outside 1607-1815."""
    with pytest.raises(
        ModelFormatError, match="draft_year must be between 1607 and 1815"
    ):
        ColonialMilitiaRecord(
            source_id=valid_source_id,
            source_urn=valid_draft_urn,
            record_category=SourceRecordCategory.MILITARY,
            description="Out of period year",
            repository_id=valid_repo_id,
            audit=valid_audit,
            draft_record_id=DraftRecordID("DRF-000001"),
            registrant_id=IndividualID("IND-000001"),
            registrant_name_raw="Glenn Lehman",
            draft_year=HistoricalYear(1863),
            board_jurisdiction_raw="Town of Concord",
            card_tier=DraftCardTier.OTHER,
            colony_or_state_raw="New Hampshire",
        )


@pytest.mark.unit
@pytest.mark.regression
def test_colonial_militia_empty_colony_fails(
    valid_source_id: SourceID,
    valid_draft_urn: MilitaryDraftUrn,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify ModelFormatError raised if colony_or_state_raw is empty or whitespace."""
    with pytest.raises(ModelFormatError, match="colony_or_state_raw.*cannot be empty"):
        ColonialMilitiaRecord(
            source_id=valid_source_id,
            source_urn=valid_draft_urn,
            record_category=SourceRecordCategory.MILITARY,
            description="Empty colony check",
            repository_id=valid_repo_id,
            audit=valid_audit,
            draft_record_id=DraftRecordID("DRF-000001"),
            registrant_id=IndividualID("IND-000001"),
            registrant_name_raw="Glenn Lehman",
            draft_year=HistoricalYear(1776),
            board_jurisdiction_raw="Town of Concord",
            card_tier=DraftCardTier.OTHER,
            colony_or_state_raw="   ",
        )


@pytest.mark.unit
@pytest.mark.regression
def test_colonial_militia_missing_substitute_details_fails(
    valid_source_id: SourceID,
    valid_draft_urn: MilitaryDraftUrn,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify ModelFormatError raised when substitute_provided is True without details."""
    with pytest.raises(
        ModelFormatError,
        match="requires substitute_name_raw or substitute_individual_id",
    ):
        ColonialMilitiaRecord(
            source_id=valid_source_id,
            source_urn=valid_draft_urn,
            record_category=SourceRecordCategory.MILITARY,
            description="Missing substitute identity",
            repository_id=valid_repo_id,
            audit=valid_audit,
            draft_record_id=DraftRecordID("DRF-000001"),
            registrant_id=IndividualID("IND-000001"),
            registrant_name_raw="Glenn Lehman",
            draft_year=HistoricalYear(1776),
            board_jurisdiction_raw="Town of Concord",
            card_tier=DraftCardTier.OTHER,
            colony_or_state_raw="Province of New Hampshire",
            substitute_provided=True,
            substitute_name_raw="   ",
        )
