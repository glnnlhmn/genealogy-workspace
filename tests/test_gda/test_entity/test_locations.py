"""Path: tests/test_gda/test_entity/test_locations.py

Defensive unit, regression, and smoke test suite for the Locations entity collection.

Operational Role:
    Verifies container protocols, in-place graveyard soft-deletions and restorations,
    cycle-safe redirect traversal, parent-child graph navigation, date-bounded
    historical naming resolution, fuzzy search ranking, and serialization parity.
"""

from __future__ import annotations

import pytest

from gda.entity.locations import Locations
from gda.enums.vital import NameStatus
from gda.model.atom.date import DateModifier, DateString, EventDate, IsoTimestamp
from gda.model.atom.id import LocationID
from gda.model.base.audit import AuditStamp
from gda.model.base.name import HistoricalName
from gda.model.base.time_period import TimePeriod
from gda.model.base.tombstone import TombstoneRecord
from gda.model.entity.location import JurisdictionCategory, Location

__version__ = "1.0.0+build.12"


# ==========================================================================
# TEST FIXTURES & HANDCRAFTED FACTORIES
# ==========================================================================


def _make_loc(
    loc_id: str,
    name: str,
    category: JurisdictionCategory = JurisdictionCategory.MUNICIPALITY,
    canonical_urn: str | None = None,
    parent_id: str | None = None,
    historical_names: list[HistoricalName] | None = None,
    alternate_names: list[str] | None = None,
    predecessor_ids: list[str] | None = None,
    successor_ids: list[str] | None = None,
    is_deprecated: bool = False,
    superseded_by: str | None = None,
) -> Location:
    """Handcraft a valid synthetic Location entity for testing."""
    urn = canonical_urn or f"urn:gda:loc:test:{name.lower().replace(' ', '_')}"
    pid = LocationID(parent_id) if parent_id else None
    preds = [LocationID(p) for p in (predecessor_ids or [])]
    succs = [LocationID(s) for s in (successor_ids or [])]
    superseded_atom = LocationID(superseded_by) if superseded_by else None

    tombstone = (
        TombstoneRecord[LocationID](
            is_deprecated=True,
            deprecated_at=IsoTimestamp.now_utc(),
            superseded_by=superseded_atom,
        )
        if is_deprecated
        else TombstoneRecord[LocationID]()
    )

    now = IsoTimestamp.now_utc()
    audit = AuditStamp(
        created_at=now,
        updated_at=now,
    )

    return Location(
        id=LocationID(loc_id),
        name=name,
        category=category,
        canonical_urn=urn,
        parent_id=pid,
        historical_names=historical_names or [],
        alternate_names=alternate_names or [],
        predecessor_ids=preds,
        successor_ids=succs,
        tombstone=tombstone,
        audit=audit,
    )


# ==========================================================================
# GROUP 1: Primary Initialization & Container Protocols
# Note: Verifies basic collection mechanics, len, iter, contains, and accessors
# ==========================================================================


@pytest.mark.unit
def test_init_empty_collection() -> None:
    """Verify empty initialization produces zero counts and clean dirty flag."""
    col = Locations()
    assert len(col) == 0
    assert col.count_active == 0
    assert col.count_graveyard == 0
    assert col.total_count == 0
    assert not col.is_dirty


@pytest.mark.unit
def test_init_prepopulated_collection() -> None:
    """Verify collection initializes with provided entities and indexes correctly."""
    loc = _make_loc("LOC-000001", "New Hampshire", JurisdictionCategory.STATOID)
    col = Locations([loc])
    assert len(col) == 1
    assert col.count_active == 1
    assert not col.is_dirty
    assert col["LOC-000001"] == loc


@pytest.mark.unit
def test_len_reflects_only_active_entities() -> None:
    """Verify len() reflects active items and excludes graveyard tombstones."""
    loc1 = _make_loc("LOC-000001", "Countryland", JurisdictionCategory.COUNTRY)
    loc2 = _make_loc("LOC-000002", "Old County", is_deprecated=True)
    col = Locations([loc1, loc2])

    assert len(col) == 1
    assert col.count_active == 1
    assert col.count_graveyard == 1
    assert col.total_count == 2


