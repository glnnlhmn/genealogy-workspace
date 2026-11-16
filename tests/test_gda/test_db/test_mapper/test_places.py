"""Path: tests/test_gda/test_db/test_mapper/test_places.py

Unit and regression verification suite for LocationRowMapper and SiteRowMapper.

Operational Role:
    1:1 verification suite for src/gda/db/mapper/places.py. Validates lossless
    round-trip mapping for Location and Site entities (with and without Address,
    Coordinates, and TimePeriod) and EntityMappingError boundaries.
"""

from __future__ import annotations

import pytest

import gda.db.mapper.places as places_mod
from gda.core.enums.archival import NoteType
from gda.core.enums.location import JurisdictionCategory
from gda.core.enums.site import SiteType
from gda.db.exceptions import EntityMappingError
from gda.db.mapper.places import LocationRowMapper, SiteRowMapper
from gda.model.atom.date import DateString, IsoTimestamp
from gda.model.atom.geo import Latitude, Longitude
from gda.model.atom.id import LocationID, SiteID
from gda.model.base.address import Address
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate, TimePeriod
from gda.model.base.geo import Coordinates
from gda.model.base.name import HistoricVariant, NameThing
from gda.model.base.note import Note
from gda.model.base.tombstone import Tombstone
from gda.model.entity.location import Location
from gda.model.entity.site import Site

__version__ = "1.0.0+build.1"


def _make_audit() -> AuditStamp:
    now = IsoTimestamp("2026-01-01T00:00:00Z")
    return AuditStamp(created_at=now, updated_at=now)


@pytest.mark.unit
def test_places_mapper_dunder_all() -> None:
    """Verify gda.db.mapper.places.__all__ is sorted."""
    assert places_mod.__all__ == ["LocationRowMapper", "SiteRowMapper"]


@pytest.mark.integration
def test_location_row_mapper_full_and_sparse_round_trip() -> None:
    """Verify LocationRowMapper round-trips full and minimal Location entities."""
    audit = _make_audit()
    dep_ts = IsoTimestamp("2026-06-15T10:30:00Z")
    coords = Coordinates(latitude=Latitude(43.13), longitude=Longitude(-71.53))
    period = TimePeriod(
        start_date=EventDate(date=DateString("1727-05-20")),
        end_date=EventDate(date=DateString("1900-01-01")),
    )
    note = Note.create(
        note_id="NOT-000001",
        note_type=NoteType.RESEARCH,
        text="Settlement founded 1727",
        audit=audit,
    )
    name_obj = NameThing.create(
        raw="Bow",
        canonical="Bow",
        aliases=["Bow Mills"],
        alt_spellings=["Bowe"],
        historic=[HistoricVariant.create(raw="Bow Town", name="Bow Town")],
        comment="Historic Merrimack township",
    )
    loc = Location.create(
        location_id="LOC-000001",
        canonical_urn="urn:gda:loc:us:nh:bow",
        name=name_obj,
        category=JurisdictionCategory.MUNICIPALITY,
        parent_id="LOC-000002",
        is_primary_local_authority=True,
        is_unincorporated=False,
        coordinates=coords,
        period=period,
        predecessor_ids=["LOC-000004"],
        successor_ids=["LOC-000005"],
        audit=audit,
        tombstone=Tombstone(
            is_deprecated=True,
            deprecated_at=dep_ts,
            superseded_by=LocationID("LOC-000009"),
        ),
        notes=[note],
    )

    mapper = LocationRowMapper()
    row_data = mapper.to_row(loc)
    assert mapper.from_row(row_data) == loc

    minimal_loc = Location.create(
        location_id="LOC-000002",
        canonical_urn="urn:gda:loc:us",
        name="United States",
        category=JurisdictionCategory.COUNTRY,
        audit=audit,
    )
    min_row = mapper.to_row(minimal_loc)
    min_row["aliases_json"] = None
    min_row["alt_spellings_json"] = None
    min_row["historical_names_json"] = None
    min_row["predecessor_ids_json"] = None
    min_row["successor_ids_json"] = None
    assert mapper.from_row(min_row) == minimal_loc


@pytest.mark.integration
def test_site_row_mapper_full_and_sparse_round_trip() -> None:
    """Verify SiteRowMapper round-trips Site entities with and without Address/Coordinates."""
    audit = _make_audit()
    coords = Coordinates(latitude=Latitude(43.2081), longitude=Longitude(-71.5376))
    addr_with_coords = Address(
        address_line_1="10 Woodhill Hook Rd",
        address_line_2="Plot Section B",
        city="Bow",
        state="NH",
        postal_code="03304",
        coordinates=coords,
    )
    period = TimePeriod(start_date=EventDate.create("1800"))
    site = Site.create(
        site_id="SID-000001",
        canonical_urn="urn:gda:site:us:nh:bow:cemetery",
        name="Old Bow Cemetery",
        category=SiteType.CEMETERY,
        location_id="LOC-000001",
        is_active=False,
        address=addr_with_coords,
        coordinates=coords,
        period=period,
        audit=audit,
        tombstone=Tombstone(
            is_deprecated=True,
            deprecated_at=audit.updated_at,
            superseded_by=SiteID("SID-000002"),
        ),
    )

    mapper = SiteRowMapper()
    row_data = mapper.to_row(site)
    assert mapper.from_row(row_data) == site

    # Site with Address without coordinates, and Site without Address at all
    addr_no_coords = Address(address_line_1="1 Main St", city="Bow", state="NH")
    site_no_addr_coords = Site.create(
        site_id="SID-000002",
        canonical_urn="urn:gda:site:us:nh:bow:hall",
        name="Bow Hall",
        category=SiteType.GOVERNMENT,
        location_id="LOC-000001",
        address=addr_no_coords,
        audit=audit,
    )
    assert mapper.from_row(mapper.to_row(site_no_addr_coords)) == site_no_addr_coords

    site_minimal = Site.create(
        site_id="SID-000003",
        canonical_urn="urn:gda:site:us:nh:bow:field",
        name="Town Field",
        category=SiteType.OTHER,
        location_id="LOC-000001",
        audit=audit,
    )
    assert mapper.from_row(mapper.to_row(site_minimal)) == site_minimal


@pytest.mark.regression
def test_places_mappers_corrupt_rows_raise_entity_mapping_error() -> None:
    """Verify LocationRowMapper and SiteRowMapper raise EntityMappingError on invalid rows."""
    with pytest.raises(EntityMappingError, match="Failed to map row to Location"):
        LocationRowMapper().from_row({"id": None})

    with pytest.raises(EntityMappingError, match="Failed to map row to Site"):
        SiteRowMapper().from_row({"id": None})
