"""Path: src/gda/model/atom/geo.py

Geographic coordinate primitives using Pydantic dataclasses.

Operational Role:
    Defines validated geospatial atoms (Latitude, Longitude, Coordinates)
    for physical repository, civil jurisdiction, and site locations.

Architecture:
    - Latitude: Validated float bounded between -90.0 and +90.0.
    - Longitude: Validated float bounded between -180.0 and +180.0.
    - Coordinates: Combined geospatial pair with string rendering.
"""

from __future__ import annotations

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

from gda.core.errors import ModelRangeError
from gda.core.introspectable import IntrospectableMixin
from gda.core.logging import GDALogger

__version__ = "1.0.0+build.6"

_logger = GDALogger(__name__)


@dataclass(config=ConfigDict(frozen=True, extra="forbid"))
class Latitude(IntrospectableMixin):
    """Geographic latitude bounded strictly between -90.0 and +90.0 degrees."""

    value: float

    def __post_init__(self) -> None:
        if not (-90.0 <= self.value <= 90.0):
            err_msg = (
                f"Latitude {self.value} out of range. Must be between -90.0 and 90.0."
            )
            _logger.debug(
                "Latitude range boundary exceeded", details={"value": self.value}
            )
            raise ModelRangeError(err_msg, details={"value": self.value})

    def __float__(self) -> float:
        return self.value

    def __str__(self) -> str:
        return f"{self.value:.6f}"

    def __repr__(self) -> str:
        return f"Latitude(value={self.value})"


@dataclass(config=ConfigDict(frozen=True, extra="forbid"))
class Longitude(IntrospectableMixin):
    """Geographic longitude bounded strictly between -180.0 and +180.0 degrees."""

    value: float

    def __post_init__(self) -> None:
        if not (-180.0 <= self.value <= 180.0):
            err_msg = f"Longitude {self.value} out of range. Must be between -180.0 and 180.0."
            _logger.debug(
                "Longitude range boundary exceeded", details={"value": self.value}
            )
            raise ModelRangeError(err_msg, details={"value": self.value})

    def __float__(self) -> float:
        return self.value

    def __str__(self) -> str:
        return f"{self.value:.6f}"

    def __repr__(self) -> str:
        return f"Longitude(value={self.value})"


@dataclass(config=ConfigDict(frozen=True, extra="forbid"))
class Coordinates(IntrospectableMixin):
    """Immutable geospatial coordinate pair uniting Latitude and Longitude."""

    latitude: Latitude
    longitude: Longitude

    @property
    def formatted_coordinates(self) -> str:
        return f"{self.latitude}, {self.longitude}"

    def __str__(self) -> str:
        return self.formatted_coordinates

    def __repr__(self) -> str:
        return f"Coordinates(latitude={self.latitude!r}, longitude={self.longitude!r})"