@pytest.mark.unit
def test_contains_distinguishes_active_from_graveyard() -> None:
    """Verify in operator returns True for active and False for tombstones or missing."""
    loc1 = _make_loc("LOC-000001", "Concord")
    loc2 = _make_loc("LOC-000002", "Defunct Town", is_deprecated=True)
    col = Locations([loc1, loc2])

    assert "LOC-000001" in col
    assert LocationID("LOC-000001") in col
    assert "LOC-000002" not in col
    assert LocationID("LOC-000002") not in col
    assert "LOC-999999" not in col
    assert "NOT-A-LOC-ID" not in col
    assert 12345 not in col


@pytest.mark.unit
def test_iter_orders_strictly_by_sort_key() -> None:
    """Verify iteration orders by administrative hierarchy rank then name."""
    loc_town = _make_loc("LOC-000003", "Bow", JurisdictionCategory.CIVIL_TOWNSHIP)
    loc_state = _make_loc("LOC-000002", "New Hampshire", JurisdictionCategory.STATOID)
    loc_country = _make_loc("LOC-000001", "United States", JurisdictionCategory.COUNTRY)

    col = Locations([loc_town, loc_state, loc_country])
    items = list(col)

    assert items[0].id == LocationID("LOC-000001")
    assert items[1].id == LocationID("LOC-000002")
    assert items[2].id == LocationID("LOC-000003")


@pytest.mark.unit
def test_getitem_and_get_fallbacks() -> None:
    """Verify subscript access, missing keys raising KeyError, and safe get fallbacks."""
    loc = _make_loc("LOC-000001", "Merrimack County")
    col = Locations([loc])

    assert col["LOC-000001"] == loc
    assert col.get("LOC-000001") == loc
    assert col.get("LOC-999999") is None
    assert col.get("LOC-999999", default=loc) == loc
    assert col.get("INVALID_TOKEN") is None

    with pytest.raises(KeyError, match="not found in active registry"):
        _ = col["LOC-999999"]


@pytest.mark.regression
def test_get_graveyard_resolution_and_dead_ends() -> None:
    """Verify get traverses to active successor and falls back to default on dead-ends."""
    loc_active = _make_loc("LOC-000001", "Active City")
    loc_redirect = _make_loc(
        "LOC-000002", "Interim Town", is_deprecated=True, superseded_by="LOC-000001"
    )
    loc_dead = _make_loc(
        "LOC-000003", "Dead End", is_deprecated=True, superseded_by=None
    )
    col = Locations([loc_active, loc_redirect, loc_dead])

    assert col.get("LOC-000001") == loc_active
    assert col.get("LOC-000002", resolve_redirects=True) == loc_active
    assert col.get("LOC-000002", resolve_redirects=False) is None
    assert (
        col.get("LOC-000002", default=loc_active, resolve_redirects=False) == loc_active
    )
    assert col.get("LOC-000003", resolve_redirects=True) is None
    assert (
        col.get("LOC-000003", default=loc_active, resolve_redirects=True) == loc_active
    )


@pytest.mark.unit
def test_keys_values_items_accessors() -> None:
    """Verify keys, values, and items accessors return active items."""
    loc = _make_loc("LOC-000001", "Concord")
    col = Locations([loc])

    assert col.keys() == (LocationID("LOC-000001"),)
    assert col.values() == (loc,)
    assert col.items() == ((LocationID("LOC-000001"), loc),)


