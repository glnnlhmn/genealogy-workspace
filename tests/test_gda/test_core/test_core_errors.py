"""Path: tests/test_gda/test_core/test_core_errors.py

Comprehensive test suite verifying core exception hierarchies and payload mechanics.

Operational Role:
    Verifies GenealogyDeskError base functionality (timestamps, serialization,
    attributes), ConfigError subsystem exceptions, and ModelError validation
    subclasses.

Test Structure & Protocol:
    - Atomized tests: 1:1 behavioral contract mapping.
    - Fully decorated: Strictly unit and regression markers.
    - Zero production disk I/O.
"""

from __future__ import annotations

from pathlib import Path

import pytest

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

__version__ = "1.0.0+build.6"


# ==============================================================================
# GROUP 1: BASE GENEALOGYDESKERROR CONTRACT
# ==============================================================================


@pytest.mark.unit
def test_genealogy_desk_error_default_attributes() -> None:
    """Verify GenealogyDeskError initializes with expected defaults."""
    err = GenealogyDeskError("Test failure")
    assert err.message == "Test failure"
    assert err.error_code == "ERR_GENERIC"
    assert err.details == {}
    assert str(err) == "Test failure"
    assert err.timestamp.endswith("Z")


@pytest.mark.unit
def test_genealogy_desk_error_custom_payload() -> None:
    """Verify GenealogyDeskError retains custom code and diagnostic details."""
    payload = {"entity_id": "IND-000001"}
    err = GenealogyDeskError("Custom error", error_code="ERR_CUSTOM", details=payload)
    assert err.message == "Custom error"
    assert err.error_code == "ERR_CUSTOM"
    assert err.details == payload


@pytest.mark.unit
def test_genealogy_desk_error_to_dict_serialization() -> None:
    """Verify to_dict returns a well-formed JSON-compatible metadata dictionary."""
    details = {"field": "source_urn"}
    err = GenealogyDeskError("Missing URN", error_code="ERR_MISSING", details=details)
    serialized = err.to_dict()

    assert serialized["message"] == "Missing URN"
    assert serialized["error_code"] == "ERR_MISSING"
    assert serialized["details"] == details
    assert serialized["timestamp"] == err.timestamp


@pytest.mark.regression
def test_genealogy_desk_error_non_serializable_details() -> None:
    """Verify to_dict handles non-standard objects in details dictionary (ERR-001)."""
    details = {"target_path": Path("data/sample.db"), "flags": {1, 2, 3}}
    err = GenealogyDeskError("Path unreadable", error_code="ERR_IO", details=details)
    serialized = err.to_dict()
    assert serialized["details"]["target_path"] == Path("data/sample.db")
    assert serialized["details"]["flags"] == {1, 2, 3}


@pytest.mark.regression
def test_genealogy_desk_error_cause_chaining() -> None:
    """Verify __cause__ chaining retains nested exception context (ERR-002)."""
    root_cause = ValueError("Invalid disk sector")
    try:
        raise GenealogyDeskError("Higher-level failure", error_code="ERR_SYS") from root_cause
    except GenealogyDeskError as exc:
        assert exc.__cause__ is root_cause
        assert str(exc.__cause__) == "Invalid disk sector"


@pytest.mark.regression
def test_genealogy_desk_error_empty_or_none_diagnostics() -> None:
    """Verify defensive handling of None and empty string diagnostics (ERR-004)."""
    err = GenealogyDeskError("", error_code="", details=None)
    assert err.message == ""
    assert err.error_code == ""
    assert err.details == {}
    assert err.timestamp.endswith("Z")
    serialized = err.to_dict()
    assert serialized["details"] == {}


# ==============================================================================
# GROUP 2: CONFIGURATION SUBSYSTEM EXCEPTIONS
# ==============================================================================


@pytest.mark.unit
def test_config_error_hierarchy() -> None:
    """Verify ConfigError inherits from GenealogyDeskError with ERR_CONFIG."""
    err = ConfigError("Configuration failed")
    assert isinstance(err, GenealogyDeskError)
    assert err.error_code == "ERR_CONFIG"
    assert err.message == "Configuration failed"


@pytest.mark.regression
def test_config_validation_error_contract() -> None:
    """Verify ConfigValidationError sets ERR_CONFIG_VALIDATION."""
    err = ConfigValidationError("Invalid port number", details={"port": -1})
    assert isinstance(err, ConfigError)
    assert isinstance(err, GenealogyDeskError)
    assert err.error_code == "ERR_CONFIG_VALIDATION"
    assert err.details == {"port": -1}


@pytest.mark.regression
def test_config_parse_error_contract() -> None:
    """Verify ConfigParseError sets ERR_CONFIG_PARSE."""
    err = ConfigParseError("Malformed TOML", details={"line": 12})
    assert isinstance(err, ConfigError)
    assert isinstance(err, GenealogyDeskError)
    assert err.error_code == "ERR_CONFIG_PARSE"
    assert err.details == {"line": 12}


# ==============================================================================
# GROUP 3: MODEL VALIDATION EXCEPTIONS
# ==============================================================================


@pytest.mark.unit
def test_model_error_hierarchy() -> None:
    """Verify ModelError inherits from GenealogyDeskError with ERR_MODEL_VALIDATION."""
    err = ModelError("Model failure")
    assert isinstance(err, GenealogyDeskError)
    assert err.error_code == "ERR_MODEL_VALIDATION"
    assert err.message == "Model failure"


@pytest.mark.regression
def test_model_format_error_contract() -> None:
    """Verify ModelFormatError inherits from ModelError with ERR_MODEL_FORMAT."""
    err = ModelFormatError("Invalid syntax", details={"value": "bad_token"})
    assert isinstance(err, ModelError)
    assert isinstance(err, GenealogyDeskError)
    assert err.error_code == "ERR_MODEL_FORMAT"
    assert err.details == {"value": "bad_token"}


@pytest.mark.regression
def test_model_range_error_contract() -> None:
    """Verify ModelRangeError inherits from ModelError with ERR_MODEL_RANGE."""
    err = ModelRangeError("Value out of bounds", details={"min": 0, "max": 3})
    assert isinstance(err, ModelError)
    assert isinstance(err, GenealogyDeskError)
    assert err.error_code == "ERR_MODEL_RANGE"
    assert err.details == {"min": 0, "max": 3}


@pytest.mark.regression
def test_model_prefix_mismatch_error_contract() -> None:
    """Verify ModelPrefixMismatchError inherits from ModelError with ERR_MODEL_PREFIX_MISMATCH."""
    details = {"expected": "IND", "actual": "FID"}
    err = ModelPrefixMismatchError("Prefix mismatch", details=details)
    assert isinstance(err, ModelError)
    assert isinstance(err, GenealogyDeskError)
    assert err.error_code == "ERR_MODEL_PREFIX_MISMATCH"
    assert err.details == details
