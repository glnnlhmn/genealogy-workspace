"""Path: src/gda/model/atom/gender.py

Biological sex and gender at birth atomic value object representation.

Operational Role:
    Defines the immutable atomic value object ('GenderAtom') representing
    biological sex or gender recorded at birth across historical vital records,
    censuses, and parish registers. Restricts canonical codes strictly to
    exact 'M' (Male), 'F' (Female), and 'U' (Undetermined/Unknown), providing
    strict validation, immutability, string equality, and homogeneous total ordering.
"""

from __future__ import annotations

from functools import total_ordering
from typing import Any, ClassVar

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.errors import ModelFormatError
from gda.core.introspectable import IntrospectableMixin
from gda.core.types import GENDER_CODES

__version__ = "1.0.0+build.7"

__all__ = ["GenderAtom"]


@total_ordering
@dataclass(config=ConfigDict(frozen=True, extra="forbid"))
class GenderAtom(IntrospectableMixin):
    """Immutable atomic representation of biological sex or gender recorded at birth."""

    value: str = Field(..., description="Canonical single-character code: 'M', 'F', or 'U'.")

    VALID_CODES: ClassVar[frozenset[str]] = GENDER_CODES

    def __post_init__(self) -> None:
        """Enforce strict membership within M, F, and U without silent mutation."""
        if self.value not in self.VALID_CODES:
            raise ModelFormatError(
                f"Invalid GenderAtom code: '{self.value}'. Must be exactly one of ('M', 'F', 'U').",
                details={"value": self.value, "valid_codes": sorted(self.VALID_CODES)},
            )

    @property
    def is_male(self) -> bool:
        """Return True if male."""
        return self.value == "M"

    @property
    def is_female(self) -> bool:
        """Return True if female."""
        return self.value == "F"

    @property
    def is_undetermined(self) -> bool:
        """Return True if unknown or unrecorded."""
        return self.value == "U"

    def __str__(self) -> str:
        """Return canonical single-character code."""
        return self.value

    def __repr__(self) -> str:
        """Return constructor representation."""
        return f"GenderAtom(value='{self.value}')"

    def __eq__(self, other: Any) -> bool:
        """Support equality comparison with another GenderAtom or raw string."""
        if type(other) is GenderAtom:
            return self.value == other.value
        if isinstance(other, str):
            return self.value == other
        return False

    def __hash__(self) -> int:
        """Return hash based on canonical string value."""
        return hash(self.value)

    def __lt__(self, other: Any) -> bool:
        """Support deterministic ordering strictly between GenderAtom instances."""
        if type(other) is not GenderAtom:
            return NotImplemented
        return self.value < other.value
