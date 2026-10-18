"""Path: tests/test_gda/test_model/test_base/test_address.py

Comprehensive test suite verifying Address formatting and boundaries.

Operational Role:
    Verifies that Address enforces non-empty address_line_1 invariants,
    formats single-line addresses across optional lines and postal codes,
    associates spatial coordinates, and guarantees immutability.

Test Structure & Protocol:
    - Atomized tests: 1:1 behavioral contract mapping.
    - Fully decorated: Standard 7-marker taxonomy.
    - Zero production disk I/O.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from gda.core.errors import ModelFormatError
from gda.model.atom.geo import Coordinates, Latitude, Longitude
from gda.model.base.address import Address

__version__ = "1.0.0+build.3"


# ==============================================================================
# GROUP 1: ADDRESS CREATION & FORMATTING
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_address_full_creation() -> None:
    """Verify Address with lines, postal code, and coordinates."""
    coords = Coordinates(latitude=Latitude(43.200000), longitude=Longitude(-71.530000))
    addr = Address(
        address_line_1="100 Main St",
        address_line_2="Suite 4B",
        postal_code="03301",
        coordinates=coords,
    )
    assert addr.address_line_1 == "100 Main St"
    assert addr.address_line_2 == "Suite 4B"
    assert addr.postal_code == "03301"
    assert addr.coordinates == coords
    assert addr.formatted_address == "100 Main St, Suite 4B, 03301"
    assert str(addr) == "100 Main St, Suite 4B, 03301"
    assert repr(addr) == (
        "Address(address_line_1='100 Main St', address_line_2='Suite 4B', "
        "postal_code='03301', coordinates=Coordinates(latitude=Latitude(value=43.2), "
        "longitude=Longitude(value=-71.53)))"
    )


@pytest.mark.unit
@pytest.mark.smoke
def test_address_single_line_only() -> None:
    """Verify Address formatting with only address_line_1."""
    addr = Address(address_line_1="Rural Route 2")
    assert addr.formatted_address == "Rural Route 2"
    assert addr.address_line_2 is None
    assert addr.postal_code is None
    assert addr.coordinates is None


# ==============================================================================
# GROUP 2: DEFENSIVE BOUNDARIES & IMMUTABILITY
# ==============================================================================


@pytest.mark.unit
@pytest.mark.regression
@pytest.mark.parametrize("blank_line", ["", "   ", "\t\n"])
def test_address_empty_line_1_raises_error(blank_line: str) -> None:
    """Verify Address raises ModelFormatError if address_line_1 is blank."""
    with pytest.raises(ModelFormatError, match="address_line_1 cannot be empty"):
        Address(address_line_1=blank_line)


@pytest.mark.unit
def test_address_immutability() -> None:
    """Verify Address is frozen and immutable."""
    addr = Address(address_line_1="123 Oak St")
    with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
        addr.address_line_1 = "456 Pine St"  # type: ignore[misc]


@pytest.mark.unit
def test_address_introspection() -> None:
    """Verify .help() renders member directory on Address."""
    addr = Address(address_line_1="123 Oak St")
    help_text = addr.help(as_str=True)
    assert help_text is not None
    assert "=== Address Public Directory ===" in help_text
    assert "formatted_address" in help_text
