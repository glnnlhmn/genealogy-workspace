"""Path: src/gda/repository/vital/repository.py

SQLite repositories for Vital archival source records.

Operational Role:
    Provides concrete CRUD and domain-specialized analytical repositories for
    BaptismRecord, BirthRecord, DeathRecord, DivorceRecord, and MarriageRecord
    backed by dedicated SQLite tables (vital_baptisms, vital_births, vital_deaths,
    vital_divorces, vital_marriages).
"""

from __future__ import annotations

from gda.db.mapper.vital_cemetery import (
    BaptismRecordMapper,
    BirthRecordMapper,
    DeathRecordMapper,
    DivorceRecordMapper,
    MarriageRecordMapper,
)
from gda.db.session import DatabaseSessionManager
from gda.model.atom.id import IndividualID, LocationID, OrganizationID, SiteID, SourceID
from gda.model.source.vital.baptism import BaptismRecord
from gda.model.source.vital.birth import BirthRecord
from gda.model.source.vital.death import DeathRecord
from gda.model.source.vital.divorce import DivorceRecord
from gda.model.source.vital.marriage import MarriageRecord
from gda.repository.base import BaseSQLiteRepository, _normalize_id
from gda.repository.query import FilterOp, SortOrder

__version__ = "1.0.0+build.1"

__all__ = [
    "BaptismRepository",
    "BirthRepository",
    "DeathRepository",
    "DivorceRepository",
    "MarriageRepository",
]


class BaptismRepository(BaseSQLiteRepository[BaptismRecord, SourceID]):
    """SQLite repository for ecclesiastical BaptismRecord sources."""

    def __init__(
        self,
        session_manager: DatabaseSessionManager | None = None,
        mapper: BaptismRecordMapper | None = None,
    ) -> None:
        """Initialize BaptismRepository."""
        super().__init__(
            mapper=mapper or BaptismRecordMapper(),
            session_manager=session_manager,
        )

    @property
    def table_name(self) -> str:
        """Return target SQLite table name."""
        return "vital_baptisms"

    def find_by_individual(self, individual_id: IndividualID | str) -> list[BaptismRecord]:
        """Find baptism records linked to a specific baptized individual."""
        return self.find_by(individual_id=_normalize_id(individual_id))

    def find_by_church_org(self, church_org_id: OrganizationID | str) -> list[BaptismRecord]:
        """Find baptism records linked to an ecclesiastical organization."""
        return self.find_by(church_org_id=_normalize_id(church_org_id))

    def find_by_church_site(self, church_site_id: SiteID | str) -> list[BaptismRecord]:
        """Find baptism records linked to a church site."""
        return self.find_by(church_site_id=_normalize_id(church_site_id))

    def find_by_location(self, location_id: LocationID | str) -> list[BaptismRecord]:
        """Find baptism records occurring in a specific geographic location."""
        return self.find_by(location_id=_normalize_id(location_id))

    def find_by_year_range(self, start_year: int, end_year: int) -> list[BaptismRecord]:
        """Find baptism records within an inclusive baptism year range."""
        qb = (
            self.query()
            .where("baptism_year", start_year, FilterOp.GE)
            .where("baptism_year", end_year, FilterOp.LE)
            .order_by("baptism_date_sort", SortOrder.ASC)
            .order_by("id", SortOrder.ASC)
        )
        return self.find_where(qb)


class BirthRepository(BaseSQLiteRepository[BirthRecord, SourceID]):
    """SQLite repository for civil and archival BirthRecord sources."""

    def __init__(
        self,
        session_manager: DatabaseSessionManager | None = None,
        mapper: BirthRecordMapper | None = None,
    ) -> None:
        """Initialize BirthRepository."""
        super().__init__(
            mapper=mapper or BirthRecordMapper(),
            session_manager=session_manager,
        )

    @property
    def table_name(self) -> str:
        """Return target SQLite table name."""
        return "vital_births"

    def find_by_child(self, child_id: IndividualID | str) -> list[BirthRecord]:
        """Find birth records linked to a specific child individual ID."""
        return self.find_by(child_id=_normalize_id(child_id))

    def find_by_location(self, location_id: LocationID | str) -> list[BirthRecord]:
        """Find birth records linked to a place_of_birth_id."""
        return self.find_by(place_of_birth_id=_normalize_id(location_id))

    def find_by_certificate_number(self, certificate_number: str) -> list[BirthRecord]:
        """Find birth records matching a civil certificate number."""
        return self.find_by(certificate_number=certificate_number)

    def find_by_year_range(self, start_year: int, end_year: int) -> list[BirthRecord]:
        """Find birth records within an inclusive birth year range."""
        qb = (
            self.query()
            .where("birth_year", start_year, FilterOp.GE)
            .where("birth_year", end_year, FilterOp.LE)
            .order_by("birth_date_sort", SortOrder.ASC)
            .order_by("id", SortOrder.ASC)
        )
        return self.find_where(qb)


