"""Path: src/gda/core/__init__.py

Core infrastructure, configuration, error contracts, and runtime introspection.

Operational Role:
    Unified public export facade for foundational framework classes:
    AppConfig, DatabaseConfig, LoggingConfig, structured exceptions,
    introspective mixins, logging services, temporal formatters, cryptographic
    hashing, controlled vocabulary enums, and canonical scalar type definitions.
"""

from __future__ import annotations

from gda.core import enums
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
    CENSUS_SHEET_SIDES,
    CIVIL_WAR_DRAFT_YEARS,
    COLONIAL_MILITIA_MAX_YEAR,
    COLONIAL_MILITIA_MIN_YEAR,
    ENTITY_ID_PATTERNS,
    ENTITY_ID_REGEXES,
    ENTITY_URN_PATTERNS,
    ENTITY_URN_REGEXES,
    ENUM_KEY_SEPARATOR_PATTERN,
    ENUM_KEY_SEPARATOR_REGEX,
    GENDER_CODES,
    ISO_DATE_FMT,
    ISO_DATE_PATTERN,
    ISO_DATE_REGEX,
    ISO_MONTH_FMT,
    ISO_TIMESTAMP_FMT,
    ISO_TIMESTAMP_PATTERN,
    ISO_TIMESTAMP_REGEX,
    ISO_YEAR_FMT,
    MAX_BOUNTY_LAND_ACREAGE,
    MAX_CENSUS_LINE_NUMBER,
    MAX_CONFIDENCE_SCORE,
    MAX_ENLISTMENT_TERM_MONTHS,
    MAX_FOREIGN_SERVICE_MONTHS,
    MAX_HEIGHT_INCHES,
    MAX_HISTORICAL_YEAR,
    MAX_LATITUDE,
    MAX_LONGITUDE,
    MAX_MINOR_CHILDREN_COUNT,
    MAX_QUAY_SCORE,
    MAX_VIETNAM_LOTTERY_NUMBER,
    MAX_WEIGHT_LBS,
    MIN_AHNENTAFEL,
    MIN_CONFIDENCE_SCORE,
    MIN_ENLISTMENT_TERM_MONTHS,
    MIN_HEIGHT_INCHES,
    MIN_HISTORICAL_YEAR,
    MIN_LATITUDE,
    MIN_LONGITUDE,
    MIN_QUAY_SCORE,
    MIN_VIETNAM_LOTTERY_NUMBER,
    MIN_WEIGHT_LBS,
    MODERN_SSS_MIN_YEAR,
    NEWS_CATEGORY_PATTERN,
    NEWS_CATEGORY_REGEX,
    PUB_CODE_PATTERN,
    PUB_CODE_REGEX,
    SHA256_PATTERN,
    SHA256_REGEX,
    SQL_IDENTIFIER_PATTERN,
    SQL_IDENTIFIER_REGEX,
    TAX_ASSESSMENT_MIN_YEAR,
    URN_BASE_PATTERN,
    URN_BASE_REGEX,
    URN_PATTERNS,
    URN_REGEXES,
    US_AGRICULTURAL_SCHEDULE_YEARS,
    US_FEDERAL_CENSUS_1850_1870_YEARS,
    US_FEDERAL_CENSUS_1900_1910_YEARS,
    US_FEDERAL_CENSUS_TALLY_YEARS,
    US_FEDERAL_CENSUS_YEARS,
    US_MANUFACTURING_SCHEDULE_YEARS,
    US_MORTALITY_SCHEDULE_YEARS,
    US_SLAVE_SCHEDULE_YEARS,
    US_VETERANS_SCHEDULE_YEAR,
    UUID_V4_PATTERN,
    UUID_V4_REGEX,
    WWI_DRAFT_YEARS,
    WWII_DRAFT_YEARS,
)

__version__ = "1.0.0+build.12"

__all__ = [
    "ATOM_ID_PATTERN",  # types.py
    "ATOM_ID_REGEX",  # types.py
    "AppConfig",  # config.py
    "CENSUS_SHEET_SIDES",  # types.py
    "CIVIL_WAR_DRAFT_YEARS",  # types.py
    "COLONIAL_MILITIA_MAX_YEAR",  # types.py
    "COLONIAL_MILITIA_MIN_YEAR",  # types.py
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
    "GENDER_CODES",  # types.py
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
    "MAX_BOUNTY_LAND_ACREAGE",  # types.py
    "MAX_CENSUS_LINE_NUMBER",  # types.py
    "MAX_CONFIDENCE_SCORE",  # types.py
    "MAX_ENLISTMENT_TERM_MONTHS",  # types.py
    "MAX_FOREIGN_SERVICE_MONTHS",  # types.py
    "MAX_HEIGHT_INCHES",  # types.py
    "MAX_HISTORICAL_YEAR",  # types.py
    "MAX_LATITUDE",  # types.py
    "MAX_LONGITUDE",  # types.py
    "MAX_MINOR_CHILDREN_COUNT",  # types.py
    "MAX_QUAY_SCORE",  # types.py
    "MAX_VIETNAM_LOTTERY_NUMBER",  # types.py
    "MAX_WEIGHT_LBS",  # types.py
    "MIN_AHNENTAFEL",  # types.py
    "MIN_CONFIDENCE_SCORE",  # types.py
    "MIN_ENLISTMENT_TERM_MONTHS",  # types.py
    "MIN_HEIGHT_INCHES",  # types.py
    "MIN_HISTORICAL_YEAR",  # types.py
    "MIN_LATITUDE",  # types.py
    "MIN_LONGITUDE",  # types.py
    "MIN_QUAY_SCORE",  # types.py
    "MIN_VIETNAM_LOTTERY_NUMBER",  # types.py
    "MIN_WEIGHT_LBS",  # types.py
    "MODERN_SSS_MIN_YEAR",  # types.py
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
    "TAX_ASSESSMENT_MIN_YEAR",  # types.py
    "URN_BASE_PATTERN",  # types.py
    "URN_BASE_REGEX",  # types.py
    "URN_PATTERNS",  # types.py
    "URN_REGEXES",  # types.py
    "US_AGRICULTURAL_SCHEDULE_YEARS",  # types.py
    "US_FEDERAL_CENSUS_1850_1870_YEARS",  # types.py
    "US_FEDERAL_CENSUS_1900_1910_YEARS",  # types.py
    "US_FEDERAL_CENSUS_TALLY_YEARS",  # types.py
    "US_FEDERAL_CENSUS_YEARS",  # types.py
    "US_MANUFACTURING_SCHEDULE_YEARS",  # types.py
    "US_MORTALITY_SCHEDULE_YEARS",  # types.py
    "US_SLAVE_SCHEDULE_YEARS",  # types.py
    "US_VETERANS_SCHEDULE_YEAR",  # types.py
    "UUID_V4_PATTERN",  # types.py
    "UUID_V4_REGEX",  # types.py
    "WWII_DRAFT_YEARS",  # types.py
    "WWI_DRAFT_YEARS",  # types.py
    "calculate_age_years",  # dates.py
    "enums",  # enums/
    "format_utc_timestamp",  # dates.py
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