@pytest.mark.unit
def test_add_type_validation_and_update() -> None:
    """Verify add enforces type checking and updates existing indexes cleanly."""
    col = Locations()
    with pytest.raises(TypeError, match="Expected Location instance"):
        col.add("Not a location")  # type: ignore[arg-type]

    parent = _make_loc("LOC-000001", "Parent Jurisdiction")
    loc1 = _make_loc(
        "LOC-000002",
        "Bow",
        canonical_urn="urn:gda:loc:test:bow1",
        parent_id="LOC-000001",
    )
    col.add(parent)
    col.add(loc1)
    assert col["LOC-000002"].canonical_urn == "urn:gda:loc:test:bow1"
    assert len(col.get_children("LOC-000001")) == 1

    loc2 = _make_loc("LOC-000002", "Bow Updated", canonical_urn="urn:gda:loc:test:bow2")
    col.add(loc2)
    assert col["LOC-000002"].name == "Bow Updated"
    assert col.get_by_urn("urn:gda:loc:test:bow2") == loc2
    assert col.get_by_urn("urn:gda:loc:test:bow1") is None
    assert len(col.get_children("LOC-000001")) == 0


@pytest.mark.regression
def test_add_replacing_entity_with_missing_urn_index_branch() -> None:
    """Verify add handles replacement when old entity URN was already pruned from secondary map."""
    loc1 = _make_loc("LOC-000001", "Bow", canonical_urn="urn:gda:loc:test:bow1")
    col = Locations([loc1])

    del col._by_urn["urn:gda:loc:test:bow1"]

    loc1_updated = _make_loc(
        "LOC-000001", "Bow City", canonical_urn="urn:gda:loc:test:bow_new"
    )
    col.add(loc1_updated)
    assert col["LOC-000001"].name == "Bow City"
    assert col.get_by_urn("urn:gda:loc:test:bow_new") == loc1_updated


@pytest.mark.unit
def test_remove_and_clear_mutations() -> None:
    """Verify remove evicts entities and clear resets all index state."""
    loc_parent = _make_loc("LOC-000001", "State", JurisdictionCategory.STATOID)
    loc_child1 = _make_loc(
        "LOC-000002",
        "County",
        JurisdictionCategory.COUNTY_EQUIVALENT,
        parent_id="LOC-000001",
    )
    loc_child2 = _make_loc(
        "LOC-000003",
        "Town",
        JurisdictionCategory.CIVIL_TOWNSHIP,
        parent_id="LOC-000001",
    )
    col = Locations([loc_parent, loc_child1, loc_child2])

    assert col.remove("LOC-000002") is True
    assert len(col.get_children("LOC-000001")) == 1

    assert col.remove("LOC-000003") is True
    assert len(col.get_children("LOC-000001")) == 0

    col.add(loc_child2)
    assert col.remove("LOC-000001") is True
    assert col.remove("INVALID_KEY") is False

    col.clear()
    assert len(col) == 0
    assert col.is_dirty


# ==========================================================================
# GROUP 2: Graveyard & Tombstone Management
# Note: Verifies soft-deletion, restoration, redirection, and cycle detection
# ==========================================================================


@pytest.mark.unit
def test_iter_graveyard_and_iter_all() -> None:
    """Verify iter_graveyard yields only tombstones while iter_all yields all items."""
    loc_act = _make_loc("LOC-000001", "Active City")
    loc_dep = _make_loc("LOC-000002", "Ghost Town", is_deprecated=True)
    col = Locations([loc_act, loc_dep])

    graveyard_ids = [loc.id for loc in col.iter_graveyard()]
    all_ids = [loc.id for loc in col.iter_all()]

    assert graveyard_ids == [LocationID("LOC-000002")]
    assert set(all_ids) == {LocationID("LOC-000001"), LocationID("LOC-000002")}


@pytest.mark.unit
def test_deprecate_in_place_success() -> None:
    """Verify deprecating an entity updates tombstone metadata in place."""
    loc1 = _make_loc("LOC-000001", "Merged Town")
    loc2 = _make_loc("LOC-000002", "Primary City")
    col = Locations([loc1, loc2])

    tombstoned = col.deprecate("LOC-000001", superseded_by="LOC-000002")
    assert tombstoned.tombstone.is_deprecated is True
    assert tombstoned.tombstone.superseded_by == LocationID("LOC-000002")
    assert col.count_active == 1
    assert col.count_graveyard == 1

    tombstoned2 = col.deprecate("LOC-000002", superseded_by=None)
    assert tombstoned2.tombstone.is_deprecated is True
    assert tombstoned2.tombstone.superseded_by is None
    assert col.count_active == 0
    assert col.count_graveyard == 2


