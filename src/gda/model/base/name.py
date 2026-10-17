# Name: name.py
# Path: src/gda/model/base/name.py

"""Canonical personal name model using Pydantic dataclasses.

Operational Role:
    Defines the structured personal name representation ('CanonicalNameModel')
    for individuals across the Genealogy Digital Archive (GDA). Preserves
    verbatim raw names while breaking down given, middle, surname, suffix,
    and maiden names.

Architecture:
    - CanonicalNameModel: Pydantic dataclass validating personal name segments.
"""

from __future__ import annotations

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

from gda.core.introspectable import IntrospectableMixin
from gda.core.logging import GDALogger
from gda.model.atom.errors import AtomFormatError

__version__ = "1.0.0+build.r4"

_logger = GDALogger(__name__)


@dataclass(config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True))
class CanonicalNameModel(IntrospectableMixin):
    """Structured personal name model preserving verbatim string and parsed components."""

    raw_name: str
    given: str | None = None
    middle: str | None = None
    surname: str | None = None
    suffix: str | None = None
    maiden_name: str | None = None

    def __post_init__(self) -> None:
        if not self.raw_name.strip():
            err_msg = "CanonicalNameModel raw_name cannot be empty or whitespace."
            _logger.debug("CanonicalNameModel raw_name validation failed")
            raise AtomFormatError(err_msg, details={"raw_name": self.raw_name})

    @property
    def full_name(self) -> str:
        parts: list[str] = []
        if self.given:
            parts.append(self.given)
        if self.middle:
            parts.append(self.middle)
        if self.surname:
            parts.append(self.surname)
        if self.suffix:
            parts.append(self.suffix)

        if parts:
            return " ".join(parts)
        return self.raw_name

    def __str__(self) -> str:
        return self.full_name

    def __repr__(self) -> str:
        return (
            f"CanonicalNameModel(raw_name='{self.raw_name}', given={self.given!r}, "
            f"middle={self.middle!r}, surname={self.surname!r}, "
            f"suffix={self.suffix!r}, maiden_name={self.maiden_name!r})"
        )
