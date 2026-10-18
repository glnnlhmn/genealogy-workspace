"""Path: src/gda/model/base/address.py

Structured postal address representation using Pydantic dataclasses.

Operational Role:
    Defines the address representation ('Address') for physical sites,
    repositories, residences, and civil jurisdictions. Preserves street lines,
    postal codes, and binds optional geospatial Coordinates.

Architecture:
    - Address: Pydantic dataclass validating street address components.
"""

from __future__ import annotations

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

from gda.core.errors import ModelFormatError
from gda.core.introspectable import IntrospectableMixin
from gda.core.logging import GDALogger
from gda.model.atom.geo import Coordinates

__version__ = "1.0.0+build.5"

_logger = GDALogger(__name__)


@dataclass(config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True))
class Address(IntrospectableMixin):
    """Structured postal address capturing street lines, postal codes, and coordinates."""

    address_line_1: str
    address_line_2: str | None = None
    postal_code: str | None = None
    coordinates: Coordinates | None = None

    def __post_init__(self) -> None:
        if not self.address_line_1.strip():
            err_msg = "Address address_line_1 cannot be empty or whitespace."
            _logger.debug("Address address_line_1 validation failed")
            raise ModelFormatError(err_msg, details={"field": "address_line_1"})

    @property
    def formatted_address(self) -> str:
        parts: list[str] = [self.address_line_1]
        if self.address_line_2:
            parts.append(self.address_line_2)
        if self.postal_code:
            parts.append(self.postal_code)
        return ", ".join(parts)

    def __str__(self) -> str:
        return self.formatted_address

    def __repr__(self) -> str:
        return (
            f"Address(address_line_1='{self.address_line_1}', "
            f"address_line_2={self.address_line_2!r}, postal_code={self.postal_code!r}, "
            f"coordinates={self.coordinates!r})"
        )
