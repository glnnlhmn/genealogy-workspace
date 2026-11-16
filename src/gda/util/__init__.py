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

__version__ = "1.0.0+build.4"

__all__ = [
    "clean_string",  # text.py
    "clean_whitespace",  # text.py
    "extract_max_smart_id",  # ids.py
    "mint_smart_id",  # ids.py
    "mint_uuid",  # ids.py
    "normalize_ascii",  # text.py
    "parse_smart_id",  # ids.py
    "phonetic_nysiis",  # text.py
    "phonetic_soundex",  # text.py
    "slugify",  # text.py
    "verify_id",  # ids.py
]
