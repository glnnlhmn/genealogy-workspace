"""Path: src/gda/db/exceptions.py

Database persistence exception hierarchy for the Genealogy Digital Archive.

Defines specialized persistence and database error types rooted in the canonical
GenealogyDeskError hierarchy. Every exception provides a deterministic error_code,
human-readable message, optional structured details, exit_code, and UTC timestamping.
"""

from __future__ import annotations

from typing import Any

from gda.core.errors import GenealogyDeskError

__version__ = "1.0.0+build.2"

__all__ = [
    "ConnectionTimeoutError",
    "ConstraintViolationError",
    "DatabaseConnectionError",
    "DatabaseError",
    "DatabaseOperationalError",
    "DirtyStateError",
    "EntityMappingError",
    "RecordNotFoundError",
    "SchemaMigrationError",
    "TransactionError",
]


class DatabaseError(GenealogyDeskError):
    """Base exception for all database and persistence operations."""

    def __init__(
        self,
        message: str = "An unexpected database error occurred.",
        error_code: str = "ERR_DATABASE",
        details: dict[str, Any] | None = None,
        exit_code: int = 1,
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code,
            details=details,
            exit_code=exit_code,
        )


class DatabaseConnectionError(DatabaseError):
    """Raised when a database connection cannot be established or is unexpectedly lost."""

    def __init__(
        self,
        message: str = "Failed to establish or maintain database connection.",
        error_code: str = "ERR_DB_CONNECTION",
        details: dict[str, Any] | None = None,
        exit_code: int = 1,
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code,
            details=details,
            exit_code=exit_code,
        )


class ConnectionTimeoutError(DatabaseConnectionError):
    """Raised when a database operation exceeds the configured busy timeout under lock contention."""

    def __init__(
        self,
        message: str = "Database operation timed out under lock contention.",
        error_code: str = "ERR_DB_TIMEOUT",
        details: dict[str, Any] | None = None,
        exit_code: int = 1,
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code,
            details=details,
            exit_code=exit_code,
        )


class TransactionError(DatabaseError):
    """Raised when a transaction or savepoint fails to begin, commit, or roll back."""

    def __init__(
        self,
        message: str = "Database transaction failed.",
        error_code: str = "ERR_DB_TRANSACTION",
        details: dict[str, Any] | None = None,
        exit_code: int = 1,
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code,
            details=details,
            exit_code=exit_code,
        )


class ConstraintViolationError(DatabaseError):
    """Raised when an INSERT, UPDATE, or DELETE violates UNIQUE, FOREIGN KEY, or CHECK constraints."""

    def __init__(
        self,
        message: str = "Database integrity constraint violation.",
        error_code: str = "ERR_DB_CONSTRAINT",
        details: dict[str, Any] | None = None,
        exit_code: int = 1,
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code,
            details=details,
            exit_code=exit_code,
        )


class RecordNotFoundError(DatabaseError):
    """Raised when a requested entity record does not exist in the persistence store."""

    def __init__(
        self,
        message: str = "Requested database record was not found.",
        error_code: str = "ERR_DB_RECORD_NOT_FOUND",
        details: dict[str, Any] | None = None,
        exit_code: int = 1,
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code,
            details=details,
            exit_code=exit_code,
        )


class SchemaMigrationError(DatabaseError):
    """Raised when schema initialization, DDL execution, or version migration fails."""

    def __init__(
        self,
        message: str = "Database schema migration failed.",
        error_code: str = "ERR_DB_MIGRATION",
        details: dict[str, Any] | None = None,
        exit_code: int = 1,
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code,
            details=details,
            exit_code=exit_code,
        )


class DatabaseOperationalError(DatabaseError):
    """Raised when the database driver encounters a syntax, table, or I/O operational error."""

    def __init__(
        self,
        message: str = "Database driver operational error.",
        error_code: str = "ERR_DB_OPERATIONAL",
        details: dict[str, Any] | None = None,
        exit_code: int = 1,
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code,
            details=details,
            exit_code=exit_code,
        )


class EntityMappingError(DatabaseError):
    """Raised when a database row cannot be mapped to or from a domain entity model."""

    def __init__(
        self,
        message: str = "Failed to map database row to domain entity.",
        error_code: str = "ERR_DB_ENTITY_MAPPING",
        details: dict[str, Any] | None = None,
        exit_code: int = 1,
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code,
            details=details,
            exit_code=exit_code,
        )


class DirtyStateError(DatabaseError):
    """Raised when an operation is blocked due to unpersisted dirty state conflicts."""

    def __init__(
        self,
        message: str = "Operation blocked by unpersisted dirty state conflict.",
        error_code: str = "ERR_DB_DIRTY_STATE",
        details: dict[str, Any] | None = None,
        exit_code: int = 1,
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code,
            details=details,
            exit_code=exit_code,
        )
