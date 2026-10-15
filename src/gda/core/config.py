# Name: config.py
# Path: src/gda/core/config.py
# Version: 1.0.0+build.r7

"""Multi-tiered configuration engine for GDA Core components.

Operational Role:
    Defines strongly-typed Pydantic schemas for database, logging, and application
    configuration. Resolves values across precedence tiers: hardcoded defaults,
    pyproject.toml, custom TOML configuration files, environment variables,
    and explicit runtime overrides.

Classes:
    DatabaseConfig: Database connection and pool settings.
    LoggingConfig: Logging levels, formats, and persistence routing.
    AppConfig: Root application configuration aggregator.
"""

from __future__ import annotations

import os
import tomllib
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator

from gda.core.errors import ConfigParseError, ConfigValidationError

__version__ = "1.0.0+build.r7"


class ImmutableBaseModel(BaseModel):
    """Base model enforcing immutability and forbidding undeclared attributes."""

    model_config = ConfigDict(frozen=True, extra="forbid")


class DatabaseConfig(ImmutableBaseModel):
    """Database connection and connection pool configuration parameters."""

    host: str = Field(default="localhost", min_length=1)
    port: int = Field(default=5432, ge=1, le=65535)
    database: str = Field(default="genealogy_archive", min_length=1)
    username: str = Field(default="gda_admin", min_length=1)
    password: SecretStr = Field(default=SecretStr(""))
    pool_size: int = Field(default=5, ge=1, le=50)

    @property
    def connection_string(self) -> str:
        """Render database connection string with password masked."""
        if not self.username:
            auth = ""
        elif self.password.get_secret_value():
            auth = f"{self.username}:********@"
        else:
            auth = f"{self.username}@"
        return f"postgresql://{auth}{self.host}:{self.port}/{self.database}"


class LoggingConfig(ImmutableBaseModel):
    """Structured logging configuration parameters."""

    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO"
    )
    log_to_console: bool = Field(default=True)
    log_to_file: bool = Field(default=False)
    log_file_path: str = Field(default="logs/gda.log")
    max_bytes: int = Field(default=10_485_760, ge=1024)
    backup_count: int = Field(default=5, ge=0)

    @field_validator("level", mode="before")
    @classmethod
    def normalize_level(cls, value: Any) -> Any:
        """Coerce logging level strings to uppercase."""
        if isinstance(value, str):
            return value.upper()
        return value