@pytest.mark.regression
def test_deprecate_defensive_validations() -> None:
    """Verify deprecate rejects missing IDs, missing successors, and self-supersession."""
    loc1 = _make_loc("LOC-000001", "Town A")
    col = Locations([loc1])

    with pytest.raises(KeyError, match="not found in registry"):
        col.deprecate("LOC-999999")

    with pytest.raises(KeyError, match="Target superseded_by location"):
        col.deprecate("LOC-000001", superseded_by="LOC-999999")

    with pytest.raises(KeyError, match="Invalid superseded_by identifier"):
        col.deprecate("LOC-000001", superseded_by="INVALID_KEY")

    with pytest.raises(ValueError, match="cannot supersede itself"):
        col.deprecate("LOC-000001", superseded_by="LOC-000001")


@pytest.mark.unit
def test_restore_reverses_deprecation() -> None:
    """Verify restoring a deprecated entity clears tombstone flags back to active."""
    loc = _make_loc("LOC-000001", "Revived Town", is_deprecated=True)
    col = Locations([loc])
    assert len(col) == 0

    restored = col.restore("LOC-000001")
    assert restored.tombstone.is_deprecated is False
    assert restored.tombstone.superseded_by is None
    assert len(col) == 1

    with pytest.raises(KeyError, match="not found in registry"):
        col.restore("LOC-999999")


@pytest.mark.unit
def test_resolve_id_and_transparent_subscript_redirection() -> None:
    """Verify resolve_id traces single and multi-hop redirects and subscript resolves target."""
    loc_a = _make_loc(
        "LOC-000001", "Old Village", is_deprecated=True, superseded_by="LOC-000002"
    )
    loc_b = _make_loc(
        "LOC-000002", "Interim Town", is_deprecated=True, superseded_by="LOC-000003"
    )
    loc_c = _make_loc("LOC-000003", "Metro City")
    col = Locations([loc_a, loc_b, loc_c])

    assert col.resolve_id("LOC-000001") == LocationID("LOC-000003")
    assert col.resolve_id("LOC-000002") == LocationID("LOC-000003")
    assert col.resolve_id("LOC-000003") == LocationID("LOC-000003")
    assert col["LOC-000001"] == loc_c
    assert col.get("LOC-000001") == loc_c


@pytest.mark.regression
def test_resolve_id_handles_cycles_and_dead_ends() -> None:
    """Verify resolve_id returns None when encountering circular redirects or defunct ends."""
    loc_dead = _make_loc(
        "LOC-000001", "Dead End", is_deprecated=True, superseded_by=None
    )
    loc_cyc1 = _make_loc(
        "LOC-000002", "Cycle 1", is_deprecated=True, superseded_by="LOC-000003"
    )
    loc_cyc2 = _make_loc(
        "LOC-000003", "Cycle 2", is_deprecated=True, superseded_by="LOC-000002"
    )
    loc_missing_ptr = _make_loc(
        "LOC-000004", "Points Missing", is_deprecated=True, superseded_by="LOC-999999"
    )
    col = Locations([loc_dead, loc_cyc1, loc_cyc2, loc_missing_ptr])

    assert col.resolve_id("LOC-000001") is None
    assert col.resolve_id("LOC-000002") is None
    assert col.resolve_id("LOC-000004") is None
    assert col.resolve_id("LOC-999999") is None
    assert col.resolve_id("INVALID_KEY") is None

    with pytest.raises(KeyError, match="resolvable graveyard"):
        _ = col["LOC-000001"]


# ==========================================================================
# GROUP 3: Jurisdictional Graph & Relational Traversals
# Note: Verifies URN lookups, child resolution, ancestor trees, and lineages
# ==========================================================================


