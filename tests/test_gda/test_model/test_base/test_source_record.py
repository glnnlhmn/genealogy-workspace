"""Path: tests/test_gda/test_model/test_base/test_source_record.py

Atomized behavioral test suite for SourceRecord composite entity.

Operational Role:
    Verifies instantiation invariants, repository link type safety, URN enforcement,
    associated people handling, media ID decoupling, and tombstone deprecation status.

Test Structure & Protocol:
    - Atomized tests: 1:1 behavioral contract verification.
    - Fully decorated: Pytest marker taxonomy (@pytest.mark.unit, @pytest.mark.smoke, @pytest.mark.regression).
    - Synthetic baselines: Pure in-memory fixtures with isolated basetemp execution.
"""

from __future__ import annotations

import pytest

from gda.core.errors import ModelFormatError
from gda.enums.core import AssociatedRole
from gda.enums.sources import SourceRecordCategory
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import IndividualID, MediaID, RepositoryID, SourceID
from gda.model.atom.urn import SourceURN
from gda.model.base.association import AssociatedIndividual
from gda.model.base.audit import AuditStamp
from gda.model.base.source_record import SourceRecord
from gda.model.base.tombstone import TombstoneRecord

__version__ = "1.0.0+build.6"


# ==============================================================================
# FIXTURES
# ==============================================================================


@pytest.fixture
def valid_audit() -> AuditStamp:
    """Return synthetic in-memory AuditStamp with required timestamps."""
    timestamp = IsoTimestamp("2026-01-01T00:00:00Z")
    return AuditStamp(
        created_at=timestamp,
        updated_at=timestamp,
    )


@pytest.fixture
def valid_source_id() -> SourceID:
    """Return synthetic SourceID."""
    return SourceID("c9a646d3-9c61-4a70-8b14-c48c8b417c8d")


@pytest.fixture
def valid_source_urn() -> SourceURN:
    """Return synthetic SourceURN."""
    return SourceURN("URN:SRC:1917:NH_MERRIMACK:DOC_000101")


@pytest.fixture
def valid_repo_id() -> RepositoryID:
    """Return synthetic RepositoryID."""
    return RepositoryID("REP-000001")


