"""Path: tests/test_gda/test_entity/test_locations/test_hierarchy_graph.py

Relational graph and multi-hop hierarchy validation test suite for locations.

Operational Role:
    Verifies full-collection integrity checks including multi-hop cycle detection,
    root anchoring, pattern compliance, graveyard boundaries, and index sync.
"""

from __future__ import annotations

import pytest

from gda.entity.locations.collection import Locations
from gda.entity.locations.validation import (
    valid_collection_all,
    valid_collection_cycles,
    valid_collection_indexes,
    valid_collection_patterns,
    valid_collection_roots,
    valid_collection_tombstones,
)
from gda.enums.location import JurisdictionCategory
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import LocationID
from gda.model.base.audit import AuditStamp
from gda.model.base.name import NameThing
from gda.model.base.tombstone import Tombstone
from gda.model.entity.location import Location

__version__ = "1.0.0+build.11"

# ==============================================================================
# GROUP 1: MULTI-HOP CYCLE DETECTION
# ==============================================================================


@pytest.mark.unit
def test_valid_collection_cycles_passes_on_valid_tree(
    valid_hierarchy_collection: Locations,
) -> None:
    """Verify valid acyclic collection passes cycle check."""
    assert valid_collection_cycles(valid_hierarchy_collection) is True


@pytest.mark.unit
def test_valid_collection_cycles_skips_already_visited_nodes() -> None:
    """Verify cycle traversal skips nodes already marked as visited."""
    col = Locations()
    now = IsoTimestamp.now_utc()

    loc_b = Location(
        id=LocationID("LOC-000002"),
        audit=AuditStamp(created_at=now, updated_at=now),
        name=NameThing.create(raw="Child", canonical="Child"),
        category=JurisdictionCategory.STATOID,
        canonical_urn="urn:gda:loc:usa:child",
        parent_id=LocationID("LOC-000001"),
        tombstone=Tombstone[LocationID](),
    )
    loc_a = Location(
        id=LocationID("LOC-000001"),
        audit=AuditStamp(created_at=now, updated_at=now),
        name=NameThing.create(raw="Parent", canonical="Parent"),
        category=JurisdictionCategory.COUNTRY,
        canonical_urn="urn:gda:loc:usa",
        parent_id=None,
        tombstone=Tombstone[LocationID](),
    )

    col._registry[loc_b.id] = loc_b
    col._registry[loc_a.id] = loc_a

    assert valid_collection_cycles(col) is True


@pytest.mark.regression
def test_valid_collection_cycles_fails_on_cycle(cyclic_collection: Locations) -> None:
    """Verify indirect cycle returns False and logs diagnostic."""
    assert valid_collection_cycles(cyclic_collection) is False


# ==============================================================================
# GROUP 2: ROOT ANCHORING & ORPHAN SUBTREES
# ==============================================================================


@pytest.mark.unit
def test_valid_collection_roots_passes_on_valid_tree(
    valid_hierarchy_collection: Locations,
) -> None:
    """Verify branches terminating at COUNTRY evaluate to True."""
    assert valid_collection_roots(valid_hierarchy_collection) is True


@pytest.mark.regression
def test_valid_collection_roots_fails_on_floating_island(
    floating_island_collection: Locations,
) -> None:
    """Verify floating subtrees lacking COUNTRY root evaluate to False."""
    assert valid_collection_roots(floating_island_collection) is False


@pytest.mark.regression
def test_valid_collection_roots_fails_on_missing_parent_reference() -> None:
    """Verify active entity pointing to non-existent parent returns False."""
    col = Locations()
    now = IsoTimestamp.now_utc()
    s = Location(
        id=LocationID("LOC-000002"),
        audit=AuditStamp(created_at=now, updated_at=now),
        name=NameThing.create(raw="NH", canonical="NH"),
        category=JurisdictionCategory.STATOID,
        canonical_urn="urn:gda:loc:nh",
        parent_id=LocationID("LOC-999999"),
        tombstone=Tombstone[LocationID](),
    )
    col.add(s)
    assert valid_collection_roots(col) is False


@pytest.mark.regression
def test_valid_collection_roots_cycle_boundary_guard(
    cyclic_collection: Locations,
) -> None:
    """Verify root evaluation breaks safely when evaluating circular parentage."""
    assert valid_collection_roots(cyclic_collection) is False


# ==============================================================================
# GROUP 3: PATTERN 1-7 JURISDICTIONAL COMPLIANCE
# ==============================================================================


