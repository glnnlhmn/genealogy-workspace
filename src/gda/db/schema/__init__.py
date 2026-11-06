"""Path: src/gda/db/schema/__init__.py

Schema management facade for GDA persistence layer.

Operational Role:
    Exports SchemaManager and Migration dataclass for public consumer access.
"""

from __future__ import annotations

from gda.db.schema.manager import SchemaManager
from gda.db.schema.migrations import MIGRATION_REGISTRY, Migration

__version__ = "1.0.0+build.3"

__all__ = ["MIGRATION_REGISTRY", "Migration", "SchemaManager"]
