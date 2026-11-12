"""Path: src/gda/model/base/geo.py

Composite geospatial coordinate base structures.

Operational Role:
    Defines the immutable composite coordinate pair ('Coordinates') uniting
    validated Latitude and Longitude atoms for physical sites, repositories,
    and civil jurisdictions across the GDA domain model.
"""

from __future__ import annotations

import json
from typing import Any

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.errors import ModelFormatError
from gda.core.introspectable import IntrospectableMixin
from gda.model.atom.geo import Latitude, Longitude

__version__ = "1.1.0+build.1"

__all__ = ["Coordinates"]


@dataclass(repr=False, config=ConfigDict(frozen=True, extra="forbid", strict=True))
class Coordinates(IntrospectableMixin):
    """Immutable geospatial coordinate pair uniting Latitude and Longitude."""

    latitude: Latitude = Field(..., description="WGS 84 latitude atom (-90.0 to +90.0).")
    longitude: Longitude = Field(..., description="WGS 84 longitude atom (-180.0 to +180.0).")

    @classmethod
    def create(cls, latitude: Latitude | float, longitude: Longitude | float) -> Coordinates:
        """Factory constructor accepting validated atoms or raw numeric coordinates."""
        lat = latitude if isinstance(latitude, Latitude) else Latitude(latitude)
        lon = longitude if isinstance(longitude, Longitude) else Longitude(longitude)
        return cls(latitude=lat, longitude=lon)

    @property
    def formatted_coordinates(self) -> str:
        """Return canonical comma-separated formatted coordinates."""
        return f"{self.latitude}, {self.longitude}"

    def as_tuple(self) -> tuple[float, float]:
        """Return raw floating-point (latitude, longitude) tuple."""
        return float(self.latitude), float(self.longitude)

    def to_dict(self) -> dict[str, float]:
        """Serialize Coordinates to a primitive dictionary."""
        return {
            "latitude": self.latitude.value,
            "longitude": self.longitude.value,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Coordinates:
        """Deserialize a dictionary payload into immutable Coordinates."""
        if not isinstance(data, dict):
            raise ModelFormatError("Coordinates payload must be a dictionary.")
        if "latitude" not in data or "longitude" not in data:
            raise ModelFormatError("Coordinates payload requires 'latitude' and 'longitude'.")
        return cls.create(latitude=data["latitude"], longitude=data["longitude"])

    def to_json(self) -> str:
        """Serialize Coordinates to a JSON formatted string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_json(cls, payload: str) -> Coordinates:
        """Deserialize a JSON string directly into a Coordinates instance."""
        try:
            data = json.loads(payload)
        except Exception as exc:
            raise ModelFormatError(f"Failed to parse Coordinates JSON string: {exc}") from exc
        return cls.from_dict(data)

    def __str__(self) -> str:
        return self.formatted_coordinates

    def __repr__(self) -> str:
        return f"Coordinates(latitude={self.latitude!r}, longitude={self.longitude!r})"
