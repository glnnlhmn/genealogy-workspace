"""Path: src/gda/core/types.py

Authoritative regex patterns, format tokens, and strict numeric type guards.

Operational Role:
    Provides the code-first declarative repository for RFC 4122 UUIDv4 patterns,
    ISO 8601 date and timestamp directives, canonical 6-digit entity identifier
    regex patterns, canonical entity lookup URN patterns, archival URN patterns
    across all documentary domains, SQL identifier patterns, enum key separator
    patterns, publication/news code patterns, SHA-256 hexadecimal hash patterns,
    and strict numeric guards (is_strict_int, is_finite_number).
"""

from __future__ import annotations

import math
import re
from types import MappingProxyType
from typing import Any

__version__ = "1.0.0+build.10"

__all__ = [
    "ATOM_ID_PATTERN",
    "ATOM_ID_REGEX",
    "ENTITY_ID_PATTERNS",
    "ENTITY_ID_REGEXES",
    "ENTITY_URN_PATTERNS",
    "ENTITY_URN_REGEXES",
    "ENUM_KEY_SEPARATOR_PATTERN",
    "ENUM_KEY_SEPARATOR_REGEX",
    "ISO_DATE_FMT",
    "ISO_DATE_PATTERN",
    "ISO_DATE_REGEX",
    "ISO_MONTH_FMT",
    "ISO_TIMESTAMP_FMT",
    "ISO_TIMESTAMP_PATTERN",
    "ISO_TIMESTAMP_REGEX",
    "ISO_YEAR_FMT",
    "NEWS_CATEGORY_PATTERN",
    "NEWS_CATEGORY_REGEX",
    "PUB_CODE_PATTERN",
    "PUB_CODE_REGEX",
    "SHA256_PATTERN",
    "SHA256_REGEX",
    "SQL_IDENTIFIER_PATTERN",
    "SQL_IDENTIFIER_REGEX",
    "URN_BASE_PATTERN",
    "URN_BASE_REGEX",
    "URN_PATTERNS",
    "URN_REGEXES",
    "UUID_V4_PATTERN",
    "UUID_V4_REGEX",
    "is_finite_number",
    "is_strict_int",
]

# ------------------------------------------------------------------------------
# 1. String Format Directives (strftime / strptime)
# ------------------------------------------------------------------------------
ISO_YEAR_FMT: str = "%Y"
ISO_MONTH_FMT: str = "%Y-%m"
ISO_DATE_FMT: str = "%Y-%m-%d"
ISO_TIMESTAMP_FMT: str = "%Y-%m-%dT%H:%M:%SZ"

# ------------------------------------------------------------------------------
# 2. UUIDv4 Pattern (Strict lowercase RFC 4122)
# ------------------------------------------------------------------------------
UUID_V4_PATTERN: str = r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
UUID_V4_REGEX: re.Pattern[str] = re.compile(UUID_V4_PATTERN)

# ------------------------------------------------------------------------------
# 3. ISO-8601 Temporal Patterns
# ------------------------------------------------------------------------------
# Matches YYYY, YYYY-MM (01-12), or YYYY-MM-DD (01-31)
ISO_DATE_PATTERN: str = r"^\d{4}(-(0[1-9]|1[0-2])(-(0[1-9]|[12]\d|3[01]))?)?$"
ISO_DATE_REGEX: re.Pattern[str] = re.compile(ISO_DATE_PATTERN)

# Matches full UTC or offset timestamps (YYYY-MM-DDTHH:MM:SS[.ffffff][Z|+HH:MM])
ISO_TIMESTAMP_PATTERN: str = (
    r"^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])T"
    r"([01]\d|2[0-3]):[0-5]\d:[0-5]\d(\.\d{1,6})?"
    r"(Z|[+-]([01]\d|2[0-3]):[0-5]\d)$"
)
ISO_TIMESTAMP_REGEX: re.Pattern[str] = re.compile(ISO_TIMESTAMP_PATTERN)

# ------------------------------------------------------------------------------
# 4. Canonical 6-Digit Entity Identifier Patterns
# ------------------------------------------------------------------------------
ATOM_ID_PATTERN: str = r"^[A-Z]{3}-\d{6}$"
ATOM_ID_REGEX: re.Pattern[str] = re.compile(ATOM_ID_PATTERN)

