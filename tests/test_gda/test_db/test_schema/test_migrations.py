"""Path: tests/test_gda/test_db/test_schema/test_migrations.py

Unit, integration, and regression verification suite for GDA DB schema migrations.

Operational Role:
    1:1 verification suite for src/gda/db/schema/migrations/. Validates
    MIGRATION_REGISTRY ordering, version continuity, and SQLite DDL execution.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import gda.db.schema.migrations as migrations_mod
from gda.db.schema import SchemaManager
from gda.db.schema.migrations import (
    MIGRATION_REGISTRY,
    v001_places,
    v002_organizations,
    v003_personas,
    v004_facts,
    v005_indexes,
    v006_sources_vital_cemetery,
    v007_sources_enumerated_publications,
    v008_sources_probate_land,
    v009_sources_immigration_military,
    v010_sources_education_manuscripts_orgs_other,
    v011_xrefs,
)
from gda.db.session import DatabaseSessionManager

__version__ = "1.0.0+build.7"


@pytest.mark.unit
def test_migrations_dunder_all_and_registry_continuity() -> None:
    """Verify __all__ exports and strictly sequential migration versions."""
    assert migrations_mod.__all__ == [
        "MIGRATION_REGISTRY",
        "Migration",
        "v001_places",
        "v002_organizations",
        "v003_personas",
        "v004_facts",
        "v005_indexes",
        "v006_sources_vital_cemetery",
        "v007_sources_enumerated_publications",
        "v008_sources_probate_land",
        "v009_sources_immigration_military",
        "v010_sources_education_manuscripts_orgs_other",
        "v011_xrefs",
    ]

    versions = [m.version for m in MIGRATION_REGISTRY]
    assert versions == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]

    for mod, expected_ver in (
        (v001_places, 1),
        (v002_organizations, 2),
        (v003_personas, 3),
        (v004_facts, 4),
        (v005_indexes, 5),
        (v006_sources_vital_cemetery, 6),
        (v007_sources_enumerated_publications, 7),
        (v008_sources_probate_land, 8),
        (v009_sources_immigration_military, 9),
        (v010_sources_education_manuscripts_orgs_other, 10),
        (v011_xrefs, 11),
    ):
        assert mod.__all__ == ["NAME", "UP_SQL", "VERSION"]
        assert mod.VERSION == expected_ver
        assert isinstance(mod.NAME, str) and mod.NAME
        assert isinstance(mod.UP_SQL, str) and mod.UP_SQL.strip()


@pytest.mark.integration
def test_migrations_ddl_creates_expected_tables_and_indexes(tmp_path: Path) -> None:
    """Verify executing all migrations creates core, source, and xref tables."""
    db_file = tmp_path / "test_migrations.db"
    session = DatabaseSessionManager(db_path=db_file)
    manager = SchemaManager(session_manager=session)

    applied = manager.init_db()
    assert applied == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]

    with session.get_connection() as conn:
        tables = {
            row["name"]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
        }
        assert {
            "schema_migrations",
            "locations",
            "sites",
            "organizations",
            "individuals",
            "families",
            "facts",
            "vital_baptisms",
            "vital_births",
            "vital_deaths",
            "vital_divorces",
            "vital_marriages",
            "cemetery_markers",
            "cemetery_registries",
            "enumerated_population_schedules",
            "enumerated_supplemental_schedules",
            "enumerated_directories",
            "enumerated_tax_assessments",
            "publications_catalog",
            "publications_newspaper_clips",
            "publications_periodical_articles",
            "probate_wills",
            "probate_inventories",
            "land_deeds",
            "land_grants",
            "immigration_manifests",
            "immigration_naturalizations",
            "military_draft_records",
            "military_service_records",
            "military_pension_records",
            "military_bounty_land_warrants",
            "military_casualty_records",
            "military_award_records",
            "education_credentials",
            "manuscripts_family_bibles",
            "manuscripts_narratives",
            "orgs_memberships",
            "orgs_rosters",
            "other_miscellaneous_records",
            "xref_fact_participants",
            "xref_individual_families",
            "xref_individual_organizations",
            "xref_individual_sources",
            "xref_individual_surnames",
            "xref_locations",
            "xref_media",
            "xref_sites",
            "xref_surnames",
        }.issubset(tables)
