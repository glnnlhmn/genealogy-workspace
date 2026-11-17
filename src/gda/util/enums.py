"""Path: src/gda/util/enums.py

Generic controlled-vocabulary enumeration coercion utilities.

Operational Role:
    Provides a single centralized resolver (coerce_enum) for converting raw
    strings, integers, or existing Enum instances into strongly typed GDA
    StrEnum and IntEnum members across domain models and database mappers.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from gda.core.errors import ModelFormatError
from gda.core.types import ENUM_KEY_SEPARATOR_REGEX

__version__ = "1.0.0+build.3"

__all__ = [
    "coerce_enum",
]


def _match_string_enum[E: Enum](enum_cls: type[E], cleaned: str) -> E | None:
    """Resolve a trimmed string against an Enum's values, member names, or numeric values.

    Args:
        enum_cls: Target Enum class to search.
        cleaned: Trimmed non-empty string candidate.

    Returns:
        Matching Enum member if found, or None if no match exists.
    """
    # --- Step 1: Fast Exact Value Match ---
    try:
        return enum_cls(cleaned)
    except ValueError:
        pass

    # --- Step 2: Case-Insensitive Value Match & Member Name Match ---
    upper_candidate = cleaned.upper()
    normalized_name = ENUM_KEY_SEPARATOR_REGEX.sub("_", upper_candidate)

    for member in enum_cls:
        if isinstance(member.value, str) and member.value.upper() == upper_candidate:
            return member
        if member.name.upper() in (upper_candidate, normalized_name):
            return member

    # --- Step 3: Numeric String Fallback for IntEnum Classes ---
    if cleaned.isdigit():
        try:
            return enum_cls(int(cleaned))
        except ValueError:
            pass

    return None


def coerce_enum[E: Enum](
    enum_cls: type[E],
    raw: Any,
    *,
    field_name: str | None = None,
) -> E:
    """Coerce a raw value into a validated member of the specified Enum class.

    Supports direct Enum instances, exact or case-insensitive string values,
    member names (with spaces or hyphens normalized to underscores), and integer
    values or numeric strings for IntEnum subclasses.

    Args:
        enum_cls: Target Enum subclass to resolve against.
        raw: Candidate Enum member, string, or integer value.
        field_name: Optional field label included in diagnostic error details.

    Returns:
        Resolved member of enum_cls.

    Raises:
        ModelFormatError: If raw is a boolean, wrong type, empty string, or cannot
            be matched to any member of enum_cls.
    """
    target_label = field_name or enum_cls.__name__

    # Reject booleans explicitly since bool is a subclass of int in Python
    if isinstance(raw, bool):
        raise ModelFormatError(
            f"Invalid {target_label}: boolean '{raw}' is not a valid {enum_cls.__name__}.",
            error_code="ERR_MODEL_FORMAT",
            details={"field": target_label, "enum": enum_cls.__name__, "value": raw},
        )

    if isinstance(raw, enum_cls):
        return raw

    if isinstance(raw, int):
        try:
            return enum_cls(raw)
        except ValueError as err:
            raise ModelFormatError(
                f"Invalid {target_label}: '{raw}' is not a valid {enum_cls.__name__}.",
                error_code="ERR_MODEL_FORMAT",
                details={"field": target_label, "enum": enum_cls.__name__, "value": raw},
            ) from err

    if isinstance(raw, str):
        cleaned = raw.strip()
        matched = _match_string_enum(enum_cls, cleaned) if cleaned else None
        if matched is not None:
            return matched
        raise ModelFormatError(
            f"Invalid {target_label}: '{raw}' is not a valid {enum_cls.__name__}.",
            error_code="ERR_MODEL_FORMAT",
            details={"field": target_label, "enum": enum_cls.__name__, "value": raw},
        )

    raise ModelFormatError(
        f"Invalid {target_label}: expected {enum_cls.__name__} or str, got {type(raw).__name__}.",
        error_code="ERR_MODEL_FORMAT",
        details={"field": target_label, "enum": enum_cls.__name__, "value": repr(raw)},
    )
