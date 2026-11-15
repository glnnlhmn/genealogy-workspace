"""Path: tests/test_gda/test_model/test_source/test_military/casualty/test_pow_record.py

Atomized behavioral test suite for PrisonerOfWarRecord domain entity.

Operational Role:
    Verifies POW capture records, detaining powers, prison camp facilities,
    repatriation/escape chronological bounds, and in-captivity fatalities.
"""

from __future__ import annotations

import pytest

from gda.core.enums.sources import SourceRecordCategory
from gda.core.errors import ModelFormatError
from gda.model.atom.id import IndividualID, LocationID, RepositoryID, SourceID
from gda.model.atom.urn import SourceURN
from gda.model.atom.year import HistoricalYear
from gda.model.base.audit import AuditStamp
from gda.model.source.military.casualty import (
    CasualtyCategory,
    PowCampType,
    PrisonerOfWarRecord,
)
from gda.model.source.military.service import MilitaryBranch

__version__ = "1.0.0+build.2"


@pytest.mark.unit
@pytest.mark.smoke
def test_pow_record_smoke_valid_initialization(
    valid_source_id: SourceID,
    valid_casualty_urn: SourceURN,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify minimal valid instantiation of PrisonerOfWarRecord."""
    rec = PrisonerOfWarRecord(
        source_id=valid_source_id,
        source_urn=valid_casualty_urn,
        record_category=SourceRecordCategory.MILITARY,
        description="POW interned in Germany",
        repository_id=valid_repo_id,
        audit=valid_audit,
        servicemember_id=IndividualID("IND-000001"),
        servicemember_name_raw="Glenn D. Lehman",
        branch=MilitaryBranch.AIR_FORCE,
        casualty_category=CasualtyCategory.PRISONER_OF_WAR,
        casualty_year=HistoricalYear(1944),
        unit_designation_raw="8th Air Force, 100th Bomb Group",
        rank_raw="Lieutenant",
        camp_type=PowCampType.OFFICER_CAMP,
        camp_name_raw="  Stalag Luft III  ",
        detaining_power_raw="  Germany  ",
        capture_year=HistoricalYear(1944),
    )
    assert rec.casualty_category == CasualtyCategory.PRISONER_OF_WAR
    assert rec.camp_type == PowCampType.OFFICER_CAMP
    assert rec.camp_name_raw == "Stalag Luft III"
    assert rec.detaining_power_raw == "Germany"
    assert rec.capture_year == HistoricalYear(1944)
    assert rec.died_in_captivity is False
    assert rec.release_or_repatriation_year is None


@pytest.mark.unit
def test_pow_record_repatriation_and_location(
    valid_source_id: SourceID,
    valid_casualty_urn: SourceURN,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify PrisonerOfWarRecord preserves repatriation year and camp location ID."""
    loc_id = LocationID("LOC-000105")
    rec = PrisonerOfWarRecord(
        source_id=valid_source_id,
        source_urn=valid_casualty_urn,
        record_category=SourceRecordCategory.MILITARY,
        description="Repatriated POW record",
        repository_id=valid_repo_id,
        audit=valid_audit,
        servicemember_id=IndividualID("IND-000001"),
        servicemember_name_raw="Glenn Lehman",
        branch=MilitaryBranch.AIR_FORCE,
        casualty_category=CasualtyCategory.PRISONER_OF_WAR,
        casualty_year=HistoricalYear(1943),
        unit_designation_raw="306th Bomb Group",
        rank_raw="Staff Sergeant",
        camp_type=PowCampType.ENLISTED_CAMP,
        camp_name_raw="Stalag Luft IV",
        detaining_power_raw="Germany",
        capture_year=HistoricalYear(1943),
        release_or_repatriation_year=HistoricalYear(1945),
        camp_location_id=loc_id,
    )
    assert rec.release_or_repatriation_year == HistoricalYear(1945)
    assert rec.camp_location_id == loc_id


@pytest.mark.unit
def test_pow_record_died_in_captivity(
    valid_source_id: SourceID,
    valid_casualty_urn: SourceURN,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify PrisonerOfWarRecord flags in-captivity deaths."""
    rec = PrisonerOfWarRecord(
        source_id=valid_source_id,
        source_urn=valid_casualty_urn,
        record_category=SourceRecordCategory.MILITARY,
        description="Died in Andersonville",
        repository_id=valid_repo_id,
        audit=valid_audit,
        servicemember_id=IndividualID("IND-000001"),
        servicemember_name_raw="Glenn Lehman",
        branch=MilitaryBranch.ARMY,
        casualty_category=CasualtyCategory.PRISONER_OF_WAR,
        casualty_year=HistoricalYear(1864),
        unit_designation_raw="Co. D, 16th Connecticut Infantry",
        rank_raw="Private",
        camp_type=PowCampType.CIVIL_WAR_STOCKADE,
        camp_name_raw="Camp Sumter (Andersonville)",
        detaining_power_raw="Confederate States of America",
        capture_year=HistoricalYear(1864),
        died_in_captivity=True,
    )
    assert rec.died_in_captivity is True


@pytest.mark.unit
@pytest.mark.regression
def test_pow_record_invalid_category_fails(
    valid_source_id: SourceID,
    valid_casualty_urn: SourceURN,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify ModelFormatError raised if casualty_category is not PRISONER_OF_WAR."""
    with pytest.raises(ModelFormatError, match="requires casualty_category 'PRISONER_OF_WAR'"):
        PrisonerOfWarRecord(
            source_id=valid_source_id,
            source_urn=valid_casualty_urn,
            record_category=SourceRecordCategory.MILITARY,
            description="WIA filed under POW",
            repository_id=valid_repo_id,
            audit=valid_audit,
            servicemember_id=IndividualID("IND-000001"),
            servicemember_name_raw="Glenn Lehman",
            branch=MilitaryBranch.ARMY,
            casualty_category=CasualtyCategory.WOUNDED_IN_ACTION,
            casualty_year=HistoricalYear(1944),
            unit_designation_raw="Co. A",
            rank_raw="Private",
            camp_type=PowCampType.ENLISTED_CAMP,
            camp_name_raw="Stalag II-B",
            detaining_power_raw="Germany",
            capture_year=HistoricalYear(1944),
        )


@pytest.mark.unit
@pytest.mark.regression
def test_pow_record_repatriation_precedes_capture_fails(
    valid_source_id: SourceID,
    valid_casualty_urn: SourceURN,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify ModelFormatError raised if release precedes capture_year."""
    with pytest.raises(ModelFormatError, match="cannot precede capture_year"):
        PrisonerOfWarRecord(
            source_id=valid_source_id,
            source_urn=valid_casualty_urn,
            record_category=SourceRecordCategory.MILITARY,
            description="Inverted repatriation",
            repository_id=valid_repo_id,
            audit=valid_audit,
            servicemember_id=IndividualID("IND-000001"),
            servicemember_name_raw="Glenn Lehman",
            branch=MilitaryBranch.ARMY,
            casualty_category=CasualtyCategory.PRISONER_OF_WAR,
            casualty_year=HistoricalYear(1944),
            unit_designation_raw="Co. A",
            rank_raw="Private",
            camp_type=PowCampType.ENLISTED_CAMP,
            camp_name_raw="Stalag II-B",
            detaining_power_raw="Germany",
            capture_year=HistoricalYear(1944),
            release_or_repatriation_year=HistoricalYear(1942),
        )


@pytest.mark.unit
@pytest.mark.regression
def test_pow_record_empty_strings_fail(
    valid_source_id: SourceID,
    valid_casualty_urn: SourceURN,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify ModelFormatError raised if camp_name_raw or detaining_power_raw is whitespace."""
    with pytest.raises(ModelFormatError, match="camp_name_raw.*cannot be empty"):
        PrisonerOfWarRecord(
            source_id=valid_source_id,
            source_urn=valid_casualty_urn,
            record_category=SourceRecordCategory.MILITARY,
            description="Empty camp",
            repository_id=valid_repo_id,
            audit=valid_audit,
            servicemember_id=IndividualID("IND-000001"),
            servicemember_name_raw="Glenn Lehman",
            branch=MilitaryBranch.ARMY,
            casualty_category=CasualtyCategory.PRISONER_OF_WAR,
            casualty_year=HistoricalYear(1944),
            unit_designation_raw="Co. A",
            rank_raw="Private",
            camp_type=PowCampType.ENLISTED_CAMP,
            camp_name_raw="   ",
            detaining_power_raw="Germany",
            capture_year=HistoricalYear(1944),
        )

    with pytest.raises(ModelFormatError, match="detaining_power_raw.*cannot be empty"):
        PrisonerOfWarRecord(
            source_id=valid_source_id,
            source_urn=valid_casualty_urn,
            record_category=SourceRecordCategory.MILITARY,
            description="Empty power",
            repository_id=valid_repo_id,
            audit=valid_audit,
            servicemember_id=IndividualID("IND-000001"),
            servicemember_name_raw="Glenn Lehman",
            branch=MilitaryBranch.ARMY,
            casualty_category=CasualtyCategory.PRISONER_OF_WAR,
            casualty_year=HistoricalYear(1944),
            unit_designation_raw="Co. A",
            rank_raw="Private",
            camp_type=PowCampType.ENLISTED_CAMP,
            camp_name_raw="Stalag II-B",
            detaining_power_raw="   ",
            capture_year=HistoricalYear(1944),
        )
