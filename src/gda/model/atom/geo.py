"""Path: src/gda/model/atom/geo.py

Geographic coordinate scalar primitives using Pydantic dataclasses.

Operational Role:
    Defines validated geospatial scalar atoms (Latitude, Longitude) for physical
    repository, civil jurisdiction, and site locations. Enforces strict boundary
    ranges from gda.core.types, rejects booleans and strings, normalizes ints to
    floats, supports raw float equality, and provides homogeneous total ordering.
"""

from __future__ import annotations

from functools import total_ordering
from typing import Any, ClassVar

from pydantic import ConfigDict, Field, field_validator
from pydantic.dataclasses import dataclass

from gda.core.constants import MAX_LATITUDE, MAX_LONGITUDE, MIN_LATITUDE, MIN_LONGITUDE
from gda.core.errors import ModelFormatError, ModelRangeError
from gda.core.introspectable import IntrospectableMixin

__version__ = "1.0.0+build.9"

__all__ = [
    "Latitude",
    "Longitude",
]


@total_ordering
@dataclass(config=ConfigDict(frozen=True, extra="forbid"))
class Latitude(IntrospectableMixin):
    """Geographic latitude bounded strictly between -90.0 and +90.0 degrees."""

    value: float = Field(..., description="WGS 84 latitude in decimal degrees.")

    MIN_VAL: ClassVar[float] = MIN_LATITUDE
    MAX_VAL: ClassVar[float] = MAX_LATITUDE

    @field_validator("value", mode="before")
    @classmethod
    def _validate_numeric_type(cls, v: Any) -> float:
        """Reject booleans, strings, and non-numeric types before Pydantic coercion."""
        if type(v) not in (float, int) or type(v) is bool:
            raise ModelFormatError(
                f"Invalid Latitude type: expected float, got {type(v).__name__}.",
                error_code="ERR_MODEL_FORMAT",
                details={"value": v},
            )
        return float(v)

    def __post_init__(self) -> None:
        """Validate geographic latitude range boundaries."""
        if not (self.MIN_VAL <= self.value <= self.MAX_VAL):
            raise ModelRangeError(
                f"Latitude '{self.value}' out of range. Must be between {self.MIN_VAL} and {self.MAX_VAL}.",
                error_code="ERR_MODEL_RANGE",
                details={"value": self.value, "min": self.MIN_VAL, "max": self.MAX_VAL},
            )

    def __float__(self) -> float:
        return self.value

    def __str__(self) -> str:
        return f"{self.value:.6f}"

    def __repr__(self) -> str:
        return f"Latitude(value={self.value})"

    def __eq__(self, other: Any) -> bool:
        """Support equality comparison with Latitude or raw float/int (excluding bool)."""
        if type(other) is Latitude:
            return self.value == other.value
        if type(other) in (float, int) and type(other) is not bool:
            return self.value == float(other)
        return False

    def __hash__(self) -> int:
        return hash(self.value)

    def __lt__(self, other: Any) -> bool:
        """Enforce homogeneous ordering strictly between Latitude instances."""
        if type(other) is not Latitude:
            return NotImplemented
        return self.value < other.value


@total_ordering
@dataclass(config=ConfigDict(frozen=True, extra="forbid"))
class Longitude(IntrospectableMixin):
    """Geographic longitude bounded strictly between -180.0 and +180.0 degrees."""

    value: float = Field(..., description="WGS 84 longitude in decimal degrees.")

    MIN_VAL: ClassVar[float] = MIN_LONGITUDE
    MAX_VAL: ClassVar[float] = MAX_LONGITUDE

    @field_validator("value", mode="before")
    @classmethod
    def _validate_numeric_type(cls, v: Any) -> float:
        """Reject booleans, strings, and non-numeric types before Pydantic coercion."""
        if type(v) not in (float, int) or type(v) is bool:
            raise ModelFormatError(
                f"Invalid Longitude type: expected float, got {type(v).__name__}.",
                error_code="ERR_MODEL_FORMAT",
                details={"value": v},
            )
        return float(v)

    def __post_init__(self) -> None:
        """Validate geographic longitude range boundaries."""
        if not (self.MIN_VAL <= self.value <= self.MAX_VAL):
            raise ModelRangeError(
                f"Longitude '{self.value}' out of range. Must be between {self.MIN_VAL} and {self.MAX_VAL}.",
                error_code="ERR_MODEL_RANGE",
                details={"value": self.value, "min": self.MIN_VAL, "max": self.MAX_VAL},
            )

    def __float__(self) -> float:
        return self.value

    def __str__(self) -> str:
        return f"{self.value:.6f}"

    def __repr__(self) -> str:
        return f"Longitude(value={self.value})"

    def __eq__(self, other: Any) -> bool:
        """Support equality comparison with Longitude or raw float/int (excluding bool)."""
        if type(other) is Longitude:
            return self.value == other.value
        if type(other) in (float, int) and type(other) is not bool:
            return self.value == float(other)
        return False

    def __hash__(self) -> int:
        return hash(self.value)

    def __lt__(self, other: Any) -> bool:
        """Enforce homogeneous ordering strictly between Longitude instances."""
        if type(other) is not Longitude:
            return NotImplemented
        return self.value < other.value
