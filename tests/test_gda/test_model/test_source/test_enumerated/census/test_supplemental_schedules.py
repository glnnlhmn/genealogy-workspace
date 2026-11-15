"""Path: tests/test_gda/test_model/test_source/test_enumerated/census/test_supplemental_schedules.py

Atomized behavioral test suite for non-population federal census schedules.

Operational Role:
    Verifies Mortality, Agricultural, Manufacturing, Slave, and 1890 Veterans
    census schedule records, entry constraints, and statutory year invariants.
"""

from __future__ import annotations

import pytest

from gda.core.enums.sources import SourceRecordCategory
from gda.core.errors import ModelFormatError
from gda.model.atom.id import IndividualID, RepositoryID, SourceID
from gda.model.atom.urn import CensusUrn
from gda.model.atom.year import HistoricalYear
from gda.model.base.audit import AuditStamp
from gda.model.source.enumerated.census.supplemental import (
    AgriculturalScheduleEntry,
    AgriculturalScheduleRecord,
    ManufacturingScheduleEntry,
    ManufacturingScheduleRecord,
    MortalityScheduleEntry,
    MortalityScheduleRecord,
    SlaveScheduleEntry,
    SlaveScheduleRecord,
    Veterans1890Entry,
    Veterans1890ScheduleRecord,
)

__version__ = "1.0.0+build.2"


