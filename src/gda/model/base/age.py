# Name: age.py
# Path: src/gda/model/base/age.py

"""Age record representation model using Pydantic dataclasses.

Operational Role:
    Defines the structured age representation ('AgeRecordModel') recorded
    at the time of an event across vital certificates, census returns,
    and mortuary markers in the Genealogy Digital Archive (GDA). Preserves
    verbatim text while parsing discrete years, months, and days.

Architecture:
    - AgeRecordModel: Pydantic dataclass validating event age assertions.
"""

from __future__ import annotations

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

from gda.core.introspectable import IntrospectableMixin
from gda.core.logging import GDALogger
from gda.model.atom.errors import AtomFormatError

__version__ = "1.0.0+build.r2"

_logger = GDALogger(__name__)


@dataclass(config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True))
class AgeRecordModel(IntrospectableMixin):
    """Event age assertion capturing discrete units and verbatim historical strings."""

    raw_text: str | None = None
    years: int | None = None
    months: int | None = None
    days: int | None = None

    def __post_init__(self) -> None:
        has_text = self.raw_text is not None and bool(self.raw_text.strip())
        has_numeric = (
            self.years is not None or self.months is not None or self.days is not None
        )

        if not has_text and not has_numeric:
            err_msg = "AgeRecordModel must specify raw_text or at least one of (years, months, days)."
            _logger.debug("AgeRecordModel validation failed: empty record")
            raise AtomFormatError(err_msg, details={"record": repr(self)})

        if self.years is not None and self.years < 0:
            raise AtomFormatError(
                f"Age years '{self.years}' cannot be negative.",
                details={"years": self.years},
            )

        if self.months is not None and not (0 <= self.months <= 11):
            raise AtomFormatError(
                f"Age months '{self.months}' must be between 0 and 11.",
                details={"months": self.months},
            )

        if self.days is not None and not (0 <= self.days <= 31):
            raise AtomFormatError(
                f"Age days '{self.days}' must be between 0 and 31.",
                details={"days": self.days},
            )

    @property
    def formatted_age(self) -> str:
        parts: list[str] = []
        if self.years is not None:
            parts.append(f"{self.years}y")
        if self.months is not None:
            parts.append(f"{self.months}m")
        if self.days is not None:
            parts.append(f"{self.days}d")

        if parts:
            return " ".join(parts)
        assert self.raw_text is not None
        return self.raw_text

    def __str__(self) -> str:
        return self.formatted_age

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(raw_text={self.raw_text!r}, "
            f"years={self.years}, months={self.months}, days={self.days})"
        )
