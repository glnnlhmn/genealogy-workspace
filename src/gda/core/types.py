"""Path: src/gda/core/types.py

Authoritative regex patterns, format tokens, and primitive scalar definitions.

Operational Role:
    Provides the code-first declarative repository for RFC 4122 UUIDv4 patterns,
    ISO 8601 date and timestamp directives, canonical 6-digit entity identifier
    regex patterns, archival URN patterns across all documentary domains, gender
    code sets, historical year bounds, coordinate bounds, scalar metric bounds/patterns,
    military domain scalar bounds, enumerated schedule year sets/bounds, and SHA-256
    hexadecimal hash patterns across the GDA core infrastructure.
"""

from __future__ import annotations

import re

__version__ = "1.0.0+build.1"

__all__ = [
    "ATOM_ID_PATTERN",
    "ATOM_ID_REGEX",
    "CENSUS_SHEET_SIDES",
    "CIVIL_WAR_DRAFT_YEARS",
    "COLONIAL_MILITIA_MAX_YEAR",
    "COLONIAL_MILITIA_MIN_YEAR",
    "ENTITY_ID_PATTERNS",
    "ENTITY_ID_REGEXES",
    "GENDER_CODES",
    "ISO_DATE_FMT",
    "ISO_DATE_PATTERN",
    "ISO_DATE_REGEX",
    "ISO_MONTH_FMT",
    "ISO_TIMESTAMP_FMT",
    "ISO_TIMESTAMP_PATTERN",
    "ISO_TIMESTAMP_REGEX",
    "ISO_YEAR_FMT",
    "MAX_BOUNTY_LAND_ACREAGE",
    "MAX_CENSUS_LINE_NUMBER",
    "MAX_CONFIDENCE_SCORE",
    "MAX_ENLISTMENT_TERM_MONTHS",
    "MAX_FOREIGN_SERVICE_MONTHS",
    "MAX_HEIGHT_INCHES",
    "MAX_HISTORICAL_YEAR",
    "MAX_LATITUDE",
    "MAX_LONGITUDE",
    "MAX_MINOR_CHILDREN_COUNT",
    "MAX_QUAY_SCORE",
    "MAX_VIETNAM_LOTTERY_NUMBER",
    "MAX_WEIGHT_LBS",
    "MIN_AHNENTAFEL",
    "MIN_CONFIDENCE_SCORE",
    "MIN_ENLISTMENT_TERM_MONTHS",
    "MIN_HEIGHT_INCHES",
    "MIN_HISTORICAL_YEAR",
    "MIN_LATITUDE",
    "MIN_LONGITUDE",
    "MIN_QUAY_SCORE",
    "MIN_VIETNAM_LOTTERY_NUMBER",
    "MIN_WEIGHT_LBS",
    "MODERN_SSS_MIN_YEAR",
    "NEWS_CATEGORY_PATTERN",
    "NEWS_CATEGORY_REGEX",
    "PUB_CODE_PATTERN",
    "PUB_CODE_REGEX",
    "SHA256_PATTERN",
    "SHA256_REGEX",
    "TAX_ASSESSMENT_MIN_YEAR",
    "URN_BASE_PATTERN",
    "URN_BASE_REGEX",
    "URN_PATTERNS",
    "URN_REGEXES",
    "US_AGRICULTURAL_SCHEDULE_YEARS",
    "US_FEDERAL_CENSUS_1850_1870_YEARS",
    "US_FEDERAL_CENSUS_1900_1910_YEARS",
    "US_FEDERAL_CENSUS_TALLY_YEARS",
    "US_FEDERAL_CENSUS_YEARS",
    "US_MANUFACTURING_SCHEDULE_YEARS",
    "US_MORTALITY_SCHEDULE_YEARS",
    "US_SLAVE_SCHEDULE_YEARS",
    "US_VETERANS_SCHEDULE_YEAR",
    "UUID_V4_PATTERN",
    "UUID_V4_REGEX",
    "WWII_DRAFT_YEARS",
    "WWI_DRAFT_YEARS",
]

# ------------------------------------------------------------------------------
# String Format Directives (strftime / strptime)
# ------------------------------------------------------------------------------
ISO_YEAR_FMT: str = "%Y"
ISO_MONTH_FMT: str = "%Y-%m"
ISO_DATE_FMT: str = "%Y-%m-%d"
ISO_TIMESTAMP_FMT: str = "%Y-%m-%dT%H:%M:%SZ"

# ------------------------------------------------------------------------------
# Canonical Domain Scalar Sets & Numerical Invariants
# ------------------------------------------------------------------------------
GENDER_CODES: frozenset[str] = frozenset({"M", "F", "U"})
MIN_HISTORICAL_YEAR: int = 1000
MAX_HISTORICAL_YEAR: int = 2100

MIN_LATITUDE: float = -90.0
MAX_LATITUDE: float = 90.0
MIN_LONGITUDE: float = -180.0
MAX_LONGITUDE: float = 180.0

MIN_QUAY_SCORE: int = 0
MAX_QUAY_SCORE: int = 3
MIN_AHNENTAFEL: int = 1
MIN_CONFIDENCE_SCORE: float = 0.0
MAX_CONFIDENCE_SCORE: float = 1.0