@pytest.mark.unit
def test_valid_collection_patterns_passes_standard_and_independent_cities(
    valid_hierarchy_collection: Locations,
    independent_city_collection: Locations,
) -> None:
    """Verify Pattern 5 and Pattern 7 hierarchies pass pattern checks."""
    assert valid_collection_patterns(valid_hierarchy_collection) is True
    assert valid_collection_patterns(independent_city_collection) is True


@pytest.mark.unit
def test_valid_collection_patterns_multi_child_loop_continuation(
    consecutive_multi_child_collection: Locations,
) -> None:
    """Verify pattern loop continues across multiple consecutive valid children (covers Line 459->446)."""
    assert valid_collection_patterns(consecutive_multi_child_collection) is True


@pytest.mark.regression
def test_valid_collection_patterns_fails_on_illegal_tier_skip() -> None:
    """Verify civil township directly under statoid returns False."""
    col = Locations()
    now = IsoTimestamp.now_utc()

    c = Location(
        id=LocationID("LOC-000001"),
        audit=AuditStamp(created_at=now, updated_at=now),
        name=NameThing.create(raw="USA", canonical="USA"),
        category=JurisdictionCategory.COUNTRY,
        canonical_urn="urn:gda:loc:usa",
        tombstone=Tombstone[LocationID](),
    )
    s = Location(
        id=LocationID("LOC-000002"),
        audit=AuditStamp(created_at=now, updated_at=now),
        name=NameThing.create(raw="NH", canonical="NH"),
        category=JurisdictionCategory.STATOID,
        canonical_urn="urn:gda:loc:usa:nh",
        parent_id=c.id,
        tombstone=Tombstone[LocationID](),
    )
    twp = Location(
        id=LocationID("LOC-000003"),
        audit=AuditStamp(created_at=now, updated_at=now),
        name=NameThing.create(raw="Bow", canonical="Bow"),
        category=JurisdictionCategory.CIVIL_TOWNSHIP,
        canonical_urn="urn:gda:loc:usa:nh:bow",
        parent_id=s.id,
        tombstone=Tombstone[LocationID](),
    )
    col.add(c)
    col.add(s)
    col.add(twp)
    assert valid_collection_patterns(col) is False


@pytest.mark.regression
def test_valid_collection_patterns_fails_on_country_with_parent() -> None:
    """Verify COUNTRY node with parent pointer fails pattern check."""
    col = Locations()
    now = IsoTimestamp.now_utc()
    c = Location(
        id=LocationID("LOC-000001"),
        audit=AuditStamp(created_at=now, updated_at=now),
        name=NameThing.create(raw="USA", canonical="USA"),
        category=JurisdictionCategory.COUNTRY,
        canonical_urn="urn:gda:loc:usa",
        parent_id=LocationID("LOC-999999"),
        tombstone=Tombstone[LocationID](),
    )
    col.add(c)
    assert valid_collection_patterns(col) is False


@pytest.mark.regression
def test_valid_collection_patterns_fails_on_missing_parent_pointer() -> None:
    """Verify non-country node without parent fails pattern check."""
    col = Locations()
    now = IsoTimestamp.now_utc()
    s = Location(
        id=LocationID("LOC-000002"),
        audit=AuditStamp(created_at=now, updated_at=now),
        name=NameThing.create(raw="NH", canonical="NH"),
        category=JurisdictionCategory.STATOID,
        canonical_urn="urn:gda:loc:nh",
        parent_id=None,
        tombstone=Tombstone[LocationID](),
    )
    col.add(s)
    assert valid_collection_patterns(col) is False


