"""Path: src/gda/db/__init__.py

Public package exports and facade for GDA persistence layer.
"""

from __future__ import annotations

from gda.db.exceptions import (
    ConnectionTimeoutError,
    ConstraintViolationError,
    DatabaseConnectionError,
    DatabaseError,
    DatabaseOperationalError,
    DirtyStateError,
    EntityMappingError,
    RecordNotFoundError,
    TransactionError,
)
from gda.db.mapper import (
    BaseRowMapper,
    FactRowMapper,
    FamilyRowMapper,
    IndividualRowMapper,
    LocationRowMapper,
    SiteRowMapper,
    get_mapper,
)
from gda.db.schema import MIGRATION_REGISTRY, Migration, SchemaManager
from gda.db.session import DatabaseConfig, DatabaseSessionManager

__version__ = "1.0.0+build.2"

__all__ = [
    "BaseRowMapper",
    "ConnectionTimeoutError",
    "ConstraintViolationError",
    "DatabaseConfig",
    "DatabaseConnectionError",
    "DatabaseError",
    "DatabaseOperationalError",
    "DatabaseSessionManager",
    "DirtyStateError",
    "EntityMappingError",
    "FactRowMapper",
    "FamilyRowMapper",
    "IndividualRowMapper",
    "LocationRowMapper",
    "MIGRATION_REGISTRY",
    "Migration",
    "RecordNotFoundError",
    "SchemaManager",
    "SiteRowMapper",
    "TransactionError",
    "get_mapper",
]
