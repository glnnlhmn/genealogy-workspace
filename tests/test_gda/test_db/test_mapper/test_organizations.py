"""Path: tests/test_gda/test_db/test_mapper/test_organizations.py

Unit and regression verification suite for OrganizationRowMapper.

Operational Role:
    1:1 verification suite for src/gda/db/mapper/organizations.py. Validates
    lossless round-trip mapping for Organization entities (full hierarchy and
    minimal/deprecated configurations) and EntityMappingError boundaries.
"""

from __future__ import annotations

import pytest

import gda.db.mapper.organizations as org_mod
from gda.core.enums.orgs import OrganizationCategory
from gda.db.exceptions import EntityMappingError
from gda.db.mapper.organizations import OrganizationRowMapper
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import OrganizationID
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate, TimePeriod
from gda.model.base.name import NameThing
from gda.model.base.tombstone import Tombstone
from gda.model.entity.organization import Organization

__version__ = "1.0.0+build.1"


def _make_audit() -> AuditStamp:
    now = IsoTimestamp("2026-01-01T00:00:00Z")
    return AuditStamp(created_at=now, updated_at=now)


@pytest.mark.unit
def test_organizations_mapper_dunder_all() -> None:
    """Verify gda.db.mapper.organizations.__all__ is sorted."""
    assert org_mod.__all__ == ["OrganizationRowMapper"]


@pytest.mark.integration
def test_organization_row_mapper_full_and_minimal_round_trip() -> None:
    """Verify OrganizationRowMapper round-trips full and minimal Organization entities."""
    audit = _make_audit()
    period = TimePeriod(
        start_date=EventDate.create("1920"),
        end_date=EventDate.create("1995"),
    )
    org = Organization.create(
        org_id="ORG-000001",
        canonical_urn="urn:gda:org:nh:vfw_post_411",
        name=NameThing.create(
            raw="VFW Post 411",
            canonical="VFW Post 411",
            aliases=["Bow VFW"],
        ),
        category=OrganizationCategory.VETERANS,
        parent_org_id="ORG-000010",
        predecessor_ids=["ORG-000008"],
        successor_ids=["ORG-000009"],
        location_id="LOC-000001",
        meeting_site_id="SID-000001",
        period=period,
        is_active=True,
        audit=audit,
        tombstone=Tombstone(
            is_deprecated=True,
            deprecated_at=audit.updated_at,
            superseded_by=OrganizationID("ORG-000002"),
        ),
    )

    mapper = OrganizationRowMapper()
    row_data = mapper.to_row(org)
    assert mapper.from_row(row_data) == org

    minimal_org = Organization.create(
        org_id="ORG-000002",
        canonical_urn="urn:gda:org:nh:grange",
        name="Bow Grange",
        category=OrganizationCategory.FRATERNAL,
        audit=audit,
    )
    min_row = mapper.to_row(minimal_org)
    min_row["predecessor_ids_json"] = None
    min_row["successor_ids_json"] = None
    assert mapper.from_row(min_row) == minimal_org


@pytest.mark.regression
def test_organization_row_mapper_corrupt_row_raises_error() -> None:
    """Verify OrganizationRowMapper raises EntityMappingError on invalid row."""
    with pytest.raises(EntityMappingError, match="Failed to map row to Organization"):
        OrganizationRowMapper().from_row({"id": None})
