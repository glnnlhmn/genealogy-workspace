"""Path: tests/test_gda/test_entity/test_organizations/test_organizations_collection.py

Comprehensive unit and regression test suite for Organizations collection manager.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from gda.core.enums.orgs import OrganizationCategory
from gda.core.errors import ModelFormatError
from gda.entity.organizations.collection import Organizations
from gda.entity.organizations.errors import (
    OrganizationNotFoundError,
    OrganizationValidationError,
)
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import LocationID, OrganizationID, SiteID
from gda.model.base.name import NameThing
from gda.model.base.tombstone import Tombstone
from gda.model.entity.organization import Organization

__version__ = "1.0.0+build.3"


@pytest.mark.unit
def test_organizations_init_empty_and_with_list(
    make_organization: Callable[..., Organization],
) -> None:
    """Verify Organizations initialization with empty state and pre-populated list."""
    empty = Organizations()
    assert len(empty) == 0
    assert empty.is_dirty is False

    org1 = make_organization("ORG-000001").mark_dirty()
    org2 = make_organization(
        "ORG-000002",
        name="Bow Men's Choir",
        category=OrganizationCategory.CULTURAL_ARTS,
    )
    populated = Organizations([org1, org2])
    assert len(populated) == 2
    assert populated.is_dirty is True
    assert populated.dirty_entities() == [org1]
    populated.mark_clean()
    assert populated.is_dirty is False
    assert populated.dirty_entities() == []


@pytest.mark.unit
def test_organizations_contains_getitem_get_and_graveyard_helpers(
    make_organization: Callable[..., Organization],
    active_organization: Organization,
    tombstoned_organization: Organization,
) -> None:
    """Verify __contains__, __getitem__, get(), get_any(), find_tombstoned(), and resolve_active()."""
    now = IsoTimestamp("2026-11-15T12:00:00Z")
    sup_org = make_organization(
        "ORG-000003",
        tombstone=Tombstone[OrganizationID]().retire(
            timestamp=now, superseded_by=active_organization.id
        ),
    )
    cyc1 = make_organization(
        "ORG-000004",
        tombstone=Tombstone[OrganizationID]().retire(
            timestamp=now, superseded_by=OrganizationID("ORG-000005")
        ),
    )
    cyc2 = make_organization(
        "ORG-000005",
        tombstone=Tombstone[OrganizationID]().retire(
            timestamp=now, superseded_by=OrganizationID("ORG-000004")
        ),
    )
    coll = Organizations([active_organization, tombstoned_organization, sup_org, cyc1, cyc2])

    assert active_organization.id in coll
    assert "ORG-000001" in coll
    assert active_organization.canonical_urn in coll
    assert tombstoned_organization.id not in coll
    assert "ORG-000002" not in coll
    assert tombstoned_organization.canonical_urn not in coll
    assert "ORG-999999" not in coll
    assert "urn:gda:org:missing" not in coll
    assert 12345 not in coll  # type: ignore[operator]

    assert coll[active_organization.id] is active_organization
    assert coll["ORG-000001"] is active_organization
    assert coll[active_organization.canonical_urn] is active_organization
    assert coll.get("ORG-000001") is active_organization
    assert coll.get("ORG-999999") is None

    assert coll.get_any("ORG-000002") is tombstoned_organization
    assert coll.get_any("ORG-999999") is None
    assert coll.get_any(12345) is None  # type: ignore[arg-type]
    assert len(coll.find_tombstoned()) == 4
    assert coll.resolve_active("ORG-000001") is active_organization
    assert coll.resolve_active("ORG-000003") is active_organization
    assert coll.resolve_active("ORG-000002") is None
    assert coll.resolve_active("ORG-000004") is None
    assert coll.resolve_active("ORG-999999") is None

    with pytest.raises(OrganizationNotFoundError, match="not found"):
        _ = coll["ORG-999999"]
    with pytest.raises(OrganizationNotFoundError, match="not found"):
        _ = coll[12345]  # type: ignore[index]
    with pytest.raises(OrganizationNotFoundError, match="tombstoned"):
        _ = coll[tombstoned_organization.id]


@pytest.mark.unit
def test_organizations_iteration_excludes_tombstoned_and_iter_all_includes(
    active_organization: Organization,
    tombstoned_organization: Organization,
) -> None:
    """Verify __iter__ yields only active entities while iter_all yields all."""
    coll = Organizations([active_organization, tombstoned_organization])
    assert list(coll) == [active_organization]
    assert list(coll.iter_all()) == [active_organization, tombstoned_organization]


@pytest.mark.regression
def test_organizations_add_and_update_type_guards_and_reindexing(
    make_organization: Callable[..., Organization],
) -> None:
    """Verify add and update enforce Organization type and re-index all secondary buckets."""
    coll = Organizations()
    with pytest.raises(TypeError, match="Expected Organization instance"):
        coll.add("not-an-org")  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="Expected Organization instance"):
        coll.update("not-an-org")  # type: ignore[arg-type]

    missing = make_organization("ORG-000099")
    with pytest.raises(OrganizationNotFoundError, match="not found in registry"):
        coll.update(missing)

    parent1 = make_organization("ORG-000001", name="State VFW")
    parent2 = make_organization("ORG-000002", name="National VFW")
    coll.add(parent1)
    coll.add(parent2)

    name_with_aliases = NameThing.create(raw="Post 411", canonical="Post 411").add_alias(
        "Concord Post"
    )
    child = Organization.create(
        org_id="ORG-000003",
        name=name_with_aliases,
        category=OrganizationCategory.VETERANS,
        canonical_urn="urn:gda:org:post_411",
        parent_org_id=parent1.id,
        location_id=LocationID("LOC-000001"),
        meeting_site_id=SiteID("SID-000001"),
    )
    coll.add(child)
    assert coll.find_by_alias("Concord Post") == [child]
    assert coll.find_by_alias("   ") == []

    # Clear category/location/site buckets first to test empty-bucket deletion on update
    coll._category_index[OrganizationCategory.VETERANS].discard(parent1.id)
    coll._category_index[OrganizationCategory.VETERANS].discard(parent2.id)
    coll._location_index[LocationID("LOC-000001")].discard(parent1.id)
    coll._location_index[LocationID("LOC-000001")].discard(parent2.id)
    coll._site_index[SiteID("SID-000001")].discard(parent1.id)
    coll._site_index[SiteID("SID-000001")].discard(parent2.id)

    updated_name = NameThing.create(raw="Civic Club 411", canonical="Civic Club 411").add_alias(
        "Bow Civic"
    )
    updated_child = Organization.create(
        org_id="ORG-000003",
        name=updated_name,
        category=OrganizationCategory.CIVIC_SERVICE,
        canonical_urn="urn:gda:org:civic_411",
        parent_org_id=parent2.id,
        location_id=LocationID("LOC-000002"),
        meeting_site_id=SiteID("SID-000002"),
    )
    coll.update(updated_child)

    assert "concord post" not in coll._alias_index
    assert coll._alias_index["bow civic"] == {child.id}
    assert "urn:gda:org:post_411" not in coll._urn_index
    assert coll["urn:gda:org:civic_411"] is updated_child
    assert coll.find_by_category("CIVIC_SERVICE") == [updated_child]
    assert coll.find_by_location("LOC-000002") == [updated_child]
    assert coll.find_by_location(LocationID("LOC-000002")) == [updated_child]
    assert coll.find_by_site("SID-000002") == [updated_child]
    assert coll.find_by_site(SiteID("SID-000002")) == [updated_child]
    assert coll.find_children(parent1.id) == []
    assert coll.find_children(str(parent2.id)) == [updated_child]


@pytest.mark.unit
def test_organizations_update_retains_non_empty_shared_buckets_and_handles_missing_old_alias(
    make_organization: Callable[..., Organization],
) -> None:
    """Verify update retains index buckets when other entities share the same bucket and handles unindexed aliases."""
    coll = Organizations()
    p1 = make_organization("ORG-000001", category=OrganizationCategory.FRATERNAL)
    name_c1 = NameThing.create(raw="Lodge 1", canonical="Lodge 1").add_alias("Shared Alias")
    c1 = Organization.create(
        org_id="ORG-000002",
        name=name_c1,
        category=OrganizationCategory.FRATERNAL,
        canonical_urn="urn:gda:org:lodge_1",
        parent_org_id="ORG-000001",
        location_id="LOC-000001",
        meeting_site_id="SID-000001",
    )
    name_c2 = NameThing.create(raw="Lodge 2", canonical="Lodge 2").add_alias("Shared Alias")
    c2 = Organization.create(
        org_id="ORG-000003",
        name=name_c2,
        category=OrganizationCategory.FRATERNAL,
        canonical_urn="urn:gda:org:lodge_2",
        parent_org_id="ORG-000001",
        location_id="LOC-000001",
        meeting_site_id="SID-000001",
    )
    coll.add(p1)
    coll.add(c1)
    coll.add(c2)
    assert coll._alias_index["shared alias"] == {c1.id, c2.id}

    c2_same = Organization.create(
        org_id="ORG-000003",
        name="Lodge 2 Updated",
        category=OrganizationCategory.RELIGIOUS,
        canonical_urn="urn:gda:org:lodge_2",
        parent_org_id=None,
        location_id=None,
        meeting_site_id=None,
    )
    coll.update(c2_same)
    assert coll._alias_index["shared alias"] == {c1.id}
    assert OrganizationCategory.FRATERNAL in coll._category_index
    assert LocationID("LOC-000001") in coll._location_index
    assert SiteID("SID-000001") in coll._site_index
    assert OrganizationID("ORG-000001") in coll._parent_index

    # Clear _alias_index and update c1 to exercise key not in _alias_index branch
    coll._alias_index.clear()
    c1_again = Organization.create(
        org_id="ORG-000002",
        name="Lodge 1 Final",
        category=OrganizationCategory.FRATERNAL,
        canonical_urn="urn:gda:org:lodge_1",
        parent_org_id="ORG-000001",
        location_id="LOC-000001",
        meeting_site_id="SID-000001",
    )
    coll.update(c1_again)

    c2_again = Organization.create(
        org_id="ORG-000003",
        name="Lodge 2 Final",
        category=OrganizationCategory.RELIGIOUS,
        canonical_urn="urn:gda:org:lodge_2",
        parent_org_id=None,
        location_id=None,
        meeting_site_id=None,
    )
    coll.update(c2_again)
    assert coll["ORG-000003"].canonical_name == "Lodge 2 Final"


@pytest.mark.unit
def test_organizations_create_variants_and_validation_guards(
    mock_locations_collection: MagicMock,
    mock_sites_collection: MagicMock,
) -> None:
    """Verify Organizations.create supports standalone, parented, location-only, and explicit URN modes."""
    coll = Organizations()

    with pytest.raises(ModelFormatError, match="cannot be blank"):
        coll.create(name="   ", category=OrganizationCategory.VETERANS)

    with pytest.raises(OrganizationValidationError, match="Governing location"):
        coll.create(
            name="Post 1",
            category=OrganizationCategory.VETERANS,
            location_id="LOC-999999",
            locations_collection=mock_locations_collection,
        )

    with pytest.raises(OrganizationValidationError, match="Meeting site"):
        coll.create(
            name="Post 1",
            category=OrganizationCategory.VETERANS,
            meeting_site_id="SID-999999",
            sites_collection=mock_sites_collection,
        )

    # 1. Standalone with neither parent_org_id nor location_id
    standalone = coll.create(
        name="Independent Choir",
        category="CULTURAL_ARTS",
        alternate_names=["Bow Singers", "   "],
    )
    assert standalone.id == OrganizationID("ORG-000001")
    assert standalone.canonical_urn == "urn:gda:org:independent_choir_o000001"
    assert standalone.parent_org_id is None
    assert standalone.location_id is None

    # 2. Standalone with location_id
    with_loc = coll.create(
        name="Bow Historical Society",
        category=OrganizationCategory.EDUCATIONAL,
        location_id=LocationID("LOC-000001"),
        meeting_site_id=SiteID("SID-000001"),
        locations_collection=mock_locations_collection,
        sites_collection=mock_sites_collection,
    )
    assert with_loc.canonical_urn == "urn:gda:org:loc_000001:bow_historical_society_o000002"

    # 3. Child with parent_org_id (auto-prefixes parent's canonical_urn)
    child = coll.create(
        name="Youth Chapter",
        category=OrganizationCategory.EDUCATIONAL,
        parent_org_id=with_loc.id,
    )
    assert child.parent_org_id == with_loc.id
    assert child.canonical_urn == f"{with_loc.canonical_urn}:youth_chapter"

    # 4. Explicit canonical_urn
    explicit = coll.create(
        name="Custom Guild",
        category=OrganizationCategory.LABOR_GUILD,
        canonical_urn="urn:gda:org:custom:guild_1",
    )
    assert explicit.canonical_urn == "urn:gda:org:custom:guild_1"


@pytest.mark.unit
def test_organizations_persistence_and_file_facades(
    active_organization: Organization,
    tmp_path: Path,
) -> None:
    """Verify from_database, load_from_db, save_to_db, refresh, import_file, and export_file facades."""
    with (
        patch("gda.entity.organizations.collection.load_from_db", return_value=1) as mock_load,
        patch("gda.entity.organizations.collection.save_to_db", return_value=1) as mock_save,
    ):
        db_coll = Organizations.from_database()
        mock_load.assert_called_once_with(db_coll)

        db_coll.add(active_organization)
        assert db_coll.save_to_db() == 1
        assert db_coll.is_dirty is False
        mock_save.assert_called_once_with(db_coll)

        assert db_coll.load_from_db() == 1
        assert db_coll.refresh() == 1
        assert len(db_coll) == 0

    out_file = tmp_path / "orgs.json"
    coll = Organizations([active_organization])
    assert coll.export_file(out_file) == 1
    fresh = Organizations()
    assert fresh.import_file(out_file) == 1
    assert len(fresh) == 1
