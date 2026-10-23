"""Path: src/gda/db/schema/migrations/__init__.py

Migration registry and automated script discovery for GDA DB schema.

Operational Role:
    Aggregates versioned DDL migration modules and exports the ordered MIGRATION_REGISTRY.
"""

from __future__ import annotations

from typing import NamedTuple

from gda.db.schema.migrations import v001_core, v002_sources, v003_indexes

__version__ = "1.0.0+build.3"


class Migration(NamedTuple):
    """Immutable representation of a versioned schema migration script."""

    version: int
    name: str
    up_sql: str


MIGRATION_REGISTRY: list[Migration] = [
    Migration(
        version=v001_core.VERSION,
        name=v001_core.NAME,
        up_sql=v001_core.UP_SQL,
    ),
    Migration(
        version=v002_sources.VERSION,
        name=v002_sources.NAME,
        up_sql=v002_sources.UP_SQL,
    ),
    Migration(
        version=v003_indexes.VERSION,
        name=v003_indexes.NAME,
        up_sql=v003_indexes.UP_SQL,
    ),
]
