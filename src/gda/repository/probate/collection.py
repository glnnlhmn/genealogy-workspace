"""Path: src/gda/repository/probate/collection.py

In-memory collections for Probate archival source records.

Operational Role:
    Provides indexed in-memory collection managers for ProbateRecord and
    EstateInventoryRecord with editing, graveyard lifecycle, and SQLite/JSON
    persistence synchronization.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from gda.db.session import DatabaseSessionManager
from gda.model.atom.id import IndividualID, LocationID, SourceID
from gda.model.source.probate.inventory import EstateInventoryRecord
from gda.model.source.probate.will import ProbateRecord
from gda.repository.base import _normalize_id
from gda.repository.collection import BaseSourceCollection
from gda.repository.probate.repository import (
    EstateInventoryRepository,
    ProbateRepository,
)

__version__ = "1.0.0+build.1"

__all__ = [
    "EstateInventoryCollection",
    "ProbateCollection",
]


def _sorted_records[T](registry: dict[SourceID, T], sids: set[SourceID]) -> list[T]:
    return [registry[sid] for sid in sorted(sids, key=lambda s: s.value)]


class ProbateCollection(BaseSourceCollection[ProbateRecord, ProbateRepository]):
    """In-memory collection for ProbateRecord (wills, codicils, and letters)."""

    def __init__(self, repository: ProbateRepository | None = None) -> None:
        """Initialize ProbateCollection with decedent and court_location buckets."""
        self._by_decedent: dict[str, set[SourceID]] = defaultdict(set)
        self._by_court_location: dict[str, set[SourceID]] = defaultdict(set)
        super().__init__(repository=repository)

    def _create_default_repository(
        self,
        session_manager: DatabaseSessionManager | None = None,
    ) -> ProbateRepository:
        return ProbateRepository(session_manager=session_manager)

    def _deserialize_record(self, data: dict[str, Any]) -> ProbateRecord:
        return ProbateRecord.from_dict(data)

    def _index_domain_fields(self, record: ProbateRecord) -> None:
        if record.decedent_id is not None:
            self._by_decedent[record.decedent_id.value].add(record.source_id)
        if record.court_location_id is not None:
            self._by_court_location[record.court_location_id.value].add(record.source_id)

    def _unindex_domain_fields(self, record: ProbateRecord) -> None:
        if record.decedent_id is not None:
            self._by_decedent[record.decedent_id.value].discard(record.source_id)
        if record.court_location_id is not None:
            self._by_court_location[record.court_location_id.value].discard(record.source_id)

    def find_by_decedent(
        self,
        decedent_id: IndividualID | str,
    ) -> list[ProbateRecord]:
        """Return active probate records for a decedent IndividualID."""
        return _sorted_records(
            self._registry,
            self._by_decedent.get(_normalize_id(decedent_id), set()),
        )

    def find_by_court_location(
        self,
        court_location_id: LocationID | str,
    ) -> list[ProbateRecord]:
        """Return active probate records for a court jurisdiction LocationID."""
        return _sorted_records(
            self._registry,
            self._by_court_location.get(_normalize_id(court_location_id), set()),
        )


class EstateInventoryCollection(
    BaseSourceCollection[EstateInventoryRecord, EstateInventoryRepository]
):
    """In-memory collection for EstateInventoryRecord sources."""

    def __init__(
        self,
        repository: EstateInventoryRepository | None = None,
    ) -> None:
        """Initialize EstateInventoryCollection with decedent and parent buckets."""
        self._by_decedent: dict[str, set[SourceID]] = defaultdict(set)
        self._by_parent_probate: dict[str, set[SourceID]] = defaultdict(set)
        super().__init__(repository=repository)

    def _create_default_repository(
        self,
        session_manager: DatabaseSessionManager | None = None,
    ) -> EstateInventoryRepository:
        return EstateInventoryRepository(session_manager=session_manager)

    def _deserialize_record(self, data: dict[str, Any]) -> EstateInventoryRecord:
        return EstateInventoryRecord.from_dict(data)

    def _index_domain_fields(self, record: EstateInventoryRecord) -> None:
        if record.decedent_id is not None:
            self._by_decedent[record.decedent_id.value].add(record.source_id)
        if record.parent_probate_source_id is not None:
            self._by_parent_probate[record.parent_probate_source_id.value].add(record.source_id)

    def _unindex_domain_fields(self, record: EstateInventoryRecord) -> None:
        if record.decedent_id is not None:
            self._by_decedent[record.decedent_id.value].discard(record.source_id)
        if record.parent_probate_source_id is not None:
            self._by_parent_probate[record.parent_probate_source_id.value].discard(record.source_id)

    def find_by_decedent(
        self,
        decedent_id: IndividualID | str,
    ) -> list[EstateInventoryRecord]:
        """Return active estate inventories for a decedent IndividualID."""
        return _sorted_records(
            self._registry,
            self._by_decedent.get(_normalize_id(decedent_id), set()),
        )

    def find_by_parent_probate_source(
        self,
        parent_probate_source_id: SourceID | str,
    ) -> list[EstateInventoryRecord]:
        """Return active estate inventories linked to a parent ProbateRecord SourceID."""
        return _sorted_records(
            self._registry,
            self._by_parent_probate.get(_normalize_id(parent_probate_source_id), set()),
        )
