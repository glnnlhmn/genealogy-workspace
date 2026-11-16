"""Path: src/gda/repository/publications/repository.py

SQLite repositories for Publications archival source records.

Operational Role:
    Provides concrete CRUD and domain-specialized analytical repositories for
    Publication catalog entries, NewspaperClipRecord items, and
    PeriodicalArticleRecord items.
"""

from __future__ import annotations

from gda.db.mapper.enumerated_publications import (
    NewspaperClipRecordMapper,
    PeriodicalArticleRecordMapper,
    PublicationMapper,
)
from gda.db.session import DatabaseSessionManager
from gda.model.atom.id import LocationID, OrganizationID, SourceID
from gda.model.source.publications import (
    NewspaperClipRecord,
    PeriodicalArticleRecord,
    Publication,
)
from gda.repository.base import BaseSQLiteRepository, _normalize_id
from gda.repository.query import FilterOp, SortOrder

__version__ = "1.0.0+build.1"

__all__ = [
    "NewspaperClipRepository",
    "PeriodicalArticleRepository",
    "PublicationRepository",
]


class PublicationRepository(BaseSQLiteRepository[Publication, SourceID]):
    """SQLite repository for serial, newspaper, and periodical master catalog records."""

    def __init__(
        self,
        session_manager: DatabaseSessionManager | None = None,
        mapper: PublicationMapper | None = None,
    ) -> None:
        """Initialize PublicationRepository."""
        super().__init__(
            mapper=mapper or PublicationMapper(),
            session_manager=session_manager,
        )

    @property
    def table_name(self) -> str:
        """Return target SQLite table name."""
        return "publications_catalog"

    def get_by_pub_code(self, pub_code: str) -> Publication | None:
        """Retrieve a Publication catalog record by its unique pub_code."""
        matches = self.find_by(pub_code=pub_code)
        return matches[0] if matches else None

    def find_by_location(self, location_id: LocationID | str) -> list[Publication]:
        """Find publications published in a specific geographic LocationID."""
        return self.find_by(location_id=_normalize_id(location_id))


class NewspaperClipRepository(BaseSQLiteRepository[NewspaperClipRecord, SourceID]):
    """SQLite repository for newspaper clippings, obituaries, and notices."""

    def __init__(
        self,
        session_manager: DatabaseSessionManager | None = None,
        mapper: NewspaperClipRecordMapper | None = None,
    ) -> None:
        """Initialize NewspaperClipRepository."""
        super().__init__(
            mapper=mapper or NewspaperClipRecordMapper(),
            session_manager=session_manager,
        )

    @property
    def table_name(self) -> str:
        """Return target SQLite table name."""
        return "publications_newspaper_clips"

    def find_by_pub_code(self, pub_code: str) -> list[NewspaperClipRecord]:
        """Find newspaper clippings matching a parent publication code."""
        return self.find_by(pub_code=pub_code)

    def find_by_parent_source(
        self,
        parent_source_id: SourceID | str,
    ) -> list[NewspaperClipRecord]:
        """Find newspaper clippings linked to a parent Publication SourceID."""
        return self.find_by(parent_source_id=_normalize_id(parent_source_id))

    def find_by_location(
        self,
        location_id: LocationID | str,
    ) -> list[NewspaperClipRecord]:
        """Find newspaper clippings linked to a publication_location_id."""
        return self.find_by(publication_location_id=_normalize_id(location_id))

    def find_by_year_range(
        self,
        start_year: int,
        end_year: int,
    ) -> list[NewspaperClipRecord]:
        """Find newspaper clippings within an inclusive issue year range."""
        qb = (
            self.query()
            .where("issue_year", start_year, FilterOp.GE)
            .where("issue_year", end_year, FilterOp.LE)
            .order_by("issue_date_sort", SortOrder.ASC)
            .order_by("id", SortOrder.ASC)
        )
        return self.find_where(qb)


class PeriodicalArticleRepository(BaseSQLiteRepository[PeriodicalArticleRecord, SourceID]):
    """SQLite repository for periodical articles, journals, and academic annuals."""

    def __init__(
        self,
        session_manager: DatabaseSessionManager | None = None,
        mapper: PeriodicalArticleRecordMapper | None = None,
    ) -> None:
        """Initialize PeriodicalArticleRepository."""
        super().__init__(
            mapper=mapper or PeriodicalArticleRecordMapper(),
            session_manager=session_manager,
        )

    @property
    def table_name(self) -> str:
        """Return target SQLite table name."""
        return "publications_periodical_articles"

    def find_by_pub_code(self, pub_code: str) -> list[PeriodicalArticleRecord]:
        """Find periodical articles matching a parent publication code."""
        return self.find_by(pub_code=pub_code)

    def find_by_parent_source(
        self,
        parent_source_id: SourceID | str,
    ) -> list[PeriodicalArticleRecord]:
        """Find periodical articles linked to a parent Publication SourceID."""
        return self.find_by(parent_source_id=_normalize_id(parent_source_id))

    def find_by_institution_org(
        self,
        org_id: OrganizationID | str,
    ) -> list[PeriodicalArticleRecord]:
        """Find periodical articles linked to a publishing institution OrganizationID."""
        return self.find_by(institution_org_id=_normalize_id(org_id))

    def find_by_year_range(
        self,
        start_year: int,
        end_year: int,
    ) -> list[PeriodicalArticleRecord]:
        """Find periodical articles within an inclusive publication year range."""
        qb = (
            self.query()
            .where("published_year", start_year, FilterOp.GE)
            .where("published_year", end_year, FilterOp.LE)
            .order_by("published_date_sort", SortOrder.ASC)
            .order_by("id", SortOrder.ASC)
        )
        return self.find_where(qb)
