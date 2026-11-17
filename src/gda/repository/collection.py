"""Path: src/gda/repository/collection.py

In-memory archival source collection base class with editing, dirty-tracking,
graveyard lifecycle, and SQLite/JSON synchronization.

Operational Role:
    Provides the shared collection ergonomics of gda.entity (O(1) ID/URN lookup,
    in-memory editing via dataclasses.replace, tombstone/undelete lifecycle,
    supersession chain resolution, dirty tracking, and repository/JSON I/O)
    for all SourceRecord domain collections.
"""

from __future__ import annotations

import dataclasses
from abc import ABC, abstractmethod
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any, Self

from gda.core.dates import utc_now_iso
from gda.core.enums import IDType
from gda.core.introspectable import IntrospectableMixin
from gda.db.session import DatabaseSessionManager
from gda.io.json import GDAJsonIO
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import SourceID
from gda.model.base.audit import AuditStamp
from gda.model.base.source import SourceRecord
from gda.model.base.tombstone import Tombstone
from gda.repository.base import BaseSQLiteRepository
from gda.repository.errors import (
    DuplicateRecordError,
    RecordNotFoundError,
    RepositoryError,
)
from gda.util.ids import verify_id

__version__ = "1.0.0+build.5"

__all__ = [
    "BaseSourceCollection",
]


def _to_source_id(identifier: SourceID | str) -> SourceID:
    """Coerce a SourceID or UUID string into a validated SourceID."""
    return identifier if isinstance(identifier, SourceID) else SourceID(str(identifier))


