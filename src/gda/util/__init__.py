"""Path: src/gda/util/__init__.py

Domain-specific helper utilities for identifiers, text sanitization, and phonetics.

Operational Role:
    Public export facade for high-level utility helpers:
    sequential smartID and UUIDv4 minting, decomposition, high-water mark sequence
    extraction, Unicode/ASCII sanitization, slugging, and historical phonetic encodings.
"""

from __future__ import annotations

from gda.util.ids import (
    extract_max_smart_id,
    mint_smart_id,
    mint_uuid,
    parse_smart_id,
    verify_id,
)
from gda.util.text import (
    clean_string,
    clean_whitespace,
    normalize_ascii,
    phonetic_nysiis,
    phonetic_soundex,
    slugify,
)

__version__ = "1.0.0+build.3"

__all__ = [
    "clean_string",
    "clean_whitespace",
    "extract_max_smart_id",
    "mint_smart_id",
    "mint_uuid",
    "normalize_ascii",
    "parse_smart_id",
    "phonetic_nysiis",
    "phonetic_soundex",
    "slugify",
    "verify_id",
]
