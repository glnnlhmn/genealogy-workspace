"""Path: src/gda/core/config.py

Multi-tiered configuration engine for GDA Core components.

Operational Role:
    Defines strongly-typed Pydantic schemas for database, logging, and application
    configuration. Supports multi-engine database connection strings (SQLite file/memory
    and client-server RDBMS engines with host, port, username, password, and db_name)
    and resolves environment-specific database targets (DEV, TEST, STAGING, PROD)
    from pyproject.toml, custom TOML files, environment variables, and runtime overrides.

Classes:
    DatabaseConfig: Multi-engine connection parameters, credentials, and SQLite PRAGMA settings.
    LoggingConfig: Logging levels, formats, and persistence routing.
    AppConfig: Root application configuration aggregator.
"""

from __future__ import annotations

import os
import tomllib
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Literal, Self
from urllib.parse import quote_plus

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from gda.core.errors import ConfigParseError, ConfigValidationError

__version__ = "1.0.0+build.15"

__all__ = [
    "AppConfig",
    "DatabaseConfig",
    "ImmutableBaseModel",
    "LoggingConfig",
]

_ENV_ALIAS_TO_CANONICAL: dict[str, Literal["development", "testing", "staging", "production"]] = {
    "dev": "development",
    "development": "development",
    "test": "testing",
    "testing": "testing",
    "stage": "staging",
    "staging": "staging",
    "prod": "production",
    "production": "production",
}

_CANONICAL_TO_ENV_CODE: dict[str, Literal["DEV", "TEST", "STAGING", "PROD"]] = {
    "development": "DEV",
    "testing": "TEST",
    "staging": "STAGING",
    "production": "PROD",
}


class ImmutableBaseModel(BaseModel):
    """Base model enforcing immutability and forbidding undeclared attributes."""

    model_config = ConfigDict(frozen=True, extra="forbid")


class DatabaseConfig(ImmutableBaseModel):
    """Database connection, authentication, and PRAGMA configuration parameters."""

    engine: str = Field(default="sqlite", min_length=1)
    db_name: str | None = Field(default=None)
    db_path: Path | str = Field(default=Path("data/archive.db"))
    host: str | None = Field(default=None)
    port: int | None = Field(default=None, ge=1, le=65535)
    username: str | None = Field(default=None)
    password: str | None = Field(default=None)
    dsn_override: str | None = Field(default=None)
    busy_timeout: int = Field(default=5000, ge=100, le=60000)
    journal_mode: str = Field(default="WAL")
    foreign_keys: bool = Field(default=True)
    synchronous: str = Field(default="NORMAL")

    @field_validator("engine", mode="before")
    @classmethod
    def normalize_engine(cls, value: Any) -> str:
        """Normalize database engine/dialect identifier to lowercase."""
        if isinstance(value, str) and value.strip():
            return value.strip().lower()
        raise ValueError(f"Invalid engine value: {value!r}")

    @field_validator("db_path", mode="before")
    @classmethod
    def normalize_db_path(cls, value: Any) -> Path | str:
        """Coerce filesystem strings to Path instances while preserving in-memory tokens."""
        if isinstance(value, str):
            clean = value.strip()
            if clean in (":memory:", "file::memory:"):
                return clean
            return Path(clean)
        if isinstance(value, Path):
            return value
        raise ValueError(f"Invalid db_path type: {type(value)}")

    @model_validator(mode="before")
    @classmethod
    def synchronize_db_name_and_path(cls, data: Any) -> Any:
        """Derive db_path from db_name when db_name is given without an explicit db_path."""
        if isinstance(data, Mapping):
            mutable = dict(data)
            if "timeout_seconds" in mutable and "busy_timeout" not in mutable:
                sec = float(mutable.pop("timeout_seconds"))
                mutable["busy_timeout"] = int(sec * 1000)
            else:
                mutable.pop("timeout_seconds", None)

            db_name_val = mutable.get("db_name")
            if isinstance(db_name_val, str) and db_name_val.strip() and "db_path" not in mutable:
                clean_name = db_name_val.strip()
                if clean_name in (":memory:", "file::memory:"):
                    mutable["db_path"] = clean_name
                else:
                    mutable["db_path"] = Path("data") / clean_name
            return mutable
        return data

    @property
    def is_in_memory(self) -> bool:
        """Check if target database is an ephemeral in-memory instance."""
        return str(self.db_path) in (":memory:", "file::memory:")

    @property
    def resolved_db_name(self) -> str:
        """Return explicit db_name or derive it from db_path."""
        if self.db_name and self.db_name.strip():
            return self.db_name.strip()
        if self.is_in_memory:
            return ":memory:"
        return Path(self.db_path).name

    @property
    def connection_string(self) -> str:
        """Render URI connection string for SQLite or client-server database engines."""
        if self.dsn_override and self.dsn_override.strip():
            return self.dsn_override.strip()

        if self.engine == "sqlite" or self.engine.startswith("sqlite+"):
            if self.is_in_memory:
                return f"{self.engine}:///:memory:"
            return f"{self.engine}:///{Path(self.db_path).as_posix()}"

        auth_segment = ""
        if self.username:
            user_enc = quote_plus(self.username)
            if self.password is not None:
                pw_enc = quote_plus(self.password)
                auth_segment = f"{user_enc}:{pw_enc}@"
            else:
                auth_segment = f"{user_enc}@"

        host_str = self.host or "localhost"
        host_segment = f"{host_str}:{self.port}" if self.port is not None else host_str
        return f"{self.engine}://{auth_segment}{host_segment}/{self.resolved_db_name}"


