"""Path: src/gda/model/atom/date.py

Atomic date and timestamp primitives using Pydantic dataclasses.

Operational Role:
    Provides validated, immutable string atoms representing genealogical dates
    (DateString) and standardized ISO 8601 extended timestamps (IsoTimestamp).
    Enforces strict invariants without silent mutation, supports string equality,
    and provides homogeneous total ordering.
"""

from __future__ import annotations

import re
from functools import total_ordering
from typing import Any, ClassVar

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.errors import ModelFormatError
from gda.core.introspectable import IntrospectableMixin
from gda.core.types import ISO_TIMESTAMP_REGEX

__version__ = "1.0.0+build.3"

__all__ = [
    "DateString",
    "IsoTimestamp",
]


@total_ordering
@dataclass(config=ConfigDict(frozen=True, extra="forbid"))
class DateString(IntrospectableMixin):
    """Immutable textual genealogical date representation."""

    value: str = Field(..., description="Canonical textual date expression.")

    def __post_init__(self) -> None:
        """Enforce non-empty string and no unnormalized outer whitespace."""
        if not isinstance(self.value, str) or not self.value or self.value != self.value.strip():
            raise ModelFormatError(
                f"Invalid DateString: '{self.value}'. Must be a non-empty string without leading or trailing whitespace.",
                details={"value": self.value},
            )

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"DateString(value='{self.value}')"

    def __eq__(self, other: Any) -> bool:
        """Support equality comparison with another DateString or raw string."""
        if type(other) is DateString:
            return self.value == other.value
        if isinstance(other, str):
            return self.value == other
        return False

    def __hash__(self) -> int:
        return hash(self.value)

    def __lt__(self, other: Any) -> bool:
        """Support deterministic ordering strictly between DateString instances."""
        if type(other) is DateString:
            return self.value < other.value
        return NotImplemented


@total_ordering
@dataclass(config=ConfigDict(frozen=True, extra="forbid"))
class IsoTimestamp(IntrospectableMixin):
    """Standardized ISO 8601 extended timestamp representation."""

    value: str = Field(..., description="Canonical ISO 8601 extended timestamp string.")

    _PATTERN: ClassVar[re.Pattern[str]] = ISO_TIMESTAMP_REGEX

    def __post_init__(self) -> None:
        """Enforce exact ISO 8601 format without silent mutation."""
        if not isinstance(self.value, str) or not self._PATTERN.match(self.value):
            raise ModelFormatError(
                f"Invalid IsoTimestamp: '{self.value}'. Must match ISO 8601 extended format.",
                details={"value": self.value},
            )

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"IsoTimestamp(value='{self.value}')"

    def __eq__(self, other: Any) -> bool:
        """Support equality comparison with another IsoTimestamp or raw string."""
        if type(other) is IsoTimestamp:
            return self.value == other.value
        if isinstance(other, str):
            return self.value == other
        return False

    def __hash__(self) -> int:
        return hash(self.value)

    def __lt__(self, other: Any) -> bool:
        """Support deterministic chronological ordering strictly between IsoTimestamp instances."""
        if type(other) is IsoTimestamp:
            return self.value < other.value
        return NotImplemented
