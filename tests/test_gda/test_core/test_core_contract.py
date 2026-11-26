"""Path: tests/test_gda/test_core/test_core_contract.py

Authoritative package-level facade and API surface contract suite for gda.core.

Operational Role:
    Freezes and validates the Tier 0 package facade (gda.core.__init__),
    ensuring exact __all__ export parity, alphabetical ordering, Pydantic
    schema field and property surfaces, and public callable signatures for
    downstream Tier 1-4 consumers.

Test Structure & Protocol:
    - Atomized tests: 1:1 structural contract assertions.
    - Fully decorated: 5-marker taxonomy (smoke, unit, integrity).
    - Zero disk I/O; submodule behavior is tested in dedicated module suites.
"""

from __future__ import annotations

import inspect

import pytest

import gda.core
from gda.core import (
    AppConfig,
    DatabaseConfig,
    GDALogger,
    IntrospectableMixin,
    LoggingConfig,
)

__version__ = "1.0.0+build.13"

# ==============================================================================
# AUTHORITATIVE CONTRACT SPECIFICATION
# Note: Strict, immutable contract for gda.core.__all__ (62 symbols).
# ==============================================================================

AUTHORITATIVE_EXPORTS: frozenset[str] = frozenset(
    {
        # config.py (4)
        "AppConfig",
        "DatabaseConfig",
        "ImmutableBaseModel",
        "LoggingConfig",
        # constants/ (1)
        "constants",
        # dates.py (8)
        "calculate_age_years",
        "format_utc_timestamp",
        "parse_iso_date_parts",
        "parse_iso_timestamp",
        "utc_now_iso",
        "utc_today_iso",
        "validate_iso_date",
        "validate_iso_timestamp",
        # enums/ (1)
        "enums",
        # errors.py (8)
        "ConfigError",
        "ConfigParseError",
        "ConfigValidationError",
        "GenealogyDeskError",
        "ModelError",
        "ModelFormatError",
        "ModelPrefixMismatchError",
        "ModelRangeError",
        # hashes.py (4)
        "is_valid_sha256",
        "sha256_bytes",
        "sha256_file",
        "sha256_text",
        # introspectable.py (1)
        "IntrospectableMixin",
        # logging.py (3)
        "ConsoleFormatter",
        "GDALogger",
        "JsonFormatter",
        # types.py (32)
        "ATOM_ID_PATTERN",
        "ATOM_ID_REGEX",
        "ENTITY_ID_PATTERNS",
        "ENTITY_ID_REGEXES",
        "ENTITY_URN_PATTERNS",
        "ENTITY_URN_REGEXES",
        "ENUM_KEY_SEPARATOR_PATTERN",
        "ENUM_KEY_SEPARATOR_REGEX",
        "ISO_DATE_FMT",
        "ISO_DATE_PATTERN",
        "ISO_DATE_REGEX",
        "ISO_MONTH_FMT",
        "ISO_TIMESTAMP_FMT",
        "ISO_TIMESTAMP_PATTERN",
        "ISO_TIMESTAMP_REGEX",
        "ISO_YEAR_FMT",
        "NEWS_CATEGORY_PATTERN",
        "NEWS_CATEGORY_REGEX",
        "PUB_CODE_PATTERN",
        "PUB_CODE_REGEX",
        "SHA256_PATTERN",
        "SHA256_REGEX",
        "SQL_IDENTIFIER_PATTERN",
        "SQL_IDENTIFIER_REGEX",
        "URN_BASE_PATTERN",
        "URN_BASE_REGEX",
        "URN_PATTERNS",
        "URN_REGEXES",
        "UUID_V4_PATTERN",
        "UUID_V4_REGEX",
        "is_finite_number",
        "is_strict_int",
    }
)


# ==============================================================================
# GROUP 1: Smoke & Primary Entrypoints
# Note: Single smoke gate freezing gda.core.__all__ against drift.
# ==============================================================================


