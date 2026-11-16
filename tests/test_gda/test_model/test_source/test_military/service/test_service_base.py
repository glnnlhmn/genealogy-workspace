"""Path: tests/test_gda/test_model/test_source/test_military/service/test_service_base.py

Atomized behavioral test suite for MilitaryServiceRecord domain entity.

Operational Role:
    Verifies service record instantiation invariants, chronological year consistency,
    branch/component assignments, and raw string boundaries with 100% coverage.
"""

from __future__ import annotations

import pytest

from gda.core.enums.sources import SourceRecordCategory
from gda.core.errors import ModelFormatError
from gda.model.atom.id import (
    IndividualID,
    LocationID,
    RepositoryID,
    ServiceRecordID,
    SourceID,
    TranscriptID,
)
from gda.model.atom.urn import SourceURN
from gda.model.atom.year import HistoricalYear
from gda.model.base.audit import AuditStamp
from gda.model.source.military.service.base import (
    MilitaryBranch,
    MilitaryServiceRecord,
    SeparationCharacter,
    ServiceComponent,
)

__version__ = "1.0.0+build.2"


# ==============================================================================
# FIXTURES
# ==============================================================================


# ==============================================================================
# GROUP 1: SMOKE & GOLDEN PATH
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_military_service_record_smoke_valid_initialization(
    valid_source_id: SourceID,
    valid_service_urn: SourceURN,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
    valid_service_record_id: ServiceRecordID,
) -> None:
    """Verify minimal valid instantiation of MilitaryServiceRecord golden path."""
    rec = MilitaryServiceRecord(
        source_id=valid_source_id,
        source_urn=valid_service_urn,
        record_category=SourceRecordCategory.MILITARY,
        description="Muster-out roll entry for Glenn Lehman",
        repository_id=valid_repo_id,
        audit=valid_audit,
        service_record_id=valid_service_record_id,
        veteran_id=IndividualID("IND-000001"),
        veteran_name_raw="  Glenn D. Lehman  ",
        branch=MilitaryBranch.ARMY,
        unit_designation_raw="  Co. E, 1st New Hampshire Heavy Artillery  ",
        rank_raw="  Corporal  ",
        enlistment_year=HistoricalYear(1864),
        separation_year=HistoricalYear(1865),
    )
    assert rec.service_record_id == valid_service_record_id
    assert rec.veteran_id == IndividualID("IND-000001")
    assert rec.veteran_name_raw == "Glenn D. Lehman"
    assert rec.unit_designation_raw == "Co. E, 1st New Hampshire Heavy Artillery"
    assert rec.rank_raw == "Corporal"
    assert rec.branch == MilitaryBranch.ARMY
    assert rec.service_component == ServiceComponent.REGULAR
    assert rec.separation_character == SeparationCharacter.HONORABLE
    assert rec.enlistment_location_id is None
    assert rec.transcript_id is None
    assert "Corporal" in str(rec)
    assert "1864-1865" in str(rec)
    assert "MilitaryServiceRecord(" in repr(rec)


# ==============================================================================
# GROUP 2: OPTIONAL ATTRIBUTES & CHRONOLOGICAL PATHS
# ==============================================================================


