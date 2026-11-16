"""Path: src/gda/db/schema/migrations/__init__.py

Migration registry and automated script discovery for GDA DB schema.

Operational Role:
    Aggregates modular versioned DDL migration modules (v001_places through
    v005_indexes) and exports the ordered MIGRATION_REGISTRY.
"""

from __future__ import annotations

from typing import NamedTuple

from gda.db.schema.migrations import (
    v001_places,
    v002_organizations,
    v003_personas,
    v004_facts,
    v005_indexes,
)

__version__ = "1.0.0+build.6"

__all__ = [
    "MIGRATION_REGISTRY",
    "Migration",
    "v001_places",
    "v002_organizations",
    "v003_personas",
    "v004_facts",
    "v005_indexes",
]


class Migration(NamedTuple):
    """Immutable representation of a versioned schema migration script."""

    version: int
    name: str
    up_sql: str


MIGRATION_REGISTRY: list[Migration] = [
    Migration(
        version=v001_places.VERSION,
        name=v001_places.NAME,
        up_sql=v001_places.UP_SQL,
    ),
    Migration(
        version=v002_organizations.VERSION,
        name=v002_organizations.NAME,
        up_sql=v002_organizations.UP_SQL,
    ),
    Migration(
        version=v003_personas.VERSION,
        name=v003_personas.NAME,
        up_sql=v003_personas.UP_SQL,
    ),
    Migration(
        version=v004_facts.VERSION,
        name=v004_facts.NAME,
        up_sql=v004_facts.UP_SQL,
    ),
    Migration(
        version=v005_indexes.VERSION,
        name=v005_indexes.NAME,
        up_sql=v005_indexes.UP_SQL,
    ),
]