class DeathRepository(BaseSQLiteRepository[DeathRecord, SourceID]):
    """SQLite repository for civil and archival DeathRecord sources."""

    def __init__(
        self,
        session_manager: DatabaseSessionManager | None = None,
        mapper: DeathRecordMapper | None = None,
    ) -> None:
        """Initialize DeathRepository."""
        super().__init__(
            mapper=mapper or DeathRecordMapper(),
            session_manager=session_manager,
        )

    @property
    def table_name(self) -> str:
        """Return target SQLite table name."""
        return "vital_deaths"

    def find_by_decedent(self, decedent_id: IndividualID | str) -> list[DeathRecord]:
        """Find death records linked to a specific decedent individual ID."""
        return self.find_by(decedent_id=_normalize_id(decedent_id))

    def find_by_location(self, location_id: LocationID | str) -> list[DeathRecord]:
        """Find death records linked to a place_of_death_id."""
        return self.find_by(place_of_death_id=_normalize_id(location_id))

    def find_by_disposition_site(self, site_id: SiteID | str) -> list[DeathRecord]:
        """Find death records linked to a burial/disposition site."""
        return self.find_by(disposition_site_id=_normalize_id(site_id))

    def find_by_certificate_number(self, certificate_number: str) -> list[DeathRecord]:
        """Find death records matching a civil certificate number."""
        return self.find_by(certificate_number=certificate_number)

    def find_by_year_range(self, start_year: int, end_year: int) -> list[DeathRecord]:
        """Find death records within an inclusive death year range."""
        qb = (
            self.query()
            .where("death_year", start_year, FilterOp.GE)
            .where("death_year", end_year, FilterOp.LE)
            .order_by("death_date_sort", SortOrder.ASC)
            .order_by("id", SortOrder.ASC)
        )
        return self.find_where(qb)


class DivorceRepository(BaseSQLiteRepository[DivorceRecord, SourceID]):
    """SQLite repository for judicial DivorceRecord sources."""

    def __init__(
        self,
        session_manager: DatabaseSessionManager | None = None,
        mapper: DivorceRecordMapper | None = None,
    ) -> None:
        """Initialize DivorceRepository."""
        super().__init__(
            mapper=mapper or DivorceRecordMapper(),
            session_manager=session_manager,
        )

    @property
    def table_name(self) -> str:
        """Return target SQLite table name."""
        return "vital_divorces"

    def find_by_husband(self, husband_id: IndividualID | str) -> list[DivorceRecord]:
        """Find divorce records linked to a specific husband individual ID."""
        return self.find_by(husband_id=_normalize_id(husband_id))

    def find_by_wife(self, wife_id: IndividualID | str) -> list[DivorceRecord]:
        """Find divorce records linked to a specific wife individual ID."""
        return self.find_by(wife_id=_normalize_id(wife_id))

    def find_by_jurisdiction(self, jurisdiction_id: LocationID | str) -> list[DivorceRecord]:
        """Find divorce records linked to a court jurisdiction location ID."""
        return self.find_by(jurisdiction_id=_normalize_id(jurisdiction_id))

    def find_by_docket_number(self, docket_number: str) -> list[DivorceRecord]:
        """Find divorce records matching a judicial docket number."""
        return self.find_by(docket_number=docket_number)

    def find_by_year_range(self, start_year: int, end_year: int) -> list[DivorceRecord]:
        """Find divorce records within an inclusive decree year range."""
        qb = (
            self.query()
            .where("decree_year", start_year, FilterOp.GE)
            .where("decree_year", end_year, FilterOp.LE)
            .order_by("decree_date_sort", SortOrder.ASC)
            .order_by("id", SortOrder.ASC)
        )
        return self.find_where(qb)


class MarriageRepository(BaseSQLiteRepository[MarriageRecord, SourceID]):
    """SQLite repository for civil and ecclesiastical MarriageRecord sources."""

    def __init__(
        self,
        session_manager: DatabaseSessionManager | None = None,
        mapper: MarriageRecordMapper | None = None,
    ) -> None:
        """Initialize MarriageRepository."""
        super().__init__(
            mapper=mapper or MarriageRecordMapper(),
            session_manager=session_manager,
        )

    @property
    def table_name(self) -> str:
        """Return target SQLite table name."""
        return "vital_marriages"

    def find_by_groom(self, groom_id: IndividualID | str) -> list[MarriageRecord]:
        """Find marriage records linked to a specific groom individual ID."""
        return self.find_by(groom_id=_normalize_id(groom_id))

    def find_by_bride(self, bride_id: IndividualID | str) -> list[MarriageRecord]:
        """Find marriage records linked to a specific bride individual ID."""
        return self.find_by(bride_id=_normalize_id(bride_id))

    def find_by_location(self, location_id: LocationID | str) -> list[MarriageRecord]:
        """Find marriage records linked to a place_of_marriage_id."""
        return self.find_by(place_of_marriage_id=_normalize_id(location_id))

    def find_by_license_number(self, license_number: str) -> list[MarriageRecord]:
        """Find marriage records matching a license number."""
        return self.find_by(license_number=license_number)

    def find_by_year_range(self, start_year: int, end_year: int) -> list[MarriageRecord]:
        """Find marriage records within an inclusive marriage year range."""
        qb = (
            self.query()
            .where("marriage_year", start_year, FilterOp.GE)
            .where("marriage_year", end_year, FilterOp.LE)
            .order_by("marriage_date_sort", SortOrder.ASC)
            .order_by("id", SortOrder.ASC)
        )
        return self.find_where(qb)
