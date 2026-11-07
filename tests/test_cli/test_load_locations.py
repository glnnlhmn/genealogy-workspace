"""Path: tests/test_cli/test_load_locations.py

Automated test suite verifying the bulk location intake CLI orchestrator.

Tests structural validation, pyproject.toml environment resolution, partition
ordering, transactional database ingestion, and CLI exit code boundaries.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

import pytest

from cli.commands.load_locations import LocationLoader, build_parser, main

__version__ = "1.0.0+build.6"


# ==========================================================================
# FIXTURES
# Note: Handcrafted synthetic fixtures for testing environments and partitions
# ==========================================================================


@pytest.fixture
def workspace_env(tmp_path: Path) -> Path:
    """Provision a minimal synthetic workspace root directory."""
    root = tmp_path / "workspace"
    root.mkdir(parents=True, exist_ok=True)

    pyproject_content = (
        b"[tool.gda.environments.DEV]\n"
        b'db_path = "data/db/gen_desk_dev.sqlite"\n'
        b'setup_dir = "data/setup/dev/locations"\n'
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
        conn.commit()

    return root


def create_partition_file(
    directory: Path,
    filename: str,
    record_type: str = "LOCATION_IMPORT",
    total_count: int = 1,
    locations: list[dict[str, Any]] | None = None,
) -> Path:
    """Generate a synthetic partitioned JSON intake file."""
    if locations is None:
        locations = [
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

    payload = {
        "_path": f"data/setup/dev/locations/{filename}",
        "$schema": "https://gda.archive/schemas/dev/intake/location_import.schema.json",
        "schema_version": "1.0.0",
        "record_type": record_type,
        "created_at": "2026-11-04T12:00:00Z",
        "batch_id": "BATCH-TEST",
        "source_note": "Test partition.",
        "total_count": total_count,
        "locations": locations,
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
    assert args.intake_dir is None
    assert args.root_dir == "."
    assert not args.verbose
    assert not args.debug


@pytest.mark.unit
def test_load_environment_config_success_resolves_db_path(workspace_env: Path) -> None:
    """Verify load_environment_config extracts settings from pyproject.toml."""
    loader = LocationLoader(env_name="DEV", root_dir=workspace_env)
    config = loader.load_environment_config()

    expected_db = workspace_env / "data" / "db" / "gen_desk_dev.sqlite"
    assert config.db_path == expected_db
    assert config.busy_timeout == 10000
    assert config.journal_mode == "WAL"


@pytest.mark.unit
def test_get_default_setup_dir_derives_path(workspace_env: Path) -> None:
    """Verify get_default_setup_dir derives correct path from configuration."""
    loader = LocationLoader(env_name="DEV", root_dir=workspace_env)
    setup_dir = loader.get_default_setup_dir()

    expected_setup = workspace_env / "data" / "setup" / "dev" / "locations"
    assert setup_dir == expected_setup


# ==========================================================================
# GROUP 2: Validation and Defensive Regression Tests
# Note: Verifies schema bounds, missing keys, and mismatch handling
# ==========================================================================


@pytest.mark.regression
def test_load_environment_config_missing_pyproject_raises_error(tmp_path: Path) -> None:
    """Verify load_environment_config fails when pyproject.toml is missing."""
    empty_root = tmp_path / "empty_workspace"
    empty_root.mkdir()
    loader = LocationLoader(env_name="DEV", root_dir=empty_root)

    with pytest.raises(FileNotFoundError, match="Configuration file not found"):
        loader.load_environment_config()


@pytest.mark.regression
def test_load_environment_config_missing_environment_raises_key_error(
    workspace_env: Path,
) -> None:
    """Verify load_environment_config fails when requested environment is not configured."""
    loader = LocationLoader(env_name="STAGING", root_dir=workspace_env)

    with pytest.raises(KeyError, match="Environment 'STAGING' not defined"):
        loader.load_environment_config()


@pytest.mark.regression
def test_validate_file_structure_missing_envelope_fields_raises_error(
    tmp_path: Path,
) -> None:
    """Verify validate_file_structure detects missing envelope properties."""
    bad_file = tmp_path / "bad_envelope.json"
    bad_file.write_text('{"schema_version": "1.0.0"}', encoding="utf-8")

    loader = LocationLoader(root_dir=tmp_path)
    with pytest.raises(ValueError, match="missing envelope fields"):
        loader.validate_file_structure(bad_file)


@pytest.mark.regression
def test_validate_file_structure_invalid_record_type_raises_error(
    tmp_path: Path,
) -> None:
    """Verify validate_file_structure rejects wrong record_type string."""
    bad_file = create_partition_file(tmp_path, "wrong_type.json", record_type="WRONG_TYPE")
    loader = LocationLoader(root_dir=tmp_path)

    with pytest.raises(ValueError, match="invalid record_type"):
        loader.validate_file_structure(bad_file)


@pytest.mark.regression
def test_validate_file_structure_count_mismatch_raises_error(
    tmp_path: Path,
) -> None:
    """Verify validate_file_structure rejects total_count mismatch."""
    bad_file = create_partition_file(tmp_path, "count_mismatch.json", total_count=99)
    loader = LocationLoader(root_dir=tmp_path)

    with pytest.raises(ValueError, match="total_count .* does not match"):
        loader.validate_file_structure(bad_file)


@pytest.mark.regression
def test_validate_file_structure_missing_location_field_raises_error(
    tmp_path: Path,
) -> None:
    """Verify validate_file_structure rejects items missing required fields."""
    incomplete_locations = [
        {
            "id": "LOC-000001",
            "name": "Missing Attributes",
        }
    ]
    bad_file = create_partition_file(
        tmp_path,
        "missing_fields.json",
        total_count=1,
        locations=incomplete_locations,
    )
    loader = LocationLoader(root_dir=tmp_path)

    with pytest.raises(ValueError, match="missing required fields"):
        loader.validate_file_structure(bad_file)


@pytest.mark.regression
def test_discover_and_sort_files_missing_dir_raises_error(tmp_path: Path) -> None:
    """Verify discover_and_sort_files rejects non-existent intake directory."""
    loader = LocationLoader(root_dir=tmp_path)
    with pytest.raises(FileNotFoundError, match="Intake directory does not exist"):
        loader.discover_and_sort_files(tmp_path / "non_existent")


@pytest.mark.regression
def test_discover_and_sort_files_empty_dir_raises_error(tmp_path: Path) -> None:
    """Verify discover_and_sort_files rejects empty intake directory."""
    empty_dir = tmp_path / "empty_intake"
    empty_dir.mkdir()
    loader = LocationLoader(root_dir=tmp_path)

    with pytest.raises(ValueError, match="No JSON intake partitions discovered"):
        loader.discover_and_sort_files(empty_dir)


# ==========================================================================
# GROUP 3: Integration and Transactional Execution Tests
# Note: Verifies partition discovery, database write commit, and CLI entrypoint
# ==========================================================================


@pytest.mark.integration
def test_discover_and_sort_files_sorts_lexicographically(tmp_path: Path) -> None:
    """Verify partition files are returned in ascending filename order."""
    create_partition_file(tmp_path, "02_us_states.json")
    create_partition_file(tmp_path, "00_root_countries.json")
    create_partition_file(tmp_path, "01_non_us.json")

    loader = LocationLoader(root_dir=tmp_path)
    sorted_files = loader.discover_and_sort_files(tmp_path)

    file_names = [f.name for f in sorted_files]
    assert file_names == [
        "00_root_countries.json",
        "01_non_us.json",
        "02_us_states.json",
    ]


@pytest.mark.integration
def test_load_partitions_persists_records_to_database(workspace_env: Path) -> None:
    """Verify load_partitions writes location entities to SQLite database using default dir."""
    setup_dir = workspace_env / "data" / "setup" / "dev" / "locations"
    setup_dir.mkdir(parents=True, exist_ok=True)

    loc1 = {
        "id": "LOC-000001",
        "name": {"raw": "United States", "canonical": "United States"},
        "category": "COUNTRY",
        "canonical_urn": "urn:gda:loc:united_states",
        "parent_id": None,
        "is_primary_local_authority": False,
        "is_unincorporated": False,
    }
    create_partition_file(
        setup_dir,
        "00_root_countries.json",
        total_count=1,
        locations=[loc1],
    )

    loader = LocationLoader(env_name="DEV", root_dir=workspace_env)
    stats = loader.load_partitions()

    assert stats["00_root_countries.json"] == 1
    assert stats["__TOTAL__"] == 1

    db_path = workspace_env / "data" / "db" / "gen_desk_dev.sqlite"
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, name, category, is_unincorporated, created_at, updated_at
            FROM locations
            """
        )
        rows = cursor.fetchall()

    assert len(rows) == 1
    assert rows[0][0] == "LOC-000001"
    assert rows[0][1] == "United States"
    assert rows[0][2] == "COUNTRY"
    assert rows[0][3] == 0
    assert rows[0][4] == "2026-11-04T12:00:00Z"
    assert rows[0][5] is not None


# ==========================================================================
# GROUP 4: Smoke End-to-End CLI Gateway Tests
# Note: Validates main() invocation exit codes and parameter wiring
# ==========================================================================


@pytest.mark.smoke
def test_main_cli_execution_success(workspace_env: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify end-to-end main() invocation returns exit code 0."""
    setup_dir = workspace_env / "data" / "setup" / "dev" / "locations"
    setup_dir.mkdir(parents=True, exist_ok=True)
    create_partition_file(setup_dir, "00_test.json", total_count=1)

    cli_args = [
        "--env",
        "DEV",
        "--root",
        str(workspace_env),
        "-v",
    ]

    exit_code = main(cli_args)
    assert exit_code == 0


@pytest.mark.smoke
def test_main_cli_execution_failure_returns_code_1(
    workspace_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify main() returns exit code 1 when an invalid environment is targeted."""
    cli_args = [
        "--env",
        "NONEXISTENT",
        "--root",
        str(workspace_env),
    ]

    exit_code = main(cli_args)
    assert exit_code == 1
