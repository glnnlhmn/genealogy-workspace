"""Path: tests/test_gda/test_model/test_military/casualty/test_combat_casualty.py

Atomized behavioral test suite for CombatCasualtyRecord domain entity.

Operational Role:
    Verifies combat engagement casualties (KIA, WIA, DOW, MIA), causes,
    field medical evacuations, string hygiene, and died-of-wounds chronological invariants.

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
from gda.model.atom.id import IndividualID, LocationID, RepositoryID, SourceID
from gda.model.atom.urn import SourceURN
from gda.model.base.audit import AuditStamp
from gda.model.military.casualty import CasualtyCategory, CombatCasualtyRecord
from gda.model.military.service import MilitaryBranch

__version__ = "1.0.0+build.2"


# ==============================================================================
# FIXTURES
# ==============================================================================


@pytest.fixture
def valid_audit() -> AuditStamp:
    """Return synthetic in-memory AuditStamp."""
    timestamp = IsoTimestamp("2026-01-01T00:00:00Z")
    return AuditStamp(created_at=timestamp, updated_at=timestamp)


@pytest.fixture
def valid_casualty_urn() -> SourceURN:
    """Return synthetic SourceURN."""
    return SourceURN("URN:SRC:1863:NH_ADJ_GEN:CAS_REC_51")


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
def test_combat_casualty_smoke_valid_initialization(
    valid_source_id: SourceID,
    valid_casualty_urn: SourceURN,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify minimal valid instantiation of CombatCasualtyRecord."""
    rec = CombatCasualtyRecord(
        source_id=valid_source_id,
        source_urn=valid_casualty_urn,
        record_category=SourceRecordCategory.MILITARY,
        description="Civil War battle casualty record",
        repository_id=valid_repo_id,
        audit=valid_audit,
        servicemember_id=IndividualID("IND-000001"),
        servicemember_name_raw="Glenn D. Lehman",
        branch=MilitaryBranch.ARMY,
        casualty_category=CasualtyCategory.KILLED_IN_ACTION,
        casualty_year=HistoricalYear(1863),
        unit_designation_raw="Company B, 2nd NH Volunteer Infantry",
        rank_raw="Private",
        engagement_name_raw="Battle of Gettysburg",
        cause_of_casualty_raw="Gunshot wound to chest",
    )
    assert rec.casualty_category == CasualtyCategory.KILLED_IN_ACTION
    assert rec.engagement_name_raw == "Battle of Gettysburg"
    assert rec.cause_of_casualty_raw == "Gunshot wound to chest"
    assert rec.died_of_wounds_year is None


# ==============================================================================
# GROUP 2: DIED OF WOUNDS, EVACUATIONS & STRING NORMALIZATION
# ==============================================================================