@pytest.mark.unit
def test_get_by_urn_exact_match() -> None:
    """Verify O(1) lookup via canonical URN string."""
    loc = _make_loc(
        "LOC-000001", "Bow", canonical_urn="urn:gda:loc:us:nh:merrimack:bow"
    )
    col = Locations([loc])

    assert col.get_by_urn("urn:gda:loc:us:nh:merrimack:bow") == loc
    assert col.get_by_urn("urn:gda:loc:unknown") is None


@pytest.mark.unit
def test_get_children_and_ancestors() -> None:
    """Verify upward ancestor chains and downward direct child listings."""
    loc_us = _make_loc("LOC-000001", "United States", JurisdictionCategory.COUNTRY)
    loc_nh = _make_loc(
        "LOC-000002",
        "New Hampshire",
        JurisdictionCategory.STATOID,
        parent_id="LOC-000001",
    )
    loc_mer = _make_loc(
        "LOC-000003",
        "Merrimack County",
        JurisdictionCategory.COUNTY_EQUIVALENT,
        parent_id="LOC-000002",
    )
    loc_bow = _make_loc(
        "LOC-000004", "Bow", JurisdictionCategory.CIVIL_TOWNSHIP, parent_id="LOC-000003"
    )
    loc_dep_child = _make_loc(
        "LOC-000005",
        "Old Bow Settlement",
        JurisdictionCategory.CIVIL_TOWNSHIP,
        parent_id="LOC-000003",
        is_deprecated=True,
    )
    col = Locations([loc_us, loc_nh, loc_mer, loc_bow, loc_dep_child])

    children = col.get_children("LOC-000003")
    assert children == (loc_bow,)

    children_all = col.get_children("LOC-000003", include_graveyard=True)
    assert len(children_all) == 2

    col._children[LocationID("LOC-000003")].add(LocationID("LOC-999999"))
    assert len(col.get_children("LOC-000003")) == 1

    assert col.get_children("INVALID_KEY") == ()
    assert col.get_children("LOC-999999") == ()

    ancestors = col.get_ancestors("LOC-000004")
    assert ancestors == (loc_mer, loc_nh, loc_us)
    assert col.get_ancestors("LOC-999999") == ()
    assert col.get_ancestors("INVALID_KEY") == ()


@pytest.mark.regression
def test_get_ancestors_with_graveyard_and_cycle_safety() -> None:
    """Verify get_ancestors handles deprecated ancestors and cycles cleanly."""
    loc_dep_anc = _make_loc(
        "LOC-000001", "Old Colony", JurisdictionCategory.STATOID, is_deprecated=True
    )
    loc_active_child = _make_loc("LOC-000002", "County", parent_id="LOC-000001")
    col = Locations([loc_dep_anc, loc_active_child])

    assert col.get_ancestors("LOC-000002", include_graveyard=False) == ()
    assert len(col.get_ancestors("LOC-000002", include_graveyard=True)) == 1

    loc_a = _make_loc("LOC-000010", "A", parent_id="LOC-000011")
    loc_b = _make_loc("LOC-000011", "B", parent_id="LOC-000010")
    col.add(loc_a)
    col.add(loc_b)

    ancestors = col.get_ancestors("LOC-000010")
    assert len(ancestors) == 1
    assert ancestors[0].id == LocationID("LOC-000011")


@pytest.mark.unit
def test_get_predecessors_and_successors() -> None:
    """Verify lineage resolvers resolve recorded predecessor and successor entities."""
    loc_old = _make_loc("LOC-000001", "Old Territory")
    loc_new = _make_loc(
        "LOC-000002",
        "Partition A",
        predecessor_ids=["LOC-000001", "LOC-999999"],
        successor_ids=["LOC-000003", "LOC-999998"],
    )
    loc_fut = _make_loc("LOC-000003", "Future Metro")
    col = Locations([loc_old, loc_new, loc_fut])

    preds = col.get_predecessors("LOC-000002")
    succs = col.get_successors("LOC-000002")

    assert preds == (loc_old,)
    assert succs == (loc_fut,)
    assert col.get_predecessors("LOC-999999") == ()
    assert col.get_successors("LOC-999999") == ()


