"""Path: src/gda/repository/orgs/repository.py

SQLite repositories for Organization archival source records.

Operational Role:
    Provides concrete CRUD and domain-specialized analytical repositories for
    OrganizationMembershipRecord (lodge/congregation membership records) and
    OrganizationRosterRecord (enumerated organizational rosters).
"""

from __future__ import annotations

from gda.db.mapper.education_manuscripts_orgs_other import (
    OrganizationMembershipRecordMapper,
    OrganizationRosterRecordMapper,
)
from gda.db.session import DatabaseSessionManager
from gda.model.atom.id import IndividualID, LocationID, OrganizationID, SourceID
from gda.model.source.orgs.membership import OrganizationMembershipRecord
from gda.model.source.orgs.roster import OrganizationRosterRecord
from gda.repository.base import BaseSQLiteRepository
from gda.util.ids import normalize_id

__version__ = "1.0.0+build.2"

__all__ = [
    "OrganizationMembershipRepository",
    "OrganizationRosterRepository",
]


class OrganizationMembershipRepository(
    BaseSQLiteRepository[OrganizationMembershipRecord, SourceID]
):
    """SQLite repository for organization membership and lodge ledger records."""

    def __init__(
        self,
        session_manager: DatabaseSessionManager | None = None,
        mapper: OrganizationMembershipRecordMapper | None = None,
    ) -> None:
        """Initialize OrganizationMembershipRepository."""
        super().__init__(
            mapper=mapper or OrganizationMembershipRecordMapper(),
            session_manager=session_manager,
        )

    @property
    def table_name(self) -> str:
        """Return target SQLite table name."""
        return "orgs_memberships"

    def find_by_individual(
        self,
        individual_id: IndividualID | str,
    ) -> list[OrganizationMembershipRecord]:
        """Find organization membership records for an IndividualID."""
        return self.find_by(individual_id=normalize_id(individual_id))

    def find_by_organization(
        self,
        org_id: OrganizationID | str,
    ) -> list[OrganizationMembershipRecord]:
        """Find organization membership records linked to an OrganizationID."""
        return self.find_by(org_id=normalize_id(org_id))


class OrganizationRosterRepository(BaseSQLiteRepository[OrganizationRosterRecord, SourceID]):
    """SQLite repository for enumerated organizational and fraternal rosters."""

    def __init__(
        self,
        session_manager: DatabaseSessionManager | None = None,
        mapper: OrganizationRosterRecordMapper | None = None,
    ) -> None:
        """Initialize OrganizationRosterRepository."""
        super().__init__(
            mapper=mapper or OrganizationRosterRecordMapper(),
            session_manager=session_manager,
        )

    @property
    def table_name(self) -> str:
        """Return target SQLite table name."""
        return "orgs_rosters"

    def find_by_organization(
        self,
        org_id: OrganizationID | str,
    ) -> list[OrganizationRosterRecord]:
        """Find organization roster records linked to an OrganizationID."""
        return self.find_by(org_id=normalize_id(org_id))

    def find_by_jurisdiction(
        self,
        jurisdiction_id: LocationID | str,
    ) -> list[OrganizationRosterRecord]:
        """Find organization roster records linked to a jurisdiction LocationID."""
        return self.find_by(jurisdiction_id=normalize_id(jurisdiction_id))

    def find_by_year(
        self,
        enumeration_year: int,
    ) -> list[OrganizationRosterRecord]:
        """Find organization roster records for a specific enumeration year."""
        return self.find_by(enumeration_year=enumeration_year)
