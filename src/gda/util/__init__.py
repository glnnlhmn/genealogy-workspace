"""Path: src/gda/util/__init__.py

Stateless utility functions for identifier management, enum coercion, and text processing.

Operational Role:
    Public package facade for gda.util, re-exporting pure helper functions from
    gda.util.enums, gda.util.ids, and gda.util.text.
"""

from __future__ import annotations

from gda.util.enums import coerce_enum
from gda.util.ids import (
    extract_max_smart_id,
    mint_smart_id,
    mint_uuid,
    normalize_id,
    parse_smart_id,
    resolve_polymorphic_id,
    unwrap_bool_int,
    unwrap_int,
    unwrap_value,
    verify_id,
)
from gda.util.text import (
    clean_string,
    clean_unique_strings,
    clean_whitespace,
    normalize_ascii,
    phonetic_nysiis,
    phonetic_soundex,
    require_non_empty,
    slugify,
)

__version__ = "1.0.0+build.5"

__all__ = [
    "clean_string",
    "clean_unique_strings",
    "clean_whitespace",
    "coerce_enum",
    "extract_max_smart_id",
    "mint_smart_id",
    "mint_uuid",
    "normalize_ascii",
    "normalize_id",
    "parse_smart_id",
    "phonetic_nysiis",
    "phonetic_soundex",
    "require_non_empty",
    "resolve_polymorphic_id",
    "slugify",
    "unwrap_bool_int",
    "unwrap_int",
    "unwrap_value",
    "verify_id",
]
