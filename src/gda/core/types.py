"""Path: src/gda/core/types.py

Authoritative regex patterns, format tokens, and primitive scalar definitions.

Operational Role:
    Provides the code-first declarative repository for RFC 4122 UUIDv4 patterns,
    ISO 8601 date and timestamp directives, canonical entity identifier regex patterns,
    and SHA-256 hexadecimal hash patterns across the GDA core infrastructure.
"""

from __future__ import annotations

import re

__version__ = "1.0.0+build.1"

__all__ = [
    "ENTITY_ID_PATTERNS",
    "ISO_DATE_FMT",
    "ISO_DATE_PATTERN",
    "ISO_DATE_REGEX",
    "ISO_MONTH_FMT",
    "ISO_TIMESTAMP_FMT",
    "ISO_TIMESTAMP_PATTERN",
    "ISO_TIMESTAMP_REGEX",
    "ISO_YEAR_FMT",
    "SHA256_PATTERN",
    "SHA256_REGEX",
    "UUID_V4_PATTERN",
    "UUID_V4_REGEX",
]

# ------------------------------------------------------------------------------
# String Format Directives (strftime / strptime)
# ------------------------------------------------------------------------------
ISO_YEAR_FMT: str = "%Y"
ISO_MONTH_FMT: str = "%Y-%m"
ISO_DATE_FMT: str = "%Y-%m-%d"
ISO_TIMESTAMP_FMT: str = "%Y-%m-%dT%H:%M:%SZ"

# ------------------------------------------------------------------------------
# Structural Regex Patterns (from schemas/defs/_shared_defs.schema.json)
# ------------------------------------------------------------------------------
UUID_V4_PATTERN: str = r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
ISO_DATE_PATTERN: str = r"^\d{4}(-(0[1-9]|1[0-2])(-(0[1-9]|[12]\d|3[01]))?)?$"
ISO_TIMESTAMP_PATTERN: str = (
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?$"
)
SHA256_PATTERN: str = r"^[0-9a-f]{64}$"

ENTITY_ID_PATTERNS: dict[str, str] = {
    "IND": r"^IND-\d{5}$",
    "LOC": r"^LOC-\d{5}$",
    "SID": r"^SID-\d{5}$",
    "NOT": r"^NOT-\d{5}$",
    "REP": r"^REP-\d{5}$",
}

# ------------------------------------------------------------------------------
# Compiled Regular Expressions
# ------------------------------------------------------------------------------
UUID_V4_REGEX: re.Pattern[str] = re.compile(UUID_V4_PATTERN)
ISO_DATE_REGEX: re.Pattern[str] = re.compile(ISO_DATE_PATTERN)
ISO_TIMESTAMP_REGEX: re.Pattern[str] = re.compile(ISO_TIMESTAMP_PATTERN)
SHA256_REGEX: re.Pattern[str] = re.compile(SHA256_PATTERN)