# ==========================================================================
# GROUP 4: Temporal Name Resolution & Hierarchy Formatting
# Note: Verifies HistoricalName period matching and formatted path strings
# ==========================================================================


@pytest.mark.unit
def test_get_name_at_date_boundary_conditions() -> None:
    """Verify historical name matches across dates, ranges, and missing bounds."""
    hist_bounded = HistoricalName(
        raw_name="New Amsterdam",
        canonical_name="New Amsterdam",
        status=NameStatus.PRIMARY,
        valid_period=TimePeriod(
            start_date=EventDate(date=DateString("1625")),
            end_date=EventDate(date=DateString("1664")),
        ),
    )
    hist_early = HistoricalName(
        raw_name="Early Settlement",
        status=NameStatus.PRIMARY,
        valid_period=TimePeriod(
            start_date=EventDate(date=DateString("1610")),
            end_date=EventDate(date=DateString("1624")),
        ),
    )
    hist_open_end = HistoricalName(
        raw_name="York Shire",
        status=NameStatus.PRIMARY,
        valid_period=TimePeriod(
            start_date=EventDate(date=DateString("1665")),
            end_date=None,
        ),
    )
    hist_non_primary = HistoricalName(
        raw_name="Manhatta",
        status=NameStatus.INDIGENOUS,
        valid_period=TimePeriod(
            start_date=EventDate(date=DateString("1500")),
            end_date=EventDate(date=DateString("1600")),
        ),
    )
    hist_no_period = HistoricalName(
        raw_name="Old York",
        status=NameStatus.PRIMARY,
        valid_period=None,
    )
    loc = _make_loc(
        "LOC-000001",
        "New York City",
        historical_names=[
            hist_no_period,
            hist_bounded,
            hist_early,
            hist_open_end,
            hist_non_primary,
        ],
    )
    col = Locations([loc])

    evt_query = EventDate(date=DateString("1640"), modifier=DateModifier.EXACT)
    assert col.get_name_at_date("LOC-000001", evt_query) == "New Amsterdam"
    assert col.get_name_at_date("LOC-000001", "1620") == "Early Settlement"
    assert col.get_name_at_date("LOC-000001", "1670") == "York Shire"
    assert col.get_name_at_date("LOC-000001", "1605") == "New York City"
    assert col.get_name_at_date("LOC-000001", "1550") == "New York City"
    assert col.get_name_at_date("LOC-000001", "NoYearGiven") == "New York City"
    assert col.get_name_at_date("LOC-000001", "circa spring") == "New York City"
    assert col.get_name_at_date("LOC-999999", "1650") == ""


@pytest.mark.regression
def test_get_name_at_date_start_only_and_end_only_bounds() -> None:
    """Verify temporal boundary branch conditions when start or end is absent."""
    hist_only_end = HistoricalName(
        raw_name="Before Colony",
        status=NameStatus.PRIMARY,
        valid_period=TimePeriod(
            start_date=None,
            end_date=EventDate(date=DateString("1650")),
        ),
    )
    loc = _make_loc("LOC-000001", "Town", historical_names=[hist_only_end])
    col = Locations([loc])

    assert col.get_name_at_date("LOC-000001", "1640") == "Before Colony"
    assert col.get_name_at_date("LOC-000001", "1655") == "Town"


@pytest.mark.unit
def test_format_hierarchy_with_dates() -> None:
    """Verify hierarchy path formatting with at_date historical evaluation."""
    loc_state = _make_loc("LOC-000001", "State Province")
    hist_town = HistoricalName(
        raw_name="Olde Towne",
        canonical_name="Olde Towne",
        status=NameStatus.PRIMARY,
        valid_period=TimePeriod(
            start_date=EventDate(date=DateString("1700")),
            end_date=EventDate(date=DateString("1750")),
        ),
    )
    loc_town = _make_loc(
        "LOC-000002",
        "Modern Town",
        parent_id="LOC-000001",
        historical_names=[hist_town],
    )
    col = Locations([loc_state, loc_town])

    path_at_date = col.format_hierarchy("LOC-000002", at_date="1725")
    assert path_at_date == "Olde Towne, State Province"

    path_reverse = col.format_hierarchy("LOC-000002", reverse=True)
    assert path_reverse == "State Province, Modern Town"
    assert col.format_hierarchy("LOC-999999") == ""