@pytest.mark.unit
def test_combat_casualty_died_of_wounds_and_aid_station(
    valid_source_id: SourceID,
    valid_casualty_urn: SourceURN,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify CombatCasualtyRecord populates DOW years and medical stations."""
    loc_id = LocationID("LOC-000099")
    rec = CombatCasualtyRecord(
        source_id=valid_source_id,
        source_urn=valid_casualty_urn,
        record_category=SourceRecordCategory.MILITARY,
        description="WIA leading to DOW report",
        repository_id=valid_repo_id,
        audit=valid_audit,
        servicemember_id=IndividualID("IND-000001"),
        servicemember_name_raw="Glenn Lehman",
        branch=MilitaryBranch.ARMY,
        casualty_category=CasualtyCategory.DIED_OF_WOUNDS,
        casualty_year=HistoricalYear(1864),
        unit_designation_raw="Company B, 2nd NH Infantry",
        rank_raw="Corporal",
        engagement_name_raw="Battle of Cold Harbor",
        cause_of_casualty_raw="Shrapnel shell fragments",
        aid_station_raw="18th Army Corps Field Hospital",
        died_of_wounds_year=HistoricalYear(1864),
        evacuation_location_id=loc_id,
    )
    assert rec.casualty_category == CasualtyCategory.DIED_OF_WOUNDS
    assert rec.died_of_wounds_year == HistoricalYear(1864)
    assert rec.aid_station_raw == "18th Army Corps Field Hospital"
    assert rec.evacuation_location_id == loc_id


@pytest.mark.unit
def test_combat_casualty_engagement_name_whitespace_stripped(
    valid_source_id: SourceID,
    valid_casualty_urn: SourceURN,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify engagement_name_raw is trimmed of whitespace and safely assigned."""
    rec = CombatCasualtyRecord(
        source_id=valid_source_id,
        source_urn=valid_casualty_urn,
        record_category=SourceRecordCategory.MILITARY,
        description="Whitespace engagement test",
        repository_id=valid_repo_id,
        audit=valid_audit,
        servicemember_id=IndividualID("IND-000001"),
        servicemember_name_raw="Glenn Lehman",
        branch=MilitaryBranch.ARMY,
        casualty_category=CasualtyCategory.WOUNDED_IN_ACTION,
        casualty_year=HistoricalYear(1862),
        unit_designation_raw="Company A",
        rank_raw="Private",
        engagement_name_raw="  Battle of Antietam  ",
    )
    assert rec.engagement_name_raw == "Battle of Antietam"


@pytest.mark.unit
def test_combat_casualty_none_optional_engagement(
    valid_source_id: SourceID,
    valid_casualty_urn: SourceURN,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify CombatCasualtyRecord allows None for engagement_name_raw."""
    rec = CombatCasualtyRecord(
        source_id=valid_source_id,
        source_urn=valid_casualty_urn,
        record_category=SourceRecordCategory.MILITARY,
        description="No engagement test",
        repository_id=valid_repo_id,
        audit=valid_audit,
        servicemember_id=IndividualID("IND-000001"),
        servicemember_name_raw="Glenn Lehman",
        branch=MilitaryBranch.ARMY,
        casualty_category=CasualtyCategory.DIED_OF_DISEASE,
        casualty_year=HistoricalYear(1863),
        unit_designation_raw="Company A",
        rank_raw="Private",
        engagement_name_raw=None,
    )
    assert rec.engagement_name_raw is None


# ==============================================================================
# GROUP 3: BOUNDARY & VALIDATION REJECTIONS
# ==============================================================================


@pytest.mark.unit
@pytest.mark.regression
def test_combat_casualty_non_combat_category_fails(
    valid_source_id: SourceID,
    valid_casualty_urn: SourceURN,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify ModelFormatError raised if casualty_category is not a combat type."""
    with pytest.raises(ModelFormatError, match="requires combat casualty_category"):
        CombatCasualtyRecord(
            source_id=valid_source_id,
            source_urn=valid_casualty_urn,
            record_category=SourceRecordCategory.MILITARY,
            description="POW under combat class",
            repository_id=valid_repo_id,
            audit=valid_audit,
            servicemember_id=IndividualID("IND-000001"),
            servicemember_name_raw="Glenn Lehman",
            branch=MilitaryBranch.ARMY,
            casualty_category=CasualtyCategory.PRISONER_OF_WAR,
            casualty_year=HistoricalYear(1864),
            unit_designation_raw="Co. B",
            rank_raw="Private",
        )


@pytest.mark.unit
@pytest.mark.regression
def test_combat_casualty_dow_year_precedes_casualty_fails(
    valid_source_id: SourceID,
    valid_casualty_urn: SourceURN,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify ModelFormatError raised if died_of_wounds_year precedes casualty_year."""
    with pytest.raises(ModelFormatError, match="cannot precede casualty_year"):
        CombatCasualtyRecord(
            source_id=valid_source_id,
            source_urn=valid_casualty_urn,
            record_category=SourceRecordCategory.MILITARY,
            description="Inverted DOW dates",
            repository_id=valid_repo_id,
            audit=valid_audit,
            servicemember_id=IndividualID("IND-000001"),
            servicemember_name_raw="Glenn Lehman",
            branch=MilitaryBranch.ARMY,
            casualty_category=CasualtyCategory.DIED_OF_WOUNDS,
            casualty_year=HistoricalYear(1864),
            unit_designation_raw="Co. B",
            rank_raw="Private",
            died_of_wounds_year=HistoricalYear(1863),
        )


@pytest.mark.unit
@pytest.mark.regression
def test_combat_casualty_empty_engagement_fails(
    valid_source_id: SourceID,
    valid_casualty_urn: SourceURN,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify ModelFormatError raised if engagement_name_raw is whitespace."""
    with pytest.raises(ModelFormatError, match="engagement_name_raw.*cannot be empty"):
        CombatCasualtyRecord(
            source_id=valid_source_id,
            source_urn=valid_casualty_urn,
            record_category=SourceRecordCategory.MILITARY,
            description="Empty engagement name",
            repository_id=valid_repo_id,
            audit=valid_audit,
            servicemember_id=IndividualID("IND-000001"),
            servicemember_name_raw="Glenn Lehman",
            branch=MilitaryBranch.ARMY,
            casualty_category=CasualtyCategory.KILLED_IN_ACTION,
            casualty_year=HistoricalYear(1863),
            unit_designation_raw="Co. B",
            rank_raw="Private",
            engagement_name_raw="   ",
        )
