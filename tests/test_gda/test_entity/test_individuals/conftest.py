"""Path: tests/test_gda/test_entity/test_individuals/conftest.py

Shared directory-scoped test fixtures for gda.entity.individuals test suites.
Inherits mock_locations_collection and mock_sites_collection from
tests/test_gda/test_entity/conftest.py.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest

from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import IndividualID
from gda.model.base.audit import AuditStamp
from gda.model.base.name import NamePerson
from gda.model.base.tombstone import Tombstone
from gda.model.entity.individual import Individual

__version__ = "1.0.0+build.3"


@pytest.fixture
def make_individual() -> Callable[..., Individual]:
    """Factory fixture building validated Individual entities with sensible defaults."""

    def _factory(
        individual_id: str = "IND-000001",
        name: NamePerson | str = "John Quincy Adams",
        canonical_urn: str | None = None,
        gender: str = "M",
        birth_date: Any = "1842-05-14",
        death_date: Any = "1910-11-20",
        birth_place_id: str | None = "LOC-000001",
        death_place_id: str | None = "SID-000001",
        is_deceased: bool = True,
        tombstone: Tombstone[IndividualID] | None = None,
        **kwargs: Any,
    ) -> Individual:
        now = IsoTimestamp("2026-11-15T12:00:00Z")
        audit = AuditStamp(created_at=now, updated_at=now)
        urn = canonical_urn or f"urn:gda:ind:person_{individual_id.lower().replace('-', '_')}"
        if isinstance(name, str):
            tokens = name.strip().split()
            if len(tokens) >= 2:
                resolved_name = NamePerson.create(
                    raw=name.strip(),
                    given=" ".join(tokens[:-1]),
                    surname=tokens[-1],
                )
            else:
                resolved_name = NamePerson.create(raw=name.strip(), given=tokens[0])
        else:
            resolved_name = name
        return Individual.create(
            individual_id=IndividualID(individual_id),
            name=resolved_name,
            canonical_urn=urn,
            gender=gender,
            birth_date=birth_date,
            death_date=death_date,
            birth_place_id=birth_place_id,
            death_place_id=death_place_id,
            is_deceased=is_deceased,
            audit=audit,
            tombstone=tombstone or Tombstone[IndividualID](),
            **kwargs,
        )

    return _factory


@pytest.fixture
def active_individual(make_individual: Callable[..., Individual]) -> Individual:
    """Return a default active Individual entity."""
    return make_individual("IND-000001")


@pytest.fixture
def tombstoned_individual(make_individual: Callable[..., Individual]) -> Individual:
    """Return a default retired Individual entity."""
    now = IsoTimestamp("2026-11-15T12:00:00Z")
    tomb = Tombstone[IndividualID]().retire(timestamp=now)
    return make_individual("IND-000002", tombstone=tomb)
