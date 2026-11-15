"""Path: tests/test_gda/test_model/test_atom/test_atom_year.py

Targeted behavioral test suite verifying HistoricalYear, BirthYear, and DeathYear atoms.

Operational Role:
    Verifies valid calendar year ranges (1000..2100), range error rejections (999, 2101),
    strict type enforcement (rejecting bool/str/float), cross-subclass lifecycle ordering
    (BirthYear <= DeathYear), raw integer equality, hashability, immutability,
    and introspection.

Test Structure & Protocol:
    - Atomized tests: 1:1 verification per behavioral contract.
    - Fully decorated: Pytest marker taxonomy (1 @pytest.mark.smoke).
    - Dependencies: In-memory only; zero physical disk I/O.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from typing import Any

import pytest
from tests.test_gda.test_model.test_atom.conftest import INVALID_NON_NUMERIC_VALUES

from gda.core.errors import ModelFormatError, ModelRangeError
from gda.model.atom.year import BirthYear, DeathYear, HistoricalYear

__version__ = "1.0.0+build.9"


# ==============================================================================
# GROUP 1: Construction & Boundary Invariants
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
@pytest.mark.parametrize("year_val", [1000, 1492, 1776, 1880, 1945, 2026, 2100])
def test_historical_year_valid_boundaries(year_val: int) -> None:
    """Verify HistoricalYear instantiates across the supported 1000..2100 range."""
    year = HistoricalYear(year_val)
    assert year.value == year_val
    assert int(year) == year_val
    assert str(year) == str(year_val)
    assert repr(year) == f"HistoricalYear(value={year_val})"


@pytest.mark.unit
@pytest.mark.regression
@pytest.mark.parametrize("invalid_year", [999, 500, 0, -1, -100, 2101, 2102, 3000])
def test_historical_year_out_of_bounds_raises_range_error(invalid_year: int) -> None:
    """Verify HistoricalYear raises ModelRangeError on boundary off-by-one values (999, 2101)."""
    with pytest.raises(ModelRangeError, match="out of range. Must be between 1000 and 2100"):
        HistoricalYear(invalid_year)


@pytest.mark.unit
@pytest.mark.regression
@pytest.mark.parametrize("bad_type", [*INVALID_NON_NUMERIC_VALUES, 1880.0, 1950.5])
def test_historical_year_non_int_or_bool_raises_format_error(bad_type: Any) -> None:
    """Verify HistoricalYear strictly rejects booleans, floats, and strings without coercion."""
    with pytest.raises((ModelFormatError, TypeError, ValueError)):
        HistoricalYear(bad_type)


@pytest.mark.unit
@pytest.mark.regression
def test_historical_year_post_init_defensive_type_guard() -> None:
    """Verify HistoricalYear.__post_init__ raises ModelFormatError if bypassed with non-int."""
    raw = object.__new__(HistoricalYear)
    object.__setattr__(raw, "value", True)
    with pytest.raises(ModelFormatError, match="Invalid HistoricalYear type"):
        raw.__post_init__()


# ==============================================================================
# GROUP 2: Domain Subclasses & Cross-Lifecycle Ordering
# ==============================================================================


@pytest.mark.unit
def test_birth_and_death_year_subclasses(
    sample_birth_year: BirthYear,
    sample_death_year: DeathYear,
) -> None:
    """Verify BirthYear and DeathYear specialize HistoricalYear and support lifecycle ordering."""
    assert isinstance(sample_birth_year, HistoricalYear)
    assert isinstance(sample_death_year, HistoricalYear)
    assert sample_birth_year.value == 1880
    assert sample_death_year.value == 1950
    assert repr(sample_birth_year) == "BirthYear(value=1880)"
    assert repr(sample_death_year) == "DeathYear(value=1950)"

    # Cross-subclass ordering across HistoricalYear hierarchy
    assert sample_birth_year < sample_death_year
    assert sample_birth_year <= sample_death_year
    assert sample_death_year > sample_birth_year
    assert sample_death_year >= sample_birth_year
    assert BirthYear(1900) <= DeathYear(1900)
    assert BirthYear(1900) == DeathYear(1900)


# ==============================================================================
# GROUP 3: Comparisons, Hashing & Ordering
# ==============================================================================


@pytest.mark.unit
def test_historical_year_ordering_and_comparison() -> None:
    """Verify comparison ordering, integer equality, hashing, and non-atom type mismatch handling."""
    y1 = HistoricalYear(1850)
    y2 = HistoricalYear(1880)
    y3 = HistoricalYear(1880)

    assert y1 < y2
    assert y2 <= y3
    assert y2 == y3
    assert y2 > y1
    assert y2 >= y1

    # Raw integer equality (but NOT bool or raw int inequality ordering)
    assert y2 == 1880
    assert (y2 == 1881) is False
    assert (y2 == True) is False  # noqa: E712  # type: ignore[comparison-overlap]
    assert (y1 == "1850") is False  # type: ignore[comparison-overlap]

    # Hash coverage
    assert hash(y2) == hash(y3) == hash(1880)
    assert len({y1, y2, y3}) == 2

    # Raw int and string ordering must raise TypeError
    with pytest.raises(TypeError):
        _ = y1 < 1880  # type: ignore[operator]
    with pytest.raises(TypeError):
        _ = y2 > 1850  # type: ignore[operator]
    with pytest.raises(TypeError):
        _ = y1 < "1880"  # type: ignore[operator]
    with pytest.raises(TypeError):
        _ = y1 <= "1880"  # type: ignore[operator]


# ==============================================================================
# GROUP 4: Immutability & Introspection
# ==============================================================================


@pytest.mark.unit
def test_historical_year_immutability(sample_birth_year: BirthYear) -> None:
    """Verify HistoricalYear instances are frozen and immutable."""
    with pytest.raises((FrozenInstanceError, AttributeError)):
        sample_birth_year.value = 1890  # type: ignore[misc]


@pytest.mark.unit
def test_historical_year_introspection(sample_birth_year: BirthYear) -> None:
    """Verify HistoricalYear inherits IntrospectableMixin with working .help()."""
    help_text = sample_birth_year.help(as_str=True)
    assert help_text is not None
    assert "BirthYear" in help_text
