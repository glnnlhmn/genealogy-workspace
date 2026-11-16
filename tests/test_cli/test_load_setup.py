"""Path: tests/test_cli/test_load_setup.py

Automated test suite verifying the baseline setup loader CLI orchestrator.

Tests structural validation, pyproject.toml environment resolution, partition
ordering, multi-entity dispatch, debug logging paths, and entrypoint execution.
"""

from __future__ import annotations

import json
import runpy
import sqlite3
import sys
from pathlib import Path
from typing import Any

import pytest

from cli.commands.load_setup import SetupLoader, build_parser, main

__version__ = "1.0.0+build.8"


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

    conn = sqlite3.connect(db_file)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sites (
                id TEXT PRIMARY KEY,
                canonical_urn TEXT NOT NULL,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                location_id TEXT NOT NULL,
                is_active INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.commit()
    finally:
        conn.close()

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
                    "alternate_names": ["USA"],
                    "historical_names": [],
                    "notes": [],
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
# GROUP 1: Parser, Configuration, and Integration Tests
# Note: Verifies CLI flag defaults, multi-entity dispatch, and entrypoint execution
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
def test_run_setup_both_entities_persists_to_database(
    workspace_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify run_setup loads both locations and sites cleanly via domain collections."""
    loc_dir = workspace_env / "data" / "setup" / "dev" / "locations"
    site_dir = workspace_env / "data" / "setup" / "dev" / "sites"

    create_partition(loc_dir, "00_loc.json", entity_type="locations")
    create_partition(site_dir, "00_site.json", entity_type="sites")

    saved_locs: list[Any] = []
    saved_sites: list[Any] = []

    def fake_save_locs(col: Any, **kwargs: Any) -> int:
        saved_locs.extend(list(col.iter_all()))
        return len(saved_locs)

    def fake_save_sites(col: Any, **kwargs: Any) -> int:
        saved_sites.extend(list(col.iter_all()))
        return len(saved_sites)

    monkeypatch.setattr("cli.commands.load_setup.save_locations_to_db", fake_save_locs)
    monkeypatch.setattr("cli.commands.load_setup.save_sites_to_db", fake_save_sites)

    loader = SetupLoader(env_name="DEV", root_dir=workspace_env)
    stats = loader.run_setup(entity="both")

    assert stats["locations"] == 1
    assert stats["sites"] == 1
    assert len(saved_locs) == 1
    assert len(saved_sites) == 1


@pytest.mark.unit
def test_run_setup_locations_only(workspace_env: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify run_setup loads only locations when entity='locations'."""
    loc_dir = workspace_env / "data" / "setup" / "dev" / "locations"
    create_partition(loc_dir, "00_loc.json", entity_type="locations")

    monkeypatch.setattr("cli.commands.load_setup.save_locations_to_db", lambda col, **kwargs: 1)

    loader = SetupLoader(env_name="DEV", root_dir=workspace_env)
    stats = loader.run_setup(entity="locations")

    assert "locations" in stats
    assert "sites" not in stats


@pytest.mark.unit
def test_run_setup_sites_only_with_directory_override(
    workspace_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify run_setup respects explicit directory override for sites."""
    custom_dir = workspace_env / "custom_sites"
    create_partition(custom_dir, "custom_site.json", entity_type="sites")

    monkeypatch.setattr("cli.commands.load_setup.save_sites_to_db", lambda col, **kwargs: 1)

    loader = SetupLoader(env_name="DEV", root_dir=workspace_env)
    stats = loader.run_setup(entity="sites", source_dir=custom_dir)

    assert stats["sites"] == 1


@pytest.mark.unit
def test_main_cli_execution_success(workspace_env: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify end-to-end main() invocation returns exit code 0."""
    loc_dir = workspace_env / "data" / "setup" / "dev" / "locations"
    site_dir = workspace_env / "data" / "setup" / "dev" / "sites"
    create_partition(loc_dir, "00_loc.json", entity_type="locations")
    create_partition(site_dir, "00_site.json", entity_type="sites")

    monkeypatch.setattr("cli.commands.load_setup.save_locations_to_db", lambda col, **kwargs: 1)
    monkeypatch.setattr("cli.commands.load_setup.save_sites_to_db", lambda col, **kwargs: 1)

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


@pytest.mark.unit
def test_main_cli_execution_debug_mode_success(
    workspace_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify end-to-end main() invocation with --debug returns exit code 0."""
    loc_dir = workspace_env / "data" / "setup" / "dev" / "locations"
    site_dir = workspace_env / "data" / "setup" / "dev" / "sites"
    create_partition(loc_dir, "00_loc.json", entity_type="locations")
    create_partition(site_dir, "00_site.json", entity_type="sites")

    monkeypatch.setattr("cli.commands.load_setup.save_locations_to_db", lambda col, **kwargs: 1)
    monkeypatch.setattr("cli.commands.load_setup.save_sites_to_db", lambda col, **kwargs: 1)

    cli_args = [
        "--env",
        "DEV",
        "--entity",
        "both",
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
    loc_dir = workspace_env / "data" / "setup" / "dev" / "locations"
    site_dir = workspace_env / "data" / "setup" / "dev" / "sites"
    create_partition(loc_dir, "00_loc.json", entity_type="locations")
    create_partition(site_dir, "00_site.json", entity_type="sites")

    monkeypatch.setattr("cli.commands.load_setup.save_locations_to_db", lambda col, **kwargs: 1)
    monkeypatch.setattr("cli.commands.load_setup.save_sites_to_db", lambda col, **kwargs: 1)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "load_setup.py",
            "--env",
            "DEV",
            "--entity",
            "both",
            "--root",
            str(workspace_env),
            "-v",
        ],
    )

    monkeypatch.setattr("gda.entity.locations.util.save_to_db", lambda col, **kwargs: 1)
    monkeypatch.setattr("gda.entity.sites.util.save_to_db", lambda col, **kwargs: 1)
    monkeypatch.delitem(sys.modules, "cli.commands.load_setup", raising=False)

    with pytest.raises(SystemExit) as exc_info:
        runpy.run_module("cli.commands.load_setup", run_name="__main__")

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
def test_get_default_setup_dir_invalid_type_raises_error(workspace_env: Path) -> None:
    """Verify get_default_setup_dir rejects unsupported entity keys."""
    loader = SetupLoader(env_name="DEV", root_dir=workspace_env)
    with pytest.raises(ValueError, match="Unsupported entity type"):
        loader.get_default_setup_dir("unsupported")


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