@pytest.mark.smoke
@pytest.mark.integrity
@pytest.mark.unit
def test_core_exports_exact_authoritative_symbols() -> None:
    """Verify gda.core exports exactly the authoritative symbol set with zero drift."""
    actual_symbols = frozenset(gda.core.__all__)
    assert actual_symbols == AUTHORITATIVE_EXPORTS
    assert len(gda.core.__all__) == len(AUTHORITATIVE_EXPORTS)


# ==============================================================================
# GROUP 2: Core Logic & Happy Paths
# Note: Verifies every exported facade symbol resolves to a non-None attribute.
# ==============================================================================


@pytest.mark.unit
def test_all_symbols_exist_as_module_attributes() -> None:
    """Verify every symbol declared in AUTHORITATIVE_EXPORTS is accessible on gda.core."""
    for symbol_name in AUTHORITATIVE_EXPORTS:
        assert hasattr(gda.core, symbol_name), f"Missing symbol {symbol_name} in gda.core"
        assert getattr(gda.core, symbol_name) is not None


# ==============================================================================
# GROUP 6: Integrity & Invariants
# Note: Alphabetical __all__, schema field/property freeze, and callable signatures.
# ==============================================================================


@pytest.mark.integrity
@pytest.mark.unit
def test_core_all_is_sorted_and_unique() -> None:
    """Verify gda.core.__all__ is strictly sorted with no duplicate entries."""
    assert gda.core.__all__ == sorted(gda.core.__all__)
    assert len(gda.core.__all__) == len(set(gda.core.__all__))


@pytest.mark.integrity
@pytest.mark.unit
def test_config_models_field_names_and_types() -> None:
    """Verify expected field names remain frozen across configuration models."""
    assert {
        "engine",
        "db_name",
        "db_path",
        "host",
        "port",
        "username",
        "password",
        "dsn_override",
        "busy_timeout",
        "journal_mode",
        "foreign_keys",
        "synchronous",
    } == set(DatabaseConfig.model_fields.keys())
    assert {
        "level",
        "log_to_console",
        "log_to_file",
        "log_file_path",
        "max_bytes",
        "backup_count",
    } == set(LoggingConfig.model_fields.keys())
    assert {"app_name", "environment", "debug", "root_path", "database", "logging"} == set(
        AppConfig.model_fields.keys()
    )


@pytest.mark.integrity
@pytest.mark.unit
def test_app_and_database_config_derived_property_accessors() -> None:
    """Verify derived directory, env, and connection property accessors remain declared."""
    for prop in ("env_code", "data_path", "logs_path", "backups_path"):
        assert isinstance(getattr(AppConfig, prop, None), property)

    for db_prop in ("is_in_memory", "resolved_db_name", "connection_string"):
        assert isinstance(getattr(DatabaseConfig, db_prop, None), property)


@pytest.mark.integrity
@pytest.mark.unit
def test_gda_logger_public_interface_methods() -> None:
    """Verify GDALogger preserves all expected public logging methods and signatures."""
    for method_name in ("debug", "info", "warning", "error", "critical"):
        method = getattr(GDALogger, method_name, None)
        assert callable(method), f"GDALogger.{method_name} must be callable"
        params = list(inspect.signature(method).parameters.keys())
        assert {"self", "msg", "details"}.issubset(params)


@pytest.mark.integrity
@pytest.mark.unit
def test_introspectable_mixin_and_app_config_load_signatures() -> None:
    """Verify IntrospectableMixin and AppConfig.load/for_environment preserve callable contracts."""
    assert hasattr(IntrospectableMixin, "help")
    assert inspect.ismethod(IntrospectableMixin._get_public_members)

    load_method = getattr(AppConfig, "load", None)
    assert callable(load_method)
    load_params = set(inspect.signature(load_method).parameters.keys())
    assert {"config_path", "root_path", "env_prefix", "env_vars", "overrides", "env_name"}.issubset(
        load_params
    )
    assert callable(getattr(AppConfig, "for_environment", None))
