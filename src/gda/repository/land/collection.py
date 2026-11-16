"""Path: src/gda/repository/land/collection.py

In-memory collections for Land archival source records.

Operational Role:
    Provides indexed in-memory collection managers for LandDeedRecord and
    LandGrantRecord with editing, graveyard lifecycle, and SQLite/JSON
    persistence synchronization.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from gda.db.session import DatabaseSessionManager
from gda.model.atom.id import IndividualID, LocationID, SourceID
from gda.model.source.land.deed import LandDeedRecord
from gda.model.source.land.grant import LandGrantRecord
from gda.repository.base import _normalize_id
from gda.repository.collection import BaseSourceCollection
from gda.repository.land.repository import (
    LandDeedRepository,
    LandGrantRepository,
)

__version__ = "1.0.0+build.1"

__all__ = [
    "LandDeedCollection",
    "LandGrantCollection",
]


def _sorted_records[T](registry: dict[SourceID, T], sids: set[SourceID]) -> list[T]:
    return [registry[sid] for sid in sorted(sids, key=lambda s: s.value)]


class LandDeedCollection(BaseSourceCollection[LandDeedRecord, LandDeedRepository]):
    """In-memory collection for LandDeedRecord sources."""

    def __init__(self, repository: LandDeedRepository | None = None) -> None:
        """Initialize LandDeedCollection with party and parcel_location buckets."""
        self._by_party: dict[str, set[SourceID]] = defaultdict(set)
        self._by_parcel_location: dict[str, set[SourceID]] = defaultdict(set)
        super().__init__(repository=repository)

    def _create_default_repository(
        self,
        session_manager: DatabaseSessionManager | None = None,
    ) -> LandDeedRepository:
        return LandDeedRepository(session_manager=session_manager)

    def _deserialize_record(self, data: dict[str, Any]) -> LandDeedRecord:
        return LandDeedRecord.from_dict(data)

    def _index_domain_fields(self, record: LandDeedRecord) -> None:
        for party in (*record.grantors, *record.grantees):
            if party.individual_id is not None:
                self._by_party[party.individual_id.value].add(record.source_id)
        if record.parcel.location_id is not None:
            self._by_parcel_location[record.parcel.location_id.value].add(record.source_id)

    def _unindex_domain_fields(self, record: LandDeedRecord) -> None:
        for party in (*record.grantors, *record.grantees):
            if party.individual_id is not None:
                self._by_party[party.individual_id.value].discard(record.source_id)
        if record.parcel.location_id is not None:
            self._by_parcel_location[record.parcel.location_id.value].discard(record.source_id)

    def find_by_party(
        self,
        individual_id: IndividualID | str,
    ) -> list[LandDeedRecord]:
        """Return active deeds involving a grantor or grantee IndividualID."""
        return _sorted_records(
            self._registry,
            self._by_party.get(_normalize_id(individual_id), set()),
        )

    def find_by_parcel_location(
        self,
        location_id: LocationID | str,
    ) -> list[LandDeedRecord]:
        """Return active deeds for a parcel LocationID."""
        return _sorted_records(
            self._registry,
            self._by_parcel_location.get(_normalize_id(location_id), set()),
        )


class LandGrantCollection(BaseSourceCollection[LandGrantRecord, LandGrantRepository]):
    """In-memory collection for LandGrantRecord sources."""

    def __init__(self, repository: LandGrantRepository | None = None) -> None:
        """Initialize LandGrantCollection with patentee and parcel_location buckets."""
        self._by_patentee: dict[str, set[SourceID]] = defaultdict(set)
        self._by_parcel_location: dict[str, set[SourceID]] = defaultdict(set)
        super().__init__(repository=repository)

    def _create_default_repository(
        self,
        session_manager: DatabaseSessionManager | None = None,
    ) -> LandGrantRepository:
        return LandGrantRepository(session_manager=session_manager)

    def _deserialize_record(self, data: dict[str, Any]) -> LandGrantRecord:
        return LandGrantRecord.from_dict(data)

    def _index_domain_fields(self, record: LandGrantRecord) -> None:
        if record.patentee_id is not None:
            self._by_patentee[record.patentee_id.value].add(record.source_id)
        if record.parcel.location_id is not None:
            self._by_parcel_location[record.parcel.location_id.value].add(record.source_id)

    def _unindex_domain_fields(self, record: LandGrantRecord) -> None:
        if record.patentee_id is not None:
            self._by_patentee[record.patentee_id.value].discard(record.source_id)
        if record.parcel.location_id is not None:
            self._by_parcel_location[record.parcel.location_id.value].discard(record.source_id)

    def find_by_patentee(
        self,
        patentee_id: IndividualID | str,
    ) -> list[LandGrantRecord]:
        """Return active land grants for a patentee IndividualID."""
        return _sorted_records(
            self._registry,
            self._by_patentee.get(_normalize_id(patentee_id), set()),
        )

    def find_by_parcel_location(
        self,
        location_id: LocationID | str,
    ) -> list[LandGrantRecord]:
        """Return active land grants for a parcel LocationID."""
        return _sorted_records(
            self._registry,
            self._by_parcel_location.get(_normalize_id(location_id), set()),
        )
