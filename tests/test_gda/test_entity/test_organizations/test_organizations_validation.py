"""Path: tests/test_gda/test_entity/test_organizations/test_organizations_validation.py

Comprehensive test suite for gda.entity.organizations.validation.
"""

from __future__ import annotations

from collections.abc import Callable
from unittest.mock import MagicMock

import pytest

from gda.core.enums.orgs import OrganizationCategory
from gda.entity.organizations.collection import Organizations
from gda.entity.organizations.errors import OrganizationValidationError
from gda.entity.organizations.validation import (
    valid_collection_all,
    valid_collection_hierarchy,
    valid_collection_indexes,
    valid_collection_references,
    valid_collection_tombstones,
    valid_organization,
    valid_urn,
)
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import LocationID, OrganizationID, SiteID
from gda.model.base.name import NameThing
from gda.model.base.tombstone import Tombstone
from gda.model.entity.organization import Organization

__version__ = "1.0.0+build.3"


@pytest.mark.unit
def test_valid_urn_and_valid_organization_checks(
    make_organization: Callable[..., Organization],
) -> None:
    """Verify valid_urn and valid_organization enforce URN, name, and category invariants."""
    assert valid_urn("urn:gda:org:us:nh:concord:vfw_post_411") is True

    with pytest.raises(OrganizationValidationError, match="Invalid canonical_urn format"):
        valid_urn("")
    with pytest.raises(OrganizationValidationError, match="Invalid canonical_urn format"):
        valid_urn("urn:gda:site:wrong_prefix")
    with pytest.raises(OrganizationValidationError, match="Contains empty or adjacent delimiters"):
        valid_urn("urn:gda:org:us::nh")

    org = make_organization("ORG-000001")
    assert valid_organization(org) is True

    blank_name_org = make_organization("ORG-000002")
    object.__setattr__(blank_name_org.name, "canonical", "   ")
    with pytest.raises(OrganizationValidationError, match="canonical name cannot be blank"):
        valid_organization(blank_name_org)

    bad_cat_org = make_organization("ORG-000003")
    object.__setattr__(bad_cat_org, "category", "NOT_AN_ENUM")
    with pytest.raises(OrganizationValidationError, match="must be an OrganizationCategory enum"):
        valid_organization(bad_cat_org)


@pytest.mark.unit
def test_valid_collection_hierarchy_supports_standalone_and_detects_cycles_and_bad_parents(
    make_organization: Callable[..., Organization],
) -> None:
    """Verify valid_collection_hierarchy allows standalone orgs and flags cycles/missing/tombstoned parents."""
    now = IsoTimestamp("2026-11-15T12:00:00Z")

    p = make_organization("ORG-000001", name="State VFW")
    c = make_organization("ORG-000002", name="Post 411", parent_org_id="ORG-000001")
    standalone = make_organization("ORG-000003", name="Local Choir", parent_org_id=None)
    valid_coll = Organizations([c, p, standalone])
    assert valid_collection_hierarchy(valid_coll) is True

    a = make_organization("ORG-000010", parent_org_id="ORG-000011")
    b = make_organization("ORG-000011", parent_org_id="ORG-000010")
    c_into_cycle = make_organization("ORG-000012", parent_org_id="ORG-000010")
    cyclic_coll = Organizations([c_into_cycle, a, b])
    assert valid_collection_hierarchy(cyclic_coll) is False

    dead_parent = make_organization(
        "ORG-000020",
        tombstone=Tombstone[OrganizationID]().retire(timestamp=now),
    )
    child_of_dead = make_organization("ORG-000021", parent_org_id="ORG-000020")
    child_of_missing = make_organization("ORG-000022", parent_org_id="ORG-000099")
    bad_parent_coll = Organizations([dead_parent, child_of_dead, child_of_missing])
    assert valid_collection_hierarchy(bad_parent_coll) is False


@pytest.mark.unit
def test_valid_collection_references_checks_optional_location_and_site_fks(
    make_organization: Callable[..., Organization],
    mock_locations_collection: MagicMock,
    mock_sites_collection: MagicMock,
) -> None:
    """Verify valid_collection_references passes when FKs are None or valid, and fails when invalid."""
    org_none = make_organization("ORG-000001", location_id=None, meeting_site_id=None)
    org_valid = make_organization(
        "ORG-000002",
        location_id="LOC-000001",
        meeting_site_id="SID-000001",
    )
    coll = Organizations([org_none, org_valid])
    assert (
        valid_collection_references(
            coll,
            locations_collection=mock_locations_collection,
            sites_collection=mock_sites_collection,
        )
        is True
    )
    assert valid_collection_references(coll) is True

    org_bad_missing = make_organization(
        "ORG-000003",
        location_id="LOC-000099",
        meeting_site_id="SID-000099",
    )
    org_bad_prefix = make_organization("ORG-000004")
    object.__setattr__(org_bad_prefix, "location_id", "BAD-1")
    object.__setattr__(org_bad_prefix, "meeting_site_id", "BAD-2")
    bad_coll = Organizations([org_bad_missing, org_bad_prefix])
    assert (
        valid_collection_references(
            bad_coll,
            locations_collection=mock_locations_collection,
            sites_collection=mock_sites_collection,
        )
        is False
    )


