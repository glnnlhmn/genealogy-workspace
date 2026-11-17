"""Path: src/gda/repository/xref/repository.py

SQLite repositories for Cross-Reference (gda.model.xref) index models.

Operational Role:
    Provides concrete SQLite repositories for all 9 derived XRef bridge tables
    (FactParticipantXRef, IndividualFamilyXRef, IndividualOrganizationXRef,
    IndividualSourceXRef, IndividualSurnameXRef, LocationXRef, MediaXRef,
    SiteXRef, and SurnameXRef).
"""

from __future__ import annotations

from gda.db.mapper.xref import (
    FactParticipantXRefMapper,
    IndividualFamilyXRefMapper,
    IndividualOrganizationXRefMapper,
    IndividualSourceXRefMapper,
    IndividualSurnameXRefMapper,
    LocationXRefMapper,
    MediaXRefMapper,
    SiteXRefMapper,
    SurnameXRefMapper,
)
from gda.db.session import DatabaseSessionManager
from gda.model.atom.id import (
    AtomID,
    FactID,
    FamilyID,
    IndividualID,
    LocationID,
    MediaID,
    OrganizationID,
    SiteID,
    SourceID,
)
from gda.model.xref import (
    FactParticipantXRef,
    IndividualFamilyXRef,
    IndividualOrganizationXRef,
    IndividualSourceXRef,
    IndividualSurnameXRef,
    LocationXRef,
    MediaXRef,
    SiteXRef,
    SurnameXRef,
)
from gda.repository.base import BaseSQLiteRepository
from gda.util.ids import normalize_id
from gda.util.text import clean_string

__version__ = "1.0.0+build.2"

__all__ = [
    "FactParticipantXRefRepository",
    "IndividualFamilyXRefRepository",
    "IndividualOrganizationXRefRepository",
    "IndividualSourceXRefRepository",
    "IndividualSurnameXRefRepository",
    "LocationXRefRepository",
    "MediaXRefRepository",
    "SiteXRefRepository",
    "SurnameXRefRepository",
]


class FactParticipantXRefRepository(BaseSQLiteRepository[FactParticipantXRef, str]):
    """SQLite repository for FactParticipantXRef bridge rows."""

    def __init__(
        self,
        session_manager: DatabaseSessionManager | None = None,
        mapper: FactParticipantXRefMapper | None = None,
    ) -> None:
        """Initialize FactParticipantXRefRepository."""
        super().__init__(
            mapper=mapper or FactParticipantXRefMapper(),
            session_manager=session_manager,
        )

    @property
    def table_name(self) -> str:
        """Return target SQLite table name."""
        return "xref_fact_participants"

    def find_by_fact(
        self,
        fact_id: FactID | str,
    ) -> list[FactParticipantXRef]:
        """Find participant XRef rows for a FactID."""
        return self.find_by(fact_id=normalize_id(fact_id))

    def find_by_individual(
        self,
        individual_id: IndividualID | str,
    ) -> list[FactParticipantXRef]:
        """Find participant XRef rows for an IndividualID."""
        return self.find_by(individual_id=normalize_id(individual_id))


class IndividualFamilyXRefRepository(BaseSQLiteRepository[IndividualFamilyXRef, str]):
    """SQLite repository for IndividualFamilyXRef bridge rows."""

    def __init__(
        self,
        session_manager: DatabaseSessionManager | None = None,
        mapper: IndividualFamilyXRefMapper | None = None,
    ) -> None:
        """Initialize IndividualFamilyXRefRepository."""
        super().__init__(
            mapper=mapper or IndividualFamilyXRefMapper(),
            session_manager=session_manager,
        )

    @property
    def table_name(self) -> str:
        """Return target SQLite table name."""
        return "xref_individual_families"

    def find_by_family(
        self,
        family_id: FamilyID | str,
    ) -> list[IndividualFamilyXRef]:
        """Find family member XRef rows for a FamilyID."""
        return self.find_by(family_id=normalize_id(family_id))

    def find_by_individual(
        self,
        individual_id: IndividualID | str,
    ) -> list[IndividualFamilyXRef]:
        """Find family membership XRef rows for an IndividualID."""
        return self.find_by(individual_id=normalize_id(individual_id))


