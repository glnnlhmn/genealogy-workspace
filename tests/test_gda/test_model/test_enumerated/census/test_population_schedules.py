"""Path: tests/test_gda/test_model/test_enumerated/census/test_population_schedules.py

Atomized behavioral test suite for all decennial U.S. Federal Population Schedules.

Operational Role:
    Verifies valid instantiation, specialized entry columns, and decennial
    enumeration year boundaries across 1790-1840, 1850-1870, 1880, 1900-1910,
    1920, 1930, 1940, and 1950 population schedules with 100% branch coverage.
"""

from __future__ import annotations

import pytest

from gda.core.enums.fiscal import CitizenshipStatus, HomeOwnership
from gda.core.enums.sources import SourceRecordCategory
from gda.core.errors import ModelFormatError
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import RepositoryID, SourceID
from gda.model.atom.urn import CensusUrn
from gda.model.atom.year import HistoricalYear
from gda.model.base.audit import AuditStamp
from gda.model.enumerated.census.population import (
    HouseholdTallyEntry,
    Population1850_1870Entry,
    Population1880Entry,
    Population1900_1910Entry,
    Population1920Entry,
    Population1930Entry,
    Population1940Entry,
    Population1950Entry,
    PopulationSchedule1790_1840,
    PopulationSchedule1850_1870,
    PopulationSchedule1880,
    PopulationSchedule1900_1910,
    PopulationSchedule1920,
    PopulationSchedule1930,
    PopulationSchedule1940,
    PopulationSchedule1950,
)

__version__ = "1.0.0+build.1"


@pytest.fixture
def valid_audit() -> AuditStamp:
    """Return synthetic in-memory AuditStamp."""
    ts = IsoTimestamp("2026-01-01T00:00:00Z")
    return AuditStamp(created_at=ts, updated_at=ts)


@pytest.fixture
def valid_repo_id() -> RepositoryID:
    """Return synthetic RepositoryID."""
    return RepositoryID("REP-000001")


@pytest.fixture
def valid_source_id() -> SourceID:
    """Return synthetic SourceID."""
    return SourceID("c9a646d3-9c61-4a70-8b14-c48c8b417c8d")


