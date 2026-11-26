"""Path: tests/test_gda/test_core/test_core_config_4_5_6.py

Error handling, integration, and integrity test suite for gda.core.config (Groups 4-6).

Operational Role:
    Covers Groups 4-6 of the 6-group catalog for gda.core.config:
    - GROUP 4: Error Handling & Validation Failures (schema bounds, empty db_path,
      env coercion for binary strings and Unicode digits, bool/NaN/Inf guards,
      and ConfigParseError / ConfigValidationError).
    - GROUP 5: Filesystem, CLI & Integration (directory provisioning, TOML and
      pyproject.toml loading, for_environment, GDA_CONFIG_PATH, symlinked TOML,
      and OSError wrapping).
    - GROUP 6: Integrity & Invariants (SecretStr password masking, frozen
      immutability, and extra='forbid' contracts across all config models).

Test Structure & Protocol:
    - Atomized & parametrized tests: 1:1 behavioral contract mapping.
    - Fully decorated: 5-marker taxonomy (unit, regression, integration, integrity).
    - Companion module: test_core_config_1_2_3.py (Groups 1-3).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from pydantic import SecretStr, ValidationError

from gda.core.config import AppConfig, DatabaseConfig, LoggingConfig
from gda.core.errors import ConfigParseError, ConfigValidationError

__version__ = "1.0.0+build.2"


# ==============================================================================
# GROUP 4: Error Handling & Validation Failures
# Note: Schema bounds, env coercion safety, and TOML/validation loader errors.
# ==============================================================================


@pytest.mark.regression
def test_database_config_invalid_fields_raise() -> None:
    """Verify DatabaseConfig rejects invalid db_path, blank engine, and non-mapping input."""
    with pytest.raises(ValidationError, match="Invalid db_path type"):
        DatabaseConfig(db_path=12345)  # type: ignore[arg-type]

    with pytest.raises(ValidationError, match="Invalid engine value"):
        DatabaseConfig(engine=" ")

    with pytest.raises(ValidationError):
        DatabaseConfig.model_validate("not-a-mapping")


@pytest.mark.regression
@pytest.mark.unit
@pytest.mark.parametrize("blank_path", ["", "   ", "\t\n"])
def test_database_config_rejects_empty_or_whitespace_db_path(blank_path: str) -> None:
    """Verify DatabaseConfig rejects empty or whitespace-only db_path values."""
    with pytest.raises(ValidationError, match="db_path cannot be empty"):
        DatabaseConfig(db_path=blank_path)


@pytest.mark.regression
@pytest.mark.parametrize("bad_timeout", [50, 70000])
def test_database_config_busy_timeout_boundary_validation(bad_timeout: int) -> None:
    """Verify DatabaseConfig rejects busy_timeout outside 100-60000 ms."""
    with pytest.raises(ValidationError):
        DatabaseConfig(busy_timeout=bad_timeout)


@pytest.mark.regression
@pytest.mark.parametrize("bad_port", [0, -1, 65536, 70000])
def test_database_config_rejects_out_of_range_ports(bad_port: int) -> None:
    """Verify DatabaseConfig rejects network ports outside 1-65535."""
    with pytest.raises(ValidationError):
        DatabaseConfig(port=bad_port)


@pytest.mark.regression
@pytest.mark.parametrize(
    "bad_timeout_sec",
    [True, False, float("nan"), float("inf"), float("-inf")],
)
def test_database_config_rejects_bool_nan_inf_timeout_seconds(
    bad_timeout_sec: Any,
) -> None:
    """Verify timeout_seconds rejects bool, NaN, and Inf."""
    with pytest.raises(ValidationError):
        DatabaseConfig.model_validate({"timeout_seconds": bad_timeout_sec})


@pytest.mark.regression
@pytest.mark.unit
@pytest.mark.parametrize(
    ("env_map", "expected_app_name", "expected_debug", "expected_log_to_file"),
    [
        (
            {"GDA_APP_NAME": "1", "GDA_DEBUG": "1", "GDA_LOGGING__LOG_TO_FILE": "0"},
            "1",
            True,
            False,
        ),
        (
            {"GDA_APP_NAME": "0", "GDA_DEBUG": "0", "GDA_LOGGING__LOG_TO_FILE": "1"},
            "0",
            False,
            True,
        ),
        (
            {"GDA_APP_NAME": "²", "GDA_DEBUG": "false", "GDA_LOGGING__LOG_TO_FILE": "true"},
            "²",
            False,
            True,
        ),
    ],
)
def test_app_config_env_coercion_preserves_binary_strings_and_unicode_digits(
    tmp_path: Path,
    env_map: dict[str, str],
    expected_app_name: str,
    expected_debug: bool,
    expected_log_to_file: bool,
) -> None:
    """Verify '0'/'1' stay strings on str fields, coerce on bool fields, and '²' never crashes."""
    cfg = AppConfig.load(
        root_path=tmp_path,
        env_vars={**env_map, "GDA_DATABASE__PASSWORD": "0"},
    )
    assert cfg.app_name == expected_app_name
    assert cfg.debug is expected_debug
    assert cfg.logging.log_to_file is expected_log_to_file
    assert cfg.database.password is not None
    assert cfg.database.password.get_secret_value() == "0"


@pytest.mark.regression
@pytest.mark.parametrize("bad_level", [12345, "VERBOSE"])
def test_logging_config_rejects_invalid_levels(bad_level: Any) -> None:
    """Verify LoggingConfig rejects non-string and unrecognized log level strings."""
    with pytest.raises(ValidationError):
        LoggingConfig(level=bad_level)


@pytest.mark.regression
def test_logging_config_rejects_invalid_rotation_bounds() -> None:
    """Verify LoggingConfig rejects max_bytes < 1024 and negative backup_count."""
    with pytest.raises(ValidationError):
        LoggingConfig(max_bytes=512)

    with pytest.raises(ValidationError):
        LoggingConfig(backup_count=-1)


@pytest.mark.regression
def test_app_config_root_path_and_environment_validation_errors(tmp_path: Path) -> None:
    """Verify AppConfig rejects invalid environment, bad root_path types, missing dirs, and files."""
    with pytest.raises(ValidationError):
        AppConfig(root_path=tmp_path, environment=12345)  # type: ignore[arg-type]

    with pytest.raises(ValidationError, match="Invalid path type"):
        AppConfig(root_path=12345)  # type: ignore[arg-type]

    with pytest.raises(ValidationError, match="Root path does not exist"):
        AppConfig(root_path=tmp_path / "does_not_exist")

    file_target = tmp_path / "regular_file.txt"
    file_target.write_text("content", encoding="utf-8")
    with pytest.raises(ValidationError, match="Root path must be a directory"):
        AppConfig(root_path=file_target)


@pytest.mark.regression
def test_app_config_missing_explicit_or_env_config_path_raises(tmp_path: Path) -> None:
    """Verify missing explicit config_path or GDA_CONFIG_PATH raises ConfigParseError."""
    missing = tmp_path / "missing.toml"
    with pytest.raises(ConfigParseError) as exc_direct:
        AppConfig.load(config_path=missing)
    assert exc_direct.value.error_code == "ERR_CONFIG_FILE_NOT_FOUND"

    with pytest.raises(ConfigParseError) as exc_env:
        AppConfig.load(env_vars={"GDA_CONFIG_PATH": str(missing)})
    assert exc_env.value.error_code == "ERR_CONFIG_FILE_NOT_FOUND"


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
        AppConfig.load(root_path=tmp_path, overrides={"environment": "invalid_env"})
    assert exc_info.value.error_code == "ERR_CONFIG_VALIDATION"


# ==============================================================================
# GROUP 5: Filesystem, CLI & Integration
# Note: Directory creation, TOML/pyproject discovery, symlinks, and OSError wrapping.
# ==============================================================================


@pytest.mark.integration
def test_app_config_ensure_directories(tmp_path: Path) -> None:
    """Verify ensure_directories creates data, logs, and backups directories on disk."""
    cfg = AppConfig(root_path=tmp_path)
    cfg.ensure_directories()
    assert cfg.data_path.is_dir()
    assert cfg.logs_path.is_dir()
    assert cfg.backups_path.is_dir()


@pytest.mark.integration
def test_app_config_load_from_custom_toml_and_environments(tmp_path: Path) -> None:
    """Verify AppConfig.load(config_path) parses custom TOML files and environment tables."""
    toml_path = tmp_path / "custom_config.toml"
    toml_path.write_text(
        'app_name = "Custom Archive"\nenvironment = "staging"\ndebug = true\n\n'
        '[database]\ndb_path = "data/custom.db"\nbusy_timeout = 8000\n\n'
        '[environments.STAGING.database]\ndb_name = "gda_staging.db"\n'
        'db_path = "data/db/gda_staging.db"\n\n[logging]\nlevel = "WARNING"\n',
        encoding="utf-8",
    )

    cfg = AppConfig.load(config_path=toml_path, root_path=tmp_path, env_name="STAGING")
    assert cfg.app_name == "Custom Archive"
    assert cfg.environment == "staging"
    assert cfg.debug is True
    assert cfg.database.db_name == "gda_staging.db"
    assert cfg.database.db_path == Path("data/db/gda_staging.db")
    assert cfg.database.busy_timeout == 8000
    assert cfg.logging.level == "WARNING"

    cfg_unmapped = AppConfig.load(config_path=toml_path, root_path=tmp_path, env_name="PROD")
    assert cfg_unmapped.environment == "production"
    assert cfg_unmapped.database.db_path == Path("data/custom.db")


@pytest.mark.integration
def test_app_config_for_environment_from_pyproject(tmp_path: Path) -> None:
    """Verify AppConfig.for_environment resolves DEV and PROD from pyproject.toml."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[tool.gda]\napp_name = "GDA Environment Suite"\n\n'
        '[tool.gda.environments.DEV]\ndb_name = "gda_dev.db"\n'
        'db_path = "data/db/gda_dev.db"\ntimeout_seconds = 30.0\n\n'
        '[tool.gda.environments.PROD]\ndb_name = "gda_prod.db"\n'
        'db_path = "data/db/gda_prod.db"\ntimeout_seconds = 45.0\n',
        encoding="utf-8",
    )

    dev_cfg = AppConfig.for_environment("DEV", root_path=tmp_path)
    assert dev_cfg.environment == "development"
    assert dev_cfg.database.db_name == "gda_dev.db"
    assert dev_cfg.database.busy_timeout == 30000

    prod_cfg = AppConfig.for_environment("PROD", root_path=tmp_path, config_path=pyproject)
    assert prod_cfg.environment == "production"
    assert prod_cfg.database.db_name == "gda_prod.db"
    assert prod_cfg.database.busy_timeout == 45000

    assert AppConfig._extract_env_db_settings({"DEV": "not-a-dict"}, "DEV") == {}