# ==============================================================================
# GROUP 1: SMOKE & GOLDEN PATH
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_source_record_smoke_valid_initialization(
    valid_source_id: SourceID,
    valid_source_urn: SourceURN,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify minimal valid instantiation of SourceRecord golden path."""
    rec = SourceRecord(
        source_id=valid_source_id,
        source_urn=valid_source_urn,
        record_category=SourceRecordCategory.MILITARY,
        description="WWI Draft Registration Card for Glenn Lehman",
        repository_id=valid_repo_id,
        audit=valid_audit,
    )
    assert rec.source_id == valid_source_id
    assert rec.source_urn == valid_source_urn
    assert rec.record_category == SourceRecordCategory.MILITARY
    assert rec.repository_id == valid_repo_id
    assert rec.media_ids == []
    assert rec.associated_people == []
    assert rec.tombstone is None
    assert rec.is_deprecated is False
    assert rec.media_count == 0
    assert rec.participant_count == 0
    assert "MILITARY" in str(rec)


# ==============================================================================
# GROUP 2: OPTIONAL ATTRIBUTES & COMPOSITE LINKAGES
# ==============================================================================


@pytest.mark.unit
def test_source_record_with_media_and_associations(
    valid_source_id: SourceID,
    valid_source_urn: SourceURN,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify SourceRecord populates media_ids and associated_people correctly."""
    media_id = MediaID("d0a646d3-9c61-4a70-8b14-c48c8b417c8e")
    assoc = AssociatedIndividual(
        role=AssociatedRole.INFORMANT,
        individual_id=IndividualID("IND-000001"),
        name_raw="Mary Lehman",
    )
    rec = SourceRecord(
        source_id=valid_source_id,
        source_urn=valid_source_urn,
        record_category=SourceRecordCategory.MILITARY,
        description="Draft Registration Card",
        repository_id=valid_repo_id,
        audit=valid_audit,
        media_ids=[media_id],
        associated_people=[assoc],
    )
    assert rec.media_count == 1
    assert rec.participant_count == 1
    assert rec.media_ids[0] == media_id
    assert rec.associated_people[0].name_raw == "Mary Lehman"


@pytest.mark.unit
def test_source_record_tombstone_reflects_deprecation(
    valid_source_id: SourceID,
    valid_source_urn: SourceURN,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify is_deprecated accurately surfaces TombstoneRecord state."""
    tombstone = TombstoneRecord[SourceID](
        is_deprecated=True,
        deprecated_at=IsoTimestamp("2026-06-01T12:00:00Z"),
        superseded_by=valid_source_id,
    )
    rec = SourceRecord(
        source_id=valid_source_id,
        source_urn=valid_source_urn,
        record_category=SourceRecordCategory.MILITARY,
        description="Superseded Record",
        repository_id=valid_repo_id,
        audit=valid_audit,
        tombstone=tombstone,
    )
    assert rec.is_deprecated is True


# ==============================================================================
# GROUP 3: BOUNDARY & VALIDATION REJECTIONS
# ==============================================================================


@pytest.mark.unit
@pytest.mark.regression
def test_source_record_empty_description_fails(
    valid_source_id: SourceID,
    valid_source_urn: SourceURN,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify ModelFormatError raised when description is empty or whitespace."""
    with pytest.raises(ModelFormatError, match="cannot be empty or whitespace-only"):
        SourceRecord(
            source_id=valid_source_id,
            source_urn=valid_source_urn,
            record_category=SourceRecordCategory.MILITARY,
            description="   ",
            repository_id=valid_repo_id,
            audit=valid_audit,
        )


@pytest.mark.unit
@pytest.mark.regression
def test_source_record_invalid_source_urn_type_fails(
    valid_source_id: SourceID,
    valid_source_urn: SourceURN,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify ModelFormatError raised when source_urn bypasses instance type check."""
    rec = SourceRecord(
        source_id=valid_source_id,
        source_urn=valid_source_urn,
        record_category=SourceRecordCategory.MILITARY,
        description="Valid description",
        repository_id=valid_repo_id,
        audit=valid_audit,
    )
    object.__setattr__(rec, "source_urn", "not-an-archival-urn")
    with pytest.raises(ModelFormatError, match="must be an instance of ArchivalURN"):
        rec.__post_init__()


@pytest.mark.unit
@pytest.mark.regression
def test_source_record_invalid_repository_id_type_fails(
    valid_source_id: SourceID,
    valid_source_urn: SourceURN,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify ModelFormatError raised when repository_id bypasses instance type check."""
    rec = SourceRecord(
        source_id=valid_source_id,
        source_urn=valid_source_urn,
        record_category=SourceRecordCategory.MILITARY,
        description="Valid description",
        repository_id=valid_repo_id,
        audit=valid_audit,
    )
    object.__setattr__(rec, "repository_id", "not-a-repo-id")
    with pytest.raises(ModelFormatError, match="must be an instance of RepositoryID"):
        rec.__post_init__()


@pytest.mark.unit
@pytest.mark.regression
def test_source_record_introspection(
    valid_source_id: SourceID,
    valid_source_urn: SourceURN,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify IntrospectableMixin .help() executes cleanly on SourceRecord."""
    rec = SourceRecord(
        source_id=valid_source_id,
        source_urn=valid_source_urn,
        record_category=SourceRecordCategory.MILITARY,
        description="Draft Card Inspection",
        repository_id=valid_repo_id,
        audit=valid_audit,
    )
    rec.help()
    captured = capsys.readouterr()
    assert "SourceRecord" in captured.out or rec.__doc__ is not None
