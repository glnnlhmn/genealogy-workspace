"""Path: tests/test_gda/test_core/test_enums/test_date_enums.py

Targeted behavioral test suite verifying historical temporal and date modifier enums.

Operational Role:
    Validates gda.core.enums.date public exports, US Federal decennial census
    schedule years (CensusYearUS), DateModifier canonical codes, DateModifier.from_raw()
    (including optional field_name diagnostics), read-only MappingProxyType
    MODIFIER_ALIASES, and normalize_modifier parsing and rejection boundaries.

Test Structure & Protocol:
    - Atomized & parametrized tests: 1:1 behavioral contract mapping.
    - Fully decorated: 5-marker taxonomy (smoke, unit, regression, integrity).
    - Dependencies: In-memory only; zero physical disk I/O.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any

import pytest

import gda.core.enums.date as date_enums
from gda.core.enums.date import (
    MODIFIER_ALIASES,
    CensusYearUS,
    DateModifier,
    normalize_modifier,
)
from gda.core.errors import ModelFormatError

__version__ = "1.0.0+build.5"


# ==============================================================================
# GROUP 1: Smoke & Primary Entrypoints
# Note: Single smoke gate verifying gda.core.enums.date public exports.
# ==============================================================================


@pytest.mark.smoke
@pytest.mark.unit
def test_date_enums_exposes_expected_public_interface() -> None:
    """Verify gda.core.enums.date exports CensusYearUS, DateModifier, and helpers."""
    expected = {"CensusYearUS", "DateModifier", "MODIFIER_ALIASES", "normalize_modifier"}
    assert set(date_enums.__all__) == expected


# ==============================================================================
# GROUP 2: Core Logic & Happy Paths
# Note: CensusYearUS decennial schedule integers and DateModifier codes.
# ==============================================================================


@pytest.mark.unit
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
    assert [m.value for m in CensusYearUS] == expected_years
    assert len(CensusYearUS) == 16
    assert CensusYearUS.Y1790 == 1790
    assert int(CensusYearUS.Y1920) == 1920
    assert CensusYearUS.Y1950 == 1950


@pytest.mark.unit
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


# ==============================================================================
# GROUP 3: Edge Cases & Boundary Conditions
# Note: normalize_modifier None handling, enum passthrough, and alias variants.
# ==============================================================================


@pytest.mark.unit
def test_normalize_modifier_none_and_enum_passthrough() -> None:
    """Verify normalize_modifier returns None for None and passes through DateModifier."""
    assert normalize_modifier(None) is None
    for member in DateModifier:
        assert normalize_modifier(member) is member
        assert DateModifier.from_raw(member) is member


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
        (" abt ", DateModifier.ABOUT),
        ("\tBEFORE\n", DateModifier.BEFORE),
    ],
)
def test_date_modifier_from_raw_and_normalize_modifier_string_variants(
    input_token: str,
    expected_modifier: DateModifier,
) -> None:
    """Verify DateModifier.from_raw and normalize_modifier parse alias and case variants."""
    assert DateModifier.from_raw(input_token) is expected_modifier
    assert normalize_modifier(input_token) is expected_modifier


# ==============================================================================
# GROUP 4: Error Handling & Validation Failures
# Note: Rejection of unrecognized or non-string tokens via ModelFormatError.
# ==============================================================================


@pytest.mark.regression
@pytest.mark.parametrize(
    "invalid_token",
    ["", " ", "INVALID", "UNKNOWN", "CIRCA_1880", "123", 456],
)
def test_date_modifier_from_raw_and_normalize_modifier_raise_model_format_error(
    invalid_token: Any,
) -> None:
    """Verify DateModifier.from_raw and normalize_modifier raise ModelFormatError."""
    with pytest.raises(ModelFormatError) as exc_raw:
        DateModifier.from_raw(invalid_token)
    assert exc_raw.value.error_code == "ERR_MODEL_FORMAT"

    with pytest.raises(ModelFormatError) as exc_norm:
        normalize_modifier(invalid_token)
    assert exc_norm.value.error_code == "ERR_MODEL_FORMAT"


@pytest.mark.regression
@pytest.mark.unit
def test_date_modifier_from_raw_includes_field_name_in_error_details() -> None:
    """Verify DateModifier.from_raw attaches optional field_name to ModelFormatError details."""
    with pytest.raises(ModelFormatError) as exc_info:
        DateModifier.from_raw("bad_modifier", field_name="modifier")
    assert exc_info.value.error_code == "ERR_MODEL_FORMAT"
    assert exc_info.value.details.get("field_name") == "modifier"


# ==============================================================================
# GROUP 6: Integrity & Invariants
# Note: MODIFIER_ALIASES MappingProxyType immutability and target integrity.
# ==============================================================================


@pytest.mark.integrity
@pytest.mark.unit
def test_modifier_aliases_is_immutable_and_targets_are_valid_enum_members() -> None:
    """Verify MODIFIER_ALIASES is a MappingProxyType mapping to valid DateModifier members."""
    assert isinstance(MODIFIER_ALIASES, MappingProxyType)
    with pytest.raises(TypeError):
        MODIFIER_ALIASES["BAD"] = DateModifier.EXACT  # type: ignore[index]

    for alias_key, enum_val in MODIFIER_ALIASES.items():
        assert isinstance(alias_key, str)
        assert isinstance(enum_val, DateModifier)
