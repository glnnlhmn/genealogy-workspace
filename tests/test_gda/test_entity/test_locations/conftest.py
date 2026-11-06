"""Path: tests/test_gda/test_entity/test_locations/conftest.py

Shared pytest fixtures for the locations domain test suite.

Operational Role:
    Supplies isolated, synthetic Location and Locations fixtures representing
    valid multi-tier hierarchies, cyclic dependencies, independent city edge
    cases, and graveyard tombstone topologies.
"""

from __future__ import annotations

import pytest

from gda.entity.locations.collection import Locations
from gda.enums.location import JurisdictionCategory
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import LocationID
from gda.model.base.audit import AuditStamp
from gda.model.base.name import NameThing
from gda.model.base.tombstone import Tombstone
from gda.model.entity.location import Location

__version__ = "1.0.0+build.6"


@pytest.fixture
def base_audit() -> AuditStamp:
    """Provide a consistent audit stamp for synthetic test locations."""
    now = IsoTimestamp.now_utc()
    return AuditStamp(created_at=now, updated_at=now)


@pytest.fixture
def empty_collection() -> Locations:
    """Provide a fresh, empty in-memory Locations collection."""
    return Locations()


@pytest.fixture
def populated_collection(base_audit: AuditStamp) -> Locations:
    """Provide a pre-populated 5-tier location collection."""
    col = Locations()

    usa = Location.create(
        location_id=LocationID("LOC-000001"),
        audit=base_audit,
        name=NameThing.create(raw="United States", canonical="United States"),
        category=JurisdictionCategory.COUNTRY,
        canonical_urn="urn:gda:loc:united_states",
        tombstone=Tombstone[LocationID](),
    )
    nh = Location.create(
        location_id=LocationID("LOC-000002"),
        audit=base_audit,
        name=NameThing.create(raw="New Hampshire", canonical="New Hampshire"),
        category=JurisdictionCategory.STATOID,
        canonical_urn="urn:gda:loc:united_states:nh",
        parent_id=usa.id,
        tombstone=Tombstone[LocationID](),
    )
    merrimack = Location.create(
        location_id=LocationID("LOC-000003"),
        audit=base_audit,
        name=NameThing.create(raw="Merrimack", canonical="Merrimack"),
        category=JurisdictionCategory.COUNTY_EQUIVALENT,
        canonical_urn="urn:gda:loc:united_states:nh:merrimack",
        parent_id=nh.id,
        tombstone=Tombstone[LocationID](),
    )
    bow = Location.create(
        location_id=LocationID("LOC-000004"),
        audit=base_audit,
        name=NameThing.create(raw="Bow", canonical="Bow"),
        category=JurisdictionCategory.CIVIL_TOWNSHIP,
        canonical_urn="urn:gda:loc:united_states:nh:merrimack:bow",
        parent_id=merrimack.id,
        is_primary_local_authority=True,
        tombstone=Tombstone[LocationID](),
    )
    center = Location.create(
        location_id=LocationID("LOC-000005"),
        audit=base_audit,
        name=NameThing.create(raw="Center", canonical="Center"),
        category=JurisdictionCategory.MUNICIPALITY,
        canonical_urn="urn:gda:loc:united_states:nh:merrimack:bow:center",
        parent_id=bow.id,
        tombstone=Tombstone[LocationID](),
    )

    for loc in (usa, nh, merrimack, bow, center):
        col.add(loc)

    col.mark_clean()
    return col


@pytest.fixture
def valid_hierarchy_collection(base_audit: AuditStamp) -> Locations:
    """Construct an acyclic 5-tier authoritative jurisdictional hierarchy (Pattern 5)."""
    col = Locations()

    c = Location.create(
        location_id=LocationID("LOC-000001"),
        audit=base_audit,
        name=NameThing.create(raw="United States", canonical="United States"),
        category=JurisdictionCategory.COUNTRY,
        canonical_urn="urn:gda:loc:united_states",
        tombstone=Tombstone[LocationID](),
    )
    s = Location.create(
        location_id=LocationID("LOC-000002"),
        audit=base_audit,
        name=NameThing.create(raw="New Hampshire", canonical="New Hampshire"),
        category=JurisdictionCategory.STATOID,
        canonical_urn="urn:gda:loc:united_states:nh",
        parent_id=c.id,
        tombstone=Tombstone[LocationID](),
    )
    co = Location.create(
        location_id=LocationID("LOC-000003"),
        audit=base_audit,
        name=NameThing.create(raw="Merrimack", canonical="Merrimack"),
        category=JurisdictionCategory.COUNTY_EQUIVALENT,
        canonical_urn="urn:gda:loc:united_states:nh:merrimack",
        parent_id=s.id,
        tombstone=Tombstone[LocationID](),
    )
    twp = Location.create(
        location_id=LocationID("LOC-000004"),
        audit=base_audit,
        name=NameThing.create(raw="Bow", canonical="Bow"),
        category=JurisdictionCategory.CIVIL_TOWNSHIP,
        canonical_urn="urn:gda:loc:united_states:nh:merrimack:bow",
        parent_id=co.id,
        tombstone=Tombstone[LocationID](),
    )
    m = Location.create(
        location_id=LocationID("LOC-000005"),
        audit=base_audit,
        name=NameThing.create(raw="Bow Center", canonical="Bow Center"),
        category=JurisdictionCategory.MUNICIPALITY,
        canonical_urn="urn:gda:loc:united_states:nh:merrimack:bow:center",
        parent_id=twp.id,
        tombstone=Tombstone[LocationID](),
    )

    for item in (c, s, co, twp, m):
        col.add(item)

    col.mark_clean()
    return col


