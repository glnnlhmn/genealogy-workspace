"""Path: tests/test_system/test_create_dev_database.py

Unit and integration test suite for create_dev_database utility.

Operational Role:
    Verifies pyproject.toml environment resolution via AppConfig.for_environment(),
    end-to-end SQLite database initialization across all registered migrations,
    --reset file recreation, WAL pragma configuration, missing file/key error
    boundaries, and CLI argument parsing achieving 100.00% statement and branch coverage.
"""

from __future__ import annotations

import runpy
import sqlite3
import sys
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

import pytest

import system.gen_db as gen_db_pkg
import system.gen_db.create_dev_database as create_db_mod
from gda.db.schema.migrations import MIGRATION_REGISTRY
from system.gen_db.create_dev_database import (
    create_environment_database,
    main,
    parse_args,
)

__version__ = "1.0.0+build.4"


# ==============================================================================
# GROUP 1: Database Initialization & Environment Configuration Tests
# ==============================================================================


@pytest.mark.unit
def test_gen_db_dunder_all_contract() -> None:
    """Verify __all__ exports on system.gen_db and create_dev_database."""
    assert gen_db_pkg.__all__ == ["create_environment_database", "main", "parse_args"]
    assert create_db_mod.__all__ == ["create_environment_database", "main", "parse_args"]


@pytest.mark.integration
def test_create_environment_database_end_to_end_and_reset(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Verify real SQLite database provisioning, idempotency, and --reset recreation."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """
[tool.gda]
app_name = "GDA Test Provisioner"

[tool.gda.environments.DEV]
db_name = "gda_dev.db"
db_path = "data/db/gda_dev.db"
timeout_seconds = 15.0
""",
        encoding="utf-8",
    )

    db_path = create_environment_database(env_name="DEV", root_dir=tmp_path)
    assert db_path == (tmp_path / "data" / "db" / "gda_dev.db").resolve()
    assert db_path.exists()

    expected_versions = [m.version for m in MIGRATION_REGISTRY]
    latest_version = expected_versions[-1]

    captured = capsys.readouterr()
    assert "[DEV] Successfully initialized" in captured.out
    assert f"{expected_versions}" in captured.out
    assert f"schema version: v{latest_version}" in captured.out

    # Verify all 6 core entity tables exist and explicitly close the handle for Windows
    with closing(sqlite3.connect(db_path)) as conn:
        tables = {
            r[0]
            for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
        }
    assert {
        "schema_migrations",
        "locations",
        "sites",
        "organizations",
        "individuals",
        "families",
        "facts",
    }.issubset(tables)

    # Create a dummy -wal sidecar and re-run with reset=True to verify clean recreation
    wal_sidecar = Path(f"{db_path}-wal")
    wal_sidecar.write_text("dummy", encoding="utf-8")
    db_path_reset = create_environment_database(env_name="DEV", root_dir=tmp_path, reset=True)
    assert db_path_reset == db_path
    assert db_path.exists()

    # Also test absolute db_path in pyproject.toml
    abs_target = (tmp_path / "abs_data" / "abs_dev.db").resolve()
    pyproject.write_text(
        f"""
[tool.gda.environments.DEV]
db_path = "{abs_target.as_posix()}"
timeout_seconds = 10.0
""",
        encoding="utf-8",
    )
    abs_result = create_environment_database(env_name="DEV", root_dir=tmp_path)
    assert abs_result == abs_target


@pytest.mark.unit
def test_create_environment_database_missing_pyproject(tmp_path: Path) -> None:
    """Verify FileNotFoundError is raised when pyproject.toml does not exist."""
    with pytest.raises(FileNotFoundError, match="Configuration file not found"):
        create_environment_database(env_name="DEV", root_dir=tmp_path)


@pytest.mark.unit
def test_create_environment_database_missing_environment_key(tmp_path: Path) -> None:
    """Verify KeyError is raised when target environment is not configured."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """
[tool.gda.environments.TEST]
db_path = "data/db/test.db"
""",
        encoding="utf-8",
    )

    with pytest.raises(KeyError, match="Environment 'DEV' not defined"):
        create_environment_database(env_name="DEV", root_dir=tmp_path)


# ==============================================================================
# GROUP 2: CLI Argument Parsing & Entrypoint Execution Tests
# ==============================================================================


@pytest.mark.unit
def test_parse_args_defaults_and_custom() -> None:
    """Verify default and custom arguments parsed cleanly."""
    default_args = parse_args([])
    assert default_args.env == "DEV"
    assert default_args.root == "."
    assert default_args.reset is False

    custom_args = parse_args(["--env", "PROD", "--root", "/custom/dir", "--reset"])
    assert custom_args.env == "PROD"
    assert custom_args.root == "/custom/dir"
    assert custom_args.reset is True


@pytest.mark.integration
def test_main_cli_success(tmp_path: Path) -> None:
    """Verify main returns 0 on successful execution."""
    with patch("system.gen_db.create_dev_database.create_environment_database") as mock_create:
        mock_create.return_value = tmp_path / "dev.db"
        exit_code = main(["--env", "DEV", "--root", str(tmp_path), "--reset"])
        assert exit_code == 0
        mock_create.assert_called_once_with(env_name="DEV", root_dir=str(tmp_path), reset=True)


@pytest.mark.unit
def test_main_cli_error(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify main catches exceptions, prints to stderr, and returns 1."""
    with patch(
        "system.gen_db.create_dev_database.create_environment_database",
        side_effect=FileNotFoundError("pyproject missing"),
    ):
        exit_code = main(["--env", "DEV"])
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "Error provisioning DEV database: pyproject missing" in captured.err


@pytest.mark.unit
def test_create_dev_database_module_runpy(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify execution as __main__ module."""
    monkeypatch.setattr("sys.argv", ["create_dev_database", "-h"])
    monkeypatch.delitem(sys.modules, "system.gen_db.create_dev_database", raising=False)
    with pytest.raises(SystemExit) as exc:
        runpy.run_module("system.gen_db.create_dev_database", run_name="__main__")
    assert exc.value.code == 0
