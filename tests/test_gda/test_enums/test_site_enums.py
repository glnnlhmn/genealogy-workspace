"""Path: tests/test_gda/test_enums/test_site_enums.py

Targeted behavioral test suite verifying spatial jurisdictions and venue enums.

Operational Role:
    Validates geographic boundaries, physical site classifications,
    operational lifecycle states, and cemetery monument attributes.
"""

from __future__ import annotations

import pytest

from gda.enums.site import (
    LocationType,
    MarkerCondition,
    MarkerMaterial,
    MarkerType,
    OperationalStatus,
    SiteCategory,
    SiteType,
)

__version__ = "1.1.0+build.2"


# ==============================================================================
# GROUP 1: Spatial Jurisdictions & Physical Venues
# Note: Verification of LocationType, SiteType, SiteCategory alias, and OperationalStatus
# ==============================================================================


@pytest.mark.regression
def test_location_and_site_types() -> None:
    """Verify administrative jurisdictions and venue tokens."""
    assert LocationType.COUNTRY == "COUNTRY"
    assert LocationType.STATE == "STATE"
    assert LocationType.COUNTY == "COUNTY"
    assert LocationType.CITY == "CITY"

    expected_site_types = {
        "CEMETERY",
        "CHURCH",
        "COMMERCIAL",
        "GOVERNMENT",
        "HOSPITAL",
        "LANDMARK",
        "MILITARY",
        "REPOSITORY",
        "RESIDENCE",
        "OTHER",
        "UNKNOWN",
    }
    assert {s.value for s in SiteType} == expected_site_types
    assert SiteCategory is SiteType


@pytest.mark.regression
def test_operational_status_tokens() -> None:
    """Verify facility lifecycle operational statuses."""
    assert OperationalStatus.ACTIVE == "ACTIVE"
    assert OperationalStatus.DEFUNCT == "DEFUNCT"
    assert OperationalStatus.ABANDONED == "ABANDONED"
    assert OperationalStatus.HISTORICAL == "HISTORICAL"
    assert OperationalStatus.UNKNOWN == "UNKNOWN"


# ==============================================================================
# GROUP 2: Cemetery Memorial Typologies
# Note: Verification of MarkerType, MarkerMaterial, and MarkerCondition
# ==============================================================================


@pytest.mark.regression
def test_marker_type_typologies() -> None:
    """Verify cemetery marker and monument typologies."""
    assert MarkerType.UPRIGHT_HEADSTONE == "Upright Headstone"
    assert MarkerType.FLAT_MARKER == "Flat Marker"
    assert MarkerType.OBELISK == "Obelisk"
    assert MarkerType.TABLE_TOMB == "Table Tomb"


@pytest.mark.regression
def test_marker_material_and_conditions() -> None:
    """Verify headstone composition materials and preservation conditions."""
    assert MarkerMaterial.MARBLE == "Marble"
    assert MarkerMaterial.GRANITE == "Granite"
    assert MarkerMaterial.SLATE == "Slate"
    assert MarkerCondition.SOUND == "Sound"
    assert MarkerCondition.WEATHERED == "Weathered"
    assert MarkerCondition.BROKEN_REPAIRED == "Broken/Repaired"
