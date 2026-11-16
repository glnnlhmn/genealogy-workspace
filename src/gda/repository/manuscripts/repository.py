"""Path: src/gda/repository/manuscripts/repository.py

SQLite repositories for Manuscripts archival source records.

Operational Role:
    Provides concrete CRUD and domain-specialized analytical repositories for
    FamilyBibleRecord (inscribed family Bible vital registers) and
    NarrativeManuscriptRecord (letters, diaries, memoirs, depositions).
"""

from __future__ import annotations

from gda.db.mapper.education_manuscripts_orgs_other import (
    FamilyBibleRecordMapper,
    NarrativeManuscriptRecordMapper,
)
from gda.db.session import DatabaseSessionManager
from gda.model.atom.id import IndividualID, LocationID, SourceID
from gda.model.source.manuscripts.bible import FamilyBibleRecord
from gda.model.source.manuscripts.narrative import NarrativeManuscriptRecord
from gda.repository.base import BaseSQLiteRepository, _normalize_id
from gda.repository.query import FilterOp, SortOrder

__version__ = "1.0.0+build.1"

__all__ = [
    "FamilyBibleRepository",
    "NarrativeManuscriptRepository",
]


class FamilyBibleRepository(BaseSQLiteRepository[FamilyBibleRecord, SourceID]):
    """SQLite repository for family Bible registers."""

    def __init__(
        self,
        session_manager: DatabaseSessionManager | None = None,
        mapper: FamilyBibleRecordMapper | None = None,
    ) -> None:
        """Initialize FamilyBibleRepository."""
        super().__init__(
            mapper=mapper or FamilyBibleRecordMapper(),
            session_manager=session_manager,
        )

    @property
    def table_name(self) -> str:
        """Return target SQLite table name."""
        return "manuscripts_family_bibles"

    def find_by_family_surname(
        self,
        family_surname: str,
    ) -> list[FamilyBibleRecord]:
        """Find family Bible records matching a primary family surname."""
        return self.find_by(family_surname=family_surname)

    def find_by_original_owner(
        self,
        original_owner_id: IndividualID | str,
    ) -> list[FamilyBibleRecord]:
        """Find family Bible records linked to an original owner IndividualID."""
        return self.find_by(original_owner_id=_normalize_id(original_owner_id))


class NarrativeManuscriptRepository(BaseSQLiteRepository[NarrativeManuscriptRecord, SourceID]):
    """SQLite repository for letters, diaries, memoirs, and oral histories."""

    def __init__(
        self,
        session_manager: DatabaseSessionManager | None = None,
        mapper: NarrativeManuscriptRecordMapper | None = None,
    ) -> None:
        """Initialize NarrativeManuscriptRepository."""
        super().__init__(
            mapper=mapper or NarrativeManuscriptRecordMapper(),
            session_manager=session_manager,
        )

    @property
    def table_name(self) -> str:
        """Return target SQLite table name."""
        return "manuscripts_narratives"

    def find_by_author(
        self,
        author_id: IndividualID | str,
    ) -> list[NarrativeManuscriptRecord]:
        """Find narrative manuscripts linked to an author or sender IndividualID."""
        return self.find_by(author_or_sender_id=_normalize_id(author_id))

    def find_by_recipient(
        self,
        recipient_id: IndividualID | str,
    ) -> list[NarrativeManuscriptRecord]:
        """Find narrative manuscripts linked to a recipient IndividualID."""
        return self.find_by(recipient_id=_normalize_id(recipient_id))

    def find_by_origin_place(
        self,
        location_id: LocationID | str,
    ) -> list[NarrativeManuscriptRecord]:
        """Find narrative manuscripts written at an origin LocationID."""
        return self.find_by(origin_place_id=_normalize_id(location_id))

    def find_by_written_year_range(
        self,
        start_year: int,
        end_year: int,
    ) -> list[NarrativeManuscriptRecord]:
        """Find narrative manuscripts written within an inclusive year range."""
        qb = (
            self.query()
            .where("written_year", start_year, FilterOp.GE)
            .where("written_year", end_year, FilterOp.LE)
            .order_by("written_date_sort", SortOrder.ASC)
            .order_by("id", SortOrder.ASC)
        )
        return self.find_where(qb)