class BaseSourceCollection[
    TModel: SourceRecord,
    TRepo: BaseSQLiteRepository[Any, SourceID],
](IntrospectableMixin, ABC):
    """Abstract in-memory collection manager for a SourceRecord domain."""

    def __init__(self, repository: TRepo | None = None) -> None:
        """Initialize an empty source collection and its backing SQLite repository."""
        self._repo: TRepo = repository or self._create_default_repository()
        self._registry: dict[SourceID, TModel] = {}
        self._urn_index: dict[str, SourceID] = {}
        self._dirty_ids: set[SourceID] = set()

    @abstractmethod
    def _create_default_repository(
        self,
        session_manager: DatabaseSessionManager | None = None,
    ) -> TRepo:
        """Instantiate the default SQLite repository for this collection domain."""

    @abstractmethod
    def _deserialize_record(self, data: dict[str, Any]) -> TModel:
        """Hydrate a domain record instance from a serialized dictionary."""

    def _index_domain_fields(self, record: TModel) -> None:  # noqa: B027
        """Hook for subclasses to index active record into domain-specific buckets."""

    def _unindex_domain_fields(self, record: TModel) -> None:  # noqa: B027
        """Hook for subclasses to remove record from domain-specific buckets."""

    def _records_for_ids(self, sids: Iterable[SourceID]) -> list[TModel]:
        """Return active records for a set of SourceIDs sorted deterministically by ID."""
        return [
            self._registry[sid]
            for sid in sorted(sids, key=lambda s: s.value)
            if sid in self._registry
        ]

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
        """Return True if any records have uncommitted in-memory modifications."""
        return bool(self._dirty_ids)

    def dirty_records(self) -> list[TModel]:
        """Return all modified or newly added records awaiting database persistence."""
        return self._records_for_ids(self._dirty_ids)

    def dirty_entities(self) -> list[TModel]:
        """Return all modified or newly added records (gda.entity interface parity)."""
        return self.dirty_records()

    def mark_clean(self) -> None:
        """Clear all dirty-tracking flags after synchronization."""
        self._dirty_ids.clear()

    @staticmethod
    def _is_deprecated(record: TModel) -> bool:
        """Return True if the record has an active deprecation tombstone."""
        return record.tombstone is not None and record.tombstone.is_deprecated

    def __len__(self) -> int:
        """Return the count of active (non-tombstoned) records in the collection."""
        return sum(1 for rec in self._registry.values() if not self._is_deprecated(rec))

    def __iter__(self) -> Iterator[TModel]:
        """Iterate over active (non-tombstoned) records in the collection."""
        for rec in self._registry.values():
            if not self._is_deprecated(rec):
                yield rec

    def iter_all(self) -> Iterator[TModel]:
        """Iterate over all records in the collection, including tombstoned records."""
        yield from self._registry.values()

    def _resolve_lookup_id(
        self,
        key: SourceID | str,
        *,
        include_graveyard: bool = False,
    ) -> SourceID | None:
        """Resolve a SourceID, UUID string, or URN string to a registered SourceID."""
        if isinstance(key, SourceID):
            rec = self._registry.get(key)
            if rec is None:
                return None
            if not include_graveyard and self._is_deprecated(rec):
                return None
            return key

        key_str = str(key)
        if key_str in self._urn_index:
            return self._urn_index[key_str]

        if verify_id(key_str, id_type=IDType.UUID):
            sid = SourceID(key_str)
            if sid in self._registry:
                rec = self._registry[sid]
                if include_graveyard or not self._is_deprecated(rec):
                    return sid
            return None

        if include_graveyard:
            for cand_id, cand in self._registry.items():
                if str(cand.source_urn.value) == key_str:
                    return cand_id
        return None

    def __contains__(self, key: object) -> bool:
        """Return True if an active record with the given SourceID or URN exists."""
        if not isinstance(key, (SourceID, str)):
            return False
        return self._resolve_lookup_id(key, include_graveyard=False) is not None

    def __getitem__(self, key: SourceID | str) -> TModel:
        """Retrieve an active record by SourceID or URN, or raise RecordNotFoundError."""
        sid = self._resolve_lookup_id(key, include_graveyard=False)
        if sid is None:
            raise RecordNotFoundError(self.table_name, key)
        return self._registry[sid]

    def get(
        self,
        key: SourceID | str,
        default: TModel | None = None,
    ) -> TModel | None:
        """Retrieve an active record by SourceID or URN, or return default."""
        sid = self._resolve_lookup_id(key, include_graveyard=False)
        return self._registry[sid] if sid is not None else default

    def get_any(
        self,
        key: SourceID | str,
        default: TModel | None = None,
    ) -> TModel | None:
        """Retrieve a record by SourceID or URN including tombstoned records."""
        sid = self._resolve_lookup_id(key, include_graveyard=True)
        return self._registry[sid] if sid is not None else default

    def add(self, record: TModel, *, mark_dirty: bool = True) -> TModel:
        """Register a new source record into the collection."""
        sid = record.source_id
        urn_str = str(record.source_urn.value)

        if sid in self._registry:
            raise DuplicateRecordError(self.table_name, sid.value)
        if not self._is_deprecated(record) and urn_str in self._urn_index:
            raise DuplicateRecordError(self.table_name, urn_str)

        self._registry[sid] = record
        if not self._is_deprecated(record):
            self._urn_index[urn_str] = sid
            self._index_domain_fields(record)

        if mark_dirty:
            self._dirty_ids.add(sid)
        return record

    def update(self, record: TModel) -> TModel:
        """Replace an existing record in the collection and re-index all buckets."""
        sid = record.source_id
        existing = self._registry.get(sid)
        if existing is None:
            raise RecordNotFoundError(self.table_name, sid.value)

        new_urn = str(record.source_urn.value)
        if (
            not self._is_deprecated(record)
            and new_urn in self._urn_index
            and self._urn_index[new_urn] != sid
        ):
            raise DuplicateRecordError(self.table_name, new_urn)

        if not self._is_deprecated(existing):
            self._urn_index.pop(str(existing.source_urn.value), None)
            self._unindex_domain_fields(existing)

        self._registry[sid] = record
        if not self._is_deprecated(record):
            self._urn_index[new_urn] = sid
            self._index_domain_fields(record)

        self._dirty_ids.add(sid)
        return record

    def edit(self, target_id: SourceID | str, /, **changes: Any) -> TModel:
        """Create an updated copy of an existing record with modified fields."""
        sid = _to_source_id(target_id)
        existing = self._registry.get(sid)
        if existing is None:
            raise RecordNotFoundError(self.table_name, sid.value)

        if "source_id" in changes and changes["source_id"] != sid:
            raise RepositoryError("Cannot mutate primary key 'source_id' via edit().")

        if "audit" not in changes:
            now_ts = IsoTimestamp(utc_now_iso())
            changes["audit"] = AuditStamp(
                created_at=existing.audit.created_at,
                updated_at=now_ts,
            )

        updated: TModel = dataclasses.replace(existing, **changes)
        return self.update(updated)

    def can_tombstone(
        self,
        source_id: SourceID | str,
        superseded_by: SourceID | str | None = None,
    ) -> tuple[bool, str | None]:
        """Verify whether a source record can be safely retired."""
        sid = _to_source_id(source_id)
        target = self._registry.get(sid)
        if target is None:
            return False, f"Source record '{sid}' does not exist in collection."
        if self._is_deprecated(target):
            return False, f"Source record '{sid}' is already tombstoned."

        if superseded_by is not None:
            rep_id = _to_source_id(superseded_by)
            if rep_id == sid:
                return (
                    False,
                    f"Replacement source '{rep_id}' cannot be the record itself.",
                )
            rep = self._registry.get(rep_id)
            if rep is None:
                return (
                    False,
                    f"Replacement source '{rep_id}' does not exist in collection.",
                )
            if self._is_deprecated(rep):
                return (
                    False,
                    f"Replacement source '{rep_id}' is itself tombstoned.",
                )

        return True, None

    def soft_delete(
        self,
        source_id: SourceID | str,
        reason: str | None = None,
        *,
        superseded_by: SourceID | str | None = None,
        deprecated_at: IsoTimestamp | str | None = None,
    ) -> TModel:
        """Tombstone an active source record and remove it from active lookup buckets."""
        if reason is not None and not reason.strip():
            raise RepositoryError("Tombstone reason cannot be empty or whitespace.")

        ok, err_msg = self.can_tombstone(source_id, superseded_by=superseded_by)
        if not ok:
            raise RepositoryError(err_msg or "Cannot tombstone source record.")

        sid = _to_source_id(source_id)
        rep_id = _to_source_id(superseded_by) if superseded_by is not None else None
        if deprecated_at is None:
            ts = IsoTimestamp(utc_now_iso())
        elif isinstance(deprecated_at, IsoTimestamp):
            ts = deprecated_at
        else:
            ts = IsoTimestamp(str(deprecated_at))

        tomb = Tombstone[SourceID](
            is_deprecated=True,
            deprecated_at=ts,
            superseded_by=rep_id,
        )
        return self.edit(sid, tombstone=tomb)

    def can_undelete(self, source_id: SourceID | str) -> tuple[bool, str | None]:
        """Verify whether a tombstoned source record can be restored to active status."""
        sid = _to_source_id(source_id)
        target = self._registry.get(sid)
        if target is None:
            return False, f"Source record '{sid}' does not exist in collection."
        if not self._is_deprecated(target):
            return False, f"Source record '{sid}' is not tombstoned."
        urn_str = str(target.source_urn.value)
        if urn_str in self._urn_index:
            return (
                False,
                f"Active URN '{urn_str}' is already claimed by another record.",
            )
        return True, None

    def undelete(self, source_id: SourceID | str) -> TModel:
        """Restore a tombstoned source record back to active status."""
        ok, err_msg = self.can_undelete(source_id)
        if not ok:
            raise RepositoryError(err_msg or "Cannot restore source record.")

        sid = _to_source_id(source_id)
        active_tomb = Tombstone[SourceID](
            is_deprecated=False,
            deprecated_at=None,
            superseded_by=None,
        )
        return self.edit(sid, tombstone=active_tomb)

    def restore(self, source_id: SourceID | str) -> TModel:
        """Alias for undelete() restoring a tombstoned source record."""
        return self.undelete(source_id)

    def find_tombstoned(self) -> list[TModel]:
        """Return all deprecated/tombstoned records in the collection."""
        return [rec for rec in self._registry.values() if self._is_deprecated(rec)]

    def resolve_active(self, source_id: SourceID | str) -> TModel:
        """Follow superseded_by links to return the current active replacement record."""
        curr_id = _to_source_id(source_id)
        visited: set[SourceID] = set()

        while True:
            if curr_id in visited:
                raise RepositoryError(f"Supersession cycle detected while resolving '{curr_id}'.")
            visited.add(curr_id)

            rec = self._registry.get(curr_id)
            if rec is None:
                raise RecordNotFoundError(self.table_name, curr_id.value)

            if not self._is_deprecated(rec):
                return rec

            next_id = rec.tombstone.superseded_by if rec.tombstone else None
            if next_id is None:
                raise RepositoryError(
                    f"Source record '{curr_id}' is tombstoned without a replacement."
                )
            curr_id = next_id

    def load_from_db(
        self,
        session_manager: DatabaseSessionManager | None = None,
    ) -> int:
        """Load all records from the SQLite table into this collection."""
        repo = (
            self._create_default_repository(session_manager=session_manager)
            if session_manager is not None
            else self._repo
        )
        for existing in list(self._registry.values()):
            self._unindex_domain_fields(existing)
        self._registry.clear()
        self._urn_index.clear()
        self._dirty_ids.clear()

        records = repo.list_all()
        for rec in records:
            self.add(rec, mark_dirty=False)
        self.mark_clean()
        return len(records)

    def refresh(
        self,
        session_manager: DatabaseSessionManager | None = None,
    ) -> int:
        """Clear in-memory state and reload all records from the SQLite database."""
        return self.load_from_db(session_manager=session_manager)

    def save_to_db(
        self,
        session_manager: DatabaseSessionManager | None = None,
        *,
        dirty_only: bool = False,
    ) -> int:
        """Persist collection records to the SQLite table and mark clean."""
        repo = (
            self._create_default_repository(session_manager=session_manager)
            if session_manager is not None
            else self._repo
        )
        targets = self.dirty_records() if dirty_only else list(self.iter_all())
        written = repo.upsert_many(targets)
        self.mark_clean()
        return written

    @classmethod
    def from_database(
        cls,
        session_manager: DatabaseSessionManager | None = None,
    ) -> Self:
        """Create and populate a collection directly from the SQLite database."""
        instance = cls()
        if session_manager is not None:
            instance._repo = instance._create_default_repository(session_manager=session_manager)
        instance.load_from_db(session_manager=session_manager)
        return instance

    def export_file(
        self,
        path: Path | str,
        *,
        include_graveyard: bool = True,
        create_backup: bool = False,
        backup_dir: Path | str | None = None,
    ) -> int:
        """Export collection records to a formatted JSON file via GDAJsonIO."""
        records = list(self.iter_all() if include_graveyard else self)
        serialized = [rec.to_dict() for rec in records]
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
        """Import source records from a formatted JSON file into the collection."""
        raw = GDAJsonIO.read(Path(path))
        if not isinstance(raw, dict) or not isinstance(raw.get("records"), list):
            raise RepositoryError(
                f"Invalid source export payload in '{path}': missing 'records' list."
            )
        items: list[dict[str, Any]] = raw["records"]
        for item_dict in items:
            rec = self._deserialize_record(item_dict)
            if rec.source_id in self._registry:
                self.update(rec)
                if not mark_dirty:
                    self._dirty_ids.discard(rec.source_id)
            else:
                self.add(rec, mark_dirty=mark_dirty)
        return len(items)
