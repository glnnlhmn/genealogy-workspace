"""Path: src/gda/core/types.py

Authoritative regex patterns, format tokens, and primitive scalar definitions.

Operational Role:
    Provides the code-first declarative repository for RFC 4122 UUIDv4 patterns,
    ISO 8601 date and timestamp directives, canonical entity identifier regex patterns,
    archival URN patterns, gender code sets, historical year bounds, coordinate bounds,
    scalar metric bounds/patterns, military domain scalar bounds, and SHA-256 hexadecimal
    hash patterns across the GDA core infrastructure.
"""

from __future__ import annotations

import re

__version__ = "1.1.0+build.1"

__all__ = [
    "ATOM_ID_PATTERN",
    "ATOM_ID_REGEX",
    "CIVIL_WAR_DRAFT_YEARS",
    "COLONIAL_MILITIA_MAX_YEAR",
    "COLONIAL_MILITIA_MIN_YEAR",
    "ENTITY_ID_PATTERNS",
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
    "URN_BASE_PATTERN",
    "URN_BASE_REGEX",
    "URN_PATTERNS",
    "URN_REGEXES",
    "UUID_V4_PATTERN",
    "UUID_V4_REGEX",
    "WWI_DRAFT_YEARS",
    "WWII_DRAFT_YEARS",
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
# Structural Regex Patterns (from schemas/defs/_shared_defs.schema.json)
# ------------------------------------------------------------------------------
UUID_V4_PATTERN: str = r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
ISO_DATE_PATTERN: str = r"^\d{4}(-(0[1-9]|1[0-2])(-(0[1-9]|[12]\d|3[01]))?)?$"
ISO_TIMESTAMP_PATTERN: str = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
SHA256_PATTERN: str = r"^[0-9a-f]{64}$"

PUB_CODE_PATTERN: str = r"^[A-Z0-9_-]{2,20}$"
NEWS_CATEGORY_PATTERN: str = r"^[A-Z]{3,15}$"

ATOM_ID_PATTERN: str = r"^([A-Z]{3})-(\d{6,})$"
ENTITY_ID_PATTERNS: dict[str, str] = {
    "IND": r"^IND-\d{6,}$",
    "FID": r"^FID-\d{6,}$",
    "LOC": r"^LOC-\d{6,}$",
    "SID": r"^SID-\d{6,}$",
    "FAM": r"^FAM-\d{6,}$",
    "NOT": r"^NOT-\d{6,}$",
    "REP": r"^REP-\d{6,}$",
    "DRF": r"^DRF-\d{6,}$",
}

URN_BASE_PATTERN: str = r"^URN:[A-Z0-9_-]+(:[A-Za-z0-9_.-]+)+$"
URN_PATTERNS: dict[str, str] = {
    "SRC": r"^URN:SRC:[0-9]{4}:[A-Z0-9_]+:[A-Za-z0-9_.-]+$",
    "DRAFT": r"^URN:DRAFT:[0-9]{4}:[A-Z0-9_]+:[A-Za-z0-9_.-]+$",
    "CENSUS": r"^URN:CENSUS:[0-9]{4}:[A-Z0-9_]+:[A-Za-z0-9_.-]+$",
    "VITAL": r"^URN:VITAL:(BIRTH|MARRIAGE|DEATH):[0-9]{4}:[A-Z0-9_]+:[A-Za-z0-9_.-]+$",
    "CEM": r"^URN:CEM:[A-Z0-9_]+:[A-Za-z0-9_.-]+$",
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
URN_BASE_REGEX: re.Pattern[str] = re.compile(URN_BASE_PATTERN)
URN_REGEXES: dict[str, re.Pattern[str]] = {
    nid: re.compile(pattern) for nid, pattern in URN_PATTERNS.items()
}
