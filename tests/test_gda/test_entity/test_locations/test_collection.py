"""Path: tests/test_gda/test_entity/test_locations/test_collection.py

Unit, regression, and integration test suite for the Locations collection class.

Operational Role:
    Verifies collection-level initialization, CRUD operations, URN and alias indexing,
    relational containment, cascading soft-delete/tombstone propagation, database
    persistence synchronization, and refresh behaviors for Locations collections.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from gda.core.errors import ModelFormatError
from gda.entity.locations.collection import Locations
from gda.entity.locations.errors import LocationHierarchyError, LocationNotFoundError
from gda.enums.location import JurisdictionCategory
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import LocationID
from gda.model.base.audit import AuditStamp
from gda.model.base.name import NameThing
from gda.model.base.tombstone import Tombstone
from gda.model.entity.location import Location

__version__ = "1.0.0+build.8"


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
    now = IsoTimestamp.now_utc()
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

    # Verify tombstoned entity returns False for 'in' check across all token formats
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
    now = IsoTimestamp.now_utc()
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
# GROUP 2: MUTATIONS & INDEX SYNCHRONIZATION (add, update, create)
# ==============================================================================


@pytest.mark.regression
def test_locations_add_rejects_non_location_type(
    empty_collection: Locations,
) -> None:
    """Verify add() raises TypeError when given a non-Location instance."""
    with pytest.raises(TypeError, match="Expected Location instance"):
        empty_collection.add("not_a_location")  # type: ignore[arg-type]


@pytest.mark.regression
def test_locations_add_filters_blank_aliases(
    empty_collection: Locations,
) -> None:
    """Verify add() skips empty or whitespace-only aliases during alias indexing."""
    now = IsoTimestamp.now_utc()
    loc = Location.create(
        location_id=LocationID("LOC-000001"),
        audit=AuditStamp(created_at=now, updated_at=now),
        name=NameThing.create(raw="Node", canonical="Node"),
        category=JurisdictionCategory.COUNTRY,
        canonical_urn="urn:gda:loc:node",
        tombstone=Tombstone[LocationID](),
    )
    loc = loc.add_alias("Valid Alias")
    object.__setattr__(loc.name, "aliases", [*loc.name.aliases, "   "])
    empty_collection.add(loc)
    assert "valid alias" in empty_collection._alias_index
    assert "" not in empty_collection._alias_index


@pytest.mark.regression
def test_locations_update_replaces_and_reindexes(
    populated_collection: Locations,
) -> None:
    """Verify update() replaces existing record and cleans stale urn/alias indexes."""
    loc = populated_collection["LOC-000004"]
    updated = loc.add_alias("Bow Village").update_urn(
        "urn:gda:loc:united_states:nh:merrimack:bow_new"
    )

    populated_collection.update(updated)
    assert "urn:gda:loc:united_states:nh:merrimack:bow_new" in populated_collection
    assert "urn:gda:loc:united_states:nh:merrimack:bow" not in populated_collection
    assert (
        populated_collection["LOC-000004"].canonical_urn
        == "urn:gda:loc:united_states:nh:merrimack:bow_new"
    )


@pytest.mark.regression
def test_locations_update_purges_removed_alias(
    populated_collection: Locations,
) -> None:
    """Verify update() purges alias from _alias_index when an alias is deleted."""
    loc = populated_collection["LOC-000004"]
    loc_with_alias = loc.add_alias("Temporary Alias")
    populated_collection.update(loc_with_alias)
    assert "temporary alias" in populated_collection._alias_index

    # Remove the alias and update the collection
    loc_without_alias = loc_with_alias.remove_alias("Temporary Alias")
    populated_collection.update(loc_without_alias)
    assert "temporary alias" not in populated_collection._alias_index


@pytest.mark.regression
def test_locations_update_handles_unindexed_or_blank_old_aliases(
    populated_collection: Locations,
) -> None:
    """Verify update() handles old records containing unindexed or whitespace aliases."""
    loc = populated_collection["LOC-000004"]
    # Manually inject a blank alias and an alias mapped to another ID into old_loc
    object.__setattr__(loc.name, "aliases", ["   ", "Mismatched Alias"])
    populated_collection._registry[loc.id] = loc
    populated_collection._alias_index["mismatched alias"] = LocationID("LOC-999999")

    # Update with clean entity
    clean_loc = loc.update_name("Bow Township")
    object.__setattr__(clean_loc.name, "aliases", ["Clean Alias"])
    populated_collection.update(clean_loc)

    # Mismatched alias in index must not be deleted because it pointed to another ID
    assert populated_collection._alias_index.get("mismatched alias") == LocationID("LOC-999999")
    assert "clean alias" in populated_collection._alias_index


@pytest.mark.regression
def test_locations_update_rejects_non_location_or_missing_id(
    empty_collection: Locations,
) -> None:
    """Verify update() raises TypeError on non-Location and LocationNotFoundError on missing ID."""
    with pytest.raises(TypeError, match="Expected Location instance"):
        empty_collection.update("not_a_loc")  # type: ignore[arg-type]

    now = IsoTimestamp.now_utc()
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
    assert "granite state" in empty_collection._alias_index


@pytest.mark.regression
def test_locations_create_raises_on_blank_name(
    empty_collection: Locations,
) -> None:
    """Verify create() raises ModelFormatError when name is blank or pure whitespace."""
    with pytest.raises(ModelFormatError, match="Location name cannot be blank"):
        empty_collection.create(name="   ", category=JurisdictionCategory.COUNTRY)


# ==============================================================================
# GROUP 3: HIERARCHY BUILDING & SOFT DELETION
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
def test_locations_soft_delete_with_cascading_reparent(
    populated_collection: Locations,
) -> None:
    """Verify soft_delete retires target and reparents child subtree."""
    bow_id = LocationID("LOC-000004")
    center_id = LocationID("LOC-000005")

    now = IsoTimestamp.now_utc()
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

    retired = populated_collection.soft_delete(
        bow_id, reason="Annexation", superseded_by=replacement_bow.id
    )
    assert retired.tombstone.is_deprecated is True
    assert retired.tombstone.superseded_by == replacement_bow.id

    child = populated_collection._registry[center_id]
    assert child.parent_id == replacement_bow.id


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


@pytest.mark.regression
def test_locations_soft_delete_raises_on_category_mismatch(
    populated_collection: Locations,
) -> None:
    """Verify soft_delete raises LocationHierarchyError on category tier mismatch."""
    with pytest.raises(LocationHierarchyError, match="must match the jurisdiction tier"):
        populated_collection.soft_delete("LOC-000004", superseded_by="LOC-000001")


# ==============================================================================
# GROUP 4: PERSISTENCE & FILE I/O FACADES
# ==============================================================================


@pytest.mark.integration
def test_locations_save_to_db_and_load_from_db_facades(
    populated_collection: Locations,
) -> None:
    """Verify save_to_db, load_from_db, and refresh invoke underlying helpers cleanly."""
    mock_save = MagicMock(return_value=5)
    mock_load = MagicMock(return_value=5)

    with (
        patch("gda.entity.locations.collection.save_to_db", mock_save),
        patch("gda.entity.locations.collection.load_from_db", mock_load),
    ):
        written = populated_collection.save_to_db()
        assert written == 5
        assert populated_collection.is_dirty is False

        # Directly invoke the load_from_db facade method
        loaded_direct = populated_collection.load_from_db()
        assert loaded_direct == 5

        # Invoke refresh which delegates to load_from_db
        loaded = populated_collection.refresh()
        assert loaded == 5
        assert populated_collection.is_dirty is False


@pytest.mark.integration
def test_locations_file_io_facades(populated_collection: Locations, tmp_path: Path) -> None:
    """Verify export_file and import_file pass through paths to util helpers."""
    out_path = tmp_path / "locations_export.json"
    mock_export = MagicMock(return_value=5)
    mock_import = MagicMock(return_value=5)

    with (
        patch("gda.entity.locations.collection.export_file", mock_export),
        patch("gda.entity.locations.collection.import_file", mock_import),
    ):
        res_exp = populated_collection.export_file(out_path, include_graveyard=True)
        assert res_exp == 5
        mock_export.assert_called_once_with(populated_collection, out_path, include_graveyard=True)

        res_imp = populated_collection.import_file(out_path)
        assert res_imp == 5
        mock_import.assert_called_once_with(populated_collection, out_path)


@pytest.mark.integration
def test_locations_from_database_factory() -> None:
    """Verify from_database factory instantiates collection and populates from SQLite."""
    mock_load = MagicMock(return_value=3)
    with patch("gda.entity.locations.collection.load_from_db", mock_load):
        col = Locations.from_database()
        assert isinstance(col, Locations)
        mock_load.assert_called_once_with(col)