@pytest.mark.unit
@pytest.mark.smoke
def test_mortality_schedule_valid_and_year_guard(
    valid_source_id: SourceID,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify MortalityScheduleRecord valid entries and 1850-1885 year bounds."""
    entry = MortalityScheduleEntry(
        entry_urn=CensusUrn("URN:CENSUS:1880:NH_MERRIMACK:MORT_P02_L07"),
        line_number=7,
        name_verbatim="Samuel Lehman",
        age_raw="68",
        sex_raw="M",
        month_of_death_raw="Feb",
        cause_of_death_raw="Pneumonia",
        attending_physician_raw="Dr. H. M. French",
    )
    sched = MortalityScheduleRecord(
        source_id=valid_source_id,
        source_urn=CensusUrn("URN:CENSUS:1880:NH_MERRIMACK:MORT_P02"),
        record_category=SourceRecordCategory.CENSUS,
        description="1880 Mortality Schedule",
        repository_id=valid_repo_id,
        audit=valid_audit,
        enumeration_year=HistoricalYear(1880),
        jurisdiction_raw="Concord, NH",
        state="New Hampshire",
        county="Merrimack",
        entries=(entry,),
    )
    assert sched.entries[0].cause_of_death_raw == "Pneumonia"

    with pytest.raises(ModelFormatError, match="MortalityScheduleRecord enumeration_year"):
        MortalityScheduleRecord(
            source_id=valid_source_id,
            source_urn=CensusUrn("URN:CENSUS:1900:NH_MERRIMACK:MORT_P02"),
            record_category=SourceRecordCategory.CENSUS,
            description="Invalid 1900 year",
            repository_id=valid_repo_id,
            audit=valid_audit,
            enumeration_year=HistoricalYear(1900),
            jurisdiction_raw="Concord, NH",
            state="New Hampshire",
            county="Merrimack",
            entries=(entry,),
        )


@pytest.mark.unit
def test_agricultural_schedule_valid_and_year_guard(
    valid_source_id: SourceID,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify AgriculturalScheduleRecord valid entries and 1850-1880 year bounds."""
    entry = AgriculturalScheduleEntry(
        entry_urn=CensusUrn("URN:CENSUS:1870:NH_MERRIMACK:AGRI_P05_L02"),
        line_number=2,
        name_verbatim="Glenn Lehman",
        tenure_raw="Owner",
        improved_acres=85,
        unimproved_acres=40,
        farm_cash_value_usd=3200,
    )
    sched = AgriculturalScheduleRecord(
        source_id=valid_source_id,
        source_urn=CensusUrn("URN:CENSUS:1870:NH_MERRIMACK:AGRI_P05"),
        record_category=SourceRecordCategory.CENSUS,
        description="1870 Agricultural Schedule",
        repository_id=valid_repo_id,
        audit=valid_audit,
        enumeration_year=HistoricalYear(1870),
        jurisdiction_raw="Concord, NH",
        state="New Hampshire",
        county="Merrimack",
        entries=(entry,),
    )
    assert sched.entries[0].improved_acres == 85

    with pytest.raises(ModelFormatError, match="AgriculturalScheduleRecord enumeration_year"):
        AgriculturalScheduleRecord(
            source_id=valid_source_id,
            source_urn=CensusUrn("URN:CENSUS:1900:NH_MERRIMACK:AGRI_P05"),
            record_category=SourceRecordCategory.CENSUS,
            description="Invalid 1900 year",
            repository_id=valid_repo_id,
            audit=valid_audit,
            enumeration_year=HistoricalYear(1900),
            jurisdiction_raw="Concord, NH",
            state="New Hampshire",
            county="Merrimack",
            entries=(entry,),
        )


@pytest.mark.unit
def test_manufacturing_schedule_valid_and_year_guard(
    valid_source_id: SourceID,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify ManufacturingScheduleRecord valid entries and 1810-1880 year bounds."""
    entry = ManufacturingScheduleEntry(
        entry_urn=CensusUrn("URN:CENSUS:1860:NH_MERRIMACK:MFG_P01_L04"),
        line_number=4,
        name_verbatim="Lehman Carriage Works",
        business_or_product_raw="Carriages & Wagons",
        capital_invested_usd=5000,
        male_hands_count=8,
        annual_product_value_usd=12000,
    )
    sched = ManufacturingScheduleRecord(
        source_id=valid_source_id,
        source_urn=CensusUrn("URN:CENSUS:1860:NH_MERRIMACK:MFG_P01"),
        record_category=SourceRecordCategory.CENSUS,
        description="1860 Manufacturing Schedule",
        repository_id=valid_repo_id,
        audit=valid_audit,
        enumeration_year=HistoricalYear(1860),
        jurisdiction_raw="Concord, NH",
        state="New Hampshire",
        county="Merrimack",
        entries=(entry,),
    )
    assert sched.entries[0].male_hands_count == 8

    with pytest.raises(ModelFormatError, match="ManufacturingScheduleRecord enumeration_year"):
        ManufacturingScheduleRecord(
            source_id=valid_source_id,
            source_urn=CensusUrn("URN:CENSUS:1900:NH_MERRIMACK:MFG_P01"),
            record_category=SourceRecordCategory.CENSUS,
            description="Invalid 1900 year",
            repository_id=valid_repo_id,
            audit=valid_audit,
            enumeration_year=HistoricalYear(1900),
            jurisdiction_raw="Concord, NH",
            state="New Hampshire",
            county="Merrimack",
            entries=(entry,),
        )


@pytest.mark.unit
def test_slave_schedule_valid_and_guards(
    valid_source_id: SourceID,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify SlaveScheduleRecord valid entries, slaveholder hygiene, and 1850/1860 year bounds."""
    entry_padded = SlaveScheduleEntry(
        entry_urn=CensusUrn("URN:CENSUS:1860:VA_HENRICO:SLV_P10_L01"),
        line_number=1,
        name_verbatim="Unnamed Enslaved Person #1",
        slaveholder_name_raw="  Thomas Carter  ",
        slaveholder_id=IndividualID("IND-000050"),
        age_raw="34",
        sex_raw="M",
        color_raw="B",
    )
    assert entry_padded.slaveholder_name_raw == "Thomas Carter"

    entry_clean = SlaveScheduleEntry(
        entry_urn=CensusUrn("URN:CENSUS:1860:VA_HENRICO:SLV_P10_L02"),
        line_number=2,
        name_verbatim="Unnamed Enslaved Person #2",
        slaveholder_name_raw="Thomas Carter",
    )
    assert entry_clean.slaveholder_name_raw == "Thomas Carter"

    with pytest.raises(ModelFormatError, match="slaveholder_name_raw.*cannot be empty"):
        SlaveScheduleEntry(
            entry_urn=CensusUrn("URN:CENSUS:1860:VA_HENRICO:SLV_P10_L03"),
            line_number=3,
            name_verbatim="Unnamed Enslaved Person #3",
            slaveholder_name_raw="   ",
        )

    sched = SlaveScheduleRecord(
        source_id=valid_source_id,
        source_urn=CensusUrn("URN:CENSUS:1860:VA_HENRICO:SLV_P10"),
        record_category=SourceRecordCategory.CENSUS,
        description="1860 Henrico County Slave Schedule",
        repository_id=valid_repo_id,
        audit=valid_audit,
        enumeration_year=HistoricalYear(1860),
        jurisdiction_raw="Henrico County, VA",
        state="Virginia",
        county="Henrico",
        entries=(entry_padded, entry_clean),
    )
    assert sched.entry_count == 2

    with pytest.raises(ModelFormatError, match="SlaveScheduleRecord enumeration_year"):
        SlaveScheduleRecord(
            source_id=valid_source_id,
            source_urn=CensusUrn("URN:CENSUS:1870:VA_HENRICO:SLV_P10"),
            record_category=SourceRecordCategory.CENSUS,
            description="Invalid 1870 year",
            repository_id=valid_repo_id,
            audit=valid_audit,
            enumeration_year=HistoricalYear(1870),
            jurisdiction_raw="Henrico County, VA",
            state="Virginia",
            county="Henrico",
            entries=(entry_clean,),
        )


@pytest.mark.unit
def test_veterans_1890_schedule_valid_and_year_guard(
    valid_source_id: SourceID,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify Veterans1890ScheduleRecord valid entries and strict 1890 year check."""
    entry = Veterans1890Entry(
        entry_urn=CensusUrn("URN:CENSUS:1890:NH_MERRIMACK:VET_ED178_P01_L03"),
        line_number=3,
        name_verbatim="Glenn Lehman",
        rank_raw="Private",
        company_raw="B",
        regiment_or_vessel_raw="2nd NH Infantry",
        enlistment_date_raw="1861-05-20",
        discharge_date_raw="1864-06-21",
        service_length_raw="3 yrs, 1 mo, 1 day",
        post_office_address_raw="Concord, NH",
    )
    sched = Veterans1890ScheduleRecord(
        source_id=valid_source_id,
        source_urn=CensusUrn("URN:CENSUS:1890:NH_MERRIMACK:VET_ED178_P01"),
        record_category=SourceRecordCategory.CENSUS,
        description="1890 Special Veterans Schedule",
        repository_id=valid_repo_id,
        audit=valid_audit,
        enumeration_year=HistoricalYear(1890),
        jurisdiction_raw="Concord, NH",
        state="New Hampshire",
        county="Merrimack",
        entries=(entry,),
    )
    assert sched.entries[0].regiment_or_vessel_raw == "2nd NH Infantry"

    with pytest.raises(ModelFormatError, match="Veterans1890ScheduleRecord enumeration_year"):
        Veterans1890ScheduleRecord(
            source_id=valid_source_id,
            source_urn=CensusUrn("URN:CENSUS:1880:NH_MERRIMACK:VET_ED178_P01"),
            record_category=SourceRecordCategory.CENSUS,
            description="Invalid 1880 year",
            repository_id=valid_repo_id,
            audit=valid_audit,
            enumeration_year=HistoricalYear(1880),
            jurisdiction_raw="Concord, NH",
            state="New Hampshire",
            county="Merrimack",
            entries=(entry,),
        )
