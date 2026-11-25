"""Path: src/gda/core/enums/base.py

Tier 0 base classes for all GDA string and integer enumerations.

Operational Role:
    Defines GDAStrEnum and GDAIntEnum, preserving Python's strict direct
    construction semantics (and Pydantic V2 compatibility) while furnishing
    standardized .from_raw() coercion and .values() introspection classmethods.
"""

from __future__ import annotations

from enum import IntEnum, StrEnum
from typing import Any, Self

from gda.core.enums.coercion import coerce_enum

__version__ = "1.0.0+build.1"

__all__ = [
    "GDAIntEnum",
    "GDAStrEnum",
]


class GDAStrEnum(StrEnum):
    """Base class for all GDA string-valued enumerations.

    Preserves strict StrEnum direct construction while exposing lenient
    .from_raw() coercion and .values() tuple introspection.
    """

    @classmethod
    def from_raw(cls, raw_value: Any, *, field_name: str | None = None) -> Self:
        """Coerce a raw external value into a validated member of this enum.

        Args:
            raw_value: External value (enum member or string token) to coerce.
            field_name: Optional field name for structured error diagnostics.

        Returns:
            Validated enum member.

        Raises:
            ModelFormatError: If raw_value cannot be coerced to a valid member.
        """
        return coerce_enum(cls, raw_value, field_name=field_name)

    @classmethod
    def values(cls) -> tuple[str, ...]:
        """Return an immutable tuple of all canonical string values in declaration order."""
        return tuple(member.value for member in cls)


class GDAIntEnum(IntEnum):
    """Base class for all GDA integer-valued enumerations.

    Preserves strict IntEnum direct construction while exposing lenient
    .from_raw() coercion (with strict bool rejection) and .values() introspection.
    """

    @classmethod
    def from_raw(cls, raw_value: Any, *, field_name: str | None = None) -> Self:
        """Coerce a raw external value into a validated member of this enum.

        Args:
            raw_value: External value (enum member, int, or string) to coerce.
            field_name: Optional field name for structured error diagnostics.

        Returns:
            Validated enum member.

        Raises:
            ModelFormatError: If raw_value is a bool, invalid type, or unmapped value.
        """
        return coerce_enum(cls, raw_value, field_name=field_name)

    @classmethod
    def values(cls) -> tuple[int, ...]:
        """Return an immutable tuple of all canonical integer values in declaration order."""
        return tuple(member.value for member in cls)
