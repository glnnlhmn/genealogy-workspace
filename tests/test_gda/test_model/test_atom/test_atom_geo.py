"""Path: tests/test_gda/test_model/test_atom/test_atom_geo.py

Comprehensive test suite verifying geographic coordinate scalar primitives.

Operational Role:
    Verifies that Latitude and Longitude enforce strict boundary ranges (-90..90
    and -180..180), reject booleans and strings, normalize ints to floats, support
    raw float equality, enforce homogeneous total ordering, and uphold immutability.

Test Structure & Protocol:
    - Atomized tests: 1:1 behavioral contract mapping.
    - Fully decorated: Pytest marker taxonomy (1 @pytest.mark.smoke).
    - Zero production disk I/O.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from typing import Any

import pytest
from tests.test_gda.test_model.test_atom.conftest import INVALID_NON_NUMERIC_VALUES

from gda.core.errors import ModelFormatError, ModelRangeError
from gda.model.atom.geo import Latitude, Longitude

__version__ = "1.0.0+build.10"


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
    lat_int = Latitude(45)

    assert float(lat_min) == -90.0
    assert float(lat_mid) == 43.208136
    assert float(lat_max) == 90.0
    assert type(lat_int.value) is float
    assert lat_int.value == 45.0
    assert str(lat_mid) == "43.208136"
    assert repr(lat_mid) == "Latitude(value=43.208136)"


@pytest.mark.unit
@pytest.mark.regression
@pytest.mark.parametrize("invalid_lat", [-90.0001, -91.0, -100.0, 90.0001, 91.0, 150.0])
def test_latitude_out_of_bounds_raises_range_error(invalid_lat: float) -> None:
    """Verify Latitude raises ModelRangeError when boundary values are exceeded."""
    with pytest.raises(ModelRangeError, match="out of range"):
        Latitude(invalid_lat)


@pytest.mark.unit
@pytest.mark.regression
@pytest.mark.parametrize("bad_type", INVALID_NON_NUMERIC_VALUES)
def test_latitude_invalid_type_raises_error(bad_type: Any) -> None:
    """Verify Latitude rejects booleans, strings, and None."""
    with pytest.raises((ModelFormatError, TypeError, ValueError)):
        Latitude(bad_type)


# ==============================================================================
# GROUP 2: LONGITUDE INVARIANTS & BOUNDARIES
# ==============================================================================


@pytest.mark.unit
def test_longitude_valid_range() -> None:
    """Verify Longitude instantiates correctly at boundary and intermediate values."""
    lon_min = Longitude(-180.0)
    lon_mid = Longitude(-71.537572)
    lon_max = Longitude(180.0)
    lon_int = Longitude(-70)

    assert float(lon_min) == -180.0
    assert float(lon_mid) == -71.537572
    assert float(lon_max) == 180.0
    assert type(lon_int.value) is float
    assert lon_int.value == -70.0
    assert str(lon_mid) == "-71.537572"
    assert repr(lon_mid) == "Longitude(value=-71.537572)"


@pytest.mark.unit
@pytest.mark.regression
@pytest.mark.parametrize("invalid_lon", [-180.0001, -181.0, -200.0, 180.0001, 181.0, 250.0])
def test_longitude_out_of_bounds_raises_range_error(invalid_lon: float) -> None:
    """Verify Longitude raises ModelRangeError when boundary values are exceeded."""
    with pytest.raises(ModelRangeError, match="out of range"):
        Longitude(invalid_lon)


@pytest.mark.unit
@pytest.mark.regression
@pytest.mark.parametrize("bad_type", INVALID_NON_NUMERIC_VALUES)
def test_longitude_invalid_type_raises_error(bad_type: Any) -> None:
    """Verify Longitude rejects booleans, strings, and None."""
    with pytest.raises((ModelFormatError, TypeError, ValueError)):
        Longitude(bad_type)


# ==============================================================================
# GROUP 3: EQUALITY, HOMOGENEOUS ORDERING, IMMUTABILITY & INTROSPECTION
# ==============================================================================


@pytest.mark.unit
def test_geo_atoms_equality_and_homogeneous_ordering(
    sample_latitude: Latitude,
    sample_longitude: Longitude,
) -> None:
    """Verify raw float equality, hashing, and strict homogeneous ordering."""
    assert sample_latitude == Latitude(43.208136)
    assert sample_latitude == 43.208136
    assert Latitude(45.0) == 45
    assert (Latitude(1.0) == True) is False  # noqa: E712  # type: ignore[comparison-overlap]
    assert hash(sample_latitude) == hash(43.208136)

    assert sample_longitude == Longitude(-71.537572)
    assert sample_longitude == -71.537572
    assert Longitude(-70.0) == -70
    assert (Longitude(1.0) == True) is False  # noqa: E712  # type: ignore[comparison-overlap]
    assert (Longitude(1.0) == "1.0") is False  # type: ignore[comparison-overlap]
    assert hash(sample_longitude) == hash(-71.537572)

    assert Latitude(-10.0) < sample_latitude < Latitude(80.0)
    assert Longitude(-120.0) < sample_longitude < Longitude(0.0)

    # Cross-type ordering between Latitude and Longitude must raise TypeError
    with pytest.raises(TypeError):
        _ = sample_latitude < sample_longitude  # type: ignore[operator]
    with pytest.raises(TypeError):
        _ = sample_latitude < 50.0  # type: ignore[operator]
    with pytest.raises(TypeError):
        _ = sample_longitude < 50.0  # type: ignore[operator]


@pytest.mark.unit
def test_geo_atoms_immutability(
    sample_latitude: Latitude,
    sample_longitude: Longitude,
) -> None:
    """Verify geographic coordinate primitives are immutable."""
    with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
        sample_latitude.value = 50.0  # type: ignore[misc]

    with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
        sample_longitude.value = -75.0  # type: ignore[misc]


@pytest.mark.unit
def test_geo_atoms_introspection(sample_latitude: Latitude) -> None:
    """Verify .help() renders member directory on coordinate primitives."""
    help_text = sample_latitude.help(as_str=True)
    assert help_text is not None
    assert "=== Latitude Public Directory ===" in help_text
