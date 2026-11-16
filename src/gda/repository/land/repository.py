"""Path: src/gda/repository/land/repository.py

SQLite repositories for Land archival source records.

Operational Role:
    Provides concrete CRUD and domain-specialized analytical repositories for
    LandDeedRecord (deeds, indentures, mortgages) and LandGrantRecord
    (warrants, surveys, patents).
"""

from __future__ import annotations

from gda.db.mapper.probate_land import (
    LandDeedRecordMapper,
    LandGrantRecordMapper,
)
from gda.db.session import DatabaseSessionManager
from gda.model.atom.id import IndividualID, LocationID, SourceID
from gda.model.source.land.deed import LandDeedRecord
from gda.model.source.land.grant import LandGrantRecord
from gda.repository.base import BaseSQLiteRepository, _normalize_id
from gda.repository.query import FilterOp, SortOrder

__version__ = "1.0.0+build.1"

__all__ = [
    "LandDeedRepository",
    "LandGrantRepository",
]


class LandDeedRepository(BaseSQLiteRepository[LandDeedRecord, SourceID]):
    """SQLite repository for land deeds, indentures, and conveyances."""

    def __init__(
        self,
        session_manager: DatabaseSessionManager | None = None,
        mapper: LandDeedRecordMapper | None = None,
    ) -> None:
        """Initialize LandDeedRepository."""
        super().__init__(
            mapper=mapper or LandDeedRecordMapper(),
            session_manager=session_manager,
        )

    @property
    def table_name(self) -> str:
        """Return target SQLite table name."""
        return "land_deeds"

    def find_by_grantor(
        self,
        grantor_id: IndividualID | str,
    ) -> list[LandDeedRecord]:
        """Find deeds where the primary grantor matches IndividualID."""
        return self.find_by(primary_grantor_id=_normalize_id(grantor_id))

    def find_by_grantee(
        self,
        grantee_id: IndividualID | str,
    ) -> list[LandDeedRecord]:
        """Find deeds where the primary grantee matches IndividualID."""
        return self.find_by(primary_grantee_id=_normalize_id(grantee_id))

    def find_by_parcel_location(
        self,
        location_id: LocationID | str,
    ) -> list[LandDeedRecord]:
        """Find deeds conveying parcels within a specific LocationID."""
        return self.find_by(parcel_location_id=_normalize_id(location_id))

    def find_by_written_year_range(
        self,
        start_year: int,
        end_year: int,
    ) -> list[LandDeedRecord]:
        """Find deeds executed within an inclusive written year range."""
        qb = (
            self.query()
            .where("written_year", start_year, FilterOp.GE)
            .where("written_year", end_year, FilterOp.LE)
            .order_by("written_date_sort", SortOrder.ASC)
            .order_by("id", SortOrder.ASC)
        )
        return self.find_where(qb)


class LandGrantRepository(BaseSQLiteRepository[LandGrantRecord, SourceID]):
    """SQLite repository for land warrants, surveys, and patents."""

    def __init__(
        self,
        session_manager: DatabaseSessionManager | None = None,
        mapper: LandGrantRecordMapper | None = None,
    ) -> None:
        """Initialize LandGrantRepository."""
        super().__init__(
            mapper=mapper or LandGrantRecordMapper(),
            session_manager=session_manager,
        )

    @property
    def table_name(self) -> str:
        """Return target SQLite table name."""
        return "land_grants"

    def find_by_patentee(
        self,
        patentee_id: IndividualID | str,
    ) -> list[LandGrantRecord]:
        """Find land grants linked to a patentee or warrantee IndividualID."""
        return self.find_by(patentee_id=_normalize_id(patentee_id))

    def find_by_assignee(
        self,
        assignee_id: IndividualID | str,
    ) -> list[LandGrantRecord]:
        """Find land grants linked to an assignee IndividualID."""
        return self.find_by(assignee_id=_normalize_id(assignee_id))

    def find_by_parcel_location(
        self,
        location_id: LocationID | str,
    ) -> list[LandGrantRecord]:
        """Find land grants located within a specific parcel LocationID."""
        return self.find_by(parcel_location_id=_normalize_id(location_id))

    def find_by_patented_year_range(
        self,
        start_year: int,
        end_year: int,
    ) -> list[LandGrantRecord]:
        """Find land grants patented within an inclusive year range."""
        qb = (
            self.query()
            .where("patented_year", start_year, FilterOp.GE)
            .where("patented_year", end_year, FilterOp.LE)
            .order_by("patented_date_sort", SortOrder.ASC)
            .order_by("id", SortOrder.ASC)
        )
        return self.find_where(qb)