@pytest.mark.integration
def test_app_config_discovers_gda_config_pyproject_and_env_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify automatic discovery of gda_config.toml, pyproject.toml, and GDA_CONFIG_PATH."""
    dedicated = tmp_path / "gda_config.toml"
    dedicated.write_text('app_name = "Dedicated TOML"\n', encoding="utf-8")
    assert AppConfig.load(root_path=tmp_path).app_name == "Dedicated TOML"
    dedicated.unlink()

    monkeypatch.chdir(tmp_path)
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[tool.gda]\napp_name = "PyProject GDA"\n[tool.gda.logging]\nlevel = "ERROR"\n',
        encoding="utf-8",
    )
    cfg_py = AppConfig.load(root_path=tmp_path)
    assert cfg_py.app_name == "PyProject GDA"
    assert cfg_py.logging.level == "ERROR"

    custom_env = tmp_path / "custom_env.toml"
    custom_env.write_text('app_name = "Custom Env Directed"\n', encoding="utf-8")
    cfg_env = AppConfig.load(
        root_path=tmp_path,
        env_vars={"GDA_CONFIG_PATH": str(custom_env)},
    )
    assert cfg_env.app_name == "Custom Env Directed"


@pytest.mark.integration
@pytest.mark.regression
def test_app_config_load_follows_symlinked_toml_file(tmp_path: Path) -> None:
    """Verify AppConfig.load reads configuration through a symlinked TOML file."""
    target = tmp_path / "real_config.toml"
    link = tmp_path / "linked_config.toml"
    target.write_text('app_name = "Symlinked Archive"\n', encoding="utf-8")
    try:
        link.symlink_to(target)
    except OSError as exc:
        pytest.skip(f"Symlink creation not permitted in environment: {exc}")

    cfg = AppConfig.load(config_path=link, root_path=tmp_path)
    assert cfg.app_name == "Symlinked Archive"


@pytest.mark.integration
@pytest.mark.regression
def test_app_config_load_wraps_os_error_on_locked_or_directory_toml(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify AppConfig.load wraps PermissionError and directory config_path in ConfigParseError."""
    # Directory passed as config_path triggers OSError / IsADirectoryError on open.
    dir_path = tmp_path / "config_dir"
    dir_path.mkdir()
    with pytest.raises(ConfigParseError) as exc_dir:
        AppConfig.load(config_path=dir_path, root_path=tmp_path)
    assert exc_dir.value.error_code == "ERR_CONFIG_TOML_PARSE"

    # Simulated Windows file lock triggers PermissionError on open.
    locked_toml = tmp_path / "locked.toml"
    locked_toml.write_text('app_name = "Locked"\n', encoding="utf-8")

    def _deny_open(self: Path, *args: Any, **kwargs: Any) -> Any:
        raise PermissionError(f"Access denied: {self}")

    monkeypatch.setattr(Path, "open", _deny_open)
    with pytest.raises(ConfigParseError, match="Access denied") as exc_perm:
        AppConfig.load(config_path=locked_toml, root_path=tmp_path)
    assert exc_perm.value.error_code == "ERR_CONFIG_TOML_PARSE"


