"""Path: tests/test_gda/test_core/test_core_config.py

Unit verification suite for GDA Core configuration subsystem.

Operational Role:
    Validates AppConfig, DatabaseConfig, and LoggingConfig schemas,
    multi-engine connection string rendering (SQLite, PostgreSQL/MySQL with
    credentials and ports, and DSN overrides), environment resolution from
    pyproject.toml ([tool.gda.environments.<ENV>]), immutability, undeclared
    attribute rejection, path derivation, precedence resolution, and error boundaries.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from gda.core.config import AppConfig, DatabaseConfig, LoggingConfig
from gda.core.errors import ConfigParseError, ConfigValidationError

__version__ = "1.0.0+build.15"

# ==============================================================================
# GROUP 1: SCHEMA DEFAULTS, IMMUTABILITY & ISOLATED VALIDATION
# ==============================================================================


@pytest.mark.unit
def test_database_config_defaults() -> None:
    """Verify default attributes and derived properties of DatabaseConfig."""
    cfg = DatabaseConfig()

    assert cfg.engine == "sqlite"
    assert cfg.db_name is None
    assert cfg.resolved_db_name == "archive.db"
    assert cfg.db_path == Path("data/archive.db")
    assert cfg.host is None
    assert cfg.port is None
    assert cfg.username is None
    assert cfg.password is None
    assert cfg.dsn_override is None
    assert cfg.busy_timeout == 5000
    assert cfg.journal_mode == "WAL"
    assert cfg.foreign_keys is True
    assert cfg.synchronous == "NORMAL"
    assert cfg.is_in_memory is False
    assert cfg.connection_string == "sqlite:///data/archive.db"


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
        password="p@ss:word/1",
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


@pytest.mark.regression
def test_database_config_invalid_fields_raise() -> None:
    """Verify DatabaseConfig rejects invalid db_path, non-mapping input, and blank engine values."""
    with pytest.raises(ValidationError) as exc_info:
        DatabaseConfig(db_path=12345)  # type: ignore[arg-type]
    assert "Invalid db_path type" in str(exc_info.value)

    with pytest.raises(ValidationError, match="Invalid engine value"):
        DatabaseConfig(engine="   ")

    with pytest.raises(ValidationError):
        DatabaseConfig.model_validate("not-a-mapping")


@pytest.mark.regression
def test_database_config_busy_timeout_boundary_validation() -> None:
    """Verify DatabaseConfig rejects busy_timeout outside 100-60000 ms."""
    with pytest.raises(ValidationError):
        DatabaseConfig(busy_timeout=50)

    with pytest.raises(ValidationError):
        DatabaseConfig(busy_timeout=70000)


@pytest.mark.regression
def test_database_config_immutability() -> None:
    """Verify DatabaseConfig forbids field mutation after initialization."""
    cfg = DatabaseConfig()
    with pytest.raises(ValidationError):
        cfg.busy_timeout = 10000  # type: ignore[misc]


@pytest.mark.unit
def test_logging_config_level_normalization() -> None:
    """Verify LoggingConfig normalizes lowercase level strings to uppercase."""
    cfg = LoggingConfig(level="debug")  # type: ignore[arg-type]
    assert cfg.level == "DEBUG"


@pytest.mark.regression
def test_logging_config_level_non_string_passthrough() -> None:
    """Verify LoggingConfig normalize_level handles non-string values gracefully."""
    with pytest.raises(ValidationError):
        LoggingConfig(level=12345)  # type: ignore[arg-type]


@pytest.mark.regression
def test_logging_config_invalid_level_raises_validation_error() -> None:
    """Verify LoggingConfig rejects unrecognized log level strings."""
    with pytest.raises(ValidationError):
        LoggingConfig(level="VERBOSE")  # type: ignore[arg-type]


@pytest.mark.regression
def test_logging_config_min_bytes_enforced() -> None:
    """Verify LoggingConfig rejects max_bytes smaller than 1024."""
    with pytest.raises(ValidationError):
        LoggingConfig(max_bytes=512)


@pytest.mark.regression
def test_logging_config_immutability() -> None:
    """Verify LoggingConfig forbids field mutation after initialization."""
    cfg = LoggingConfig()
    with pytest.raises(ValidationError):
        cfg.level = "DEBUG"  # type: ignore[misc]


@pytest.mark.regression
def test_config_forbids_undeclared_extra_attributes() -> None:
    """Verify models configured with extra='forbid' reject undeclared fields."""
    with pytest.raises(ValidationError):
        DatabaseConfig(extra_param="disallowed")  # type: ignore[call-arg]

    with pytest.raises(ValidationError):
        LoggingConfig(unknown_flag=True)  # type: ignore[call-arg]

    with pytest.raises(ValidationError):
        AppConfig(unrecognized_setting=123)  # type: ignore[call-arg]


# ==============================================================================
# GROUP 2: APPCONFIG PATH DERIVATION & DIRECTORY PROVISIONING
# ==============================================================================


@pytest.mark.unit
def test_app_config_derived_paths_and_env_codes(tmp_path: Path) -> None:
    """Verify AppConfig derives canonical subdirectories and normalizes environment codes."""
    cfg = AppConfig(root_path=tmp_path, environment="PROD")  # type: ignore[arg-type]

    assert cfg.environment == "production"
    assert cfg.env_code == "PROD"
    assert cfg.data_path == tmp_path / "data"
    assert cfg.logs_path == tmp_path / "logs"
    assert cfg.backups_path == tmp_path / "backups"

    with pytest.raises(ValidationError):
        AppConfig(root_path=tmp_path, environment=12345)  # type: ignore[arg-type]


@pytest.mark.integration
def test_app_config_ensure_directories(tmp_path: Path) -> None:
    """Verify ensure_directories creates data, logs, and backups directories on disk."""
    cfg = AppConfig(root_path=tmp_path)
    cfg.ensure_directories()

    assert cfg.data_path.is_dir()
    assert cfg.logs_path.is_dir()
    assert cfg.backups_path.is_dir()


@pytest.mark.regression
def test_app_config_root_path_validation_errors(tmp_path: Path) -> None:
    """Verify AppConfig rejects invalid root_path types, missing paths, and files."""
    with pytest.raises(ValidationError) as exc_type:
        AppConfig(root_path=12345)  # type: ignore[arg-type]
    assert "Invalid path type" in str(exc_type.value)

    missing_dir = tmp_path / "does_not_exist"
    with pytest.raises(ValidationError) as exc_missing:
        AppConfig(root_path=missing_dir)
    assert "Root path does not exist" in str(exc_missing.value)

    file_target = tmp_path / "regular_file.txt"
    file_target.write_text("content", encoding="utf-8")
    with pytest.raises(ValidationError) as exc_file:
        AppConfig(root_path=file_target)
    assert "Root path must be a directory" in str(exc_file.value)


# ==============================================================================
# GROUP 3: APPCONFIG MULTI-TIER PRECEDENCE & ENVIRONMENT RESOLUTION
# ==============================================================================


@pytest.mark.smoke
@pytest.mark.unit
def test_app_config_load_defaults(tmp_path: Path) -> None:
    """Verify AppConfig.load() initializes standard model defaults when unconfigured."""
    cfg = AppConfig.load(root_path=tmp_path)

    assert cfg.app_name == "Genealogy Digital Archive"
    assert cfg.environment == "development"
    assert cfg.env_code == "DEV"
    assert cfg.database.db_path == Path("data/archive.db")
    assert cfg.logging.level == "INFO"
    assert cfg.debug is False


@pytest.mark.integration
def test_app_config_load_from_custom_toml(tmp_path: Path) -> None:
    """Verify AppConfig.load(config_path) parses custom TOML files and environments."""
    toml_path = tmp_path / "custom_config.toml"
    toml_content = """
    app_name = "Custom Archive"
    environment = "staging"
    debug = true

    [database]
    db_path = "data/custom.db"
    busy_timeout = 8000

    [environments.STAGING.database]
    db_name = "gda_staging.db"
    db_path = "data/db/gda_staging.db"

    [logging]
    level = "WARNING"
    """
    toml_path.write_text(toml_content, encoding="utf-8")

    cfg = AppConfig.load(config_path=toml_path, root_path=tmp_path, env_name="STAGING")

    assert cfg.app_name == "Custom Archive"
    assert cfg.environment == "staging"
    assert cfg.debug is True
    assert cfg.database.db_name == "gda_staging.db"
    assert cfg.database.db_path == Path("data/db/gda_staging.db")
    assert cfg.database.busy_timeout == 8000
    assert cfg.logging.level == "WARNING"

    # Also test requesting an env_name that is absent from [environments] so env_db is empty
    cfg_unmapped = AppConfig.load(config_path=toml_path, root_path=tmp_path, env_name="PROD")
    assert cfg_unmapped.environment == "production"
    assert cfg_unmapped.database.db_path == Path("data/custom.db")


@pytest.mark.integration
def test_app_config_for_environment_from_pyproject(tmp_path: Path) -> None:
    """Verify AppConfig.for_environment resolves DEV, TEST, STAGING, and PROD from pyproject.toml."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """
