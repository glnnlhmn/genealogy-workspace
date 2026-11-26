"""Path: src/gda/core/constants/census.py

Enumerated census schedule and tax assessment bounds and historical year sets.

Operational Role:
    Centralizes immutable sheet-side tokens, line limits, tax assessment year
    floors, and US Federal decennial and supplemental schedule year sets.
"""

from __future__ import annotations

__version__ = "1.0.0+build.1"

__all__ = [
    "CENSUS_SHEET_SIDES",
    "MAX_CENSUS_LINE_NUMBER",
    "TAX_ASSESSMENT_MIN_YEAR",
    "US_AGRICULTURAL_SCHEDULE_YEARS",
    "US_FEDERAL_CENSUS_1850_1870_YEARS",
    "US_FEDERAL_CENSUS_1900_1910_YEARS",
    "US_FEDERAL_CENSUS_TALLY_YEARS",
    "US_FEDERAL_CENSUS_YEARS",
    "US_MANUFACTURING_SCHEDULE_YEARS",
    "US_MORTALITY_SCHEDULE_YEARS",
    "US_SLAVE_SCHEDULE_YEARS",
    "US_VETERANS_SCHEDULE_YEAR",
]

CENSUS_SHEET_SIDES: frozenset[str] = frozenset({"A", "B"})
MAX_CENSUS_LINE_NUMBER: int = 200
TAX_ASSESSMENT_MIN_YEAR: int = 1600

US_FEDERAL_CENSUS_TALLY_YEARS: frozenset[int] = frozenset({1790, 1800, 1810, 1820, 1830, 1840})
US_FEDERAL_CENSUS_1850_1870_YEARS: frozenset[int] = frozenset({1850, 1860, 1870})
US_FEDERAL_CENSUS_1900_1910_YEARS: frozenset[int] = frozenset({1900, 1910})
US_FEDERAL_CENSUS_YEARS: frozenset[int] = frozenset(
    {
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
        1890,
        1900,
        1910,
        1920,
        1930,
        1940,
        1950,
    }
)
US_MORTALITY_SCHEDULE_YEARS: frozenset[int] = frozenset({1850, 1860, 1870, 1880, 1885})
US_AGRICULTURAL_SCHEDULE_YEARS: frozenset[int] = frozenset({1850, 1860, 1870, 1880})
US_MANUFACTURING_SCHEDULE_YEARS: frozenset[int] = frozenset({1810, 1820, 1850, 1860, 1870, 1880})
US_SLAVE_SCHEDULE_YEARS: frozenset[int] = frozenset({1850, 1860})
US_VETERANS_SCHEDULE_YEAR: int = 1890
