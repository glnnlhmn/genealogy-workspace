"""Path: tests/test_gda/test_db/test_schema.py

Behavioral contract and verification test suite for SchemaManager and DDL migrations.

Validates migration table creation, version discovery, sequential migration execution,
idempotency, schema completeness across domain entities and sources, foreign keys, and rollback.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from gda.db.exceptions import DatabaseOperationalError
from gda.db.schema import Migration, SchemaManager
from gda.db.session import DatabaseSessionManager

__version__ = "1.0.0+build.5"


# ==============================================================================
# GROUP 1: INITIALIZATION & INTROSPECTION CONTRACTS
# ==============================================================================


@pytest.mark.unit
def test_schema_manager_initialization() -> None:
    """Verify SchemaManager binds to session manager with baseline version 0."""
    session = DatabaseSessionManager(db_path=":memory:")
    manager = SchemaManager(session_manager=session)
    assert manager.session_manager is session
    assert manager.get_current_version() == 0


@pytest.mark.unit
def test_schema_manager_introspectable_help() -> None:
    """Verify IntrospectableMixin .help() renders public directory output."""
    session = DatabaseSessionManager(db_path=":memory:")
    manager = SchemaManager(session_manager=session)
    help_text = manager.help(as_str=True)
    assert help_text is not None
    assert "SchemaManager Public Directory" in help_text
    assert "migrate" in help_text
    assert "init_db" in help_text


# ==============================================================================
# GROUP 2: DDL MIGRATION EXECUTION & CANONICAL TABLES
# ==============================================================================


@pytest.mark.integration
def test_schema_manager_init_db_creates_canonical_tables(tmp_path: Path) -> None:
    """Verify init_db provisions tables across all 3 migrations (core, sources, indexes)."""
    db_file = tmp_path / "schema_init.db"
    session = DatabaseSessionManager(db_path=db_file)
    manager = SchemaManager(session_manager=session)

    applied = manager.init_db()
    assert applied == [1, 2, 3]
    assert manager.get_current_version() == 3

    with session.get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = {row[0] for row in cursor.fetchall()}
            expected_tables = {
                "schema_migrations",
                "locations",
                "sites",
                "individuals",
                "families",
                "facts",
                "source_records",
                "individual_family_xrefs",
                "fact_participant_xrefs",
                "media_xrefs",
            }
            assert expected_tables.issubset(tables)

            cursor.execute("SELECT name FROM sqlite_master WHERE type='index';")
            indexes = {row[0] for row in cursor.fetchall()}
            expected_indexes = {
                "idx_individuals_surname",
                "idx_individuals_given_name",
                "idx_individuals_urn",
                "idx_individuals_birth_year",
                "idx_individuals_death_year",
                "idx_individuals_birth_sort",
                "idx_families_urn",
                "idx_facts_subject",
                "idx_facts_type",
                "idx_facts_year",
                "idx_facts_date_sort",
                "idx_locations_parent",
                "idx_sites_location",
                "idx_ind_fam_xref_subject",
                "idx_fact_part_xref_ind",
                "idx_source_records_urn",
                "idx_source_records_category",
                "idx_source_records_repo",
                "idx_media_xref_entity",
            }
            assert expected_indexes.issubset(indexes)
        finally:
            cursor.close()


@pytest.mark.integration
def test_schema_manager_migrate_idempotency(tmp_path: Path) -> None:
    """Verify running migrate multiple times skips already applied migrations."""
    db_file = tmp_path / "idempotent.db"
    session = DatabaseSessionManager(db_path=db_file)
    manager = SchemaManager(session_manager=session)

    applied_first = manager.migrate()
    assert applied_first == [1, 2, 3]

    applied_second = manager.migrate()
    assert applied_second == []
    assert manager.get_current_version() == 3


# ==============================================================================
# GROUP 3: RELATIONAL INTEGRITY & FOREIGN KEY ENFORCEMENT
# ==============================================================================


@pytest.mark.integration
def test_schema_manager_location_parent_foreign_key_on_delete_set_null(
    tmp_path: Path,
) -> None:
    """Verify deleting a parent location sets child parent_id to NULL."""
    db_file = tmp_path / "fk_test.db"
    session = DatabaseSessionManager(db_path=db_file)
    manager = SchemaManager(session_manager=session)
    manager.init_db()

    with session.transaction() as tx:
        tx.execute(
            """
            INSERT INTO locations (id, canonical_urn, name, category, created_at, updated_at)
            VALUES (
                'LOC-000001', 'urn:gda:loc:us:nh', 'New Hampshire',
                'STATOID', '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z'
            );
            """
        )
        tx.execute(
            """
            INSERT INTO locations (
                id, canonical_urn, name, category, parent_id, created_at, updated_at
            ) VALUES (
                'LOC-000002', 'urn:gda:loc:us:nh:merrimack', 'Merrimack County',
                'COUNTY_EQUIVALENT', 'LOC-000001', '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z'
            );
            """
        )

    with session.transaction() as tx:
        tx.execute("DELETE FROM locations WHERE id = 'LOC-000001';")

    with session.get_connection() as conn:
        child = conn.execute(
            "SELECT parent_id FROM locations WHERE id = 'LOC-000002';"
        ).fetchone()
        assert child["parent_id"] is None


# ==============================================================================
# GROUP 4: DEFENSIVE ERROR BOUNDARIES & MIGRATION FAILURES
# ==============================================================================


@pytest.mark.regression
def test_schema_manager_migration_failure_raises_operational_error(
    tmp_path: Path,
) -> None:
    """Verify corrupt SQL in migration triggers DatabaseOperationalError and rollback."""
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
