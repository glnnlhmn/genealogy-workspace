"""Path: src/gda/repository/query.py

Parameterized SQLite query builder and SQL identifier validation utilities.

Operational Role:
    Provides safe, composable SELECT, COUNT, DELETE, and UPSERT SQL construction
    with strict regex validation on table and column identifiers and positional
    parameter binding for all user/domain values.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from enum import StrEnum
from typing import Any

from gda.core.introspectable import IntrospectableMixin
from gda.repository.errors import QueryValidationError

__version__ = "1.0.0+build.1"

__all__ = [
    "FilterOp",
    "QueryBuilder",
    "SortOrder",
    "build_insert_sql",
    "build_upsert_sql",
    "validate_sql_identifier",
]

_SQL_IDENTIFIER_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


def validate_sql_identifier(identifier: str) -> str:
    """Validate that a SQL table or column name is a safe identifier.

    Args:
        identifier: Candidate table or column name string.

    Returns:
        The validated identifier string.

    Raises:
        QueryValidationError: If the identifier is empty, non-string, or
             fails the strict alphanumeric/underscore pattern.
    """
    if not isinstance(identifier, str) or not _SQL_IDENTIFIER_RE.match(identifier):
        raise QueryValidationError(
            f"Invalid or unsafe SQL identifier: {identifier!r}.",
            details={"identifier": identifier},
        )
    return identifier


class SortOrder(StrEnum):
    """SQL ORDER BY direction."""

    ASC = "ASC"
    DESC = "DESC"


class FilterOp(StrEnum):
    """Supported SQL WHERE comparison operators."""

    EQ = "="
    NE = "!="
    LT = "<"
    LE = "<="
    GT = ">"
    GE = ">="
    LIKE = "LIKE"
    IN = "IN"
    IS_NULL = "IS NULL"
    IS_NOT_NULL = "IS NOT NULL"


class QueryBuilder(IntrospectableMixin):
    """Composable, parameterized SQLite query builder for repository lookups."""

    def __init__(
        self,
        table_name: str,
        columns: Sequence[str] | None = None,
    ) -> None:
        """Initialize QueryBuilder for a target table.

        Args:
            table_name: Validated SQLite table name.
            columns: Optional sequence of column names to project. Defaults
                to all columns ('*') when omitted or None.

        Raises:
            QueryValidationError: If table_name or any column name is invalid,
                or if columns is an empty sequence.
        """
        self._table_name = validate_sql_identifier(table_name)
        if columns is None:
            self._columns: tuple[str, ...] = ()
        else:
            if len(columns) == 0:
                raise QueryValidationError(
                    "Projected columns sequence cannot be empty when specified.",
                    details={"table_name": self._table_name},
                )
            self._columns = tuple(validate_sql_identifier(col) for col in columns)

        self._where_clauses: list[str] = []
        self._params: list[Any] = []
        self._order_by: list[str] = []
        self._limit_val: int | None = None
        self._offset_val: int | None = None

    @property
    def table_name(self) -> str:
        """Return target SQLite table name."""
        return self._table_name

    @property
    def columns(self) -> tuple[str, ...]:
        """Return projected column names (empty tuple represents '*')."""
        return self._columns

    def where(
        self,
        column: str,
        value: Any = None,
        op: FilterOp | str = FilterOp.EQ,
    ) -> QueryBuilder:
        """Append a parameterized WHERE condition.

        Args:
            column: Validated column name.
            value: Parameter value to bind (ignored for IS_NULL/IS_NOT_NULL,
                must be a non-empty sequence for IN).
            op: Comparison operator (FilterOp or string representation).

        Returns:
            Self for fluent chaining.

        Raises:
            QueryValidationError: On invalid column, unsupported operator,
                or invalid IN value sequence.
        """
        col = validate_sql_identifier(column)
        try:
            resolved_op = op if isinstance(op, FilterOp) else FilterOp(op)
        except ValueError as err:
            raise QueryValidationError(
                f"Unsupported filter operator: {op!r}.",
                details={"column": col, "operator": str(op)},
            ) from err

        if resolved_op in (FilterOp.IS_NULL, FilterOp.IS_NOT_NULL):
            self._where_clauses.append(f"{col} {resolved_op.value}")
            return self

        if resolved_op is FilterOp.IN:
            if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
                raise QueryValidationError(
                    f"Operator IN for column '{col}' requires a non-string sequence.",
                    details={"column": col},
                )
            return self.where_in(col, value)

        self._where_clauses.append(f"{col} {resolved_op.value} ?")
        self._params.append(value)
        return self

    def where_in(self, column: str, values: Sequence[Any]) -> QueryBuilder:
        """Append a parameterized `column IN (?, ...)` condition.

        Args:
            column: Validated column name.
            values: Non-empty sequence of parameter values.

        Returns:
            Self for fluent chaining.

        Raises:
            QueryValidationError: If values is empty or column is invalid.
        """
        col = validate_sql_identifier(column)
        if not values:
            raise QueryValidationError(
                f"Values for WHERE IN on column '{col}' cannot be empty.",
                details={"column": col},
            )
        placeholders = ", ".join("?" for _ in values)
        self._where_clauses.append(f"{col} IN ({placeholders})")
        self._params.extend(values)
        return self

    def where_null(self, column: str, *, is_null: bool = True) -> QueryBuilder:
        """Append an `IS NULL` or `IS NOT NULL` condition.

        Args:
            column: Validated column name.
            is_null: True for IS NULL, False for IS NOT NULL.

        Returns:
            Self for fluent chaining.
        """
        op = FilterOp.IS_NULL if is_null else FilterOp.IS_NOT_NULL
        return self.where(column, op=op)

    def order_by(
        self,
        column: str,
        direction: SortOrder | str = SortOrder.ASC,
    ) -> QueryBuilder:
        """Append an ORDER BY clause column and sort direction.

        Args:
            column: Validated column name.
            direction: SortOrder.ASC or SortOrder.DESC (case-insensitive string allowed).

        Returns:
            Self for fluent chaining.

        Raises:
            QueryValidationError: On invalid column or sort direction.
        """
        col = validate_sql_identifier(column)
        norm_dir = direction.upper() if isinstance(direction, str) else direction.value
        try:
            resolved_dir = SortOrder(norm_dir)
        except ValueError as err:
            raise QueryValidationError(
                f"Invalid sort direction: {direction!r}.",
                details={"column": col, "direction": str(direction)},
            ) from err

        self._order_by.append(f"{col} {resolved_dir.value}")
        return self

    def limit(self, count: int) -> QueryBuilder:
        """Set a positive integer LIMIT on the query.

        Args:
            count: Maximum number of rows to return (must be >= 0).

        Returns:
            Self for fluent chaining.

        Raises:
            QueryValidationError: If count is negative or not an int.
        """
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            raise QueryValidationError(
                f"LIMIT must be a non-negative integer, got {count!r}.",
                details={"limit": count},
            )
        self._limit_val = count
        return self

    def offset(self, start: int) -> QueryBuilder:
        """Set a non-negative integer OFFSET on the query.

        Args:
            start: Number of initial rows to skip (must be >= 0).

        Returns:
            Self for fluent chaining.

        Raises:
            QueryValidationError: If start is negative or not an int.
        """
        if isinstance(start, bool) or not isinstance(start, int) or start < 0:
            raise QueryValidationError(
                f"OFFSET must be a non-negative integer, got {start!r}.",
                details={"offset": start},
            )
        self._offset_val = start
        return self

    def _compile_where(self) -> str:
        """Compile accumulated WHERE conditions into a SQL fragment."""
        if not self._where_clauses:
            return ""
        return " WHERE " + " AND ".join(self._where_clauses)

    def build_select(self) -> tuple[str, tuple[Any, ...]]:
        """Compile a parameterized SELECT query and its bound parameter tuple.

        Returns:
            Tuple of (sql_string, params_tuple).

        Raises:
            QueryValidationError: If OFFSET is specified without a LIMIT.
        """
        if self._offset_val is not None and self._limit_val is None:
            raise QueryValidationError(
                "OFFSET cannot be specified without a corresponding LIMIT in SQLite.",
                details={"table_name": self._table_name, "offset": self._offset_val},
            )

        projection = ", ".join(self._columns) if self._columns else "*"
        sql = f"SELECT {projection} FROM {self._table_name}{self._compile_where()}"
        params: list[Any] = list(self._params)

        if self._order_by:
            sql += " ORDER BY " + ", ".join(self._order_by)

        if self._limit_val is not None:
            sql += " LIMIT ?"
            params.append(self._limit_val)

        if self._offset_val is not None:
            sql += " OFFSET ?"
            params.append(self._offset_val)

        return sql + ";", tuple(params)

    def build_count(self) -> tuple[str, tuple[Any, ...]]:
        """Compile a parameterized SELECT COUNT(*) query and its parameter tuple.

        Returns:
            Tuple of (sql_string, params_tuple).
        """
        sql = f"SELECT COUNT(*) FROM {self._table_name}{self._compile_where()};"
        return sql, tuple(self._params)

    def build_delete(self, *, allow_unconditional: bool = False) -> tuple[str, tuple[Any, ...]]:
        """Compile a parameterized DELETE query and its parameter tuple.

        Args:
            allow_unconditional: Whether to permit DELETE without a WHERE clause.

        Returns:
            Tuple of (sql_string, params_tuple).

        Raises:
            QueryValidationError: If no WHERE clauses are present and
                allow_unconditional is False.
        """
        if not self._where_clauses and not allow_unconditional:
            raise QueryValidationError(
                f"Refusing to build unconditional DELETE on '{self._table_name}' "
                "without explicit allow_unconditional=True.",
                details={"table_name": self._table_name},
            )
        sql = f"DELETE FROM {self._table_name}{self._compile_where()};"
        return sql, tuple(self._params)


def build_insert_sql(table_name: str, columns: Sequence[str]) -> str:
    """Build a strict parameterized SQLite INSERT statement.

    Args:
        table_name: Validated SQLite table name.
        columns: Non-empty sequence of column identifiers.

    Returns:
        Parameterized INSERT SQL string using `:column` named placeholders.

    Raises:
        QueryValidationError: If table_name or columns are invalid/empty.
    """
    tbl = validate_sql_identifier(table_name)
    if not columns:
        raise QueryValidationError(
            f"Cannot build INSERT SQL for '{tbl}' with empty column list.",
            details={"table_name": tbl},
        )
    valid_cols = [validate_sql_identifier(col) for col in columns]
    col_list = ", ".join(valid_cols)
    placeholders = ", ".join(f":{col}" for col in valid_cols)
    return f"INSERT INTO {tbl} ({col_list}) VALUES ({placeholders});"


def build_upsert_sql(
    table_name: str,
    columns: Sequence[str],
    primary_key: str = "id",
) -> str:
    """Build a deterministic SQLite INSERT ... ON CONFLICT DO UPDATE statement.

    Args:
        table_name: Validated SQLite table name.
        columns: Non-empty sequence of column identifiers.
        primary_key: Conflict target primary key column (defaults to 'id').

    Returns:
        Parameterized UPSERT SQL string using `:column` named placeholders.

    Raises:
        QueryValidationError: If identifiers are invalid, columns is empty,
            or primary_key is not included in columns.
    """
    tbl = validate_sql_identifier(table_name)
    pk = validate_sql_identifier(primary_key)
    if not columns:
        raise QueryValidationError(
            f"Cannot build UPSERT SQL for '{tbl}' with empty column list.",
            details={"table_name": tbl},
        )
    valid_cols = [validate_sql_identifier(col) for col in columns]
    if pk not in valid_cols:
        raise QueryValidationError(
            f"Primary key '{pk}' must be present in columns for UPSERT on '{tbl}'.",
            details={"table_name": tbl, "primary_key": pk, "columns": valid_cols},
        )

    col_list = ", ".join(valid_cols)
    placeholders = ", ".join(f":{col}" for col in valid_cols)
    non_pk_cols = [col for col in valid_cols if col != pk]

    if not non_pk_cols:
        return (
            f"INSERT INTO {tbl} ({col_list}) VALUES ({placeholders}) ON CONFLICT({pk}) DO NOTHING;"
        )

    update_assignments = ", ".join(f"{col} = excluded.{col}" for col in non_pk_cols)
    return (
        f"INSERT INTO {tbl} ({col_list}) VALUES ({placeholders}) "
        f"ON CONFLICT({pk}) DO UPDATE SET {update_assignments};"
    )
