"""Path: tests/test_gda/test_core/test_core_types_guards.py

Unit, regression, and property-based tests for numeric guards in gda.core.types.

Operational Role:
    Verifies is_strict_int and is_finite_number across true integers, IntEnum
    members, finite floats, bool-as-int traps, non-finite floats (NaN, Inf),
    Decimal/StrEnum/string/container inputs, and Hypothesis properties.

Test Structure & Protocol:
    - Atomized & parametrized tests: 1:1 behavioral contract mapping.
    - Fully decorated: 5-marker taxonomy (smoke, unit, regression, integrity).
    - Property-based: Hypothesis strategies imported from test_core/strategies.py.
    - Dependencies: Pure in-memory evaluation with zero disk I/O.
"""

from __future__ import annotations

from decimal import Decimal
from enum import IntEnum, StrEnum
from typing import Any

import pytest
from hypothesis import given
from hypothesis import strategies as st
from tests.test_gda.test_core.strategies import (
    bool_or_non_int,
    non_finite_floats,
    strict_ints,
)

import gda.core.types as prim

__version__ = "1.0.0+build.1"


class _SampleIntEnum(IntEnum):
    """Test helper IntEnum to verify int subclasses are accepted by is_strict_int."""

    ONE = 1


class _SampleStrEnum(StrEnum):
    """Test helper StrEnum to verify string enums are rejected by is_strict_int."""

    ONE = "1"


# ==============================================================================
# GROUP 1: Smoke & Primary Entrypoints
# Note: Verifies numeric type guards are exported and callable.
# ==============================================================================


@pytest.mark.smoke
@pytest.mark.unit
def test_types_guards_exported_and_callable() -> None:
    """Verify is_strict_int and is_finite_number are exported and callable."""
    assert {"is_finite_number", "is_strict_int"}.issubset(set(prim.__all__))
    assert callable(prim.is_strict_int)
    assert callable(prim.is_finite_number)


# ==============================================================================
# GROUP 2: Core Logic & Happy Paths
# Note: Valid integer, IntEnum, and finite float inputs.
# ==============================================================================


@pytest.mark.unit
@given(value=strict_ints())
def test_is_strict_int_accepts_true_integers(value: int) -> None:
    """Verify is_strict_int returns True for all true integers."""
    assert prim.is_strict_int(value) is True


@pytest.mark.unit
def test_is_strict_int_accepts_int_enum_instances() -> None:
    """Verify is_strict_int returns True for IntEnum values."""
    assert prim.is_strict_int(_SampleIntEnum.ONE) is True


@pytest.mark.unit
@given(
    value=st.one_of(
        strict_ints(),
        st.floats(allow_nan=False, allow_infinity=False),
    )
)
def test_is_finite_number_accepts_finite_ints_and_floats(value: int | float) -> None:
    """Verify is_finite_number returns True for all finite ints and floats."""
    assert prim.is_finite_number(value) is True


# ==============================================================================
# GROUP 4: Error Handling & Validation Failures
# Note: Bool-as-int traps, non-finite floats, and non-numeric types.
# ==============================================================================


@pytest.mark.regression
@pytest.mark.parametrize(
    "non_strict_val",
    [
        True,
        False,
        1.0,
        -2.0,
        Decimal("10"),
        _SampleStrEnum.ONE,
        "1",
        None,
        [1],
    ],
)
def test_is_strict_int_rejects_explicit_non_int_types(non_strict_val: Any) -> None:
    """Verify is_strict_int rejects bool, float, Decimal, StrEnum, and containers."""
    assert prim.is_strict_int(non_strict_val) is False


@pytest.mark.regression
@given(value=bool_or_non_int())
def test_is_strict_int_rejects_booleans_and_non_integers(value: Any) -> None:
    """Verify is_strict_int rejects booleans, floats, strings, None, and containers."""
    assert prim.is_strict_int(value) is False


@pytest.mark.regression
@pytest.mark.parametrize(
    "non_finite_val",
    [True, False, float("nan"), float("inf"), float("-inf"), "42", None],
)
def test_is_finite_number_rejects_explicit_booleans_and_non_finite_values(
    non_finite_val: Any,
) -> None:
    """Verify is_finite_number rejects bool, NaN, +/-Inf, strings, and None."""
    assert prim.is_finite_number(non_finite_val) is False


@pytest.mark.regression
@given(
    value=st.one_of(
        st.booleans(),
        non_finite_floats(),
        st.text(max_size=8),
        st.none(),
    )
)
def test_is_finite_number_rejects_booleans_and_non_finite_floats(value: Any) -> None:
    """Verify is_finite_number rejects booleans, NaN, Inf, -Inf, strings, and None."""
    assert prim.is_finite_number(value) is False
