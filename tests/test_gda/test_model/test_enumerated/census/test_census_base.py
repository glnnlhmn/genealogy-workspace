"""Path: tests/test_gda/test_model/test_enumerated/census/test_census_base.py

Atomized behavioral test suite for CensusLineEntry and CensusScheduleRecord.

Operational Role:
    Verifies row-level URN/GUID uniqueness, sheet side validation, line_count
    bounds, dual-path get_entry/require_entry lookup, immutable replace_entry,
    flatten_entries(), and dict/JSON serialization round-trips.
"""

from __future__ import annotations

import dataclasses

import pytest

from gda.core.enums.sources import SourceRecordCategory, SourceRecordType
from gda.core.errors import ModelFormatError
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import IndividualID, RepositoryID, SourceID
from gda.model.atom.urn import CensusUrn, SourceURN
from gda.model.atom.year import HistoricalYear
from gda.model.base.audit import AuditStamp
from gda.model.enumerated.census.base import CensusLineEntry, CensusScheduleRecord
from gda.model.enumerated.census.population import (
    Population1900_1910Entry,
    PopulationSchedule1900_1910,
)

__version__ = "1.0.0+build.7"


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


@pytest.fixture
def valid_sheet_urn() -> CensusUrn:
    """Return synthetic sheet-level CensusUrn."""
    return CensusUrn("URN:CENSUS:1880:NH_MERRIMACK:ED178_S12A")


