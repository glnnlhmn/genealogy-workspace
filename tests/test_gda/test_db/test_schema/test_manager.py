"""Path: tests/test_gda/test_db/test_schema/test_manager.py

Unit, integration, and regression verification suite for SchemaManager.

Operational Role:
    1:1 verification suite for src/gda/db/schema/manager.py. Validates
    SchemaManager initialization, migration table bootstrap, version tracking,
    idempotent migration execution, and rollback on migration SQL failure.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

import gda.db.schema.manager as manager_mod
from gda.db.exceptions import DatabaseOperationalError
from gda.db.schema.manager import SchemaManager
from gda.db.schema.migrations import Migration
from gda.db.session import DatabaseSessionManager

__version__ = "1.0.0+build.1"


@pytest.mark.unit
def test_schema_manager_dunder_all_and_initialization() -> None:
    """Verify SchemaManager __all__, default session creation, and help() introspection."""
    assert manager_mod.__all__ == ["SchemaManager"]

    default_mgr = SchemaManager()
    assert isinstance(default_mgr.session_manager, DatabaseSessionManager)

    session = DatabaseSessionManager(db_path=":memory:")
    manager = SchemaManager(session_manager=session)
    assert manager.session_manager is session
    assert manager.get_current_version() == 0

    help_text = manager.help(as_str=True)
    assert help_text is not None
    assert "SchemaManager Public Directory" in help_text
    assert "migrate" in help_text
    assert "init_db" in help_text


@pytest.mark.integration
def test_schema_manager_migrate_and_idempotency(tmp_path: Path) -> None:
    """Verify init_db and migrate apply all 5 migrations once and skip on re-run."""
    db_file = tmp_path / "manager_migrate.db"
    session = DatabaseSessionManager(db_path=db_file)
    manager = SchemaManager(session_manager=session)

    applied_first = manager.init_db()
    assert applied_first == [1, 2, 3, 4, 5]
    assert manager.get_current_version() == 5

    applied_second = manager.migrate()
    assert applied_second == []
    assert manager.get_current_version() == 5


@pytest.mark.regression
def test_schema_manager_migration_failure_raises_operational_error(
    tmp_path: Path,
) -> None:
    """Verify corrupt SQL in a migration raises DatabaseOperationalError and rolls back."""
    db_file = tmp_path / "failing_mig.db"
    session = DatabaseSessionManager(db_path=db_file)
    manager = SchemaManager(session_manager=session)

    bad_migration = Migration(
        version=99,
        name="bad_migration",
        up_sql="INVALID SQL SYNTAX HERE;",
    )

    with patch("gda.db.schema.manager.MIGRATION_REGISTRY", [bad_migration]):
        with pytest.raises(DatabaseOperationalError) as exc_info:
            manager.migrate()

        assert "Migration 99 ('bad_migration') failed" in exc_info.value.message
        assert exc_info.value.details["version"] == 99

    assert manager.get_current_version() == 0
