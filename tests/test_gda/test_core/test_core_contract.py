"""Path: tests/test_gda/test_core/test_core_contract.py

Authoritative public interface and contract verification suite for gda.core.

Operational Role:
    Freezes and validates the public API surface of the core framework.
    Ensures symbol parity, prevents unintended surface changes, validates class
    hierarchies, member signatures, immutability guarantees, and ensures that
    the current export format is the only valid format.

Test Structure & Protocol:
    - Atomized tests: 1:1 structural contract assertions.
    - Fully decorated: Strictly unit and integrity markers.
    - Zero production disk I/O.
"""

from __future__ import annotations

import inspect

import pytest
from pydantic import BaseModel

import gda.core
from gda.core import (
    AppConfig,
    ConfigError,
    ConfigParseError,
    ConfigValidationError,
    DatabaseConfig,
    GDALogger,
    GenealogyDeskError,
    ImmutableBaseModel,
    IntrospectableMixin,
    LoggingConfig,
    ModelError,
    ModelFormatError,
    ModelPrefixMismatchError,
    ModelRangeError,
)

__version__ = "1.0.0+build.5"

# ==============================================================================
# AUTHORITATIVE CONTRACT SPECIFICATION
# Note: Defines the strict, immutable contract for gda.core exports
# ==============================================================================

AUTHORITATIVE_EXPORTS: frozenset[str] = frozenset(
    {
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
    }
)


# ==============================================================================
# GROUP 1: PUBLIC EXPORT SURFACE INTEGRITY
# ==============================================================================


@pytest.mark.smoke
@pytest.mark.integrity
@pytest.mark.unit
def test_core_exports_exact_authoritative_symbols() -> None:
    """Verify gda.core exports exactly the authoritative symbol set with zero drift (CTR-001)."""
    actual_symbols = frozenset(gda.core.__all__)
    assert actual_symbols == AUTHORITATIVE_EXPORTS
    assert len(gda.core.__all__) == 37


@pytest.mark.integrity
@pytest.mark.unit
def test_core_all_is_sorted_alphabetically() -> None:
    """Verify gda.core.__all__ is formatted strictly in alphabetical order."""
    assert gda.core.__all__ == sorted(gda.core.__all__)


@pytest.mark.unit
def test_all_symbols_exist_as_module_attributes() -> None:
    """Verify every symbol declared in __all__ exists as an accessible attribute."""
    for symbol_name in AUTHORITATIVE_EXPORTS:
        assert hasattr(gda.core, symbol_name), f"Missing symbol {symbol_name} in gda.core"
        attr = getattr(gda.core, symbol_name)
        assert attr is not None


# ==============================================================================
# GROUP 2: EXCEPTION INHERITANCE HIERARCHIES
# ==============================================================================


@pytest.mark.integrity
@pytest.mark.unit
def test_exception_tree_hierarchy_contracts() -> None:
    """Verify strict inheritance hierarchy of all exported core exception classes."""
    # Root
    assert issubclass(GenealogyDeskError, Exception)

    # Config subsystem branch
    assert issubclass(ConfigError, GenealogyDeskError)
    assert issubclass(ConfigValidationError, ConfigError)
    assert issubclass(ConfigParseError, ConfigError)

    # Model subsystem branch
    assert issubclass(ModelError, GenealogyDeskError)
    assert issubclass(ModelFormatError, ModelError)
    assert issubclass(ModelRangeError, ModelError)
    assert issubclass(ModelPrefixMismatchError, ModelError)


@pytest.mark.unit
def test_exception_serialization_contract() -> None:
    """Verify all exceptions implement to_dict returning standard keys including exit_code."""
    err = GenealogyDeskError("Base", error_code="ERR_BASE", details={"ctx": 1})
    payload = err.to_dict()
    assert set(payload.keys()) == {
        "error_code",
        "message",
        "details",
        "timestamp",
        "exit_code",
    }


# ==============================================================================
# GROUP 3: PYDANTIC SCHEMA IMMUTABILITY & CONTRACTS
# ==============================================================================


@pytest.mark.integrity
@pytest.mark.unit
def test_config_models_inherit_immutable_base() -> None:
    """Verify all configuration models inherit from ImmutableBaseModel."""
    assert issubclass(ImmutableBaseModel, BaseModel)
    assert issubclass(DatabaseConfig, ImmutableBaseModel)
    assert issubclass(LoggingConfig, ImmutableBaseModel)
    assert issubclass(AppConfig, ImmutableBaseModel)


@pytest.mark.integrity
@pytest.mark.unit
def test_config_models_enforce_frozen_and_forbid_extra() -> None:
    """Verify immutable config base strictly forbids extra attributes and mutation."""
    assert ImmutableBaseModel.model_config.get("frozen") is True
    assert ImmutableBaseModel.model_config.get("extra") == "forbid"
    assert DatabaseConfig.model_config.get("frozen") is True
    assert DatabaseConfig.model_config.get("extra") == "forbid"
    assert LoggingConfig.model_config.get("frozen") is True
    assert LoggingConfig.model_config.get("extra") == "forbid"
    assert AppConfig.model_config.get("frozen") is True
    assert AppConfig.model_config.get("extra") == "forbid"


@pytest.mark.integrity
@pytest.mark.unit
def test_config_models_field_names_and_types() -> None:
    """Verify expected field names exist across configuration models (CTR-002)."""
    assert {"db_path", "busy_timeout", "journal_mode", "foreign_keys", "synchronous"} == set(
        DatabaseConfig.model_fields.keys()
    )
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
def test_app_config_derived_property_accessors() -> None:
    """Verify derived directory property accessors remain declared on AppConfig (CTR-003)."""
    for prop in ("data_path", "logs_path", "backups_path"):
        assert hasattr(AppConfig, prop)
        assert isinstance(getattr(AppConfig, prop), property)


# ==============================================================================
# GROUP 4: CALLABLE SERVICE & DESCRIPTOR SIGNATURES
# ==============================================================================


@pytest.mark.integrity
@pytest.mark.unit
def test_gda_logger_public_interface_methods() -> None:
    """Verify GDALogger preserves all expected public logging methods and signatures."""
    expected_methods = ["debug", "info", "warning", "error", "critical"]
    for method_name in expected_methods:
        method = getattr(GDALogger, method_name, None)
        assert callable(method), f"GDALogger.{method_name} must be callable"
        sig = inspect.signature(method)
        params = list(sig.parameters.keys())
        assert "self" in params
        assert "msg" in params
        assert "details" in params


@pytest.mark.integrity
@pytest.mark.unit
def test_introspectable_mixin_contract() -> None:
    """Verify IntrospectableMixin maintains the .help descriptor contract."""
    assert hasattr(IntrospectableMixin, "help")
    assert hasattr(IntrospectableMixin, "_get_public_members")
    assert inspect.ismethod(IntrospectableMixin._get_public_members)


@pytest.mark.integrity
@pytest.mark.unit
def test_app_config_load_signature() -> None:
    """Verify AppConfig.load preserves required classmethod signature and parameter names."""
    load_method = getattr(AppConfig, "load", None)
    assert callable(load_method)
    sig = inspect.signature(load_method)
    params = list(sig.parameters.keys())
    assert "config_path" in params
    assert "root_path" in params
    assert "env_prefix" in params
    assert "env_vars" in params
    assert "overrides" in params
