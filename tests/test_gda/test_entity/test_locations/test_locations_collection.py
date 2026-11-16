"""Path: tests/test_gda/test_entity/test_locations/test_locations_collection.py

Unit, regression, and integration test suite for the Locations collection class.

Operational Role:
    Verifies collection-level initialization, CRUD operations, URN, alias,
    category, and parent indexing, relational containment, cascading
    soft-delete/undelete propagation, graveyard inspection helpers, database
    persistence synchronization, and refresh behaviors for Locations collections.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from gda.core.enums.location import JurisdictionCategory
from gda.core.errors import ModelFormatError
from gda.entity.locations.collection import Locations
from gda.entity.locations.errors import LocationHierarchyError, LocationNotFoundError
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import LocationID
from gda.model.base.audit import AuditStamp
from gda.model.base.name import NameThing
from gda.model.base.tombstone import Tombstone
from gda.model.entity.location import Location

__version__ = "1.0.0+build.14"


# ==============================================================================
# GROUP 1: INITIALIZATION, DIRTY STATE & CONTAINMENT
# ==============================================================================


@pytest.mark.smoke
def test_locations_init_empty_collection(empty_collection: Locations) -> None:
    """Verify empty collection initializes with zero length and clean dirty flag."""
    assert len(empty_collection) == 0
    assert empty_collection.is_dirty is False
    assert list(empty_collection) == []
    assert list(empty_collection.iter_all()) == []


@pytest.mark.regression
def test_locations_init_with_initial_list() -> None:
    """Verify initialization with an initial list of Location instances."""
    now = IsoTimestamp("2026-11-15T12:00:00Z")
    audit = AuditStamp(created_at=now, updated_at=now)
    loc = Location.create(
        location_id=LocationID("LOC-000001"),
        audit=audit,
        name="Canada",
        category=JurisdictionCategory.COUNTRY,
        canonical_urn="urn:gda:loc:canada",
        tombstone=Tombstone[LocationID](),
    )
    col = Locations([loc])
    assert len(col) == 1
    assert col.is_dirty is True
    assert col[LocationID("LOC-000001")] is loc


@pytest.mark.regression
def test_locations_contains_and_getitem_resolution(
    populated_collection: Locations,
) -> None:
    """Verify containment testing and subscript lookup by ID, string ID, and URN."""
    loc_id = LocationID("LOC-000001")
    urn = "urn:gda:loc:united_states"

    assert loc_id in populated_collection
    assert "LOC-000001" in populated_collection
    assert urn in populated_collection
    assert "urn:gda:loc:non_existent" not in populated_collection
    assert LocationID("LOC-999999") not in populated_collection

    assert populated_collection[loc_id].id == loc_id
    assert populated_collection["LOC-000001"].id == loc_id
    assert populated_collection[urn].canonical_urn == urn


@pytest.mark.regression
def test_locations_contains_fallback_branches(
    populated_collection: Locations,
) -> None:
    """Verify __contains__ returns False on invalid types, missing URNs, and tombstoned IDs."""
    assert ("non_urn_missing_string" in populated_collection) is False
    assert (12345 in populated_collection) is False  # type: ignore[operator]

    populated_collection.soft_delete("LOC-000005")
    assert (LocationID("LOC-000005") in populated_collection) is False
    assert ("LOC-000005" in populated_collection) is False
    assert ("urn:gda:loc:united_states:nh:merrimack:bow:center" in populated_collection) is False


@pytest.mark.regression
def test_locations_getitem_raises_on_missing_or_tombstoned(
    populated_collection: Locations,
) -> None:
    """Verify subscript lookup raises LocationNotFoundError on missing, tombstoned, or invalid keys."""
    with pytest.raises(LocationNotFoundError, match="Location not found"):
        _ = populated_collection["LOC-999999"]

    with pytest.raises(LocationNotFoundError, match="Location not found"):
        _ = populated_collection["urn:gda:loc:missing"]

    with pytest.raises(LocationNotFoundError, match="Location not found"):
        _ = populated_collection[999999]  # type: ignore[index]

    populated_collection.soft_delete("LOC-000005")
    with pytest.raises(LocationNotFoundError, match="Location has been tombstoned"):
        _ = populated_collection["LOC-000005"]


@pytest.mark.regression
def test_locations_get_returns_default_when_absent(
    populated_collection: Locations,
) -> None:
    """Verify get() returns default value when target does not exist."""
    now = IsoTimestamp("2026-11-15T12:00:00Z")
    default_loc = Location.create(
        location_id=LocationID("LOC-000099"),
        audit=AuditStamp(created_at=now, updated_at=now),
        name="Fallback",
        category=JurisdictionCategory.COUNTRY,
        canonical_urn="urn:gda:loc:fallback",
    )
    res = populated_collection.get("LOC-999999", default=default_loc)
    assert res is default_loc
    assert populated_collection.get("LOC-999999") is None


# ==============================================================================
# GROUP 2: MUTATIONS, MULTI-ENTITY ALIASES & SECONDARY INDEXES
# ==============================================================================


@pytest.mark.regression
def test_locations_add_rejects_non_location_type(
    empty_collection: Locations,
) -> None:
    """Verify add() raises TypeError when given a non-Location instance."""
    with pytest.raises(TypeError, match="Expected Location instance"):
        empty_collection.add("not_a_location")  # type: ignore[arg-type]


@pytest.mark.regression
def test_locations_add_supports_multi_entity_aliases(
    empty_collection: Locations,
) -> None:
    """Verify add() indexes multiple entities sharing an alias and update() retains remaining peers."""
    now = IsoTimestamp("2026-11-15T12:00:00Z")
    loc1 = Location.create(
        location_id=LocationID("LOC-000001"),
        audit=AuditStamp(created_at=now, updated_at=now),
        name=NameThing.create(raw="Node 1", canonical="Node 1"),
        category=JurisdictionCategory.COUNTRY,
        canonical_urn="urn:gda:loc:node1",
        tombstone=Tombstone[LocationID](),
    ).add_alias("Shared Alias")

    loc2 = Location.create(
        location_id=LocationID("LOC-000002"),
        audit=AuditStamp(created_at=now, updated_at=now),
        name=NameThing.create(raw="Node 2", canonical="Node 2"),
        category=JurisdictionCategory.COUNTRY,
        canonical_urn="urn:gda:loc:node2",
        tombstone=Tombstone[LocationID](),
    ).add_alias("Shared Alias")

    empty_collection.add(loc1)
    empty_collection.add(loc2)

    assert empty_collection._alias_index["shared alias"] == {loc1.id, loc2.id}
    assert len(empty_collection.find_by_alias("Shared Alias")) == 2
    assert empty_collection.find_by_alias("   ") == []

    # Removing alias from loc1 retains loc2 in the bucket
    loc1_no_alias = loc1.remove_alias("Shared Alias")
    empty_collection.update(loc1_no_alias)
    assert empty_collection._alias_index["shared alias"] == {loc2.id}


@pytest.mark.regression
def test_locations_update_replaces_and_reindexes(
    populated_collection: Locations,
) -> None:
    """Verify update() replaces existing record and cleans stale urn/alias/category/parent indexes."""
    loc = populated_collection["LOC-000004"]
    updated = (
        loc.add_alias("Bow Village")
        .update_urn("urn:gda:loc:united_states:nh:merrimack:bow_new")
        .update_category(JurisdictionCategory.MUNICIPALITY)
        .update_parent(LocationID("LOC-000002"))
    )

    populated_collection.update(updated)
    assert "urn:gda:loc:united_states:nh:merrimack:bow_new" in populated_collection
    assert "urn:gda:loc:united_states:nh:merrimack:bow" not in populated_collection
    assert populated_collection.find_by_category("CIVIL_TOWNSHIP") == []
    assert populated_collection.find_children("LOC-000003") == []
    assert updated in populated_collection.find_children(LocationID("LOC-000002"))

    # Also test update where parent bucket and category bucket still have peers
    c2 = populated_collection.create(
        name="Peer Municipality",
        category=JurisdictionCategory.MUNICIPALITY,
        parent_id="LOC-000002",
    )
    c2_moved = c2.update_category(JurisdictionCategory.COUNTY_EQUIVALENT).update_parent(
        LocationID("LOC-000001")
    )
    populated_collection.update(c2_moved)
    assert JurisdictionCategory.MUNICIPALITY in populated_collection._category_index
    assert LocationID("LOC-000002") in populated_collection._parent_index


@pytest.mark.regression
def test_locations_update_purges_removed_alias(
    populated_collection: Locations,
) -> None:
    """Verify update() purges alias from _alias_index when an alias is deleted."""
    loc = populated_collection["LOC-000004"]
    loc_with_alias = loc.add_alias("Temporary Alias")
    populated_collection.update(loc_with_alias)
    assert "temporary alias" in populated_collection._alias_index

    loc_without_alias = loc_with_alias.remove_alias("Temporary Alias")
    populated_collection.update(loc_without_alias)
    assert "temporary alias" not in populated_collection._alias_index


@pytest.mark.regression
def test_locations_update_handles_unindexed_old_aliases(
    populated_collection: Locations,
) -> None:
    """Verify update() handles old records whose alias key was cleared from _alias_index."""
    loc = populated_collection["LOC-000004"].add_alias("Unindexed Alias")
    populated_collection.update(loc)
    populated_collection._alias_index.clear()

    clean_loc = loc.remove_alias("Unindexed Alias").add_alias("Clean Alias")
    populated_collection.update(clean_loc)
    assert "clean alias" in populated_collection._alias_index


@pytest.mark.regression
def test_locations_update_rejects_non_location_or_missing_id(
    empty_collection: Locations,
) -> None:
    """Verify update() raises TypeError on non-Location and LocationNotFoundError on missing ID."""
    with pytest.raises(TypeError, match="Expected Location instance"):
        empty_collection.update("not_a_loc")  # type: ignore[arg-type]

    now = IsoTimestamp("2026-11-15T12:00:00Z")
    loc = Location.create(
        location_id=LocationID("LOC-000001"),
        audit=AuditStamp(created_at=now, updated_at=now),
        name="Orphan",
        category=JurisdictionCategory.COUNTRY,
        canonical_urn="urn:gda:loc:orphan",
        tombstone=Tombstone[LocationID](),
    )
    with pytest.raises(LocationNotFoundError, match="Cannot update location"):
        empty_collection.update(loc)


@pytest.mark.unit
def test_locations_create_generates_and_registers_new_entity(
    empty_collection: Locations,
) -> None:
    """Verify create() mints new sequential ID, registers entity, and returns it."""
    loc1 = empty_collection.create(name="United States", category=JurisdictionCategory.COUNTRY)
    assert loc1.id == LocationID("LOC-000001")
    assert loc1.canonical_urn == "urn:gda:loc:united_states"

    loc2 = empty_collection.create(
        name="New Hampshire",
        category=JurisdictionCategory.STATOID,
        parent_id=loc1.id,
        alternate_names=["Granite State", "   "],
    )
    assert loc2.id == LocationID("LOC-000002")
    assert loc2.parent_id == loc1.id
    assert empty_collection.find_by_alias("Granite State") == [loc2]
    assert empty_collection.find_by_category(JurisdictionCategory.STATOID) == [loc2]
    assert empty_collection.find_children("LOC-000001") == [loc2]


@pytest.mark.regression
def test_locations_create_raises_on_blank_name(
    empty_collection: Locations,
) -> None:
    """Verify create() raises ModelFormatError when name is blank or pure whitespace."""
    with pytest.raises(ModelFormatError, match="Location name cannot be blank"):
        empty_collection.create(name="   ", category=JurisdictionCategory.COUNTRY)


# ==============================================================================
# GROUP 3: HIERARCHY BUILDING, SOFT DELETION, UNDELETE & GRAVEYARD HELPERS
# ==============================================================================


@pytest.mark.regression
def test_locations_create_hierarchy_full_chain(
    empty_collection: Locations,
) -> None:
    """Verify create_hierarchy builds or resolves complete 5-tier jurisdiction chain."""
    leaf = empty_collection.create_hierarchy(
        country="United States",
        state="New Hampshire",
        county="Merrimack",
        township="Bow",
        local="Bow Center",
    )
    assert leaf.category == JurisdictionCategory.MUNICIPALITY
    assert leaf.canonical_urn == "urn:gda:loc:united_states:new_hampshire:merrimack:bow:bow_center"
    assert len(empty_collection) == 5


@pytest.mark.regression
def test_locations_soft_delete_with_cascading_reparent_and_graveyard_helpers(
    populated_collection: Locations,
) -> None:
    """Verify soft_delete, get_any, find_tombstoned, resolve_active, and dirty_entities."""
    bow_id = LocationID("LOC-000004")
    center_id = LocationID("LOC-000005")

    now = IsoTimestamp("2026-11-15T12:00:00Z")
    audit = AuditStamp(created_at=now, updated_at=now)
    replacement_bow = Location.create(
        location_id=LocationID("LOC-000006"),
        audit=audit,
        name=NameThing.create(raw="New Bow", canonical="New Bow"),
        category=JurisdictionCategory.CIVIL_TOWNSHIP,
        canonical_urn="urn:gda:loc:united_states:nh:merrimack:new_bow",
        parent_id=LocationID("LOC-000003"),
        tombstone=Tombstone[LocationID](),
    )
    populated_collection.add(replacement_bow)
    populated_collection.mark_clean()
    assert populated_collection.dirty_entities() == []

    retired = populated_collection.soft_delete(
        bow_id, reason="Annexation", superseded_by=replacement_bow.id
    )
    assert retired.tombstone.is_deprecated is True
    assert retired.tombstone.superseded_by == replacement_bow.id
    assert len(populated_collection.dirty_entities()) == 2
    assert populated_collection.get_any(bow_id) is retired
    assert populated_collection.get_any("LOC-000004") is retired
    assert populated_collection.get_any("urn:gda:loc:united_states:nh:merrimack:bow") is retired
    assert populated_collection.get_any("LOC-999999") is None
    assert populated_collection.get_any(99999, default=None) is None  # type: ignore[arg-type]
    assert populated_collection.find_tombstoned() == [retired]
    assert populated_collection.resolve_active(bow_id) is replacement_bow
    assert populated_collection.resolve_active(replacement_bow.id) is replacement_bow
    assert populated_collection.resolve_active("LOC-999999") is None

    # Retire center_id without replacement -> resolve_active returns None
    retired_center = populated_collection.soft_delete(center_id, reason="Dissolved")
    assert populated_collection.resolve_active(center_id) is None

    # 2-node cyclic superseded_by guard in resolve_active (bow_id -> center_id -> bow_id)
    object.__setattr__(retired.tombstone, "superseded_by", center_id)
    object.__setattr__(retired_center.tombstone, "superseded_by", bow_id)
    assert populated_collection.resolve_active(bow_id) is None

    populated_collection.mark_clean()
    assert populated_collection.dirty_entities() == []


@pytest.mark.regression
def test_locations_soft_delete_raises_on_active_children_without_replacement(
    populated_collection: Locations,
) -> None:
    """Verify soft_delete raises LocationHierarchyError when target has active children and no replacement."""
    with pytest.raises(LocationHierarchyError, match="active child jurisdictions"):
        populated_collection.soft_delete("LOC-000004")


@pytest.mark.regression
def test_locations_soft_delete_raises_on_self_supersession(
    populated_collection: Locations,
) -> None:
    """Verify soft_delete raises LocationHierarchyError when target supersedes itself."""
    with pytest.raises(LocationHierarchyError, match="cannot be the entity itself"):
        populated_collection.soft_delete("LOC-000005", superseded_by="LOC-000005")


# ==============================================================================
# GROUP 4: PERSISTENCE DELEGATION & FILE I/O FACADES
# ==============================================================================


@pytest.mark.unit
def test_locations_persistence_and_file_facades(
    populated_collection: Locations,
    tmp_path: Path,
) -> None:
    """Verify from_database, load_from_db, save_to_db, refresh, import_file, and export_file facades."""
    with (
        patch("gda.entity.locations.collection.load_from_db", return_value=5) as mock_load,
        patch("gda.entity.locations.collection.save_to_db", return_value=5) as mock_save,
    ):
        db_col = Locations.from_database()
        mock_load.assert_called_once_with(db_col)

        assert populated_collection.save_to_db() == 5
        assert populated_collection.is_dirty is False
        mock_save.assert_called_once_with(populated_collection)

        assert populated_collection.load_from_db() == 5
        assert populated_collection.refresh() == 5
        assert len(populated_collection) == 0

    out_path = tmp_path / "locs.json"
    col = Locations()
    col.create(name="United States", category=JurisdictionCategory.COUNTRY)
    assert col.export_file(out_path) == 1
    fresh = Locations()
    assert fresh.import_file(out_path) == 1
    assert len(fresh) == 1