class LoggingConfig(ImmutableBaseModel):
    """Structured logging configuration parameters."""

    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(default="INFO")
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

    @field_validator("environment", mode="before")
    @classmethod
    def normalize_environment(cls, value: Any) -> Any:
        """Normalize short environment codes (DEV, TEST, STAGING, PROD) to canonical literals."""
        if isinstance(value, str):
            mapped = _ENV_ALIAS_TO_CANONICAL.get(value.strip().lower())
            if mapped is not None:
                return mapped
        return value

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
    def env_code(self) -> Literal["DEV", "TEST", "STAGING", "PROD"]:
        """Return the canonical uppercase environment key (DEV, TEST, STAGING, PROD)."""
        return _CANONICAL_TO_ENV_CODE[self.environment]

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

    @staticmethod
    def _extract_env_db_settings(
        environments_table: Mapping[str, Any],
        target_env: str,
    ) -> dict[str, Any]:
        """Extract database settings for a target environment from [tool.gda.environments]."""
        canonical = _ENV_ALIAS_TO_CANONICAL.get(target_env.strip().lower())
        env_code = _CANONICAL_TO_ENV_CODE.get(canonical or "", target_env.strip().upper())

        env_entry: Mapping[str, Any] | None = None
        for candidate in (env_code, env_code.lower(), canonical):
            if candidate and candidate in environments_table:
                raw_entry = environments_table[candidate]
                if isinstance(raw_entry, Mapping):
                    env_entry = raw_entry
                    break

        if env_entry is None:
            return {}

        if isinstance(env_entry.get("database"), Mapping):
            db_sec = dict(env_entry["database"])
        else:
            db_fields = set(DatabaseConfig.model_fields.keys()) | {"timeout_seconds"}
            db_sec = {k: v for k, v in env_entry.items() if k in db_fields}

        return db_sec

    @classmethod
    def for_environment(
        cls,
        env_name: str,
        root_path: str | Path | None = None,
        *,
        config_path: str | Path | None = None,
    ) -> Self:
        """Load AppConfig and resolve [tool.gda.environments.<ENV>] database settings."""
        return cls.load(
            config_path=config_path,
            root_path=root_path,
            env_name=env_name,
        )

    @classmethod
    def load(
        cls,
        config_path: str | Path | None = None,
        *,
        root_path: str | Path | None = None,
        env_name: str | None = None,
        env_prefix: str = "GDA_",
        env_vars: Mapping[str, str] | None = None,
        overrides: dict[str, Any] | None = None,
    ) -> Self:
        """Load and merge configuration across precedence tiers.

        Args:
            config_path: Explicit path to custom TOML config file.
            root_path: Base workspace directory anchor.
            env_name: Optional target environment ('DEV', 'TEST', 'STAGING', 'PROD')
                to resolve from [tool.gda.environments.<ENV>].
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
        environments_table: Mapping[str, Any] = {}

        if root_path is not None:
            payload["root_path"] = root_path

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
            if file_to_load.name == "pyproject.toml":
                is_pyproject = True
        elif "GDA_CONFIG_PATH" in active_env:
            env_cfg = Path(active_env["GDA_CONFIG_PATH"])
            if not env_cfg.exists():
                raise ConfigParseError(
                    f"GDA_CONFIG_PATH target not found: {env_cfg}",
                    error_code="ERR_CONFIG_FILE_NOT_FOUND",
                    details={"path": str(env_cfg)},
                )
            file_to_load = env_cfg
            if file_to_load.name == "pyproject.toml":
                is_pyproject = True
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
                if is_pyproject or "tool" in raw_toml:
                    gda_section = raw_toml.get("tool", {}).get("gda", {})
                    if isinstance(gda_section.get("environments"), Mapping):
                        environments_table = gda_section["environments"]
                    valid_keys = cls.model_fields.keys()
                    filtered = {k: v for k, v in gda_section.items() if k in valid_keys}
                    payload.update(filtered)
                else:
                    if isinstance(raw_toml.get("environments"), Mapping):
                        environments_table = dict(raw_toml["environments"])
                    raw_copy = {k: v for k, v in raw_toml.items() if k != "environments"}
                    payload.update(raw_copy)
            except tomllib.TOMLDecodeError as err:
                raise ConfigParseError(
                    f"Malformed TOML syntax in {file_to_load}: {err}",
                    error_code="ERR_CONFIG_TOML_PARSE",
                    details={"path": str(file_to_load), "syntax_error": str(err)},
                ) from err

        if env_name is not None:
            payload["environment"] = env_name

        # Resolve [tool.gda.environments.<ENV>] when env_name is explicitly requested
        # or when [tool.gda.database] was not explicitly set in pyproject.toml
        if environments_table and (env_name is not None or "database" in environments_table):
            target_env = str(env_name or payload.get("environment", "development"))
            env_db = cls._extract_env_db_settings(environments_table, target_env)
            if env_db:
                base_db = payload.get("database")
                if isinstance(base_db, Mapping):
                    payload["database"] = {**base_db, **env_db}
                else:
                    payload["database"] = env_db

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
