"""Path: tests/test_gda/test_entity/test_sites/test_collection.py

Comprehensive test suite verifying the Sites in-memory collection and lookup index.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from gda.core.errors import ModelFormatError
from gda.entity.sites.collection import Sites
from gda.entity.sites.errors import SiteNotFoundError, SiteValidationError
from gda.enums.site import SiteType
from gda.model.atom.id import LocationID, SiteID

__version__ = "1.0.0+build.5"


# ==============================================================================
# GROUP 1: INITIALIZATION, CONTAINMENT & RETRIEVAL CONTRACTS
# Note: Verifies dict-like accessors, len counts, and URN/alias containment
# ==============================================================================


@pytest.mark.unit
def test_sites_initialization_with_entities_populates_indexes(make_site) -> None:
    """Verify Sites initializes cleanly and populates secondary indexes."""
    site = make_site("SID-000001")
    coll = Sites([site])

    assert len(coll) == 1
    assert site.id in coll
    assert "SID-000001" in coll
    assert site.canonical_urn in coll
    assert coll[site.id] == site
    assert coll[str(site.id)] == site
    assert coll[site.canonical_urn] == site
    assert coll.get("SID-000001") == site
    assert coll.get(site.id) == site
    assert coll.get("SID-999999", default=None) is None


@pytest.mark.unit
def test_sites_contains_tombstoned_returns_false(tombstoned_site) -> None:
    """Verify tombstoned site is excluded from len and containment checks."""
    coll = Sites([tombstoned_site])

    assert len(coll) == 0
    assert tombstoned_site.id not in coll
    assert "SID-000002" not in coll
    assert tombstoned_site.canonical_urn not in coll
    assert coll.get(tombstoned_site.id) is None
    assert coll.get("SID-000002") is None
    assert "SID-999999" not in coll
    assert "urn:gda:site:not:real" not in coll


@pytest.mark.regression
def test_sites_contains_and_getitem_non_string_non_siteid(make_site) -> None:
    """Verify __contains__ and __getitem__ handle non-str/non-SiteID objects."""
    site = make_site("SID-000001")
    coll = Sites([site])

    assert (12345 in coll) is False

    with pytest.raises(SiteNotFoundError, match="Site not found"):
        _ = coll[12345]  # type: ignore[index]


@pytest.mark.regression
def test_sites_getitem_missing_or_tombstoned_raises_not_found_error(tombstoned_site) -> None:
    """Verify getitem on missing or deprecated site raises SiteNotFoundError."""
    coll = Sites([tombstoned_site])

    with pytest.raises(SiteNotFoundError, match="Site not found"):
        _ = coll["SID-000099"]

    with pytest.raises(SiteNotFoundError, match="Site has been tombstoned"):
        _ = coll["SID-000002"]

    with pytest.raises(SiteNotFoundError, match="Site has been tombstoned"):
        _ = coll[tombstoned_site.id]

    with pytest.raises(SiteNotFoundError, match="Site has been tombstoned"):
        _ = coll[tombstoned_site.canonical_urn]


@pytest.mark.regression
def test_sites_add_type_error_on_invalid_instance() -> None:
    """Verify add raises TypeError when passed non-Site object."""
    coll = Sites()
    with pytest.raises(TypeError, match="Expected Site instance"):
        coll.add("not-a-site")  # type: ignore[arg-type]


# ==============================================================================
# GROUP 2: UPDATE AND MUTATION INDEX SYNCHRONIZATION
# Note: Verifies updating site updates aliases, URNs, location and category buckets
# ==============================================================================


@pytest.mark.regression
def test_sites_update_reindexes_aliases_and_buckets(make_site) -> None:
    """Verify update cleanly swaps alias keys and bucket index entries."""
    site = make_site("SID-000001", category=SiteType.CHURCH)
    site = site.add_alias("Old Chapel")
    coll = Sites([site])

    assert coll._alias_index.get("old chapel") == site.id
    assert site.id in coll._category_index[SiteType.CHURCH]

    updated_site = (
        site.update_category(SiteType.CEMETERY)
        .remove_alias("Old Chapel")
        .update_location("LOC-000002")
        .update_urn("urn:gda:site:us:nh:bow:new_urn_s000001")
    )
    coll.update(updated_site)

    assert "old chapel" not in coll._alias_index
    assert site.id not in coll._category_index[SiteType.CHURCH]
    assert site.id in coll._category_index[SiteType.CEMETERY]
    assert site.id not in coll._location_index[LocationID("LOC-000001")]
    assert site.id in coll._location_index[LocationID("LOC-000002")]
    assert coll._urn_index["urn:gda:site:us:nh:bow:new_urn_s000001"] == site.id


@pytest.mark.regression
def test_sites_update_location_retains_bucket_when_peers_exist(make_site) -> None:
    """Verify update removes site from location bucket without deleting bucket if peers exist (branch 185->188)."""
    site1 = make_site("SID-000001", location_id="LOC-000001")
    site2 = make_site("SID-000002", location_id="LOC-000001")
    coll = Sites([site1, site2])

    assert len(coll._location_index[LocationID("LOC-000001")]) == 2

    moved_site1 = site1.update_location("LOC-000002")
    coll.update(moved_site1)

    assert LocationID("LOC-000001") in coll._location_index
    assert SiteID("SID-000002") in coll._location_index[LocationID("LOC-000001")]
    assert SiteID("SID-000001") not in coll._location_index[LocationID("LOC-000001")]


@pytest.mark.regression
def test_sites_update_category_retains_bucket_when_peers_exist(make_site) -> None:
    """Verify update removes site from category bucket without deleting bucket if peers exist."""
    site1 = make_site("SID-000001", category=SiteType.CHURCH)
    site2 = make_site("SID-000002", category=SiteType.CHURCH)
    coll = Sites([site1, site2])

    assert len(coll._category_index[SiteType.CHURCH]) == 2

    moved_site1 = site1.update_category(SiteType.CEMETERY)
    coll.update(moved_site1)

    assert SiteType.CHURCH in coll._category_index
    assert SiteID("SID-000002") in coll._category_index[SiteType.CHURCH]
    assert SiteID("SID-000001") not in coll._category_index[SiteType.CHURCH]


@pytest.mark.regression
def test_sites_update_unchanged_fields_and_no_aliases(make_site) -> None:
    """Verify update where fields do not change and site has no aliases."""
    site = make_site("SID-000001", category=SiteType.CHURCH, location_id="LOC-000001")
    coll = Sites([site])

    modified = site.update_active(False)
    coll.update(modified)

    assert coll["SID-000001"].is_active is False
    assert site.id in coll._location_index[LocationID("LOC-000001")]
    assert site.id in coll._category_index[SiteType.CHURCH]


@pytest.mark.regression
def test_sites_update_alias_key_not_matching_target_id(make_site) -> None:
    """Verify update cleanly bypasses alias deletion if alias points elsewhere."""
    site = make_site("SID-000001").add_alias("Shared Alias")
    coll = Sites([site])

    coll._alias_index["shared alias"] = SiteID("SID-000099")

    updated = site.remove_alias("Shared Alias")
    coll.update(updated)

    assert coll._alias_index.get("shared alias") == SiteID("SID-000099")


@pytest.mark.regression
def test_sites_update_missing_site_raises_site_not_found_error(make_site) -> None:
    """Verify update on unregistered site raises SiteNotFoundError."""
    site = make_site("SID-000001")
    coll = Sites()

    with pytest.raises(SiteNotFoundError, match="not found in registry"):
        coll.update(site)

    with pytest.raises(TypeError, match="Expected Site instance"):
        coll.update("not-a-site")  # type: ignore[arg-type]


# ==============================================================================
# GROUP 3: QUERY AND FACADE CONVENIENCE ROUTINES
# Note: Verifies find_by_location, find_by_category, soft_delete, and undelete
# ==============================================================================


@pytest.mark.regression
def test_sites_iteration_and_iter_all(make_site, tombstoned_site) -> None:
    """Verify __iter__ (lines 93-95) and iter_all (line 99) yield active vs all records."""
    active = make_site("SID-000001")
    coll = Sites([active, tombstoned_site])

    active_iter = list(coll)
    assert len(active_iter) == 1
    assert active_iter[0].id == active.id

    all_iter = list(coll.iter_all())
    assert len(all_iter) == 2


@pytest.mark.regression
def test_sites_find_by_location_and_category_returns_active_entities(make_site) -> None:
    """Verify querying by location and category returns active sites."""
    site1 = make_site("SID-000001", location_id="LOC-000001", category=SiteType.CHURCH)
    site2 = make_site("SID-000002", location_id="LOC-000001", category=SiteType.CEMETERY)
    coll = Sites([site1, site2])

    loc_sites = coll.find_by_location("LOC-000001")
    assert len(loc_sites) == 2
    assert set(s.id for s in loc_sites) == {site1.id, site2.id}

    assert coll.find_by_location("LOC-000099") == []
    assert coll.find_by_location(LocationID("LOC-000099")) == []

    church_sites = coll.find_by_category(SiteType.CHURCH)
    assert len(church_sites) == 1
    assert church_sites[0].id == site1.id
    assert coll.find_by_category(SiteType.HOSPITAL) == []
    assert coll.find_by_category("CHURCH") == [site1]


@pytest.mark.regression
def test_sites_soft_delete_and_undelete_lifecycle_flow(
    make_site, mock_locations_collection
) -> None:
    """Verify soft_delete and undelete transitions on collection."""
    site = make_site("SID-000001", location_id="LOC-000001")
    coll = Sites([site])

    assert len(coll) == 1
    retired = coll.soft_delete("SID-000001", reason="Facility closed")
    assert retired.tombstone.is_deprecated is True
    assert len(coll) == 0
    assert coll.is_dirty is True

    restored = coll.undelete("SID-000001", locations_collection=mock_locations_collection)
    assert restored.tombstone.is_deprecated is False
    assert len(coll) == 1


# ==============================================================================
# GROUP 4: CREATION FACTORY & PERSISTENCE DELEGATION
# Note: Verifies create minting, FK verification, and database facades
# ==============================================================================


@pytest.mark.regression
def test_sites_create_auto_mints_id_and_urn() -> None:
    """Verify create generates sequential ID and canonical URN with smart ID suffix."""
    coll = Sites()
    new_site = coll.create(
        name="Bow Center Cemetery",
        category=SiteType.CEMETERY,
        location_id="LOC-000001",
        alternate_names=["Old Center Ground"],
    )

    assert new_site.id == SiteID("SID-000001")
    assert new_site.canonical_urn == "urn:gda:site:loc_000001:bow_center_cemetery_s000001"
    assert new_site.id in coll
    assert "Old Center Ground" in new_site.aliases
    assert len(coll) == 1


@pytest.mark.regression
def test_sites_create_with_active_location_collection_happy_path(mock_locations_collection) -> None:
    """Verify create passes when location collection contains target (branch 290->295)."""
    coll = Sites()
    new_site = coll.create(
        name="New Meetinghouse",
        category=SiteType.CHURCH,
        location_id="LOC-000001",
        locations_collection=mock_locations_collection,
    )

    assert new_site.id in coll
    assert new_site.canonical_urn == "urn:gda:site:loc_000001:new_meetinghouse_s000001"


@pytest.mark.regression
def test_sites_create_explicit_urn_passed() -> None:
    """Verify create honors explicitly supplied canonical_urn."""
    coll = Sites()
    new_site = coll.create(
        name="Bow Center Cemetery",
        category=SiteType.CEMETERY,
        location_id="LOC-000001",
        canonical_urn="urn:gda:site:us:nh:bow:cemetery_s000001",
    )
    assert new_site.canonical_urn == "urn:gda:site:us:nh:bow:cemetery_s000001"


@pytest.mark.regression
def test_sites_create_missing_location_raises_validation_error() -> None:
    """Verify create validates governing location presence when collection provided."""
    coll = Sites()
    loc_coll = MagicMock()
    loc_coll.__contains__.return_value = False

    with pytest.raises(SiteValidationError, match="does not exist or is tombstoned"):
        coll.create(
            name="Bow Center Cemetery",
            category=SiteType.CEMETERY,
            location_id="LOC-000001",
            locations_collection=loc_coll,
        )


@pytest.mark.regression
def test_sites_create_blank_name_raises_model_format_error() -> None:
    """Verify create with whitespace name delegates to NameThing and raises ModelFormatError."""
    coll = Sites()
    with pytest.raises(ModelFormatError, match="cannot be empty"):
        coll.create(name="   ", category=SiteType.OTHER, location_id="LOC-000001")


@pytest.mark.regression
@patch("gda.entity.sites.collection.load_from_db")
@patch("gda.entity.sites.collection.save_to_db")
def test_sites_persistence_facade_delegation(
    mock_save: MagicMock,
    mock_load: MagicMock,
) -> None:
    """Verify load_from_db, save_to_db, refresh, and from_database delegate correctly."""
    mock_load.return_value = 2
    mock_save.return_value = 2

    coll = Sites.from_database()
    assert mock_load.call_count == 1

    loaded = coll.load_from_db()
    assert loaded == 2
    mock_load.assert_called_with(coll)

    saved = coll.save_to_db()
    assert saved == 2
    mock_save.assert_called_once_with(coll)
    assert coll.is_dirty is False

    refreshed = coll.refresh()
    assert refreshed == 2


@pytest.mark.regression
@patch("gda.entity.sites.collection.import_file")
@patch("gda.entity.sites.collection.export_file")
def test_sites_io_facade_delegation(
    mock_export: MagicMock,
    mock_import: MagicMock,
) -> None:
    """Verify import_file and export_file facade methods delegate directly to util (lines 263, 267)."""
    mock_import.return_value = 5
    mock_export.return_value = 5

    coll = Sites()
    assert coll.import_file("dummy.json") == 5
    mock_import.assert_called_once_with(coll, "dummy.json")

    assert coll.export_file("dummy_out.json", include_graveyard=False) == 5
    mock_export.assert_called_once_with(coll, "dummy_out.json", include_graveyard=False)