@pytest.mark.regression
def test_valid_collection_patterns_fails_on_invalid_intermediate_parents() -> None:
    """Verify statoid under non-country and county under non-statoid fail pattern check."""
    col = Locations()
    now = IsoTimestamp.now_utc()

    c = Location(
        id=LocationID("LOC-000001"),
        audit=AuditStamp(created_at=now, updated_at=now),
        name=NameThing.create(raw="USA", canonical="USA"),
        category=JurisdictionCategory.COUNTRY,
        canonical_urn="urn:gda:loc:usa",
        tombstone=Tombstone[LocationID](),
    )
    s1 = Location(
        id=LocationID("LOC-000002"),
        audit=AuditStamp(created_at=now, updated_at=now),
        name=NameThing.create(raw="S1", canonical="S1"),
        category=JurisdictionCategory.STATOID,
        canonical_urn="urn:gda:loc:usa:s1",
        parent_id=c.id,
        tombstone=Tombstone[LocationID](),
    )
    s2 = Location(
        id=LocationID("LOC-000003"),
        audit=AuditStamp(created_at=now, updated_at=now),
        name=NameThing.create(raw="S2", canonical="S2"),
        category=JurisdictionCategory.STATOID,
        canonical_urn="urn:gda:loc:usa:s1:s2",
        parent_id=s1.id,
        tombstone=Tombstone[LocationID](),
    )
    co = Location(
        id=LocationID("LOC-000004"),
        audit=AuditStamp(created_at=now, updated_at=now),
        name=NameThing.create(raw="CO", canonical="CO"),
        category=JurisdictionCategory.COUNTY_EQUIVALENT,
        canonical_urn="urn:gda:loc:usa:co",
        parent_id=c.id,
        tombstone=Tombstone[LocationID](),
    )
    local = Location(
        id=LocationID("LOC-000005"),
        audit=AuditStamp(created_at=now, updated_at=now),
        name=NameThing.create(raw="L", canonical="L"),
        category=JurisdictionCategory.MUNICIPALITY,
        canonical_urn="urn:gda:loc:usa:l",
        parent_id=c.id,
        tombstone=Tombstone[LocationID](),
    )
    for node in [c, s1, s2, co, local]:
        col.add(node)
    assert valid_collection_patterns(col) is False


# ==============================================================================
# GROUP 4: TOMBSTONE BOUNDARIES & GRAVEYARD ISOLATION
# ==============================================================================


@pytest.mark.unit
def test_valid_collection_tombstones_passes_on_valid_tree(
    valid_hierarchy_collection: Locations,
) -> None:
    """Verify clean collection passes tombstone check."""
    assert valid_collection_tombstones(valid_hierarchy_collection) is True


@pytest.mark.unit
def test_valid_collection_tombstones_passes_on_deprecated_without_superseded() -> None:
    """Verify tombstone with no replacement passes tombstone check."""
    col = Locations()
    now = IsoTimestamp.now_utc()
    c = Location(
        id=LocationID("LOC-000001"),
        audit=AuditStamp(created_at=now, updated_at=now),
        name=NameThing.create(raw="USA", canonical="USA"),
        category=JurisdictionCategory.COUNTRY,
        canonical_urn="urn:gda:loc:usa",
        tombstone=Tombstone[LocationID]().retire(timestamp=now),
    )
    col._registry[c.id] = c
    assert valid_collection_tombstones(col) is True


@pytest.mark.regression
def test_valid_collection_tombstones_fails_on_deprecated_ancestor(
    tombstone_violation_collection: Locations,
) -> None:
    """Verify active child referencing deprecated ancestor returns False."""
    assert valid_collection_tombstones(tombstone_violation_collection) is False


@pytest.mark.regression
def test_valid_collection_tombstones_cycle_and_missing_parent_guard(
    cyclic_collection: Locations,
) -> None:
    """Verify tombstone check safely breaks on cyclic references and missing parents."""
    assert valid_collection_tombstones(cyclic_collection) is True

    col = Locations()
    now = IsoTimestamp.now_utc()
    loc = Location(
        id=LocationID("LOC-000001"),
        audit=AuditStamp(created_at=now, updated_at=now),
        name=NameThing.create(raw="Node", canonical="Node"),
        category=JurisdictionCategory.STATOID,
        canonical_urn="urn:gda:loc:node",
        parent_id=LocationID("LOC-999999"),
        tombstone=Tombstone[LocationID](),
    )
    col.add(loc)
    assert valid_collection_tombstones(col) is True