@pytest.mark.unit
def test_military_service_record_full_attributes(
    valid_source_id: SourceID,
    valid_service_urn: SourceURN,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify MilitaryServiceRecord populates optional locations, serials, and transcripts."""
    srv_id = ServiceRecordID("b2a646d3-9c61-4a70-8b14-c48c8b417c8b")
    loc_id = LocationID("LOC-000010")
    trn_id = TranscriptID("e1a646d3-9c61-4a70-8b14-c48c8b417c8f")
    rec = MilitaryServiceRecord(
        source_id=valid_source_id,
        source_urn=valid_service_urn,
        record_category=SourceRecordCategory.MILITARY,
        description="DD-214 Record of Separation",
        repository_id=valid_repo_id,
        audit=valid_audit,
        service_record_id=srv_id,
        veteran_id=IndividualID("IND-000001"),
        veteran_name_raw="Glenn Lehman",
        branch=MilitaryBranch.NAVY,
        service_component=ServiceComponent.RESERVE,
        unit_designation_raw="USS Missouri (BB-63)",
        rank_raw="Seaman 1st Class",
        service_number_raw="312-44-90",
        enlistment_year=HistoricalYear(1943),
        separation_year=HistoricalYear(1946),
        separation_character=SeparationCharacter.HONORABLE,
        enlistment_location_raw="Boston, MA",
        enlistment_location_id=loc_id,
        transcript_id=trn_id,
    )
    assert rec.service_record_id == srv_id
    assert rec.service_number_raw == "312-44-90"
    assert rec.enlistment_location_id == loc_id
    assert rec.transcript_id == trn_id


@pytest.mark.unit
def test_military_service_record_partial_years_and_same_year(
    valid_source_id: SourceID,
    valid_service_urn: SourceURN,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
    valid_service_record_id: ServiceRecordID,
) -> None:
    """Verify MilitaryServiceRecord accepts partial years and same-year discharge."""
    rec_enl = MilitaryServiceRecord(
        source_id=valid_source_id,
        source_urn=valid_service_urn,
        record_category=SourceRecordCategory.MILITARY,
        description="Enlistment entry",
        repository_id=valid_repo_id,
        audit=valid_audit,
        service_record_id=valid_service_record_id,
        veteran_id=IndividualID("IND-000001"),
        veteran_name_raw="Glenn Lehman",
        branch=MilitaryBranch.ARMY,
        unit_designation_raw="Co. A",
        rank_raw="Private",
        enlistment_year=HistoricalYear(1861),
    )
    assert rec_enl.enlistment_year == HistoricalYear(1861)
    assert rec_enl.separation_year is None
    assert "1861-?" in str(rec_enl)

    rec_sep = MilitaryServiceRecord(
        source_id=valid_source_id,
        source_urn=valid_service_urn,
        record_category=SourceRecordCategory.MILITARY,
        description="Discharge entry",
        repository_id=valid_repo_id,
        audit=valid_audit,
        service_record_id=valid_service_record_id,
        veteran_id=IndividualID("IND-000001"),
        veteran_name_raw="Glenn Lehman",
        branch=MilitaryBranch.ARMY,
        unit_designation_raw="Co. A",
        rank_raw="Private",
        separation_year=HistoricalYear(1865),
    )
    assert rec_sep.enlistment_year is None
    assert rec_sep.separation_year == HistoricalYear(1865)
    assert "?-1865" in str(rec_sep)

    rec_none = MilitaryServiceRecord(
        source_id=valid_source_id,
        source_urn=valid_service_urn,
        record_category=SourceRecordCategory.MILITARY,
        description="Undated record",
        repository_id=valid_repo_id,
        audit=valid_audit,
        service_record_id=valid_service_record_id,
        veteran_id=IndividualID("IND-000001"),
        veteran_name_raw="Glenn Lehman",
        branch=MilitaryBranch.ARMY,
        unit_designation_raw="Co. A",
        rank_raw="Private",
    )
    assert "?-?" in str(rec_none)

    rec_same = MilitaryServiceRecord(
        source_id=valid_source_id,
        source_urn=valid_service_urn,
        record_category=SourceRecordCategory.MILITARY,
        description="90-day enlistment",
        repository_id=valid_repo_id,
        audit=valid_audit,
        service_record_id=valid_service_record_id,
        veteran_id=IndividualID("IND-000001"),
        veteran_name_raw="Glenn Lehman",
        branch=MilitaryBranch.ARMY,
        unit_designation_raw="Co. A",
        rank_raw="Private",
        enlistment_year=HistoricalYear(1861),
        separation_year=HistoricalYear(1861),
    )
    assert rec_same.enlistment_year == rec_same.separation_year


# ==============================================================================
# GROUP 3: BOUNDARY & VALIDATION REJECTIONS
# ==============================================================================


@pytest.mark.unit
@pytest.mark.regression
def test_military_service_record_chronological_sequence_fails(
    valid_source_id: SourceID,
    valid_service_urn: SourceURN,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
    valid_service_record_id: ServiceRecordID,
) -> None:
    """Verify ModelFormatError raised if separation_year precedes enlistment_year."""
    with pytest.raises(ModelFormatError, match="cannot precede enlistment_year") as exc_info:
        MilitaryServiceRecord(
            source_id=valid_source_id,
            source_urn=valid_service_urn,
            record_category=SourceRecordCategory.MILITARY,
            description="Inverted dates",
            repository_id=valid_repo_id,
            audit=valid_audit,
            service_record_id=valid_service_record_id,
            veteran_id=IndividualID("IND-000001"),
            veteran_name_raw="Glenn Lehman",
            branch=MilitaryBranch.ARMY,
            unit_designation_raw="Co. A",
            rank_raw="Private",
            enlistment_year=HistoricalYear(1945),
            separation_year=HistoricalYear(1942),
        )
    assert exc_info.value.details == {"enlistment_year": 1945, "separation_year": 1942}


@pytest.mark.unit
@pytest.mark.regression
def test_military_service_record_validate_chronology_direct(
    valid_source_id: SourceID,
    valid_service_urn: SourceURN,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
    valid_service_record_id: ServiceRecordID,
) -> None:
    """Verify direct invocation of _validate_chronology correctly flags reversed years."""
    rec = MilitaryServiceRecord(
        source_id=valid_source_id,
        source_urn=valid_service_urn,
        record_category=SourceRecordCategory.MILITARY,
        description="Valid record",
        repository_id=valid_repo_id,
        audit=valid_audit,
        service_record_id=valid_service_record_id,
        veteran_id=IndividualID("IND-000001"),
        veteran_name_raw="Glenn Lehman",
        branch=MilitaryBranch.ARMY,
        unit_designation_raw="Co. A",
        rank_raw="Private",
        enlistment_year=HistoricalYear(1861),
        separation_year=HistoricalYear(1865),
    )
    rec._validate_chronology()

    object.__setattr__(rec, "separation_year", HistoricalYear(1860))
    with pytest.raises(ModelFormatError, match="cannot precede enlistment_year"):
        rec._validate_chronology()


@pytest.mark.unit
@pytest.mark.regression
def test_military_service_record_invalid_category_fails(
    valid_source_id: SourceID,
    valid_service_urn: SourceURN,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
    valid_service_record_id: ServiceRecordID,
) -> None:
    """Verify ModelFormatError raised if record_category is not MILITARY."""
    with pytest.raises(ModelFormatError, match="requires category 'MILITARY'"):
        MilitaryServiceRecord(
            source_id=valid_source_id,
            source_urn=valid_service_urn,
            record_category=SourceRecordCategory.CENSUS,
            description="Mismatched category",
            repository_id=valid_repo_id,
            audit=valid_audit,
            service_record_id=valid_service_record_id,
            veteran_id=IndividualID("IND-000001"),
            veteran_name_raw="Glenn Lehman",
            branch=MilitaryBranch.ARMY,
            unit_designation_raw="Co. A",
            rank_raw="Private",
        )


@pytest.mark.unit
@pytest.mark.regression
def test_military_service_record_empty_strings_fail(
    valid_source_id: SourceID,
    valid_service_urn: SourceURN,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
    valid_service_record_id: ServiceRecordID,
) -> None:
    """Verify ModelFormatError raised if raw required strings are whitespace."""
    with pytest.raises(ModelFormatError, match="veteran_name_raw.*cannot be empty"):
        MilitaryServiceRecord(
            source_id=valid_source_id,
            source_urn=valid_service_urn,
            record_category=SourceRecordCategory.MILITARY,
            description="Empty name",
            repository_id=valid_repo_id,
            audit=valid_audit,
            service_record_id=valid_service_record_id,
            veteran_id=IndividualID("IND-000001"),
            veteran_name_raw="   ",
            branch=MilitaryBranch.ARMY,
            unit_designation_raw="Co. A",
            rank_raw="Private",
        )

    with pytest.raises(ModelFormatError, match="unit_designation_raw.*cannot be empty"):
        MilitaryServiceRecord(
            source_id=valid_source_id,
            source_urn=valid_service_urn,
            record_category=SourceRecordCategory.MILITARY,
            description="Empty unit",
            repository_id=valid_repo_id,
            audit=valid_audit,
            service_record_id=valid_service_record_id,
            veteran_id=IndividualID("IND-000001"),
            veteran_name_raw="Glenn Lehman",
            branch=MilitaryBranch.ARMY,
            unit_designation_raw="   ",
            rank_raw="Private",
        )

    with pytest.raises(ModelFormatError, match="rank_raw.*cannot be empty"):
        MilitaryServiceRecord(
            source_id=valid_source_id,
            source_urn=valid_service_urn,
            record_category=SourceRecordCategory.MILITARY,
            description="Empty rank",
            repository_id=valid_repo_id,
            audit=valid_audit,
            service_record_id=valid_service_record_id,
            veteran_id=IndividualID("IND-000001"),
            veteran_name_raw="Glenn Lehman",
            branch=MilitaryBranch.ARMY,
            unit_designation_raw="Co. A",
            rank_raw="   ",
        )
