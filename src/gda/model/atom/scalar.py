"""Path: src/gda/model/atom/scalar.py

Domain scalar metrics and code primitives using Pydantic dataclasses.

Operational Role:
    Encapsulates validated discrete metrics, scores, and taxonomy code scalars
    including QuayScore, AhnentafelNumber, ConfidenceScore, PubCode, and
    NewsCategoryCode. Enforces strict typing and range/pattern invariants from
    gda.core.types without silent mutation, supports raw primitive equality,
    and provides homogeneous total ordering.

Architecture:
    - QuayScore: Validated integer evidentiary rating (0..3).
    - AhnentafelNumber: Positive integer genealogical lineage position (>= 1).
    - ConfidenceScore: Bounded float probability metric (0.0..1.0).
    - PubCode: Alphanumeric uppercase publisher/repository token code.
    - NewsCategoryCode: Standardized uppercase news clipping category code.
"""

from __future__ import annotations

import re
from functools import total_ordering
from typing import Any, ClassVar

from pydantic import ConfigDict, Field, field_validator
from pydantic.dataclasses import dataclass

from gda.core.constants import (
    MAX_CONFIDENCE_SCORE,
    MAX_QUAY_SCORE,
    MIN_AHNENTAFEL,
    MIN_CONFIDENCE_SCORE,
    MIN_QUAY_SCORE,
)
from gda.core.errors import ModelFormatError, ModelRangeError
from gda.core.introspectable import IntrospectableMixin
from gda.core.types import NEWS_CATEGORY_REGEX, PUB_CODE_REGEX

__version__ = "1.0.0+build.8"

__all__ = [
    "AhnentafelNumber",
    "ConfidenceScore",
    "NewsCategoryCode",
    "PubCode",
    "QuayScore",
]


@total_ordering
@dataclass(config=ConfigDict(frozen=True, extra="forbid", strict=True))
class QuayScore(IntrospectableMixin):
    """Evidentiary certainty score bounded between 0 and 3."""

    value: int = Field(..., description="GEDCOM QUAY evidentiary certainty rating (0..3).")

    MIN_VAL: ClassVar[int] = MIN_QUAY_SCORE
    MAX_VAL: ClassVar[int] = MAX_QUAY_SCORE

    def __post_init__(self) -> None:
        """Validate exact integer type and range boundaries without silent coercion."""
        if type(self.value) is not int:
            raise ModelFormatError(
                f"Invalid QuayScore type: expected int, got {type(self.value).__name__}.",
                error_code="ERR_MODEL_FORMAT",
                details={"value": self.value},
            )

        if not (self.MIN_VAL <= self.value <= self.MAX_VAL):
            raise ModelRangeError(
                f"QuayScore '{self.value}' out of range. Must be between {self.MIN_VAL} and {self.MAX_VAL}.",
                error_code="ERR_MODEL_RANGE",
                details={"value": self.value, "min": self.MIN_VAL, "max": self.MAX_VAL},
            )

    def __int__(self) -> int:
        return self.value

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        return f"QuayScore(value={self.value})"

    def __eq__(self, other: Any) -> bool:
        """Support equality comparison with QuayScore or raw int (excluding bool)."""
        if type(other) is QuayScore:
            return self.value == other.value
        if type(other) is int:
            return self.value == other
        return False

    def __hash__(self) -> int:
        return hash(self.value)

    def __lt__(self, other: Any) -> bool:
        """Enforce homogeneous ordering strictly between QuayScore instances."""
        if type(other) is not QuayScore:
            return NotImplemented
        return self.value < other.value


@total_ordering
@dataclass(config=ConfigDict(frozen=True, extra="forbid", strict=True))
class AhnentafelNumber(IntrospectableMixin):
    """Genealogical ancestor calculation index bounded to positive integers (>= 1)."""

    value: int = Field(..., description="Positive integer Ahnentafel lineage number (>= 1).")

    MIN_VAL: ClassVar[int] = MIN_AHNENTAFEL

    def __post_init__(self) -> None:
        """Validate exact positive integer type without silent coercion."""
        if type(self.value) is not int:
            raise ModelFormatError(
                f"Invalid AhnentafelNumber type: expected int, got {type(self.value).__name__}.",
                error_code="ERR_MODEL_FORMAT",
                details={"value": self.value},
            )

        if self.value < self.MIN_VAL:
            raise ModelRangeError(
                f"AhnentafelNumber '{self.value}' must be a positive integer >= {self.MIN_VAL}.",
                error_code="ERR_MODEL_RANGE",
                details={"value": self.value, "min": self.MIN_VAL},
            )

    @property
    def is_male(self) -> bool | None:
        """Return True for male ancestors (even > 1), False for female (odd > 1), None for proband (1)."""
        if self.value == 1:
            return None
        return (self.value % 2) == 0

    @property
    def is_female(self) -> bool | None:
        """Return True for female ancestors (odd > 1), False for male (even > 1), None for proband (1)."""
        if self.value == 1:
            return None
        return (self.value % 2) != 0

    @property
    def father_index(self) -> int:
        """Return Ahnentafel index of the father (2n)."""
        return self.value * 2

    @property
    def mother_index(self) -> int:
        """Return Ahnentafel index of the mother (2n + 1)."""
        return (self.value * 2) + 1

    @property
    def child_index(self) -> int | None:
        """Return Ahnentafel index of the child (n // 2), or None for proband (1)."""
        if self.value == 1:
            return None
        return self.value // 2

    def __int__(self) -> int:
        return self.value

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        return f"AhnentafelNumber(value={self.value})"

    def __eq__(self, other: Any) -> bool:
        """Support equality comparison with AhnentafelNumber or raw int (excluding bool)."""
        if type(other) is AhnentafelNumber:
            return self.value == other.value
        if type(other) is int:
            return self.value == other
        return False

    def __hash__(self) -> int:
        return hash(self.value)

    def __lt__(self, other: Any) -> bool:
        """Enforce homogeneous ordering strictly between AhnentafelNumber instances."""
        if type(other) is not AhnentafelNumber:
            return NotImplemented
        return self.value < other.value


