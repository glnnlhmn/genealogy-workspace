"""Path: src/gda/repository/cemetery/collection.py

In-memory collections for Cemetery archival source records.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from gda.db.session import DatabaseSessionManager
from gda.model.atom.id import LocationID, SiteID, SourceID
from gda.model.source.cemetery.marker import CemeteryMarkerRecord
from gda.model.source.cemetery.registry import CemeteryRegistryRecord
from gda.repository.cemetery.repository import (
    CemeteryMarkerRepository,
    CemeteryRegistryRepository,
)
from gda.repository.collection import BaseSourceCollection
from gda.util.ids import normalize_id

__version__ = "1.0.0+build.4"

__all__ = [
    "CemeteryMarkerCollection",
    "CemeteryRegistryCollection",
]


class CemeteryMarkerCollection(
    BaseSourceCollection[CemeteryMarkerRecord, CemeteryMarkerRepository]
):
    """In-memory collection for grave marker and headstone survey records."""

    def __init__(self, repository: CemeteryMarkerRepository | None = None) -> None:
        """Initialize CemeteryMarkerCollection with secondary index buckets."""
        self._by_site: dict[str, set[SourceID]] = defaultdict(set)
        self._by_location: dict[str, set[SourceID]] = defaultdict(set)
        super().__init__(repository=repository)

    def _create_default_repository(
        self,
        session_manager: DatabaseSessionManager | None = None,
    ) -> CemeteryMarkerRepository:
        return CemeteryMarkerRepository(session_manager=session_manager)

    def _deserialize_record(self, data: dict[str, Any]) -> CemeteryMarkerRecord:
        return CemeteryMarkerRecord.from_dict(data)

    def _index_domain_fields(self, record: CemeteryMarkerRecord) -> None:
        if record.cemetery_site_id is not None:
            self._by_site[record.cemetery_site_id.value].add(record.source_id)
        if record.location_id is not None:
            self._by_location[record.location_id.value].add(record.source_id)

    def _unindex_domain_fields(self, record: CemeteryMarkerRecord) -> None:
        if record.cemetery_site_id is not None:
            self._by_site[record.cemetery_site_id.value].discard(record.source_id)
        if record.location_id is not None:
            self._by_location[record.location_id.value].discard(record.source_id)

    def find_by_cemetery_site(
        self,
        cemetery_site_id: SiteID | str,
    ) -> list[CemeteryMarkerRecord]:
        """Return active marker records for a cemetery SiteID."""
        return self._records_for_ids(self._by_site.get(normalize_id(cemetery_site_id), set()))

    def find_by_location(
        self,
        location_id: LocationID | str,
    ) -> list[CemeteryMarkerRecord]:
        """Return active marker records for a geographic LocationID."""
        return self._records_for_ids(self._by_location.get(normalize_id(location_id), set()))


class CemeteryRegistryCollection(
    BaseSourceCollection[CemeteryRegistryRecord, CemeteryRegistryRepository]
):
    """In-memory collection for sexton books and cemetery plot registries."""

    def __init__(self, repository: CemeteryRegistryRepository | None = None) -> None:
        """Initialize CemeteryRegistryCollection with secondary index buckets."""
        self._by_site: dict[str, set[SourceID]] = defaultdict(set)
        self._by_location: dict[str, set[SourceID]] = defaultdict(set)
        super().__init__(repository=repository)

    def _create_default_repository(
        self,
        session_manager: DatabaseSessionManager | None = None,
    ) -> CemeteryRegistryRepository:
        return CemeteryRegistryRepository(session_manager=session_manager)

    def _deserialize_record(self, data: dict[str, Any]) -> CemeteryRegistryRecord:
        return CemeteryRegistryRecord.from_dict(data)

    def _index_domain_fields(self, record: CemeteryRegistryRecord) -> None:
        self._by_site[record.cemetery_site_id.value].add(record.source_id)
        if record.location_id is not None:
            self._by_location[record.location_id.value].add(record.source_id)

    def _unindex_domain_fields(self, record: CemeteryRegistryRecord) -> None:
        self._by_site[record.cemetery_site_id.value].discard(record.source_id)
        if record.location_id is not None:
            self._by_location[record.location_id.value].discard(record.source_id)

    def find_by_cemetery_site(
        self,
        cemetery_site_id: SiteID | str,
    ) -> list[CemeteryRegistryRecord]:
        """Return active plot registry records for a cemetery SiteID."""
        return self._records_for_ids(self._by_site.get(normalize_id(cemetery_site_id), set()))

    def find_by_location(
        self,
        location_id: LocationID | str,
    ) -> list[CemeteryRegistryRecord]:
        """Return active plot registry records for a geographic LocationID."""
        return self._records_for_ids(self._by_location.get(normalize_id(location_id), set()))
