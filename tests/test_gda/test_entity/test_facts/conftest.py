"""Path: tests/test_gda/test_entity/test_facts/conftest.py

Shared directory-scoped test fixtures for gda.entity.facts test suites.
Inherits mock_locations_collection, mock_sites_collection,
mock_individuals_collection, and mock_families_collection from
tests/test_gda/test_entity/conftest.py.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest

from gda.core.enums.core import AssociatedRole, FactType
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import FactID, FamilyID, IndividualID, LocationID, SiteID
from gda.model.base.audit import AuditStamp
from gda.model.base.tombstone import Tombstone
from gda.model.entity.fact import Fact, FactParticipant

__version__ = "1.0.0+build.2"


@pytest.fixture
def make_fact() -> Callable[..., Fact]:
    """Factory fixture building validated Fact entities with sensible defaults."""

    def _factory(
        fact_id: str = "FID-000001",
        fact_type: FactType = FactType.BIRTH,
        title: str = "Birth of John Quincy Adams",
        primary_subject_id: str | IndividualID | FamilyID = "IND-000001",
        canonical_urn: str | None = None,
        date: Any = "1842-05-14",
        location_id: str | None = "LOC-000001",
        site_id: str | None = "SID-000001",
        participants: list[FactParticipant | dict[str, Any]] | None = None,
        tombstone: Tombstone[FactID] | None = None,
        **kwargs: Any,
    ) -> Fact:
        now = IsoTimestamp("2026-11-15T12:00:00Z")
        audit = AuditStamp(created_at=now, updated_at=now)
        urn = canonical_urn or f"urn:gda:fact:event_{fact_id.lower().replace('-', '_')}"
        default_participants = (
            participants
            if participants is not None
            else [FactParticipant.create("IND-000010", AssociatedRole.WITNESS)]
        )
        return Fact.create(
            fact_id=FactID(fact_id),
            canonical_urn=urn,
            fact_type=fact_type,
            title=title,
            primary_subject_id=primary_subject_id,
            date=date,
            location_id=LocationID(location_id) if location_id else None,
            site_id=SiteID(site_id) if site_id else None,
            participants=default_participants,
            audit=audit,
            tombstone=tombstone or Tombstone[FactID](),
            **kwargs,
        )

    return _factory


@pytest.fixture
def active_fact(make_fact: Callable[..., Fact]) -> Fact:
    """Return a default active Fact entity."""
    return make_fact("FID-000001")


@pytest.fixture
def tombstoned_fact(make_fact: Callable[..., Fact]) -> Fact:
    """Return a default retired Fact entity."""
    now = IsoTimestamp("2026-11-15T12:00:00Z")
    tomb = Tombstone[FactID]().retire(timestamp=now)
    return make_fact("FID-000002", tombstone=tomb)
