"""Path: tests/test_gda/test_model/test_base/test_address.py

Comprehensive test suite verifying Address formatting, mutators, and boundaries.

Operational Role:
    Verifies that Address enforces non-empty address_line_1 invariants,
    formats single-line addresses across optional lines, city, state, and postal codes,
    executes copy-on-write mutators, verifies dictionary and JSON serialization,
    and guarantees frozen immutability with 100% statement and branch coverage.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from typing import Any

import pytest

from gda.core.errors import ModelFormatError
from gda.model.atom.geo import Coordinates, Latitude, Longitude
from gda.model.base.address import Address

__version__ = "1.1.0+build.3"


# ==============================================================================
# GROUP 1: ADDRESS CREATION & FORMATTING
# Note: Verification of instantiation, string rendering, and constructor representation
# ==============================================================================


@pytest.mark.regression
def test_address_full_creation() -> None:
    """Verify Address with lines, city, state, postal code, and coordinates."""
    coords = Coordinates(latitude=Latitude(43.200000), longitude=Longitude(-71.530000))
    addr = Address(
        address_line_1="100 Main St",
        address_line_2="Suite 4B",
        city="Concord",
        state="NH",
        postal_code="03301",
        coordinates=coords,
    )
    assert addr.address_line_1 == "100 Main St"
    assert addr.address_line_2 == "Suite 4B"
    assert addr.city == "Concord"
    assert addr.state == "NH"
    assert addr.postal_code == "03301"
    assert addr.coordinates == coords
    assert addr.formatted_address == "100 Main St, Suite 4B, Concord, NH, 03301"
    assert str(addr) == "100 Main St, Suite 4B, Concord, NH, 03301"
    assert repr(addr) == (
        "Address(address_line_1='100 Main St', address_line_2='Suite 4B', "
        "city='Concord', state='NH', postal_code='03301', "
        "coordinates=Coordinates(latitude=Latitude(value=43.2), longitude=Longitude(value=-71.53)))"
    )


@pytest.mark.regression
def test_address_single_line_only() -> None:
    """Verify Address formatting with only address_line_1."""
    addr = Address(address_line_1="Rural Route 2")
    assert addr.formatted_address == "Rural Route 2"
    assert addr.address_line_2 is None
    assert addr.city is None
    assert addr.state is None
    assert addr.postal_code is None
    assert addr.coordinates is None


@pytest.mark.regression
def test_address_partial_city_state_formatting() -> None:
    """Verify formatting branches when either city or state is independently populated."""
    city_only = Address(address_line_1="100 Main St", city="Bow")
    assert city_only.formatted_address == "100 Main St, Bow"

    state_only = Address(address_line_1="100 Main St", state="NH")
    assert state_only.formatted_address == "100 Main St, NH"


@pytest.mark.regression
def test_address_factory_create() -> None:
    """Verify Address.create cleans whitespace and instantiates properly."""
    addr = Address.create(
        address_line_1="  50 South St  ",
        address_line_2="  Apt 2B  ",
        city="  Concord  ",
        state="  NH  ",
        postal_code="  03304  ",
    )
    assert addr.address_line_1 == "50 South St"
    assert addr.address_line_2 == "Apt 2B"
    assert addr.city == "Concord"
    assert addr.state == "NH"
    assert addr.postal_code == "03304"

    addr_empty_opt = Address.create(
        address_line_1="50 South St",
        address_line_2="   ",
        city="",
        state=None,
        postal_code="",
    )
    assert addr_empty_opt.address_line_2 is None
    assert addr_empty_opt.city is None
    assert addr_empty_opt.state is None
    assert addr_empty_opt.postal_code is None


# ==============================================================================
# GROUP 2: COPY-ON-WRITE MUTATORS
# Note: Verification of immutable copy production on field modifications
# ==============================================================================


@pytest.mark.regression
def test_address_copy_on_write_mutators() -> None:
    """Verify Address mutators produce fresh copies with updated attributes."""
    original = Address(address_line_1="100 Main St")

    up1 = original.update_line_1("200 Elm St")
    assert up1 is not original
    assert up1.address_line_1 == "200 Elm St"

    up2 = original.update_line_2("Floor 3")
    assert up2 is not original
    assert up2.address_line_2 == "Floor 3"

    up_city = original.update_city("Manchester")
    assert up_city is not original
    assert up_city.city == "Manchester"

    up_state = original.update_state("NH")
    assert up_state is not original
    assert up_state.state == "NH"

    up_zip = original.update_postal_code("03301")
    assert up_zip is not original
    assert up_zip.postal_code == "03301"

    new_coords = Coordinates(latitude=Latitude(43.10), longitude=Longitude(-71.50))
    up_coords = original.update_coordinates(new_coords)
    assert up_coords is not original
    assert up_coords.coordinates == new_coords


@pytest.mark.regression
def test_address_mutators_empty_rejection() -> None:
    """Verify update_line_1 rejects empty or whitespace strings."""
    addr = Address(address_line_1="100 Main St")
    with pytest.raises(ModelFormatError, match="address_line_1 cannot be empty"):
        addr.update_line_1("   ")


# ==============================================================================
# GROUP 3: SERIALIZATION & ROUND TRIPS
# Note: Verification of dictionary and JSON string payload conversions
# ==============================================================================


@pytest.mark.integration
def test_address_to_dict_and_from_dict_round_trip() -> None:
    """Verify Address dictionary serialization and deserialization."""
    coords = Coordinates(latitude=Latitude(43.1319), longitude=Longitude(-71.5497))
    addr = Address(
        address_line_1="Woodhill Hook Road",
        address_line_2="Building B",
        city="Bow",
        state="NH",
        postal_code="03304",
        coordinates=coords,
    )
    data = addr.to_dict()
    assert data["address_line_1"] == "Woodhill Hook Road"
    assert data["address_line_2"] == "Building B"
    assert data["city"] == "Bow"
    assert data["state"] == "NH"
    assert data["postal_code"] == "03304"
    assert data["coordinates"] == {"latitude": 43.1319, "longitude": -71.5497}

    restored = Address.from_dict(data)
    assert restored == addr


@pytest.mark.integration
def test_address_to_dict_minimal_omits_none_fields() -> None:
    """Verify Address.to_dict omits None optional fields."""
    minimal = Address(address_line_1="Route 3A")
    data = minimal.to_dict()
    assert data == {"address_line_1": "Route 3A"}
    assert "address_line_2" not in data
    assert "city" not in data
    assert "state" not in data
    assert "postal_code" not in data
    assert "coordinates" not in data

    restored = Address.from_dict(data)
    assert restored == minimal


@pytest.mark.integration
def test_address_from_dict_with_direct_coordinates_instance() -> None:
    """Verify Address.from_dict handles pre-constructed Coordinates object."""
    coords = Coordinates(latitude=Latitude(43.1319), longitude=Longitude(-71.5497))
    data: dict[str, Any] = {
        "address_line_1": "Woodhill Hook Road",
        "coordinates": coords,
    }
    restored = Address.from_dict(data)
    assert restored.coordinates == coords


@pytest.mark.integration
def test_address_from_dict_partial_coordinates_dict() -> None:
    """Verify Address.from_dict handles dict coordinates with missing latitude or longitude."""
    data_missing_lat: dict[str, Any] = {
        "address_line_1": "Woodhill Hook Road",
        "coordinates": {"latitude": None, "longitude": -71.5497},
    }
    restored = Address.from_dict(data_missing_lat)
    assert restored.coordinates is None

    data_missing_lon: dict[str, Any] = {
        "address_line_1": "Woodhill Hook Road",
        "coordinates": {"latitude": 43.1319, "longitude": None},
    }
    restored_lon = Address.from_dict(data_missing_lon)
    assert restored_lon.coordinates is None


@pytest.mark.integration
def test_address_json_serialization_round_trip() -> None:
    """Verify Address JSON serialization round trip."""
    addr = Address(
        address_line_1="100 Main St",
        city="Concord",
        state="NH",
        postal_code="03301",
    )
    json_str = addr.to_json()
    assert "100 Main St" in json_str
    assert "Concord" in json_str

    restored = Address.from_json(json_str)
    assert restored == addr


@pytest.mark.regression
def test_address_deserialization_defensive_errors() -> None:
    """Verify deserializers reject malformed payloads."""
    with pytest.raises(ModelFormatError, match="payload must be a dictionary"):
        Address.from_dict("not-a-dict")  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="Missing required field 'address_line_1'"):
        Address.from_dict({"address_line_2": "Suite 1"})

    with pytest.raises(ModelFormatError, match="address_line_1 cannot be empty"):
        Address.create(address_line_1="   ")

    with pytest.raises(ModelFormatError, match="Failed to parse Address JSON"):
        Address.from_json("{broken json")


# ==============================================================================
# GROUP 4: DEFENSIVE BOUNDARIES & IMMUTABILITY
# Note: Verification of whitespace rejections, frozen instances, and introspection
# ==============================================================================


@pytest.mark.regression
@pytest.mark.parametrize("blank_line", ["", " ", "\t\n"])
def test_address_empty_line_1_raises_error(blank_line: str) -> None:
    """Verify Address raises ModelFormatError if address_line_1 is blank."""
    with pytest.raises(ModelFormatError, match="address_line_1 cannot be empty"):
        Address(address_line_1=blank_line)


@pytest.mark.regression
def test_address_immutability() -> None:
    """Verify Address is frozen and immutable."""
    addr = Address(address_line_1="123 Oak St")
    with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
        addr.address_line_1 = "456 Pine St"  # type: ignore[misc]


@pytest.mark.regression
def test_address_introspection() -> None:
    """Verify .help() renders member directory on Address."""
    addr = Address(address_line_1="123 Oak St")
    help_text = addr.help(as_str=True)
    assert help_text is not None
    assert "=== Address Public Directory ===" in help_text
    assert "formatted_address" in help_text
    assert "update_line_1" in help_text
    assert "update_city" in help_text
    assert "update_state" in help_text