@pytest.fixture
def consecutive_multi_child_collection(base_audit: AuditStamp) -> Locations:
    """Construct a collection containing multiple consecutive non-country children."""
    col = Locations()

    c = Location.create(
        location_id=LocationID("LOC-000001"),
        audit=base_audit,
        name=NameThing.create(raw="United States", canonical="United States"),
        category=JurisdictionCategory.COUNTRY,
        canonical_urn="urn:gda:loc:united_states",
        tombstone=Tombstone[LocationID](),
    )
    s1 = Location.create(
        location_id=LocationID("LOC-000002"),
        audit=base_audit,
        name=NameThing.create(raw="New Hampshire", canonical="New Hampshire"),
        category=JurisdictionCategory.STATOID,
        canonical_urn="urn:gda:loc:united_states:nh",
        parent_id=c.id,
        tombstone=Tombstone[LocationID](),
    )
    s2 = Location.create(
        location_id=LocationID("LOC-000003"),
        audit=base_audit,
        name=NameThing.create(raw="Vermont", canonical="Vermont"),
        category=JurisdictionCategory.STATOID,
        canonical_urn="urn:gda:loc:united_states:vt",
        parent_id=c.id,
        tombstone=Tombstone[LocationID](),
    )
    s3 = Location.create(
        location_id=LocationID("LOC-000004"),
        audit=base_audit,
        name=NameThing.create(raw="Maine", canonical="Maine"),
        category=JurisdictionCategory.STATOID,
        canonical_urn="urn:gda:loc:united_states:me",
        parent_id=c.id,
        tombstone=Tombstone[LocationID](),
    )
    co1 = Location.create(
        location_id=LocationID("LOC-000005"),
        audit=base_audit,
        name=NameThing.create(raw="Merrimack", canonical="Merrimack"),
        category=JurisdictionCategory.COUNTY_EQUIVALENT,
        canonical_urn="urn:gda:loc:united_states:nh:merrimack",
        parent_id=s1.id,
        tombstone=Tombstone[LocationID](),
    )
    co2 = Location.create(
        location_id=LocationID("LOC-000006"),
        audit=base_audit,
        name=NameThing.create(raw="Belknap", canonical="Belknap"),
        category=JurisdictionCategory.COUNTY_EQUIVALENT,
        canonical_urn="urn:gda:loc:united_states:nh:belknap",
        parent_id=s1.id,
        tombstone=Tombstone[LocationID](),
    )

    for item in (c, s1, s2, s3, co1, co2):
        col.add(item)

    col.mark_clean()
    return col


@pytest.fixture
def independent_city_collection(base_audit: AuditStamp) -> Locations:
    """Construct an authoritative Pattern 7 hierarchy (skipping County and Township)."""
    col = Locations()

    c = Location.create(
        location_id=LocationID("LOC-000001"),
        audit=base_audit,
        name=NameThing.create(raw="United States", canonical="United States"),
        category=JurisdictionCategory.COUNTRY,
        canonical_urn="urn:gda:loc:united_states",
        tombstone=Tombstone[LocationID](),
    )
    s = Location.create(
        location_id=LocationID("LOC-000002"),
        audit=base_audit,
        name=NameThing.create(raw="Virginia", canonical="Virginia"),
        category=JurisdictionCategory.STATOID,
        canonical_urn="urn:gda:loc:united_states:va",
        parent_id=c.id,
        tombstone=Tombstone[LocationID](),
    )
    m = Location.create(
        location_id=LocationID("LOC-000003"),
        audit=base_audit,
        name=NameThing.create(raw="Richmond", canonical="Richmond"),
        category=JurisdictionCategory.MUNICIPALITY,
        canonical_urn="urn:gda:loc:united_states:va:richmond",
        parent_id=s.id,
        tombstone=Tombstone[LocationID](),
    )

    for item in (c, s, m):
        col.add(item)

    col.mark_clean()
    return col


