"""Path: src/gda/core/constants/military.py

Military service, pension, and conscription scalar bounds and historical era year sets.

Operational Role:
    Centralizes immutable bounds for enlistment terms, foreign service duration,
    bounty land acreage, dependent counts, physical measurements, Vietnam draft
    lottery numbers, and statutory draft/militia era year sets.
"""

from __future__ import annotations

__version__ = "1.0.0+build.1"

__all__ = [
    "CIVIL_WAR_DRAFT_YEARS",
    "COLONIAL_MILITIA_MAX_YEAR",
    "COLONIAL_MILITIA_MIN_YEAR",
    "MAX_BOUNTY_LAND_ACREAGE",
    "MAX_ENLISTMENT_TERM_MONTHS",
    "MAX_FOREIGN_SERVICE_MONTHS",
    "MAX_HEIGHT_INCHES",
    "MAX_MINOR_CHILDREN_COUNT",
    "MAX_VIETNAM_LOTTERY_NUMBER",
    "MAX_WEIGHT_LBS",
    "MIN_ENLISTMENT_TERM_MONTHS",
    "MIN_HEIGHT_INCHES",
    "MIN_VIETNAM_LOTTERY_NUMBER",
    "MIN_WEIGHT_LBS",
    "MODERN_SSS_MIN_YEAR",
    "WWII_DRAFT_YEARS",
    "WWI_DRAFT_YEARS",
]

MIN_ENLISTMENT_TERM_MONTHS: int = 1
MAX_ENLISTMENT_TERM_MONTHS: int = 120
MAX_FOREIGN_SERVICE_MONTHS: int = 600
MAX_BOUNTY_LAND_ACREAGE: int = 1000
MAX_MINOR_CHILDREN_COUNT: int = 25
MIN_VIETNAM_LOTTERY_NUMBER: int = 1
MAX_VIETNAM_LOTTERY_NUMBER: int = 366
MIN_HEIGHT_INCHES: int = 36
MAX_HEIGHT_INCHES: int = 96
MIN_WEIGHT_LBS: int = 50
MAX_WEIGHT_LBS: int = 500

COLONIAL_MILITIA_MIN_YEAR: int = 1607
COLONIAL_MILITIA_MAX_YEAR: int = 1815
CIVIL_WAR_DRAFT_YEARS: frozenset[int] = frozenset({1862, 1863, 1864, 1865})
WWI_DRAFT_YEARS: frozenset[int] = frozenset({1917, 1918})
WWII_DRAFT_YEARS: frozenset[int] = frozenset({1940, 1941, 1942, 1943, 1944, 1945, 1946})
MODERN_SSS_MIN_YEAR: int = 1948
