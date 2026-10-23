"""Path: tests/test_gda/test_core/test_config.py

Unit verification suite for GDA Core configuration subsystem.

Operational Role:
    Validates AppConfig, DatabaseConfig, and LoggingConfig schemas,
    immutability, undeclared attribute rejection, path derivation,
    precedence resolution (defaults, TOML, GDA_CONFIG_PATH, environment variables, overrides),
    and defensive error boundaries.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from gda.core.config import AppConfig, DatabaseConfig, LoggingConfig
from gda.core.errors import ConfigParseError, ConfigValidationError

__version__ = "1.0.0+build.r11"

# ==============================================================================
# GROUP 1: SCHEMA DEFAULTS, IMMUTABILITY & ISOLATED VALIDATION
# Note: Validates baseline Pydantic model constraints, immutability, and helpers
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_database_config_defaults() -> None:
    """Verify default attributes and derived properties of DatabaseConfig."""
    cfg = DatabaseConfig()

    assert cfg.db_path == Path("data/archive.db")
    assert cfg.busy_timeout == 5000
    assert cfg.journal_mode == "WAL"
    assert cfg.foreign_keys is True
    assert cfg.synchronous == "NORMAL"
    assert cfg.is_in_memory is False
    assert cfg.connection_string == "sqlite:///data/archive.db"


@pytest.mark.unit
def test_database_config_in_memory() -> None:
    """Verify in-memory path detection and rendered connection string."""
    cfg_str = DatabaseConfig(db_path=":memory:")
    assert cfg_str.is_in_memory is True
    assert cfg_str.connection_string == "sqlite:///:memory:"

    cfg_uri = DatabaseConfig(db_path="file::memory:")
    assert cfg_uri.is_in_memory is True
    assert cfg_uri.connection_string == "sqlite:///:memory:"


@pytest.mark.unit
def test_database_config_path_instance_passthrough(tmp_path: Path) -> None:
    """Verify pre-constructed Path instances pass through validator unchanged."""
    custom_path = tmp_path / "custom.db"
    cfg = DatabaseConfig(db_path=custom_path)
    assert cfg.db_path == custom_path


@pytest.mark.regression
def test_database_config_invalid_db_path_type_raises() -> None:
    """Verify DatabaseConfig rejects non-string and non-Path types on line 57."""
    with pytest.raises(ValidationError) as exc_info:
        DatabaseConfig(db_path=12345)  # type: ignore[arg-type]
    assert "Invalid db_path type" in str(exc_info.value)


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
        LoggingConfig(unexpected_flag=True)  # type: ignore[call-arg]

    with pytest.raises(ValidationError):
        AppConfig(unsupported_block=123)  # type: ignore[call-arg]


# ==============================================================================
# GROUP 2: APPCONFIG PATHS & DIRECTORY PROVISIONING
# Note: Validates root_path validation, derived directories, and provisioning
# ==============================================================================


@pytest.mark.regression
def test_app_config_immutability() -> None:
    """Verify AppConfig forbids attribute mutation after initialization."""
    cfg = AppConfig.load()
    with pytest.raises(ValidationError):
        cfg.debug = True  # type: ignore[misc]


@pytest.mark.regression
def test_root_path_invalid_type_raises_validation_error() -> None:
    """Verify root_path validator rejects non-string/Path types."""
    with pytest.raises(ValidationError) as exc_info:
        AppConfig(root_path=12345)  # type: ignore[arg-type]
    assert "Invalid path type" in str(exc_info.value)


@pytest.mark.regression
def test_root_path_nonexistent_raises_validation_error(tmp_path: Path) -> None:
    """Verify root_path validator rejects non-existent paths."""
    missing = tmp_path / "missing_folder"
    with pytest.raises(ValidationError) as exc_info:
        AppConfig(root_path=missing)
    assert "Root path does not exist" in str(exc_info.value)


@pytest.mark.regression
def test_root_path_file_target_raises_validation_error(tmp_path: Path) -> None:
    """Verify root_path validator rejects files where directories are required."""
    file_path = tmp_path / "file.txt"
    file_path.write_text("sample", encoding="utf-8")
    with pytest.raises(ValidationError) as exc_info:
        AppConfig(root_path=file_path)
    assert "Root path must be a directory" in str(exc_info.value)


@pytest.mark.unit
def test_derived_directory_paths_match_root(tmp_path: Path) -> None:
    """Verify data_path, logs_path, and backups_path derive directly from root_path."""
    cfg = AppConfig(root_path=tmp_path)
    assert cfg.data_path == tmp_path / "data"
    assert cfg.logs_path == tmp_path / "logs"
    assert cfg.backups_path == tmp_path / "backups"


@pytest.mark.integration
def test_ensure_directories_creates_all_subdirectories(tmp_path: Path) -> None:
    """Verify ensure_directories creates data, logs, and backups folders."""
    cfg = AppConfig(root_path=tmp_path)
    cfg.ensure_directories()

    assert (tmp_path / "data").is_dir()
    assert (tmp_path / "logs").is_dir()
    assert (tmp_path / "backups").is_dir()


# ==============================================================================
# GROUP 3: APPCONFIG MULTI-TIER PRECEDENCE
# Note: Validates loading across defaults, files, environment, and overrides
# ==============================================================================


@pytest.mark.unit
def test_app_config_load_defaults() -> None:
    """Verify AppConfig.load() initializes standard model defaults when unconfigured."""
    cfg = AppConfig.load()

    assert cfg.app_name == "Genealogy Digital Archive"
    assert cfg.environment == "development"
    assert cfg.database.db_path == Path("data/archive.db")
    assert cfg.logging.level == "INFO"
    assert cfg.debug is False


@pytest.mark.integration
def test_app_config_load_from_custom_toml(tmp_path: Path) -> None:
    """Verify AppConfig.load(config_path) parses custom TOML files."""
    toml_path = tmp_path / "custom_config.toml"
    toml_content = """
    app_name = "Custom Archive"
    environment = "staging"
    debug = true

    [database]
    db_path = "data/custom.db"
    busy_timeout = 8000

    [logging]
    level = "WARNING"
    """
    toml_path.write_text(toml_content, encoding="utf-8")

    cfg = AppConfig.load(config_path=toml_path, root_path=tmp_path)

    assert cfg.app_name == "Custom Archive"
    assert cfg.environment == "staging"
    assert cfg.debug is True
    assert cfg.database.db_path == Path("data/custom.db")
    assert cfg.database.busy_timeout == 8000
    assert cfg.logging.level == "WARNING"


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
def test_app_config_load_from_gda_config_path_env_var(tmp_path: Path) -> None:
    """Verify GDA_CONFIG_PATH environment variable directs config file loading."""
    env_target = tmp_path / "env_directed.toml"
    env_target.write_text('app_name = "Env Directed"', encoding="utf-8")

    env_map = {"GDA_CONFIG_PATH": str(env_target)}
    cfg = AppConfig.load(root_path=tmp_path, env_vars=env_map)

    assert cfg.app_name == "Env Directed"


@pytest.mark.regression
def test_app_config_missing_gda_config_path_file_raises_parse_error(
    tmp_path: Path,
) -> None:
    """Verify missing GDA_CONFIG_PATH target file raises ConfigParseError."""
    missing = tmp_path / "missing_target.toml"
    env_map = {"GDA_CONFIG_PATH": str(missing)}

    with pytest.raises(ConfigParseError) as exc_info:
        AppConfig.load(root_path=tmp_path, env_vars=env_map)

    assert exc_info.value.error_code == "ERR_CONFIG_FILE_NOT_FOUND"
    assert str(missing) in exc_info.value.message


@pytest.mark.integration
def test_app_config_environment_variable_precedence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify GDA_ environment variables take precedence over configuration defaults."""
    monkeypatch.setenv("GDA_ENVIRONMENT", "production")
    monkeypatch.setenv("GDA_DEBUG", "true")
    monkeypatch.setenv("GDA_DATABASE__DB_PATH", "prod_data/archive.db")
    monkeypatch.setenv("GDA_DATABASE__BUSY_TIMEOUT", "4500")
    monkeypatch.setenv("GDA_LOGGING__LOG_TO_FILE", "false")

    cfg = AppConfig.load()

    assert cfg.environment == "production"
    assert cfg.debug is True
    assert cfg.database.db_path == Path("prod_data/archive.db")
    assert cfg.database.busy_timeout == 4500
    assert cfg.logging.log_to_file is False