@pytest.fixture
def cyclic_collection(base_audit: AuditStamp) -> Locations:
    """Construct an invalid collection containing a 3-hop parent cycle."""
    col = Locations()

    loc1 = Location.create(
        location_id=LocationID("LOC-000001"),
        audit=base_audit,
        name=NameThing.create(raw="Node 1", canonical="Node 1"),
        category=JurisdictionCategory.STATOID,
        canonical_urn="urn:gda:loc:node1",
        parent_id=LocationID("LOC-000003"),
        tombstone=Tombstone[LocationID](),
    )
    loc2 = Location.create(
        location_id=LocationID("LOC-000002"),
        audit=base_audit,
        name=NameThing.create(raw="Node 2", canonical="Node 2"),
        category=JurisdictionCategory.STATOID,
        canonical_urn="urn:gda:loc:node2",
        parent_id=LocationID("LOC-000001"),
        tombstone=Tombstone[LocationID](),
    )
    loc3 = Location.create(
        location_id=LocationID("LOC-000003"),
        audit=base_audit,
        name=NameThing.create(raw="Node 3", canonical="Node 3"),
        category=JurisdictionCategory.STATOID,
        canonical_urn="urn:gda:loc:node3",
        parent_id=LocationID("LOC-000002"),
        tombstone=Tombstone[LocationID](),
    )

    col._registry[loc1.id] = loc1
    col._registry[loc2.id] = loc2
    col._registry[loc3.id] = loc3

    return col


@pytest.fixture
def floating_island_collection(base_audit: AuditStamp) -> Locations:
    """Construct an orphan subtree whose root is not a COUNTRY."""
    col = Locations()

    s = Location.create(
        location_id=LocationID("LOC-000002"),
        audit=base_audit,
        name=NameThing.create(raw="Island Statoid", canonical="Island Statoid"),
        category=JurisdictionCategory.STATOID,
        canonical_urn="urn:gda:loc:island_statoid",
        parent_id=None,
        tombstone=Tombstone[LocationID](),
    )
    co = Location.create(
        location_id=LocationID("LOC-000003"),
        audit=base_audit,
        name=NameThing.create(raw="Island County", canonical="Island County"),
        category=JurisdictionCategory.COUNTY_EQUIVALENT,
        canonical_urn="urn:gda:loc:island_statoid:county",
        parent_id=s.id,
        tombstone=Tombstone[LocationID](),
    )

    col.add(s)
    col.add(co)
    return col


@pytest.fixture
def tombstone_violation_collection(base_audit: AuditStamp) -> Locations:
    """Construct a collection where an active entity descends from a tombstone."""
    col = Locations()

    c = Location.create(
        location_id=LocationID("LOC-000001"),
        audit=base_audit,
        name=NameThing.create(raw="United States", canonical="United States"),
        category=JurisdictionCategory.COUNTRY,
        canonical_urn="urn:gda:loc:united_states",
        tombstone=Tombstone[LocationID](),
    )
    s = Location.create(
        location_id=LocationID("LOC-000002"),
        audit=base_audit,
        name=NameThing.create(raw="Old Province", canonical="Old Province"),
        category=JurisdictionCategory.STATOID,
        canonical_urn="urn:gda:loc:united_states:old_prov",
        parent_id=c.id,
        tombstone=Tombstone[LocationID]().retire(timestamp=base_audit.created_at),
    )
    co = Location.create(
        location_id=LocationID("LOC-000003"),
        audit=base_audit,
        name=NameThing.create(raw="Active County", canonical="Active County"),
        category=JurisdictionCategory.COUNTY_EQUIVALENT,
        canonical_urn="urn:gda:loc:united_states:old_prov:county",
        parent_id=s.id,
        tombstone=Tombstone[LocationID](),
    )

    col.add(c)
    col._registry[s.id] = s
    col.add(co)
    return col


@pytest.fixture
def desynchronized_index_collection(base_audit: AuditStamp) -> Locations:
    """Construct a collection where URN index mappings conflict with the registry."""
    col = Locations()

    c = Location.create(
        location_id=LocationID("LOC-000001"),
        audit=base_audit,
        name=NameThing.create(raw="United States", canonical="United States"),
        category=JurisdictionCategory.COUNTRY,
        canonical_urn="urn:gda:loc:united_states",
        tombstone=Tombstone[LocationID](),
    )
    col.add(c)
    col._urn_index[c.canonical_urn] = LocationID("LOC-999999")
    return col
