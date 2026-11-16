"""Path: tests/test_gda/test_db/test_schema/test_migrations.py

Package-level DDL contract and relational verification suite for gda.db.schema.migrations.

Operational Role:
    1:1 package-level verification suite for src/gda/db/schema/migrations/
    (__init__.py, v001_places.py, v002_organizations.py, v003_personas.py,
    v004_facts.py, and v005_indexes.py). Validates module exports, migration
    ordering, flattened analytical column definitions, B-Tree index coverage,
    and SQLite foreign key enforcement across all 6 core entity tables.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import gda.db.schema.migrations as migrations_pkg
from gda.db.exceptions import ConstraintViolationError
from gda.db.schema import MIGRATION_REGISTRY, SchemaManager
from gda.db.schema.migrations import (
    v001_places,
    v002_organizations,
    v003_personas,
    v004_facts,
    v005_indexes,
)
from gda.db.session import DatabaseSessionManager

__version__ = "1.0.0+build.1"


@pytest.mark.unit
def test_migrations_package_and_module_exports() -> None:
    """Verify __all__ and version metadata across migrations/__init__.py and v001..v005."""
    assert migrations_pkg.__all__ == [
        "MIGRATION_REGISTRY",
        "Migration",
        "v001_places",
        "v002_organizations",
        "v003_personas",
        "v004_facts",
        "v005_indexes",
    ]
    assert migrations_pkg.__all__ == sorted(migrations_pkg.__all__)
    assert [m.version for m in MIGRATION_REGISTRY] == [1, 2, 3, 4, 5]

    for mod, expected_ver in (
        (v001_places, 1),
        (v002_organizations, 2),
        (v003_personas, 3),
        (v004_facts, 4),
        (v005_indexes, 5),
    ):
        assert mod.__all__ == ["NAME", "UP_SQL", "VERSION"]
        assert mod.VERSION == expected_ver
        assert isinstance(mod.NAME, str) and mod.NAME
        assert isinstance(mod.UP_SQL, str) and "CREATE" in mod.UP_SQL


@pytest.mark.integration
def test_migrations_provision_flattened_analytical_columns_and_indexes(
    tmp_path: Path,
) -> None:
    """Verify v001..v005 create all 6 entity tables, flattened columns, and B-Tree indexes."""
    db_file = tmp_path / "migrations_ddl.db"
    session = DatabaseSessionManager(db_path=db_file)
    SchemaManager(session_manager=session).init_db()

    with session.get_connection() as conn:
        cursor = conn.cursor()
        try:
            tables = {
                r[0]
                for r in cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table';"
                ).fetchall()
            }
            assert tables == {
                "schema_migrations",
                "locations",
                "sites",
                "organizations",
                "individuals",
                "families",
                "facts",
            }

            loc_cols = {
                r["name"] for r in cursor.execute("PRAGMA table_info(locations);").fetchall()
            }
            assert {
                "raw_name",
                "canonical_name",
                "aliases_json",
                "alt_spellings_json",
                "historical_names_json",
                "name_comment",
                "latitude",
                "longitude",
                "deprecated_at",
            }.issubset(loc_cols)

            site_cols = {r["name"] for r in cursor.execute("PRAGMA table_info(sites);").fetchall()}
            assert {
                "raw_name",
                "canonical_name",
                "address_line_1",
                "address_line_2",
                "address_city",
                "address_state",
                "address_postal_code",
                "address_latitude",
                "address_longitude",
                "latitude",
                "longitude",
                "deprecated_at",
            }.issubset(site_cols)

            org_cols = {
                r["name"] for r in cursor.execute("PRAGMA table_info(organizations);").fetchall()
            }
            assert {
                "raw_name",
                "canonical_name",
                "parent_org_id",
                "location_id",
                "meeting_site_id",
                "deprecated_at",
            }.issubset(org_cols)

            ind_cols = {
                r["name"] for r in cursor.execute("PRAGMA table_info(individuals);").fetchall()
            }
            assert {
                "raw_name",
                "canonical_name",
                "prefix",
                "given_name",
                "middle_name",
                "surname",
                "suffix",
                "married_names_json",
                "aliases_json",
                "alt_spellings_json",
                "name_comment",
                "gender",
                "deprecated_at",
            }.issubset(ind_cols)

            fam_cols = {
                r["name"] for r in cursor.execute("PRAGMA table_info(families);").fetchall()
            }
            assert {
                "union_type",
                "dissolution_type",
                "start_date_json",
                "end_date_json",
                "partner_ids_json",
                "children_json",
                "deprecated_at",
            }.issubset(fam_cols)

            indexes = {
                r[0]
                for r in cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='index';"
                ).fetchall()
            }
            assert {
                "idx_locations_urn",
                "idx_locations_canonical_name",
                "idx_locations_parent",
                "idx_locations_category",
                "idx_sites_urn",
                "idx_sites_canonical_name",
                "idx_sites_location",
                "idx_sites_category",
                "idx_organizations_urn",
                "idx_organizations_canonical_name",
                "idx_organizations_category",
                "idx_organizations_parent",
                "idx_organizations_location",
                "idx_organizations_site",
                "idx_individuals_urn",
                "idx_individuals_canonical_name",
                "idx_individuals_surname",
                "idx_individuals_given_name",
                "idx_individuals_birth_year",
                "idx_individuals_death_year",
                "idx_individuals_birth_sort",
                "idx_individuals_birth_place",
                "idx_individuals_death_place",
                "idx_families_urn",
                "idx_families_union_type",
                "idx_facts_urn",
                "idx_facts_subject",
                "idx_facts_type",
                "idx_facts_year",
                "idx_facts_date_sort",
                "idx_facts_location",
                "idx_facts_site",
            }.issubset(indexes)
        finally:
            cursor.close()


@pytest.mark.integration
def test_migrations_foreign_key_constraints(tmp_path: Path) -> None:
    """Verify foreign key ON DELETE RESTRICT and ON DELETE SET NULL rules across tables."""
    db_file = tmp_path / "migrations_fk.db"
    session = DatabaseSessionManager(db_path=db_file)
    SchemaManager(session_manager=session).init_db()

    with session.transaction() as tx:
        tx.execute(
            """
            INSERT INTO locations (
                id, canonical_urn, raw_name, canonical_name, category, created_at, updated_at
            ) VALUES (
                'LOC-000001', 'urn:gda:loc:us:nh', 'New Hampshire', 'New Hampshire',
                'STATOID', '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z'
            );
            """
        )
        tx.execute(
            """
            INSERT INTO locations (
                id, canonical_urn, raw_name, canonical_name, category,
                parent_id, created_at, updated_at
            ) VALUES (
                'LOC-000002', 'urn:gda:loc:us:nh:merrimack', 'Merrimack County', 'Merrimack County',
                'COUNTY_EQUIVALENT', 'LOC-000001', '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z'
            );
            """
        )
        tx.execute(
            """
            INSERT INTO sites (
                id, canonical_urn, raw_name, canonical_name, category,
                location_id, created_at, updated_at
            ) VALUES (
                'SID-000001', 'urn:gda:site:us:nh:merrimack:hall_s000001', 'Town Hall', 'Town Hall',
                'GOVERNMENT', 'LOC-000002', '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z'
            );
            """
        )
        tx.execute(
            """
            INSERT INTO organizations (
                id, canonical_urn, raw_name, canonical_name, category, parent_org_id,
                location_id, meeting_site_id, created_at, updated_at
            ) VALUES (
                'ORG-000001', 'urn:gda:org:nh:vfw', 'State VFW', 'State VFW',
                'VETERANS', NULL, 'LOC-000001', 'SID-000001',
                '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z'
            );
            """
        )
        tx.execute(
            """
            INSERT INTO organizations (
                id, canonical_urn, raw_name, canonical_name, category, parent_org_id,
                location_id, meeting_site_id, created_at, updated_at
            ) VALUES (
                'ORG-000002', 'urn:gda:org:nh:vfw:post_411', 'VFW Post 411', 'VFW Post 411',
                'VETERANS', 'ORG-000001', 'LOC-000002', 'SID-000001',
                '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z'
            );
            """
        )

    with pytest.raises(ConstraintViolationError):
        with session.transaction() as tx:
            tx.execute("DELETE FROM locations WHERE id = 'LOC-000002';")

    with session.transaction() as tx:
        tx.execute("DELETE FROM locations WHERE id = 'LOC-000001';")
        tx.execute("DELETE FROM organizations WHERE id = 'ORG-000001';")

    with session.get_connection() as conn:
        child_loc = conn.execute(
            "SELECT parent_id FROM locations WHERE id = 'LOC-000002';"
        ).fetchone()
        assert child_loc["parent_id"] is None

        child_org = conn.execute(
            "SELECT parent_org_id FROM organizations WHERE id = 'ORG-000002';"
        ).fetchone()
        assert child_org["parent_org_id"] is None
