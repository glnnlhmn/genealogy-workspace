"""Path: src/gda/repository/xref/collection.py

In-memory collections for Cross-Reference (gda.model.xref) bridge and index models.

Operational Role:
    Provides BaseXRefCollection and 9 concrete in-memory XRef collection
    managers with secondary lookup buckets, dirty tracking, SQLite persistence
    synchronization, and GDAJsonIO file export/import.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any, Self

from gda.core.introspectable import IntrospectableMixin
from gda.db.session import DatabaseSessionManager
from gda.io.json import GDAJsonIO
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
from gda.repository.errors import (
    DuplicateRecordError,
    RecordNotFoundError,
    RepositoryError,
)
from gda.repository.xref.repository import (
    FactParticipantXRefRepository,
    IndividualFamilyXRefRepository,
    IndividualOrganizationXRefRepository,
    IndividualSourceXRefRepository,
    IndividualSurnameXRefRepository,
    LocationXRefRepository,
    MediaXRefRepository,
    SiteXRefRepository,
    SurnameXRefRepository,
)
from gda.util.ids import normalize_id
from gda.util.text import clean_string

__version__ = "1.0.0+build.1"

__all__ = [
    "BaseXRefCollection",
    "FactParticipantXRefCollection",
    "IndividualFamilyXRefCollection",
    "IndividualOrganizationXRefCollection",
    "IndividualSourceXRefCollection",
    "IndividualSurnameXRefCollection",
    "LocationXRefCollection",
    "MediaXRefCollection",
    "SiteXRefCollection",
    "SurnameXRefCollection",
]


class BaseXRefCollection[
    TXRef,
    TRepo: BaseSQLiteRepository[Any, str],
](IntrospectableMixin, ABC):
    """Abstract in-memory collection manager for a compound-keyed XRef domain."""

    def __init__(self, repository: TRepo | None = None) -> None:
        """Initialize an empty XRef collection and its backing SQLite repository."""
        self._repo: TRepo = repository or self._create_default_repository()
        self._registry: dict[str, TXRef] = {}
        self._dirty_keys: set[str] = set()

    @abstractmethod
    def _create_default_repository(
        self,
        session_manager: DatabaseSessionManager | None = None,
    ) -> TRepo:
        """Instantiate the default SQLite repository for this XRef collection."""

    @abstractmethod
    def _deserialize_record(self, data: dict[str, Any]) -> TXRef:
        """Hydrate an XRef model instance from a serialized dictionary."""

    @abstractmethod
    def _index_domain_fields(self, record: TXRef) -> None:
        """Index an XRef record into secondary lookup buckets."""

    @abstractmethod
    def _unindex_domain_fields(self, record: TXRef) -> None:
        """Remove an XRef record from secondary lookup buckets."""

    def _records_for_keys(self, keys: Iterable[str]) -> list[TXRef]:
        """Return XRef records for a set of xref_keys sorted deterministically."""
        return [self._registry[k] for k in sorted(keys) if k in self._registry]

    @property
    def repository(self) -> TRepo:
        """Return the bound SQLite repository."""
        return self._repo

    @property
    def table_name(self) -> str:
        """Return the underlying SQLite table name."""
        return self._repo.table_name

    @property
    def is_dirty(self) -> bool:
        """Return True if any XRef records have uncommitted in-memory changes."""
        return bool(self._dirty_keys)

    def dirty_records(self) -> list[TXRef]:
        """Return all modified or newly added XRef records awaiting persistence."""
        return self._records_for_keys(self._dirty_keys)

    def dirty_entities(self) -> list[TXRef]:
        """Return all modified or newly added XRef records (gda.entity parity)."""
        return self.dirty_records()

    def mark_clean(self) -> None:
        """Clear all dirty-tracking flags after synchronization."""
        self._dirty_keys.clear()

    def __len__(self) -> int:
        """Return the count of XRef records in the collection."""
        return len(self._registry)

    def __iter__(self) -> Iterator[TXRef]:
        """Iterate over all XRef records in the collection."""
        yield from self._registry.values()

    def iter_all(self) -> Iterator[TXRef]:
        """Iterate over all XRef records in the collection."""
        yield from self._registry.values()

    def __contains__(self, key: object) -> bool:
        """Return True if an XRef record with the given xref_key exists."""
        if not isinstance(key, str):
            return False
        return key in self._registry

    def __getitem__(self, key: str) -> TXRef:
        """Retrieve an XRef record by xref_key, or raise RecordNotFoundError."""
        rec = self._registry.get(key)
        if rec is None:
            raise RecordNotFoundError(self.table_name, key)
        return rec

    def get(self, key: str, default: TXRef | None = None) -> TXRef | None:
        """Retrieve an XRef record by xref_key, or return default."""
        return self._registry.get(key, default)

    def add(self, record: TXRef, *, mark_dirty: bool = True) -> TXRef:
        """Register a new XRef record into the collection."""
        key = str(record.xref_key)
        if key in self._registry:
            raise DuplicateRecordError(self.table_name, key)
        self._registry[key] = record
        self._index_domain_fields(record)
        if mark_dirty:
            self._dirty_keys.add(key)
        return record

    def update(self, record: TXRef) -> TXRef:
        """Replace an existing XRef record and re-index secondary buckets."""
        key = str(record.xref_key)
        existing = self._registry.get(key)
        if existing is None:
            raise RecordNotFoundError(self.table_name, key)
        self._unindex_domain_fields(existing)
        self._registry[key] = record
        self._index_domain_fields(record)
        self._dirty_keys.add(key)
        return record

    def remove(self, key: str) -> bool:
        """Remove an XRef record from in-memory state by xref_key."""
        existing = self._registry.pop(key, None)
        if existing is None:
            return False
        self._unindex_domain_fields(existing)
        self._dirty_keys.discard(key)
        return True

    def clear(self) -> None:
        """Remove all XRef records and reset secondary indexes."""
        for existing in list(self._registry.values()):
            self._unindex_domain_fields(existing)
        self._registry.clear()
        self._dirty_keys.clear()

    def load_from_db(
        self,
        session_manager: DatabaseSessionManager | None = None,
    ) -> int:
        """Load all XRef records from the SQLite table into this collection."""
        repo = (
            self._create_default_repository(session_manager=session_manager)
            if session_manager is not None
            else self._repo
        )
        self.clear()
        records = repo.list_all()
        for rec in records:
            self.add(rec, mark_dirty=False)
        self.mark_clean()
        return len(records)

    def refresh(
        self,
        session_manager: DatabaseSessionManager | None = None,
    ) -> int:
        """Clear in-memory state and reload all XRef records from SQLite."""
        return self.load_from_db(session_manager=session_manager)

    def save_to_db(
        self,
        session_manager: DatabaseSessionManager | None = None,
        *,
        dirty_only: bool = False,
    ) -> int:
        """Persist XRef records to the SQLite table and mark clean."""
        repo = (
            self._create_default_repository(session_manager=session_manager)
            if session_manager is not None
            else self._repo
        )
        targets = self.dirty_records() if dirty_only else list(self._registry.values())
        written = repo.upsert_many(targets)
        self.mark_clean()
        return written

    @classmethod
    def from_database(
        cls,
        session_manager: DatabaseSessionManager | None = None,
    ) -> Self:
        """Create and populate an XRef collection directly from SQLite."""
        instance = cls()
        if session_manager is not None:
            instance._repo = instance._create_default_repository(session_manager=session_manager)
        instance.load_from_db(session_manager=session_manager)
        return instance

    def export_file(
        self,
        path: Path | str,
        *,
        create_backup: bool = False,
        backup_dir: Path | str | None = None,
    ) -> int:
        """Export XRef collection records to a formatted JSON file via GDAJsonIO."""
        records = self._records_for_keys(self._registry.keys())
        serialized = [rec.to_dict() for rec in records]  # type: ignore[attr-defined]
        payload = {
            "schema_version": "1.0.0",
            "table_name": self.table_name,
            "total_count": len(serialized),
            "records": serialized,
        }
        GDAJsonIO.write(
            Path(path),
            payload,
            create_backup=create_backup,
            backup_dir=backup_dir,
        )
        return len(serialized)

    def import_file(self, path: Path | str, *, mark_dirty: bool = True) -> int:
        """Import XRef records from a formatted JSON file into the collection."""
        raw = GDAJsonIO.read(Path(path))
        if not isinstance(raw, dict) or not isinstance(raw.get("records"), list):
            raise RepositoryError(
                f"Invalid XRef export payload in '{path}': missing 'records' list."
            )
        items: list[dict[str, Any]] = raw["records"]
        for item_dict in items:
            rec = self._deserialize_record(item_dict)
            key = str(rec.xref_key)
            if key in self._registry:
                self.update(rec)
                if not mark_dirty:
                    self._dirty_keys.discard(key)
            else:
                self.add(rec, mark_dirty=mark_dirty)
        return len(items)


class FactParticipantXRefCollection(
    BaseXRefCollection[FactParticipantXRef, FactParticipantXRefRepository]
):
    """In-memory collection for FactParticipantXRef bridge records."""

    def __init__(
        self,
        repository: FactParticipantXRefRepository | None = None,
    ) -> None:
        """Initialize FactParticipantXRefCollection with fact and individual buckets."""
        self._by_fact: dict[str, set[str]] = defaultdict(set)
        self._by_individual: dict[str, set[str]] = defaultdict(set)
        super().__init__(repository=repository)

    def _create_default_repository(
        self,
        session_manager: DatabaseSessionManager | None = None,
    ) -> FactParticipantXRefRepository:
        return FactParticipantXRefRepository(session_manager=session_manager)

    def _deserialize_record(self, data: dict[str, Any]) -> FactParticipantXRef:
        return FactParticipantXRef.from_dict(data)

    def _index_domain_fields(self, record: FactParticipantXRef) -> None:
        self._by_fact[record.fact_id.value].add(record.xref_key)
        self._by_individual[record.individual_id.value].add(record.xref_key)

    def _unindex_domain_fields(self, record: FactParticipantXRef) -> None:
        self._by_fact[record.fact_id.value].discard(record.xref_key)
        self._by_individual[record.individual_id.value].discard(record.xref_key)

    def find_by_fact(
        self,
        fact_id: FactID | str,
    ) -> list[FactParticipantXRef]:
        """Return FactParticipantXRef rows for a FactID."""
        return self._records_for_keys(self._by_fact.get(normalize_id(fact_id), set()))

    def find_by_individual(
        self,
        individual_id: IndividualID | str,
    ) -> list[FactParticipantXRef]:
        """Return FactParticipantXRef rows for an IndividualID."""
        return self._records_for_keys(self._by_individual.get(normalize_id(individual_id), set()))


class IndividualFamilyXRefCollection(
    BaseXRefCollection[IndividualFamilyXRef, IndividualFamilyXRefRepository]
):
    """In-memory collection for IndividualFamilyXRef bridge records."""

    def __init__(
        self,
        repository: IndividualFamilyXRefRepository | None = None,
    ) -> None:
        """Initialize IndividualFamilyXRefCollection with family and individual buckets."""
        self._by_family: dict[str, set[str]] = defaultdict(set)
        self._by_individual: dict[str, set[str]] = defaultdict(set)
        super().__init__(repository=repository)

    def _create_default_repository(
        self,
        session_manager: DatabaseSessionManager | None = None,
    ) -> IndividualFamilyXRefRepository:
        return IndividualFamilyXRefRepository(session_manager=session_manager)

    def _deserialize_record(self, data: dict[str, Any]) -> IndividualFamilyXRef:
        return IndividualFamilyXRef.from_dict(data)

    def _index_domain_fields(self, record: IndividualFamilyXRef) -> None:
        self._by_family[record.family_id.value].add(record.xref_key)
        self._by_individual[record.individual_id.value].add(record.xref_key)

    def _unindex_domain_fields(self, record: IndividualFamilyXRef) -> None:
        self._by_family[record.family_id.value].discard(record.xref_key)
        self._by_individual[record.individual_id.value].discard(record.xref_key)

    def find_by_family(
        self,
        family_id: FamilyID | str,
    ) -> list[IndividualFamilyXRef]:
        """Return IndividualFamilyXRef rows for a FamilyID."""
        return self._records_for_keys(self._by_family.get(normalize_id(family_id), set()))

    def find_by_individual(
        self,
        individual_id: IndividualID | str,
    ) -> list[IndividualFamilyXRef]:
        """Return IndividualFamilyXRef rows for an IndividualID."""
        return self._records_for_keys(self._by_individual.get(normalize_id(individual_id), set()))


class IndividualOrganizationXRefCollection(
    BaseXRefCollection[
        IndividualOrganizationXRef,
        IndividualOrganizationXRefRepository,
    ]
):
    """In-memory collection for IndividualOrganizationXRef bridge records."""

    def __init__(
        self,
        repository: IndividualOrganizationXRefRepository | None = None,
    ) -> None:
        """Initialize IndividualOrganizationXRefCollection with org and individual buckets."""
        self._by_organization: dict[str, set[str]] = defaultdict(set)
        self._by_individual: dict[str, set[str]] = defaultdict(set)
        super().__init__(repository=repository)

    def _create_default_repository(
        self,
        session_manager: DatabaseSessionManager | None = None,
    ) -> IndividualOrganizationXRefRepository:
        return IndividualOrganizationXRefRepository(session_manager=session_manager)

    def _deserialize_record(
        self,
        data: dict[str, Any],
    ) -> IndividualOrganizationXRef:
        return IndividualOrganizationXRef.from_dict(data)

    def _index_domain_fields(self, record: IndividualOrganizationXRef) -> None:
        self._by_organization[record.organization_id.value].add(record.xref_key)
        self._by_individual[record.individual_id.value].add(record.xref_key)

    def _unindex_domain_fields(
        self,
        record: IndividualOrganizationXRef,
    ) -> None:
        self._by_organization[record.organization_id.value].discard(record.xref_key)
        self._by_individual[record.individual_id.value].discard(record.xref_key)

    def find_by_organization(
        self,
        organization_id: OrganizationID | str,
    ) -> list[IndividualOrganizationXRef]:
        """Return IndividualOrganizationXRef rows for an OrganizationID."""
        return self._records_for_keys(
            self._by_organization.get(normalize_id(organization_id), set())
        )

    def find_by_individual(
        self,
        individual_id: IndividualID | str,
    ) -> list[IndividualOrganizationXRef]:
        """Return IndividualOrganizationXRef rows for an IndividualID."""
        return self._records_for_keys(self._by_individual.get(normalize_id(individual_id), set()))


class IndividualSourceXRefCollection(
    BaseXRefCollection[IndividualSourceXRef, IndividualSourceXRefRepository]
):
    """In-memory collection for IndividualSourceXRef bridge records."""

    def __init__(
        self,
        repository: IndividualSourceXRefRepository | None = None,
    ) -> None:
        """Initialize IndividualSourceXRefCollection with source and individual buckets."""
        self._by_source: dict[str, set[str]] = defaultdict(set)
        self._by_individual: dict[str, set[str]] = defaultdict(set)
        super().__init__(repository=repository)

    def _create_default_repository(
        self,
        session_manager: DatabaseSessionManager | None = None,
    ) -> IndividualSourceXRefRepository:
        return IndividualSourceXRefRepository(session_manager=session_manager)

    def _deserialize_record(self, data: dict[str, Any]) -> IndividualSourceXRef:
        return IndividualSourceXRef.from_dict(data)

    def _index_domain_fields(self, record: IndividualSourceXRef) -> None:
        self._by_source[record.source_id.value].add(record.xref_key)
        self._by_individual[record.individual_id.value].add(record.xref_key)

    def _unindex_domain_fields(self, record: IndividualSourceXRef) -> None:
        self._by_source[record.source_id.value].discard(record.xref_key)
        self._by_individual[record.individual_id.value].discard(record.xref_key)

    def find_by_source(
        self,
        source_id: SourceID | str,
    ) -> list[IndividualSourceXRef]:
        """Return IndividualSourceXRef rows for a SourceID."""
        return self._records_for_keys(self._by_source.get(normalize_id(source_id), set()))

    def find_by_individual(
        self,
        individual_id: IndividualID | str,
    ) -> list[IndividualSourceXRef]:
        """Return IndividualSourceXRef rows for an IndividualID."""
        return self._records_for_keys(self._by_individual.get(normalize_id(individual_id), set()))


class IndividualSurnameXRefCollection(
    BaseXRefCollection[IndividualSurnameXRef, IndividualSurnameXRefRepository]
):
    """In-memory collection for IndividualSurnameXRef bridge records."""

    def __init__(
        self,
        repository: IndividualSurnameXRefRepository | None = None,
    ) -> None:
        """Initialize IndividualSurnameXRefCollection with surname and individual buckets."""
        self._by_surname: dict[str, set[str]] = defaultdict(set)
        self._by_individual: dict[str, set[str]] = defaultdict(set)
        super().__init__(repository=repository)

    def _create_default_repository(
        self,
        session_manager: DatabaseSessionManager | None = None,
    ) -> IndividualSurnameXRefRepository:
        return IndividualSurnameXRefRepository(session_manager=session_manager)

    def _deserialize_record(
        self,
        data: dict[str, Any],
    ) -> IndividualSurnameXRef:
        return IndividualSurnameXRef.from_dict(data)

    def _index_domain_fields(self, record: IndividualSurnameXRef) -> None:
        self._by_surname[record.surname].add(record.xref_key)
        self._by_individual[record.individual_id.value].add(record.xref_key)

    def _unindex_domain_fields(self, record: IndividualSurnameXRef) -> None:
        self._by_surname[record.surname].discard(record.xref_key)
        self._by_individual[record.individual_id.value].discard(record.xref_key)

    def find_by_surname(self, surname: str) -> list[IndividualSurnameXRef]:
        """Return IndividualSurnameXRef rows matching a surname."""
        norm = (clean_string(surname) or "").upper()
        return self._records_for_keys(self._by_surname.get(norm, set()))

    def find_by_individual(
        self,
        individual_id: IndividualID | str,
    ) -> list[IndividualSurnameXRef]:
        """Return IndividualSurnameXRef rows for an IndividualID."""
        return self._records_for_keys(self._by_individual.get(normalize_id(individual_id), set()))


class LocationXRefCollection(BaseXRefCollection[LocationXRef, LocationXRefRepository]):
    """In-memory collection for LocationXRef bridge records."""

    def __init__(self, repository: LocationXRefRepository | None = None) -> None:
        """Initialize LocationXRefCollection with location and target buckets."""
        self._by_location: dict[str, set[str]] = defaultdict(set)
        self._by_target: dict[str, set[str]] = defaultdict(set)
        super().__init__(repository=repository)

    def _create_default_repository(
        self,
        session_manager: DatabaseSessionManager | None = None,
    ) -> LocationXRefRepository:
        return LocationXRefRepository(session_manager=session_manager)

    def _deserialize_record(self, data: dict[str, Any]) -> LocationXRef:
        return LocationXRef.from_dict(data)

    def _index_domain_fields(self, record: LocationXRef) -> None:
        self._by_location[record.location_id.value].add(record.xref_key)
        self._by_target[record.target_id.value].add(record.xref_key)

    def _unindex_domain_fields(self, record: LocationXRef) -> None:
        self._by_location[record.location_id.value].discard(record.xref_key)
        self._by_target[record.target_id.value].discard(record.xref_key)

    def find_by_location(
        self,
        location_id: LocationID | str,
    ) -> list[LocationXRef]:
        """Return LocationXRef rows for a LocationID."""
        return self._records_for_keys(self._by_location.get(normalize_id(location_id), set()))

    def find_by_target(
        self,
        target_id: AtomID | SourceID | str,
    ) -> list[LocationXRef]:
        """Return LocationXRef rows for a target entity/source ID."""
        return self._records_for_keys(self._by_target.get(normalize_id(target_id), set()))


class MediaXRefCollection(BaseXRefCollection[MediaXRef, MediaXRefRepository]):
    """In-memory collection for MediaXRef bridge records."""

    def __init__(self, repository: MediaXRefRepository | None = None) -> None:
        """Initialize MediaXRefCollection with media and target buckets."""
        self._by_media: dict[str, set[str]] = defaultdict(set)
        self._by_target: dict[str, set[str]] = defaultdict(set)
        super().__init__(repository=repository)

    def _create_default_repository(
        self,
        session_manager: DatabaseSessionManager | None = None,
    ) -> MediaXRefRepository:
        return MediaXRefRepository(session_manager=session_manager)

    def _deserialize_record(self, data: dict[str, Any]) -> MediaXRef:
        return MediaXRef.from_dict(data)

    def _index_domain_fields(self, record: MediaXRef) -> None:
        self._by_media[record.media_id.value].add(record.xref_key)
        self._by_target[record.target_id.value].add(record.xref_key)

    def _unindex_domain_fields(self, record: MediaXRef) -> None:
        self._by_media[record.media_id.value].discard(record.xref_key)
        self._by_target[record.target_id.value].discard(record.xref_key)

    def find_by_media(self, media_id: MediaID | str) -> list[MediaXRef]:
        """Return MediaXRef rows for a MediaID."""
        return self._records_for_keys(self._by_media.get(normalize_id(media_id), set()))

    def find_by_target(
        self,
        target_id: AtomID | SourceID | str,
    ) -> list[MediaXRef]:
        """Return MediaXRef rows for a target entity/source ID."""
        return self._records_for_keys(self._by_target.get(normalize_id(target_id), set()))


class SiteXRefCollection(BaseXRefCollection[SiteXRef, SiteXRefRepository]):
    """In-memory collection for SiteXRef bridge records."""

    def __init__(self, repository: SiteXRefRepository | None = None) -> None:
        """Initialize SiteXRefCollection with site, location, and target buckets."""
        self._by_site: dict[str, set[str]] = defaultdict(set)
        self._by_location: dict[str, set[str]] = defaultdict(set)
        self._by_target: dict[str, set[str]] = defaultdict(set)
        super().__init__(repository=repository)

    def _create_default_repository(
        self,
        session_manager: DatabaseSessionManager | None = None,
    ) -> SiteXRefRepository:
        return SiteXRefRepository(session_manager=session_manager)

    def _deserialize_record(self, data: dict[str, Any]) -> SiteXRef:
        return SiteXRef.from_dict(data)

    def _index_domain_fields(self, record: SiteXRef) -> None:
        self._by_site[record.site_id.value].add(record.xref_key)
        self._by_location[record.location_id.value].add(record.xref_key)
        self._by_target[record.target_id.value].add(record.xref_key)

    def _unindex_domain_fields(self, record: SiteXRef) -> None:
        self._by_site[record.site_id.value].discard(record.xref_key)
        self._by_location[record.location_id.value].discard(record.xref_key)
        self._by_target[record.target_id.value].discard(record.xref_key)

    def find_by_site(self, site_id: SiteID | str) -> list[SiteXRef]:
        """Return SiteXRef rows for a SiteID."""
        return self._records_for_keys(self._by_site.get(normalize_id(site_id), set()))

    def find_by_location(
        self,
        location_id: LocationID | str,
    ) -> list[SiteXRef]:
        """Return SiteXRef rows for a LocationID."""
        return self._records_for_keys(self._by_location.get(normalize_id(location_id), set()))

    def find_by_target(
        self,
        target_id: AtomID | SourceID | str,
    ) -> list[SiteXRef]:
        """Return SiteXRef rows for a target entity/source ID."""
        return self._records_for_keys(self._by_target.get(normalize_id(target_id), set()))


class SurnameXRefCollection(BaseXRefCollection[SurnameXRef, SurnameXRefRepository]):
    """In-memory collection for SurnameXRef onomastic equivalence records."""

    def __init__(self, repository: SurnameXRefRepository | None = None) -> None:
        """Initialize SurnameXRefCollection with canonical and variant buckets."""
        self._by_canonical: dict[str, set[str]] = defaultdict(set)
        self._by_variant: dict[str, set[str]] = defaultdict(set)
        super().__init__(repository=repository)

    def _create_default_repository(
        self,
        session_manager: DatabaseSessionManager | None = None,
    ) -> SurnameXRefRepository:
        return SurnameXRefRepository(session_manager=session_manager)

    def _deserialize_record(self, data: dict[str, Any]) -> SurnameXRef:
        return SurnameXRef.from_dict(data)

    def _index_domain_fields(self, record: SurnameXRef) -> None:
        self._by_canonical[record.canonical_surname].add(record.xref_key)
        self._by_variant[record.variant_surname].add(record.xref_key)

    def _unindex_domain_fields(self, record: SurnameXRef) -> None:
        self._by_canonical[record.canonical_surname].discard(record.xref_key)
        self._by_variant[record.variant_surname].discard(record.xref_key)

    def find_by_canonical_surname(
        self,
        canonical_surname: str,
    ) -> list[SurnameXRef]:
        """Return SurnameXRef rows for a canonical surname."""
        norm = (clean_string(canonical_surname) or "").upper()
        return self._records_for_keys(self._by_canonical.get(norm, set()))

    def find_by_variant_surname(
        self,
        variant_surname: str,
    ) -> list[SurnameXRef]:
        """Return SurnameXRef rows for a variant surname."""
        norm = (clean_string(variant_surname) or "").upper()
        return self._records_for_keys(self._by_variant.get(norm, set()))
