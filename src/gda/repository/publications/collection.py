"""Path: src/gda/repository/publications/collection.py

In-memory collections for Publications archival source records.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from gda.db.session import DatabaseSessionManager
from gda.model.atom.id import LocationID, OrganizationID, SourceID
from gda.model.source.publications import (
    NewspaperClipRecord,
    PeriodicalArticleRecord,
    Publication,
)
from gda.repository.collection import BaseSourceCollection
from gda.repository.publications.repository import (
    NewspaperClipRepository,
    PeriodicalArticleRepository,
    PublicationRepository,
)
from gda.util.ids import normalize_id
from gda.util.text import clean_string

__version__ = "1.0.0+build.4"

__all__ = [
    "NewspaperClipCollection",
    "PeriodicalArticleCollection",
    "PublicationCollection",
]


class PublicationCollection(BaseSourceCollection[Publication, PublicationRepository]):
    """In-memory collection for serial, newspaper, and periodical catalog records."""

    def __init__(self, repository: PublicationRepository | None = None) -> None:
        """Initialize PublicationCollection with pub_code and location buckets."""
        self._by_pub_code: dict[str, SourceID] = {}
        self._by_location: dict[str, set[SourceID]] = defaultdict(set)
        super().__init__(repository=repository)

    def _create_default_repository(
        self,
        session_manager: DatabaseSessionManager | None = None,
    ) -> PublicationRepository:
        return PublicationRepository(session_manager=session_manager)

    def _deserialize_record(self, data: dict[str, Any]) -> Publication:
        return Publication.from_dict(data)

    def _index_domain_fields(self, record: Publication) -> None:
        self._by_pub_code[record.pub_code] = record.source_id
        if record.location_id is not None:
            self._by_location[record.location_id.value].add(record.source_id)

    def _unindex_domain_fields(self, record: Publication) -> None:
        self._by_pub_code.pop(record.pub_code, None)
        if record.location_id is not None:
            self._by_location[record.location_id.value].discard(record.source_id)

    def get_by_pub_code(self, pub_code: str) -> Publication | None:
        """Return active Publication matching pub_code, or None."""
        clean_code = (clean_string(pub_code) or pub_code).upper()
        sid = self._by_pub_code.get(clean_code)
        return self._registry[sid] if sid is not None else None

    def find_by_location(self, location_id: LocationID | str) -> list[Publication]:
        """Return active Publications for a geographic LocationID."""
        return self._records_for_ids(self._by_location.get(normalize_id(location_id), set()))


class NewspaperClipCollection(BaseSourceCollection[NewspaperClipRecord, NewspaperClipRepository]):
    """In-memory collection for newspaper clippings, obituaries, and notices."""

    def __init__(self, repository: NewspaperClipRepository | None = None) -> None:
        """Initialize NewspaperClipCollection with pub_code and parent_source buckets."""
        self._by_pub_code: dict[str, set[SourceID]] = defaultdict(set)
        self._by_parent: dict[str, set[SourceID]] = defaultdict(set)
        super().__init__(repository=repository)

    def _create_default_repository(
        self,
        session_manager: DatabaseSessionManager | None = None,
    ) -> NewspaperClipRepository:
        return NewspaperClipRepository(session_manager=session_manager)

    def _deserialize_record(self, data: dict[str, Any]) -> NewspaperClipRecord:
        return NewspaperClipRecord.from_dict(data)

    def _index_domain_fields(self, record: NewspaperClipRecord) -> None:
        if record.pub_code is not None:
            self._by_pub_code[record.pub_code].add(record.source_id)
        if record.parent_source_id is not None:
            self._by_parent[record.parent_source_id.value].add(record.source_id)

    def _unindex_domain_fields(self, record: NewspaperClipRecord) -> None:
        if record.pub_code is not None:
            self._by_pub_code[record.pub_code].discard(record.source_id)
        if record.parent_source_id is not None:
            self._by_parent[record.parent_source_id.value].discard(record.source_id)

    def find_by_pub_code(self, pub_code: str) -> list[NewspaperClipRecord]:
        """Return active newspaper clippings for a publication code."""
        clean_code = (clean_string(pub_code) or pub_code).upper()
        return self._records_for_ids(self._by_pub_code.get(clean_code, set()))

    def find_by_parent_source(
        self,
        parent_source_id: SourceID | str,
    ) -> list[NewspaperClipRecord]:
        """Return active newspaper clippings linked to a parent Publication SourceID."""
        return self._records_for_ids(self._by_parent.get(normalize_id(parent_source_id), set()))


class PeriodicalArticleCollection(
    BaseSourceCollection[PeriodicalArticleRecord, PeriodicalArticleRepository]
):
    """In-memory collection for periodical articles, journals, and academic annuals."""

    def __init__(
        self,
        repository: PeriodicalArticleRepository | None = None,
    ) -> None:
        """Initialize PeriodicalArticleCollection with pub_code and org buckets."""
        self._by_pub_code: dict[str, set[SourceID]] = defaultdict(set)
        self._by_org: dict[str, set[SourceID]] = defaultdict(set)
        super().__init__(repository=repository)

    def _create_default_repository(
        self,
        session_manager: DatabaseSessionManager | None = None,
    ) -> PeriodicalArticleRepository:
        return PeriodicalArticleRepository(session_manager=session_manager)

    def _deserialize_record(self, data: dict[str, Any]) -> PeriodicalArticleRecord:
        return PeriodicalArticleRecord.from_dict(data)

    def _index_domain_fields(self, record: PeriodicalArticleRecord) -> None:
        if record.pub_code is not None:
            self._by_pub_code[record.pub_code].add(record.source_id)
        if record.institution_org_id is not None:
            self._by_org[record.institution_org_id.value].add(record.source_id)

    def _unindex_domain_fields(self, record: PeriodicalArticleRecord) -> None:
        if record.pub_code is not None:
            self._by_pub_code[record.pub_code].discard(record.source_id)
        if record.institution_org_id is not None:
            self._by_org[record.institution_org_id.value].discard(record.source_id)

    def find_by_pub_code(self, pub_code: str) -> list[PeriodicalArticleRecord]:
        """Return active periodical articles for a publication code."""
        clean_code = (clean_string(pub_code) or pub_code).upper()
        return self._records_for_ids(self._by_pub_code.get(clean_code, set()))

    def find_by_institution_org(
        self,
        org_id: OrganizationID | str,
    ) -> list[PeriodicalArticleRecord]:
        """Return active periodical articles for a publishing institution OrganizationID."""
        return self._records_for_ids(self._by_org.get(normalize_id(org_id), set()))
