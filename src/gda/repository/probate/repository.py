"""Path: src/gda/repository/probate/repository.py

SQLite repositories for Probate archival source records.

Operational Role:
    Provides concrete CRUD and domain-specialized analytical repositories for
    ProbateRecord (wills, codicils, letters) and EstateInventoryRecord
    (inventories, appraisals, administration accounts).
"""

from __future__ import annotations

from gda.db.mapper.probate_land import (
    EstateInventoryRecordMapper,
    ProbateRecordMapper,
)
from gda.db.session import DatabaseSessionManager
from gda.model.atom.id import IndividualID, LocationID, SourceID
from gda.model.source.probate.inventory import EstateInventoryRecord
from gda.model.source.probate.will import ProbateRecord
from gda.repository.base import BaseSQLiteRepository
from gda.repository.query import FilterOp, SortOrder
from gda.util.ids import normalize_id

__version__ = "1.0.0+build.2"

__all__ = [
    "EstateInventoryRepository",
    "ProbateRepository",
]


class ProbateRepository(BaseSQLiteRepository[ProbateRecord, SourceID]):
    """SQLite repository for wills, codicils, and letters of administration."""

    def __init__(
        self,
        session_manager: DatabaseSessionManager | None = None,
        mapper: ProbateRecordMapper | None = None,
    ) -> None:
        """Initialize ProbateRepository."""
        super().__init__(
            mapper=mapper or ProbateRecordMapper(),
            session_manager=session_manager,
        )

    @property
    def table_name(self) -> str:
        """Return target SQLite table name."""
        return "probate_wills"

    def find_by_decedent(
        self,
        decedent_id: IndividualID | str,
    ) -> list[ProbateRecord]:
        """Find probate records linked to a decedent IndividualID."""
        return self.find_by(decedent_id=normalize_id(decedent_id))

    def find_by_court_location(
        self,
        court_location_id: LocationID | str,
    ) -> list[ProbateRecord]:
        """Find probate records filed in a court jurisdiction LocationID."""
        return self.find_by(court_location_id=normalize_id(court_location_id))

    def find_by_estate_file_number(
        self,
        estate_file_number: str,
    ) -> list[ProbateRecord]:
        """Find probate records matching an official estate packet/file number."""
        return self.find_by(estate_file_number=estate_file_number)

    def find_by_probated_year_range(
        self,
        start_year: int,
        end_year: int,
    ) -> list[ProbateRecord]:
        """Find probate records admitted to probate within an inclusive year range."""
        qb = (
            self.query()
            .where("probated_year", start_year, FilterOp.GE)
            .where("probated_year", end_year, FilterOp.LE)
            .order_by("probated_date_sort", SortOrder.ASC)
            .order_by("id", SortOrder.ASC)
        )
        return self.find_where(qb)


class EstateInventoryRepository(BaseSQLiteRepository[EstateInventoryRecord, SourceID]):
    """SQLite repository for estate inventories, appraisals, and accounts."""

    def __init__(
        self,
        session_manager: DatabaseSessionManager | None = None,
        mapper: EstateInventoryRecordMapper | None = None,
    ) -> None:
        """Initialize EstateInventoryRepository."""
        super().__init__(
            mapper=mapper or EstateInventoryRecordMapper(),
            session_manager=session_manager,
        )

    @property
    def table_name(self) -> str:
        """Return target SQLite table name."""
        return "probate_inventories"

    def find_by_decedent(
        self,
        decedent_id: IndividualID | str,
    ) -> list[EstateInventoryRecord]:
        """Find estate inventory records linked to a decedent IndividualID."""
        return self.find_by(decedent_id=normalize_id(decedent_id))

    def find_by_parent_probate_source(
        self,
        parent_probate_source_id: SourceID | str,
    ) -> list[EstateInventoryRecord]:
        """Find estate inventories linked to a parent ProbateRecord SourceID."""
        return self.find_by(parent_probate_source_id=normalize_id(parent_probate_source_id))

    def find_by_court_location(
        self,
        court_location_id: LocationID | str,
    ) -> list[EstateInventoryRecord]:
        """Find estate inventories filed in a court jurisdiction LocationID."""
        return self.find_by(court_location_id=normalize_id(court_location_id))

    def find_by_year_range(
        self,
        start_year: int,
        end_year: int,
    ) -> list[EstateInventoryRecord]:
        """Find estate inventories appraised within an inclusive year range."""
        qb = (
            self.query()
            .where("appraised_year", start_year, FilterOp.GE)
            .where("appraised_year", end_year, FilterOp.LE)
            .order_by("appraised_date_sort", SortOrder.ASC)
            .order_by("id", SortOrder.ASC)
        )
        return self.find_where(qb)
