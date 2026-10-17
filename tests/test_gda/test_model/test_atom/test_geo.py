# Name: test_geo.py
# Path: tests/test_gda/test_model/test_atom/test_geo.py

"""Comprehensive test suite verifying geographic coordinate primitives.

Operational Role:
    Verifies that Latitude and Longitude enforce strict boundary ranges,
    render formatted floating-point strings, and assemble into immutable Coordinates.

Test Structure & Protocol:
    - Atomized tests: 1:1 behavioral contract mapping.
    - Fully decorated: Standard 7-marker taxonomy.
    - Zero production disk I/O.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from gda.model.atom.errors import AtomRangeError
from gda.model.atom.geo import Coordinates, Latitude, Longitude

__version__ = "1.0.0+build.r5"


# ==============================================================================
# GROUP 1: LATITUDE INVARIANTS & BOUNDARIES
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_latitude_valid_range() -> None:
    """Verify Latitude instantiates correctly at boundary and intermediate values."""
    lat_min = Latitude(-90.0)
    lat_mid = Latitude(43.208136)
    lat_max = Latitude(90.0)

    assert float(lat_min) == -90.0
    assert float(lat_mid) == 43.208136
    assert float(lat_max) == 90.0
    assert str(lat_mid) == "43.208136"
    assert repr(lat_mid) == "Latitude(value=43.208136)"


@pytest.mark.unit
@pytest.mark.regression
@pytest.mark.parametrize("invalid_lat", [-90.0001, -100.0, 90.0001, 150.0])
def test_latitude_out_of_bounds_raises_range_error(invalid_lat: float) -> None:
    """Verify Latitude raises AtomRangeError when boundary values are exceeded."""
    with pytest.raises(AtomRangeError, match="out of range"):
        Latitude(invalid_lat)


# ==============================================================================
# GROUP 2: LONGITUDE INVARIANTS & BOUNDARIES
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_longitude_valid_range() -> None:
    """Verify Longitude instantiates correctly at boundary and intermediate values."""
    lon_min = Longitude(-180.0)
    lon_mid = Longitude(-71.537572)
    lon_max = Longitude(180.0)

    assert float(lon_min) == -180.0
    assert float(lon_mid) == -71.537572
    assert float(lon_max) == 180.0
    assert str(lon_mid) == "-71.537572"
    assert repr(lon_mid) == "Longitude(value=-71.537572)"


@pytest.mark.unit
@pytest.mark.regression
@pytest.mark.parametrize("invalid_lon", [-180.0001, -200.0, 180.0001, 250.0])
def test_longitude_out_of_bounds_raises_range_error(invalid_lon: float) -> None:
    """Verify Longitude raises AtomRangeError when boundary values are exceeded."""
    with pytest.raises(AtomRangeError, match="out of range"):
        Longitude(invalid_lon)


# ==============================================================================
# GROUP 3: COORDINATES AGGREGATION & FORMATTING
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_coordinates_formatting() -> None:
    """Verify Coordinates aggregates Latitude and Longitude into standard string representations."""
    coords = Coordinates(latitude=Latitude(43.208136), longitude=Longitude(-71.537572))
    assert coords.formatted_coordinates == "43.208136, -71.537572"
    assert str(coords) == "43.208136, -71.537572"
    assert repr(coords) == (
        "Coordinates(latitude=Latitude(value=43.208136), longitude=Longitude(value=-71.537572))"
    )


# ==============================================================================
# GROUP 4: IMMUTABILITY & INTROSPECTION
# ==============================================================================


@pytest.mark.unit
def test_geo_atoms_immutability() -> None:
    """Verify geographic coordinate primitives are immutable."""
    lat = Latitude(45.0)
    with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
        lat.value = 50.0  # type: ignore[misc]

    lon = Longitude(-70.0)
    with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
        lon.value = -75.0  # type: ignore[misc]

    coords = Coordinates(latitude=lat, longitude=lon)
    with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
        coords.latitude = Latitude(0.0)  # type: ignore[misc]


@pytest.mark.unit
def test_geo_atoms_introspection() -> None:
    """Verify .help() renders member directory on coordinate primitives."""
    coords = Coordinates(latitude=Latitude(43.0), longitude=Longitude(-71.0))
    help_text = coords.help(as_str=True)
    assert help_text is not None
    assert "=== Coordinates Public Directory ===" in help_text
    assert "formatted_coordinates" in help_text
