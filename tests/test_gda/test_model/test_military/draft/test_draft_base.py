"""Path: tests/test_gda/test_model/test_military/draft/test_draft_base.py

Atomized behavioral test suite for MilitaryDraftRecord domain entity.

Operational Role:
    Verifies draft registration base record instantiation, field hygiene, classification
    integrity, URN constraints, and audit linkages against canonical base attributes.

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
    DraftRecordID,
    IndividualID,
    LocationID,
    RepositoryID,
    SourceID,
    TranscriptID,
)
from gda.model.atom.urn import MilitaryDraftUrn, SourceURN
from gda.model.base.audit import AuditStamp
from gda.model.military.draft.base import MilitaryDraftRecord

__version__ = "1.0.0+build.8"


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
    """Return synthetic MilitaryDraftUrn adhering to canonical syntax."""
    return MilitaryDraftUrn("URN:DRAFT:1917:SELECTIVE_SERVICE:0001")


@pytest.fixture
def valid_repo_id() -> RepositoryID:
    """Return synthetic RepositoryID."""
    return RepositoryID("REP-000001")


@pytest.fixture
def valid_source_id() -> SourceID:
    """Return synthetic SourceID."""
    return SourceID("c9a646d3-9c61-4a70-8b14-c48c8b417c8d")


@pytest.fixture
def valid_draft_record_id() -> DraftRecordID:
    """Return synthetic DraftRecordID conforming to AtomID prefix DRF."""
    return DraftRecordID("DRF-000001")


# ==============================================================================
# GROUP 1: SMOKE & GOLDEN PATH
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_military_draft_record_smoke_valid_initialization(
    valid_source_id: SourceID,
    valid_draft_urn: MilitaryDraftUrn,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
    valid_draft_record_id: DraftRecordID,
) -> None:
    """Verify minimal valid instantiation of MilitaryDraftRecord golden path."""
    rec = MilitaryDraftRecord(
        source_id=valid_source_id,
        source_urn=valid_draft_urn,
        record_category=SourceRecordCategory.MILITARY,
        description="Draft registration for Glenn Lehman",
        repository_id=valid_repo_id,
        audit=valid_audit,
        draft_record_id=valid_draft_record_id,
        registrant_id=IndividualID("IND-000001"),
        registrant_name_raw="Glenn D. Lehman",
        draft_year=HistoricalYear(1917),
        board_jurisdiction_raw="Local Board No. 1, Merrimack County, NH",
    )
    assert rec.draft_record_id == valid_draft_record_id
    assert rec.registrant_id == IndividualID("IND-000001")
    assert rec.registrant_name_raw == "Glenn D. Lehman"
    assert rec.draft_year == HistoricalYear(1917)
    assert rec.board_jurisdiction_raw == "Local Board No. 1, Merrimack County, NH"
    assert rec.board_location_id is None
    assert rec.transcript_id is None
    assert "Glenn D. Lehman" in str(rec)
    assert "1917" in str(rec)


# ==============================================================================
# GROUP 2: OPTIONAL LINKAGES & EXTENSIONS
# ==============================================================================


@pytest.mark.unit
def test_military_draft_record_full_attributes(
    valid_source_id: SourceID,
    valid_draft_urn: MilitaryDraftUrn,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
    valid_draft_record_id: DraftRecordID,
) -> None:
    """Verify MilitaryDraftRecord correctly preserves optional locations and transcripts."""
    loc_id = LocationID("LOC-000005")
    trn_id = TranscriptID("e1a646d3-9c61-4a70-8b14-c48c8b417c8f")
    rec = MilitaryDraftRecord(
        source_id=valid_source_id,
        source_urn=valid_draft_urn,
        record_category=SourceRecordCategory.MILITARY,
        description="Detailed draft card",
        repository_id=valid_repo_id,
        audit=valid_audit,
        draft_record_id=valid_draft_record_id,
        registrant_id=IndividualID("IND-000001"),
        registrant_name_raw="Glenn D. Lehman",
        draft_year=HistoricalYear(1942),
        board_jurisdiction_raw="Local Board No. 1, Merrimack County, NH",
        board_location_id=loc_id,
        transcript_id=trn_id,
    )
    assert rec.board_location_id == loc_id
    assert rec.transcript_id == trn_id


# ==============================================================================
# GROUP 3: BOUNDARY & ERROR CONDITIONS
# ==============================================================================


@pytest.mark.unit
@pytest.mark.regression
def test_military_draft_record_invalid_category_fails(
    valid_source_id: SourceID,
    valid_draft_urn: MilitaryDraftUrn,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
    valid_draft_record_id: DraftRecordID,
) -> None:
    """Verify ModelFormatError raised if record_category is not MILITARY."""
    with pytest.raises(ModelFormatError, match="requires category 'MILITARY'"):
        MilitaryDraftRecord(
            source_id=valid_source_id,
            source_urn=valid_draft_urn,
            record_category=SourceRecordCategory.CENSUS,
            description="Mismatched category",
            repository_id=valid_repo_id,
            audit=valid_audit,
            draft_record_id=valid_draft_record_id,
            registrant_id=IndividualID("IND-000001"),
            registrant_name_raw="Glenn D. Lehman",
            draft_year=HistoricalYear(1917),
            board_jurisdiction_raw="Local Board No. 1",
        )


@pytest.mark.unit
@pytest.mark.regression
def test_military_draft_record_invalid_urn_type_fails(
    valid_source_id: SourceID,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
    valid_draft_record_id: DraftRecordID,
) -> None:
    """Verify ModelFormatError raised when source_urn is not a MilitaryDraftUrn."""
    generic_urn = SourceURN("URN:SRC:1917:SELECTIVE_SERVICE:DRAFT_REG_1")
    with pytest.raises(ModelFormatError, match="must be a MilitaryDraftUrn"):
        MilitaryDraftRecord(
            source_id=valid_source_id,
            source_urn=generic_urn,  # type: ignore[arg-type]
            record_category=SourceRecordCategory.MILITARY,
            description="Invalid URN type",
            repository_id=valid_repo_id,
            audit=valid_audit,
            draft_record_id=valid_draft_record_id,
            registrant_id=IndividualID("IND-000001"),
            registrant_name_raw="Glenn D. Lehman",
            draft_year=HistoricalYear(1917),
            board_jurisdiction_raw="Local Board No. 1",
        )


@pytest.mark.unit
@pytest.mark.regression
def test_military_draft_record_empty_name_fails(
    valid_source_id: SourceID,
    valid_draft_urn: MilitaryDraftUrn,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
    valid_draft_record_id: DraftRecordID,
) -> None:
    """Verify ModelFormatError raised if registrant_name_raw is whitespace."""
    with pytest.raises(ModelFormatError, match="registrant_name_raw.*cannot be empty"):
        MilitaryDraftRecord(
            source_id=valid_source_id,
            source_urn=valid_draft_urn,
            record_category=SourceRecordCategory.MILITARY,
            description="Empty name test",
            repository_id=valid_repo_id,
            audit=valid_audit,
            draft_record_id=valid_draft_record_id,
            registrant_id=IndividualID("IND-000001"),
            registrant_name_raw="   ",
            draft_year=HistoricalYear(1917),
            board_jurisdiction_raw="Local Board No. 1",
        )


@pytest.mark.unit
@pytest.mark.regression
def test_military_draft_record_empty_jurisdiction_fails(
    valid_source_id: SourceID,
    valid_draft_urn: MilitaryDraftUrn,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
    valid_draft_record_id: DraftRecordID,
) -> None:
    """Verify ModelFormatError raised if board_jurisdiction_raw is whitespace."""
    with pytest.raises(
        ModelFormatError, match="board_jurisdiction_raw.*cannot be empty"
    ):
        MilitaryDraftRecord(
            source_id=valid_source_id,
            source_urn=valid_draft_urn,
            record_category=SourceRecordCategory.MILITARY,
            description="Empty jurisdiction test",
            repository_id=valid_repo_id,
            audit=valid_audit,
            draft_record_id=valid_draft_record_id,
            registrant_id=IndividualID("IND-000001"),
            registrant_name_raw="Glenn D. Lehman",
            draft_year=HistoricalYear(1917),
            board_jurisdiction_raw="   ",
        )
