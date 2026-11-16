"""Path: src/gda/repository/manuscripts/collection.py

In-memory collections for Manuscripts archival source records.

Operational Role:
    Provides indexed in-memory collection managers for FamilyBibleRecord and
    NarrativeManuscriptRecord with editing, graveyard lifecycle, and SQLite/JSON
    synchronization.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from gda.db.session import DatabaseSessionManager
from gda.model.atom.id import IndividualID, LocationID, SourceID
from gda.model.source.manuscripts.bible import FamilyBibleRecord
from gda.model.source.manuscripts.narrative import NarrativeManuscriptRecord
from gda.repository.base import _normalize_id
from gda.repository.collection import BaseSourceCollection
from gda.repository.manuscripts.repository import (
    FamilyBibleRepository,
    NarrativeManuscriptRepository,
)

__version__ = "1.0.0+build.1"

__all__ = [
    "FamilyBibleCollection",
    "NarrativeManuscriptCollection",
]


def _sorted_records[T](registry: dict[SourceID, T], sids: set[SourceID]) -> list[T]:
    return [registry[sid] for sid in sorted(sids, key=lambda s: s.value)]


class FamilyBibleCollection(BaseSourceCollection[FamilyBibleRecord, FamilyBibleRepository]):
    """In-memory collection for FamilyBibleRecord sources."""

    def __init__(
        self,
        repository: FamilyBibleRepository | None = None,
    ) -> None:
        """Initialize FamilyBibleCollection with surname and owner buckets."""
        self._by_surname: dict[str, set[SourceID]] = defaultdict(set)
        self._by_owner: dict[str, set[SourceID]] = defaultdict(set)
        super().__init__(repository=repository)

    def _create_default_repository(
        self,
        session_manager: DatabaseSessionManager | None = None,
    ) -> FamilyBibleRepository:
        return FamilyBibleRepository(session_manager=session_manager)

    def _deserialize_record(self, data: dict[str, Any]) -> FamilyBibleRecord:
        return FamilyBibleRecord.from_dict(data)

    def _index_domain_fields(self, record: FamilyBibleRecord) -> None:
        self._by_surname[record.family_surname].add(record.source_id)
        if record.original_owner_id is not None:
            self._by_owner[record.original_owner_id.value].add(record.source_id)

    def _unindex_domain_fields(self, record: FamilyBibleRecord) -> None:
        self._by_surname[record.family_surname].discard(record.source_id)
        if record.original_owner_id is not None:
            self._by_owner[record.original_owner_id.value].discard(record.source_id)

    def find_by_family_surname(
        self,
        family_surname: str,
    ) -> list[FamilyBibleRecord]:
        """Return active family Bible records for a surname."""
        return _sorted_records(
            self._registry,
            self._by_surname.get(family_surname, set()),
        )

    def find_by_original_owner(
        self,
        original_owner_id: IndividualID | str,
    ) -> list[FamilyBibleRecord]:
        """Return active family Bible records for an original owner IndividualID."""
        return _sorted_records(
            self._registry,
            self._by_owner.get(_normalize_id(original_owner_id), set()),
        )


class NarrativeManuscriptCollection(
    BaseSourceCollection[
        NarrativeManuscriptRecord,
        NarrativeManuscriptRepository,
    ]
):
    """In-memory collection for NarrativeManuscriptRecord sources."""

    def __init__(
        self,
        repository: NarrativeManuscriptRepository | None = None,
    ) -> None:
        """Initialize NarrativeManuscriptCollection with author and origin buckets."""
        self._by_author: dict[str, set[SourceID]] = defaultdict(set)
        self._by_origin: dict[str, set[SourceID]] = defaultdict(set)
        super().__init__(repository=repository)

    def _create_default_repository(
        self,
        session_manager: DatabaseSessionManager | None = None,
    ) -> NarrativeManuscriptRepository:
        return NarrativeManuscriptRepository(session_manager=session_manager)

    def _deserialize_record(
        self,
        data: dict[str, Any],
    ) -> NarrativeManuscriptRecord:
        return NarrativeManuscriptRecord.from_dict(data)

    def _index_domain_fields(self, record: NarrativeManuscriptRecord) -> None:
        if record.author_or_sender_id is not None:
            self._by_author[record.author_or_sender_id.value].add(record.source_id)
        if record.origin_place_id is not None:
            self._by_origin[record.origin_place_id.value].add(record.source_id)

    def _unindex_domain_fields(self, record: NarrativeManuscriptRecord) -> None:
        if record.author_or_sender_id is not None:
            self._by_author[record.author_or_sender_id.value].discard(record.source_id)
        if record.origin_place_id is not None:
            self._by_origin[record.origin_place_id.value].discard(record.source_id)

    def find_by_author(
        self,
        author_id: IndividualID | str,
    ) -> list[NarrativeManuscriptRecord]:
        """Return active narrative manuscripts for an author IndividualID."""
        return _sorted_records(
            self._registry,
            self._by_author.get(_normalize_id(author_id), set()),
        )

    def find_by_origin_place(
        self,
        location_id: LocationID | str,
    ) -> list[NarrativeManuscriptRecord]:
        """Return active narrative manuscripts for an origin LocationID."""
        return _sorted_records(
            self._registry,
            self._by_origin.get(_normalize_id(location_id), set()),
        )
