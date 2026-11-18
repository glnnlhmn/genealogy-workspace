"""Path: src/gda/repository/errors.py

Domain repository exception hierarchy for the GDA persistence layer.

Operational Role:
    Defines structured, introspectable exceptions raised by SQLite repositories
    and query builders when persistence constraints, record lookups, or SQL
    identifier validations fail. Unifies RecordNotFoundError with
    gda.db.exceptions.RecordNotFoundError so callers catching either exception
    class handle missing-record errors uniformly.
"""

from __future__ import annotations

from typing import Any

from gda.core.errors import GenealogyDeskError
from gda.db.exceptions import RecordNotFoundError as DbRecordNotFoundError

__version__ = "1.0.0+build.3"

__all__ = [
    "DuplicateRecordError",
    "QueryValidationError",
    "RecordNotFoundError",
    "RepositoryError",
]


class RepositoryError(GenealogyDeskError):
    """Base exception for all GDA repository and query operations."""


class RecordNotFoundError(RepositoryError, DbRecordNotFoundError):
    """Raised when a requested record ID or URN cannot be found in a table."""

    def __init__(
        self,
        table_name: str,
        identifier: Any,
        *,
        field: str = "id",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize RecordNotFoundError with table and lookup context.

        Args:
            table_name: Target SQLite table name.
            identifier: The primary key or URN value that was not found.
            field: Column name queried (defaults to 'id').
            details: Optional supplemental diagnostic metadata.
        """
        merged_details: dict[str, Any] = {
            "table_name": table_name,
            "field": field,
            "identifier": str(identifier),
        }
        if details:
            merged_details.update(details)

        super().__init__(
            message=f"Record not found in '{table_name}' where {field}={identifier!r}.",
            error_code="ERR_DB_RECORD_NOT_FOUND",
            details=merged_details,
        )
        self.table_name = table_name
        self.field = field
        self.identifier = identifier


class DuplicateRecordError(RepositoryError):
    """Raised when a strict insert violates a primary key or unique constraint."""

    def __init__(
        self,
        table_name: str,
        identifier: Any,
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize DuplicateRecordError with table and colliding identifier.

        Args:
            table_name: Target SQLite table name.
            identifier: Colliding primary key or unique value.
            details: Optional supplemental diagnostic metadata.
        """
        merged_details: dict[str, Any] = {
            "table_name": table_name,
            "identifier": str(identifier),
        }
        if details:
            merged_details.update(details)

        super().__init__(
            f"Duplicate record in '{table_name}' for identifier {identifier!r}.",
            details=merged_details,
        )
        self.table_name = table_name
        self.identifier = identifier


class QueryValidationError(RepositoryError):
    """Raised when a SQL identifier, filter operator, or pagination bound is invalid."""
