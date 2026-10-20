"""Path: tests/test_gda/test_model/test_military/draft/test_civil_war.py

Atomized behavioral test suite for CivilWarDraftRecord domain entity.

Operational Role:
    Verifies Civil War conscription enrollment invariants, substitution linkages,
    commutation flags, and 1862-1865 registration year boundaries.

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
from gda.model.military.draft.civil_war import (
    CivilWarConscriptionAllegiance,
    CivilWarDraftRecord,
    CivilWarEnrollmentClass,
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
    """Return synthetic MilitaryDraftUrn for Civil War enrollment."""
    return MilitaryDraftUrn("URN:DRAFT:1863:NH_DIST2:ROLL_001")


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
def test_civil_war_draft_smoke_valid_initialization(
    valid_source_id: SourceID,
    valid_draft_urn: MilitaryDraftUrn,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify minimal valid instantiation of CivilWarDraftRecord golden path."""
    rec = CivilWarDraftRecord(
        source_id=valid_source_id,
        source_urn=valid_draft_urn,
        record_category=SourceRecordCategory.MILITARY,
        description="1863 Civil War Enrollment Roll entry for Glenn Lehman",
        repository_id=valid_repo_id,
        audit=valid_audit,
        draft_record_id=DraftRecordID("DRF-000001"),
        registrant_id=IndividualID("IND-000001"),
        registrant_name_raw="Glenn Lehman",
        draft_year=HistoricalYear(1863),
        board_jurisdiction_raw="2nd Congressional District, New Hampshire",
        card_tier=DraftCardTier.OTHER,
    )
    assert rec.allegiance == CivilWarConscriptionAllegiance.UNION
    assert rec.enrollment_class == CivilWarEnrollmentClass.CLASS_1
    assert rec.commutation_paid is False
    assert rec.substitute_provided is False
    assert "Glenn Lehman" in str(rec)


# ==============================================================================
# GROUP 2: SUBSTITUTES & COMMUTATION CLAIMS
# ==============================================================================


@pytest.mark.unit
def test_civil_war_draft_substitute_linkage(
    valid_source_id: SourceID,
    valid_draft_urn: MilitaryDraftUrn,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify CivilWarDraftRecord preserves resolved and verbatim substitute data."""
    sub_id = IndividualID("IND-000002")
    rec = CivilWarDraftRecord(
        source_id=valid_source_id,
        source_urn=valid_draft_urn,
        record_category=SourceRecordCategory.MILITARY,
        description="Enrollment with hired substitute",
        repository_id=valid_repo_id,
        audit=valid_audit,
        draft_record_id=DraftRecordID("DRF-000001"),
        registrant_id=IndividualID("IND-000001"),
        registrant_name_raw="Glenn Lehman",
        draft_year=HistoricalYear(1863),
        board_jurisdiction_raw="2nd Congressional District, NH",
        card_tier=DraftCardTier.OTHER,
        substitute_provided=True,
        substitute_individual_id=sub_id,
        substitute_name_raw="John Doe",
        commutation_paid=False,
    )
    assert rec.substitute_provided is True
    assert rec.substitute_individual_id == sub_id
    assert rec.substitute_name_raw == "John Doe"


# ==============================================================================
# GROUP 3: BOUNDARY & VALIDATION REJECTIONS
# ==============================================================================


@pytest.mark.unit
@pytest.mark.regression
def test_civil_war_draft_invalid_year_fails(
    valid_source_id: SourceID,
    valid_draft_urn: MilitaryDraftUrn,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify ModelFormatError raised if draft_year outside 1862-1865 range."""
    with pytest.raises(
        ModelFormatError, match="draft_year must be between 1862 and 1865"
    ):
        CivilWarDraftRecord(
            source_id=valid_source_id,
            source_urn=valid_draft_urn,
            record_category=SourceRecordCategory.MILITARY,
            description="Out of period year",
            repository_id=valid_repo_id,
            audit=valid_audit,
            draft_record_id=DraftRecordID("DRF-000001"),
            registrant_id=IndividualID("IND-000001"),
            registrant_name_raw="Glenn Lehman",
            draft_year=HistoricalYear(1861),
            board_jurisdiction_raw="2nd District",
            card_tier=DraftCardTier.OTHER,
        )


@pytest.mark.unit
@pytest.mark.regression
def test_civil_war_draft_missing_substitute_details_fails(
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
        CivilWarDraftRecord(
            source_id=valid_source_id,
            source_urn=valid_draft_urn,
            record_category=SourceRecordCategory.MILITARY,
            description="Missing substitute identity",
            repository_id=valid_repo_id,
            audit=valid_audit,
            draft_record_id=DraftRecordID("DRF-000001"),
            registrant_id=IndividualID("IND-000001"),
            registrant_name_raw="Glenn Lehman",
            draft_year=HistoricalYear(1863),
            board_jurisdiction_raw="2nd District",
            card_tier=DraftCardTier.OTHER,
            substitute_provided=True,
            substitute_name_raw="   ",
        )
