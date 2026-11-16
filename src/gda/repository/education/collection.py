"""Path: src/gda/repository/education/collection.py

In-memory collection for Education archival source records.

Operational Role:
    Provides indexed in-memory collection management for AcademicCredentialRecord
    with editing, graveyard lifecycle, and SQLite/JSON synchronization.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from gda.db.session import DatabaseSessionManager
from gda.model.atom.id import IndividualID, LocationID, SourceID
from gda.model.source.education.credential import AcademicCredentialRecord
from gda.repository.base import _normalize_id
from gda.repository.collection import BaseSourceCollection
from gda.repository.education.repository import AcademicCredentialRepository

__version__ = "1.0.0+build.1"

__all__ = [
    "AcademicCredentialCollection",
]


def _sorted_records[T](registry: dict[SourceID, T], sids: set[SourceID]) -> list[T]:
    return [registry[sid] for sid in sorted(sids, key=lambda s: s.value)]


class AcademicCredentialCollection(
    BaseSourceCollection[AcademicCredentialRecord, AcademicCredentialRepository]
):
    """In-memory collection for AcademicCredentialRecord sources."""

    def __init__(
        self,
        repository: AcademicCredentialRepository | None = None,
    ) -> None:
        """Initialize AcademicCredentialCollection with subject and location buckets."""
        self._by_subject: dict[str, set[SourceID]] = defaultdict(set)
        self._by_location: dict[str, set[SourceID]] = defaultdict(set)
        super().__init__(repository=repository)

    def _create_default_repository(
        self,
        session_manager: DatabaseSessionManager | None = None,
    ) -> AcademicCredentialRepository:
        return AcademicCredentialRepository(session_manager=session_manager)

    def _deserialize_record(
        self,
        data: dict[str, Any],
    ) -> AcademicCredentialRecord:
        return AcademicCredentialRecord.from_dict(data)

    def _index_domain_fields(self, record: AcademicCredentialRecord) -> None:
        if record.subject_id is not None:
            self._by_subject[record.subject_id.value].add(record.source_id)
        if record.institution_location_id is not None:
            self._by_location[record.institution_location_id.value].add(record.source_id)

    def _unindex_domain_fields(self, record: AcademicCredentialRecord) -> None:
        if record.subject_id is not None:
            self._by_subject[record.subject_id.value].discard(record.source_id)
        if record.institution_location_id is not None:
            self._by_location[record.institution_location_id.value].discard(record.source_id)

    def find_by_subject(
        self,
        subject_id: IndividualID | str,
    ) -> list[AcademicCredentialRecord]:
        """Return active academic credentials for a subject IndividualID."""
        return _sorted_records(
            self._registry,
            self._by_subject.get(_normalize_id(subject_id), set()),
        )

    def find_by_institution_location(
        self,
        location_id: LocationID | str,
    ) -> list[AcademicCredentialRecord]:
        """Return active academic credentials for an institution LocationID."""
        return _sorted_records(
            self._registry,
            self._by_location.get(_normalize_id(location_id), set()),
        )
