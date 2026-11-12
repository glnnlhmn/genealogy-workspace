"""Path: src/gda/model/base/age.py

Age record representation using Pydantic dataclasses.

Operational Role:
    Defines the structured age representation ('Age') recorded at the time
    of an event across vital certificates, census returns, and mortuary markers.
    Preserves verbatim text while parsing discrete years, months, and days.

Architecture:
    - Age: Strict immutable Pydantic dataclass validating event age assertions.
"""

from __future__ import annotations

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

from gda.core.errors import ModelFormatError
from gda.core.introspectable import IntrospectableMixin
from gda.core.logging import GDALogger

__version__ = "1.1.0+build.1"

__all__ = ["Age"]

_logger = GDALogger(__name__)


@dataclass(repr=False, config=ConfigDict(frozen=True, extra="forbid", strict=True))
class Age(IntrospectableMixin):
    """Event age assertion capturing discrete units and verbatim historical strings."""

    raw_text: str | None = None
    years: int | None = None
    months: int | None = None
    days: int | None = None

    def __post_init__(self) -> None:
        has_text = self.raw_text is not None and bool(self.raw_text.strip())
        has_numeric = self.years is not None or self.months is not None or self.days is not None

        if not has_text and not has_numeric:
            err_msg = "Age must specify raw_text or at least one of (years, months, days)."
            _logger.debug("Age validation failed: empty record")
            raise ModelFormatError(err_msg, details={"record": repr(self)})

        if self.years is not None and self.years < 0:
            raise ModelFormatError(
                f"Age years '{self.years}' cannot be negative.",
                details={"years": self.years},
            )

        if self.months is not None and not (0 <= self.months <= 11):
            raise ModelFormatError(
                f"Age months '{self.months}' must be between 0 and 11.",
                details={"months": self.months},
            )

        if self.days is not None and not (0 <= self.days <= 31):
            raise ModelFormatError(
                f"Age days '{self.days}' must be between 0 and 31.",
                details={"days": self.days},
            )

    @property
    def formatted_age(self) -> str:
        """Render normalized unit shorthand or fallback to verbatim text."""
        parts: list[str] = []
        if self.years is not None:
            parts.append(f"{self.years}y")
        if self.months is not None:
            parts.append(f"{self.months}m")
        if self.days is not None:
            parts.append(f"{self.days}d")

        if parts:
            return " ".join(parts)
        return self.raw_text.strip() if self.raw_text is not None else ""

    def __str__(self) -> str:
        return self.formatted_age

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(raw_text={self.raw_text!r}, "
            f"years={self.years}, months={self.months}, days={self.days})"
        )
