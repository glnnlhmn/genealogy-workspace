"""Path: src/gda/db/__init__.py

Database persistence, schema migration, and entity mapping facade for GDA.

Operational Role:
    Exposes the canonical public API for the gda.db package, including
    DatabaseSessionManager, SchemaManager, MIGRATION_REGISTRY, all 6 core
    entity RowMappers, get_mapper, and the complete DatabaseError exception
    hierarchy.
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
    SchemaMigrationError,
    TransactionError,
)
from gda.db.mapper import (
    BaseRowMapper,
    FactRowMapper,
    FamilyRowMapper,
    IndividualRowMapper,
    LocationRowMapper,
    OrganizationRowMapper,
    SiteRowMapper,
    get_mapper,
)
from gda.db.schema import MIGRATION_REGISTRY, Migration, SchemaManager
from gda.db.session import DatabaseSessionManager

__version__ = "1.0.0+build.5"

__all__ = [
    "BaseRowMapper",
    "ConnectionTimeoutError",
    "ConstraintViolationError",
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
    "OrganizationRowMapper",
    "RecordNotFoundError",
    "SchemaManager",
    "SchemaMigrationError",
    "SiteRowMapper",
    "TransactionError",
    "get_mapper",
]
