"""Path: src/gda/core/__init__.py

Core infrastructure, configuration, error contracts, and runtime introspection.

Operational Role:
    Unified public export facade for foundational framework classes:
    AppConfig, DatabaseConfig, LoggingConfig, structured exceptions,
    introspective mixins, logging services, temporal formatters, cryptographic
    hashing, controlled vocabulary enums, domain constants, and canonical
    regex/type guard primitives.
"""

from __future__ import annotations

from gda.core import constants, enums
from gda.core.config import (
    AppConfig,
    DatabaseConfig,
    ImmutableBaseModel,
    LoggingConfig,
)
from gda.core.dates import (
    calculate_age_years,
    format_utc_timestamp,
    parse_iso_date_parts,
    parse_iso_timestamp,
    utc_now_iso,
    utc_today_iso,
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
from gda.core.logging import (
    ConsoleFormatter,
    GDALogger,
    JsonFormatter,
)
from gda.core.types import (
    ATOM_ID_PATTERN,
    ATOM_ID_REGEX,
    ENTITY_ID_PATTERNS,
    ENTITY_ID_REGEXES,
    ENTITY_URN_PATTERNS,
    ENTITY_URN_REGEXES,
    ENUM_KEY_SEPARATOR_PATTERN,
    ENUM_KEY_SEPARATOR_REGEX,
    ISO_DATE_FMT,
    ISO_DATE_PATTERN,
    ISO_DATE_REGEX,
    ISO_MONTH_FMT,
    ISO_TIMESTAMP_FMT,
    ISO_TIMESTAMP_PATTERN,
    ISO_TIMESTAMP_REGEX,
    ISO_YEAR_FMT,
    NEWS_CATEGORY_PATTERN,
    NEWS_CATEGORY_REGEX,
    PUB_CODE_PATTERN,
    PUB_CODE_REGEX,
    SHA256_PATTERN,
    SHA256_REGEX,
    SQL_IDENTIFIER_PATTERN,
    SQL_IDENTIFIER_REGEX,
    URN_BASE_PATTERN,
    URN_BASE_REGEX,
    URN_PATTERNS,
    URN_REGEXES,
    UUID_V4_PATTERN,
    UUID_V4_REGEX,
    is_finite_number,
    is_strict_int,
)

__version__ = "1.0.0+build.14"

__all__ = [
    "ATOM_ID_PATTERN",  # types.py
    "ATOM_ID_REGEX",  # types.py
    "AppConfig",  # config.py
    "ConfigError",  # errors.py
    "ConfigParseError",  # errors.py
    "ConfigValidationError",  # errors.py
    "ConsoleFormatter",  # logging.py
    "DatabaseConfig",  # config.py
    "ENTITY_ID_PATTERNS",  # types.py
    "ENTITY_ID_REGEXES",  # types.py
    "ENTITY_URN_PATTERNS",  # types.py
    "ENTITY_URN_REGEXES",  # types.py
    "ENUM_KEY_SEPARATOR_PATTERN",  # types.py
    "ENUM_KEY_SEPARATOR_REGEX",  # types.py
    "GDALogger",  # logging.py
    "GenealogyDeskError",  # errors.py
    "ISO_DATE_FMT",  # types.py
    "ISO_DATE_PATTERN",  # types.py
    "ISO_DATE_REGEX",  # types.py
    "ISO_MONTH_FMT",  # types.py
    "ISO_TIMESTAMP_FMT",  # types.py
    "ISO_TIMESTAMP_PATTERN",  # types.py
    "ISO_TIMESTAMP_REGEX",  # types.py
    "ISO_YEAR_FMT",  # types.py
    "ImmutableBaseModel",  # config.py
    "IntrospectableMixin",  # introspectable.py
    "JsonFormatter",  # logging.py
    "LoggingConfig",  # config.py
    "ModelError",  # errors.py
    "ModelFormatError",  # errors.py
    "ModelPrefixMismatchError",  # errors.py
    "ModelRangeError",  # errors.py
    "NEWS_CATEGORY_PATTERN",  # types.py
    "NEWS_CATEGORY_REGEX",  # types.py
    "PUB_CODE_PATTERN",  # types.py
    "PUB_CODE_REGEX",  # types.py
    "SHA256_PATTERN",  # types.py
    "SHA256_REGEX",  # types.py
    "SQL_IDENTIFIER_PATTERN",  # types.py
    "SQL_IDENTIFIER_REGEX",  # types.py
    "URN_BASE_PATTERN",  # types.py
    "URN_BASE_REGEX",  # types.py
    "URN_PATTERNS",  # types.py
    "URN_REGEXES",  # types.py
    "UUID_V4_PATTERN",  # types.py
    "UUID_V4_REGEX",  # types.py
    "calculate_age_years",  # dates.py
    "constants",  # constants/
    "enums",  # enums/
    "format_utc_timestamp",  # dates.py
    "is_finite_number",  # types.py
    "is_strict_int",  # types.py
    "is_valid_sha256",  # hashes.py
    "parse_iso_date_parts",  # dates.py
    "parse_iso_timestamp",  # dates.py
    "sha256_bytes",  # hashes.py
    "sha256_file",  # hashes.py
    "sha256_text",  # hashes.py
    "utc_now_iso",  # dates.py
    "utc_today_iso",  # dates.py
    "validate_iso_date",  # dates.py
    "validate_iso_timestamp",  # dates.py
]