@total_ordering
@dataclass(config=ConfigDict(frozen=True, extra="forbid"))
class ConfidenceScore(IntrospectableMixin):
    """Algorithmic confidence probability bounded between 0.0 and 1.0."""

    value: float = Field(..., description="Normalized probability metric (0.0..1.0).")

    MIN_VAL: ClassVar[float] = MIN_CONFIDENCE_SCORE
    MAX_VAL: ClassVar[float] = MAX_CONFIDENCE_SCORE

    @field_validator("value", mode="before")
    @classmethod
    def _validate_numeric_type(cls, v: Any) -> float:
        """Reject booleans, strings, and non-numeric types before Pydantic coercion."""
        if type(v) not in (float, int) or type(v) is bool:
            raise ModelFormatError(
                f"Invalid ConfidenceScore type: expected float, got {type(v).__name__}.",
                error_code="ERR_MODEL_FORMAT",
                details={"value": v},
            )
        return float(v)

    def __post_init__(self) -> None:
        """Validate range boundaries."""
        if not (self.MIN_VAL <= self.value <= self.MAX_VAL):
            raise ModelRangeError(
                f"ConfidenceScore '{self.value}' out of range. Must be between {self.MIN_VAL} and {self.MAX_VAL}.",
                error_code="ERR_MODEL_RANGE",
                details={"value": self.value, "min": self.MIN_VAL, "max": self.MAX_VAL},
            )

    def __float__(self) -> float:
        return self.value

    def __str__(self) -> str:
        return f"{self.value:.4f}"

    def __repr__(self) -> str:
        return f"ConfidenceScore(value={self.value})"

    def __eq__(self, other: Any) -> bool:
        """Support equality comparison with ConfidenceScore or raw float/int (excluding bool)."""
        if type(other) is ConfidenceScore:
            return self.value == other.value
        if type(other) in (float, int) and type(other) is not bool:
            return self.value == float(other)
        return False

    def __hash__(self) -> int:
        return hash(self.value)

    def __lt__(self, other: Any) -> bool:
        """Enforce homogeneous ordering strictly between ConfidenceScore instances."""
        if type(other) is not ConfidenceScore:
            return NotImplemented
        return self.value < other.value


@total_ordering
@dataclass(config=ConfigDict(frozen=True, extra="forbid", strict=True))
class PubCode(IntrospectableMixin):
    """Standardized uppercase publisher or archive repository classification code."""

    value: str = Field(
        ..., description="Uppercase alphanumeric/underscore/hyphen token (2..20 chars)."
    )

    _PATTERN: ClassVar[re.Pattern[str]] = PUB_CODE_REGEX

    def __post_init__(self) -> None:
        """Enforce exact PubCode pattern without silent whitespace stripping."""
        if not isinstance(self.value, str) or not self._PATTERN.match(self.value):
            raise ModelFormatError(
                f"Invalid PubCode format: '{self.value}'. Must match '^[A-Z0-9_-]{{2,20}}$' without whitespace.",
                error_code="ERR_MODEL_FORMAT",
                details={"value": self.value},
            )

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"PubCode(value='{self.value}')"

    def __eq__(self, other: Any) -> bool:
        """Support equality comparison with PubCode or raw str."""
        if type(other) is PubCode:
            return self.value == other.value
        if isinstance(other, str):
            return self.value == other
        return False

    def __hash__(self) -> int:
        return hash(self.value)

    def __lt__(self, other: Any) -> bool:
        """Enforce homogeneous ordering strictly between PubCode instances."""
        if type(other) is not PubCode:
            return NotImplemented
        return self.value < other.value


@total_ordering
@dataclass(config=ConfigDict(frozen=True, extra="forbid", strict=True))
class NewsCategoryCode(IntrospectableMixin):
    """Standardized uppercase newspaper clipping topic category code."""

    value: str = Field(..., description="Uppercase alphabetic topic category token (3..15 chars).")

    _PATTERN: ClassVar[re.Pattern[str]] = NEWS_CATEGORY_REGEX

    def __post_init__(self) -> None:
        """Enforce exact NewsCategoryCode pattern without silent whitespace stripping."""
        if not isinstance(self.value, str) or not self._PATTERN.match(self.value):
            raise ModelFormatError(
                f"Invalid NewsCategoryCode format: '{self.value}'. Must match '^[A-Z]{{3,15}}$' without whitespace.",
                error_code="ERR_MODEL_FORMAT",
                details={"value": self.value},
            )

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"NewsCategoryCode(value='{self.value}')"

    def __eq__(self, other: Any) -> bool:
        """Support equality comparison with NewsCategoryCode or raw str."""
        if type(other) is NewsCategoryCode:
            return self.value == other.value
        if isinstance(other, str):
            return self.value == other
        return False

    def __hash__(self) -> int:
        return hash(self.value)

    def __lt__(self, other: Any) -> bool:
        """Enforce homogeneous ordering strictly between NewsCategoryCode instances."""
        if type(other) is not NewsCategoryCode:
            return NotImplemented
        return self.value < other.value