# ==========================================================================
# GROUP 5: Search, Query Filtering & Helper Protocols
# Note: Verifies name lookups, fuzzy matching, category filters, and serialization
# ==========================================================================


@pytest.mark.unit
def test_find_by_name_full_matching_permutations() -> None:
    """Verify name matching across raw names, display names, and alternate spellings."""
    hist = HistoricalName(
        raw_name="Fort Orange",
        canonical_name="Albany Settlement",
        alternate_spellings=["Fort Aurania"],
        status=NameStatus.HISTORICAL,
    )
    hist_no_alt = HistoricalName(
        raw_name="Beverwyck Historic",
        alternate_spellings=[],
        status=NameStatus.HISTORICAL,
    )
    loc_albany = _make_loc(
        "LOC-000001",
        "Albany",
        alternate_names=["Beverwijck"],
        historical_names=[hist, hist_no_alt],
        parent_id="LOC-000010",
    )
    loc_troy = _make_loc(
        "LOC-000002",
        "Troy",
        parent_id="LOC-000020",
    )
    col = Locations([loc_albany, loc_troy])

    # Direct primary name match
    assert len(col.find_by_name("Albany")) == 1

    # Scoped parent match (exercises entity.parent_id == target_parent at line 593)
    assert len(col.find_by_name("Albany", parent_id="LOC-000010")) == 1
    # Scoped parent non-match (exercises entity.parent_id != target_parent continue branch)
    assert len(col.find_by_name("Albany", parent_id="LOC-000020")) == 0

    # Alternate name
    assert len(col.find_by_name("Beverwijck")) == 1

    # Historical display name
    assert len(col.find_by_name("Albany Settlement")) == 1

    # Historical raw name
    assert len(col.find_by_name("Fort Orange")) == 1

    # Historical alternate spelling
    assert len(col.find_by_name("Fort Aurania")) == 1

    # Non-matching name with alternates enabled
    assert len(col.find_by_name("NonExistentTown")) == 0

    # Not matched AND include_alternate is False
    assert len(col.find_by_name("Beverwijck", include_alternate=False)) == 0
    assert (
        len(col.find_by_name("CompletelyUnmatchedName", include_alternate=False)) == 0
    )


@pytest.mark.unit
def test_search_scoring_and_graveyard_search() -> None:
    """Verify relevance search across wildcards, exact matches, substrings, and graveyard."""
    hist = HistoricalName(
        raw_name="Rumford",
        canonical_name="Rumford Town",
        alternate_spellings=["Pennycook"],
    )
    hist_no_canonical = HistoricalName(
        raw_name="Ancient Native Site",
        canonical_name=None,
        alternate_spellings=["Old Site"],
    )
    loc_active = _make_loc(
        "LOC-000001",
        "Concord",
        JurisdictionCategory.MUNICIPALITY,
        canonical_urn="urn:gda:loc:us:nh:concord",
        historical_names=[hist, hist_no_canonical],
    )
    loc_tomb = _make_loc(
        "LOC-000002",
        "Hopkinton",
        JurisdictionCategory.CIVIL_TOWNSHIP,
        canonical_urn="urn:gda:loc:us:nh:hopkinton",
        is_deprecated=True,
    )
    col = Locations([loc_active, loc_tomb])

    res_exact = col.search("Concord")
    assert res_exact[0].id == LocationID("LOC-000001")

    assert len(col.search("Concord", category=JurisdictionCategory.STATOID)) == 0

    res_sub = col.search("cord")
    assert len(res_sub) == 1

    res_wc = col.search("Conc*")
    assert len(res_wc) == 1
    assert res_wc[0].id == LocationID("LOC-000001")

    res_wc_multi = col.search("Rum*")
    assert len(res_wc_multi) == 1
    assert res_wc_multi[0].id == LocationID("LOC-000001")

    res_fuzzy = col.search("Conkord", fuzzy=True, threshold=0.75)
    assert len(res_fuzzy) == 1

    res_low_fuzzy = col.search("CompletelyDifferent", fuzzy=True, threshold=0.85)
    assert len(res_low_fuzzy) == 0

    res_no_fuzzy = col.search("Conkord", fuzzy=False)
    assert len(res_no_fuzzy) == 0

    res_alt = col.search("Pennycook")
    assert len(res_alt) == 1

    res_canon = col.search("Rumford Town")
    assert len(res_canon) == 1

    res_raw_only = col.search("Ancient Native Site")
    assert len(res_raw_only) == 1

    assert len(col.search("Hopkinton", include_graveyard=False)) == 0
    assert len(col.search("Hopkinton", include_graveyard=True)) == 1
    assert col.search("") == ()