@pytest.mark.regression
def test_valid_collection_tombstones_fails_on_invalid_superseded_links() -> None:
    """Verify tombstone with missing or category-mismatched replacement returns False."""
    col = Locations()
    now = IsoTimestamp.now_utc()

    c = Location(
        id=LocationID("LOC-000001"),
        audit=AuditStamp(created_at=now, updated_at=now),
        name=NameThing.create(raw="USA", canonical="USA"),
        category=JurisdictionCategory.COUNTRY,
        canonical_urn="urn:gda:loc:usa",
        tombstone=Tombstone[LocationID](),
    )
    s = Location(
        id=LocationID("LOC-000002"),
        audit=AuditStamp(created_at=now, updated_at=now),
        name=NameThing.create(raw="NH", canonical="NH"),
        category=JurisdictionCategory.STATOID,
        canonical_urn="urn:gda:loc:usa:nh",
        parent_id=c.id,
        tombstone=Tombstone[LocationID](),
    )
    t1 = Location(
        id=LocationID("LOC-000003"),
        audit=AuditStamp(created_at=now, updated_at=now),
        name=NameThing.create(raw="Old State", canonical="Old State"),
        category=JurisdictionCategory.STATOID,
        canonical_urn="urn:gda:loc:usa:old_state",
        parent_id=c.id,
        tombstone=Tombstone[LocationID]().retire(
            timestamp=now, superseded_by=LocationID("LOC-999999")
        ),
    )
    col.add(c)
    col.add(s)
    col._registry[t1.id] = t1
    assert valid_collection_tombstones(col) is False

    t2 = Location(
        id=LocationID("LOC-000004"),
        audit=AuditStamp(created_at=now, updated_at=now),
        name=NameThing.create(raw="Old State 2", canonical="Old State 2"),
        category=JurisdictionCategory.STATOID,
        canonical_urn="urn:gda:loc:usa:old_state_2",
        parent_id=c.id,
        tombstone=Tombstone[LocationID]().retire(timestamp=now, superseded_by=c.id),
    )
    col._registry[t2.id] = t2
    assert valid_collection_tombstones(col) is False


# ==============================================================================
# GROUP 5: INDEX SYNCHRONIZATION & MASTER ORCHESTRATION
# ==============================================================================


@pytest.mark.unit
def test_valid_collection_indexes_passes_on_valid_tree(
    valid_hierarchy_collection: Locations,
) -> None:
    """Verify synchronized indices evaluate to True."""
    assert valid_collection_indexes(valid_hierarchy_collection) is True


@pytest.mark.unit
def test_valid_collection_indexes_passes_with_populated_aliases() -> None:
    """Verify locations with valid aliases pass index validation."""
    col = Locations()
    now = IsoTimestamp.now_utc()
    name = (
        NameThing.create(raw="USA", canonical="USA").add_alias("United States").add_alias("America")
    )
    c = Location(
        id=LocationID("LOC-000001"),
        audit=AuditStamp(created_at=now, updated_at=now),
        name=name,
        category=JurisdictionCategory.COUNTRY,
        canonical_urn="urn:gda:loc:usa",
        tombstone=Tombstone[LocationID](),
    )
    col.add(c)
    assert valid_collection_indexes(col) is True


@pytest.mark.regression
def test_valid_collection_indexes_fails_on_desynchronization(
    desynchronized_index_collection: Locations,
) -> None:
    """Verify desynchronized index mapping returns False."""
    assert valid_collection_indexes(desynchronized_index_collection) is False


@pytest.mark.regression
def test_valid_collection_indexes_fails_on_missing_urn_or_dangling_reference() -> None:
    """Verify missing URN index or dangling index pointer returns False."""
    col = Locations()
    now = IsoTimestamp.now_utc()
    c = Location(
        id=LocationID("LOC-000001"),
        audit=AuditStamp(created_at=now, updated_at=now),
        name=NameThing.create(raw="USA", canonical="USA"),
        category=JurisdictionCategory.COUNTRY,
        canonical_urn="urn:gda:loc:usa",
        tombstone=Tombstone[LocationID](),
    )
    col._registry[c.id] = c
    assert valid_collection_indexes(col) is False

    col._urn_index["urn:gda:loc:usa"] = c.id
    col._urn_index["urn:gda:loc:dangling"] = LocationID("LOC-999999")
    assert valid_collection_indexes(col) is False


@pytest.mark.regression
def test_valid_collection_indexes_fails_on_missing_alias() -> None:
    """Verify location with alias missing from alias index returns False."""
    col = Locations()
    now = IsoTimestamp.now_utc()
    name = NameThing.create(raw="USA", canonical="USA").add_alias("United States")
    c = Location(
        id=LocationID("LOC-000001"),
        audit=AuditStamp(created_at=now, updated_at=now),
        name=name,
        category=JurisdictionCategory.COUNTRY,
        canonical_urn="urn:gda:loc:usa",
        tombstone=Tombstone[LocationID](),
    )
    col.add(c)
    col._alias_index.clear()
    assert valid_collection_indexes(col) is False


@pytest.mark.smoke
def test_valid_collection_all_evaluates_master_pass_and_fail(
    valid_hierarchy_collection: Locations,
    cyclic_collection: Locations,
) -> None:
    """Verify master validator evaluates complete collection health."""
    assert valid_collection_all(valid_hierarchy_collection) is True
    assert valid_collection_all(cyclic_collection) is False
