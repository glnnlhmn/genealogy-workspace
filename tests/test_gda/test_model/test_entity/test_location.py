"""Path: tests/test_gda/test_model/test_entity/test_location.py

Comprehensive test suite verifying Location and jurisdictional primitives.

Operational Role:
    Verifies JurisdictionCategory, NameStatus, HistoricalName, and Location
    behavioral contracts, including temporal sequence composition, self-referential
    boundary guards, LocationID enforcement, URN formatting, sorting properties,
    and immutability invariants.

Test Structure & Protocol:
    - Atomized tests: 1:1 behavioral contract mapping.
    - Fully decorated: Standard 7-marker taxonomy.
    - Zero production disk I/O.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest
from pydantic import ValidationError

from gda.core.errors import ModelFormatError
from gda.model.atom.date import (
    DateModifier,
    DateString,
    EventDate,
    IsoTimestamp,
)
from gda.model.atom.geo import Coordinates, Latitude, Longitude
from gda.model.atom.id import FactID, LocationID, SiteID
from gda.model.base.audit import AuditStamp
from gda.model.base.name import HistoricalName, NameStatus
from gda.model.base.time_period import TimePeriod
from gda.model.base.tombstone import TombstoneRecord
from gda.model.entity.location import (
    JurisdictionCategory,
    Location,
)

__version__ = "1.0.0+build.24"


# ==============================================================================
# FIXTURES: GOLDEN PAYLOADS & BASE INSTANCES
# ==============================================================================


@pytest.fixture
def golden_timestamp() -> IsoTimestamp:
    """Fixture providing a standard test timestamp."""
    return IsoTimestamp("2026-10-16T12:00:00Z")


@pytest.fixture
def golden_audit(golden_timestamp: IsoTimestamp) -> AuditStamp:
    """Fixture providing a standard audit stamp."""
    return AuditStamp(created_at=golden_timestamp, updated_at=golden_timestamp)


@pytest.fixture
def golden_period() -> TimePeriod:
    """Fixture providing a standard bounded temporal period."""
    return TimePeriod(
        start_date=EventDate(date=DateString("1727"), modifier=DateModifier.EXACT),
        end_date=EventDate(date=DateString("1900"), modifier=DateModifier.EXACT),
    )


@pytest.fixture
def golden_location(golden_audit: AuditStamp, golden_period: TimePeriod) -> Location:
    """Fixture providing a complete standard Location instance."""
    loc_id = LocationID("LOC-000004")
    parent_id = LocationID("LOC-000003")
    coords = Coordinates(latitude=Latitude(43.1319), longitude=Longitude(-71.5497))
    hn = HistoricalName(raw_name="Bow Mills", status=NameStatus.COLLOQUIAL)

    return Location(
        id=loc_id,
        audit=golden_audit,
        name="Bow",
        category=JurisdictionCategory.CIVIL_TOWNSHIP,
        canonical_urn="urn:gda:loc:us:nh:merrimack:bow",
        parent_id=parent_id,
        historical_names=[hn],
        alternate_names=["Bow Town"],
        is_primary_local_authority=True,
        is_unincorporated=False,
        period=golden_period,
        coordinates=coords,
    )


# ==============================================================================
# GROUP 1: ENUMERATIONS & JURISDICTION RANKINGS
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_jurisdiction_category_members_and_ranks() -> None:
    """Verify JurisdictionCategory enum values and hierarchical administrative rank ordering."""
    assert JurisdictionCategory.COUNTRY.administrative_rank == 10
    assert JurisdictionCategory.STATOID.administrative_rank == 20
    assert JurisdictionCategory.COUNTY_EQUIVALENT.administrative_rank == 30
    assert JurisdictionCategory.CIVIL_TOWNSHIP.administrative_rank == 40
    assert JurisdictionCategory.MUNICIPALITY.administrative_rank == 40
    assert JurisdictionCategory.UNINCORPORATED_PLACE.administrative_rank == 50
    assert JurisdictionCategory.SPECIAL_DISTRICT.administrative_rank == 60


# ==============================================================================
# GROUP 2: LOCATION CREATION & ATTRIBUTES
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_location_valid_creation(
    golden_location: Location, golden_audit: AuditStamp, golden_period: TimePeriod
) -> None:
    """Verify Location instantiates with complete domain attributes and delegated properties."""
    loc = golden_location
    assert loc.id == LocationID("LOC-000004")
    assert loc.audit == golden_audit
    assert loc.created_at == golden_audit.created_at
    assert loc.updated_at == golden_audit.updated_at
    assert loc.name == "Bow"
    assert loc.category == JurisdictionCategory.CIVIL_TOWNSHIP
    assert loc.canonical_urn == "urn:gda:loc:us:nh:merrimack:bow"
    assert loc.parent_id == LocationID("LOC-000003")
    assert len(loc.historical_names) == 1
    assert loc.historical_names[0].raw_name == "Bow Mills"
    assert loc.alternate_names == ["Bow Town"]
    assert loc.is_primary_local_authority is True
    assert loc.is_unincorporated is False
    assert loc.period == golden_period
    assert loc.coordinates is not None
    assert loc.is_deprecated is False
    assert loc.category_rank == 40
    assert loc.sort_key == (40, "bow")


@pytest.mark.unit
@pytest.mark.smoke
def test_location_string_representation(golden_location: Location) -> None:
    """Verify Location renders concise human-readable string representation."""
    assert str(golden_location) == "Bow [CIVIL_TOWNSHIP] (LOC-000004)"


# ==============================================================================
# GROUP 3: DEFENSIVE BOUNDARIES & VALIDATIONS
# ==============================================================================


@pytest.mark.unit
@pytest.mark.regression
@pytest.mark.parametrize(
    "bad_id_str",
    [
        "LOC-12345",
        "LOC-1234567",
        "LOC-ABCDEF",
        "000001",
        "",
    ],
)
def test_location_invalid_location_id_raises_format_error(
    bad_id_str: str, golden_audit: AuditStamp
) -> None:
    """Verify malformed LocationID values raise ModelFormatError when constructed."""
    try:
        bad_id = LocationID(bad_id_str)
        with pytest.raises(ModelFormatError, match="Invalid LocationID format"):
            Location(
                id=bad_id,
                audit=golden_audit,
                name="Invalid ID Town",
                category=JurisdictionCategory.CIVIL_TOWNSHIP,
                canonical_urn="urn:gda:loc:us:nh:invalid",
            )
    except ModelFormatError:
        pass


@pytest.mark.unit
@pytest.mark.regression
def test_location_conflicting_atom_id_type_raises_error(
    golden_audit: AuditStamp,
) -> None:
    """Verify Location rejects foreign AtomID subclasses assigned to id."""
    wrong_id = FactID("FID-000001")
    with pytest.raises((TypeError, ValidationError)):
        Location(
            id=wrong_id,  # type: ignore[arg-type]
            audit=golden_audit,
            name="Mismatched ID Town",
            category=JurisdictionCategory.CIVIL_TOWNSHIP,
            canonical_urn="urn:gda:loc:us:nh:wrong_id",
        )


@pytest.mark.unit
@pytest.mark.regression
@pytest.mark.parametrize("blank_name", ["", "   ", "\t\n"])
def test_location_blank_name_raises_format_error(
    blank_name: str, golden_audit: AuditStamp
) -> None:
    """Verify Location raises ModelFormatError if name is blank."""
    with pytest.raises(ModelFormatError, match="'name' cannot be empty or whitespace"):
        Location(
            id=LocationID("LOC-000001"),
            audit=golden_audit,
            name=blank_name,
            category=JurisdictionCategory.COUNTRY,
            canonical_urn="urn:gda:loc:us",
        )


@pytest.mark.unit
@pytest.mark.regression
@pytest.mark.parametrize(
    "invalid_urn",
    [
        "",
        "   ",
        "urn:gda:site:us:nh:bow",
        "urn:loc:us:nh:bow",
        "URN:GDA:LOC:US:NH",
        "urn:gda:loc:invalid char",
    ],
)
def test_location_invalid_urn_raises_format_error(
    invalid_urn: str, golden_audit: AuditStamp
) -> None:
    """Verify Location raises ModelFormatError when canonical_urn is malformed."""
    with pytest.raises(ModelFormatError, match="Invalid canonical_urn format"):
        Location(
            id=LocationID("LOC-000001"),
            audit=golden_audit,
            name="United States",
            category=JurisdictionCategory.COUNTRY,
            canonical_urn=invalid_urn,
        )


@pytest.mark.unit
@pytest.mark.regression
def test_location_self_parent_raises_format_error(golden_audit: AuditStamp) -> None:
    """Verify Location raises ModelFormatError if parent_id equals id."""
    loc_id = LocationID("LOC-000001")
    with pytest.raises(ModelFormatError, match="cannot be its own parent"):
        Location(
            id=loc_id,
            audit=golden_audit,
            name="Circular State",
            category=JurisdictionCategory.STATOID,
            canonical_urn="urn:gda:loc:us:cs",
            parent_id=loc_id,
        )


@pytest.mark.unit
@pytest.mark.regression
def test_location_foreign_parent_id_type_raises_error(golden_audit: AuditStamp) -> None:
    """Verify Location raises TypeError or ValidationError if parent_id is not a LocationID."""
    wrong_parent = SiteID("SID-000001")
    with pytest.raises((TypeError, ValidationError)):
        Location(
            id=LocationID("LOC-000001"),
            audit=golden_audit,
            name="Child Town",
            category=JurisdictionCategory.CIVIL_TOWNSHIP,
            canonical_urn="urn:gda:loc:us:nh:ct",
            parent_id=wrong_parent,  # type: ignore[arg-type]
        )


@pytest.mark.unit
@pytest.mark.regression
def test_location_self_referential_associated_jurisdiction_raises_format_error(
    golden_audit: AuditStamp,
) -> None:
    """Verify Location rejects self-references in associated_jurisdiction_ids."""
    loc_id = LocationID("LOC-000005")
    with pytest.raises(
        ModelFormatError, match="cannot reference itself in associated_jurisdiction_ids"
    ):
        Location(
            id=loc_id,
            audit=golden_audit,
            name="Boundary Town",
            category=JurisdictionCategory.CIVIL_TOWNSHIP,
            canonical_urn="urn:gda:loc:us:nh:bt",
            associated_jurisdiction_ids=[loc_id],
        )


@pytest.mark.unit
@pytest.mark.regression
def test_location_self_referential_predecessor_ids_raises_format_error(
    golden_audit: AuditStamp,
) -> None:
    """Verify Location rejects self-references in predecessor_ids."""
    loc_id = LocationID("LOC-000005")
    with pytest.raises(
        ModelFormatError, match="cannot reference itself in predecessor_ids"
    ):
        Location(
            id=loc_id,
            audit=golden_audit,
            name="Boundary Town",
            category=JurisdictionCategory.CIVIL_TOWNSHIP,
            canonical_urn="urn:gda:loc:us:nh:bt",
            predecessor_ids=[loc_id],
        )


@pytest.mark.unit
@pytest.mark.regression
def test_location_self_referential_successor_ids_raises_format_error(
    golden_audit: AuditStamp,
) -> None:
    """Verify Location rejects self-references in successor_ids."""
    loc_id = LocationID("LOC-000005")
    with pytest.raises(
        ModelFormatError, match="cannot reference itself in successor_ids"
    ):
        Location(
            id=loc_id,
            audit=golden_audit,
            name="Boundary Town",
            category=JurisdictionCategory.CIVIL_TOWNSHIP,
            canonical_urn="urn:gda:loc:us:nh:bt",
            successor_ids=[loc_id],
        )


@pytest.mark.unit
@pytest.mark.regression
def test_location_duplicate_relational_ids_raise_format_error(
    golden_audit: AuditStamp,
) -> None:
    """Verify duplicate IDs in graph collections raise ModelFormatError."""
    other_id = LocationID("LOC-000099")

    with pytest.raises(
        ModelFormatError, match="Duplicate entries found in associated_jurisdiction_ids"
    ):
        Location(
            id=LocationID("LOC-000010"),
            audit=golden_audit,
            name="Split Town",
            category=JurisdictionCategory.CIVIL_TOWNSHIP,
            canonical_urn="urn:gda:loc:us:nh:st",
            associated_jurisdiction_ids=[other_id, other_id],
        )

    with pytest.raises(
        ModelFormatError, match="Duplicate entries found in predecessor_ids"
    ):
        Location(
            id=LocationID("LOC-000010"),
            audit=golden_audit,
            name="Split Town",
            category=JurisdictionCategory.CIVIL_TOWNSHIP,
            canonical_urn="urn:gda:loc:us:nh:st",
            predecessor_ids=[other_id, other_id],
        )

    with pytest.raises(
        ModelFormatError, match="Duplicate entries found in successor_ids"
    ):
        Location(
            id=LocationID("LOC-000010"),
            audit=golden_audit,
            name="Split Town",
            category=JurisdictionCategory.CIVIL_TOWNSHIP,
            canonical_urn="urn:gda:loc:us:nh:st",
            successor_ids=[other_id, other_id],
        )


@pytest.mark.unit
@pytest.mark.regression
def test_location_tombstone_superseded_by_type_mismatch_raises_type_error(
    golden_audit: AuditStamp, golden_timestamp: IsoTimestamp
) -> None:
    """Verify Location raises TypeError via BaseEntity if tombstone superseded_by is not a LocationID."""
    loc_id = LocationID("LOC-000001")
    wrong_id = FactID("FID-000002")

    tombstone = TombstoneRecord(
        is_deprecated=True,
        deprecated_at=golden_timestamp,
        superseded_by=wrong_id,  # type: ignore[arg-type]
    )

    with pytest.raises(TypeError, match="superseded_by type mismatch"):
        Location(
            id=loc_id,
            audit=golden_audit,
            name="Merged Town",
            category=JurisdictionCategory.CIVIL_TOWNSHIP,
            canonical_urn="urn:gda:loc:us:nh:mt",
            tombstone=tombstone,
        )


@pytest.mark.unit
@pytest.mark.regression
def test_location_tombstone_self_superseded_raises_error(
    golden_audit: AuditStamp, golden_timestamp: IsoTimestamp
) -> None:
    """Verify Location rejects a tombstone where superseded_by points to itself."""
    loc_id = LocationID("LOC-000001")
    tombstone = TombstoneRecord(
        is_deprecated=True,
        deprecated_at=golden_timestamp,
        superseded_by=loc_id,
    )
    with pytest.raises(ModelFormatError, match="cannot be superseded by itself"):
        Location(
            id=loc_id,
            audit=golden_audit,
            name="Dead Town",
            category=JurisdictionCategory.CIVIL_TOWNSHIP,
            canonical_urn="urn:gda:loc:us:nh:dt",
            tombstone=tombstone,
        )


# ==============================================================================
# GROUP 4: SORTING, IMMUTABILITY & INTROSPECTION
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_location_sorting_by_administrative_rank_and_name(
    golden_audit: AuditStamp,
) -> None:
    """Verify locations sort deterministically by administrative rank and then alphabetically."""
    us = Location(
        id=LocationID("LOC-000001"),
        audit=golden_audit,
        name="United States",
        category=JurisdictionCategory.COUNTRY,
        canonical_urn="urn:gda:loc:us",
    )
    nh = Location(
        id=LocationID("LOC-000002"),
        audit=golden_audit,
        name="New Hampshire",
        category=JurisdictionCategory.STATOID,
        canonical_urn="urn:gda:loc:us:nh",
    )
    merrimack = Location(
        id=LocationID("LOC-000003"),
        audit=golden_audit,
        name="Merrimack",
        category=JurisdictionCategory.COUNTY_EQUIVALENT,
        canonical_urn="urn:gda:loc:us:nh:merrimack",
    )
    bow = Location(
        id=LocationID("LOC-000004"),
        audit=golden_audit,
        name="Bow",
        category=JurisdictionCategory.CIVIL_TOWNSHIP,
        canonical_urn="urn:gda:loc:us:nh:merrimack:bow",
    )
    concord = Location(
        id=LocationID("LOC-000005"),
        audit=golden_audit,
        name="Concord",
        category=JurisdictionCategory.CIVIL_TOWNSHIP,
        canonical_urn="urn:gda:loc:us:nh:merrimack:concord",
    )

    unsorted = [concord, us, bow, merrimack, nh]
    sorted_locs = sorted(unsorted, key=lambda loc: loc.sort_key)

    assert sorted_locs == [us, nh, merrimack, bow, concord]


@pytest.mark.unit
def test_location_entity_immutability(golden_location: Location) -> None:
    """Verify Location instances are frozen and immutable."""
    with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
        golden_location.name = "New Name"  # type: ignore[misc]


@pytest.mark.unit
def test_location_entity_introspection(golden_location: Location) -> None:
    """Verify .help() introspection renders member directory on Location."""
    help_text = golden_location.help(as_str=True)
    assert help_text is not None
    assert "=== Location Public Directory ===" in help_text
    assert "category_rank" in help_text
    assert "sort_key" in help_text
    assert "created_at" in help_text
    assert "updated_at" in help_text
    assert "is_deprecated" in help_text
