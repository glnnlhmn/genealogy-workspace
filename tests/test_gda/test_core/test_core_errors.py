"""Path: tests/test_gda/test_core/test_core_errors.py

Comprehensive unit, regression, and property-based test suite for gda.core.errors.

Operational Role:
    Verifies GenealogyDeskError base functionality (UTC timestamps, structured
    to_dict serialization, __repr__ formatting, CLI exit codes, cause chaining,
    and defensive details isolation) along with the full ConfigError and
    ModelError exception hierarchies.

Test Structure & Protocol:
    - Atomized & parametrized tests: 1:1 behavioral contract mapping.
    - Fully decorated: 5-marker taxonomy (smoke, unit, regression, integrity).
    - Property-based: Hypothesis strategies imported from test_core/strategies.py.
    - Dependencies: Pure in-memory evaluation with zero disk I/O.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from hypothesis import given
from hypothesis import strategies as st
from tests.test_gda.test_core.strategies import strict_ints

import gda.core.errors as errs
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
from gda.core.types import ISO_TIMESTAMP_REGEX

__version__ = "1.0.0+build.8"


# ==============================================================================
# GROUP 1: Smoke & Primary Entrypoints
# Note: Verifies gda.core.errors exports all 8 classes and canonical dict keys.
# ==============================================================================


@pytest.mark.smoke
@pytest.mark.unit
def test_errors_exposes_expected_public_interface_and_schema(
    sample_genealogy_desk_error: GenealogyDeskError,
) -> None:
    """Verify gda.core.errors exports all 8 exception classes and 5-key to_dict schema."""
    expected_exports = {
        "ConfigError",
        "ConfigParseError",
        "ConfigValidationError",
        "GenealogyDeskError",
        "ModelError",
        "ModelFormatError",
        "ModelPrefixMismatchError",
        "ModelRangeError",
    }
    assert set(errs.__all__) == expected_exports
    assert set(sample_genealogy_desk_error.to_dict().keys()) == {
        "error_code",
        "message",
        "details",
        "timestamp",
        "exit_code",
    }


# ==============================================================================
# GROUP 2: Core Logic & Happy Paths
# Note: Full hierarchy inheritance, default error/exit codes, and serialization.
# ==============================================================================


@pytest.mark.unit
@pytest.mark.parametrize(
    ("exc_cls", "parent_cls", "expected_code", "expected_exit_code"),
    [
        (GenealogyDeskError, Exception, "ERR_GENERIC", 1),
        (ConfigError, GenealogyDeskError, "ERR_CONFIG", 2),
        (ConfigValidationError, ConfigError, "ERR_CONFIG_VALIDATION", 2),
        (ConfigParseError, ConfigError, "ERR_CONFIG_PARSE", 2),
        (ModelError, GenealogyDeskError, "ERR_MODEL_VALIDATION", 3),
        (ModelFormatError, ModelError, "ERR_MODEL_FORMAT", 3),
        (ModelRangeError, ModelError, "ERR_MODEL_RANGE", 3),
        (ModelPrefixMismatchError, ModelError, "ERR_MODEL_PREFIX_MISMATCH", 3),
    ],
)
def test_error_hierarchy_default_codes_and_exit_codes(
    exc_cls: type[GenealogyDeskError],
    parent_cls: type[Exception],
    expected_code: str,
    expected_exit_code: int,
) -> None:
    """Verify each exception class inherits properly and sets canonical error/exit codes."""
    err = exc_cls("Failure message")
    assert isinstance(err, parent_cls)
    assert isinstance(err, GenealogyDeskError)
    assert err.message == "Failure message"
    assert str(err) == "Failure message"
    assert err.error_code == expected_code
    assert err.exit_code == expected_exit_code
    assert err.details == {}


@pytest.mark.unit
@pytest.mark.parametrize(
    ("exc_cls", "message", "expected_code", "expected_exit"),
    [
        (GenealogyDeskError, "base failure", "ERR_GENERIC", 1),
        (ConfigParseError, "bad toml", "ERR_CONFIG_PARSE", 2),
        (ModelRangeError, "out of bounds", "ERR_MODEL_RANGE", 3),
    ],
)
def test_genealogy_desk_error_repr_includes_class_code_and_exit(
    exc_cls: type[GenealogyDeskError],
    message: str,
    expected_code: str,
    expected_exit: int,
) -> None:
    """Verify __repr__ surfaces class name, message, error_code, and exit_code."""
    err = exc_cls(message)
    expected = (
        f"{exc_cls.__name__}("
        f"message={message!r}, "
        f"error_code={expected_code!r}, "
        f"exit_code={expected_exit!r})"
    )
    assert repr(err) == expected


@pytest.mark.unit
def test_genealogy_desk_error_custom_payload_and_overrides() -> None:
    """Verify GenealogyDeskError retains custom error_code, details, and exit_code."""
    payload: dict[str, Any] = {"entity_id": "IND-000001", "attempt": 2}
    err = GenealogyDeskError(
        "Custom error",
        error_code="ERR_CUSTOM",
        details=payload,
        exit_code=42,
    )
    assert err.message == "Custom error"
    assert err.error_code == "ERR_CUSTOM"
    assert err.details == payload
    assert err.exit_code == 42


@pytest.mark.unit
def test_genealogy_desk_error_to_dict_serialization(
    sample_genealogy_desk_error: GenealogyDeskError,
) -> None:
    """Verify to_dict returns all structured diagnostic fields accurately."""
    serialized = sample_genealogy_desk_error.to_dict()
    assert serialized["message"] == sample_genealogy_desk_error.message
    assert serialized["error_code"] == "ERR_DB_TIMEOUT"
    assert serialized["details"] == {"host": "10.0.0.1", "port": 5432}
    assert serialized["timestamp"] == sample_genealogy_desk_error.timestamp
    assert serialized["exit_code"] == 1


@pytest.mark.unit
@given(
    message=st.text(max_size=64),
    error_code=st.text(min_size=1, max_size=24),
    exit_code=strict_ints(min_value=0, max_value=255),
)
def test_genealogy_desk_error_hypothesis_str_and_to_dict_invariants(
    message: str,
    error_code: str,
    exit_code: int,
) -> None:
    """Verify str(err) and to_dict() preserve arbitrary messages, codes, and exit codes."""
    err = GenealogyDeskError(message, error_code=error_code, exit_code=exit_code)
    serialized = err.to_dict()
    assert str(err) == message
    assert serialized["message"] == message
    assert serialized["error_code"] == error_code
    assert serialized["exit_code"] == exit_code


# ==============================================================================
# GROUP 3: Edge Cases & Boundary Conditions
# Note: Non-JSON-native details, exception cause chaining, and empty diagnostics.
# ==============================================================================


@pytest.mark.regression
def test_genealogy_desk_error_non_serializable_details() -> None:
    """Verify to_dict retains non-JSON-native objects in details without raising."""
    details: dict[str, Any] = {"target_path": Path("data/sample.db"), "flags": {1, 2, 3}}
    err = GenealogyDeskError("Path unreadable", error_code="ERR_IO", details=details)
    serialized = err.to_dict()
    assert serialized["details"]["target_path"] == Path("data/sample.db")
    assert serialized["details"]["flags"] == {1, 2, 3}


@pytest.mark.regression
def test_genealogy_desk_error_cause_chaining() -> None:
    """Verify __cause__ chaining retains nested exception context."""
    root_cause = ValueError("Invalid disk sector")
    with pytest.raises(GenealogyDeskError) as exc_info:
        raise GenealogyDeskError("Higher-level failure", error_code="ERR_SYS") from root_cause

    assert exc_info.value.__cause__ is root_cause
    assert str(exc_info.value.__cause__) == "Invalid disk sector"


@pytest.mark.regression
def test_genealogy_desk_error_empty_or_none_diagnostics() -> None:
    """Verify defensive handling of None and empty string diagnostics."""
    err = GenealogyDeskError("", error_code="", details=None)
    assert err.message == ""
    assert err.error_code == ""
    assert err.details == {}
    assert err.to_dict()["details"] == {}


# ==============================================================================
# GROUP 4: Error Handling & Validation Failures
# Note: Defensive isolation so external dict mutations cannot corrupt error state.
# ==============================================================================


@pytest.mark.regression
def test_genealogy_desk_error_defensively_copies_details_dict() -> None:
    """Verify mutating caller or serialized dicts cannot corrupt err.details (Phase 4)."""
    caller_details: dict[str, Any] = {"field": "source_urn"}
    err = GenealogyDeskError("Missing URN", details=caller_details)

    # Mutate caller dict after construction; error state must remain isolated.
    caller_details["field"] = "mutated_by_caller"
    assert err.details["field"] == "source_urn"

    # Mutate serialized dict after to_dict(); error state must remain isolated.
    serialized = err.to_dict()
    serialized["details"]["field"] = "mutated_after_to_dict"
    assert err.details["field"] == "source_urn"


# ==============================================================================
# GROUP 6: Integrity & Invariants
# Note: Canonical UTC timestamp formatting parity with gda.core.types.
# ==============================================================================


@pytest.mark.integrity
@pytest.mark.unit
def test_genealogy_desk_error_timestamp_matches_iso_regex(
    sample_genealogy_desk_error: GenealogyDeskError,
) -> None:
    """Verify GenealogyDeskError.timestamp conforms strictly to ISO_TIMESTAMP_REGEX."""
    assert ISO_TIMESTAMP_REGEX.match(sample_genealogy_desk_error.timestamp) is not None
    assert sample_genealogy_desk_error.timestamp.endswith("Z")
