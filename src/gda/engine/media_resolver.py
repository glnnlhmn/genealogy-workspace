"""Path: src/gda/engine/media_resolver.py

Active in-memory media graph indexer and bidirectional resolver.

Operational Role:
    Provides in-memory graph resolution infrastructure for digital media assets.
    'MediaXRefResolver' manages bidirectional mappings between domain entities
    and media UUIDs, enabling O(1) lookups, dynamic indexing, and safe evictions.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from uuid import UUID

from gda.core.introspectable import IntrospectableMixin
from gda.core.logging import GDALogger
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import AtomID
from gda.model.xref.media_xref import MediaXRef

__version__ = "1.0.0+build.2"

__all__ = ["MediaXRefResolver"]

_logger = GDALogger(__name__)


class MediaXRefResolver(IntrospectableMixin):
    """In-memory bidirectional media indexer and traversal resolver."""

    def __init__(self) -> None:
        """Initialize empty graph index tables and compilation timestamp."""
        self._last_compiled: IsoTimestamp = IsoTimestamp.now_utc()
        self._edges: dict[UUID, MediaXRef] = {}

        self._entity_to_media: dict[AtomID, set[UUID]] = defaultdict(set)
        self._media_to_entities: dict[UUID, set[AtomID]] = defaultdict(set)

    @property
    def last_compiled(self) -> IsoTimestamp:
        """Return the compilation timestamp of the index state."""
        return self._last_compiled

    @property
    def edge_count(self) -> int:
        """Return the total count of indexed media cross-reference edges."""
        return len(self._edges)

    def _mark_updated(self) -> None:
        """Advance the index compilation timestamp."""
        self._last_compiled = IsoTimestamp.now_utc()

    @classmethod
    def from_xrefs(cls, xrefs: Iterable[MediaXRef]) -> MediaXRefResolver:
        """Hydrate graph index directly from an iterable of pre-formed MediaXRef edges."""
        resolver = cls()
        for edge in xrefs:
            resolver.add_xref(edge)
        return resolver

    def add_xref(self, edge: MediaXRef) -> None:
        """Add a single pre-formed MediaXRef edge into index tables."""
        if edge.xref_id in self._edges:
            return

        self._edges[edge.xref_id] = edge
        self._entity_to_media[edge.entity_id].add(edge.media_id)
        self._media_to_entities[edge.media_id].add(edge.entity_id)

        self._mark_updated()

    def evict_entity(self, entity_id: AtomID) -> None:
        """Safely remove all media cross-reference edges and index mappings for an entity."""
        keys_to_delete = [
            k for k, edge in self._edges.items() if edge.entity_id == entity_id
        ]

        if not keys_to_delete:
            return

        for k in keys_to_delete:
            del self._edges[k]

        associated_media = self._entity_to_media.pop(entity_id, set())
        for mid in associated_media:
            self._media_to_entities[mid].discard(entity_id)

        self._mark_updated()

    def evict_media(self, media_id: UUID) -> None:
        """Safely remove all cross-reference edges and index mappings for a media asset."""
        keys_to_delete = [
            k for k, edge in self._edges.items() if edge.media_id == media_id
        ]

        if not keys_to_delete:
            return

        for k in keys_to_delete:
            del self._edges[k]

        associated_entities = self._media_to_entities.pop(media_id, set())
        for eid in associated_entities:
            self._entity_to_media[eid].discard(media_id)

        self._mark_updated()

    def get_media_for_entity(self, entity_id: AtomID) -> tuple[UUID, ...]:
        """Return tuple of all MediaIDs attached to a domain entity."""
        return tuple(sorted(self._entity_to_media.get(entity_id, set())))

    def get_entities_for_media(self, media_id: UUID) -> tuple[AtomID, ...]:
        """Return tuple of all entity identifiers linked to a media asset."""
        return tuple(sorted(self._media_to_entities.get(media_id, set())))

    def export_xrefs(self) -> list[MediaXRef]:
        """Export all current indexed edges as a list of MediaXRef objects."""
        return list(self._edges.values())