[tool.gda]
app_name = "GDA Environment Suite"

[tool.gda.environments.DEV]
db_name = "gda_dev.db"
db_path = "data/db/gda_dev.db"
timeout_seconds = 30.0

[tool.gda.environments.TEST]
db_name = "gda_test.db"
db_path = "data/db/gda_test.db"
timeout_seconds = 15.0

[tool.gda.environments.STAGING]
db_name = "gda_staging.db"
db_path = "data/db/gda_staging.db"
timeout_seconds = 20.0

[tool.gda.environments.PROD]
db_name = "gda_prod.db"
db_path = "data/db/gda_prod.db"
timeout_seconds = 45.0
""",
        encoding="utf-8",
    )

    dev_cfg = AppConfig.for_environment("DEV", root_path=tmp_path)
    assert dev_cfg.environment == "development"
    assert dev_cfg.database.db_name == "gda_dev.db"
    assert dev_cfg.database.db_path == Path("data/db/gda_dev.db")
    assert dev_cfg.database.busy_timeout == 30000

    prod_cfg = AppConfig.for_environment("PROD", root_path=tmp_path, config_path=pyproject)
    assert prod_cfg.environment == "production"
    assert prod_cfg.database.db_name == "gda_prod.db"
    assert prod_cfg.database.db_path == Path("data/db/gda_prod.db")
    assert prod_cfg.database.busy_timeout == 45000

    # Unconfigured environment key in _extract_env_db_settings returns empty dict
    assert AppConfig._extract_env_db_settings({"DEV": "not-a-dict"}, "DEV") == {}


@pytest.mark.integration
def test_app_config_load_from_dedicated_gda_config_toml(tmp_path: Path) -> None:
    """Verify AppConfig.load finds gda_config.toml when present in root_path."""
    dedicated = tmp_path / "gda_config.toml"
    dedicated.write_text('app_name = "Dedicated TOML"', encoding="utf-8")

    cfg = AppConfig.load(root_path=tmp_path)
    assert cfg.app_name == "Dedicated TOML"


@pytest.mark.integration
def test_app_config_load_from_pyproject_tool_section(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify AppConfig.load() automatically inspects pyproject.toml [tool.gda]."""
    monkeypatch.chdir(tmp_path)
    pyproject = tmp_path / "pyproject.toml"
    pyproject_content = """
    [tool.gda]
    app_name = "PyProject GDA"

    [tool.gda.logging]
    level = "ERROR"
    """
    pyproject.write_text(pyproject_content, encoding="utf-8")

    cfg = AppConfig.load(root_path=tmp_path)

    assert cfg.app_name == "PyProject GDA"
    assert cfg.logging.level == "ERROR"


