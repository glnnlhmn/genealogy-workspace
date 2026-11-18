"""Path: src/gda/repository/education/repository.py

SQLite repository for Education archival source records.

Operational Role:
    Provides concrete CRUD and domain-specialized analytical queries for
    AcademicCredentialRecord (diplomas, certificates, rosters, yearbooks).
"""

from __future__ import annotations

from gda.db.mapper.education_manuscripts_orgs_other import (
    AcademicCredentialRecordMapper,
)
from gda.db.session import DatabaseSessionManager
from gda.model.atom.id import IndividualID, LocationID, SourceID
from gda.model.source.education.credential import AcademicCredentialRecord
from gda.repository.base import BaseSQLiteRepository
from gda.repository.query import FilterOp, SortOrder
from gda.util.ids import normalize_id

__version__ = "1.0.0+build.2"

__all__ = [
    "AcademicCredentialRepository",
]


class AcademicCredentialRepository(BaseSQLiteRepository[AcademicCredentialRecord, SourceID]):
    """SQLite repository for academic credentials, diplomas, and yearbooks."""

    def __init__(
        self,
        session_manager: DatabaseSessionManager | None = None,
        mapper: AcademicCredentialRecordMapper | None = None,
    ) -> None:
        """Initialize AcademicCredentialRepository."""
        super().__init__(
            mapper=mapper or AcademicCredentialRecordMapper(),
            session_manager=session_manager,
        )

    @property
    def table_name(self) -> str:
        """Return target SQLite table name."""
        return "education_credentials"

    def find_by_subject(
        self,
        subject_id: IndividualID | str,
    ) -> list[AcademicCredentialRecord]:
        """Find academic credentials linked to a student/graduate IndividualID."""
        return self.find_by(subject_id=normalize_id(subject_id))

    def find_by_institution_location(
        self,
        location_id: LocationID | str,
    ) -> list[AcademicCredentialRecord]:
        """Find academic credentials linked to an institution LocationID."""
        return self.find_by(institution_location_id=normalize_id(location_id))

    def find_by_graduation_year(
        self,
        graduation_year: int,
    ) -> list[AcademicCredentialRecord]:
        """Find academic credentials matching a specific graduation year."""
        return self.find_by(graduation_year=graduation_year)

    def find_by_issued_year_range(
        self,
        start_year: int,
        end_year: int,
    ) -> list[AcademicCredentialRecord]:
        """Find academic credentials issued within an inclusive year range."""
        qb = (
            self.query()
            .where("issued_year", start_year, FilterOp.GE)
            .where("issued_year", end_year, FilterOp.LE)
            .order_by("issued_date_sort", SortOrder.ASC)
            .order_by("id", SortOrder.ASC)
        )
        return self.find_where(qb)