class IndividualOrganizationXRefRepository(BaseSQLiteRepository[IndividualOrganizationXRef, str]):
    """SQLite repository for IndividualOrganizationXRef bridge rows."""

    def __init__(
        self,
        session_manager: DatabaseSessionManager | None = None,
        mapper: IndividualOrganizationXRefMapper | None = None,
    ) -> None:
        """Initialize IndividualOrganizationXRefRepository."""
        super().__init__(
            mapper=mapper or IndividualOrganizationXRefMapper(),
            session_manager=session_manager,
        )

    @property
    def table_name(self) -> str:
        """Return target SQLite table name."""
        return "xref_individual_organizations"

    def find_by_organization(
        self,
        organization_id: OrganizationID | str,
    ) -> list[IndividualOrganizationXRef]:
        """Find affiliation XRef rows for an OrganizationID."""
        return self.find_by(organization_id=normalize_id(organization_id))

    def find_by_individual(
        self,
        individual_id: IndividualID | str,
    ) -> list[IndividualOrganizationXRef]:
        """Find affiliation XRef rows for an IndividualID."""
        return self.find_by(individual_id=normalize_id(individual_id))


class IndividualSourceXRefRepository(BaseSQLiteRepository[IndividualSourceXRef, str]):
    """SQLite repository for IndividualSourceXRef bridge rows."""

    def __init__(
        self,
        session_manager: DatabaseSessionManager | None = None,
        mapper: IndividualSourceXRefMapper | None = None,
    ) -> None:
        """Initialize IndividualSourceXRefRepository."""
        super().__init__(
            mapper=mapper or IndividualSourceXRefMapper(),
            session_manager=session_manager,
        )

    @property
    def table_name(self) -> str:
        """Return target SQLite table name."""
        return "xref_individual_sources"

    def find_by_source(
        self,
        source_id: SourceID | str,
    ) -> list[IndividualSourceXRef]:
        """Find person XRef rows linked to a SourceID."""
        return self.find_by(source_id=normalize_id(source_id))

    def find_by_individual(
        self,
        individual_id: IndividualID | str,
    ) -> list[IndividualSourceXRef]:
        """Find source XRef rows linked to an IndividualID."""
        return self.find_by(individual_id=normalize_id(individual_id))


class IndividualSurnameXRefRepository(BaseSQLiteRepository[IndividualSurnameXRef, str]):
    """SQLite repository for IndividualSurnameXRef bridge rows."""

    def __init__(
        self,
        session_manager: DatabaseSessionManager | None = None,
        mapper: IndividualSurnameXRefMapper | None = None,
    ) -> None:
        """Initialize IndividualSurnameXRefRepository."""
        super().__init__(
            mapper=mapper or IndividualSurnameXRefMapper(),
            session_manager=session_manager,
        )

    @property
    def table_name(self) -> str:
        """Return target SQLite table name."""
        return "xref_individual_surnames"

    def find_by_surname(self, surname: str) -> list[IndividualSurnameXRef]:
        """Find individual surname XRef rows matching an uppercase surname."""
        return self.find_by(surname=(clean_string(surname) or "").upper())

    def find_by_individual(
        self,
        individual_id: IndividualID | str,
    ) -> list[IndividualSurnameXRef]:
        """Find surname XRef rows for an IndividualID."""
        return self.find_by(individual_id=normalize_id(individual_id))