@pytest.mark.integration
def test_app_config_load_via_gda_config_path_env_var(tmp_path: Path) -> None:
    """Verify GDA_CONFIG_PATH environment variable directs TOML loading (both pyproject and custom)."""
    env_toml = tmp_path / "pyproject.toml"
    env_toml.write_text('[tool.gda]\napp_name = "Env Directed"\ndebug = true\n', encoding="utf-8")

    cfg = AppConfig.load(
        root_path=tmp_path,
        env_vars={"GDA_CONFIG_PATH": str(env_toml)},
    )
    assert cfg.app_name == "Env Directed"
    assert cfg.debug is True

    custom_env_toml = tmp_path / "custom_env.toml"
    custom_env_toml.write_text('app_name = "Custom Env Directed"\n', encoding="utf-8")
    cfg_custom = AppConfig.load(
        root_path=tmp_path,
        env_vars={"GDA_CONFIG_PATH": str(custom_env_toml)},
    )
    assert cfg_custom.app_name == "Custom Env Directed"


@pytest.mark.unit
def test_app_config_environment_variables_and_overrides_precedence(
    tmp_path: Path,
) -> None:
    """Verify environment variables and runtime overrides supersede TOML settings."""
    toml_file = tmp_path / "base.toml"
    toml_file.write_text(
        """
        app_name = "TOML Name"
        debug = false

        [database]
        busy_timeout = 3000

        [logging]
        level = "INFO"
        log_to_file = false
        """,
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


# ==============================================================================
# GROUP 4: ERROR BOUNDARIES & EXCEPTION TRANSLATION
# ==============================================================================


@pytest.mark.regression
def test_app_config_missing_explicit_config_path_raises(tmp_path: Path) -> None:
    """Verify missing explicit config_path raises ConfigParseError."""
    missing = tmp_path / "missing.toml"
    with pytest.raises(ConfigParseError) as exc_info:
        AppConfig.load(config_path=missing)
    assert exc_info.value.error_code == "ERR_CONFIG_FILE_NOT_FOUND"


@pytest.mark.regression
def test_app_config_missing_gda_config_path_env_raises(tmp_path: Path) -> None:
    """Verify non-existent GDA_CONFIG_PATH target raises ConfigParseError."""
    missing = tmp_path / "missing_env.toml"
    with pytest.raises(ConfigParseError) as exc_info:
        AppConfig.load(env_vars={"GDA_CONFIG_PATH": str(missing)})
    assert exc_info.value.error_code == "ERR_CONFIG_FILE_NOT_FOUND"


@pytest.mark.regression
def test_app_config_malformed_toml_raises_config_parse_error(tmp_path: Path) -> None:
    """Verify malformed TOML syntax raises ConfigParseError with ERR_CONFIG_TOML_PARSE."""
    bad_toml = tmp_path / "broken.toml"
    bad_toml.write_text("app_name = [unclosed_list\n", encoding="utf-8")

    with pytest.raises(ConfigParseError) as exc_info:
        AppConfig.load(config_path=bad_toml, root_path=tmp_path)
    assert exc_info.value.error_code == "ERR_CONFIG_TOML_PARSE"


@pytest.mark.regression
def test_app_config_invalid_merged_values_raise_config_validation_error(
    tmp_path: Path,
) -> None:
    """Verify invalid schema values in AppConfig.load raise ConfigValidationError."""
    with pytest.raises(ConfigValidationError) as exc_info:
        AppConfig.load(
            root_path=tmp_path,
            overrides={"environment": "invalid_env"},
        )
    assert exc_info.value.error_code == "ERR_CONFIG_VALIDATION"
