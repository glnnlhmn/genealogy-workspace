"""Path: tests/test_gda/test_core/test_enums/test_site_enums.py

Targeted behavioral test suite verifying physical venue and cemetery monument enums.

Operational Role:
    Validates gda.core.enums.site public exports, physical site classifications,
    facility operational lifecycle states, and cemetery monument typologies,
    materials, and preservation conditions.

Test Structure & Protocol:
    - Atomized & parametrized tests: 1:1 behavioral contract mapping.
    - Fully decorated: 5-marker taxonomy (smoke, unit, regression).
    - Dependencies: In-memory only; zero physical disk I/O.
"""

from __future__ import annotations

import pytest

import gda.core.enums.site as site_enums
from gda.core.enums.site import (
    MarkerCondition,
    MarkerMaterial,
    MarkerType,
    OperationalStatus,
    SiteType,
)

__version__ = "1.0.0+build.6"


# ==============================================================================
# GROUP 1: Smoke & Primary Entrypoints
# Note: Single smoke gate verifying gda.core.enums.site public exports.
# ==============================================================================


@pytest.mark.smoke
@pytest.mark.unit
def test_site_enums_exposes_expected_public_interface() -> None:
    """Verify gda.core.enums.site exports all 5 site and monument enum classes."""
    expected = {
        "MarkerCondition",
        "MarkerMaterial",
        "MarkerType",
        "OperationalStatus",
        "SiteType",
    }
    assert set(site_enums.__all__) == expected


# ==============================================================================
# GROUP 2: Core Logic & Happy Paths
# Note: Physical venues, facility lifecycles, and UPPER_SNAKE_CASE monument enums.
# ==============================================================================


@pytest.mark.unit
def test_site_types_and_operational_status() -> None:
    """Verify physical venue classifications and facility operational statuses."""
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
    assert {s.value for s in OperationalStatus} == {
        "ACTIVE",
        "DEFUNCT",
        "ABANDONED",
        "HISTORICAL",
        "UNKNOWN",
    }


@pytest.mark.unit
def test_marker_type_upper_snake_case_values() -> None:
    """Verify MarkerType uses UPPER_SNAKE_CASE tokens (Phase 3 TDD Red)."""
    assert MarkerType.UPRIGHT_HEADSTONE == "UPRIGHT_HEADSTONE"
    assert MarkerType.FLAT_MARKER == "FLAT_MARKER"
    assert MarkerType.SLANT == "SLANT"
    assert MarkerType.OBELISK == "OBELISK"
    assert MarkerType.LEDGER == "LEDGER"
    assert MarkerType.TABLE_TOMB == "TABLE_TOMB"
    assert MarkerType.FOOTSTONE == "FOOTSTONE"
    assert MarkerType.MONUMENT == "MONUMENT"
    assert MarkerType.OTHER == "OTHER"


@pytest.mark.unit
def test_marker_material_upper_snake_case_values() -> None:
    """Verify MarkerMaterial uses UPPER_SNAKE_CASE tokens (Phase 3 TDD Red)."""
    assert MarkerMaterial.MARBLE == "MARBLE"
    assert MarkerMaterial.GRANITE == "GRANITE"
    assert MarkerMaterial.SANDSTONE == "SANDSTONE"
    assert MarkerMaterial.LIMESTONE == "LIMESTONE"
    assert MarkerMaterial.SLATE == "SLATE"
    assert MarkerMaterial.FIELDSTONE == "FIELDSTONE"
    assert MarkerMaterial.BRONZE == "BRONZE"
    assert MarkerMaterial.OTHER == "OTHER"


@pytest.mark.unit
def test_marker_condition_upper_snake_case_values() -> None:
    """Verify MarkerCondition uses UPPER_SNAKE_CASE tokens (Phase 3 TDD Red)."""
    assert MarkerCondition.SOUND == "SOUND"
    assert MarkerCondition.WEATHERED == "WEATHERED"
    assert MarkerCondition.BROKEN == "BROKEN"
    assert MarkerCondition.BROKEN_REPAIRED == "BROKEN_REPAIRED"
    assert MarkerCondition.SUNKEN == "SUNKEN"
    assert MarkerCondition.ILLEGIBLE == "ILLEGIBLE"
    assert MarkerCondition.OVERGROWN == "OVERGROWN"


# ==============================================================================
# GROUP 4: Error Handling & Validation Failures
# Note: Strict invalid-value rejection on site enums.
# ==============================================================================


@pytest.mark.regression
@pytest.mark.parametrize("bad_value", ["COUNTY", "cemetery", " CHURCH ", ""])
def test_site_type_rejects_invalid_and_untrimmed_values(bad_value: str) -> None:
    """Verify SiteType rejects jurisdiction names, lowercase, and padded strings."""
    with pytest.raises(ValueError):
        SiteType(bad_value)
