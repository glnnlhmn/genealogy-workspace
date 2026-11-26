"""Path: tests/test_gda/test_core/test_core_config_1_2_3.py

Unit and regression test suite for gda.core.config (Groups 1-3).

Operational Role:
    Covers Groups 1-3 of the 6-group catalog for gda.core.config:
    - GROUP 1: Smoke & Primary Entrypoints (__all__ exports, default load).
    - GROUP 2: Core Logic & Happy Paths (DatabaseConfig, LoggingConfig,
      AppConfig defaults, multi-engine URIs, path derivation, and precedence).
    - GROUP 3: Edge Cases & Boundary Conditions (password-only auth safety,
      scalar nested env vars, GDA_ENVIRONMENT-only overlay activation, and
      host GDA_* env isolation).

Test Structure & Protocol:
    - Atomized & parametrized tests: 1:1 behavioral contract mapping.
    - Fully decorated: 5-marker taxonomy (smoke, unit, regression, integration).
    - Companion module: test_core_config_4_5_6.py (Groups 4-6).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from pydantic import SecretStr

import gda.core.config as cfg_mod
from gda.core.config import AppConfig, DatabaseConfig, LoggingConfig

__version__ = "1.0.0+build.4"


# ==============================================================================
# GROUP 1: Smoke & Primary Entrypoints
# Note: Verifies gda.core.config exports and default AppConfig.load() contract.
# ==============================================================================


@pytest.mark.smoke
@pytest.mark.unit
def test_config_exposes_public_interface_and_loads_defaults(tmp_path: Path) -> None:
    """Verify gda.core.config exports all 4 classes and AppConfig.load() yields defaults."""
    expected_exports = {
        "AppConfig",
        "DatabaseConfig",
        "ImmutableBaseModel",
        "LoggingConfig",
    }
    assert set(cfg_mod.__all__) == expected_exports

    cfg = AppConfig.load(root_path=tmp_path)
    assert cfg.app_name == "Genealogy Digital Archive"
    assert cfg.environment == "development"
    assert cfg.env_code == "DEV"
    assert cfg.database.db_path == Path("data/archive.db")
    assert cfg.logging.level == "INFO"
    assert cfg.debug is False


# ==============================================================================
# GROUP 2: Core Logic & Happy Paths
# Note: Schema defaults, URI rendering, path derivation, and precedence rules.
# ==============================================================================


@pytest.mark.unit
@pytest.mark.parametrize(
    ("attr_name", "expected_val"),
    [
        ("engine", "sqlite"),
        ("db_name", None),
        ("resolved_db_name", "archive.db"),
        ("db_path", Path("data/archive.db")),
        ("host", None),
        ("port", None),
        ("username", None),
        ("password", None),
        ("dsn_override", None),
        ("busy_timeout", 5000),
        ("journal_mode", "WAL"),
        ("foreign_keys", True),
        ("synchronous", "NORMAL"),
        ("is_in_memory", False),
        ("connection_string", "sqlite:///data/archive.db"),
    ],
)
def test_database_config_defaults(attr_name: str, expected_val: Any) -> None:
    """Verify default attributes and derived properties of DatabaseConfig."""
    cfg = DatabaseConfig()
    assert getattr(cfg, attr_name) == expected_val


@pytest.mark.unit
def test_database_config_in_memory_and_db_name_sync() -> None:
    """Verify in-memory path detection, db_name synchronization, and timeout_seconds conversion."""
    cfg_str = DatabaseConfig(db_path=":memory:")
    assert cfg_str.is_in_memory is True
    assert cfg_str.resolved_db_name == ":memory:"
    assert cfg_str.connection_string == "sqlite:///:memory:"

    cfg_uri = DatabaseConfig(db_name="file::memory:")
    assert cfg_uri.is_in_memory is True
    assert cfg_uri.resolved_db_name == "file::memory:"
    assert cfg_uri.connection_string == "sqlite:///:memory:"

    cfg_named = DatabaseConfig.model_validate({"db_name": "gda_prod.db", "timeout_seconds": 25.0})
    assert cfg_named.db_path == Path("data/gda_prod.db")
    assert cfg_named.resolved_db_name == "gda_prod.db"
    assert cfg_named.busy_timeout == 25000


@pytest.mark.unit
def test_database_config_multi_engine_connection_strings() -> None:
    """Verify connection_string rendering for client-server engines and dsn_override."""
    pg_full = DatabaseConfig(
        engine="PostgreSQL+Psycopg",
        host="db.internal",
        port=5432,
        username="gda_admin",
        password=SecretStr("p@ss:word/1"),
        db_name="gda_prod",
    )
    assert pg_full.engine == "postgresql+psycopg"
    assert (
        pg_full.connection_string
        == "postgresql+psycopg://gda_admin:p%40ss%3Aword%2F1@db.internal:5432/gda_prod"
    )

    pg_user_only = DatabaseConfig(
        engine="postgresql",
        username="readonly",
        db_name="gda_staging",
    )
    assert pg_user_only.connection_string == "postgresql://readonly@localhost/gda_staging"

    pg_no_auth = DatabaseConfig(
        engine="postgresql",
        host="127.0.0.1",
        db_name="gda_dev",
    )
    assert pg_no_auth.connection_string == "postgresql://127.0.0.1/gda_dev"

    custom_dsn = DatabaseConfig(dsn_override="postgresql://custom_dsn_host:5432/custom_db")
    assert custom_dsn.connection_string == "postgresql://custom_dsn_host:5432/custom_db"


@pytest.mark.unit
def test_database_config_path_instance_passthrough(tmp_path: Path) -> None:
    """Verify pre-constructed Path instances pass through validator unchanged."""
    custom_path = tmp_path / "custom.db"
    cfg = DatabaseConfig(db_path=custom_path)
    assert cfg.db_path == custom_path


@pytest.mark.unit
@pytest.mark.parametrize(
    ("raw_level", "expected_level"),
    [("debug", "DEBUG"), ("info", "INFO"), ("Warning", "WARNING")],
)
def test_logging_config_normalizes_level_to_uppercase(
    raw_level: str,
    expected_level: str,
) -> None:
    """Verify LoggingConfig normalizes lowercase and mixed-case level strings to uppercase."""
    cfg = LoggingConfig(level=raw_level)  # type: ignore[arg-type]
    assert cfg.level == expected_level


@pytest.mark.unit
@pytest.mark.parametrize(
    ("raw_env", "expected_env", "expected_code"),
    [
        ("DEV", "development", "DEV"),
        ("TEST", "testing", "TEST"),
        ("stage", "staging", "STAGING"),
        ("PROD", "production", "PROD"),
    ],
)
def test_app_config_derived_paths_and_env_codes(
    tmp_path: Path,
    raw_env: str,
    expected_env: str,
    expected_code: str,
) -> None:
    """Verify AppConfig derives canonical subdirectories and normalizes environment codes."""
    cfg = AppConfig(root_path=tmp_path, environment=raw_env)  # type: ignore[arg-type]
    assert cfg.environment == expected_env
    assert cfg.env_code == expected_code
    assert cfg.data_path == tmp_path / "data"
    assert cfg.logs_path == tmp_path / "logs"
    assert cfg.backups_path == tmp_path / "backups"


@pytest.mark.unit
def test_app_config_environment_variables_and_overrides_precedence(
    tmp_path: Path,
) -> None:
    """Verify environment variables and runtime overrides supersede TOML settings."""
    toml_file = tmp_path / "base.toml"
    toml_file.write_text(
        'app_name = "TOML Name"\ndebug = false\n\n'
        "[database]\nbusy_timeout = 3000\n\n"
        '[logging]\nlevel = "INFO"\nlog_to_file = false\n',
        encoding="utf-8",
    )

    env_map = {
        "GDA_APP_NAME": "Env Name",
        "GDA_DEBUG": "true",
        "GDA_DATABASE__BUSY_TIMEOUT": "12000",
        "GDA_DATABASE__USERNAME": "db_user",
        "GDA_LOGGING__LOG_TO_FILE": "no",
        "UNRELATED_VAR": "ignored",
    }
    overrides = {
        "app_name": "Override Name",
        "database": {"journal_mode": "TRUNCATE"},
    }

    cfg = AppConfig.load(
        config_path=toml_file,
        root_path=tmp_path,
        env_vars=env_map,
        overrides=overrides,
    )
    assert cfg.app_name == "Override Name"
    assert cfg.debug is True
    assert cfg.database.busy_timeout == 12000
    assert cfg.database.username == "db_user"
    assert cfg.database.journal_mode == "TRUNCATE"
    assert cfg.logging.log_to_file is False


# ==============================================================================
# GROUP 3: Edge Cases & Boundary Conditions
# Note: Password-only auth, scalar env keys, GDA_ENVIRONMENT overlay, and isolation.
# ==============================================================================


@pytest.mark.regression
def test_database_config_password_without_username_omits_auth_segment() -> None:
    """Verify password without username does not leak credentials into URI."""
    cfg = DatabaseConfig(
        engine="postgresql",
        host="db.internal",
        password=SecretStr("secret_password"),
        db_name="gda_dev",
    )
    assert cfg.connection_string == "postgresql://db.internal/gda_dev"
    assert "secret_password" not in cfg.connection_string


@pytest.mark.regression
def test_app_config_env_nested_on_non_dict_section_ignored(tmp_path: Path) -> None:
    """Verify nested env var targeting a scalar top-level field does not crash."""
    cfg = AppConfig.load(
        root_path=tmp_path,
        env_vars={
            "GDA_APP_NAME": "ScalarApp",
            "GDA_APP_NAME__SUBKEY": "IgnoredSubkey",
        },
    )
    assert cfg.app_name == "ScalarApp"


@pytest.mark.regression
@pytest.mark.integration
def test_app_config_load_applies_env_overlay_from_gda_environment_var_alone(
    tmp_path: Path,
) -> None:
    """Verify setting only GDA_ENVIRONMENT activates the matching TOML environment overlay."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[tool.gda]\napp_name = "Env Overlay Test"\n\n'
        '[tool.gda.environments.PROD]\ndb_name = "gda_prod.db"\n'
        'db_path = "data/db/gda_prod.db"\ntimeout_seconds = 40.0\n',
        encoding="utf-8",
    )

    cfg = AppConfig.load(
        config_path=pyproject,
        root_path=tmp_path,
        env_vars={"GDA_ENVIRONMENT": "PROD"},
    )
    assert cfg.environment == "production"
    assert cfg.database.db_name == "gda_prod.db"
    assert cfg.database.db_path == Path("data/db/gda_prod.db")
    assert cfg.database.busy_timeout == 40000


@pytest.mark.regression
def test_app_config_host_env_vars_isolated_by_explicit_env_map(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify host GDA_* env vars apply by default and are isolated by env_vars={}."""
    monkeypatch.setenv("GDA_APP_NAME", "HostLeakedArchive")

    cfg_from_host = AppConfig.load(root_path=tmp_path)
    assert cfg_from_host.app_name == "HostLeakedArchive"

    cfg_isolated = AppConfig.load(root_path=tmp_path, env_vars={})
    assert cfg_isolated.app_name == "Genealogy Digital Archive"
