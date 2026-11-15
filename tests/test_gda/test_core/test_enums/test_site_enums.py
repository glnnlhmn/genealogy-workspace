"""Path: tests/test_gda/test_core/test_enums/test_site_enums.py

Targeted behavioral test suite verifying physical venue and cemetery monument enums.

Operational Role:
    Validates physical site classifications, facility operational lifecycle
    states, and cemetery monument attributes, typologies, materials,
    and preservation conditions.

Test Structure & Protocol:
    - Atomized tests: 1:1 verification per behavioral contract.
    - Fully decorated: Explicitly decorated with registered pytest markers.
    - Dependencies: In-memory only; zero physical disk I/O.
"""

from __future__ import annotations

import pytest

from gda.core.enums.site import (
    MarkerCondition,
    MarkerMaterial,
    MarkerType,
    OperationalStatus,
    SiteType,
)

__version__ = "1.0.0+build.5"


# ==============================================================================
# GROUP 1: Physical Venues & Facility Lifecycles
# ==============================================================================


@pytest.mark.regression
def test_site_types() -> None:
    """Verify physical venue classifications."""
    expected_site_types = {
        "BUSINESS",
        "CEMETERY",
        "CHURCH",
        "COMMERCIAL",
        "FACILITY",
        "GOVERNMENT",
        "HOSPITAL",
        "LANDMARK",
        "MILITARY",
        "REPOSITORY",
        "RESIDENCE",
        "SCHOOL",
        "OTHER",
        "UNKNOWN",
    }
    assert {s.value for s in SiteType} == expected_site_types


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
# ==============================================================================


@pytest.mark.regression
def test_marker_type_typologies() -> None:
    """Verify cemetery marker and monument typologies."""
    assert MarkerType.UPRIGHT_HEADSTONE == "Upright Headstone"
    assert MarkerType.FLAT_MARKER == "Flat Marker"
    assert MarkerType.SLANT == "Slant"
    assert MarkerType.OBELISK == "Obelisk"
    assert MarkerType.LEDGER == "Ledger"
    assert MarkerType.TABLE_TOMB == "Table Tomb"
    assert MarkerType.FOOTSTONE == "Footstone"
    assert MarkerType.MONUMENT == "Monument"
    assert MarkerType.OTHER == "Other"


@pytest.mark.regression
def test_marker_material_and_conditions() -> None:
    """Verify headstone composition materials and preservation conditions."""
    assert MarkerMaterial.MARBLE == "Marble"
    assert MarkerMaterial.GRANITE == "Granite"
    assert MarkerMaterial.SANDSTONE == "Sandstone"
    assert MarkerMaterial.LIMESTONE == "Limestone"
    assert MarkerMaterial.SLATE == "Slate"
    assert MarkerMaterial.FIELDSTONE == "Fieldstone"
    assert MarkerMaterial.BRONZE == "Bronze"
    assert MarkerMaterial.OTHER == "Other"

    assert MarkerCondition.SOUND == "Sound"
    assert MarkerCondition.WEATHERED == "Weathered"
    assert MarkerCondition.BROKEN == "Broken"
    assert MarkerCondition.BROKEN_REPAIRED == "Broken/Repaired"
    assert MarkerCondition.SUNKEN == "Sunken"
    assert MarkerCondition.ILLEGIBLE == "Illegible"
    assert MarkerCondition.OVERGROWN == "Overgrown"