@pytest.mark.unit
def test_app_config_env_vars_mapping_injection(tmp_path: Path) -> None:
    """Verify explicit env_vars dictionary injection isolates environment tests."""
    env_map = {
        "GDA_APP_NAME": "Isolated Environment",
        "GDA_DEBUG": "1",
        "GDA_DATABASE__BUSY_TIMEOUT": "2500",
    }
    cfg = AppConfig.load(root_path=tmp_path, env_vars=env_map)

    assert cfg.app_name == "Isolated Environment"
    assert cfg.debug is True
    assert cfg.database.busy_timeout == 2500


@pytest.mark.unit
def test_app_config_env_vars_coercion_types(tmp_path: Path) -> None:
    """Verify env var coercion converts 'no', '0', and uncastable strings accurately."""
    env_map = {
        "GDA_DEBUG": "no",
        "GDA_APP_NAME": "Uncastable String",
    }
    cfg = AppConfig.load(root_path=tmp_path, env_vars=env_map)
    assert cfg.debug is False
    assert cfg.app_name == "Uncastable String"


@pytest.mark.unit
def test_app_config_env_vars_skips_nested_when_section_not_dict(tmp_path: Path) -> None:
    """Verify nested env vars skip assignment if parent key is a scalar value."""
    env_map = {
        "GDA_APP_NAME": "Archive",
        "GDA_APP_NAME__SUB": "Ignored",
    }
    cfg = AppConfig.load(root_path=tmp_path, env_vars=env_map)
    assert cfg.app_name == "Archive"


