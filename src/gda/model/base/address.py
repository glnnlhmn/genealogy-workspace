"""Path: src/gda/model/base/address.py

Structured postal address representation using Pydantic dataclasses.

Operational Role:
    Defines the address representation ('Address') for physical sites,
    repositories, residences, and civil jurisdictions. Preserves street lines,
    city, state/province, postal codes, and binds optional geospatial Coordinates
    with copy-on-write mutators, factory instantiation, and serialization parity.

Architecture:
    - Address: Immutable Pydantic dataclass validating street address components.
"""

from __future__ import annotations

import json
from dataclasses import replace
from typing import Any, Self

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.errors import ModelFormatError
from gda.core.introspectable import IntrospectableMixin
from gda.model.atom.geo import Coordinates, Latitude, Longitude

__version__ = "1.1.0+build.2"

__all__ = ["Address"]


@dataclass(config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True))
class Address(IntrospectableMixin):
    """Structured postal address capturing street lines, city, state, postal codes, and coordinates."""

    address_line_1: str = Field(
        ..., description="Primary street line or rural route address descriptor."
    )
    address_line_2: str | None = Field(
        default=None,
        description="Optional secondary unit, suite, building, or apartment line.",
    )
    city: str | None = Field(
        default=None, description="Optional city, town, village, or municipality name."
    )
    state: str | None = Field(
        default=None,
        description="Optional state, province, region, or statoid descriptor.",
    )
    postal_code: str | None = Field(
        default=None, description="Optional postal or ZIP routing code."
    )
    coordinates: Coordinates | None = Field(
        default=None, description="Optional benchmark geospatial coordinate centroid."
    )

    def __post_init__(self) -> None:
        """Enforce non-empty primary street line invariant."""
        if not self.address_line_1 or not self.address_line_1.strip():
            raise ModelFormatError(
                "Address address_line_1 cannot be empty or whitespace.",
                details={"field": "address_line_1"},
            )

    @property
    def formatted_address(self) -> str:
        """Render single-line formatted street address."""
        parts: list[str] = [self.address_line_1]
        if self.address_line_2:
            parts.append(self.address_line_2)
        if self.city and self.state:
            parts.append(f"{self.city}, {self.state}")
        elif self.city:
            parts.append(self.city)
        elif self.state:
            parts.append(self.state)
        if self.postal_code:
            parts.append(self.postal_code)
        return ", ".join(parts)

    @classmethod
    def create(
        cls,
        address_line_1: str,
        address_line_2: str | None = None,
        city: str | None = None,
        state: str | None = None,
        postal_code: str | None = None,
        coordinates: Coordinates | None = None,
    ) -> Address:
        """Factory constructor instantiating a validated Address."""
        clean_1 = address_line_1.strip() if address_line_1 else ""
        if not clean_1:
            raise ModelFormatError("Address address_line_1 cannot be empty or whitespace.")

        clean_2 = address_line_2.strip() if address_line_2 and address_line_2.strip() else None
        clean_city = city.strip() if city and city.strip() else None
        clean_state = state.strip() if state and state.strip() else None
        clean_zip = postal_code.strip() if postal_code and postal_code.strip() else None

        return cls(
            address_line_1=clean_1,
            address_line_2=clean_2,
            city=clean_city,
            state=clean_state,
            postal_code=clean_zip,
            coordinates=coordinates,
        )

    def update_line_1(self, address_line_1: str) -> Self:
        """Return a new immutable copy with updated primary street address line."""
        clean = address_line_1.strip() if address_line_1 else ""
        if not clean:
            raise ModelFormatError("Address address_line_1 cannot be empty or whitespace.")
        return replace(self, address_line_1=clean)

    def update_line_2(self, address_line_2: str | None) -> Self:
        """Return a new immutable copy with updated secondary street address line."""
        clean = address_line_2.strip() if address_line_2 and address_line_2.strip() else None
        return replace(self, address_line_2=clean)

    def update_city(self, city: str | None) -> Self:
        """Return a new immutable copy with updated city descriptor."""
        clean = city.strip() if city and city.strip() else None
        return replace(self, city=clean)

    def update_state(self, state: str | None) -> Self:
        """Return a new immutable copy with updated state descriptor."""
        clean = state.strip() if state and state.strip() else None
        return replace(self, state=clean)

    def update_postal_code(self, postal_code: str | None) -> Self:
        """Return a new immutable copy with updated postal code."""
        clean = postal_code.strip() if postal_code and postal_code.strip() else None
        return replace(self, postal_code=clean)

    def update_coordinates(self, coordinates: Coordinates | None) -> Self:
        """Return a new immutable copy with updated geospatial coordinates."""
        return replace(self, coordinates=coordinates)

    def to_dict(self) -> dict[str, Any]:
        """Serialize Address to a dictionary payload."""
        data: dict[str, Any] = {
            "address_line_1": self.address_line_1,
        }
        if self.address_line_2 is not None:
            data["address_line_2"] = self.address_line_2
        if self.city is not None:
            data["city"] = self.city
        if self.state is not None:
            data["state"] = self.state
        if self.postal_code is not None:
            data["postal_code"] = self.postal_code
        if self.coordinates is not None:
            data["coordinates"] = {
                "latitude": self.coordinates.latitude.value,
                "longitude": self.coordinates.longitude.value,
            }
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Address:
        """Deserialize a dictionary payload into an immutable Address."""
        if not isinstance(data, dict):
            raise ModelFormatError("Address payload must be a dictionary.")

        raw_1 = data.get("address_line_1")
        if not raw_1 or not str(raw_1).strip():
            raise ModelFormatError("Missing required field 'address_line_1' for Address.")

        coords_obj: Coordinates | None = None
        raw_coords = data.get("coordinates")
        if isinstance(raw_coords, dict):
            lat = raw_coords.get("latitude")
            lon = raw_coords.get("longitude")
            if lat is not None and lon is not None:
                coords_obj = Coordinates(latitude=Latitude(lat), longitude=Longitude(lon))
        elif isinstance(raw_coords, Coordinates):
            coords_obj = raw_coords

        return cls.create(
            address_line_1=str(raw_1),
            address_line_2=data.get("address_line_2"),
            city=data.get("city"),
            state=data.get("state"),
            postal_code=data.get("postal_code"),
            coordinates=coords_obj,
        )

    def to_json(self) -> str:
        """Serialize Address to a JSON formatted string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_json(cls, payload: str) -> Address:
        """Deserialize a JSON string directly into an Address instance."""
        try:
            data = json.loads(payload)
        except Exception as exc:
            raise ModelFormatError(f"Failed to parse Address JSON string: {exc}") from exc
        return cls.from_dict(data)

    def __str__(self) -> str:
        """Render single-line formatted address."""
        return self.formatted_address

    def __repr__(self) -> str:
        """Render precise constructor representation."""
        return (
            f"Address(address_line_1='{self.address_line_1}', "
            f"address_line_2={self.address_line_2!r}, city={self.city!r}, "
            f"state={self.state!r}, postal_code={self.postal_code!r}, "
            f"coordinates={self.coordinates!r})"
        )