# ------------------------------------------------------------------------------
# Military Record Scalar Bounds & Era Year Sets
# ------------------------------------------------------------------------------
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

# ------------------------------------------------------------------------------
# Enumerated Schedule & Roll Bounds / Era Year Sets
# ------------------------------------------------------------------------------
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

# ------------------------------------------------------------------------------
# Structural Regex Patterns (Strict 6-digit SmartID standard)
# ------------------------------------------------------------------------------
UUID_V4_PATTERN: str = r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
ISO_DATE_PATTERN: str = r"^\d{4}(-(0[1-9]|1[0-2])(-(0[1-9]|[12]\d|3[01]))?)?$"
ISO_TIMESTAMP_PATTERN: str = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
SHA256_PATTERN: str = r"^[0-9a-f]{64}$"

PUB_CODE_PATTERN: str = r"^[A-Z0-9_-]{2,20}$"
NEWS_CATEGORY_PATTERN: str = r"^[A-Z]{3,15}$"

ATOM_ID_PATTERN: str = r"^([A-Z]{3})-(\d{6})$"
ENTITY_ID_PATTERNS: dict[str, str] = {
    "IND": r"^IND-\d{6}$",
    "FID": r"^FID-\d{6}$",
    "LOC": r"^LOC-\d{6}$",
    "SID": r"^SID-\d{6}$",
    "FAM": r"^FAM-\d{6}$",
    "NOT": r"^NOT-\d{6}$",
    "REP": r"^REP-\d{6}$",
    "DRF": r"^DRF-\d{6}$",
    "ORG": r"^ORG-\d{6}$",
}

URN_BASE_PATTERN: str = r"^URN:[A-Z0-9_-]+(:[A-Za-z0-9_.-]+)+$"
URN_PATTERNS: dict[str, str] = {
    "SRC": r"^URN:SRC:[0-9]{4}:[A-Z0-9_]+:[A-Za-z0-9_.-]+$",
    "DRAFT": r"^URN:DRAFT:[0-9]{4}:[A-Z0-9_]+:[A-Za-z0-9_.-]+$",
    "CENSUS": r"^URN:CENSUS:[0-9]{4}:[A-Z0-9_]+:[A-Za-z0-9_.-]+$",
    "VITAL": r"^URN:VITAL:(BIRTH|MARRIAGE|DEATH):[0-9]{4}:[A-Z0-9_]+:[A-Za-z0-9_.-]+$",
    "CEM": r"^URN:CEM:[A-Z0-9_]+:[A-Za-z0-9_.-]+$",
    "DIPLOMA": r"^URN:DIPLOMA:[0-9]{4}:[A-Z0-9_]+:[A-Za-z0-9_.-]+$",
    "IMMIGRATION": r"^URN:IMMIGRATION:[0-9]{4}:[A-Z0-9_]+:[A-Za-z0-9_.-]+$",
    "NATURALIZATION": r"^URN:NATURALIZATION:[0-9]{4}:[A-Z0-9_]+:[A-Za-z0-9_.-]+$",
    "LAND": r"^URN:LAND:[0-9]{4}:[A-Z0-9_]+:[A-Za-z0-9_.-]+$",
    "MS": r"^URN:MS:[0-9]{4}:[A-Z0-9_]+:[A-Za-z0-9_.-]+$",
    "BIBLE": r"^URN:BIBLE:[0-9]{4}:[A-Z0-9_]+:[A-Za-z0-9_.-]+$",
    "NARRATIVE": r"^URN:NARRATIVE:[0-9]{4}:[A-Z0-9_]+:[A-Za-z0-9_.-]+$",
    "OTHER": r"^URN:OTHER:[0-9]{4}:[A-Z0-9_]+:[A-Za-z0-9_.-]+$",
    "WILL": r"^URN:WILL:[0-9]{4}:[A-Z0-9_]+:[A-Za-z0-9_.-]+$",
}

# ------------------------------------------------------------------------------
# Compiled Regular Expressions
# ------------------------------------------------------------------------------
UUID_V4_REGEX: re.Pattern[str] = re.compile(UUID_V4_PATTERN)
ISO_DATE_REGEX: re.Pattern[str] = re.compile(ISO_DATE_PATTERN)
ISO_TIMESTAMP_REGEX: re.Pattern[str] = re.compile(ISO_TIMESTAMP_PATTERN)
SHA256_REGEX: re.Pattern[str] = re.compile(SHA256_PATTERN)
PUB_CODE_REGEX: re.Pattern[str] = re.compile(PUB_CODE_PATTERN)
NEWS_CATEGORY_REGEX: re.Pattern[str] = re.compile(NEWS_CATEGORY_PATTERN)
ATOM_ID_REGEX: re.Pattern[str] = re.compile(ATOM_ID_PATTERN)
ENTITY_ID_REGEXES: dict[str, re.Pattern[str]] = {
    prefix: re.compile(pattern) for prefix, pattern in ENTITY_ID_PATTERNS.items()
}
URN_BASE_REGEX: re.Pattern[str] = re.compile(URN_BASE_PATTERN)
URN_REGEXES: dict[str, re.Pattern[str]] = {
    nid: re.compile(pattern) for nid, pattern in URN_PATTERNS.items()
}