class AppConfig(ImmutableBaseModel):
    """Master application configuration container aggregating subsystem settings."""

    app_name: str = Field(default="Genealogy Digital Archive", min_length=1)
    environment: Literal["development", "testing", "staging", "production"] = Field(
        default="development"
    )
    debug: bool = Field(default=False)
    root_path: Path = Field(default_factory=Path.cwd)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    @field_validator("root_path", mode="before")
    @classmethod
    def validate_root_path(cls, value: Any) -> Path:
        """Validate root_path exists and is a directory."""
        if not isinstance(value, (str, Path)):
            raise ValueError(f"Invalid path type: {type(value)}")
        p = Path(value)
        if not p.exists():
            raise ValueError(f"Root path does not exist: {p}")
        if not p.is_dir():
            raise ValueError(f"Root path must be a directory: {p}")
        return p

    @property
    def data_path(self) -> Path:
        """Derived canonical path to data directory."""
        return self.root_path / "data"

    @property
    def logs_path(self) -> Path:
        """Derived canonical path to logs directory."""
        return self.root_path / "logs"

    @property
    def backups_path(self) -> Path:
        """Derived canonical path to backups directory."""
        return self.root_path / "backups"

    def ensure_directories(self) -> None:
        """Ensure all canonical root subdirectories exist on disk."""
        self.data_path.mkdir(parents=True, exist_ok=True)
        self.logs_path.mkdir(parents=True, exist_ok=True)
        self.backups_path.mkdir(parents=True, exist_ok=True)

    @classmethod
    def load(
        cls,
        config_path: str | Path | None = None,
        *,
        root_path: str | Path | None = None,
        env_prefix: str = "GDA_",
        env_vars: Mapping[str, str] | None = None,
        overrides: dict[str, Any] | None = None,
    ) -> Self:
        """Load and merge configuration across precedence tiers.

        Args:
            config_path: Explicit path to custom TOML config file.
            root_path: Base workspace directory anchor.
            env_prefix: Prefix for environment variable overrides.
            env_vars: Optional mapping of environment variables (defaults to os.environ).
            overrides: Direct runtime override dictionary.

        Returns:
            Instantiated and validated AppConfig instance.

        Raises:
            ConfigParseError: If TOML file cannot be read or parsed.
            ConfigValidationError: If merged values fail validation constraints.
        """
        payload: dict[str, Any] = {}
        active_env = os.environ if env_vars is None else env_vars

        # Determine effective root_path
        if root_path is not None:
            payload["root_path"] = root_path

        # Tier 3: TOML configuration discovery
        file_to_load: Path | None = None
        is_pyproject = False

        if config_path is not None:
            file_to_load = Path(config_path)
            if not file_to_load.exists():
                raise ConfigParseError(
                    f"Config file not found: {file_to_load}",
                    error_code="ERR_CONFIG_FILE_NOT_FOUND",
                    details={"path": str(file_to_load)},
                )
        elif "GDA_CONFIG_PATH" in active_env:
            env_cfg = Path(active_env["GDA_CONFIG_PATH"])
            if not env_cfg.exists():
                raise ConfigParseError(
                    f"GDA_CONFIG_PATH target not found: {env_cfg}",
                    error_code="ERR_CONFIG_FILE_NOT_FOUND",
                    details={"path": str(env_cfg)},
                )
            file_to_load = env_cfg
        else:
            base = Path(root_path) if root_path else Path.cwd()
            dedicated_cfg = base / "gda_config.toml"
            pyproject_cfg = base / "pyproject.toml"

            if dedicated_cfg.exists():
                file_to_load = dedicated_cfg
            elif pyproject_cfg.exists():
                file_to_load = pyproject_cfg
                is_pyproject = True

        if file_to_load is not None:
            try:
                with open(file_to_load, "rb") as fh:
                    raw_toml = tomllib.load(fh)
                    if is_pyproject:
                        payload.update(raw_toml.get("tool", {}).get("gda", {}))
                    else:
                        payload.update(raw_toml)
            except tomllib.TOMLDecodeError as err:
                raise ConfigParseError(
                    f"Malformed TOML syntax in {file_to_load}: {err}",
                    error_code="ERR_CONFIG_TOML_PARSE",
                    details={"path": str(file_to_load), "syntax_error": str(err)},
                ) from err

        # Tier 2: Environment variables
        prefix_len = len(env_prefix)
        for env_key, env_val in active_env.items():
            if env_key.startswith(env_prefix) and env_key != "GDA_CONFIG_PATH":
                key = env_key[prefix_len:].lower()
                if "__" in key:
                    sec, sub = key.split("__", 1)
                    sec_dict = payload.setdefault(sec, {})
                    if isinstance(sec_dict, dict):
                        sec_dict[sub] = cls._coerce_env_val(env_val)
                else:
                    payload[key] = cls._coerce_env_val(env_val)

        # Tier 1: Explicit overrides
        if overrides:
            for k, v in overrides.items():
                if isinstance(v, dict) and isinstance(payload.get(k), dict):
                    payload[k] = {**payload[k], **v}
                else:
                    payload[k] = v

        try:
            return cls.model_validate(payload)
        except Exception as err:
            raise ConfigValidationError(
                f"Configuration validation failed: {err}",
                error_code="ERR_CONFIG_VALIDATION",
                details={"cause": str(err)},
            ) from err

    @staticmethod
    def _coerce_env_val(val: str) -> Any:
        """Coerce environment string values to boolean, integer, or original string."""
        if val.lower() in ("true", "1", "yes"):
            return True
        if val.lower() in ("false", "0", "no"):
            return False
        try:
            return int(val)
        except ValueError:
            return val
