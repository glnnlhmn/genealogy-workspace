"""Path: src/gda/core/__init__.py

Core infrastructure, configuration, error contracts, and runtime introspection.

Operational Role:
    Unified public export facade for foundational framework classes:
    AppConfig, DatabaseConfig, LoggingConfig, structured exceptions,
    introspective mixins, logging services, temporal formatters, cryptographic
    hashing, and canonical scalar type definitions.
"""

from __future__ import annotations

from gda.core.config import AppConfig, DatabaseConfig, ImmutableBaseModel, LoggingConfig
from gda.core.dates import (
    format_utc_timestamp,
    parse_iso_date_parts,
    validate_iso_date,
    validate_iso_timestamp,
)
from gda.core.errors import (
    ConfigError,
    ConfigParseError,
    ConfigValidationError,
    GenealogyDeskError,
    ModelError,
    ModelFormatError,
    ModelPrefixMismatchError,
    ModelRangeError,
)
from gda.core.hashes import (
    is_valid_sha256,
    sha256_bytes,
    sha256_file,
    sha256_text,
)
from gda.core.introspectable import IntrospectableMixin
from gda.core.logging import ConsoleFormatter, GDALogger, JsonFormatter
from gda.core.types import (
    ENTITY_ID_PATTERNS,
    ISO_DATE_FMT,
    ISO_DATE_PATTERN,
    ISO_DATE_REGEX,
    ISO_MONTH_FMT,
    ISO_TIMESTAMP_FMT,
    ISO_TIMESTAMP_PATTERN,
    ISO_TIMESTAMP_REGEX,
    ISO_YEAR_FMT,
    SHA256_PATTERN,
    SHA256_REGEX,
    UUID_V4_PATTERN,
    UUID_V4_REGEX,
)

__version__ = "1.0.0+build.6"

__all__ = [
    "AppConfig",
    "ConfigError",
    "ConfigParseError",
    "ConfigValidationError",
    "ConsoleFormatter",
    "DatabaseConfig",
    "ENTITY_ID_PATTERNS",
    "GDALogger",
    "GenealogyDeskError",
    "ISO_DATE_FMT",
    "ISO_DATE_PATTERN",
    "ISO_DATE_REGEX",
    "ISO_MONTH_FMT",
    "ISO_TIMESTAMP_FMT",
    "ISO_TIMESTAMP_PATTERN",
    "ISO_TIMESTAMP_REGEX",
    "ISO_YEAR_FMT",
    "ImmutableBaseModel",
    "IntrospectableMixin",
    "JsonFormatter",
    "LoggingConfig",
    "ModelError",
    "ModelFormatError",
    "ModelPrefixMismatchError",
    "ModelRangeError",
    "SHA256_PATTERN",
    "SHA256_REGEX",
    "UUID_V4_PATTERN",
    "UUID_V4_REGEX",
    "format_utc_timestamp",
    "is_valid_sha256",
    "parse_iso_date_parts",
    "sha256_bytes",
    "sha256_file",
    "sha256_text",
    "validate_iso_date",
    "validate_iso_timestamp",
]
