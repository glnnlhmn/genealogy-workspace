# Name: test_errors.py
# Path: tests/test_gda/test_core/test_errors.py
# Version: 1.0.0+build.r4

"""Unit verification suite for GDA Core error hierarchy.

Operational Role:
    Validates GenealogyDeskError root and specialized exception subclasses,
    ensuring standard error codes, structured details dictionaries,
    ISO 8601 UTC timestamps, and dictionary serialization contracts.

Test Structure & Protocol:
    - Atomized tests: 1:1 behavioral assertion mapping across exception contracts.
    - Fully decorated: @pytest.mark.unit and @pytest.mark.smoke applied throughout.
    - Dependencies: pytest standard library fixtures only (zero disk I/O).
"""

from __future__ import annotations

from datetime import datetime

import pytest

from gda.core.errors import (
    ConfigError,
    ConfigParseError,
    ConfigValidationError,
    GenealogyDeskError,
)

__version__ = "1.0.0+build.r4"

# ==============================================================================
# GROUP 1: BASE EXCEPTION CONTRACTS
# Note: Validates GenealogyDeskError instantiation, attributes, and serialization
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_base_error_default_initialization() -> None:
    """Verify default error_code, details, and valid ISO timestamp on root error."""
    err = GenealogyDeskError("A baseline failure occurred.")

    assert str(err) == "A baseline failure occurred."
    assert err.message == "A baseline failure occurred."
    assert err.error_code == "ERR_GENERIC"
    assert err.details == {}

    # Verify timestamp format (ISO 8601 with UTC)
    ts = datetime.fromisoformat(err.timestamp)
    assert ts.tzinfo is not None


@pytest.mark.unit
def test_base_error_custom_attributes() -> None:
    """Verify custom error_code and structured details retain supplied context."""
    context = {"entity_id": "IND-0001", "attempt": 3}
    err = GenealogyDeskError(
        "Failed to resolve record",
        error_code="ERR_RECORD_LOOKUP",
        details=context,
    )

    assert err.error_code == "ERR_RECORD_LOOKUP"
    assert err.details == context
    assert err.details["entity_id"] == "IND-0001"


@pytest.mark.unit
def test_base_error_to_dict_serialization() -> None:
    """Verify to_dict() returns dictionary matching serialization contract."""
    details = {"field": "username", "value": None}
    err = GenealogyDeskError(
        "Invalid configuration",
        error_code="ERR_VALIDATION",
        details=details,
    )

    payload = err.to_dict()

    assert isinstance(payload, dict)
    assert payload["error_code"] == "ERR_VALIDATION"
    assert payload["message"] == "Invalid configuration"
    assert payload["details"] == details
    assert payload["timestamp"] == err.timestamp


# ==============================================================================
# GROUP 2: CONFIGURATION EXCEPTION SUBCLASSES
# Note: Validates ConfigError, ConfigValidationError, and ConfigParseError
# ==============================================================================


@pytest.mark.unit
def test_config_error_inheritance_and_defaults() -> None:
    """Verify ConfigError defaults to ERR_CONFIG and inherits from GenealogyDeskError."""
    err = ConfigError("Config missing")

    assert isinstance(err, GenealogyDeskError)
    assert err.error_code == "ERR_CONFIG"
    assert err.message == "Config missing"
    assert err.details == {}


@pytest.mark.unit
def test_config_validation_error_defaults() -> None:
    """Verify ConfigValidationError defaults to ERR_CONFIG_VALIDATION."""
    err = ConfigValidationError("Port out of bounds", details={"port": -1})

    assert isinstance(err, ConfigError)
    assert isinstance(err, GenealogyDeskError)
    assert err.error_code == "ERR_CONFIG_VALIDATION"
    assert err.details == {"port": -1}


@pytest.mark.unit
def test_config_parse_error_defaults() -> None:
    """Verify ConfigParseError defaults to ERR_CONFIG_PARSE."""
    err = ConfigParseError("Malformed TOML", details={"line": 42})

    assert isinstance(err, ConfigError)
    assert isinstance(err, GenealogyDeskError)
    assert err.error_code == "ERR_CONFIG_PARSE"
    assert err.details == {"line": 42}
