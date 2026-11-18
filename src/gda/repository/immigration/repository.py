"""Path: src/gda/repository/immigration/repository.py

SQLite repositories for Immigration archival source records.

Operational Role:
    Provides concrete CRUD and domain-specialized analytical repositories for
    ImmigrationManifestRecord (passenger manifests, crew lists, border crossings)
    and NaturalizationRecord (declarations, petitions, oaths, certificates).
"""

from __future__ import annotations

from gda.db.mapper.immigration_military import (
    ImmigrationManifestRecordMapper,
    NaturalizationRecordMapper,
)
from gda.db.session import DatabaseSessionManager
from gda.model.atom.id import IndividualID, LocationID, SourceID
from gda.model.source.immigration.manifest import ImmigrationManifestRecord
from gda.model.source.immigration.naturalization import NaturalizationRecord
from gda.repository.base import BaseSQLiteRepository
from gda.repository.query import FilterOp, SortOrder
from gda.util.ids import normalize_id

__version__ = "1.0.0+build.2"

__all__ = [
    "ImmigrationManifestRepository",
    "NaturalizationRepository",
]


class ImmigrationManifestRepository(BaseSQLiteRepository[ImmigrationManifestRecord, SourceID]):
    """SQLite repository for passenger arrival manifests and border crossings."""

    def __init__(
        self,
        session_manager: DatabaseSessionManager | None = None,
        mapper: ImmigrationManifestRecordMapper | None = None,
    ) -> None:
        """Initialize ImmigrationManifestRepository."""
        super().__init__(
            mapper=mapper or ImmigrationManifestRecordMapper(),
            session_manager=session_manager,
        )

    @property
    def table_name(self) -> str:
        """Return target SQLite table name."""
        return "immigration_manifests"

    def find_by_port_of_arrival(
        self,
        port_of_arrival_id: LocationID | str,
    ) -> list[ImmigrationManifestRecord]:
        """Find manifests arriving at a specific port LocationID."""
        return self.find_by(port_of_arrival_id=normalize_id(port_of_arrival_id))

    def find_by_ship_name(
        self,
        ship_name: str,
    ) -> list[ImmigrationManifestRecord]:
        """Find manifests matching a vessel or steamship name."""
        return self.find_by(ship_name=ship_name)

    def find_by_arrival_year_range(
        self,
        start_year: int,
        end_year: int,
    ) -> list[ImmigrationManifestRecord]:
        """Find manifests arriving within an inclusive calendar year range."""
        qb = (
            self.query()
            .where("arrival_year", start_year, FilterOp.GE)
            .where("arrival_year", end_year, FilterOp.LE)
            .order_by("arrival_date_sort", SortOrder.ASC)
            .order_by("id", SortOrder.ASC)
        )
        return self.find_where(qb)


class NaturalizationRepository(BaseSQLiteRepository[NaturalizationRecord, SourceID]):
    """SQLite repository for declarations, petitions, and certificates of citizenship."""

    def __init__(
        self,
        session_manager: DatabaseSessionManager | None = None,
        mapper: NaturalizationRecordMapper | None = None,
    ) -> None:
        """Initialize NaturalizationRepository."""
        super().__init__(
            mapper=mapper or NaturalizationRecordMapper(),
            session_manager=session_manager,
        )

    @property
    def table_name(self) -> str:
        """Return target SQLite table name."""
        return "immigration_naturalizations"

    def find_by_applicant(
        self,
        applicant_id: IndividualID | str,
    ) -> list[NaturalizationRecord]:
        """Find naturalization records linked to an applicant IndividualID."""
        return self.find_by(applicant_id=normalize_id(applicant_id))

    def find_by_court_location(
        self,
        court_location_id: LocationID | str,
    ) -> list[NaturalizationRecord]:
        """Find naturalization records filed in a court jurisdiction LocationID."""
        return self.find_by(court_location_id=normalize_id(court_location_id))

    def find_by_event_year_range(
        self,
        start_year: int,
        end_year: int,
    ) -> list[NaturalizationRecord]:
        """Find naturalization records executed within an inclusive year range."""
        qb = (
            self.query()
            .where("event_year", start_year, FilterOp.GE)
            .where("event_year", end_year, FilterOp.LE)
            .order_by("event_date_sort", SortOrder.ASC)
            .order_by("id", SortOrder.ASC)
        )
        return self.find_where(qb)
