"""Path: tests/test_gda/test_model/test_atom/test_date.py

Comprehensive test suite verifying atomic temporal primitives (DateString, IsoTimestamp).

Operational Role:
    Verifies DateString and IsoTimestamp format validation, strict rejection of
    unnormalized outer whitespace, string equality, homogeneous total ordering,
    frozen immutability, and introspection invariants.

Test Structure & Protocol:
    - Atomized tests: 1:1 behavioral contract mapping.
    - Fully decorated: Pytest marker taxonomy (1 @pytest.mark.smoke).
    - Zero production disk I/O.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from typing import Any

import pytest
from tests.test_gda.test_model.test_atom.conftest import INVALID_NON_STRING_VALUES

from gda.core.dates import utc_now_iso
from gda.core.errors import ModelFormatError
from gda.model.atom.date import DateString, IsoTimestamp

__version__ = "1.0.0+build.3"


# ==============================================================================
# GROUP 1: DATESTRING FORMAT VALIDATION & STRICT WHITESPACE REJECTION
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
@pytest.mark.parametrize(
    "valid_date",
    [
        "1880",
        "1880-05",
        "1880-05-14",
        "14 APR 1865",
        "ABT 1850",
        "BEF 1900",
    ],
)
def test_date_string_valid_instantiation(valid_date: str) -> None:
    """Verify DateString preserves canonical genealogical date expressions."""
    ds = DateString(valid_date)
    assert ds.value == valid_date
    assert str(ds) == valid_date
    assert repr(ds) == f"DateString(value='{valid_date}')"


@pytest.mark.unit
@pytest.mark.regression
@pytest.mark.parametrize(
    "invalid_date",
    [
        "",
        " ",
        "\t\n",
        " 1880",
        "1880 ",
        "   12 MAY 1880   ",
        "\t1880-05-14\n",
    ],
)
def test_date_string_empty_or_padded_raises_format_error(invalid_date: str) -> None:
    """Verify DateString raises ModelFormatError on empty or unnormalized outer whitespace."""
    with pytest.raises(ModelFormatError, match="Invalid DateString"):
        DateString(invalid_date)


@pytest.mark.unit
@pytest.mark.regression
@pytest.mark.parametrize("bad_type", INVALID_NON_STRING_VALUES)
def test_date_string_non_string_raises_error(bad_type: Any) -> None:
    """Verify DateString rejects non-string types without coercion."""
    with pytest.raises((ModelFormatError, TypeError, ValueError)):
        DateString(bad_type)


# ==============================================================================
# GROUP 2: ISOTIMESTAMP FORMAT VALIDATION
# ==============================================================================


@pytest.mark.unit
@pytest.mark.parametrize(
    "valid_iso",
    [
        "2026-10-16T12:00:00Z",
        "2026-10-16T12:00:00.123456Z",
        "2026-10-16T08:00:00-04:00",
        "2026-10-16T17:30:00+05:30",
    ],
)
def test_iso_timestamp_valid_formats(valid_iso: str) -> None:
    """Verify IsoTimestamp validates extended ISO 8601 UTC and offset representations."""
    ts = IsoTimestamp(valid_iso)
    assert ts.value == valid_iso
    assert str(ts) == valid_iso
    assert repr(ts) == f"IsoTimestamp(value='{valid_iso}')"


@pytest.mark.unit
def test_iso_timestamp_accepts_core_utc_now_iso() -> None:
    """Verify IsoTimestamp seamlessly wraps output from gda.core.dates.utc_now_iso()."""
    ts = IsoTimestamp(utc_now_iso())
    assert ts.value.endswith("Z")
    assert len(ts.value) == 20


@pytest.mark.unit
@pytest.mark.regression
@pytest.mark.parametrize(
    "invalid_iso",
    [
        "",
        "   ",
        "2026-10-16",
        "2026-10-16 12:00:00",
        "2026-10-16T12:00:00",
        " 2026-10-16T12:00:00Z ",
        "12:00:00Z",
        "not-a-timestamp",
    ],
)
def test_iso_timestamp_invalid_syntax_raises_format_error(invalid_iso: str) -> None:
    """Verify IsoTimestamp raises ModelFormatError on malformed or padded timestamps."""
    with pytest.raises(ModelFormatError, match="Must match ISO 8601 extended format"):
        IsoTimestamp(invalid_iso)


# ==============================================================================
# GROUP 3: EQUALITY, HOMOGENEOUS ORDERING, IMMUTABILITY & INTROSPECTION
# ==============================================================================


@pytest.mark.unit
def test_temporal_atoms_equality_and_ordering(
    sample_date_string: DateString,
    sample_iso_timestamp: IsoTimestamp,
) -> None:
    """Verify primitive string equality, hashing, and homogeneous ordering."""
    assert sample_date_string == DateString("14 APR 1865")
    assert sample_date_string == "14 APR 1865"
    assert (sample_date_string == 1865) is False  # type: ignore[comparison-overlap]
    assert hash(sample_date_string) == hash("14 APR 1865")

    d1 = DateString("1880-01-01")
    d2 = DateString("1890-01-01")
    assert d1 < d2
    assert d2 > d1

    t1 = IsoTimestamp("2026-01-01T00:00:00Z")
    t2 = IsoTimestamp("2026-12-31T23:59:59Z")
    assert t1 < t2
    assert sample_iso_timestamp == IsoTimestamp("2026-10-16T12:00:00Z")
    assert sample_iso_timestamp == "2026-10-16T12:00:00Z"
    assert (sample_iso_timestamp == 2026) is False  # type: ignore[comparison-overlap]
    assert hash(sample_iso_timestamp) == hash("2026-10-16T12:00:00Z")

    # Cross-type ordering must raise TypeError
    with pytest.raises(TypeError):
        _ = d1 < t1  # type: ignore[operator]
    with pytest.raises(TypeError):
        _ = d1 < "1890-01-01"  # type: ignore[operator]
    with pytest.raises(TypeError):
        _ = t1 < "2026-12-31T23:59:59Z"  # type: ignore[operator]


@pytest.mark.unit
def test_temporal_atoms_immutability(
    sample_date_string: DateString,
    sample_iso_timestamp: IsoTimestamp,
) -> None:
    """Verify temporal primitives are frozen and immutable."""
    with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
        sample_date_string.value = "1881"  # type: ignore[misc]

    with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
        sample_iso_timestamp.value = "2026-01-01T00:00:00Z"  # type: ignore[misc]


@pytest.mark.unit
def test_temporal_atoms_introspection(sample_date_string: DateString) -> None:
    """Verify .help() mixin renders directory on temporal primitives."""
    help_text = sample_date_string.help(as_str=True)
    assert help_text is not None
    assert "=== DateString Public Directory ===" in help_text
