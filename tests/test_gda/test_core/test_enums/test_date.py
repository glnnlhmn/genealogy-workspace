"""Path: tests/test_gda/test_core/test_enums/test_date.py

Targeted behavioral test suite verifying historical temporal and date modifier enums.

Operational Role:
    Validates US Federal decennial census schedule enumeration years (CensusYearUS),
    DateModifier values, MODIFIER_ALIASES mapping parity, and normalize_modifier
    normalization, coercion, passthrough, and rejection boundaries.

Test Structure & Protocol:
    - Atomized tests: 1:1 verification per behavioral contract.
    - Fully decorated: Strictly unit and regression markers.
    - Dependencies: In-memory only; zero physical disk I/O.
"""

from __future__ import annotations

import pytest

from gda.core.enums.date import (
    MODIFIER_ALIASES,
    CensusYearUS,
    DateModifier,
    normalize_modifier,
)

__version__ = "1.0.0+build.1"


# ==============================================================================
# GROUP 1: CensusYearUS Enumeration Invariants
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_census_year_us_count_and_members() -> None:
    """Verify CensusYearUS defines all 16 US decennial census schedules from 1790 to 1950."""
    expected_years = [
        1790,
        1800,
        1810,
        1820,
        1830,
        1840,
        1850,
        1860,
        1870,
        1880,
        1900,
        1910,
        1920,
        1930,
        1940,
        1950,
    ]
    actual_years = [m.value for m in CensusYearUS]
    assert actual_years == expected_years
    assert len(CensusYearUS) == 16


@pytest.mark.unit
def test_census_year_us_backwards_compatibility_aliases() -> None:
    """Verify CensusYearUS members evaluate as canonical integer years."""
    assert CensusYearUS.Y1790 == 1790
    assert CensusYearUS.Y1880 == 1880
    assert CensusYearUS.Y1950 == 1950
    assert int(CensusYearUS.Y1920) == 1920


# ==============================================================================
# GROUP 2: DateModifier Canonical Values & Aliases Parity
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_date_modifier_canonical_values() -> None:
    """Verify canonical DateModifier members evaluate to expected string codes."""
    assert DateModifier.EXACT == "EXACT"
    assert DateModifier.ABOUT == "ABT"
    assert DateModifier.BEFORE == "BEF"
    assert DateModifier.AFTER == "AFT"
    assert DateModifier.BETWEEN == "BET"
    assert DateModifier.ESTIMATED == "EST"
    assert DateModifier.CALCULATED == "CAL"
    assert len(DateModifier) == 7


@pytest.mark.unit
@pytest.mark.integrity
def test_modifier_aliases_mapping_targets_are_valid_enum_members() -> None:
    """Verify every target in MODIFIER_ALIASES is an instance of DateModifier."""
    for alias_key, enum_val in MODIFIER_ALIASES.items():
        assert isinstance(alias_key, str)
        assert isinstance(enum_val, DateModifier)


# ==============================================================================
# GROUP 3: normalize_modifier Parsing & Branch Verification (Lines 91-98)
# ==============================================================================


@pytest.mark.unit
def test_normalize_modifier_none_returns_none() -> None:
    """Verify normalize_modifier returns None when input is None (Line 91-92)."""
    assert normalize_modifier(None) is None


@pytest.mark.unit
def test_normalize_modifier_enum_passthrough() -> None:
    """Verify normalize_modifier returns unmodified DateModifier instances (Line 93-94)."""
    for member in DateModifier:
        assert normalize_modifier(member) is member


@pytest.mark.unit
@pytest.mark.parametrize(
    ("input_token", "expected_modifier"),
    [
        ("EXACT", DateModifier.EXACT),
        ("exact", DateModifier.EXACT),
        ("ABT", DateModifier.ABOUT),
        ("abt", DateModifier.ABOUT),
        ("ABOUT", DateModifier.ABOUT),
        ("about", DateModifier.ABOUT),
        ("CIRCA", DateModifier.ABOUT),
        ("circa", DateModifier.ABOUT),
        ("C", DateModifier.ABOUT),
        ("c", DateModifier.ABOUT),
        ("CA", DateModifier.ABOUT),
        ("ca", DateModifier.ABOUT),
        ("BEF", DateModifier.BEFORE),
        ("bef", DateModifier.BEFORE),
        ("BEFORE", DateModifier.BEFORE),
        ("before", DateModifier.BEFORE),
        ("AFT", DateModifier.AFTER),
        ("aft", DateModifier.AFTER),
        ("AFTER", DateModifier.AFTER),
        ("after", DateModifier.AFTER),
        ("BET", DateModifier.BETWEEN),
        ("bet", DateModifier.BETWEEN),
        ("BETWEEN", DateModifier.BETWEEN),
        ("between", DateModifier.BETWEEN),
        ("EST", DateModifier.ESTIMATED),
        ("est", DateModifier.ESTIMATED),
        ("ESTIMATED", DateModifier.ESTIMATED),
        ("estimated", DateModifier.ESTIMATED),
        ("CAL", DateModifier.CALCULATED),
        ("cal", DateModifier.CALCULATED),
        ("CALCULATED", DateModifier.CALCULATED),
        ("calculated", DateModifier.CALCULATED),
        ("  abt  ", DateModifier.ABOUT),
        ("\tBEFORE\n", DateModifier.BEFORE),
    ],
)
def test_normalize_modifier_string_variants(
    input_token: str,
    expected_modifier: DateModifier,
) -> None:
    """Verify normalize_modifier parses uppercase, lowercase, and padded tokens (Lines 95-97)."""
    assert normalize_modifier(input_token) is expected_modifier


@pytest.mark.unit
@pytest.mark.regression
@pytest.mark.parametrize(
    "invalid_token",
    [
        "",
        "   ",
        "INVALID",
        "UNKNOWN",
        "CIRCA_1880",
        "123",
    ],
)
def test_normalize_modifier_invalid_raises_value_error(invalid_token: str) -> None:
    """Verify normalize_modifier raises ValueError on unrecognized tokens (Line 98)."""
    with pytest.raises(ValueError, match="Invalid DateModifier value"):
        normalize_modifier(invalid_token)