# ==============================================================================
# GROUP 6: Integrity & Invariants
# Note: SecretStr password masking, frozen immutability, and extra='forbid'.
# ==============================================================================


@pytest.mark.integrity
@pytest.mark.unit
def test_database_config_password_masks_secret_value() -> None:
    """Verify DatabaseConfig.password masks plaintext in repr/str/model_dump via SecretStr."""
    cfg = DatabaseConfig.model_validate({"password": "top_secret_value"})
    assert isinstance(cfg.password, SecretStr)
    assert cfg.password.get_secret_value() == "top_secret_value"
    assert "top_secret_value" not in repr(cfg)
    assert "top_secret_value" not in str(cfg)
    assert "top_secret_value" not in str(cfg.model_dump())


@pytest.mark.integrity
@pytest.mark.regression
def test_config_models_enforce_frozen_immutability(tmp_path: Path) -> None:
    """Verify DatabaseConfig, LoggingConfig, and AppConfig forbid post-init mutation."""
    db_cfg = DatabaseConfig()
    with pytest.raises(ValidationError):
        db_cfg.busy_timeout = 10000  # type: ignore[misc]

    log_cfg = LoggingConfig()
    with pytest.raises(ValidationError):
        log_cfg.level = "DEBUG"  # type: ignore[misc]

    app_cfg = AppConfig(root_path=tmp_path)
    with pytest.raises(ValidationError):
        app_cfg.debug = True  # type: ignore[misc]


@pytest.mark.integrity
@pytest.mark.regression
def test_config_models_forbid_undeclared_extra_attributes() -> None:
    """Verify all config models configured with extra='forbid' reject undeclared fields."""
    with pytest.raises(ValidationError):
        DatabaseConfig(extra_param="disallowed")  # type: ignore[call-arg]

    with pytest.raises(ValidationError):
        LoggingConfig(unknown_flag=True)  # type: ignore[call-arg]

    with pytest.raises(ValidationError):
        AppConfig(unrecognized_setting=123)  # type: ignore[call-arg]
