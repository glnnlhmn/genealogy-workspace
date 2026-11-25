"""Path: src/gda/core/config.py

Multi-tiered configuration engine for GDA Core components.

Operational Role:
    Defines strongly-typed Pydantic schemas for database, logging, and application
    configuration. Supports multi-engine database connection strings (SQLite file/memory
    and client-server RDBMS engines with host, port, username, password, and db_name)
    and resolves environment-specific database targets (DEV, TEST, STAGING, PROD)
    from pyproject.toml, gda_config.toml, custom TOML files, environment variables,
    and runtime overrides.

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

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from gda.core.errors import ConfigParseError, ConfigValidationError
from gda.core.types import is_finite_number

__version__ = "1.0.0+build.20"

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
        if not isinstance(data, Mapping):
            return data

        mutable = dict(data)
        if "timeout_seconds" in mutable and "busy_timeout" not in mutable:
            raw_sec = mutable.pop("timeout_seconds")
            if not is_finite_number(raw_sec):
                raise ValueError(f"Invalid timeout_seconds value: {raw_sec!r}")
            mutable["busy_timeout"] = int(float(raw_sec) * 1000)
        else:
            mutable.pop("timeout_seconds", None)

        db_name_val = mutable.get("db_name")
        if isinstance(db_name_val, str) and db_name_val.strip() and "db_path" not in mutable:
            clean_name = db_name_val.strip()
            mutable["db_path"] = (
                clean_name
                if clean_name in (":memory:", "file::memory:")
                else Path("data") / clean_name
            )
        return mutable

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

        auth_segment = self._format_auth_segment()
        host_str = self.host or "localhost"
        host_segment = f"{host_str}:{self.port}" if self.port is not None else host_str
        return f"{self.engine}://{auth_segment}{host_segment}/{self.resolved_db_name}"

    def _format_auth_segment(self) -> str:
        """Format URL-encoded user[:password]@ segment for client-server URIs."""
        if not self.username:
            return ""
        user_enc = quote_plus(self.username)
        if self.password is not None:
            return f"{user_enc}:{quote_plus(self.password)}@"
        return f"{user_enc}@"


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
            return dict(env_entry["database"])

        db_fields = set(DatabaseConfig.model_fields.keys()) | {"timeout_seconds"}
        return {k: v for k, v in env_entry.items() if k in db_fields}

    @staticmethod
    def _resolve_config_file(
        config_path: str | Path | None,
        resolved_root: Path,
        env_source: Mapping[str, str],
        env_prefix: str,
    ) -> Path | None:
        """Locate the active TOML configuration file from explicit path, env var, or root_path."""
        explicit_target = config_path or env_source.get(f"{env_prefix}CONFIG_PATH")
        if explicit_target is not None:
            candidate = Path(explicit_target)
            if not candidate.exists():
                raise ConfigParseError(
                    f"Configuration file not found: {candidate}",
                    error_code="ERR_CONFIG_FILE_NOT_FOUND",
                    details={"config_path": str(candidate)},
                )
            return candidate

        for default_name in ("gda_config.toml", "pyproject.toml"):
            candidate = resolved_root / default_name
            if candidate.exists():
                return candidate
        return None

    @classmethod
    def _read_toml_file(cls, file_to_load: Path) -> dict[str, Any]:
        """Read and parse a TOML configuration file into a raw dictionary."""
        try:
            with file_to_load.open("rb") as f:
                raw_toml = tomllib.load(f)
        except tomllib.TOMLDecodeError as exc:
            raise ConfigParseError(
                f"Malformed TOML in {file_to_load}: {exc}",
                error_code="ERR_CONFIG_TOML_PARSE",
                details={"path": str(file_to_load)},
            ) from exc

        if file_to_load.name == "pyproject.toml":
            return dict(raw_toml.get("tool", {}).get("gda", {}))
        return dict(raw_toml.get("tool", {}).get("gda", raw_toml))

    @classmethod
    def _apply_toml_section(
        cls,
        merged: dict[str, Any],
        gda_section: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Merge [tool.gda] scalar, database, logging, and environment sections."""
        for key in ("app_name", "environment", "debug", "root_path"):
            if key in gda_section:
                merged[key] = gda_section[key]
        if isinstance(gda_section.get("database"), Mapping):
            merged["database"].update(gda_section["database"])
        if isinstance(gda_section.get("logging"), Mapping):
            merged["logging"].update(gda_section["logging"])

        environments_table = gda_section.get("environments")
        if isinstance(environments_table, Mapping):
            return dict(environments_table)
        return {}

    @classmethod
    def _apply_env_vars(
        cls,
        merged: dict[str, Any],
        env_source: Mapping[str, str],
        env_prefix: str,
    ) -> None:
        """Overlay prefixed environment variables onto the merged configuration dict."""
        config_path_key = f"{env_prefix}CONFIG_PATH"
        for key, raw_val in env_source.items():
            if not key.startswith(env_prefix) or key == config_path_key:
                continue
            parts = key[len(env_prefix) :].lower().split("__")
            coerced = cls._coerce_env_val(raw_val)
            if len(parts) == 1 and parts[0] in ("app_name", "environment", "debug", "root_path"):
                merged[parts[0]] = coerced
            elif parts[0] in ("database", "logging") and len(parts) == 2:
                merged[parts[0]][parts[1]] = coerced

    @staticmethod
    def _apply_overrides(merged: dict[str, Any], overrides: Mapping[str, Any]) -> None:
        """Apply explicit dictionary overrides onto the merged configuration payload."""
        for k, v in overrides.items():
            if k in ("database", "logging") and isinstance(v, Mapping):
                merged[k].update(v)
            else:
                merged[k] = v

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
        """Load and validate configuration across TOML, environment variables, and overrides.

        Precedence (lowest to highest):
            1. Schema defaults
            2. gda_config.toml, pyproject.toml [tool.gda], or explicit TOML file
            3. [tool.gda.environments.<ENV>] overlay (when env_name or environment matches)
            4. Environment variables (GDA_*, GDA_DATABASE__*, GDA_LOGGING__*)
            5. Explicit dictionary overrides

        Args:
            config_path: Optional explicit TOML configuration file path.
            root_path: Optional workspace root directory override.
            env_name: Optional target environment name or code (DEV, TEST, STAGING, PROD).
            env_prefix: Prefix for environment variable scanning (defaults to 'GDA_').
            env_vars: Optional mapping of environment variables (defaults to os.environ).
            overrides: Optional highest-precedence dictionary overrides.

        Returns:
            Validated, immutable AppConfig instance.

        Raises:
            ConfigParseError: If an explicit config_path is missing or TOML syntax fails.
            ConfigValidationError: If merged settings fail Pydantic schema validation.
        """
        merged: dict[str, Any] = {"database": {}, "logging": {}}
        if root_path is not None:
            merged["root_path"] = root_path

        resolved_root = Path(root_path) if root_path is not None else Path.cwd()
        env_source = env_vars if env_vars is not None else os.environ

        # --- Layer 1: Discover and Parse TOML File ---
        file_to_load = cls._resolve_config_file(config_path, resolved_root, env_source, env_prefix)
        environments_table: dict[str, Any] = {}
        if file_to_load is not None:
            gda_section = cls._read_toml_file(file_to_load)
            environments_table = cls._apply_toml_section(merged, gda_section)

        # --- Layer 2: [tool.gda.environments.<ENV>] Overlay & Environment Variables ---
        if env_name is not None:
            merged["environment"] = env_name

        if environments_table and (env_name is not None or "environment" in merged):
            target_env_key = str(
                env_source.get(f"{env_prefix}ENVIRONMENT") or merged["environment"]
            )
            merged["database"].update(
                cls._extract_env_db_settings(environments_table, target_env_key)
            )

        cls._apply_env_vars(merged, env_source, env_prefix)

        # --- Layer 3: Explicit Runtime Overrides & Validation ---
        if overrides:
            cls._apply_overrides(merged, overrides)

        try:
            return cls(**merged)
        except ValidationError as exc:
            raise ConfigValidationError(
                f"Configuration validation failed: {exc}",
                details={"errors": exc.errors()},
            ) from exc

    @staticmethod
    def _coerce_env_val(val: str) -> bool | int | str:
        """Coerce raw environment variable string to boolean, integer, or string."""
        lower = val.strip().lower()
        if lower in ("true", "1", "yes"):
            return True
        if lower in ("false", "0", "no"):
            return False
        if val.strip().isdigit():
            return int(val.strip())
        return val
