"""Path: tests/test_gda/test_engine/test_media_resolver.py

Atomized unit, regression, and smoke test suite for MediaXRefResolver.

Operational Role:
    Verifies media indexation, bidirectional entity-media queries, bulk hydration,
    IntrospectableMixin documentation, edge deduplication, and safe eviction.
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from gda.engine.media_resolver import MediaXRefResolver
from gda.model.atom.id import IndividualID, MediaID, SiteID
from gda.model.xref.media_xref import MediaXRef

__version__ = "1.0.0+build.4"


def _make_media_id() -> MediaID:
    """Create a fresh RFC 4122 UUIDv4 MediaID."""
    return MediaID(str(uuid4()))


# ==============================================================================
# GROUP 1: Initialization & Hydration Factories
# ==============================================================================


@pytest.mark.unit
def test_resolver_init_empty() -> None:
    """Verify clean initialization, zero edge count, and valid last_compiled."""
    resolver = MediaXRefResolver()
    assert resolver.edge_count == 0
    assert resolver.last_compiled.value is not None
    assert resolver.export_xrefs() == []


@pytest.mark.unit
def test_resolver_introspectable_help() -> None:
    """Verify .help() returns Markdown documentation via IntrospectableMixin."""
    help_doc = MediaXRefResolver.help(as_str=True)
    assert help_doc is not None
    assert "MediaXRefResolver" in help_doc


@pytest.mark.smoke
def test_resolver_from_xrefs_smoke() -> None:
    """Verify bulk instantiation from an iterable of MediaXRef edges."""
    ind = IndividualID("IND-000001")
    media_id = _make_media_id()
    edge = MediaXRef.create(
        media_id=media_id,
        target_id=ind,
    )
    resolver = MediaXRefResolver.from_xrefs([edge])
    assert resolver.edge_count == 1
    assert resolver.get_media_for_entity(ind) == (media_id,)


@pytest.mark.unit
def test_resolver_export_xrefs_parity() -> None:
    """Verify exported edges match internal indexed state."""
    ind = IndividualID("IND-000001")
    media_id = _make_media_id()
    edge = MediaXRef.create(
        media_id=media_id,
        target_id=ind,
    )
    resolver = MediaXRefResolver()
    resolver.add_xref(edge)
    assert resolver.export_xrefs() == [edge]


# ==============================================================================
# GROUP 2: Edge Intake & Bidirectional Query Traversals
# ==============================================================================


@pytest.mark.unit
def test_get_media_for_entity_multiple() -> None:
    """Verify retrieving multiple media assets attached to one entity."""
    ind = IndividualID("IND-000001")
    med1 = _make_media_id()
    med2 = _make_media_id()

    resolver = MediaXRefResolver()
    resolver.add_xref(MediaXRef.create(media_id=med1, target_id=ind))
    resolver.add_xref(MediaXRef.create(media_id=med2, target_id=ind))

    expected = tuple(sorted([med1, med2]))
    assert resolver.get_media_for_entity(ind) == expected


@pytest.mark.unit
def test_get_entities_for_media_group_portrait() -> None:
    """Verify retrieving multiple entities linked to one media asset."""
    ind1 = IndividualID("IND-000001")
    ind2 = IndividualID("IND-000002")
    media_id = _make_media_id()

    resolver = MediaXRefResolver()
    resolver.add_xref(MediaXRef.create(media_id=media_id, target_id=ind1))
    resolver.add_xref(MediaXRef.create(media_id=media_id, target_id=ind2))

    assert resolver.get_entities_for_media(media_id) == (ind1, ind2)


@pytest.mark.unit
def test_traversal_fallbacks_unlinked() -> None:
    """Verify unindexed entities/media return empty tuples."""
    resolver = MediaXRefResolver()
    unlinked_entity = IndividualID("IND-000999")
    unlinked_media = _make_media_id()

    assert resolver.get_media_for_entity(unlinked_entity) == ()
    assert resolver.get_entities_for_media(unlinked_media) == ()


@pytest.mark.regression
def test_add_duplicate_xref_idempotent() -> None:
    """Verify re-adding an edge with the same xref_key is a safe no-op."""
    ind = IndividualID("IND-000001")
    media_id = _make_media_id()
    edge = MediaXRef.create(media_id=media_id, target_id=ind)

    resolver = MediaXRefResolver()
    resolver.add_xref(edge)
    resolver.add_xref(edge)

    assert resolver.edge_count == 1


# ==============================================================================
# GROUP 3: Entity & Media Eviction Invariants
# ==============================================================================


@pytest.mark.regression
def test_evict_entity_removes_all_media_links() -> None:
    """Verify evicting an entity purges forward and reverse mappings."""
    ind = IndividualID("IND-000001")
    media_id = _make_media_id()

    resolver = MediaXRefResolver()
    resolver.add_xref(MediaXRef.create(media_id=media_id, target_id=ind))
    assert resolver.edge_count == 1

    resolver.evict_entity(ind)
    assert resolver.edge_count == 0
    assert resolver.get_media_for_entity(ind) == ()
    assert resolver.get_entities_for_media(media_id) == ()


@pytest.mark.regression
def test_evict_media_removes_all_entity_bindings() -> None:
    """Verify evicting a media asset purges all entity references."""
    ind = IndividualID("IND-000001")
    site = SiteID("SID-000001")
    media_id = _make_media_id()

    resolver = MediaXRefResolver()
    resolver.add_xref(MediaXRef.create(media_id=media_id, target_id=ind))
    resolver.add_xref(MediaXRef.create(media_id=media_id, target_id=site))
    assert resolver.edge_count == 2

    resolver.evict_media(media_id)
    assert resolver.edge_count == 0
    assert resolver.get_entities_for_media(media_id) == ()
    assert resolver.get_media_for_entity(ind) == ()
    assert resolver.get_media_for_entity(site) == ()


@pytest.mark.regression
def test_evict_nonexistent_entity_or_media_noop() -> None:
    """Verify evicting unknown entity or media IDs is a safe no-op."""
    resolver = MediaXRefResolver()
    resolver.evict_entity(IndividualID("IND-000999"))
    resolver.evict_media(uuid4())
    assert resolver.edge_count == 0