@pytest.mark.unit
@pytest.mark.smoke
def test_census_line_entry_dual_lookup_replace_flatten_and_roundtrip(
    valid_source_id: SourceID,
    valid_sheet_urn: CensusUrn,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify CensusLineEntry creation, dual lookup, replace_entry, flatten_entries, and JSON."""
    row1_urn = CensusUrn("URN:CENSUS:1880:NH_MERRIMACK:ED178_S12A_L01")
    row1_guid = SourceID("11111111-1111-4111-8111-111111111111")
    row2_urn = CensusUrn("URN:CENSUS:1880:NH_MERRIMACK:ED178_S12A_L02")

    entry1 = CensusLineEntry(
        entry_urn=row1_urn,
        entry_id=row1_guid,
        line_number=1,
        name_verbatim="  Glenn D. Leman  ",
        individual_id=IndividualID("IND-000001"),
        age_raw="35",
        sex_raw="M",
    )
    entry2 = CensusLineEntry(
        entry_urn=row2_urn,
        line_number=2,
        name_verbatim="Sarah Lehman",
        age_raw="32",
        sex_raw="F",
    )
    assert entry1.name_verbatim == "Glenn D. Leman"
    assert "Line 1: Glenn D. Leman" in str(entry1)
    assert "CensusLineEntry(" in repr(entry1)
    assert CensusLineEntry.from_json(entry1.to_json()) == entry1
    assert CensusLineEntry.from_dict(
        {"entry_urn": str(row2_urn), "line_number": 2, "name_verbatim": "Sarah Lehman"}
    ) == CensusLineEntry(entry_urn=row2_urn, line_number=2, name_verbatim="Sarah Lehman")

    schedule = CensusScheduleRecord(
        source_id=valid_source_id,
        source_urn=valid_sheet_urn,
        record_category=SourceRecordCategory.CENSUS,
        record_type=SourceRecordType.POPULATION_SCHEDULE,
        description="1880 Merrimack County Sheet 12A",
        repository_id=valid_repo_id,
        audit=valid_audit,
        enumeration_year=HistoricalYear(1880),
        jurisdiction_raw="Concord, Merrimack County, NH",
        state="  New Hampshire  ",
        county="  Merrimack  ",
        township_or_ward="Concord Ward 4",
        supervisor_district="1",
        enumeration_district="178",
        sheet_number="12",
        sheet_side="A",
        line_count=40,
        entries=(entry1, entry2),
    )
    assert schedule.state == "New Hampshire"
    assert schedule.county == "Merrimack"
    assert schedule.entry_count == 2

    # Lookup by CensusUrn object and raw URN string
    assert schedule.get_entry(row1_urn) is entry1
    assert schedule.get_entry(str(row2_urn)) is entry2
    assert schedule.require_entry(row2_urn) is entry2

    # Lookup by SourceID GUID object and raw GUID string
    assert schedule.get_entry(row1_guid) is entry1
    assert schedule.require_entry(str(row1_guid)) is entry1

    # Missing or blank lookup
    assert schedule.get_entry("") is None
    assert schedule.get_entry("URN:CENSUS:1880:NH_MERRIMACK:MISSING") is None
    with pytest.raises(ModelFormatError, match="No census line entry matching"):
        schedule.require_entry("URN:CENSUS:1880:NH_MERRIMACK:MISSING")

    # Immutable transcription fix via replace_entry (matching by URN and by GUID)
    corrected_entry1 = dataclasses.replace(entry1, name_verbatim="Glenn D. Lehman")
    updated_schedule = schedule.replace_entry(corrected_entry1)
    assert updated_schedule.entries[0].name_verbatim == "Glenn D. Lehman"
    assert schedule.entries[0].name_verbatim == "Glenn D. Leman"

    guid_only_match = CensusLineEntry(
        entry_urn=CensusUrn("URN:CENSUS:1880:NH_MERRIMACK:ED178_S12A_L01_REV"),
        entry_id=row1_guid,
        line_number=1,
        name_verbatim="Glenn D. Lehman",
    )
    updated_by_guid = schedule.replace_entry(guid_only_match)
    assert updated_by_guid.entries[0].name_verbatim == "Glenn D. Lehman"

    # Flatten rows with sheet metadata
    flat_rows = updated_schedule.flatten_entries()
    assert len(flat_rows) == 2
    assert flat_rows[0]["enumeration_district"] == "178"
    assert flat_rows[0]["name_verbatim"] == "Glenn D. Lehman"
    assert flat_rows[1]["line_number"] == 2

    # Base and polymorphic subclass dict/JSON round-trip
    assert CensusScheduleRecord.from_json(updated_schedule.to_json()) == updated_schedule

    direct_payload = updated_schedule.to_dict()
    direct_payload["entries"] = list(updated_schedule.entries)
    assert CensusScheduleRecord.from_dict(direct_payload) == updated_schedule

    pop1910 = PopulationSchedule1900_1910(
        source_id=valid_source_id,
        source_urn=CensusUrn("URN:CENSUS:1910:NH_MERRIMACK:ED155_S04A"),
        record_category=SourceRecordCategory.CENSUS,
        description="1910 Schedule",
        repository_id=valid_repo_id,
        audit=valid_audit,
        enumeration_year=HistoricalYear(1910),
        jurisdiction_raw="Concord, NH",
        state="New Hampshire",
        county="Merrimack",
        entries=(
            Population1900_1910Entry(
                entry_urn=CensusUrn("URN:CENSUS:1910:NH_MERRIMACK:ED155_S04A_L01"),
                line_number=1,
                name_verbatim="Glenn Lehman",
                years_married=12,
            ),
        ),
    )
    restored_1910 = PopulationSchedule1900_1910.from_json(pop1910.to_json())
    assert restored_1910 == pop1910
    assert isinstance(restored_1910.entries[0], Population1900_1910Entry)

    class _ParameterizedMixin[TParam]:
        pass

    class _MixedSchedule(_ParameterizedMixin[int], CensusScheduleRecord[CensusLineEntry]):
        pass

    class _GenericChild[TEntry: CensusLineEntry](CensusScheduleRecord[TEntry]):
        pass

    assert _MixedSchedule._resolve_entry_class() is CensusLineEntry
    assert _GenericChild._resolve_entry_class() is CensusLineEntry


@pytest.mark.unit
@pytest.mark.regression
def test_census_schedule_validation_and_serialization_failures(
    valid_source_id: SourceID,
    valid_sheet_urn: CensusUrn,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify ModelFormatError raised on invalid fields, duplicates, replace misses, and bad JSON."""
    row1 = CensusLineEntry(
        entry_urn=CensusUrn("URN:CENSUS:1880:NH_MERRIMACK:ED178_S12A_L01"),
        entry_id=SourceID("11111111-1111-4111-8111-111111111111"),
        line_number=1,
        name_verbatim="Glenn Lehman",
    )

    with pytest.raises(ModelFormatError, match="name_verbatim.*cannot be empty"):
        CensusLineEntry(
            entry_urn=CensusUrn("URN:CENSUS:1880:NH_MERRIMACK:ED178_S12A_L09"),
            line_number=9,
            name_verbatim="   ",
        )

    with pytest.raises(ModelFormatError, match="CensusLineEntry payload must be a dictionary"):
        CensusLineEntry.from_dict("not-a-dict")  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="Failed to parse CensusLineEntry JSON"):
        CensusLineEntry.from_json("{bad-json")

    base_sched = CensusScheduleRecord(
        source_id=valid_source_id,
        source_urn=valid_sheet_urn,
        record_category=SourceRecordCategory.CENSUS,
        description="Base sheet",
        repository_id=valid_repo_id,
        audit=valid_audit,
        enumeration_year=HistoricalYear(1880),
        jurisdiction_raw="Concord, NH",
        state="New Hampshire",
        county="Merrimack",
        entries=(row1,),
    )

    with pytest.raises(ModelFormatError, match="Cannot replace entry"):
        base_sched.replace_entry(
            CensusLineEntry(
                entry_urn=CensusUrn("URN:CENSUS:1880:NH_MERRIMACK:ED178_S12A_L99"),
                line_number=99,
                name_verbatim="Missing Row",
            )
        )

    bad_entries_payload = base_sched.to_dict()
    bad_entries_payload["entries"] = "not-a-list"
    with pytest.raises(ModelFormatError, match="'entries' must be a list or tuple"):
        CensusScheduleRecord.from_dict(bad_entries_payload)

    # Wrong category
    with pytest.raises(ModelFormatError, match="requires category 'CENSUS'"):
        CensusScheduleRecord(
            source_id=valid_source_id,
            source_urn=valid_sheet_urn,
            record_category=SourceRecordCategory.TAX,
            description="Wrong category",
            repository_id=valid_repo_id,
            audit=valid_audit,
            enumeration_year=HistoricalYear(1880),
            jurisdiction_raw="Concord, NH",
            state="New Hampshire",
            county="Merrimack",
            entries=(row1,),
        )

    # Wrong record_type
    with pytest.raises(ModelFormatError, match="requires record_type in"):
        CensusScheduleRecord(
            source_id=valid_source_id,
            source_urn=valid_sheet_urn,
            record_category=SourceRecordCategory.CENSUS,
            record_type=SourceRecordType.REAL_ESTATE_TAX,
            description="Wrong record_type",
            repository_id=valid_repo_id,
            audit=valid_audit,
            enumeration_year=HistoricalYear(1880),
            jurisdiction_raw="Concord, NH",
            state="New Hampshire",
            county="Merrimack",
            entries=(row1,),
        )

    # Non-CensusUrn source_urn
    with pytest.raises(ModelFormatError, match="must be a CensusUrn"):
        CensusScheduleRecord(
            source_id=valid_source_id,
            source_urn=SourceURN("URN:SRC:1880:NH_MERRIMACK:DOC_01"),
            record_category=SourceRecordCategory.CENSUS,
            description="Wrong URN type",
            repository_id=valid_repo_id,
            audit=valid_audit,
            enumeration_year=HistoricalYear(1880),
            jurisdiction_raw="Concord, NH",
            state="New Hampshire",
            county="Merrimack",
            entries=(row1,),
        )

    # Blank state / county
    with pytest.raises(ModelFormatError, match="'state' cannot be empty"):
        CensusScheduleRecord(
            source_id=valid_source_id,
            source_urn=valid_sheet_urn,
            record_category=SourceRecordCategory.CENSUS,
            description="Blank state",
            repository_id=valid_repo_id,
            audit=valid_audit,
            enumeration_year=HistoricalYear(1880),
            jurisdiction_raw="Concord, NH",
            state="   ",
            county="Merrimack",
            entries=(row1,),
        )

    with pytest.raises(ModelFormatError, match="'county' cannot be empty"):
        CensusScheduleRecord(
            source_id=valid_source_id,
            source_urn=valid_sheet_urn,
            record_category=SourceRecordCategory.CENSUS,
            description="Blank county",
            repository_id=valid_repo_id,
            audit=valid_audit,
            enumeration_year=HistoricalYear(1880),
            jurisdiction_raw="Concord, NH",
            state="New Hampshire",
            county="   ",
            entries=(row1,),
        )

    # Invalid sheet_side
    with pytest.raises(ModelFormatError, match="'sheet_side' must be one of"):
        CensusScheduleRecord(
            source_id=valid_source_id,
            source_urn=valid_sheet_urn,
            record_category=SourceRecordCategory.CENSUS,
            description="Bad sheet side",
            repository_id=valid_repo_id,
            audit=valid_audit,
            enumeration_year=HistoricalYear(1880),
            jurisdiction_raw="Concord, NH",
            state="New Hampshire",
            county="Merrimack",
            sheet_side="C",
            entries=(row1,),
        )

    # Entry count exceeds line_count
    row2 = CensusLineEntry(
        entry_urn=CensusUrn("URN:CENSUS:1880:NH_MERRIMACK:ED178_S12A_L02"),
        line_number=2,
        name_verbatim="Sarah Lehman",
    )
    with pytest.raises(ModelFormatError, match="exceeds declared sheet line_count"):
        CensusScheduleRecord(
            source_id=valid_source_id,
            source_urn=valid_sheet_urn,
            record_category=SourceRecordCategory.CENSUS,
            description="Too many rows",
            repository_id=valid_repo_id,
            audit=valid_audit,
            enumeration_year=HistoricalYear(1880),
            jurisdiction_raw="Concord, NH",
            state="New Hampshire",
            county="Merrimack",
            line_count=1,
            entries=(row1, row2),
        )

    # Duplicate entry_urn
    dup_urn_row = CensusLineEntry(
        entry_urn=row1.entry_urn,
        line_number=2,
        name_verbatim="Duplicate URN",
    )
    with pytest.raises(ModelFormatError, match="Duplicate CensusLineEntry entry_urn"):
        CensusScheduleRecord(
            source_id=valid_source_id,
            source_urn=valid_sheet_urn,
            record_category=SourceRecordCategory.CENSUS,
            description="Dup URN",
            repository_id=valid_repo_id,
            audit=valid_audit,
            enumeration_year=HistoricalYear(1880),
            jurisdiction_raw="Concord, NH",
            state="New Hampshire",
            county="Merrimack",
            entries=(row1, dup_urn_row),
        )

    # Duplicate entry_id GUID
    dup_guid_row = CensusLineEntry(
        entry_urn=CensusUrn("URN:CENSUS:1880:NH_MERRIMACK:ED178_S12A_L02"),
        entry_id=row1.entry_id,
        line_number=2,
        name_verbatim="Duplicate GUID",
    )
    with pytest.raises(ModelFormatError, match="Duplicate CensusLineEntry entry_id"):
        CensusScheduleRecord(
            source_id=valid_source_id,
            source_urn=valid_sheet_urn,
            record_category=SourceRecordCategory.CENSUS,
            description="Dup GUID",
            repository_id=valid_repo_id,
            audit=valid_audit,
            enumeration_year=HistoricalYear(1880),
            jurisdiction_raw="Concord, NH",
            state="New Hampshire",
            county="Merrimack",
            entries=(row1, dup_guid_row),
        )

    # Duplicate line_number
    dup_line_row = CensusLineEntry(
        entry_urn=CensusUrn("URN:CENSUS:1880:NH_MERRIMACK:ED178_S12A_L02"),
        line_number=1,
        name_verbatim="Duplicate Line",
    )
    with pytest.raises(ModelFormatError, match="Duplicate CensusLineEntry line_number"):
        CensusScheduleRecord(
            source_id=valid_source_id,
            source_urn=valid_sheet_urn,
            record_category=SourceRecordCategory.CENSUS,
            description="Dup Line",
            repository_id=valid_repo_id,
            audit=valid_audit,
            enumeration_year=HistoricalYear(1880),
            jurisdiction_raw="Concord, NH",
            state="New Hampshire",
            county="Merrimack",
            entries=(row1, dup_line_row),
        )
