"""Path: tests/test_gda/test_model/test_military/service/test_separation.py

Atomized behavioral test suite for SeparationDischargeRecord domain entity.

Operational Role:
    Verifies DD-214 and historical discharge certificate structures, mandatory
    separation years, SPN/SPD codes, foreign service metrics, and travel pay.

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
    ServiceRecordID,
    SourceID,
)
from gda.model.atom.urn import SourceURN
from gda.model.base.audit import AuditStamp
from gda.model.military.service.base import (
    MilitaryBranch,
    SeparationCharacter,
    ServiceComponent,
)
from gda.model.military.service.separation import (
    SeparationDischargeRecord,
    SeparationFormType,
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
def valid_service_urn() -> SourceURN:
    """Return synthetic SourceURN."""
    return SourceURN("URN:SRC:1953:DD214:REC_9021")


@pytest.fixture
def valid_repo_id() -> RepositoryID:
    """Return synthetic RepositoryID."""
    return RepositoryID("REP-000001")


@pytest.fixture
def valid_source_id() -> SourceID:
    """Return synthetic SourceID."""
    return SourceID("c9a646d3-9c61-4a70-8b14-c48c8b417c8d")


@pytest.fixture
def valid_service_record_id() -> ServiceRecordID:
    """Return synthetic ServiceRecordID."""
    return ServiceRecordID("a1a646d3-9c61-4a70-8b14-c48c8b417c8a")


# ==============================================================================
# GROUP 1: SMOKE & GOLDEN PATH
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_separation_discharge_smoke_valid_initialization(
    valid_source_id: SourceID,
    valid_service_urn: SourceURN,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
    valid_service_record_id: ServiceRecordID,
) -> None:
    """Verify minimal valid instantiation of SeparationDischargeRecord."""
    rec = SeparationDischargeRecord(
        source_id=valid_source_id,
        source_urn=valid_service_urn,
        record_category=SourceRecordCategory.MILITARY,
        description="DD Form 214 Certificate of Release",
        repository_id=valid_repo_id,
        audit=valid_audit,
        service_record_id=valid_service_record_id,
        veteran_id=IndividualID("IND-000001"),
        veteran_name_raw="Glenn D. Lehman",
        branch=MilitaryBranch.AIR_FORCE,
        service_component=ServiceComponent.REGULAR,
        unit_designation_raw="436th Military Airlift Wing",
        rank_raw="Staff Sergeant",
        enlistment_year=HistoricalYear(1970),
        separation_year=HistoricalYear(1974),
        separation_character=SeparationCharacter.HONORABLE,
        form_type=SeparationFormType.DD_214,
    )
    assert rec.form_type == SeparationFormType.DD_214
    assert rec.separation_year == HistoricalYear(1974)
    assert rec.separation_character == SeparationCharacter.HONORABLE
    assert rec.separation_code_raw is None
    assert "Staff Sergeant" in str(rec)


# ==============================================================================
# GROUP 2: CODES, STATIONS & FOREIGN SERVICE
# ==============================================================================


@pytest.mark.unit
def test_separation_discharge_full_attributes(
    valid_source_id: SourceID,
    valid_service_urn: SourceURN,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
    valid_service_record_id: ServiceRecordID,
) -> None:
    """Verify SeparationDischargeRecord populates codes, foreign duty, and location."""
    loc_id = LocationID("LOC-000055")
    rec = SeparationDischargeRecord(
        source_id=valid_source_id,
        source_urn=valid_service_urn,
        record_category=SourceRecordCategory.MILITARY,
        description="WWII Army Separation Record (WD AGO 53-55)",
        repository_id=valid_repo_id,
        audit=valid_audit,
        service_record_id=valid_service_record_id,
        veteran_id=IndividualID("IND-000001"),
        veteran_name_raw="Glenn Lehman",
        branch=MilitaryBranch.ARMY,
        service_component=ServiceComponent.REGULAR,
        unit_designation_raw="Company C, 16th Infantry Regiment, 1st Infantry Division",
        rank_raw="Technician 5th Grade",
        enlistment_year=HistoricalYear(1942),
        separation_year=HistoricalYear(1945),
        separation_character=SeparationCharacter.HONORABLE,
        form_type=SeparationFormType.WD_AGO_53_55,
        separation_reason_raw="Demobilization under RR1-1",
        separation_code_raw="CONV-DEMOB",
        reentry_code_raw="RE-1",
        foreign_service_months=28,
        separation_facility_raw="Fort Devens Separation Center, Massachusetts",
        separation_location_id=loc_id,
        decorations_raw="Bronze Star Medal, Purple Heart, European Theater Ribbon with 3 Stars",
        travel_allowance_paid_usd=18.50,
    )
    assert rec.form_type == SeparationFormType.WD_AGO_53_55
    assert rec.separation_reason_raw == "Demobilization under RR1-1"
    assert rec.separation_code_raw == "CONV-DEMOB"
    assert rec.reentry_code_raw == "RE-1"
    assert rec.foreign_service_months == 28
    assert rec.separation_location_id == loc_id
    assert rec.travel_allowance_paid_usd == 18.50


# ==============================================================================
# GROUP 3: BOUNDARY & VALIDATION REJECTIONS
# ==============================================================================


@pytest.mark.unit
@pytest.mark.regression
def test_separation_discharge_missing_separation_year_fails(
    valid_source_id: SourceID,
    valid_service_urn: SourceURN,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
    valid_service_record_id: ServiceRecordID,
) -> None:
    """Verify ModelFormatError raised if separation_year is omitted."""
    with pytest.raises(ModelFormatError, match="requires an explicit separation_year"):
        SeparationDischargeRecord(
            source_id=valid_source_id,
            source_urn=valid_service_urn,
            record_category=SourceRecordCategory.MILITARY,
            description="Missing discharge year",
            repository_id=valid_repo_id,
            audit=valid_audit,
            service_record_id=valid_service_record_id,
            veteran_id=IndividualID("IND-000001"),
            veteran_name_raw="Glenn Lehman",
            branch=MilitaryBranch.ARMY,
            unit_designation_raw="Co. A",
            rank_raw="Private",
            enlistment_year=HistoricalYear(1942),
            form_type=SeparationFormType.DD_214,
        )
