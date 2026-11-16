"""Path: tests/test_cli/test_load_locations.py

Automated test suite verifying the bulk location intake CLI orchestrator.

Tests structural validation, pyproject.toml environment resolution, partition
ordering, explicit directory overrides, collection delegation, and entrypoint execution.
"""

from __future__ import annotations

import json
import runpy
import sqlite3
import sys
from pathlib import Path
from typing import Any

import pytest

from cli.commands.load_locations import LocationLoader, build_parser, main

__version__ = "1.0.0+build.11"


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
        b'setup_dir = "data/setup/dev/locations"\n'
        b"timeout_seconds = 10.0\n"
    )
    (root / "pyproject.toml").write_bytes(pyproject_content)

    db_file = root / "data" / "db" / "gen_desk_dev.sqlite"
    db_file.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_file)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS locations (
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
    finally:
        conn.close()

    return root


def create_partition_file(
    directory: Path,
    filename: str,
    record_type: str = "LOCATION_IMPORT",
    total_count: int = 1,
    locations: list[dict[str, Any]] | None = None,
) -> Path:
    """Generate a synthetic partitioned JSON intake file."""
    directory.mkdir(parents=True, exist_ok=True)
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
                "alternate_names": ["USA"],
                "historical_names": [],
                "notes": [],
            }
        ]

    payload = {
        "_path": f"data/setup/dev/locations/{filename}",
        "$schema": "https://gda.archive/schemas/intake/dev/location_import.schema.json",
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
# GROUP 1: Parser, Configuration, and Integration Tests
# Note: Verifies CLI flag defaults, overrides, collection delegation, and execution
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
def test_location_loader_custom_schema_path_override(tmp_path: Path) -> None:
    """Verify LocationLoader honors an explicit schema_path override."""
    custom_schema = "custom/schemas/loc.json"
    loader = LocationLoader(env_name="DEV", root_dir=tmp_path, schema_path=custom_schema)
    expected_path = tmp_path.resolve() / Path(custom_schema)
    assert loader.schema_path == expected_path


@pytest.mark.unit
def test_load_environment_config_success_resolves_db_path(workspace_env: Path) -> None:
    """Verify load_environment_config extracts settings from pyproject.toml."""
    loader = LocationLoader(env_name="DEV", root_dir=workspace_env)
    try:
        config = loader.load_environment_config()
        expected_db = workspace_env / "data" / "db" / "gen_desk_dev.sqlite"
        assert config.db_path == expected_db
        assert config.busy_timeout == 10000
        assert config.journal_mode == "WAL"
    finally:
        if loader._session_manager and hasattr(loader._session_manager, "close"):
            loader._session_manager.close()


@pytest.mark.unit
def test_get_default_setup_dir_derives_path(workspace_env: Path) -> None:
    """Verify get_default_setup_dir derives correct path from configuration."""
    loader = LocationLoader(env_name="DEV", root_dir=workspace_env)
    setup_dir = loader.get_default_setup_dir()

    expected_setup = workspace_env / "data" / "setup" / "dev" / "locations"
    assert setup_dir == expected_setup


@pytest.mark.unit
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


@pytest.mark.unit
def test_load_partitions_persists_records_via_facade(
    workspace_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify load_partitions routes through Locations facade and persists records."""
    setup_dir = workspace_env / "data" / "setup" / "dev" / "locations"
    create_partition_file(setup_dir, "00_root_countries.json", total_count=1)

    saved_entities = []

    def fake_save_to_db(collection: Any) -> int:
        saved_entities.extend(list(collection.iter_all()))
        return len(saved_entities)

    monkeypatch.setattr("cli.commands.load_locations.save_to_db", fake_save_to_db)

    loader = LocationLoader(env_name="DEV", root_dir=workspace_env)
    stats = loader.load_partitions()

    assert stats["00_root_countries.json"] == 1
    assert stats["__TOTAL__"] == 1
    assert len(saved_entities) == 1
    assert str(saved_entities[0].id) == "LOC-000001"
    assert saved_entities[0].name.canonical == "United States"


@pytest.mark.unit
def test_load_partitions_with_explicit_intake_dir_override(
    workspace_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify load_partitions respects explicit directory override."""
    custom_dir = workspace_env / "custom_partitions"
    create_partition_file(custom_dir, "00_custom.json", total_count=1)

    monkeypatch.setattr("cli.commands.load_locations.save_to_db", lambda col: 1)

    loader = LocationLoader(env_name="DEV", root_dir=workspace_env)
    stats = loader.load_partitions(intake_dir=custom_dir)

    assert stats["00_custom.json"] == 1
    assert stats["__TOTAL__"] == 1


@pytest.mark.unit
def test_main_cli_execution_success(workspace_env: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify end-to-end main() invocation returns exit code 0."""
    setup_dir = workspace_env / "data" / "setup" / "dev" / "locations"
    create_partition_file(setup_dir, "00_test.json", total_count=1)

    monkeypatch.setattr("cli.commands.load_locations.save_to_db", lambda col: 1)

    cli_args = [
        "--env",
        "DEV",
        "--root",
        str(workspace_env),
        "-v",
    ]

    exit_code = main(cli_args)
    assert exit_code == 0


@pytest.mark.unit
def test_main_cli_execution_debug_mode_success(
    workspace_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify end-to-end main() invocation with --debug returns exit code 0."""
    setup_dir = workspace_env / "data" / "setup" / "dev" / "locations"
    create_partition_file(setup_dir, "00_test.json", total_count=1)

    monkeypatch.setattr("cli.commands.load_locations.save_to_db", lambda col: 1)

    cli_args = [
        "--env",
        "DEV",
        "--root",
        str(workspace_env),
        "--debug",
    ]

    exit_code = main(cli_args)
    assert exit_code == 0


@pytest.mark.unit
def test_module_main_entrypoint_execution(
    workspace_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify module-level execution via if __name__ == '__main__' triggers sys.exit(0)."""
    setup_dir = workspace_env / "data" / "setup" / "dev" / "locations"
    create_partition_file(setup_dir, "00_test.json", total_count=1)

    monkeypatch.setattr("gda.entity.locations.util.save_to_db", lambda col: 1)
    monkeypatch.setattr(
        sys,
        "argv",
        ["load_locations.py", "--env", "DEV", "--root", str(workspace_env), "-v"],
    )

    with pytest.raises(SystemExit) as exc_info:
        runpy.run_module("cli.commands.load_locations", run_name="__main__")

    assert exc_info.value.code == 0


# ==========================================================================
# GROUP 2: Validation and Defensive Regression Tests
# Note: Verifies schema bounds, missing keys, and error paths
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


@pytest.mark.regression
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
