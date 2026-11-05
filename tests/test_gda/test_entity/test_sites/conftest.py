"""Path: tests/test_gda/test_entity/test_sites/conftest.py

Shared pytest fixtures and test doubles for the sites entity subsystem test suite.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from gda.enums.site import SiteType
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import LocationID, SiteID
from gda.model.base.address import Address
from gda.model.base.name import NameThing
from gda.model.base.tombstone import Tombstone
from gda.model.entity.site import Site

__version__ = "1.0.0+build.2"


@pytest.fixture
def make_site():
    """Factory fixture generating deterministic synthetic Site entities."""

    def _factory(
        site_id: str = "SID-000001",
        name: str = "Old First Church",
        category: SiteType = SiteType.CHURCH,
        urn: str = "urn:gda:site:us:nh:bow:church_s000001",
        location_id: str = "LOC-000001",
        address: Address | None = None,
        tombstone: Tombstone[SiteID] | None = None,
    ) -> Site:
        return Site.create(
            site_id=SiteID(site_id),
            name=NameThing.create(raw=name, canonical=name),
            category=category,
            canonical_urn=urn,
            location_id=LocationID(location_id),
            address=address,
            tombstone=tombstone,
        )

    return _factory


@pytest.fixture
def active_site(make_site) -> Site:
    """Fixture providing a standard active Site domain entity."""
    return make_site(site_id="SID-000001")


@pytest.fixture
def tombstoned_site(make_site) -> Site:
    """Fixture providing a soft-deprecated Site domain entity."""
    now = IsoTimestamp.now_utc()
    tomb = Tombstone[SiteID]().retire(timestamp=now)
    return make_site(site_id="SID-000002", tombstone=tomb)


@pytest.fixture
def mock_locations_collection():
    """Mock Locations collection fixture answering foreign key lookups."""
    mock = MagicMock()
    mock.__contains__.return_value = True
    return mock
