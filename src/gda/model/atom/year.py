"""Path: src/gda/model/atom/year.py

Core atomic calendar year primitives and lifecycle year subclasses.

Operational Role:
    Encapsulates validated, immutable historical calendar year values bounded
    strictly between MIN_HISTORICAL_YEAR and MAX_HISTORICAL_YEAR from gda.core.types.
    Enforces strict integer validation without silent coercion, supports raw integer
    equality, and provides cross-subclass total ordering across HistoricalYear instances.

Architecture:
    - HistoricalYear: Base integer year bounded strictly between 1000 and 2100.
    - BirthYear: Specialized HistoricalYear representing an individual's birth.
    - DeathYear: Specialized HistoricalYear representing an individual's death.
"""

from __future__ import annotations

from functools import total_ordering
from typing import Any, ClassVar

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.errors import ModelFormatError, ModelRangeError
from gda.core.introspectable import IntrospectableMixin
from gda.core.types import MAX_HISTORICAL_YEAR, MIN_HISTORICAL_YEAR

__version__ = "1.0.0+build.5"

__all__ = [
    "BirthYear",
    "DeathYear",
    "HistoricalYear",
]


@total_ordering
@dataclass(eq=False, repr=False, config=ConfigDict(frozen=True, extra="forbid", strict=True))
class HistoricalYear(IntrospectableMixin):
    """Historical calendar year bounded strictly between 1000 and 2100."""

    value: int = Field(..., description="Historical 4-digit calendar year.")

    MIN_YEAR: ClassVar[int] = MIN_HISTORICAL_YEAR
    MAX_YEAR: ClassVar[int] = MAX_HISTORICAL_YEAR

    def __post_init__(self) -> None:
        """Validate exact integer type and bounding invariants without silent coercion."""
        if type(self.value) is not int:
            raise ModelFormatError(
                f"Invalid {self.__class__.__name__} type: expected int, got {type(self.value).__name__}.",
                error_code="ERR_MODEL_FORMAT",
                details={"value": self.value},
            )

        if not (self.MIN_YEAR <= self.value <= self.MAX_YEAR):
            raise ModelRangeError(
                f"{self.__class__.__name__} '{self.value}' out of range. "
                f"Must be between {self.MIN_YEAR} and {self.MAX_YEAR}.",
                error_code="ERR_MODEL_RANGE",
                details={"value": self.value, "min": self.MIN_YEAR, "max": self.MAX_YEAR},
            )

    def __int__(self) -> int:
        return self.value

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(value={self.value})"

    def __eq__(self, other: Any) -> bool:
        """Support equality comparison with any HistoricalYear subclass or raw int (excluding bool)."""
        if isinstance(other, HistoricalYear):
            return self.value == other.value
        if type(other) is int:
            return self.value == other
        return False

    def __hash__(self) -> int:
        return hash(self.value)

    def __lt__(self, other: Any) -> bool:
        """Enforce total ordering strictly between HistoricalYear instances and subclasses."""
        if not isinstance(other, HistoricalYear):
            return NotImplemented
        return self.value < other.value


@dataclass(eq=False, repr=False, config=ConfigDict(frozen=True, extra="forbid", strict=True))
class BirthYear(HistoricalYear):
    """Specialized calendar year representing an individual's birth."""


@dataclass(eq=False, repr=False, config=ConfigDict(frozen=True, extra="forbid", strict=True))
class DeathYear(HistoricalYear):
    """Specialized calendar year representing an individual's death."""
