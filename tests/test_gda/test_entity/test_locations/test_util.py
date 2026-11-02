"""Path: tests/test_gda/test_entity/test_locations/test_util.py

Unit, regression, and integration test suite for location domain utilities (LU).

Operational Role:
    Verifies jurisdictional hierarchy construction, graveyard lifecycle and soft-delete
    rules, atomic child reparenting, file serialization round-trips, and SQLite database
    persistence operations governing Locations collections.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from gda.core.errors import ModelFormatError
from gda.entity.locations.collection import Locations
from gda.entity.locations.errors import LocationHierarchyError
from gda.entity.locations.util import (
    build_jurisdiction_hierarchy,
    can_tombstone,
    export_file,
    import_file,
    load_from_db,
    save_to_db,
    tombstone_location,
)
from gda.enums.archival import NoteType
from gda.enums.location import JurisdictionCategory
from gda.enums.vital import HistoricNameType
from gda.io.json import GDAJsonIO
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import LocationID
from gda.model.base.audit import AuditStamp
from gda.model.base.name import NameThing
from gda.model.base.note import Note
from gda.model.base.tombstone import Tombstone
from gda.model.entity.location import Location

__version__ = "1.0.0+build.19"


# ==============================================================================
# GROUP 1: JURISDICTION HIERARCHY BUILDER (build_jurisdiction_hierarchy)
# ==============================================================================


@pytest.mark.regression
def test_build_jurisdiction_hierarchy_creates_single_country(
    empty_collection: Locations,
) -> None:
    """Verify building only a country mints and registers a COUNTRY node."""
    loc = build_jurisdiction_hierarchy(empty_collection, country="United States")
    assert loc.category == JurisdictionCategory.COUNTRY
    assert loc.canonical_urn == "urn:gda:loc:united_states"
    assert loc.name.canonical == "United States"
    assert loc.id == LocationID("LOC-000001")
    assert loc.parent_id is None
    assert len(empty_collection) == 1


@pytest.mark.regression
def test_build_jurisdiction_hierarchy_resolves_existing_nodes_without_duplication(
    empty_collection: Locations,
) -> None:
    """Verify subsequent hierarchy builds reuse existing nodes by canonical URN."""
    loc1 = build_jurisdiction_hierarchy(
        empty_collection, country="USA", state="NH", county="Merrimack"
    )
    loc2 = build_jurisdiction_hierarchy(
        empty_collection, country="USA", state="NH", county="Merrimack"
    )
    assert loc1.id == loc2.id
    assert len(empty_collection) == 3


@pytest.mark.regression
def test_build_jurisdiction_hierarchy_increments_past_max_id(
    empty_collection: Locations,
) -> None:
    """Verify deterministic max+1 minting past existing entries."""
    now = IsoTimestamp.now_utc()
    existing = Location.create(
        location_id=LocationID("LOC-000007"),
        audit=AuditStamp(created_at=now, updated_at=now),
        name=NameThing.create(raw="Existing Top Tier", canonical="Existing Top Tier"),
        category=JurisdictionCategory.COUNTRY,
        canonical_urn="urn:gda:loc:top",
        tombstone=Tombstone[LocationID](),
    )
    empty_collection.add(existing)

    new_loc = build_jurisdiction_hierarchy(empty_collection, country="Canada")
    assert new_loc.id == LocationID("LOC-000008")


@pytest.mark.regression
def test_build_jurisdiction_hierarchy_full_five_tiers(
    empty_collection: Locations,
) -> None:
    """Verify complete 5-tier descending hierarchy creation."""
    leaf = build_jurisdiction_hierarchy(
        empty_collection,
        country="United States",
        state="New Hampshire",
        county="Merrimack",
        township="Bow",
        local="Bow Center",
    )
    assert leaf.category == JurisdictionCategory.MUNICIPALITY
    assert (
        leaf.canonical_urn
        == "urn:gda:loc:united_states:new_hampshire:merrimack:bow:bow_center"
    )
    assert leaf.parent_id is not None
    assert len(empty_collection) == 5


@pytest.mark.regression
def test_build_jurisdiction_hierarchy_statoid_only(
    empty_collection: Locations,
) -> None:
    """Verify hierarchy terminates at statoid tier when county is omitted."""
    leaf = build_jurisdiction_hierarchy(empty_collection, country="USA", state="Maine")
    assert leaf.category == JurisdictionCategory.STATOID
    assert leaf.name.canonical == "Maine"
    assert len(empty_collection) == 2


@pytest.mark.regression
def test_build_jurisdiction_hierarchy_independent_city_pattern_7(
    empty_collection: Locations,
) -> None:
    """Verify Pattern 7 independent city directly under statoid when county and township are omitted."""
    leaf = build_jurisdiction_hierarchy(
        empty_collection,
        country="USA",
        state="Virginia",
        county=None,
        township=None,
        local="Richmond",
    )
    assert leaf.category == JurisdictionCategory.MUNICIPALITY
    assert leaf.canonical_urn == "urn:gda:loc:usa:virginia:richmond"
    assert leaf.parent_id == empty_collection.get("urn:gda:loc:usa:virginia").id
    assert len(empty_collection) == 3


@pytest.mark.regression
def test_build_jurisdiction_hierarchy_independent_locality_without_township(
    empty_collection: Locations,
) -> None:
    """Verify Pattern 6 municipality directly under county when township is omitted."""
    leaf = build_jurisdiction_hierarchy(
        empty_collection,
        country="USA",
        state="California",
        county="Los Angeles",
        township=None,
        local="Los Angeles",
    )
    assert leaf.category == JurisdictionCategory.MUNICIPALITY
    assert leaf.canonical_urn == "urn:gda:loc:usa:california:los_angeles:los_angeles"
    assert (
        leaf.parent_id
        == empty_collection.get("urn:gda:loc:usa:california:los_angeles").id
    )
    assert len(empty_collection) == 4


@pytest.mark.regression
def test_build_jurisdiction_hierarchy_township_without_locality(
    empty_collection: Locations,
) -> None:
    """Verify hierarchy terminates at civil township tier when local is omitted."""
    leaf = build_jurisdiction_hierarchy(
        empty_collection,
        country="USA",
        state="NH",
        county="Merrimack",
        township="Bow",
        local=None,
    )
    assert leaf.category == JurisdictionCategory.CIVIL_TOWNSHIP
    assert leaf.is_primary_local_authority is True
    assert len(empty_collection) == 4


@pytest.mark.regression
def test_build_jurisdiction_hierarchy_missing_country_raises_error(
    empty_collection: Locations,
) -> None:
    """Verify omitting country raises ModelFormatError."""
    with pytest.raises(ModelFormatError, match="must contain a country"):
        build_jurisdiction_hierarchy(empty_collection, country="   ")


@pytest.mark.regression
def test_build_jurisdiction_hierarchy_subtiers_without_state_raises_error(
    empty_collection: Locations,
) -> None:
    """Verify attaching county without state raises ModelFormatError."""
    with pytest.raises(ModelFormatError, match="without state"):
        build_jurisdiction_hierarchy(
            empty_collection,
            country="USA",
            state=None,
            county="Merrimack",
        )


@pytest.mark.regression
def test_build_jurisdiction_hierarchy_township_without_county_raises_error(
    empty_collection: Locations,
) -> None:
    """Verify attaching township without county raises ModelFormatError."""
    with pytest.raises(ModelFormatError, match="without county"):
        build_jurisdiction_hierarchy(
            empty_collection,
            country="USA",
            state="NH",
            county=None,
            township="Bow",
        )


# ==============================================================================
# GROUP 2: GRAVEYARD VERIFICATION & RETIREMENT (can_tombstone)
# ==============================================================================


@pytest.mark.unit
def test_can_tombstone_returns_true_for_active_leaf_without_replacement(
    populated_collection: Locations,
) -> None:
    """Verify active leaf location with zero children can be tombstoned directly."""
    leaf_id = LocationID("LOC-000005")
    ok, err = can_tombstone(populated_collection, leaf_id)
    assert ok is True
    assert err is None


@pytest.mark.regression
def test_can_tombstone_fails_on_non_existent_target(
    populated_collection: Locations,
) -> None:
    """Verify non-existent target returns False with error diagnostic."""
    ok, err = can_tombstone(populated_collection, "LOC-999999")
    assert ok is False
    assert "does not exist in collection" in str(err)


@pytest.mark.regression
def test_can_tombstone_fails_on_already_tombstoned_target(
    populated_collection: Locations,
) -> None:
    """Verify already deprecated location returns False."""
    leaf_id = LocationID("LOC-000005")
    tombstone_location(populated_collection, leaf_id, reason="Obsolete")

    ok, err = can_tombstone(populated_collection, leaf_id)
    assert ok is False
    assert "already tombstoned" in str(err)


@pytest.mark.regression
def test_can_tombstone_fails_on_parent_without_replacement(
    populated_collection: Locations,
) -> None:
    """Verify parent with active children cannot be tombstoned without replacement."""
    parent_id = LocationID("LOC-000004")
    ok, err = can_tombstone(populated_collection, parent_id)
    assert ok is False
    assert "active child jurisdictions" in str(err)
    assert "no replacement 'superseded_by' was specified" in str(err)


@pytest.mark.regression
def test_can_tombstone_formats_overflow_when_more_than_three_children(
    populated_collection: Locations,
) -> None:
    """Verify error diagnostic formats child overflow when target has >3 active children."""
    parent_id = LocationID("LOC-000004")
    now = IsoTimestamp.now_utc()
    audit = AuditStamp(created_at=now, updated_at=now)

    for i in range(10, 14):
        cid = LocationID(f"LOC-0000{i}")
        populated_collection.add(
            Location.create(
                location_id=cid,
                audit=audit,
                name=NameThing.create(raw=f"Child {i}", canonical=f"Child {i}"),
                category=JurisdictionCategory.MUNICIPALITY,
                canonical_urn=f"urn:gda:loc:united_states:nh:merrimack:bow:c{i}",
                parent_id=parent_id,
                tombstone=Tombstone[LocationID](),
            )
        )

    ok, err = can_tombstone(populated_collection, parent_id)
    assert ok is False
    assert "total)" in str(err)


@pytest.mark.regression
def test_can_tombstone_fails_when_replacement_is_self(
    populated_collection: Locations,
) -> None:
    """Verify specifying target itself as superseded_by returns False."""
    leaf_id = LocationID("LOC-000005")
    ok, err = can_tombstone(populated_collection, leaf_id, superseded_by=leaf_id)
    assert ok is False
    assert "cannot be the entity itself" in str(err)


@pytest.mark.regression
def test_can_tombstone_fails_when_replacement_does_not_exist(
    populated_collection: Locations,
) -> None:
    """Verify non-existent replacement entity returns False."""
    leaf_id = LocationID("LOC-000005")
    ok, err = can_tombstone(populated_collection, leaf_id, superseded_by="LOC-888888")
    assert ok is False
    assert "does not exist in collection" in str(err)


@pytest.mark.regression
def test_can_tombstone_fails_when_replacement_is_itself_tombstoned(
    populated_collection: Locations,
) -> None:
    """Verify specifying an already retired replacement entity returns False."""
    leaf1 = LocationID("LOC-000005")
    now = IsoTimestamp.now_utc()
    audit = AuditStamp(created_at=now, updated_at=now)
    leaf2 = Location.create(
        location_id=LocationID("LOC-000006"),
        audit=audit,
        name=NameThing.create(raw="Old", canonical="Old"),
        category=JurisdictionCategory.MUNICIPALITY,
        canonical_urn="urn:gda:loc:old",
        tombstone=Tombstone[LocationID]().retire(timestamp=now),
    )
    populated_collection._registry[leaf2.id] = leaf2

    ok, err = can_tombstone(populated_collection, leaf1, superseded_by=leaf2.id)
    assert ok is False
    assert "itself tombstoned" in str(err)


@pytest.mark.regression
def test_can_tombstone_fails_on_category_mismatch(
    populated_collection: Locations,
) -> None:
    """Verify category mismatch between target and replacement returns False."""
    target_county = LocationID("LOC-000003")
    replacement_state = LocationID("LOC-000002")

    ok, err = can_tombstone(
        populated_collection,
        target_county,
        superseded_by=replacement_state,
    )
    assert ok is False
    assert "must match the jurisdiction tier" in str(err)


# ==============================================================================
# GROUP 3: ATOMIC RETIREMENT & REPARENTING (tombstone_location)
# ==============================================================================


@pytest.mark.smoke
def test_tombstone_location_leaf_without_replacement(
    populated_collection: Locations,
) -> None:
    """Verify retiring leaf entity mutates tombstone and updates registry."""
    leaf_id = LocationID("LOC-000005")
    retired = tombstone_location(
        populated_collection,
        leaf_id,
        reason="Boundary dissolved",
    )
    assert retired.tombstone.is_deprecated is True
    assert retired.tombstone.superseded_by is None
    assert populated_collection._registry[leaf_id].tombstone.is_deprecated is True
    assert leaf_id not in populated_collection
    assert leaf_id in populated_collection._registry


@pytest.mark.regression
def test_tombstone_location_atomically_reparents_active_children(
    populated_collection: Locations,
) -> None:
    """Verify retiring parent reparents all active children to replacement."""
    target_bow = LocationID("LOC-000004")
    now = IsoTimestamp.now_utc()
    audit = AuditStamp(created_at=now, updated_at=now)

    concord = Location.create(
        location_id=LocationID("LOC-000006"),
        audit=audit,
        name=NameThing.create(raw="Concord", canonical="Concord"),
        category=JurisdictionCategory.CIVIL_TOWNSHIP,
        canonical_urn="urn:gda:loc:united_states:nh:merrimack:concord",
        parent_id=LocationID("LOC-000003"),
        tombstone=Tombstone[LocationID](),
    )
    populated_collection.add(concord)

    retired = tombstone_location(
        populated_collection,
        loc_id=target_bow,
        reason="Annexed by Concord",
        superseded_by=concord.id,
    )

    assert retired.tombstone.is_deprecated is True
    assert retired.tombstone.superseded_by == concord.id

    child_center = populated_collection[LocationID("LOC-000005")]
    assert child_center.parent_id == concord.id


@pytest.mark.regression
def test_tombstone_location_raises_on_invalid_operation(
    populated_collection: Locations,
) -> None:
    """Verify tombstone_location raises LocationHierarchyError on validation failure."""
    with pytest.raises(LocationHierarchyError, match="does not exist in collection"):
        tombstone_location(populated_collection, "LOC-999999", reason="Error")


# ==============================================================================
# GROUP 4: FILE PERSISTENCE & ROUND-TRIP (import_file & export_file)
# ==============================================================================


@pytest.mark.integration
def test_import_file_non_existent_path_returns_zero(
    empty_collection: Locations,
    tmp_path: Path,
) -> None:
    """Verify import_file returns 0 when file does not exist."""
    missing = tmp_path / "missing.json"
    assert import_file(empty_collection, missing) == 0


@pytest.mark.integration
def test_export_file_and_import_file_round_trip(
    populated_collection: Locations,
    tmp_path: Path,
) -> None:
    """Verify exporting collection to JSON and re-importing restores all entities."""
    out_path = tmp_path / "export" / "locations.json"
    exported_count = export_file(populated_collection, out_path, include_graveyard=True)
    assert exported_count == 5
    assert out_path.exists()

    new_collection = Locations()
    imported_count = import_file(new_collection, out_path)
    assert imported_count == 5
    assert len(new_collection) == 5

    orig = populated_collection[LocationID("LOC-000004")]
    restored = new_collection[LocationID("LOC-000004")]
    assert orig.canonical_urn == restored.canonical_urn
    assert orig.is_primary_local_authority == restored.is_primary_local_authority


@pytest.mark.integration
def test_export_file_excludes_graveyard_when_flag_false(
    populated_collection: Locations,
    tmp_path: Path,
) -> None:
    """Verify export_file excludes tombstoned entities when include_graveyard is False."""
    tombstone_location(populated_collection, "LOC-000005", reason="Dissolved")
    out_path = tmp_path / "active_only.json"

    exported_count = export_file(
        populated_collection, out_path, include_graveyard=False
    )
    assert exported_count == 4


@pytest.mark.integration
def test_export_file_serializes_non_empty_historical_names(
    empty_collection: Locations,
    tmp_path: Path,
) -> None:
    """Verify export_file iterates and serializes non-empty historical names (covers branch 399->396)."""
    now = IsoTimestamp.now_utc()
    loc = Location.create(
        location_id=LocationID("LOC-000001"),
        audit=AuditStamp(created_at=now, updated_at=now),
        name=NameThing.create(
            raw="Old Province", canonical="Old Province"
        ).add_historic_variant(
            raw="Ancient Province",
            name="Ancient Province",
            historic_name_type=HistoricNameType.HISTORICAL,
        ),
        category=JurisdictionCategory.STATOID,
        canonical_urn="urn:gda:loc:old_prov",
        tombstone=Tombstone[LocationID](),
    )
    empty_collection.add(loc)
    out_path = tmp_path / "historic_export.json"
    written = export_file(empty_collection, out_path)
    assert written == 1
    assert out_path.exists()

    payload = GDAJsonIO.read(out_path)
    assert len(payload["locations"][0]["historical_names"]) == 1
    assert payload["locations"][0]["historical_names"][0]["raw"] == "Ancient Province"


@pytest.mark.integration
def test_import_file_deserializes_historical_names_and_notes(
    empty_collection: Locations,
    tmp_path: Path,
) -> None:
    """Verify import_file deserializes raw names, aliases, historical variants, and notes."""
    payload = {
        "locations": [
            {
                "id": "LOC-000001",
                "name": {"raw": "Old Towne", "canonical": "Old Towne"},
                "category": "MUNICIPALITY",
                "canonical_urn": "urn:gda:loc:old_towne",
                "parent_id": None,
                "is_primary_local_authority": True,
                "is_unincorporated": False,
                "alternate_names": ["Towne", "Old Towne", "Towne"],
                "historical_names": [
                    {
                        "raw": "Ancient Towne",
                        "canonical": "Ancient Towne",
                        "historic_name_type": HistoricNameType.HISTORICAL.value,
                    },
                    {
                        "raw_name": "Olde Towne",
                        "canonical_name": "Olde Towne",
                    },
                    "non_dict_variant_ignored",
                    {
                        "raw": "Ancient Towne",
                        "canonical": "Ancient Towne",
                        "historic_name_type": HistoricNameType.HISTORICAL.value,
                    },
                ],
                "notes": [
                    {
                        "note_id": "NOT-000001",
                        "note_type": NoteType.GENERAL.value,
                        "text": "Imported research memo.",
                        "audit": {
                            "created_at": "2026-10-18T12:00:00Z",
                            "updated_at": "2026-10-18T12:00:00Z",
                        },
                    }
                ],
            },
            {
                "id": "LOC-000002",
                "name": "Plain String Name",
                "category": "COUNTRY",
                "canonical_urn": "urn:gda:loc:plain",
            },
        ]
    }
    json_path = tmp_path / "custom_import.json"
    GDAJsonIO.write(json_path, payload)

    count = import_file(empty_collection, json_path)
    assert count == 2

    loc1 = empty_collection[LocationID("LOC-000001")]
    assert len(loc1.aliases) >= 1
    assert len(loc1.name.historic) == 2
    assert len(loc1.notes) == 1
    assert loc1.notes[0].text == "Imported research memo."

    loc2 = empty_collection[LocationID("LOC-000002")]
    assert loc2.name.canonical == "Plain String Name"


@pytest.mark.unit
def test_import_file_ingests_note_objects_directly(
    empty_collection: Locations,
    tmp_path: Path,
) -> None:
    """Verify import_file directly attaches Note objects when present in-memory."""
    now = IsoTimestamp.now_utc()
    mock_note = Note.create(
        note_id="NOT-000001",
        note_type=NoteType.GENERAL,
        text="Direct note object",
        audit=AuditStamp(created_at=now, updated_at=now),
    )

    in_memory_payload = {
        "locations": [
            {
                "id": "LOC-000001",
                "name": "Township",
                "category": "CIVIL_TOWNSHIP",
                "canonical_urn": "urn:gda:loc:township",
                "notes": [mock_note],
            }
        ]
    }

    dummy_path = tmp_path / "in_memory_notes.json"
    dummy_path.write_text("{}", encoding="utf-8")

    with patch("gda.io.json.GDAJsonIO.read", return_value=in_memory_payload):
        count = import_file(empty_collection, dummy_path)

    assert count == 1
    loc = empty_collection[LocationID("LOC-000001")]
    assert len(loc.notes) == 1
    assert loc.notes[0] is mock_note


# ==============================================================================
# GROUP 5: SQLITE DATABASE PERSISTENCE (load_from_db & save_to_db)
# ==============================================================================


@pytest.mark.integration
def test_save_to_db_and_load_from_db_execution(
    populated_collection: Locations,
) -> None:
    """Verify save_to_db commits entities and load_from_db populates collection."""
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [
        {"id": "LOC-000001", "name": "USA", "category": "COUNTRY"}
    ]

    mock_conn = MagicMock()
    mock_conn.execute.return_value = mock_cursor
    mock_conn_ctx = MagicMock()
    mock_conn_ctx.__enter__.return_value = mock_conn

    mock_tx = MagicMock()
    mock_tx_ctx = MagicMock()
    mock_tx_ctx.__enter__.return_value = mock_tx

    mock_session = MagicMock()
    mock_session.get_connection.return_value = mock_conn_ctx
    mock_session.transaction.return_value = mock_tx_ctx

    mock_mapper = MagicMock()
    mock_mapper.to_row.return_value = {"id": "LOC-000001", "name": "USA"}
    mock_mapper.from_row.return_value = populated_collection[LocationID("LOC-000001")]

    with (
        patch("gda.db.session.DatabaseSessionManager", return_value=mock_session),
        patch("gda.db.schema.SchemaManager") as mock_schema_cls,
        patch("gda.db.mapper.LocationRowMapper", return_value=mock_mapper),
    ):
        written = save_to_db(populated_collection)
        assert written == 5
        assert mock_tx.execute.call_count == 5

        fresh_collection = Locations()
        loaded = load_from_db(fresh_collection)
        assert loaded == 1
        assert len(fresh_collection) == 1
        mock_schema_cls.return_value.init_db.assert_called()
