"""Path: src/gda/repository/other/collection.py

In-memory collection for Other Miscellaneous archival source records.

Operational Role:
    Provides indexed in-memory collection management for
    OtherMiscellaneousRecord with editing, graveyard lifecycle, and SQLite/JSON
    synchronization.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from gda.db.session import DatabaseSessionManager
from gda.model.atom.id import LocationID, SourceID
from gda.model.source.other.miscellaneous import OtherMiscellaneousRecord
from gda.repository.base import _normalize_id
from gda.repository.collection import BaseSourceCollection
from gda.repository.other.repository import OtherMiscellaneousRepository

__version__ = "1.0.0+build.1"

__all__ = [
    "OtherMiscellaneousCollection",
]


def _sorted_records[T](registry: dict[SourceID, T], sids: set[SourceID]) -> list[T]:
    return [registry[sid] for sid in sorted(sids, key=lambda s: s.value)]


class OtherMiscellaneousCollection(
    BaseSourceCollection[
        OtherMiscellaneousRecord,
        OtherMiscellaneousRepository,
    ]
):
    """In-memory collection for OtherMiscellaneousRecord sources."""

    def __init__(
        self,
        repository: OtherMiscellaneousRepository | None = None,
    ) -> None:
        """Initialize OtherMiscellaneousCollection with location buckets."""
        self._by_location: dict[str, set[SourceID]] = defaultdict(set)
        super().__init__(repository=repository)

    def _create_default_repository(
        self,
        session_manager: DatabaseSessionManager | None = None,
    ) -> OtherMiscellaneousRepository:
        return OtherMiscellaneousRepository(session_manager=session_manager)

    def _deserialize_record(
        self,
        data: dict[str, Any],
    ) -> OtherMiscellaneousRecord:
        return OtherMiscellaneousRecord.from_dict(data)

    def _index_domain_fields(self, record: OtherMiscellaneousRecord) -> None:
        if record.organization_location_id is not None:
            self._by_location[record.organization_location_id.value].add(record.source_id)

    def _unindex_domain_fields(self, record: OtherMiscellaneousRecord) -> None:
        if record.organization_location_id is not None:
            self._by_location[record.organization_location_id.value].discard(record.source_id)

    def find_by_organization_location(
        self,
        location_id: LocationID | str,
    ) -> list[OtherMiscellaneousRecord]:
        """Return active miscellaneous records for a LocationID."""
        return _sorted_records(
            self._registry,
            self._by_location.get(_normalize_id(location_id), set()),
        )
