"""Path: src/gda/repository/immigration/collection.py

In-memory collections for Immigration archival source records.

Operational Role:
    Provides indexed in-memory collection managers for ImmigrationManifestRecord
    and NaturalizationRecord with editing, graveyard lifecycle, and SQLite/JSON
    persistence synchronization.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from gda.db.session import DatabaseSessionManager
from gda.model.atom.id import IndividualID, LocationID, SourceID
from gda.model.source.immigration.manifest import ImmigrationManifestRecord
from gda.model.source.immigration.naturalization import NaturalizationRecord
from gda.repository.base import _normalize_id
from gda.repository.collection import BaseSourceCollection
from gda.repository.immigration.repository import (
    ImmigrationManifestRepository,
    NaturalizationRepository,
)

__version__ = "1.0.0+build.1"

__all__ = [
    "ImmigrationManifestCollection",
    "NaturalizationCollection",
]


def _sorted_records[T](registry: dict[SourceID, T], sids: set[SourceID]) -> list[T]:
    return [registry[sid] for sid in sorted(sids, key=lambda s: s.value)]


class ImmigrationManifestCollection(
    BaseSourceCollection[ImmigrationManifestRecord, ImmigrationManifestRepository]
):
    """In-memory collection for ImmigrationManifestRecord sources."""

    def __init__(
        self,
        repository: ImmigrationManifestRepository | None = None,
    ) -> None:
        """Initialize ImmigrationManifestCollection with passenger and port buckets."""
        self._by_passenger: dict[str, set[SourceID]] = defaultdict(set)
        self._by_port: dict[str, set[SourceID]] = defaultdict(set)
        super().__init__(repository=repository)

    def _create_default_repository(
        self,
        session_manager: DatabaseSessionManager | None = None,
    ) -> ImmigrationManifestRepository:
        return ImmigrationManifestRepository(session_manager=session_manager)

    def _deserialize_record(
        self,
        data: dict[str, Any],
    ) -> ImmigrationManifestRecord:
        return ImmigrationManifestRecord.from_dict(data)

    def _index_domain_fields(self, record: ImmigrationManifestRecord) -> None:
        for pax in record.passengers:
            if pax.individual_id is not None:
                self._by_passenger[pax.individual_id.value].add(record.source_id)
        if record.port_of_arrival_id is not None:
            self._by_port[record.port_of_arrival_id.value].add(record.source_id)

    def _unindex_domain_fields(self, record: ImmigrationManifestRecord) -> None:
        for pax in record.passengers:
            if pax.individual_id is not None:
                self._by_passenger[pax.individual_id.value].discard(record.source_id)
        if record.port_of_arrival_id is not None:
            self._by_port[record.port_of_arrival_id.value].discard(record.source_id)

    def find_by_passenger(
        self,
        individual_id: IndividualID | str,
    ) -> list[ImmigrationManifestRecord]:
        """Return active manifests containing a linked passenger IndividualID."""
        return _sorted_records(
            self._registry,
            self._by_passenger.get(_normalize_id(individual_id), set()),
        )

    def find_by_port_of_arrival(
        self,
        port_of_arrival_id: LocationID | str,
    ) -> list[ImmigrationManifestRecord]:
        """Return active manifests for a port of arrival LocationID."""
        return _sorted_records(
            self._registry,
            self._by_port.get(_normalize_id(port_of_arrival_id), set()),
        )


class NaturalizationCollection(
    BaseSourceCollection[NaturalizationRecord, NaturalizationRepository]
):
    """In-memory collection for NaturalizationRecord sources."""

    def __init__(
        self,
        repository: NaturalizationRepository | None = None,
    ) -> None:
        """Initialize NaturalizationCollection with applicant and court_location buckets."""
        self._by_applicant: dict[str, set[SourceID]] = defaultdict(set)
        self._by_court_location: dict[str, set[SourceID]] = defaultdict(set)
        super().__init__(repository=repository)

    def _create_default_repository(
        self,
        session_manager: DatabaseSessionManager | None = None,
    ) -> NaturalizationRepository:
        return NaturalizationRepository(session_manager=session_manager)

    def _deserialize_record(self, data: dict[str, Any]) -> NaturalizationRecord:
        return NaturalizationRecord.from_dict(data)

    def _index_domain_fields(self, record: NaturalizationRecord) -> None:
        if record.applicant_id is not None:
            self._by_applicant[record.applicant_id.value].add(record.source_id)
        if record.court_location_id is not None:
            self._by_court_location[record.court_location_id.value].add(record.source_id)

    def _unindex_domain_fields(self, record: NaturalizationRecord) -> None:
        if record.applicant_id is not None:
            self._by_applicant[record.applicant_id.value].discard(record.source_id)
        if record.court_location_id is not None:
            self._by_court_location[record.court_location_id.value].discard(record.source_id)

    def find_by_applicant(
        self,
        applicant_id: IndividualID | str,
    ) -> list[NaturalizationRecord]:
        """Return active naturalization records for an applicant IndividualID."""
        return _sorted_records(
            self._registry,
            self._by_applicant.get(_normalize_id(applicant_id), set()),
        )

    def find_by_court_location(
        self,
        court_location_id: LocationID | str,
    ) -> list[NaturalizationRecord]:
        """Return active naturalization records for a court LocationID."""
        return _sorted_records(
            self._registry,
            self._by_court_location.get(_normalize_id(court_location_id), set()),
        )
