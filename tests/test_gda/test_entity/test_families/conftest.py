"""Path: tests/test_gda/test_entity/test_families/conftest.py

Shared directory-scoped test fixtures for gda.entity.families test suites.
Inherits mock_individuals_collection from tests/test_gda/test_entity/conftest.py.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest

from gda.core.enums.vital import PedigreeType, UnionType
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import FamilyID
from gda.model.base.audit import AuditStamp
from gda.model.base.family import ChildLink, FamilyUnion
from gda.model.base.tombstone import Tombstone
from gda.model.entity.family import Family

__version__ = "1.0.0+build.3"


@pytest.fixture
def make_family() -> Callable[..., Family]:
    """Factory fixture building validated Family entities with sensible defaults."""

    def _factory(
        family_id: str = "FAM-000001",
        canonical_urn: str | None = None,
        partner_ids: list[str] | None = None,
        children: list[Any] | None = None,
        union: FamilyUnion | dict[str, Any] | None = None,
        tombstone: Tombstone[FamilyID] | None = None,
        **kwargs: Any,
    ) -> Family:
        now = IsoTimestamp("2026-11-15T12:00:00Z")
        audit = AuditStamp(created_at=now, updated_at=now)
        urn = canonical_urn or f"urn:gda:fam:unit_{family_id.lower().replace('-', '_')}"
        default_partners = partner_ids if partner_ids is not None else ["IND-000001", "IND-000002"]
        default_children = (
            children
            if children is not None
            else [ChildLink.create("IND-000003", PedigreeType.BIRTH)]
        )
        default_union = union or FamilyUnion.create(union_type=UnionType.MARRIED)
        return Family.create(
            family_id=FamilyID(family_id),
            canonical_urn=urn,
            partner_ids=default_partners,
            children=default_children,
            union=default_union,
            audit=audit,
            tombstone=tombstone or Tombstone[FamilyID](),
            **kwargs,
        )

    return _factory


@pytest.fixture
def active_family(make_family: Callable[..., Family]) -> Family:
    """Return a default active Family entity."""
    return make_family("FAM-000001")


@pytest.fixture
def tombstoned_family(make_family: Callable[..., Family]) -> Family:
    """Return a default retired Family entity."""
    now = IsoTimestamp("2026-11-15T12:00:00Z")
    tomb = Tombstone[FamilyID]().retire(timestamp=now)
    return make_family("FAM-000002", tombstone=tomb)
