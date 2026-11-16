"""Path: src/gda/repository/other/repository.py

SQLite repository for Other Miscellaneous archival source records.

Operational Role:
    Provides concrete CRUD and domain-specialized analytical queries for
    OtherMiscellaneousRecord (receipts, ephemera, unclassified archival items).
"""

from __future__ import annotations

from gda.db.mapper.education_manuscripts_orgs_other import (
    OtherMiscellaneousRecordMapper,
)
from gda.db.session import DatabaseSessionManager
from gda.model.atom.id import LocationID, SourceID
from gda.model.source.other.miscellaneous import OtherMiscellaneousRecord
from gda.repository.base import BaseSQLiteRepository, _normalize_id
from gda.repository.query import FilterOp, SortOrder

__version__ = "1.0.0+build.1"

__all__ = [
    "OtherMiscellaneousRepository",
]


class OtherMiscellaneousRepository(BaseSQLiteRepository[OtherMiscellaneousRecord, SourceID]):
    """SQLite repository for miscellaneous archival records and ephemera."""

    def __init__(
        self,
        session_manager: DatabaseSessionManager | None = None,
        mapper: OtherMiscellaneousRecordMapper | None = None,
    ) -> None:
        """Initialize OtherMiscellaneousRepository."""
        super().__init__(
            mapper=mapper or OtherMiscellaneousRecordMapper(),
            session_manager=session_manager,
        )

    @property
    def table_name(self) -> str:
        """Return target SQLite table name."""
        return "other_miscellaneous_records"

    def find_by_organization_location(
        self,
        location_id: LocationID | str,
    ) -> list[OtherMiscellaneousRecord]:
        """Find miscellaneous records linked to an organization/origin LocationID."""
        return self.find_by(organization_location_id=_normalize_id(location_id))

    def find_by_item_year_range(
        self,
        start_year: int,
        end_year: int,
    ) -> list[OtherMiscellaneousRecord]:
        """Find miscellaneous records dated within an inclusive year range."""
        qb = (
            self.query()
            .where("item_year", start_year, FilterOp.GE)
            .where("item_year", end_year, FilterOp.LE)
            .order_by("item_date_sort", SortOrder.ASC)
            .order_by("id", SortOrder.ASC)
        )
        return self.find_where(qb)
