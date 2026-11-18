"""Path: src/gda/repository/base.py

Generic SQLite CRUD repository base class for GDA domain persistence.

Operational Role:
    Bridges DatabaseSessionManager and BaseRowMapper to provide atomic,
    strongly-typed CRUD and query operations for archival source records
    and cross-reference link models.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable, Mapping
from typing import Any

from gda.core.introspectable import IntrospectableMixin
from gda.db.exceptions import (
    ConstraintViolationError,
    DatabaseError,
    EntityMappingError,
)
from gda.db.mapper.base import BaseRowMapper
from gda.db.session import DatabaseSessionManager
from gda.repository.errors import (
    DuplicateRecordError,
    RecordNotFoundError,
    RepositoryError,
)
from gda.repository.query import (
    QueryBuilder,
    SortOrder,
    build_insert_sql,
    build_upsert_sql,
    validate_sql_identifier,
)
from gda.util.ids import normalize_id
from gda.util.text import clean_string

__version__ = "1.0.0+build.6"

__all__ = [
    "BaseSQLiteRepository",
    "_normalize_id",
]

_normalize_id = normalize_id


class BaseSQLiteRepository[TModel, TID](IntrospectableMixin, ABC):
    """Abstract base SQLite repository providing standardized CRUD operations."""

    def __init__(
        self,
        mapper: BaseRowMapper[TModel],
        session_manager: DatabaseSessionManager | None = None,
    ) -> None:
        """Initialize repository with a row mapper and session manager."""
        validate_sql_identifier(self.table_name)
        validate_sql_identifier(self.primary_key)
        self._mapper = mapper
        self._session = session_manager or DatabaseSessionManager()

    @property
    @abstractmethod
    def table_name(self) -> str:
        """Return the SQLite table name managed by this repository."""

    @property
    def primary_key(self) -> str:
        """Return the primary key column name (defaults to 'id')."""
        return "id"

    @property
    def mapper(self) -> BaseRowMapper[TModel]:
        """Return the bound BaseRowMapper."""
        return self._mapper

    @property
    def session_manager(self) -> DatabaseSessionManager:
        """Return the bound DatabaseSessionManager."""
        return self._session

    def query(self, columns: tuple[str, ...] | None = None) -> QueryBuilder:
        """Create a new QueryBuilder scoped to this repository's table."""
        return QueryBuilder(self.table_name, columns=columns)

    def get(self, record_id: TID | str) -> TModel | None:
        """Retrieve a single domain record by primary key, or None if missing."""
        id_str = normalize_id(record_id)
        qb = self.query().where(self.primary_key, id_str).limit(1)
        results = self.find_where(qb)
        return results[0] if results else None

    def get_or_raise(self, record_id: TID | str) -> TModel:
        """Retrieve a single domain record by primary key or raise RecordNotFoundError."""
        record = self.get(record_id)
        if record is None:
            raise RecordNotFoundError(
                self.table_name,
                normalize_id(record_id),
                field=self.primary_key,
            )
        return record

    def get_by_urn(self, canonical_urn: str) -> TModel | None:
        """Retrieve a single domain record by its canonical_urn column."""
        clean_urn = clean_string(canonical_urn) or canonical_urn
        qb = self.query().where("canonical_urn", clean_urn).limit(1)
        results = self.find_where(qb)
        return results[0] if results else None

    def exists(self, record_id: TID | str) -> bool:
        """Check whether a record with the given primary key exists."""
        id_str = normalize_id(record_id)
        qb = self.query().where(self.primary_key, id_str)
        return self.count(qb) > 0

    def count(
        self,
        filters: QueryBuilder | Mapping[str, Any] | None = None,
    ) -> int:
        """Count rows matching optional filters or a QueryBuilder."""
        if isinstance(filters, QueryBuilder):
            qb = filters
        else:
            qb = self.query()
            if filters:
                for col, val in filters.items():
                    qb.where(col, val)

        sql, params = qb.build_count()
        try:
            with self._session.get_connection() as conn:
                row = conn.execute(sql, params).fetchone()
                return int(row[0]) if row is not None else 0
        except DatabaseError as err:
            raise RepositoryError(
                f"Failed to count records in '{self.table_name}': {err.message}",
                details={"table_name": self.table_name},
            ) from err

    def list_all(
        self,
        *,
        limit: int | None = None,
        offset: int | None = None,
        order_by: str | None = None,
        sort_order: SortOrder | str = SortOrder.ASC,
    ) -> list[TModel]:
        """List records from the table with optional sorting and pagination."""
        qb = self.query()
        sort_col = order_by if order_by is not None else self.primary_key
        qb.order_by(sort_col, sort_order)
        if limit is not None:
            qb.limit(limit)
        if offset is not None:
            qb.offset(offset)
        return self.find_where(qb)

    def find_by(self, **filters: Any) -> list[TModel]:
        """Find all records matching simple column equality filters."""
        qb = self.query()
        for col, val in filters.items():
            qb.where(col, val)
        qb.order_by(self.primary_key, SortOrder.ASC)
        return self.find_where(qb)

    def find_where(self, query_builder: QueryBuilder) -> list[TModel]:
        """Execute a configured QueryBuilder SELECT and hydrate domain models."""
        sql, params = query_builder.build_select()
        try:
            with self._session.get_connection() as conn:
                rows = conn.execute(sql, params).fetchall()
            return [self._mapper.from_row(row) for row in rows]
        except (DatabaseError, EntityMappingError) as err:
            raise RepositoryError(
                f"Query execution failed on '{self.table_name}': {err.message}",
                details={"table_name": self.table_name, "sql": sql},
            ) from err

    def insert(self, entity: TModel) -> TModel:
        """Strictly insert a new record, raising DuplicateRecordError on conflict."""
        try:
            row_dict = self._mapper.to_row(entity)
            sql = build_insert_sql(self.table_name, tuple(row_dict.keys()))
            with self._session.transaction() as conn:
                conn.execute(sql, row_dict)
            return entity
        except ConstraintViolationError as err:
            pk_val = row_dict.get(self.primary_key, "<unknown>")
            raise DuplicateRecordError(
                self.table_name,
                pk_val,
                details={"error": err.message},
            ) from err
        except (DatabaseError, EntityMappingError) as err:
            raise RepositoryError(
                f"Failed to insert record into '{self.table_name}': {err.message}",
                details={"table_name": self.table_name},
            ) from err

    def upsert(self, entity: TModel) -> TModel:
        """Insert or update a single domain record atomically."""
        self.upsert_many([entity])
        return entity

    def upsert_many(self, entities: Iterable[TModel]) -> int:
        """Atomically insert or update a batch of domain records."""
        entity_list = list(entities)
        if not entity_list:
            return 0

        try:
            row_dicts = [self._mapper.to_row(item) for item in entity_list]
            columns = tuple(row_dicts[0].keys())
            sql = build_upsert_sql(
                self.table_name,
                columns,
                primary_key=self.primary_key,
            )
            with self._session.transaction() as conn:
                conn.executemany(sql, row_dicts)
            return len(row_dicts)
        except (DatabaseError, EntityMappingError) as err:
            raise RepositoryError(
                f"Batch upsert failed on '{self.table_name}': {err.message}",
                details={"table_name": self.table_name, "count": len(entity_list)},
            ) from err

    def delete(self, record_id: TID | str) -> bool:
        """Delete a record by primary key."""
        id_str = normalize_id(record_id)
        qb = self.query().where(self.primary_key, id_str)
        sql, params = qb.build_delete()
        try:
            with self._session.transaction() as conn:
                cursor = conn.execute(sql, params)
                return cursor.rowcount > 0
        except DatabaseError as err:
            raise RepositoryError(
                f"Failed to delete record from '{self.table_name}': {err.message}",
                details={"table_name": self.table_name, "identifier": id_str},
            ) from err

    def delete_where(self, query_builder: QueryBuilder) -> int:
        """Delete all rows matching a QueryBuilder predicate."""
        sql, params = query_builder.build_delete()
        try:
            with self._session.transaction() as conn:
                cursor = conn.execute(sql, params)
                return int(cursor.rowcount)
        except DatabaseError as err:
            raise RepositoryError(
                f"Failed to delete records from '{self.table_name}': {err.message}",
                details={"table_name": self.table_name, "sql": sql},
            ) from err