@pytest.mark.unit
@pytest.mark.smoke
def test_population_schedule_1790_1840_valid_and_year_guard(
    valid_source_id: SourceID,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify PopulationSchedule1790_1840 valid tally entries and year enforcement."""
    entry = HouseholdTallyEntry(
        entry_urn=CensusUrn("URN:CENSUS:1840:NH_MERRIMACK:P102_L04"),
        line_number=4,
        name_verbatim="Samuel Lehman",
        free_white_males_under_16=2,
        free_white_males_16_and_over=1,
        free_white_females=3,
        total_in_household=6,
        revolutionary_pensioners_count=1,
        age_bracket_tallies={"FWM_30_40": 1},
    )
    sched = PopulationSchedule1790_1840(
        source_id=valid_source_id,
        source_urn=CensusUrn("URN:CENSUS:1840:NH_MERRIMACK:P102"),
        record_category=SourceRecordCategory.CENSUS,
        description="1840 Concord Tally Sheet",
        repository_id=valid_repo_id,
        audit=valid_audit,
        enumeration_year=HistoricalYear(1840),
        jurisdiction_raw="Concord, NH",
        state="New Hampshire",
        county="Merrimack",
        entries=(entry,),
    )
    assert sched.entries[0].revolutionary_pensioners_count == 1

    with pytest.raises(ModelFormatError, match="PopulationSchedule1790_1840 enumeration_year"):
        PopulationSchedule1790_1840(
            source_id=valid_source_id,
            source_urn=CensusUrn("URN:CENSUS:1850:NH_MERRIMACK:P102"),
            record_category=SourceRecordCategory.CENSUS,
            description="Invalid 1850 year",
            repository_id=valid_repo_id,
            audit=valid_audit,
            enumeration_year=HistoricalYear(1850),
            jurisdiction_raw="Concord, NH",
            state="New Hampshire",
            county="Merrimack",
            entries=(entry,),
        )


@pytest.mark.unit
def test_population_schedule_1850_1870_valid_and_year_guard(
    valid_source_id: SourceID,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify PopulationSchedule1850_1870 valid entries and year enforcement."""
    entry = Population1850_1870Entry(
        entry_urn=CensusUrn("URN:CENSUS:1870:NH_MERRIMACK:P014_L11"),
        line_number=11,
        name_verbatim="Glenn Lehman",
        dwelling_number="84",
        family_number="88",
        age_raw="28",
        sex_raw="M",
        color_raw="W",
        occupation_raw="Farmer",
        real_estate_value_usd=2400,
        personal_estate_value_usd=650,
        birthplace_raw="New Hampshire",
        father_foreign_born=False,
        mother_foreign_born=False,
    )
    sched = PopulationSchedule1850_1870(
        source_id=valid_source_id,
        source_urn=CensusUrn("URN:CENSUS:1870:NH_MERRIMACK:P014"),
        record_category=SourceRecordCategory.CENSUS,
        description="1870 Population Schedule",
        repository_id=valid_repo_id,
        audit=valid_audit,
        enumeration_year=HistoricalYear(1870),
        jurisdiction_raw="Concord, NH",
        state="New Hampshire",
        county="Merrimack",
        entries=(entry,),
    )
    assert sched.entries[0].real_estate_value_usd == 2400

    with pytest.raises(ModelFormatError, match="PopulationSchedule1850_1870 enumeration_year"):
        PopulationSchedule1850_1870(
            source_id=valid_source_id,
            source_urn=CensusUrn("URN:CENSUS:1880:NH_MERRIMACK:P014"),
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


@pytest.mark.unit
def test_population_schedule_1880_valid_and_year_guard(
    valid_source_id: SourceID,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify PopulationSchedule1880 valid entries and year enforcement."""
    entry = Population1880Entry(
        entry_urn=CensusUrn("URN:CENSUS:1880:NH_MERRIMACK:ED178_S12A_L05"),
        line_number=5,
        name_verbatim="Glenn Lehman",
        relationship_to_head_raw="Head",
        marital_status_raw="M",
        birthplace_raw="New Hampshire",
        father_birthplace_raw="Pennsylvania",
        mother_birthplace_raw="New Hampshire",
    )
    sched = PopulationSchedule1880(
        source_id=valid_source_id,
        source_urn=CensusUrn("URN:CENSUS:1880:NH_MERRIMACK:ED178_S12A"),
        record_category=SourceRecordCategory.CENSUS,
        description="1880 Population Schedule",
        repository_id=valid_repo_id,
        audit=valid_audit,
        enumeration_year=HistoricalYear(1880),
        jurisdiction_raw="Concord, NH",
        state="New Hampshire",
        county="Merrimack",
        entries=(entry,),
    )
    assert sched.entries[0].relationship_to_head_raw == "Head"

    with pytest.raises(ModelFormatError, match="PopulationSchedule1880 enumeration_year"):
        PopulationSchedule1880(
            source_id=valid_source_id,
            source_urn=CensusUrn("URN:CENSUS:1900:NH_MERRIMACK:ED178_S12A"),
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
def test_population_schedule_1900_1910_valid_and_year_guard(
    valid_source_id: SourceID,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify PopulationSchedule1900_1910 valid entries and year enforcement."""
    entry = Population1900_1910Entry(
        entry_urn=CensusUrn("URN:CENSUS:1900:NH_MERRIMACK:ED155_S04A_L12"),
        line_number=12,
        name_verbatim="Glenn Lehman",
        birth_month_raw="May",
        birth_year_raw="1864",
        years_married=10,
        citizenship_status=CitizenshipStatus.NATIVE_BORN,
        home_ownership=HomeOwnership.OWNED,
    )
    sched = PopulationSchedule1900_1910(
        source_id=valid_source_id,
        source_urn=CensusUrn("URN:CENSUS:1900:NH_MERRIMACK:ED155_S04A"),
        record_category=SourceRecordCategory.CENSUS,
        description="1900 Population Schedule",
        repository_id=valid_repo_id,
        audit=valid_audit,
        enumeration_year=HistoricalYear(1900),
        jurisdiction_raw="Concord, NH",
        state="New Hampshire",
        county="Merrimack",
        entries=(entry,),
    )
    assert sched.entries[0].birth_month_raw == "May"

    with pytest.raises(ModelFormatError, match="PopulationSchedule1900_1910 enumeration_year"):
        PopulationSchedule1900_1910(
            source_id=valid_source_id,
            source_urn=CensusUrn("URN:CENSUS:1920:NH_MERRIMACK:ED155_S04A"),
            record_category=SourceRecordCategory.CENSUS,
            description="Invalid 1920 year",
            repository_id=valid_repo_id,
            audit=valid_audit,
            enumeration_year=HistoricalYear(1920),
            jurisdiction_raw="Concord, NH",
            state="New Hampshire",
            county="Merrimack",
            entries=(entry,),
        )


@pytest.mark.unit
def test_population_schedule_1920_valid_and_year_guard(
    valid_source_id: SourceID,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify PopulationSchedule1920 valid entries and year enforcement."""
    entry = Population1920Entry(
        entry_urn=CensusUrn("URN:CENSUS:1920:NH_MERRIMACK:ED082_S07B_L03"),
        line_number=3,
        name_verbatim="Glenn Lehman",
        naturalization_year=1912,
        mother_tongue_raw="English",
    )
    sched = PopulationSchedule1920(
        source_id=valid_source_id,
        source_urn=CensusUrn("URN:CENSUS:1920:NH_MERRIMACK:ED082_S07B"),
        record_category=SourceRecordCategory.CENSUS,
        description="1920 Population Schedule",
        repository_id=valid_repo_id,
        audit=valid_audit,
        enumeration_year=HistoricalYear(1920),
        jurisdiction_raw="Concord, NH",
        state="New Hampshire",
        county="Merrimack",
        entries=(entry,),
    )
    assert sched.entries[0].naturalization_year == 1912

    with pytest.raises(ModelFormatError, match="PopulationSchedule1920 enumeration_year"):
        PopulationSchedule1920(
            source_id=valid_source_id,
            source_urn=CensusUrn("URN:CENSUS:1930:NH_MERRIMACK:ED082_S07B"),
            record_category=SourceRecordCategory.CENSUS,
            description="Invalid 1930 year",
            repository_id=valid_repo_id,
            audit=valid_audit,
            enumeration_year=HistoricalYear(1930),
            jurisdiction_raw="Concord, NH",
            state="New Hampshire",
            county="Merrimack",
            entries=(entry,),
        )


@pytest.mark.unit
def test_population_schedule_1930_valid_and_year_guard(
    valid_source_id: SourceID,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify PopulationSchedule1930 valid entries and year enforcement."""
    entry = Population1930Entry(
        entry_urn=CensusUrn("URN:CENSUS:1930:NH_MERRIMACK:ED07_0015_S03A_L18"),
        line_number=18,
        name_verbatim="Glenn Lehman",
        home_value_or_monthly_rent_raw="4500",
        has_radio_set=True,
        age_at_first_marriage=24,
        veteran_war_code_raw="WW",
    )
    sched = PopulationSchedule1930(
        source_id=valid_source_id,
        source_urn=CensusUrn("URN:CENSUS:1930:NH_MERRIMACK:ED07_0015_S03A"),
        record_category=SourceRecordCategory.CENSUS,
        description="1930 Population Schedule",
        repository_id=valid_repo_id,
        audit=valid_audit,
        enumeration_year=HistoricalYear(1930),
        jurisdiction_raw="Concord, NH",
        state="New Hampshire",
        county="Merrimack",
        entries=(entry,),
    )
    assert sched.entries[0].has_radio_set is True

    with pytest.raises(ModelFormatError, match="PopulationSchedule1930 enumeration_year"):
        PopulationSchedule1930(
            source_id=valid_source_id,
            source_urn=CensusUrn("URN:CENSUS:1940:NH_MERRIMACK:ED07_0015_S03A"),
            record_category=SourceRecordCategory.CENSUS,
            description="Invalid 1940 year",
            repository_id=valid_repo_id,
            audit=valid_audit,
            enumeration_year=HistoricalYear(1940),
            jurisdiction_raw="Concord, NH",
            state="New Hampshire",
            county="Merrimack",
            entries=(entry,),
        )


@pytest.mark.unit
def test_population_schedule_1940_valid_and_year_guard(
    valid_source_id: SourceID,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify PopulationSchedule1940 valid entries and year enforcement."""
    entry = Population1940Entry(
        entry_urn=CensusUrn("URN:CENSUS:1940:NH_MERRIMACK:ED07_0021_S02A_L14"),
        line_number=14,
        name_verbatim="Glenn Lehman",
        highest_grade_completed_raw="H-4",
        residence_1935_raw="Same House",
        weeks_worked_1939=52,
        wage_salary_income_usd=1850,
        is_sample_line=True,
    )
    sched = PopulationSchedule1940(
        source_id=valid_source_id,
        source_urn=CensusUrn("URN:CENSUS:1940:NH_MERRIMACK:ED07_0021_S02A"),
        record_category=SourceRecordCategory.CENSUS,
        description="1940 Population Schedule",
        repository_id=valid_repo_id,
        audit=valid_audit,
        enumeration_year=HistoricalYear(1940),
        jurisdiction_raw="Concord, NH",
        state="New Hampshire",
        county="Merrimack",
        entries=(entry,),
    )
    assert sched.entries[0].is_sample_line is True

    with pytest.raises(ModelFormatError, match="PopulationSchedule1940 enumeration_year"):
        PopulationSchedule1940(
            source_id=valid_source_id,
            source_urn=CensusUrn("URN:CENSUS:1950:NH_MERRIMACK:ED07_0021_S02A"),
            record_category=SourceRecordCategory.CENSUS,
            description="Invalid 1950 year",
            repository_id=valid_repo_id,
            audit=valid_audit,
            enumeration_year=HistoricalYear(1950),
            jurisdiction_raw="Concord, NH",
            state="New Hampshire",
            county="Merrimack",
            entries=(entry,),
        )


@pytest.mark.unit
def test_population_schedule_1950_valid_and_year_guard(
    valid_source_id: SourceID,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify PopulationSchedule1950 valid entries and year enforcement."""
    entry = Population1950Entry(
        entry_urn=CensusUrn("URN:CENSUS:1950:NH_MERRIMACK:ED07_0030_P05_L09"),
        line_number=9,
        name_verbatim="Glenn Lehman",
        hours_worked_last_week=40,
        is_sample_line=True,
        residence_1949_raw="Same house",
        veteran_service_raw="WWII",
    )
    sched = PopulationSchedule1950(
        source_id=valid_source_id,
        source_urn=CensusUrn("URN:CENSUS:1950:NH_MERRIMACK:ED07_0030_P05"),
        record_category=SourceRecordCategory.CENSUS,
        description="1950 Population Schedule",
        repository_id=valid_repo_id,
        audit=valid_audit,
        enumeration_year=HistoricalYear(1950),
        jurisdiction_raw="Concord, NH",
        state="New Hampshire",
        county="Merrimack",
        entries=(entry,),
    )
    assert sched.entries[0].veteran_service_raw == "WWII"

    with pytest.raises(ModelFormatError, match="PopulationSchedule1950 enumeration_year"):
        PopulationSchedule1950(
            source_id=valid_source_id,
            source_urn=CensusUrn("URN:CENSUS:1940:NH_MERRIMACK:ED07_0030_P05"),
            record_category=SourceRecordCategory.CENSUS,
            description="Invalid 1940 year",
            repository_id=valid_repo_id,
            audit=valid_audit,
            enumeration_year=HistoricalYear(1940),
            jurisdiction_raw="Concord, NH",
            state="New Hampshire",
            county="Merrimack",
            entries=(entry,),
        )
