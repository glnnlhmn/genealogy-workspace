"""Path: src/gda/core/enums/coercion.py

Canonical Tier 0 enum coercion and token normalization utilities.

Operational Role:
    Provides a single, strict coercion pipeline (coerce_enum) for converting
    messy external inputs (CSV cells, CLI flags, JSON payloads) into validated
    GDA enum members while rejecting booleans, floats, None, empty strings,
    and unmapped tokens with structured ModelFormatError diagnostics.
"""

from __future__ import annotations

import re
from enum import Enum, IntEnum
from typing import Any

from gda.core.errors import ModelFormatError
from gda.core.types import is_strict_int

__version__ = "1.0.0+build.2"

__all__ = [
    "coerce_enum",
]

_SEPARATOR_RE = re.compile(r"[\s\-]+")


def _normalize_token(raw: str) -> str:
    """Normalize a string token by stripping whitespace and converting separators to UPPER_SNAKE_CASE."""
    return _SEPARATOR_RE.sub("_", raw.strip()).upper()


def _raise_coercion_error(
    enum_cls: type[Enum],
    raw_value: Any,
    field_name: str | None,
) -> ModelFormatError:
    """Construct a structured ModelFormatError for a failed enum coercion attempt."""
    target_label = f" for field '{field_name}'" if field_name else ""
    details: dict[str, Any] = {
        "enum": enum_cls.__name__,
        "raw_value": repr(raw_value),
        "raw_type": type(raw_value).__name__,
    }
    if field_name is not None:
        details["field_name"] = field_name

    return ModelFormatError(
        f"Invalid {enum_cls.__name__} value{target_label}: {raw_value!r}",
        details=details,
    )


def _match_by_name_or_value[E: Enum](enum_cls: type[E], normalized: str) -> E | None:
    """Resolve a normalized UPPER_SNAKE_CASE token against enum member names or string values."""
    # Fast path: exact match against canonical member name
    member = enum_cls.__members__.get(normalized)
    if member is not None:
        return member

    # Fallback: match against normalized string values for StrEnum / string-valued enums
    for candidate in enum_cls:
        if isinstance(candidate.value, str) and _normalize_token(candidate.value) == normalized:
            return candidate
    return None


def coerce_enum[E: Enum](
    enum_cls: type[E],
    raw_value: Any,
    *,
    field_name: str | None = None,
) -> E:
    """Coerce an external raw value into a validated member of enum_cls.

    Resolution order:
        1. Direct passthrough if raw_value is already an instance of enum_cls.
        2. Explicit rejection of bool, None, and non-(int|str) values.
        3. For IntEnum subclasses: strict int lookup, numeric string parsing,
           or normalized member-name lookup.
        4. For StrEnum / general Enum subclasses: exact value match, then
           case- and separator-normalized lookup against member names and values.

    Args:
        enum_cls: Target Enum subclass to resolve against.
        raw_value: External value (enum member, str, or int) to coerce.
        field_name: Optional domain field name included in error diagnostics.

    Returns:
        The resolved enum member of type E.

    Raises:
        ModelFormatError: If raw_value is an invalid type, empty/blank, or
            cannot be mapped to any member of enum_cls.
    """
    if isinstance(raw_value, enum_cls):
        return raw_value

    # Explicitly reject booleans before any int checks (bool subclasses int in Python)
    if isinstance(raw_value, bool) or raw_value is None:
        raise _raise_coercion_error(enum_cls, raw_value, field_name)

    if issubclass(enum_cls, IntEnum):
        if is_strict_int(raw_value):
            try:
                return enum_cls(raw_value)
            except ValueError as exc:
                raise _raise_coercion_error(enum_cls, raw_value, field_name) from exc

        if isinstance(raw_value, str):
            cleaned = raw_value.strip()
            if not cleaned:
                raise _raise_coercion_error(enum_cls, raw_value, field_name)

            # Attempt integer string parsing first (e.g., "3", " 1880 ")
            try:
                parsed_int = int(cleaned)
            except ValueError:
                parsed_int = None

            if parsed_int is not None:
                try:
                    return enum_cls(parsed_int)
                except ValueError as exc:
                    raise _raise_coercion_error(enum_cls, raw_value, field_name) from exc

            # Fall back to member name lookup (e.g., "direct_primary", "DIRECT-PRIMARY")
            int_matched = _match_by_name_or_value(enum_cls, _normalize_token(cleaned))
            if int_matched is not None:
                return int_matched

        raise _raise_coercion_error(enum_cls, raw_value, field_name)

    # StrEnum and general string-valued Enum path
    if not isinstance(raw_value, str):
        raise _raise_coercion_error(enum_cls, raw_value, field_name)

    cleaned = raw_value.strip()
    if not cleaned:
        raise _raise_coercion_error(enum_cls, raw_value, field_name)

    # Try exact stripped value match first, then normalized token match
    try:
        return enum_cls(cleaned)
    except ValueError:
        pass

    str_matched = _match_by_name_or_value(enum_cls, _normalize_token(cleaned))
    if str_matched is not None:
        return str_matched

    raise _raise_coercion_error(enum_cls, raw_value, field_name)
