"""Path: src/gda/engine/media_resolver.py

Active in-memory media graph indexer and bidirectional resolver.

Operational Role:
    Provides in-memory graph resolution infrastructure for digital media assets.
    'MediaXRefResolver' manages bidirectional mappings between domain entities
    and MediaIDs, enabling O(1) lookups, dynamic indexing, and safe evictions.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from uuid import UUID

from gda.core.dates import utc_now_iso
from gda.core.introspectable import IntrospectableMixin
from gda.core.logging import GDALogger
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import MediaID
from gda.model.xref.media_xref import MediaTargetID, MediaXRef

__version__ = "1.0.0+build.3"

__all__ = ["MediaXRefResolver"]

_logger = GDALogger(__name__)


def _normalize_media_id(media_id: MediaID | UUID | str) -> MediaID:
    """Coerce MediaID, UUID, or string into a canonical MediaID."""
    if isinstance(media_id, MediaID):
        return media_id
    return MediaID(str(media_id).strip().lower())


class MediaXRefResolver(IntrospectableMixin):
    """In-memory bidirectional media indexer and traversal resolver."""

    def __init__(self) -> None:
        """Initialize empty graph index tables and compilation timestamp."""
        self._last_compiled: IsoTimestamp = IsoTimestamp(utc_now_iso())
        self._edges: dict[str, MediaXRef] = {}

        self._entity_to_media: dict[MediaTargetID, set[MediaID]] = defaultdict(set)
        self._media_to_entities: dict[MediaID, set[MediaTargetID]] = defaultdict(set)

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
        self._last_compiled = IsoTimestamp(utc_now_iso())

    @classmethod
    def from_xrefs(cls, xrefs: Iterable[MediaXRef]) -> MediaXRefResolver:
        """Hydrate graph index directly from an iterable of pre-formed MediaXRef edges."""
        resolver = cls()
        for edge in xrefs:
            resolver.add_xref(edge)
        return resolver

    def add_xref(self, edge: MediaXRef) -> None:
        """Add a single pre-formed MediaXRef edge into index tables."""
        key = edge.xref_key
        if key in self._edges:
            return

        self._edges[key] = edge
        self._entity_to_media[edge.target_id].add(edge.media_id)
        self._media_to_entities[edge.media_id].add(edge.target_id)

        self._mark_updated()

    def evict_entity(self, entity_id: MediaTargetID) -> None:
        """Safely remove all media cross-reference edges and index mappings for an entity."""
        keys_to_delete = [k for k, edge in self._edges.items() if edge.target_id == entity_id]

        if not keys_to_delete:
            return

        for k in keys_to_delete:
            del self._edges[k]

        associated_media = self._entity_to_media.pop(entity_id, set())
        for mid in associated_media:
            self._media_to_entities[mid].discard(entity_id)

        self._mark_updated()

    def evict_media(self, media_id: MediaID | UUID | str) -> None:
        """Safely remove all cross-reference edges and index mappings for a media asset."""
        norm_mid = _normalize_media_id(media_id)
        keys_to_delete = [k for k, edge in self._edges.items() if edge.media_id == norm_mid]

        if not keys_to_delete:
            return

        for k in keys_to_delete:
            del self._edges[k]

        associated_entities = self._media_to_entities.pop(norm_mid, set())
        for eid in associated_entities:
            self._entity_to_media[eid].discard(norm_mid)

        self._mark_updated()

    def get_media_for_entity(self, entity_id: MediaTargetID) -> tuple[MediaID, ...]:
        """Return tuple of all MediaIDs attached to a domain entity."""
        return tuple(sorted(self._entity_to_media.get(entity_id, set())))

    def get_entities_for_media(self, media_id: MediaID | UUID | str) -> tuple[MediaTargetID, ...]:
        """Return tuple of all entity identifiers linked to a media asset."""
        norm_mid = _normalize_media_id(media_id)
        return tuple(sorted(self._media_to_entities.get(norm_mid, set())))

    def export_xrefs(self) -> list[MediaXRef]:
        """Export all current indexed edges as a list of MediaXRef objects."""
        return list(self._edges.values())
