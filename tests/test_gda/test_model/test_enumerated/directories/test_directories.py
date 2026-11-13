"""Path: tests/test_gda/test_model/test_enumerated/directories/test_directories.py

Atomized behavioral test suite for DirectoryEntry and DirectoryRollRecord.

Operational Role:
    Verifies city, business, farmers', and civic/voter directory entries,
    duplicate guards, dual-path URN/GUID lookup, immutable replace_entry,
    flatten_entries(), and dict/JSON serialization round-trips.
"""

from __future__ import annotations

import dataclasses

import pytest

from gda.core.enums.sources import SourceRecordCategory, SourceRecordType
from gda.core.errors import ModelFormatError
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import IndividualID, LocationID, RepositoryID, SourceID
from gda.model.atom.urn import SourceURN
from gda.model.atom.year import HistoricalYear
from gda.model.base.audit import AuditStamp
from gda.model.enumerated.directories import (
    DirectoryEntry,
    DirectoryRollRecord,
    ResidentialStatus,
)

__version__ = "1.0.0+build.4"


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
def valid_dir_urn() -> SourceURN:
    """Return synthetic directory SourceURN."""
    return SourceURN("URN:SRC:1925:NH_CONCORD:CITY_DIR_P214")


@pytest.mark.unit
@pytest.mark.smoke
def test_directory_roll_dual_lookup_replace_flatten_and_roundtrip(
    valid_source_id: SourceID,
    valid_dir_urn: SourceURN,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify DirectoryEntry creation, lookup, replace_entry, flatten_entries, and JSON."""
    e1_urn = SourceURN("URN:SRC:1925:NH_CONCORD:CITY_DIR_P214_E01")
    e1_guid = SourceID("22222222-2222-4222-8222-222222222222")
    e2_urn = SourceURN("URN:SRC:1925:NH_CONCORD:CITY_DIR_P214_E02")

    entry1 = DirectoryEntry(
        entry_urn=e1_urn,
        entry_id=e1_guid,
        name_verbatim="  Glenn D. Leman  ",
        individual_id=IndividualID("IND-000001"),
        spouse_name_raw="(Sarah)",
        occupation_verbatim="machinist",
        employer_or_business_raw="B&M RR Shops",
        residence_address_raw="42 N. State St.",
        residential_status=ResidentialStatus.HOUSEHOLDER,
        residence_location_id=LocationID("LOC-000042"),
    )
    entry2 = DirectoryEntry(
        entry_urn=e2_urn,
        name_verbatim="Sarah Lehman",
        residential_status=ResidentialStatus.WIDOW,
    )
    assert entry1.name_verbatim == "Glenn D. Leman"
    assert "Glenn D. Leman" in str(entry1)
    assert "DirectoryEntry(" in repr(entry1)
    assert DirectoryEntry.from_json(entry1.to_json()) == entry1
    assert DirectoryEntry.from_dict(
        {"entry_urn": str(e2_urn), "name_verbatim": "Sarah Lehman"}
    ) == DirectoryEntry(entry_urn=e2_urn, name_verbatim="Sarah Lehman")

    roll = DirectoryRollRecord(
        source_id=valid_source_id,
        source_urn=valid_dir_urn,
        record_category=SourceRecordCategory.DIRECTORY,
        record_type=SourceRecordType.CITY_DIRECTORY,
        description="1925 Concord City Directory Page 214",
        repository_id=valid_repo_id,
        audit=valid_audit,
        enumeration_year=HistoricalYear(1925),
        jurisdiction_raw="Concord, NH",
        publication_title_raw="  Concord City Directory 1925  ",
        page_number_raw="214",
        entries=(entry1, entry2),
    )
    assert roll.publication_title_raw == "Concord City Directory 1925"
    assert roll.entry_count == 2
    assert roll.get_entry(e1_urn) is entry1
    assert roll.get_entry(e1_guid) is entry1
    assert roll.require_entry(e2_urn) is entry2
    assert roll.get_entry("") is None
    assert roll.get_entry("URN:SRC:1925:NH_CONCORD:MISSING") is None

    with pytest.raises(ModelFormatError, match="No directory entry matching"):
        roll.require_entry("URN:SRC:1925:NH_CONCORD:MISSING")

    # Immutable replace_entry by URN and by GUID
    fixed_e1 = dataclasses.replace(entry1, name_verbatim="Glenn D. Lehman")
    updated_roll = roll.replace_entry(fixed_e1)
    assert updated_roll.entries[0].name_verbatim == "Glenn D. Lehman"

    guid_match = DirectoryEntry(
        entry_urn=SourceURN("URN:SRC:1925:NH_CONCORD:CITY_DIR_P214_E01_REV"),
        entry_id=e1_guid,
        name_verbatim="Glenn D. Lehman",
    )
    assert roll.replace_entry(guid_match).entries[0].name_verbatim == "Glenn D. Lehman"

    # Flatten entries
    flat = updated_roll.flatten_entries()
    assert len(flat) == 2
    assert flat[0]["publication_title_raw"] == "Concord City Directory 1925"
    assert flat[0]["name_verbatim"] == "Glenn D. Lehman"

    # Round-trip JSON and direct entry pass-through
    assert DirectoryRollRecord.from_json(updated_roll.to_json()) == updated_roll

    direct_payload = updated_roll.to_dict()
    direct_payload["entries"] = list(updated_roll.entries)
    assert DirectoryRollRecord.from_dict(direct_payload) == updated_roll


@pytest.mark.unit
@pytest.mark.regression
def test_directory_roll_validation_and_serialization_failures(
    valid_source_id: SourceID,
    valid_dir_urn: SourceURN,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify ModelFormatError raised on invalid category, type, blank strings, duplicates, and bad JSON."""
    e1 = DirectoryEntry(
        entry_urn=SourceURN("URN:SRC:1925:NH_CONCORD:CITY_DIR_P214_E01"),
        entry_id=SourceID("22222222-2222-4222-8222-222222222222"),
        name_verbatim="Glenn Lehman",
    )

    with pytest.raises(ModelFormatError, match="name_verbatim.*cannot be empty"):
        DirectoryEntry(
            entry_urn=SourceURN("URN:SRC:1925:NH_CONCORD:CITY_DIR_P214_E09"),
            name_verbatim="   ",
        )

    with pytest.raises(ModelFormatError, match="DirectoryEntry payload must be a dictionary"):
        DirectoryEntry.from_dict("bad")  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="Failed to parse DirectoryEntry JSON"):
        DirectoryEntry.from_json("{bad")

    roll = DirectoryRollRecord(
        source_id=valid_source_id,
        source_urn=valid_dir_urn,
        record_category=SourceRecordCategory.DIRECTORY,
        description="Concord Directory",
        repository_id=valid_repo_id,
        audit=valid_audit,
        enumeration_year=HistoricalYear(1925),
        jurisdiction_raw="Concord, NH",
        publication_title_raw="Concord Directory",
        entries=(e1,),
    )

    with pytest.raises(ModelFormatError, match="Cannot replace entry"):
        roll.replace_entry(
            DirectoryEntry(
                entry_urn=SourceURN("URN:SRC:1925:NH_CONCORD:CITY_DIR_P214_E99"),
                name_verbatim="Missing",
            )
        )

    bad_payload = roll.to_dict()
    bad_payload["entries"] = "bad"
    with pytest.raises(ModelFormatError, match="'entries' must be a list or tuple"):
        DirectoryRollRecord.from_dict(bad_payload)

    with pytest.raises(ModelFormatError, match="requires record_category in"):
        DirectoryRollRecord(
            source_id=valid_source_id,
            source_urn=valid_dir_urn,
            record_category=SourceRecordCategory.CENSUS,
            description="Invalid category",
            repository_id=valid_repo_id,
            audit=valid_audit,
            enumeration_year=HistoricalYear(1925),
            jurisdiction_raw="Concord, NH",
            publication_title_raw="Concord Directory",
            entries=(e1,),
        )

    with pytest.raises(ModelFormatError, match="requires record_type in"):
        DirectoryRollRecord(
            source_id=valid_source_id,
            source_urn=valid_dir_urn,
            record_category=SourceRecordCategory.DIRECTORY,
            record_type=SourceRecordType.POPULATION_SCHEDULE,
            description="Invalid record_type",
            repository_id=valid_repo_id,
            audit=valid_audit,
            enumeration_year=HistoricalYear(1925),
            jurisdiction_raw="Concord, NH",
            publication_title_raw="Concord Directory",
            entries=(e1,),
        )

    with pytest.raises(ModelFormatError, match="'publication_title_raw' cannot be empty"):
        DirectoryRollRecord(
            source_id=valid_source_id,
            source_urn=valid_dir_urn,
            record_category=SourceRecordCategory.DIRECTORY,
            description="Blank publication title",
            repository_id=valid_repo_id,
            audit=valid_audit,
            enumeration_year=HistoricalYear(1925),
            jurisdiction_raw="Concord, NH",
            publication_title_raw="   ",
            entries=(e1,),
        )

    dup_urn = DirectoryEntry(entry_urn=e1.entry_urn, name_verbatim="Dup URN")
    with pytest.raises(ModelFormatError, match="Duplicate DirectoryEntry entry_urn"):
        DirectoryRollRecord(
            source_id=valid_source_id,
            source_urn=valid_dir_urn,
            record_category=SourceRecordCategory.DIRECTORY,
            description="Dup URN",
            repository_id=valid_repo_id,
            audit=valid_audit,
            enumeration_year=HistoricalYear(1925),
            jurisdiction_raw="Concord, NH",
            publication_title_raw="Concord Directory",
            entries=(e1, dup_urn),
        )

    dup_guid = DirectoryEntry(
        entry_urn=SourceURN("URN:SRC:1925:NH_CONCORD:CITY_DIR_P214_E02"),
        entry_id=e1.entry_id,
        name_verbatim="Dup GUID",
    )
    with pytest.raises(ModelFormatError, match="Duplicate DirectoryEntry entry_id"):
        DirectoryRollRecord(
            source_id=valid_source_id,
            source_urn=valid_dir_urn,
            record_category=SourceRecordCategory.DIRECTORY,
            description="Dup GUID",
            repository_id=valid_repo_id,
            audit=valid_audit,
            enumeration_year=HistoricalYear(1925),
            jurisdiction_raw="Concord, NH",
            publication_title_raw="Concord Directory",
            entries=(e1, dup_guid),
        )
