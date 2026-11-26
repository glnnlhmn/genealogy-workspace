"""Path: tests/test_gda/test_core/test_constants/test_constants.py

Targeted behavioral test suite verifying gda.core.constants exports and invariants.

Operational Role:
    Validates public facade exports in gda.core.constants.__all__, domain scalar
    bounds (domain.py), military service/draft bounds and era year sets
    (military.py), and enumerated census/tax bounds and schedule year sets
    (census.py).

Test Structure & Protocol:
    - Atomized & parametrized tests: 1:1 behavioral contract mapping.
    - Fully decorated: 5-marker taxonomy (smoke, unit, integrity).
    - Dependencies: Pure in-memory evaluation with zero disk I/O.
"""

from __future__ import annotations

from typing import Any

import pytest

import gda.core.constants as consts
from gda.core.constants import census, domain, military

__version__ = "1.0.0+build.2"


# ==============================================================================
# GROUP 1: Smoke & Primary Entrypoints
# Note: Single smoke gate verifying gda.core.constants facade parity.
# ==============================================================================


@pytest.mark.smoke
@pytest.mark.integrity
@pytest.mark.unit
def test_constants_facade_exports_exact_union_of_submodules() -> None:
    """Verify gda.core.constants.__all__ is sorted, unique, and matches its submodules."""
    expected = set(domain.__all__) | set(military.__all__) | set(census.__all__)
    assert set(consts.__all__) == expected
    assert consts.__all__ == sorted(consts.__all__)
    assert len(consts.__all__) == len(expected)

    for symbol in expected:
        assert hasattr(consts, symbol)
        assert getattr(consts, symbol) is not None


# ==============================================================================
# GROUP 6: Integrity & Invariants
# Note: Domain scalar bounds, military era sets, and census schedule sets.
# ==============================================================================


@pytest.mark.integrity
@pytest.mark.unit
def test_domain_constants_bounds_and_code_sets() -> None:
    """Verify canonical gender codes, historical year bounds, coordinate bounds, and scalar limits."""
    assert consts.GENDER_CODES == frozenset({"M", "F", "U"})
    assert (consts.MIN_HISTORICAL_YEAR, consts.MAX_HISTORICAL_YEAR) == (1000, 2100)
    assert (consts.MIN_LATITUDE, consts.MAX_LATITUDE) == (-90.0, 90.0)
    assert (consts.MIN_LONGITUDE, consts.MAX_LONGITUDE) == (-180.0, 180.0)
    assert (consts.MIN_QUAY_SCORE, consts.MAX_QUAY_SCORE) == (0, 3)
    assert consts.MIN_AHNENTAFEL == 1
    assert (consts.MIN_CONFIDENCE_SCORE, consts.MAX_CONFIDENCE_SCORE) == (0.0, 1.0)


@pytest.mark.integrity
@pytest.mark.unit
@pytest.mark.parametrize(
    ("const_name", "expected_val"),
    [
        ("MIN_ENLISTMENT_TERM_MONTHS", 1),
        ("MAX_ENLISTMENT_TERM_MONTHS", 120),
        ("MAX_FOREIGN_SERVICE_MONTHS", 600),
        ("MAX_BOUNTY_LAND_ACREAGE", 1000),
        ("MAX_MINOR_CHILDREN_COUNT", 25),
        ("MIN_VIETNAM_LOTTERY_NUMBER", 1),
        ("MAX_VIETNAM_LOTTERY_NUMBER", 366),
        ("MIN_HEIGHT_INCHES", 36),
        ("MAX_HEIGHT_INCHES", 96),
        ("MIN_WEIGHT_LBS", 50),
        ("MAX_WEIGHT_LBS", 500),
        ("COLONIAL_MILITIA_MIN_YEAR", 1607),
        ("COLONIAL_MILITIA_MAX_YEAR", 1815),
        ("CIVIL_WAR_DRAFT_YEARS", frozenset({1862, 1863, 1864, 1865})),
        ("WWI_DRAFT_YEARS", frozenset({1917, 1918})),
        ("WWII_DRAFT_YEARS", frozenset({1940, 1941, 1942, 1943, 1944, 1945, 1946})),
        ("MODERN_SSS_MIN_YEAR", 1948),
    ],
)
def test_military_constants_bounds_and_era_year_sets(
    const_name: str,
    expected_val: Any,
) -> None:
    """Verify centralized military scalar bounds and historical draft era year sets."""
    assert getattr(consts, const_name) == expected_val


@pytest.mark.integrity
@pytest.mark.unit
@pytest.mark.parametrize(
    ("const_name", "expected_val"),
    [
        ("CENSUS_SHEET_SIDES", frozenset({"A", "B"})),
        ("MAX_CENSUS_LINE_NUMBER", 200),
        ("TAX_ASSESSMENT_MIN_YEAR", 1600),
        ("US_FEDERAL_CENSUS_TALLY_YEARS", frozenset({1790, 1800, 1810, 1820, 1830, 1840})),
        ("US_FEDERAL_CENSUS_1850_1870_YEARS", frozenset({1850, 1860, 1870})),
        ("US_FEDERAL_CENSUS_1900_1910_YEARS", frozenset({1900, 1910})),
        ("US_MORTALITY_SCHEDULE_YEARS", frozenset({1850, 1860, 1870, 1880, 1885})),
        ("US_AGRICULTURAL_SCHEDULE_YEARS", frozenset({1850, 1860, 1870, 1880})),
        ("US_MANUFACTURING_SCHEDULE_YEARS", frozenset({1810, 1820, 1850, 1860, 1870, 1880})),
        ("US_SLAVE_SCHEDULE_YEARS", frozenset({1850, 1860})),
        ("US_VETERANS_SCHEDULE_YEAR", 1890),
    ],
)
def test_census_constants_bounds_and_schedule_year_sets(
    const_name: str,
    expected_val: Any,
) -> None:
    """Verify centralized census and tax assessment bounds and historical year sets."""
    assert getattr(consts, const_name) == expected_val
    assert len(consts.US_FEDERAL_CENSUS_YEARS) == 17
