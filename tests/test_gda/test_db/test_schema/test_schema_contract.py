"""Path: tests/test_gda/test_db/test_schema/test_schema_contract.py

Interface contract verification test suite for gda.db.schema (__init__.py).

Operational Role:
    1:1 verification suite for src/gda/db/schema/__init__.py. Validates __all__
    exports, alphabetical sorting, and re-export identity for SchemaManager,
    Migration, and MIGRATION_REGISTRY.
"""

from __future__ import annotations

import pytest

import gda.db.schema as schema_pkg
from gda.db.schema.manager import SchemaManager
from gda.db.schema.migrations import MIGRATION_REGISTRY, Migration

__version__ = "1.0.0+build.1"


@pytest.mark.unit
def test_schema_package_facade_contract() -> None:
    """Verify gda.db.schema.__all__ is sorted and re-exports canonical symbols."""
    assert schema_pkg.__all__ == ["MIGRATION_REGISTRY", "Migration", "SchemaManager"]
    assert schema_pkg.__all__ == sorted(schema_pkg.__all__)
    assert schema_pkg.SchemaManager is SchemaManager
    assert schema_pkg.Migration is Migration
    assert schema_pkg.MIGRATION_REGISTRY is MIGRATION_REGISTRY