class LocationXRefRepository(BaseSQLiteRepository[LocationXRef, str]):
    """SQLite repository for LocationXRef bridge rows."""

    def __init__(
        self,
        session_manager: DatabaseSessionManager | None = None,
        mapper: LocationXRefMapper | None = None,
    ) -> None:
        """Initialize LocationXRefRepository."""
        super().__init__(
            mapper=mapper or LocationXRefMapper(),
            session_manager=session_manager,
        )

    @property
    def table_name(self) -> str:
        """Return target SQLite table name."""
        return "xref_locations"

    def find_by_location(
        self,
        location_id: LocationID | str,
    ) -> list[LocationXRef]:
        """Find target XRef rows anchored to a LocationID."""
        return self.find_by(location_id=normalize_id(location_id))

    def find_by_target(
        self,
        target_id: AtomID | SourceID | str,
    ) -> list[LocationXRef]:
        """Find LocationXRef rows for a target entity/source ID."""
        return self.find_by(target_id=normalize_id(target_id))


class MediaXRefRepository(BaseSQLiteRepository[MediaXRef, str]):
    """SQLite repository for MediaXRef bridge rows."""

    def __init__(
        self,
        session_manager: DatabaseSessionManager | None = None,
        mapper: MediaXRefMapper | None = None,
    ) -> None:
        """Initialize MediaXRefRepository."""
        super().__init__(
            mapper=mapper or MediaXRefMapper(),
            session_manager=session_manager,
        )

    @property
    def table_name(self) -> str:
        """Return target SQLite table name."""
        return "xref_media"

    def find_by_media(self, media_id: MediaID | str) -> list[MediaXRef]:
        """Find target XRef rows linked to a MediaID."""
        return self.find_by(media_id=normalize_id(media_id))

    def find_by_target(
        self,
        target_id: AtomID | SourceID | str,
    ) -> list[MediaXRef]:
        """Find MediaXRef rows linked to a target entity/source ID."""
        return self.find_by(target_id=normalize_id(target_id))


class SiteXRefRepository(BaseSQLiteRepository[SiteXRef, str]):
    """SQLite repository for SiteXRef bridge rows."""

    def __init__(
        self,
        session_manager: DatabaseSessionManager | None = None,
        mapper: SiteXRefMapper | None = None,
    ) -> None:
        """Initialize SiteXRefRepository."""
        super().__init__(
            mapper=mapper or SiteXRefMapper(),
            session_manager=session_manager,
        )

    @property
    def table_name(self) -> str:
        """Return target SQLite table name."""
        return "xref_sites"

    def find_by_site(self, site_id: SiteID | str) -> list[SiteXRef]:
        """Find target XRef rows linked to a SiteID."""
        return self.find_by(site_id=normalize_id(site_id))

    def find_by_location(
        self,
        location_id: LocationID | str,
    ) -> list[SiteXRef]:
        """Find SiteXRef rows governed by a LocationID."""
        return self.find_by(location_id=normalize_id(location_id))


class SurnameXRefRepository(BaseSQLiteRepository[SurnameXRef, str]):
    """SQLite repository for SurnameXRef onomastic equivalence rows."""

    def __init__(
        self,
        session_manager: DatabaseSessionManager | None = None,
        mapper: SurnameXRefMapper | None = None,
    ) -> None:
        """Initialize SurnameXRefRepository."""
        super().__init__(
            mapper=mapper or SurnameXRefMapper(),
            session_manager=session_manager,
        )

    @property
    def table_name(self) -> str:
        """Return target SQLite table name."""
        return "xref_surnames"

    def find_by_canonical_surname(
        self,
        canonical_surname: str,
    ) -> list[SurnameXRef]:
        """Find variant surname XRef rows for a canonical surname."""
        return self.find_by(canonical_surname=(clean_string(canonical_surname) or "").upper())

    def find_by_variant_surname(
        self,
        variant_surname: str,
    ) -> list[SurnameXRef]:
        """Find canonical surname XRef rows for a variant spelling."""
        return self.find_by(variant_surname=(clean_string(variant_surname) or "").upper())
