"""Path: tests/test_cli/test_load_setup.py

Automated test suite verifying the baseline setup loader CLI orchestrator.

Tests structural validation, pyproject.toml environment resolution, partition
ordering, multi-entity dispatch, transactional writes, and CLI boundaries.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

import pytest

from cli.commands.load_setup import SetupLoader, build_parser, main

__version__ = "1.0.0+build.1"


# ==========================================================================
# FIXTURES
# Note: Handcrafted synthetic fixtures for testing environments and partitions
# ==========================================================================


@pytest.fixture
def workspace_env(tmp_path: Path) -> Path:
    """Provision a minimal synthetic workspace root directory adhering to pyproject.toml."""
    root = tmp_path / "workspace"
    root.mkdir(parents=True, exist_ok=True)

    pyproject_content = (
        b"[tool.gda.environments.DEV]\n"
        b'db_path = "data/db/gen_desk_dev.sqlite"\n'
        b'intake_dir = "data/intake/dev"\n'
        b"timeout_seconds = 10.0\n"
    )
    (root / "pyproject.toml").write_bytes(pyproject_content)

    db_file = root / "data" / "db" / "gen_desk_dev.sqlite"
    db_file.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(db_file) as conn:
        conn.execute(
            """
            CREATE TABLE locations (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                canonical_urn TEXT NOT NULL,
                parent_id TEXT,
                is_primary_local_authority INTEGER NOT NULL,
                is_unincorporated INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE sites (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                canonical_urn TEXT NOT NULL,
                location_id TEXT NOT NULL,
                is_active INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.commit()

    return root


def create_partition(
    directory: Path,
    filename: str,
    entity_type: str = "locations",
    record_type: str | None = None,
    total_count: int = 1,
    items: list[dict[str, Any]] | None = None,
) -> Path:
    """Generate a synthetic partitioned JSON setup file."""
    directory.mkdir(parents=True, exist_ok=True)
    if record_type is None:
        record_type = "LOCATION_IMPORT" if entity_type == "locations" else "SITE_IMPORT"

    if items is None:
        if entity_type == "locations":
            items = [
                {
                    "id": "LOC-000001",
                    "name": "United States",
                    "category": "COUNTRY",
                    "canonical_urn": "urn:gda:loc:united_states",
                    "parent_id": None,
                    "is_primary_local_authority": False,
                    "is_unincorporated": False,
                }
            ]
        else:
            items = [
                {
                    "id": "SID-000001",
                    "name": "Carlisle Hospital",
                    "category": "HOSPITAL",
                    "canonical_urn": "urn:gda:site:us:pa:cumberland:carlisle_hospital",
                    "location_id": "LOC-000152",
                    "is_active": False,
                }
            ]

    payload = {
        "_path": f"{directory.name}/{filename}",
        "$schema": f"https://gda.archive/schemas/intake/dev/{entity_type}_import.schema.json",
        "schema_version": "1.0.0",
        "record_type": record_type,
        "created_at": "2026-11-04T12:00:00Z",
        "batch_id": f"BATCH-{entity_type.upper()}-TEST",
        "source_note": "Test partition.",
        "total_count": total_count,
        entity_type: items,
    }

    file_path = directory / filename
    with open(file_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh)

    return file_path


# ==========================================================================
# GROUP 1: Parser and Configuration Unit Tests
# Note: Verifies CLI flag defaults and pyproject environment table resolution
# ==========================================================================


@pytest.mark.unit
def test_build_parser_defaults_verify_options() -> None:
    """Verify build_parser declares correct defaults."""
    parser = build_parser()
    args = parser.parse_args([])

    assert args.env_name == "DEV"
    assert args.entity == "both"
    assert args.source_dir is None
    assert args.root_dir == "."
    assert not args.verbose
    assert not args.debug


@pytest.mark.unit
def test_load_environment_config_success_resolves_db_path(workspace_env: Path) -> None:
    """Verify load_environment_config extracts settings from pyproject.toml."""
    loader = SetupLoader(env_name="DEV", root_dir=workspace_env)
    config = loader.load_environment_config()

    expected_db = workspace_env / "data" / "db" / "gen_desk_dev.sqlite"
    assert config.db_path == expected_db
    assert config.busy_timeout == 10000
    assert config.journal_mode == "WAL"


@pytest.mark.unit
def test_get_default_setup_dir_resolves_locations(workspace_env: Path) -> None:
    """Verify get_default_setup_dir derives data/setup/dev/locations."""
    loader = SetupLoader(env_name="DEV", root_dir=workspace_env)
    expected = workspace_env / "data" / "setup" / "dev" / "locations"
    assert loader.get_default_setup_dir("locations") == expected


@pytest.mark.unit
def test_get_default_setup_dir_resolves_sites(workspace_env: Path) -> None:
    """Verify get_default_setup_dir derives data/setup/dev/sites."""
    loader = SetupLoader(env_name="DEV", root_dir=workspace_env)
    expected = workspace_env / "data" / "setup" / "dev" / "sites"
    assert loader.get_default_setup_dir("sites") == expected


@pytest.mark.unit
def test_get_default_setup_dir_invalid_type_raises_error(workspace_env: Path) -> None:
    """Verify get_default_setup_dir rejects unsupported entity keys."""
    loader = SetupLoader(env_name="DEV", root_dir=workspace_env)
    with pytest.raises(ValueError, match="Unsupported entity type"):
        loader.get_default_setup_dir("unsupported")


# ==========================================================================
# GROUP 2: Validation and Defensive Regression Tests
# Note: Verifies schema bounds, missing keys, and mismatch handling
# ==========================================================================


@pytest.mark.regression
def test_load_environment_config_missing_pyproject_raises_error(tmp_path: Path) -> None:
    """Verify load_environment_config fails when pyproject.toml is missing."""
    empty_root = tmp_path / "empty_workspace"
    empty_root.mkdir()
    loader = SetupLoader(env_name="DEV", root_dir=empty_root)

    with pytest.raises(FileNotFoundError, match="Configuration file not found"):
        loader.load_environment_config()


@pytest.mark.regression
def test_load_environment_config_missing_environment_raises_key_error(
    workspace_env: Path,
) -> None:
    """Verify load_environment_config fails when requested environment is not configured."""
    loader = SetupLoader(env_name="STAGING", root_dir=workspace_env)

    with pytest.raises(KeyError, match="Environment 'STAGING' not defined"):
        loader.load_environment_config()


@pytest.mark.regression
def test_validate_file_structure_missing_envelope_fields_raises_error(
    tmp_path: Path,
) -> None:
    """Verify validate_file_structure detects missing envelope properties."""
    bad_file = tmp_path / "bad_envelope.json"
    bad_file.write_text('{"schema_version": "1.0.0"}', encoding="utf-8")

    loader = SetupLoader(root_dir=tmp_path)
    with pytest.raises(ValueError, match="missing envelope fields"):
        loader.validate_file_structure(bad_file, "locations")


@pytest.mark.regression
def test_validate_file_structure_invalid_record_type_raises_error(
    tmp_path: Path,
) -> None:
    """Verify validate_file_structure rejects mismatched record_type."""
    bad_file = create_partition(tmp_path, "wrong_type.json", record_type="WRONG_TYPE")
    loader = SetupLoader(root_dir=tmp_path)

    with pytest.raises(ValueError, match="invalid record_type"):
        loader.validate_file_structure(bad_file, "locations")


@pytest.mark.regression
def test_validate_file_structure_count_mismatch_raises_error(
    tmp_path: Path,
) -> None:
    """Verify validate_file_structure rejects total_count mismatch."""
    bad_file = create_partition(tmp_path, "count_mismatch.json", total_count=99)
    loader = SetupLoader(root_dir=tmp_path)

    with pytest.raises(ValueError, match="total_count .* does not match"):
        loader.validate_file_structure(bad_file, "locations")


@pytest.mark.regression
def test_validate_file_structure_missing_item_fields_raises_error(
    tmp_path: Path,
) -> None:
    """Verify validate_file_structure rejects items missing mandatory attributes."""
    bad_file = create_partition(
        tmp_path,
        "missing_attrs.json",
        items=[{"id": "LOC-000001", "name": "Incomplete"}],
    )
    loader = SetupLoader(root_dir=tmp_path)

    with pytest.raises(ValueError, match="missing required fields"):
        loader.validate_file_structure(bad_file, "locations")


@pytest.mark.regression
def test_validate_file_structure_sites_missing_fields_raises_error(
    tmp_path: Path,
) -> None:
    """Verify validate_file_structure rejects sites missing mandatory attributes."""
    bad_file = create_partition(
        tmp_path,
        "bad_site.json",
        entity_type="sites",
        items=[{"id": "SID-000001", "name": "Site Missing Fields"}],
    )
    loader = SetupLoader(root_dir=tmp_path)

    with pytest.raises(ValueError, match="missing required fields"):
        loader.validate_file_structure(bad_file, "sites")


@pytest.mark.regression
def test_discover_and_sort_files_missing_dir_raises_error(tmp_path: Path) -> None:
    """Verify discover_and_sort_files rejects non-existent intake directory."""
    loader = SetupLoader(root_dir=tmp_path)
    with pytest.raises(FileNotFoundError, match="Setup directory does not exist"):
        loader.discover_and_sort_files(tmp_path / "non_existent")


@pytest.mark.regression
def test_discover_and_sort_files_empty_dir_raises_error(tmp_path: Path) -> None:
    """Verify discover_and_sort_files rejects empty intake directory."""
    empty_dir = tmp_path / "empty_dir"
    empty_dir.mkdir()
    loader = SetupLoader(root_dir=tmp_path)

    with pytest.raises(ValueError, match="No JSON setup partitions discovered"):
        loader.discover_and_sort_files(empty_dir)


# ==========================================================================
# GROUP 3: Integration and Transactional Execution Tests
# Note: Verifies partition discovery, database write commit, and CLI entrypoint
# ==========================================================================


@pytest.mark.integration
def test_run_setup_both_entities_persists_to_database(workspace_env: Path) -> None:
    """Verify run_setup loads both locations and sites into the SQLite database."""
    loc_dir = workspace_env / "data" / "setup" / "dev" / "locations"
    site_dir = workspace_env / "data" / "setup" / "dev" / "sites"

    create_partition(loc_dir, "00_loc.json", entity_type="locations")
    create_partition(site_dir, "00_site.json", entity_type="sites")

    loader = SetupLoader(env_name="DEV", root_dir=workspace_env)
    stats = loader.run_setup(entity="both")

    assert stats["locations"] == 1
    assert stats["sites"] == 1

    db_path = workspace_env / "data" / "db" / "gen_desk_dev.sqlite"
    with sqlite3.connect(db_path) as conn:
        loc_rows = conn.execute("SELECT id, name FROM locations").fetchall()
        site_rows = conn.execute("SELECT id, name, is_active FROM sites").fetchall()

    assert loc_rows == [("LOC-000001", "United States")]
    assert site_rows == [("SID-000001", "Carlisle Hospital", 0)]


@pytest.mark.integration
def test_run_setup_locations_only(workspace_env: Path) -> None:
    """Verify run_setup loads only locations when entity='locations'."""
    loc_dir = workspace_env / "data" / "setup" / "dev" / "locations"
    create_partition(loc_dir, "00_loc.json", entity_type="locations")

    loader = SetupLoader(env_name="DEV", root_dir=workspace_env)
    stats = loader.run_setup(entity="locations")

    assert "locations" in stats
    assert "sites" not in stats


@pytest.mark.integration
def test_run_setup_sites_only_with_directory_override(workspace_env: Path) -> None:
    """Verify run_setup respects explicit directory override."""
    custom_dir = workspace_env / "custom_sites"
    create_partition(custom_dir, "custom_site.json", entity_type="sites")

    loader = SetupLoader(env_name="DEV", root_dir=workspace_env)
    stats = loader.run_setup(entity="sites", source_dir=custom_dir)

    assert stats["sites"] == 1


# ==========================================================================
# GROUP 4: Smoke End-to-End CLI Gateway Tests
# Note: Validates main() invocation exit codes and parameter wiring
# ==========================================================================


@pytest.mark.smoke
def test_main_cli_execution_success(workspace_env: Path) -> None:
    """Verify end-to-end main() invocation returns exit code 0."""
    loc_dir = workspace_env / "data" / "setup" / "dev" / "locations"
    site_dir = workspace_env / "data" / "setup" / "dev" / "sites"
    create_partition(loc_dir, "00_loc.json", entity_type="locations")
    create_partition(site_dir, "00_site.json", entity_type="sites")

    cli_args = [
        "--env",
        "DEV",
        "--entity",
        "both",
        "--root",
        str(workspace_env),
        "-v",
    ]

    exit_code = main(cli_args)
    assert exit_code == 0


@pytest.mark.smoke
def test_main_cli_execution_failure_returns_code_1(workspace_env: Path) -> None:
    """Verify main() returns exit code 1 when an invalid environment is targeted."""
    cli_args = [
        "--env",
        "NONEXISTENT",
        "--root",
        str(workspace_env),
    ]

    exit_code = main(cli_args)
    assert exit_code == 1
