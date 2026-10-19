"""Path: tests/test_gda/test_enums/test_site_enums.py

Targeted behavioral test suite verifying spatial jurisdictions and venue enums.

Operational Role:
    Validates geographic boundaries, physical site classifications,
    operational lifecycle states, and cemetery monument attributes.

Test Structure & Protocol:
    - Atomized tests: 1:1 verification per behavioral contract.
    - Fully decorated: Explicitly decorated with registered pytest markers.
    - Dependencies: In-memory only; zero physical disk I/O.
"""

from __future__ import annotations

import pytest

from gda.enums.site import (
    LocationType,
    MarkerCondition,
    MarkerMaterial,
    MarkerType,
    OperationalStatus,
    SiteType,
)

__version__ = "0.1.0+build.1"

# ==============================================================================
# GROUP 1: Spatial Jurisdictions & Physical Venues
# Note: Verification of LocationType, SiteType, and OperationalStatus
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_location_and_site_types() -> None:
    """Verify administrative jurisdictions and venue tokens."""
    assert LocationType.COUNTRY == "COUNTRY"
    assert LocationType.STATE == "STATE"
    assert LocationType.COUNTY == "COUNTY"
    assert LocationType.CITY == "CITY"
    assert SiteType.CEMETERY == "CEMETERY"
    assert SiteType.CHURCH == "CHURCH"
    assert SiteType.HOSPITAL == "HOSPITAL"
    assert SiteType.LANDMARK == "LANDMARK"


@pytest.mark.unit
def test_operational_status_tokens() -> None:
    """Verify facility lifecycle operational statuses."""
    assert OperationalStatus.ACTIVE == "ACTIVE"
    assert OperationalStatus.DEFUNCT == "DEFUNCT"
    assert OperationalStatus.ABANDONED == "ABANDONED"
    assert OperationalStatus.HISTORICAL == "HISTORICAL"


# ==============================================================================
# GROUP 2: Cemetery Memorial Typologies
# Note: Verification of MarkerType, MarkerMaterial, and MarkerCondition
# ==============================================================================


@pytest.mark.unit
def test_marker_type_typologies() -> None:
    """Verify cemetery marker and monument typologies."""
    assert MarkerType.UPRIGHT_HEADSTONE == "Upright Headstone"
    assert MarkerType.FLAT_MARKER == "Flat Marker"
    assert MarkerType.OBELISK == "Obelisk"
    assert MarkerType.TABLE_TOMB == "Table Tomb"


@pytest.mark.unit
def test_marker_material_and_conditions() -> None:
    """Verify headstone composition materials and preservation conditions."""
    assert MarkerMaterial.MARBLE == "Marble"
    assert MarkerMaterial.GRANITE == "Granite"
    assert MarkerMaterial.SLATE == "Slate"
    assert MarkerCondition.SOUND == "Sound"
    assert MarkerCondition.WEATHERED == "Weathered"
    assert MarkerCondition.BROKEN_REPAIRED == "Broken/Repaired"
