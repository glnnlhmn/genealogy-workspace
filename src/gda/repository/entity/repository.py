"""Path: src/gda/repository/entity/repository.py

SQLite repositories for the 6 core GDA entities (gda.model.entity).

Operational Role:
    Provides concrete BaseSQLiteRepository implementations for Location, Site,
    Organization, Individual, Family, and Fact using the canonical row mappers
    in gda.db.mapper.
"""

from __future__ import annotations

from gda.db.mapper.facts import FactRowMapper
from gda.db.mapper.organizations import OrganizationRowMapper
from gda.db.mapper.personas import FamilyRowMapper, IndividualRowMapper
from gda.db.mapper.places import LocationRowMapper, SiteRowMapper
from gda.db.session import DatabaseSessionManager
from gda.model.atom.id import (
    FactID,
    FamilyID,
    IndividualID,
    LocationID,
    OrganizationID,
    SiteID,
)
from gda.model.entity.fact import Fact
from gda.model.entity.family import Family
from gda.model.entity.individual import Individual
from gda.model.entity.location import Location
from gda.model.entity.organization import Organization
from gda.model.entity.site import Site
from gda.repository.base import BaseSQLiteRepository
from gda.util.ids import normalize_id
from gda.util.text import clean_string

__version__ = "1.0.0+build.2"

__all__ = [
    "FactRepository",
    "FamilyRepository",
    "IndividualRepository",
    "LocationRepository",
    "OrganizationRepository",
    "SiteRepository",
]


class LocationRepository(BaseSQLiteRepository[Location, LocationID]):
    """SQLite repository for Location (civil jurisdiction) entities."""

    def __init__(
        self,
        session_manager: DatabaseSessionManager | None = None,
        mapper: LocationRowMapper | None = None,
    ) -> None:
        """Initialize LocationRepository."""
        super().__init__(
            mapper=mapper or LocationRowMapper(),
            session_manager=session_manager,
        )

    @property
    def table_name(self) -> str:
        """Return target SQLite table name."""
        return "locations"

    def find_by_parent(
        self,
        parent_id: LocationID | str,
    ) -> list[Location]:
        """Find child jurisdictions governed by a parent LocationID."""
        return self.find_by(parent_id=normalize_id(parent_id))

    def find_by_category(self, category: str) -> list[Location]:
        """Find locations matching a JurisdictionCategory value."""
        return self.find_by(category=clean_string(category) or category)


class SiteRepository(BaseSQLiteRepository[Site, SiteID]):
    """SQLite repository for Site (physical venue/cemetery/church) entities."""

    def __init__(
        self,
        session_manager: DatabaseSessionManager | None = None,
        mapper: SiteRowMapper | None = None,
    ) -> None:
        """Initialize SiteRepository."""
        super().__init__(
            mapper=mapper or SiteRowMapper(),
            session_manager=session_manager,
        )

    @property
    def table_name(self) -> str:
        """Return target SQLite table name."""
        return "sites"

    def find_by_location(
        self,
        location_id: LocationID | str,
    ) -> list[Site]:
        """Find physical sites located within a civil jurisdiction LocationID."""
        return self.find_by(location_id=normalize_id(location_id))

    def find_by_category(self, category: str) -> list[Site]:
        """Find physical sites matching a SiteType value."""
        return self.find_by(category=clean_string(category) or category)


class OrganizationRepository(BaseSQLiteRepository[Organization, OrganizationID]):
    """SQLite repository for Organization entities."""

    def __init__(
        self,
        session_manager: DatabaseSessionManager | None = None,
        mapper: OrganizationRowMapper | None = None,
    ) -> None:
        """Initialize OrganizationRepository."""
        super().__init__(
            mapper=mapper or OrganizationRowMapper(),
            session_manager=session_manager,
        )

    @property
    def table_name(self) -> str:
        """Return target SQLite table name."""
        return "organizations"

    def find_by_location(
        self,
        location_id: LocationID | str,
    ) -> list[Organization]:
        """Find organizations operating within a civil jurisdiction LocationID."""
        return self.find_by(location_id=normalize_id(location_id))

    def find_by_category(self, category: str) -> list[Organization]:
        """Find organizations matching an OrganizationCategory value."""
        return self.find_by(category=clean_string(category) or category)


class IndividualRepository(BaseSQLiteRepository[Individual, IndividualID]):
    """SQLite repository for Individual persona entities."""

    def __init__(
        self,
        session_manager: DatabaseSessionManager | None = None,
        mapper: IndividualRowMapper | None = None,
    ) -> None:
        """Initialize IndividualRepository."""
        super().__init__(
            mapper=mapper or IndividualRowMapper(),
            session_manager=session_manager,
        )

    @property
    def table_name(self) -> str:
        """Return target SQLite table name."""
        return "individuals"

    def find_by_surname(self, surname: str) -> list[Individual]:
        """Find individuals matching a primary birth surname."""
        return self.find_by(surname=clean_string(surname) or surname)


class FamilyRepository(BaseSQLiteRepository[Family, FamilyID]):
    """SQLite repository for nuclear Family entities."""

    def __init__(
        self,
        session_manager: DatabaseSessionManager | None = None,
        mapper: FamilyRowMapper | None = None,
    ) -> None:
        """Initialize FamilyRepository."""
        super().__init__(
            mapper=mapper or FamilyRowMapper(),
            session_manager=session_manager,
        )

    @property
    def table_name(self) -> str:
        """Return target SQLite table name."""
        return "families"

    def find_by_union_type(self, union_type: str) -> list[Family]:
        """Find nuclear families matching a UnionType value."""
        return self.find_by(union_type=clean_string(union_type) or union_type)


class FactRepository(BaseSQLiteRepository[Fact, FactID]):
    """SQLite repository for evidentiary Fact entities."""

    def __init__(
        self,
        session_manager: DatabaseSessionManager | None = None,
        mapper: FactRowMapper | None = None,
    ) -> None:
        """Initialize FactRepository."""
        super().__init__(
            mapper=mapper or FactRowMapper(),
            session_manager=session_manager,
        )

    @property
    def table_name(self) -> str:
        """Return target SQLite table name."""
        return "facts"

    def find_by_primary_subject(
        self,
        subject_id: IndividualID | FamilyID | str,
    ) -> list[Fact]:
        """Find facts asserted about a primary IndividualID or FamilyID."""
        return self.find_by(primary_subject_id=normalize_id(subject_id))

    def find_by_fact_type(self, fact_type: str) -> list[Fact]:
        """Find facts matching a FactType value."""
        return self.find_by(fact_type=clean_string(fact_type) or fact_type)