@pytest.mark.regression
def test_internal_helpers_edge_cases() -> None:
    """Verify defensive handling in _coerce_id and _extract_year."""
    col = Locations()

    assert col._coerce_id("LOC-") is None
    assert col._coerce_id("LOC-INVALID-TOO-LONG-ETC-FAIL") is None
    assert col._coerce_id(12345) is None

    # Line 748-749 DateString exercise
    assert col._extract_year(DateString("1850")) == 1850

    # Line 752-753 non-temporal fall-through exercise
    assert col._extract_year(None) is None
    assert col._extract_year(1942) is None
    assert col._extract_year(12.34) is None
    assert col._extract_year([1942]) is None
    assert col._extract_year("No digits here") is None
    assert col._extract_year("") is None


@pytest.mark.unit
def test_to_list_and_from_list_parity() -> None:
    """Verify to_list export and from_list factory parity."""
    loc1 = _make_loc("LOC-000001", "City A")
    loc2 = _make_loc("LOC-000002", "City B", is_deprecated=True)
    col = Locations([loc1, loc2])

    active_list = col.to_list(include_graveyard=False)
    all_list = col.to_list(include_graveyard=True)

    assert len(active_list) == 1
    assert len(all_list) == 2

    rebuilt = Locations.from_list(all_list)
    assert rebuilt.total_count == 2
    assert rebuilt.count_active == 1


# ==========================================================================
# GROUP 6: Subsystem Gateway & Smoke Verification
# Note: End-to-end integration and smoke execution across collection lifecycle
# ==========================================================================


@pytest.mark.smoke
def test_end_to_end_locations_lifecycle() -> None:
    """Verify high-level lifecycle: creation, indexing, deprecation, and traversal."""
    col = Locations()

    us = _make_loc("LOC-000001", "United States", JurisdictionCategory.COUNTRY)
    nh = _make_loc(
        "LOC-000002",
        "New Hampshire",
        JurisdictionCategory.STATOID,
        parent_id="LOC-000001",
    )
    bow_old = _make_loc(
        "LOC-000003",
        "Bow Settlement",
        JurisdictionCategory.CIVIL_TOWNSHIP,
        parent_id="LOC-000002",
    )
    bow_new = _make_loc(
        "LOC-000004",
        "Town of Bow",
        JurisdictionCategory.CIVIL_TOWNSHIP,
        parent_id="LOC-000002",
    )

    col.add(us)
    col.add(nh)
    col.add(bow_old)
    col.add(bow_new)

    assert len(col) == 4
    col.deprecate("LOC-000003", superseded_by="LOC-000004")
    assert len(col) == 3
    assert col["LOC-000003"].id == LocationID("LOC-000004")

    path = col.format_hierarchy("LOC-000004")
    assert path == "Town of Bow, New Hampshire, United States"