@pytest.mark.unit
def test_app_config_runtime_overrides_scalar_replacement() -> None:
    """Verify runtime overrides dictionary replaces scalar top-level attributes."""
    overrides = {
        "app_name": "Override Desk",
        "debug": True,
    }
    cfg = AppConfig.load(overrides=overrides)

    assert cfg.app_name == "Override Desk"
    assert cfg.debug is True


@pytest.mark.unit
def test_app_config_runtime_overrides_highest_precedence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify runtime overrides dictionary overrides environment variables and defaults."""
    monkeypatch.setenv("GDA_ENVIRONMENT", "production")

    overrides = {
        "environment": "testing",
        "database": {"busy_timeout": 8000},
    }

    cfg = AppConfig.load(overrides=overrides)

    assert cfg.environment == "testing"
    assert cfg.database.busy_timeout == 8000


@pytest.mark.integration
def test_app_config_runtime_overrides_nested_dict_merge(tmp_path: Path) -> None:
    """Verify runtime overrides merge into existing dictionary payloads."""
    toml_path = tmp_path / "base_config.toml"
    toml_path.write_text(
        """
        [database]
        db_path = "data/base.db"
        busy_timeout = 3000
        """,
        encoding="utf-8",
    )

    overrides = {
        "database": {"busy_timeout": 9000},
    }

    cfg = AppConfig.load(config_path=toml_path, root_path=tmp_path, overrides=overrides)

    assert cfg.database.db_path == Path("data/base.db")
    assert cfg.database.busy_timeout == 9000


# ==============================================================================
# GROUP 4: DEFENSIVE ERROR BOUNDARIES
# Note: Validates ConfigParseError and ConfigValidationError mapping
# ==============================================================================


@pytest.mark.regression
def test_app_config_missing_file_raises_config_parse_error(tmp_path: Path) -> None:
    """Verify specifying non-existent configuration file raises ConfigParseError."""
    missing = tmp_path / "non_existent.toml"

    with pytest.raises(ConfigParseError) as exc_info:
        AppConfig.load(config_path=missing)

    assert exc_info.value.error_code == "ERR_CONFIG_FILE_NOT_FOUND"
    assert str(missing) in exc_info.value.message


@pytest.mark.regression
def test_app_config_missing_env_config_path_raises_config_parse_error(
    tmp_path: Path,
) -> None:
    """Verify GDA_CONFIG_PATH targeting missing file raises ConfigParseError."""
    env = {"GDA_CONFIG_PATH": str(tmp_path / "missing_env.toml")}
    with pytest.raises(ConfigParseError) as exc_info:
        AppConfig.load(root_path=tmp_path, env_vars=env)

    assert exc_info.value.error_code == "ERR_CONFIG_FILE_NOT_FOUND"


@pytest.mark.regression
def test_app_config_malformed_toml_raises_config_parse_error(tmp_path: Path) -> None:
    """Verify corrupt TOML syntax raises ConfigParseError with syntax_error details."""
    bad_toml = tmp_path / "corrupt.toml"
    bad_toml.write_text("[section\nunclosed = true", encoding="utf-8")

    with pytest.raises(ConfigParseError) as exc_info:
        AppConfig.load(config_path=bad_toml)

    assert exc_info.value.error_code == "ERR_CONFIG_TOML_PARSE"
    assert "syntax_error" in exc_info.value.details


@pytest.mark.regression
def test_app_config_invalid_data_raises_config_validation_error() -> None:
    """Verify invalid types in overrides raise ConfigValidationError."""
    with pytest.raises(ConfigValidationError) as exc_info:
        AppConfig.load(overrides={"database": {"busy_timeout": 50}})

    assert exc_info.value.error_code == "ERR_CONFIG_VALIDATION"
    assert "cause" in exc_info.value.details
