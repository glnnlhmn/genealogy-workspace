"""Path: src/gda/model/atom/scalar.py

Domain scalar metrics and code primitives using Pydantic dataclasses.

Operational Role:
    Encapsulates validated discrete metrics, scores, and taxonomy code scalars
    including QuayScore, AhnentafelNumber, ConfidenceScore, PubCode, and
    NewsCategoryCode.

Architecture:
    - QuayScore: Validated integer evidentiary rating (0..3).
    - AhnentafelNumber: Positive integer genealogical lineage position (>= 1).
    - ConfidenceScore: Bounded float probability metric (0.0..1.0).
    - PubCode: Alphanumeric uppercase publisher/repository token code.
    - NewsCategoryCode: Standardized uppercase news clipping category code.
"""

from __future__ import annotations

import re
from typing import ClassVar

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

from gda.core.errors import ModelFormatError, ModelRangeError
from gda.core.introspectable import IntrospectableMixin
from gda.core.logging import GDALogger

__version__ = "1.0.0+build.6"

_logger = GDALogger(__name__)


@dataclass(config=ConfigDict(frozen=True, extra="forbid"))
class QuayScore(IntrospectableMixin):
    """Evidentiary certainty score bounded between 0 and 3."""

    value: int

    def __post_init__(self) -> None:
        if not (0 <= self.value <= 3):
            err_msg = f"QuayScore '{self.value}' out of range. Must be between 0 and 3."
            _logger.debug("QuayScore validation failed", details={"value": self.value})
            raise ModelRangeError(err_msg, details={"value": self.value})

    def __int__(self) -> int:
        return self.value

    def __repr__(self) -> str:
        return f"QuayScore(value={self.value})"


@dataclass(config=ConfigDict(frozen=True, extra="forbid"))
class AhnentafelNumber(IntrospectableMixin):
    """Genealogical ancestor calculation index bounded to positive integers (>= 1)."""

    value: int

    def __post_init__(self) -> None:
        if self.value < 1:
            err_msg = (
                f"AhnentafelNumber '{self.value}' must be a positive integer >= 1."
            )
            _logger.debug(
                "AhnentafelNumber validation failed", details={"value": self.value}
            )
            raise ModelRangeError(err_msg, details={"value": self.value})

    @property
    def is_male(self) -> bool | None:
        if self.value == 1:
            return None
        return (self.value % 2) == 0

    @property
    def is_female(self) -> bool | None:
        if self.value == 1:
            return None
        return (self.value % 2) != 0

    @property
    def father_index(self) -> int:
        return self.value * 2

    @property
    def mother_index(self) -> int:
        return (self.value * 2) + 1

    @property
    def child_index(self) -> int | None:
        if self.value == 1:
            return None
        return self.value // 2

    def __int__(self) -> int:
        return self.value

    def __repr__(self) -> str:
        return f"AhnentafelNumber(value={self.value})"


@dataclass(config=ConfigDict(frozen=True, extra="forbid"))
class ConfidenceScore(IntrospectableMixin):
    """Algorithmic confidence probability bounded between 0.0 and 1.0."""

    value: float

    def __post_init__(self) -> None:
        if not (0.0 <= self.value <= 1.0):
            err_msg = f"ConfidenceScore '{self.value}' out of range. Must be between 0.0 and 1.0."
            _logger.debug(
                "ConfidenceScore validation failed", details={"value": self.value}
            )
            raise ModelRangeError(err_msg, details={"value": self.value})

    def __float__(self) -> float:
        return self.value

    def __repr__(self) -> str:
        return f"ConfidenceScore(value={self.value})"


@dataclass(config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True))
class PubCode(IntrospectableMixin):
    """Standardized uppercase publisher or archive repository classification code."""

    value: str

    _PATTERN: ClassVar[re.Pattern[str]] = re.compile(r"^[A-Z0-9_-]{2,20}$")

    def __post_init__(self) -> None:
        if not self._PATTERN.match(self.value):
            err_msg = f"Invalid PubCode format: '{self.value}'. Must match '^[A-Z0-9_-]{{2,20}}$'."
            _logger.debug("PubCode validation failed", details={"value": self.value})
            raise ModelFormatError(err_msg, details={"value": self.value})

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"PubCode(value='{self.value}')"


@dataclass(config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True))
class NewsCategoryCode(IntrospectableMixin):
    """Standardized uppercase newspaper clipping topic category code."""

    value: str

    _PATTERN: ClassVar[re.Pattern[str]] = re.compile(r"^[A-Z]{3,15}$")

    def __post_init__(self) -> None:
        if not self._PATTERN.match(self.value):
            err_msg = f"Invalid NewsCategoryCode format: '{self.value}'. Must match '^[A-Z]{{3,15}}$'."
            _logger.debug(
                "NewsCategoryCode validation failed", details={"value": self.value}
            )
            raise ModelFormatError(err_msg, details={"value": self.value})

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"NewsCategoryCode(value='{self.value}')"
