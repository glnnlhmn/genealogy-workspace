"""Path: src/gda/db/exceptions.py

Database exception hierarchy and error translation contracts for GDA DB.

Operational Role:
    Defines the persistence error taxonomy derived from GenealogyDeskError,
    providing structured error codes, diagnostic metadata serialization, and
    driver-level translation boundaries for SQLite, Pydantic, and repository tiers.

Classes:
    DatabaseError: Root exception for all database and persistence layer failures.
    DatabaseConnectionError: Raised when connection acquisition or lifecycle fails.
    ConnectionTimeoutError: Raised when database lock contention exceeds timeouts.
    TransactionError: Raised when transaction execution, commit, or rollback fails.
    ConstraintViolationError: Raised on relational, unique, or foreign key violations.
    RecordNotFoundError: Raised when an expected database record cannot be found.
    SchemaMigrationError: Raised when DDL execution, initialization, or migration fails.
    DatabaseOperationalError: Raised on driver-level syntax or operational failures.
    EntityMappingError: Raised when row-to-model or model-to-row deserialization fails.
    DirtyStateError: Raised when dirty-tracking descriptors or entity states conflict.
"""

from __future__ import annotations

from typing import Any

from gda.core.errors import GenealogyDeskError

__version__ = "1.0.0+build.1"


# ==============================================================================
# SECTION 1: ROOT DATABASE EXCEPTION
# ==============================================================================


class DatabaseError(GenealogyDeskError):
    """Root base exception for all database engine and persistence layer failures."""

    def __init__(
        self,
        message: str = "An unexpected database error occurred.",
        error_code: str = "ERR_DATABASE",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize DatabaseError.

        Args:
            message: Human-readable diagnostic description of the failure.
            error_code: Canonical uppercase error identifier string.
            details: Optional dictionary carrying contextual diagnostic state.
        """
        super().__init__(message=message, error_code=error_code, details=details)


# ==============================================================================
# SECTION 2: CONNECTION & CONCURRENCY EXCEPTIONS
# ==============================================================================


class DatabaseConnectionError(DatabaseError):
    """Raised when establishing, acquiring, or maintaining a database connection fails."""

    def __init__(
        self,
        message: str = "Failed to establish or maintain database connection.",
        error_code: str = "ERR_DB_CONNECTION",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize DatabaseConnectionError."""
        super().__init__(message=message, error_code=error_code, details=details)


class ConnectionTimeoutError(DatabaseConnectionError):
    """Raised when database connection acquisition times out under lock contention."""

    def __init__(
        self,
        message: str = "Database connection timed out under lock contention.",
        error_code: str = "ERR_DB_TIMEOUT",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize ConnectionTimeoutError."""
        super().__init__(message=message, error_code=error_code, details=details)


# ==============================================================================
# SECTION 3: TRANSACTION & REPOSITORY CONSTRAINTS
# ==============================================================================


class TransactionError(DatabaseError):
    """Raised when a transaction block fails, conflicts, or cannot be finalized."""

    def __init__(
        self,
        message: str = "Database transaction failed or was aborted.",
        error_code: str = "ERR_DB_TRANSACTION",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize TransactionError."""
        super().__init__(message=message, error_code=error_code, details=details)


class ConstraintViolationError(DatabaseError):
    """Raised when a database unique, foreign key, or check constraint is violated."""

    def __init__(
        self,
        message: str = "Database constraint violation detected.",
        error_code: str = "ERR_DB_CONSTRAINT",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize ConstraintViolationError."""
        super().__init__(message=message, error_code=error_code, details=details)


class RecordNotFoundError(DatabaseError):
    """Raised when an expected database record or primary key does not exist."""

    def __init__(
        self,
        message: str = "Requested database record was not found.",
        error_code: str = "ERR_DB_RECORD_NOT_FOUND",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize RecordNotFoundError."""
        super().__init__(message=message, error_code=error_code, details=details)


# ==============================================================================
# SECTION 4: SCHEMA, DDL & DRIVER OPERATIONS
# ==============================================================================


class SchemaMigrationError(DatabaseError):
    """Raised when physical schema generation, DDL, or migration runner fails."""

    def __init__(
        self,
        message: str = "Database schema initialization or migration failed.",
        error_code: str = "ERR_DB_MIGRATION",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize SchemaMigrationError."""
        super().__init__(message=message, error_code=error_code, details=details)


class DatabaseOperationalError(DatabaseError):
    """Raised when low-level driver execution, parameter binding, or SQL syntax fails."""

    def __init__(
        self,
        message: str = "Database driver operational error occurred.",
        error_code: str = "ERR_DB_OPERATIONAL",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize DatabaseOperationalError."""
        super().__init__(message=message, error_code=error_code, details=details)


# ==============================================================================
# SECTION 5: MODEL MAPPING & PERSISTENCE STATE
# ==============================================================================


class EntityMappingError(DatabaseError):
    """Raised when tabular row data fails deserialization into a domain model."""

    def __init__(
        self,
        message: str = "Failed to map database row payload to domain entity model.",
        error_code: str = "ERR_DB_ENTITY_MAPPING",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize EntityMappingError."""
        super().__init__(message=message, error_code=error_code, details=details)


class DirtyStateError(DatabaseError):
    """Raised when dirty tracking, version stamp, or uncommitted entity state conflicts."""

    def __init__(
        self,
        message: str = "Entity dirty state conflict detected during persistence operation.",
        error_code: str = "ERR_DB_DIRTY_STATE",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize DirtyStateError."""
        super().__init__(message=message, error_code=error_code, details=details)
