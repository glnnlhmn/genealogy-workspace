"""Path: tests/test_gda/test_entity/conftest.py

Shared directory-scoped test fixtures for domain entity test suites.

Operational Role:
    Provides canonical, isolated entity instances, synthetic identifiers,
    and mock persistence scaffolding for tests under tests/test_gda/test_entity/.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from gda.entity.locations.collection import Locations
from gda.enums.location import JurisdictionCategory
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import LocationID
from gda.model.base.audit import AuditStamp
from gda.model.base.name import NameThing
from gda.model.base.tombstone import Tombstone
from gda.model.entity.location import Location

__version__ = "1.0.0+build.2"


@pytest.fixture
def golden_import_path() -> Path:
    """Return the filesystem path to the golden location import envelope fixture."""
    fixture_path = (
        Path(__file__).parents[4]
        / "tests"
        / "fixtures"
        / "locations"
        / "golden"
        / "location_import_envelope_golden.json"
    )
    if not fixture_path.exists():
        fixture_path = Path(
            "tests/fixtures/locations/golden/location_import_envelope_golden.json"
        )
    return fixture_path


@pytest.fixture
def sample_location() -> Location:
    """Provide a validated canonical Location entity fixture with a NameThing."""
    now = IsoTimestamp.now_utc()
    name = NameThing.create(raw="United States", canonical="United States")
    return Location(
        id=LocationID("LOC-000001"),
        audit=AuditStamp(created_at=now, updated_at=now),
        name=name,
        category=JurisdictionCategory.COUNTRY,
        canonical_urn="urn:gda:loc:united_states",
        tombstone=Tombstone[LocationID](),
    )


@pytest.fixture
def mock_db_session() -> MagicMock:
    """Provide a mock database session manager and connection context."""
    session = MagicMock()
    conn = MagicMock()
    tx = MagicMock()
    cursor = MagicMock()

    session.get_connection.return_value.__enter__.return_value = conn
    session.transaction.return_value.__enter__.return_value = tx
    conn.execute.return_value = cursor
    return session


@pytest.fixture
def valid_hierarchy_collection() -> Locations:
    """Provide a fully valid 5-tier linked acyclic collection (Pattern 5)."""
    col = Locations()
    now = IsoTimestamp.now_utc()

    c = Location(
        id=LocationID("LOC-000001"),
        audit=AuditStamp(created_at=now, updated_at=now),
        name=NameThing.create(raw="USA", canonical="USA"),
        category=JurisdictionCategory.COUNTRY,
        canonical_urn="urn:gda:loc:usa",
        tombstone=Tombstone[LocationID](),
    )
    s = Location(
        id=LocationID("LOC-000002"),
        audit=AuditStamp(created_at=now, updated_at=now),
        name=NameThing.create(raw="NH", canonical="NH"),
        category=JurisdictionCategory.STATOID,
        canonical_urn="urn:gda:loc:usa:nh",
        parent_id=c.id,
        tombstone=Tombstone[LocationID](),
    )
    co = Location(
        id=LocationID("LOC-000003"),
        audit=AuditStamp(created_at=now, updated_at=now),
        name=NameThing.create(raw="Merrimack", canonical="Merrimack"),
        category=JurisdictionCategory.COUNTY_EQUIVALENT,
        canonical_urn="urn:gda:loc:usa:nh:merrimack",
        parent_id=s.id,
        tombstone=Tombstone[LocationID](),
    )
    twp = Location(
        id=LocationID("LOC-000004"),
        audit=AuditStamp(created_at=now, updated_at=now),
        name=NameThing.create(raw="Bow", canonical="Bow"),
        category=JurisdictionCategory.CIVIL_TOWNSHIP,
        canonical_urn="urn:gda:loc:usa:nh:merrimack:bow",
        parent_id=co.id,
        is_primary_local_authority=True,
        tombstone=Tombstone[LocationID](),
    )
    m = Location(
        id=LocationID("LOC-000005"),
        audit=AuditStamp(created_at=now, updated_at=now),
        name=NameThing.create(raw="Center", canonical="Center"),
        category=JurisdictionCategory.MUNICIPALITY,
        canonical_urn="urn:gda:loc:usa:nh:merrimack:bow:center",
        parent_id=twp.id,
        tombstone=Tombstone[LocationID](),
    )
    for loc in [c, s, co, twp, m]:
        col.add(loc)
    return col


@pytest.fixture
def independent_city_collection() -> Locations:
    """Provide a valid 3-tier collection skipping county and township (Pattern 7)."""
    col = Locations()
    now = IsoTimestamp.now_utc()

    c = Location(
        id=LocationID("LOC-000001"),
        audit=AuditStamp(created_at=now, updated_at=now),
        name=NameThing.create(raw="USA", canonical="USA"),
        category=JurisdictionCategory.COUNTRY,
        canonical_urn="urn:gda:loc:usa",
        tombstone=Tombstone[LocationID](),
    )
    s = Location(
        id=LocationID("LOC-000002"),
        audit=AuditStamp(created_at=now, updated_at=now),
        name=NameThing.create(raw="Virginia", canonical="Virginia"),
        category=JurisdictionCategory.STATOID,
        canonical_urn="urn:gda:loc:usa:va",
        parent_id=c.id,
        tombstone=Tombstone[LocationID](),
    )
    m = Location(
        id=LocationID("LOC-000003"),
        audit=AuditStamp(created_at=now, updated_at=now),
        name=NameThing.create(raw="Richmond", canonical="Richmond"),
        category=JurisdictionCategory.MUNICIPALITY,
        canonical_urn="urn:gda:loc:usa:va:richmond",
        parent_id=s.id,
        tombstone=Tombstone[LocationID](),
    )
    for loc in [c, s, m]:
        col.add(loc)
    return col


@pytest.fixture
def cyclic_collection() -> Locations:
    """Provide a collection containing an indirect multi-hop cycle (A -> B -> C -> A)."""
    col = Locations()
    now = IsoTimestamp.now_utc()

    loc1 = Location(
        id=LocationID("LOC-000001"),
        audit=AuditStamp(created_at=now, updated_at=now),
        name=NameThing.create(raw="A", canonical="A"),
        category=JurisdictionCategory.STATOID,
        canonical_urn="urn:gda:loc:a",
        parent_id=LocationID("LOC-000003"),
        tombstone=Tombstone[LocationID](),
    )
    loc2 = Location(
        id=LocationID("LOC-000002"),
        audit=AuditStamp(created_at=now, updated_at=now),
        name=NameThing.create(raw="B", canonical="B"),
        category=JurisdictionCategory.STATOID,
        canonical_urn="urn:gda:loc:b",
        parent_id=LocationID("LOC-000001"),
        tombstone=Tombstone[LocationID](),
    )
    loc3 = Location(
        id=LocationID("LOC-000003"),
        audit=AuditStamp(created_at=now, updated_at=now),
        name=NameThing.create(raw="C", canonical="C"),
        category=JurisdictionCategory.STATOID,
        canonical_urn="urn:gda:loc:c",
        parent_id=LocationID("LOC-000002"),
        tombstone=Tombstone[LocationID](),
    )
    col._registry[loc1.id] = loc1
    col._registry[loc2.id] = loc2
    col._registry[loc3.id] = loc3
    return col


@pytest.fixture
def floating_island_collection() -> Locations:
    """Provide a collection with an orphan subtree lacking an authoritative COUNTRY root."""
    col = Locations()
    now = IsoTimestamp.now_utc()

    s = Location(
        id=LocationID("LOC-000001"),
        audit=AuditStamp(created_at=now, updated_at=now),
        name=NameThing.create(raw="NH", canonical="NH"),
        category=JurisdictionCategory.STATOID,
        canonical_urn="urn:gda:loc:nh",
        parent_id=None,  # Root without being COUNTRY
        tombstone=Tombstone[LocationID](),
    )
    co = Location(
        id=LocationID("LOC-000002"),
        audit=AuditStamp(created_at=now, updated_at=now),
        name=NameThing.create(raw="Merrimack", canonical="Merrimack"),
        category=JurisdictionCategory.COUNTY_EQUIVALENT,
        canonical_urn="urn:gda:loc:nh:merrimack",
        parent_id=s.id,
        tombstone=Tombstone[LocationID](),
    )
    col.add(s)
    col.add(co)
    return col


@pytest.fixture
def tombstone_violation_collection() -> Locations:
    """Provide a collection where an active node links to a deprecated ancestor."""
    col = Locations()
    now = IsoTimestamp.now_utc()

    c = Location(
        id=LocationID("LOC-000001"),
        audit=AuditStamp(created_at=now, updated_at=now),
        name=NameThing.create(raw="USA", canonical="USA"),
        category=JurisdictionCategory.COUNTRY,
        canonical_urn="urn:gda:loc:usa",
        tombstone=Tombstone[LocationID]().retire(timestamp=now),  # Deprecated
    )
    s = Location(
        id=LocationID("LOC-000002"),
        audit=AuditStamp(created_at=now, updated_at=now),
        name=NameThing.create(raw="NH", canonical="NH"),
        category=JurisdictionCategory.STATOID,
        canonical_urn="urn:gda:loc:usa:nh",
        parent_id=c.id,  # Active child of deprecated parent
        tombstone=Tombstone[LocationID](),
    )
    col._registry[c.id] = c
    col.add(s)
    return col


@pytest.fixture
def desynchronized_index_collection() -> Locations:
    """Provide a collection with an intentionally corrupted _urn_index mapping."""
    col = Locations()
    now = IsoTimestamp.now_utc()

    c = Location(
        id=LocationID("LOC-000001"),
        audit=AuditStamp(created_at=now, updated_at=now),
        name=NameThing.create(raw="USA", canonical="USA"),
        category=JurisdictionCategory.COUNTRY,
        canonical_urn="urn:gda:loc:usa",
        tombstone=Tombstone[LocationID](),
    )
    col.add(c)
    # Intentionally corrupt index pointer
    col._urn_index["urn:gda:loc:usa"] = LocationID("LOC-999999")
    return col