@pytest.mark.unit
def test_valid_collection_tombstones_checks_all_supersession_branches(
    make_organization: Callable[..., Organization],
) -> None:
    """Verify valid_collection_tombstones validates self, missing, deprecated, and category-mismatched replacements."""
    now = IsoTimestamp("2026-11-15T12:00:00Z")
    active_vet = make_organization("ORG-000001", category=OrganizationCategory.VETERANS)
    active_civic = make_organization("ORG-000002", category=OrganizationCategory.CIVIC_SERVICE)
    dead_no_sup = make_organization(
        "ORG-000003",
        tombstone=Tombstone[OrganizationID]().retire(timestamp=now),
    )
    dead_valid_sup = make_organization(
        "ORG-000004",
        category=OrganizationCategory.VETERANS,
        tombstone=Tombstone[OrganizationID]().retire(
            timestamp=now, superseded_by=OrganizationID("ORG-000001")
        ),
    )
    clean_coll = Organizations([active_vet, active_civic, dead_no_sup, dead_valid_sup])
    assert valid_collection_tombstones(clean_coll) is True

    dead_self = make_organization(
        "ORG-000005",
        tombstone=Tombstone[OrganizationID]().retire(timestamp=now),
    )
    object.__setattr__(dead_self.tombstone, "superseded_by", OrganizationID("ORG-000005"))

    dead_missing = make_organization(
        "ORG-000006",
        tombstone=Tombstone[OrganizationID]().retire(
            timestamp=now, superseded_by=OrganizationID("ORG-000099")
        ),
    )
    dead_to_dead = make_organization(
        "ORG-000007",
        tombstone=Tombstone[OrganizationID]().retire(
            timestamp=now, superseded_by=OrganizationID("ORG-000003")
        ),
    )
    dead_mismatch = make_organization(
        "ORG-000008",
        category=OrganizationCategory.VETERANS,
        tombstone=Tombstone[OrganizationID]().retire(
            timestamp=now, superseded_by=OrganizationID("ORG-000002")
        ),
    )
    bad_coll = Organizations(
        [
            active_vet,
            active_civic,
            dead_no_sup,
            dead_self,
            dead_missing,
            dead_to_dead,
            dead_mismatch,
        ]
    )
    assert valid_collection_tombstones(bad_coll) is False


@pytest.mark.unit
def test_valid_collection_indexes_and_valid_collection_all(
    make_organization: Callable[..., Organization],
) -> None:
    """Verify valid_collection_indexes detects desynchronization across all 6 secondary indexes."""
    parent = make_organization("ORG-000001", location_id=None, meeting_site_id=None)
    name = NameThing.create(raw="Post 411", canonical="Post 411").add_alias("Concord VFW")
    child = Organization.create(
        org_id="ORG-000002",
        name=name,
        category=OrganizationCategory.VETERANS,
        canonical_urn="urn:gda:org:post_411",
        parent_org_id=parent.id,
        location_id=LocationID("LOC-000001"),
        meeting_site_id=SiteID("SID-000001"),
    )
    coll = Organizations([parent, child])
    assert valid_collection_indexes(coll) is True
    assert valid_collection_all(coll) is True

    # 1. URN mismatch & missing URN & dangling URN
    coll._urn_index["urn:gda:org:post_411"] = parent.id
    coll._urn_index.pop(parent.canonical_urn, None)
    coll._urn_index["urn:gda:org:dangling"] = OrganizationID("ORG-999999")
    # 2. Missing alias, category bucket, location bucket, site bucket, parent bucket
    coll._alias_index.clear()
    coll._category_index.clear()
    coll._location_index.clear()
    coll._site_index.clear()
    coll._parent_index.clear()
    assert valid_collection_indexes(coll) is False

    # 3. Bucket exists but entity ID missing from each bucket
    coll2 = Organizations([parent, child])
    coll2._alias_index["concord vfw"].discard(child.id)
    coll2._category_index[child.category].discard(child.id)
    coll2._location_index[LocationID("LOC-000001")].discard(child.id)
    coll2._site_index[SiteID("SID-000001")].discard(child.id)
    coll2._parent_index[parent.id].discard(child.id)
    assert valid_collection_indexes(coll2) is False
    assert valid_collection_all(coll2) is False
