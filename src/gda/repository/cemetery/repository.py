"""Path: src/gda/repository/cemetery/repository.py

SQLite repositories for Cemetery archival source records.

Operational Role:
    Provides concrete CRUD and domain-specialized analytical repositories for
    CemeteryMarkerRecord and CemeteryRegistryRecord backed by dedicated SQLite
    tables (cemetery_markers and cemetery_registries).
"""

from __future__ import annotations

from gda.db.mapper.vital_cemetery import (
    CemeteryMarkerRecordMapper,
    CemeteryRegistryRecordMapper,
)
from gda.db.session import DatabaseSessionManager
from gda.model.atom.id import LocationID, SiteID, SourceID
from gda.model.source.cemetery.marker import CemeteryMarkerRecord
from gda.model.source.cemetery.registry import CemeteryRegistryRecord
from gda.repository.base import BaseSQLiteRepository, _normalize_id

__version__ = "1.0.0+build.1"

__all__ = [
    "CemeteryMarkerRepository",
    "CemeteryRegistryRepository",
]


class CemeteryMarkerRepository(BaseSQLiteRepository[CemeteryMarkerRecord, SourceID]):
    """SQLite repository for grave marker and headstone survey records."""

    def __init__(
        self,
        session_manager: DatabaseSessionManager | None = None,
        mapper: CemeteryMarkerRecordMapper | None = None,
    ) -> None:
        """Initialize CemeteryMarkerRepository."""
        super().__init__(
            mapper=mapper or CemeteryMarkerRecordMapper(),
            session_manager=session_manager,
        )

    @property
    def table_name(self) -> str:
        """Return target SQLite table name."""
        return "cemetery_markers"

    def find_by_cemetery_site(
        self,
        cemetery_site_id: SiteID | str,
    ) -> list[CemeteryMarkerRecord]:
        """Find marker records located at a specific cemetery SiteID."""
        return self.find_by(cemetery_site_id=_normalize_id(cemetery_site_id))

    def find_by_location(
        self,
        location_id: LocationID | str,
    ) -> list[CemeteryMarkerRecord]:
        """Find marker records associated with a geographic LocationID."""
        return self.find_by(location_id=_normalize_id(location_id))

    def find_by_findagrave_id(self, findagrave_id: str) -> list[CemeteryMarkerRecord]:
        """Find marker records matching an external Find A Grave memorial ID."""
        return self.find_by(findagrave_id=findagrave_id)


class CemeteryRegistryRepository(BaseSQLiteRepository[CemeteryRegistryRecord, SourceID]):
    """SQLite repository for sexton books and cemetery plot registries."""

    def __init__(
        self,
        session_manager: DatabaseSessionManager | None = None,
        mapper: CemeteryRegistryRecordMapper | None = None,
    ) -> None:
        """Initialize CemeteryRegistryRepository."""
        super().__init__(
            mapper=mapper or CemeteryRegistryRecordMapper(),
            session_manager=session_manager,
        )

    @property
    def table_name(self) -> str:
        """Return target SQLite table name."""
        return "cemetery_registries"

    def find_by_cemetery_site(
        self,
        cemetery_site_id: SiteID | str,
    ) -> list[CemeteryRegistryRecord]:
        """Find plot registry records for a specific cemetery SiteID."""
        return self.find_by(cemetery_site_id=_normalize_id(cemetery_site_id))

    def find_by_location(
        self,
        location_id: LocationID | str,
    ) -> list[CemeteryRegistryRecord]:
        """Find plot registry records associated with a geographic LocationID."""
        return self.find_by(location_id=_normalize_id(location_id))