ENTITY_ID_PATTERNS: MappingProxyType[str, str] = MappingProxyType(
    {
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
)
ENTITY_ID_REGEXES: MappingProxyType[str, re.Pattern[str]] = MappingProxyType(
    {prefix: re.compile(pattern) for prefix, pattern in ENTITY_ID_PATTERNS.items()}
)

# ------------------------------------------------------------------------------
# 5. Canonical Entity Lookup URN Patterns (urn:gda:<domain>:<slug_segments>)
# ------------------------------------------------------------------------------
ENTITY_URN_PATTERNS: MappingProxyType[str, str] = MappingProxyType(
    {
        "IND": r"^urn:gda:ind:[a-z0-9_:-]+$",
        "FAM": r"^urn:gda:fam:[a-z0-9_:-]+$",
        "FID": r"^urn:gda:fact:[a-z0-9_:-]+$",
        "LOC": r"^urn:gda:loc:[a-z0-9_:-]+$",
        "ORG": r"^urn:gda:org:[a-z0-9_:-]+$",
        "SID": r"^urn:gda:site:[a-z0-9_:-]+$",
    }
)
ENTITY_URN_REGEXES: MappingProxyType[str, re.Pattern[str]] = MappingProxyType(
    {prefix: re.compile(pattern) for prefix, pattern in ENTITY_URN_PATTERNS.items()}
)

# ------------------------------------------------------------------------------
# 6. Publication, News Category, SQL Identifier, Enum Key & SHA-256 Patterns
# ------------------------------------------------------------------------------
PUB_CODE_PATTERN: str = r"^[A-Z0-9_-]{2,20}$"
PUB_CODE_REGEX: re.Pattern[str] = re.compile(PUB_CODE_PATTERN)

NEWS_CATEGORY_PATTERN: str = r"^[A-Z]{3,15}$"
NEWS_CATEGORY_REGEX: re.Pattern[str] = re.compile(NEWS_CATEGORY_PATTERN)

# Validates safe SQLite table and column identifiers to prevent SQL injection
SQL_IDENTIFIER_PATTERN: str = r"^[a-zA-Z_][a-zA-Z0-9_]*$"
SQL_IDENTIFIER_REGEX: re.Pattern[str] = re.compile(SQL_IDENTIFIER_PATTERN)

# Normalizes spaces, hyphens, and slashes into underscores for enum member lookup
ENUM_KEY_SEPARATOR_PATTERN: str = r"[\s\-/]+"
ENUM_KEY_SEPARATOR_REGEX: re.Pattern[str] = re.compile(ENUM_KEY_SEPARATOR_PATTERN)

# Strict 64-character lowercase hexadecimal SHA-256 digest
SHA256_PATTERN: str = r"^[0-9a-f]{64}$"
SHA256_REGEX: re.Pattern[str] = re.compile(SHA256_PATTERN)

# ------------------------------------------------------------------------------
# 7. Archival URN Patterns (URN:<NID>:<YEAR_OR_EVENT>:<JURISDICTION>:<LOCATOR>)
# ------------------------------------------------------------------------------
URN_BASE_PATTERN: str = r"^URN:[A-Z0-9_]+(:[A-Z0-9_.-]+)+$"
URN_BASE_REGEX: re.Pattern[str] = re.compile(URN_BASE_PATTERN)

URN_PATTERNS: MappingProxyType[str, str] = MappingProxyType(
    {
        "SRC": r"^URN:SRC:\d{4}:[A-Z0-9_]+:[A-Z0-9_.-]+$",
        "DRAFT": r"^URN:DRAFT:\d{4}:[A-Z0-9_]+:[A-Z0-9_.-]+$",
        "CENSUS": r"^URN:CENSUS:\d{4}:[A-Z0-9_]+:[A-Z0-9_.-]+$",
        "VITAL": r"^URN:VITAL:(BIRTH|MARRIAGE|DEATH):\d{4}:[A-Z0-9_]+:[A-Z0-9_.-]+$",
        "CEM": r"^URN:CEM:[A-Z0-9_]+:[A-Z0-9_.-]+$",
        "DIPLOMA": r"^URN:DIPLOMA:\d{4}:[A-Z0-9_]+:[A-Z0-9_.-]+$",
        "IMMIGRATION": r"^URN:IMMIGRATION:\d{4}:[A-Z0-9_]+:[A-Z0-9_.-]+$",
        "NATURALIZATION": r"^URN:NATURALIZATION:\d{4}:[A-Z0-9_]+:[A-Z0-9_.-]+$",
        "LAND": r"^URN:LAND:\d{4}:[A-Z0-9_]+:[A-Z0-9_.-]+$",
        "MS": r"^URN:MS:(\d{4}|UNDATED):[A-Z0-9_]+:[A-Z0-9_.-]+$",
        "BIBLE": r"^URN:BIBLE:(\d{4}|UNDATED):[A-Z0-9_]+:[A-Z0-9_.-]+$",
        "NARRATIVE": r"^URN:NARRATIVE:(\d{4}|UNDATED):[A-Z0-9_]+:[A-Z0-9_.-]+$",
        "OTHER": r"^URN:OTHER:(\d{4}|UNDATED):[A-Z0-9_]+:[A-Z0-9_.-]+$",
        "WILL": r"^URN:WILL:\d{4}:[A-Z0-9_]+:[A-Z0-9_.-]+$",
    }
)
URN_REGEXES: MappingProxyType[str, re.Pattern[str]] = MappingProxyType(
    {nid: re.compile(pattern) for nid, pattern in URN_PATTERNS.items()}
)


# ------------------------------------------------------------------------------
# 8. Strict Numeric Validation Guards
# ------------------------------------------------------------------------------
def is_strict_int(value: Any) -> bool:
    """Return True iff value is a true int and not a bool (bool subclasses int)."""
    return isinstance(value, int) and not isinstance(value, bool)


def is_finite_number(value: Any) -> bool:
    """Return True iff value is a non-bool int or a finite (non-NaN, non-Inf) float."""
    if isinstance(value, bool):
        return False
    if isinstance(value, int):
        return True
    if isinstance(value, float):
        return math.isfinite(value)
    return False
