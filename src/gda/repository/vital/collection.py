"""Path: src/gda/repository/vital/collection.py

In-memory collections for Vital archival source records.

Operational Role:
    Provides indexed in-memory collection managers for BaptismRecord, BirthRecord,
    DeathRecord, DivorceRecord, and MarriageRecord with editing, graveyard
    lifecycle, and SQLite persistence synchronization.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from gda.db.session import DatabaseSessionManager
from gda.model.atom.id import IndividualID, LocationID, SourceID
from gda.model.source.vital.baptism import BaptismRecord
from gda.model.source.vital.birth import BirthRecord
from gda.model.source.vital.death import DeathRecord
from gda.model.source.vital.divorce import DivorceRecord
from gda.model.source.vital.marriage import MarriageRecord
from gda.repository.base import _normalize_id
from gda.repository.collection import BaseSourceCollection
from gda.repository.vital.repository import (
    BaptismRepository,
    BirthRepository,
    DeathRepository,
    DivorceRepository,
    MarriageRepository,
)

__version__ = "1.0.0+build.2"

__all__ = [
    "BaptismCollection",
    "BirthCollection",
    "DeathCollection",
    "DivorceCollection",
    "MarriageCollection",
]


def _sorted_records[T](registry: dict[SourceID, T], sids: set[SourceID]) -> list[T]:
    return [registry[sid] for sid in sorted(sids, key=lambda s: s.value)]


class BaptismCollection(BaseSourceCollection[BaptismRecord, BaptismRepository]):
    """In-memory collection for ecclesiastical BaptismRecord sources."""

    def __init__(self, repository: BaptismRepository | None = None) -> None:
        """Initialize BaptismCollection with secondary index buckets."""
        self._by_individual: dict[str, set[SourceID]] = defaultdict(set)
        self._by_location: dict[str, set[SourceID]] = defaultdict(set)
        super().__init__(repository=repository)

    def _create_default_repository(
        self,
        session_manager: DatabaseSessionManager | None = None,
    ) -> BaptismRepository:
        return BaptismRepository(session_manager=session_manager)

    def _deserialize_record(self, data: dict[str, Any]) -> BaptismRecord:
        return BaptismRecord.from_dict(data)

    def _index_domain_fields(self, record: BaptismRecord) -> None:
        if record.individual_id is not None:
            self._by_individual[record.individual_id.value].add(record.source_id)
        if record.location_id is not None:
            self._by_location[record.location_id.value].add(record.source_id)

    def _unindex_domain_fields(self, record: BaptismRecord) -> None:
        if record.individual_id is not None:
            self._by_individual[record.individual_id.value].discard(record.source_id)
        if record.location_id is not None:
            self._by_location[record.location_id.value].discard(record.source_id)

    def find_by_individual(self, individual_id: IndividualID | str) -> list[BaptismRecord]:
        """Return active baptism records for an individual from in-memory index."""
        return _sorted_records(
            self._registry,
            self._by_individual.get(_normalize_id(individual_id), set()),
        )

    def find_by_location(self, location_id: LocationID | str) -> list[BaptismRecord]:
        """Return active baptism records for a location from in-memory index."""
        return _sorted_records(
            self._registry,
            self._by_location.get(_normalize_id(location_id), set()),
        )


class BirthCollection(BaseSourceCollection[BirthRecord, BirthRepository]):
    """In-memory collection for civil and archival BirthRecord sources."""

    def __init__(self, repository: BirthRepository | None = None) -> None:
        """Initialize BirthCollection with secondary index buckets."""
        self._by_child: dict[str, set[SourceID]] = defaultdict(set)
        self._by_location: dict[str, set[SourceID]] = defaultdict(set)
        super().__init__(repository=repository)

    def _create_default_repository(
        self,
        session_manager: DatabaseSessionManager | None = None,
    ) -> BirthRepository:
        return BirthRepository(session_manager=session_manager)

    def _deserialize_record(self, data: dict[str, Any]) -> BirthRecord:
        return BirthRecord.from_dict(data)

    def _index_domain_fields(self, record: BirthRecord) -> None:
        if record.child_id is not None:
            self._by_child[record.child_id.value].add(record.source_id)
        if record.place_of_birth_id is not None:
            self._by_location[record.place_of_birth_id.value].add(record.source_id)

    def _unindex_domain_fields(self, record: BirthRecord) -> None:
        if record.child_id is not None:
            self._by_child[record.child_id.value].discard(record.source_id)
        if record.place_of_birth_id is not None:
            self._by_location[record.place_of_birth_id.value].discard(record.source_id)

    def find_by_child(self, child_id: IndividualID | str) -> list[BirthRecord]:
        """Return active birth records for a child IndividualID from in-memory index."""
        return _sorted_records(
            self._registry,
            self._by_child.get(_normalize_id(child_id), set()),
        )

    def find_by_location(self, location_id: LocationID | str) -> list[BirthRecord]:
        """Return active birth records for a place_of_birth_id from in-memory index."""
        return _sorted_records(
            self._registry,
            self._by_location.get(_normalize_id(location_id), set()),
        )


class DeathCollection(BaseSourceCollection[DeathRecord, DeathRepository]):
    """In-memory collection for civil and archival DeathRecord sources."""

    def __init__(self, repository: DeathRepository | None = None) -> None:
        """Initialize DeathCollection with secondary index buckets."""
        self._by_decedent: dict[str, set[SourceID]] = defaultdict(set)
        self._by_location: dict[str, set[SourceID]] = defaultdict(set)
        super().__init__(repository=repository)

    def _create_default_repository(
        self,
        session_manager: DatabaseSessionManager | None = None,
    ) -> DeathRepository:
        return DeathRepository(session_manager=session_manager)

    def _deserialize_record(self, data: dict[str, Any]) -> DeathRecord:
        return DeathRecord.from_dict(data)

    def _index_domain_fields(self, record: DeathRecord) -> None:
        if record.decedent_id is not None:
            self._by_decedent[record.decedent_id.value].add(record.source_id)
        if record.place_of_death_id is not None:
            self._by_location[record.place_of_death_id.value].add(record.source_id)

    def _unindex_domain_fields(self, record: DeathRecord) -> None:
        if record.decedent_id is not None:
            self._by_decedent[record.decedent_id.value].discard(record.source_id)
        if record.place_of_death_id is not None:
            self._by_location[record.place_of_death_id.value].discard(record.source_id)

    def find_by_decedent(self, decedent_id: IndividualID | str) -> list[DeathRecord]:
        """Return active death records for a decedent IndividualID from in-memory index."""
        return _sorted_records(
            self._registry,
            self._by_decedent.get(_normalize_id(decedent_id), set()),
        )

    def find_by_location(self, location_id: LocationID | str) -> list[DeathRecord]:
        """Return active death records for a place_of_death_id from in-memory index."""
        return _sorted_records(
            self._registry,
            self._by_location.get(_normalize_id(location_id), set()),
        )


class DivorceCollection(BaseSourceCollection[DivorceRecord, DivorceRepository]):
    """In-memory collection for judicial DivorceRecord sources."""

    def __init__(self, repository: DivorceRepository | None = None) -> None:
        """Initialize DivorceCollection with secondary index buckets."""
        self._by_spouse: dict[str, set[SourceID]] = defaultdict(set)
        self._by_jurisdiction: dict[str, set[SourceID]] = defaultdict(set)
        super().__init__(repository=repository)

    def _create_default_repository(
        self,
        session_manager: DatabaseSessionManager | None = None,
    ) -> DivorceRepository:
        return DivorceRepository(session_manager=session_manager)

    def _deserialize_record(self, data: dict[str, Any]) -> DivorceRecord:
        return DivorceRecord.from_dict(data)

    def _index_domain_fields(self, record: DivorceRecord) -> None:
        if record.husband_id is not None:
            self._by_spouse[record.husband_id.value].add(record.source_id)
        if record.wife_id is not None:
            self._by_spouse[record.wife_id.value].add(record.source_id)
        if record.jurisdiction_id is not None:
            self._by_jurisdiction[record.jurisdiction_id.value].add(record.source_id)

    def _unindex_domain_fields(self, record: DivorceRecord) -> None:
        if record.husband_id is not None:
            self._by_spouse[record.husband_id.value].discard(record.source_id)
        if record.wife_id is not None:
            self._by_spouse[record.wife_id.value].discard(record.source_id)
        if record.jurisdiction_id is not None:
            self._by_jurisdiction[record.jurisdiction_id.value].discard(record.source_id)

    def find_by_spouse(self, spouse_id: IndividualID | str) -> list[DivorceRecord]:
        """Return active divorce records involving a husband or wife IndividualID."""
        return _sorted_records(
            self._registry,
            self._by_spouse.get(_normalize_id(spouse_id), set()),
        )

    def find_by_jurisdiction(
        self,
        jurisdiction_id: LocationID | str,
    ) -> list[DivorceRecord]:
        """Return active divorce records for a court jurisdiction LocationID."""
        return _sorted_records(
            self._registry,
            self._by_jurisdiction.get(_normalize_id(jurisdiction_id), set()),
        )


class MarriageCollection(BaseSourceCollection[MarriageRecord, MarriageRepository]):
    """In-memory collection for civil and ecclesiastical MarriageRecord sources."""

    def __init__(self, repository: MarriageRepository | None = None) -> None:
        """Initialize MarriageCollection with secondary index buckets."""
        self._by_spouse: dict[str, set[SourceID]] = defaultdict(set)
        self._by_location: dict[str, set[SourceID]] = defaultdict(set)
        super().__init__(repository=repository)

    def _create_default_repository(
        self,
        session_manager: DatabaseSessionManager | None = None,
    ) -> MarriageRepository:
        return MarriageRepository(session_manager=session_manager)

    def _deserialize_record(self, data: dict[str, Any]) -> MarriageRecord:
        return MarriageRecord.from_dict(data)

    def _index_domain_fields(self, record: MarriageRecord) -> None:
        if record.groom_id is not None:
            self._by_spouse[record.groom_id.value].add(record.source_id)
        if record.bride_id is not None:
            self._by_spouse[record.bride_id.value].add(record.source_id)
        if record.place_of_marriage_id is not None:
            self._by_location[record.place_of_marriage_id.value].add(record.source_id)

    def _unindex_domain_fields(self, record: MarriageRecord) -> None:
        if record.groom_id is not None:
            self._by_spouse[record.groom_id.value].discard(record.source_id)
        if record.bride_id is not None:
            self._by_spouse[record.bride_id.value].discard(record.source_id)
        if record.place_of_marriage_id is not None:
            self._by_location[record.place_of_marriage_id.value].discard(record.source_id)

    def find_by_spouse(self, spouse_id: IndividualID | str) -> list[MarriageRecord]:
        """Return active marriage records involving a groom or bride IndividualID."""
        return _sorted_records(
            self._registry,
            self._by_spouse.get(_normalize_id(spouse_id), set()),
        )

    def find_by_location(self, location_id: LocationID | str) -> list[MarriageRecord]:
        """Return active marriage records for a place_of_marriage_id."""
        return _sorted_records(
            self._registry,
            self._by_location.get(_normalize_id(location_id), set()),
        )
