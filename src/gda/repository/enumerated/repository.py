"""Path: src/gda/repository/enumerated/repository.py

SQLite repositories for Enumerated archival source records.

Operational Role:
    Provides concrete CRUD and domain-specialized analytical repositories for
    decennial population census schedules, supplemental schedules (agricultural,
    manufacturing, mortality, slave, 1890 veterans), city/civic directories,
    and tax/septennial rolls.
"""

from __future__ import annotations

from typing import Any

from gda.db.mapper.enumerated_publications import (
    DirectoryRollRecordMapper,
    PopulationScheduleMapper,
    SupplementalScheduleMapper,
    TaxAssessmentRecordMapper,
)
from gda.db.session import DatabaseSessionManager
from gda.model.atom.id import IndividualID, LocationID, SourceID
from gda.model.source.enumerated import (
    CensusScheduleRecord,
    DirectoryRollRecord,
    PopulationScheduleRecord,
    TaxAssessmentRecord,
)
from gda.repository.base import BaseSQLiteRepository, _normalize_id

__version__ = "1.0.0+build.1"

__all__ = [
    "DirectoryRollRepository",
    "PopulationScheduleRepository",
    "SupplementalScheduleRepository",
    "TaxAssessmentRepository",
]


class PopulationScheduleRepository(BaseSQLiteRepository[PopulationScheduleRecord[Any], SourceID]):
    """SQLite repository for decennial US population census schedules (1790-1950)."""

    def __init__(
        self,
        session_manager: DatabaseSessionManager | None = None,
        mapper: PopulationScheduleMapper | None = None,
    ) -> None:
        """Initialize PopulationScheduleRepository."""
        super().__init__(
            mapper=mapper or PopulationScheduleMapper(),
            session_manager=session_manager,
        )

    @property
    def table_name(self) -> str:
        """Return target SQLite table name."""
        return "enumerated_population_schedules"

    def find_by_year(self, enumeration_year: int) -> list[PopulationScheduleRecord[Any]]:
        """Find population schedules for a specific decennial census year."""
        return self.find_by(enumeration_year=enumeration_year)

    def find_by_jurisdiction(
        self,
        jurisdiction_id: LocationID | str,
    ) -> list[PopulationScheduleRecord[Any]]:
        """Find population schedules linked to a resolved jurisdiction LocationID."""
        return self.find_by(jurisdiction_id=_normalize_id(jurisdiction_id))

    def find_by_state_and_county(
        self,
        state: str,
        county: str,
    ) -> list[PopulationScheduleRecord[Any]]:
        """Find population schedules matching state and county names."""
        return self.find_by(state=state, county=county)


class SupplementalScheduleRepository(BaseSQLiteRepository[CensusScheduleRecord[Any], SourceID]):
    """SQLite repository for non-population and supplemental census schedules."""

    def __init__(
        self,
        session_manager: DatabaseSessionManager | None = None,
        mapper: SupplementalScheduleMapper | None = None,
    ) -> None:
        """Initialize SupplementalScheduleRepository."""
        super().__init__(
            mapper=mapper or SupplementalScheduleMapper(),
            session_manager=session_manager,
        )

    @property
    def table_name(self) -> str:
        """Return target SQLite table name."""
        return "enumerated_supplemental_schedules"

    def find_by_year(self, enumeration_year: int) -> list[CensusScheduleRecord[Any]]:
        """Find supplemental schedules for a specific enumeration year."""
        return self.find_by(enumeration_year=enumeration_year)

    def find_by_schedule_class(
        self,
        schedule_class: str,
    ) -> list[CensusScheduleRecord[Any]]:
        """Find supplemental schedules by concrete model class name."""
        return self.find_by(schedule_class=schedule_class)

    def find_by_jurisdiction(
        self,
        jurisdiction_id: LocationID | str,
    ) -> list[CensusScheduleRecord[Any]]:
        """Find supplemental schedules linked to a jurisdiction LocationID."""
        return self.find_by(jurisdiction_id=_normalize_id(jurisdiction_id))


class DirectoryRollRepository(BaseSQLiteRepository[DirectoryRollRecord, SourceID]):
    """SQLite repository for city, business, telephone, and civic directories."""

    def __init__(
        self,
        session_manager: DatabaseSessionManager | None = None,
        mapper: DirectoryRollRecordMapper | None = None,
    ) -> None:
        """Initialize DirectoryRollRepository."""
        super().__init__(
            mapper=mapper or DirectoryRollRecordMapper(),
            session_manager=session_manager,
        )

    @property
    def table_name(self) -> str:
        """Return target SQLite table name."""
        return "enumerated_directories"

    def find_by_year(self, enumeration_year: int) -> list[DirectoryRollRecord]:
        """Find directory pages for a specific publication/enumeration year."""
        return self.find_by(enumeration_year=enumeration_year)

    def find_by_jurisdiction(
        self,
        jurisdiction_id: LocationID | str,
    ) -> list[DirectoryRollRecord]:
        """Find directory pages linked to a jurisdiction LocationID."""
        return self.find_by(jurisdiction_id=_normalize_id(jurisdiction_id))

    def find_by_publication_title(
        self,
        publication_title_raw: str,
    ) -> list[DirectoryRollRecord]:
        """Find directory pages matching a verbatim publication title."""
        return self.find_by(publication_title_raw=publication_title_raw)


class TaxAssessmentRepository(BaseSQLiteRepository[TaxAssessmentRecord, SourceID]):
    """SQLite repository for tax assessments and PA Septennial census rolls."""

    def __init__(
        self,
        session_manager: DatabaseSessionManager | None = None,
        mapper: TaxAssessmentRecordMapper | None = None,
    ) -> None:
        """Initialize TaxAssessmentRepository."""
        super().__init__(
            mapper=mapper or TaxAssessmentRecordMapper(),
            session_manager=session_manager,
        )

    @property
    def table_name(self) -> str:
        """Return target SQLite table name."""
        return "enumerated_tax_assessments"

    def find_by_year(self, enumeration_year: int) -> list[TaxAssessmentRecord]:
        """Find tax assessment records for a specific assessment year."""
        return self.find_by(enumeration_year=enumeration_year)

    def find_by_taxpayer(
        self,
        taxpayer_id: IndividualID | str,
    ) -> list[TaxAssessmentRecord]:
        """Find tax assessment records linked to a specific taxpayer IndividualID."""
        return self.find_by(taxpayer_id=_normalize_id(taxpayer_id))

    def find_by_jurisdiction(
        self,
        jurisdiction_id: LocationID | str,
    ) -> list[TaxAssessmentRecord]:
        """Find tax assessment records linked to a jurisdiction LocationID."""
        return self.find_by(jurisdiction_id=_normalize_id(jurisdiction_id))
