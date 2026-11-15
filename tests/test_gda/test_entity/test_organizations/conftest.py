"""Path: tests/test_gda/test_entity/test_organizations/conftest.py

Shared directory-scoped test fixtures for gda.entity.organizations test suites.
Inherits mock_locations_collection and mock_sites_collection from
tests/test_gda/test_entity/conftest.py.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest

from gda.core.enums.orgs import OrganizationCategory
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import LocationID, OrganizationID, SiteID
from gda.model.base.audit import AuditStamp
from gda.model.base.name import NameThing
from gda.model.base.tombstone import Tombstone
from gda.model.entity.organization import Organization

__version__ = "1.0.0+build.2"


@pytest.fixture
def make_organization() -> Callable[..., Organization]:
    """Factory fixture building validated Organization entities with sensible defaults."""

    def _factory(
        org_id: str = "ORG-000001",
        name: str = "VFW Post 411",
        category: OrganizationCategory = OrganizationCategory.VETERANS,
        canonical_urn: str | None = None,
        parent_org_id: str | None = None,
        predecessor_ids: list[str] | None = None,
        successor_ids: list[str] | None = None,
        location_id: str | None = "LOC-000001",
        meeting_site_id: str | None = "SID-000001",
        tombstone: Tombstone[OrganizationID] | None = None,
        **kwargs: Any,
    ) -> Organization:
        now = IsoTimestamp("2026-11-15T12:00:00Z")
        audit = AuditStamp(created_at=now, updated_at=now)
        urn = canonical_urn or f"urn:gda:org:us:nh:bow:post_{org_id.lower().replace('-', '_')}"
        return Organization.create(
            org_id=OrganizationID(org_id),
            audit=audit,
            name=NameThing.create(raw=name, canonical=name),
            category=category,
            canonical_urn=urn,
            parent_org_id=OrganizationID(parent_org_id) if parent_org_id else None,
            predecessor_ids=[OrganizationID(p) for p in predecessor_ids] if predecessor_ids else [],
            successor_ids=[OrganizationID(s) for s in successor_ids] if successor_ids else [],
            location_id=LocationID(location_id) if location_id else None,
            meeting_site_id=SiteID(meeting_site_id) if meeting_site_id else None,
            tombstone=tombstone or Tombstone[OrganizationID](),
            **kwargs,
        )

    return _factory


@pytest.fixture
def active_organization(make_organization: Callable[..., Organization]) -> Organization:
    """Return a default active standalone VFW Post Organization."""
    return make_organization("ORG-000001")


@pytest.fixture
def tombstoned_organization(make_organization: Callable[..., Organization]) -> Organization:
    """Return a default retired Organization."""
    now = IsoTimestamp("2026-11-15T12:00:00Z")
    tomb = Tombstone[OrganizationID]().retire(timestamp=now)
    return make_organization("ORG-000002", tombstone=tomb)
