"""Path: tests/test_gda/test_model/test_base/test_zero_intra_base/test_geo.py

Comprehensive test suite verifying Coordinates composite invariants and serialization.

Operational Role:
    Verifies that Coordinates enforces strict Latitude/Longitude atom typing,
    provides .create() factory construction, formatted coordinates, tuple extraction,
    JSON/dict serialization round-trips, immutability, and introspection with 100%
    statement and branch coverage.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest
from pydantic import ValidationError

from gda.core.errors import ModelFormatError
from gda.model.atom.geo import Latitude, Longitude
from gda.model.base.geo import Coordinates

__version__ = "1.1.0+build.2"


# ==============================================================================
# GROUP 1: COORDINATES CREATION & FORMATTING
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_coordinates_valid_creation_and_formatting(sample_coordinates: Coordinates) -> None:
    """Verify Coordinates instantiates with Latitude/Longitude atoms and formats properly."""
    assert sample_coordinates.latitude == Latitude(43.2081)
    assert sample_coordinates.longitude == Longitude(-71.5376)
    assert sample_coordinates.formatted_coordinates == "43.208100, -71.537600"
    assert str(sample_coordinates) == "43.208100, -71.537600"
    assert sample_coordinates.as_tuple() == (43.2081, -71.5376)
    assert repr(sample_coordinates) == (
        "Coordinates(latitude=Latitude(value=43.2081), longitude=Longitude(value=-71.5376))"
    )


@pytest.mark.unit
@pytest.mark.smoke
def test_coordinates_create_factory_accepts_floats_and_atoms() -> None:
    """Verify Coordinates.create() accepts raw floats or validated atoms."""
    from_floats = Coordinates.create(43.2081, -71.5376)
    from_atoms = Coordinates.create(Latitude(43.2081), Longitude(-71.5376))
    assert from_floats == from_atoms


@pytest.mark.unit
@pytest.mark.regression
def test_coordinates_strict_mode_rejects_raw_floats_on_direct_init() -> None:
    """Verify strict=True rejects raw floats on direct Coordinates() constructor."""
    with pytest.raises(ValidationError):
        Coordinates(latitude=43.2081, longitude=-71.5376)  # type: ignore[arg-type]


# ==============================================================================
# GROUP 2: SERIALIZATION ROUND-TRIPS & DEFENSIVE ERRORS
# ==============================================================================


@pytest.mark.unit
def test_coordinates_dict_and_json_round_trip(sample_coordinates: Coordinates) -> None:
    """Verify to_dict, from_dict, to_json, and from_json round-trip fidelity."""
    payload = sample_coordinates.to_dict()
    assert payload == {"latitude": 43.2081, "longitude": -71.5376}
    assert Coordinates.from_dict(payload) == sample_coordinates

    json_str = sample_coordinates.to_json()
    assert Coordinates.from_json(json_str) == sample_coordinates


@pytest.mark.unit
@pytest.mark.regression
def test_coordinates_deserialization_errors() -> None:
    """Verify from_dict and from_json raise ModelFormatError on invalid payloads."""
    with pytest.raises(ModelFormatError, match="must be a dictionary"):
        Coordinates.from_dict("not-a-dict")  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="requires 'latitude' and 'longitude'"):
        Coordinates.from_dict({"latitude": 43.2081})

    with pytest.raises(ModelFormatError, match="Failed to parse Coordinates JSON"):
        Coordinates.from_json("{invalid-json")


@pytest.mark.unit
def test_coordinates_immutability_and_introspection(sample_coordinates: Coordinates) -> None:
    """Verify Coordinates is frozen and supports IntrospectableMixin .help()."""
    with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
        sample_coordinates.latitude = Latitude(40.0)  # type: ignore[misc]

    help_text = sample_coordinates.help(as_str=True)
    assert help_text is not None
    assert "=== Coordinates Public Directory ===" in help_text
