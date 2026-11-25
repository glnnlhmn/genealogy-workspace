"""Path: tests/test_gda/test_core/test_enums/test_location_enums.py

Targeted behavioral test suite verifying location and administrative enums.

Operational Role:
    Validates gda.core.enums.location public exports, civil administrative
    jurisdictions (JurisdictionCategory), linear administrative_rank hierarchy,
    and spatial place classifications (LocationType).

Test Structure & Protocol:
    - Atomized & parametrized tests: 1:1 behavioral contract mapping.
    - Fully decorated: 5-marker taxonomy (smoke, unit, regression, integrity).
    - Dependencies: In-memory only; zero physical disk I/O.
"""

from __future__ import annotations

import pytest

import gda.core.enums.location as location_enums
from gda.core.enums.location import (
    JurisdictionCategory,
    LocationType,
)

__version__ = "1.0.0+build.3"


# ==============================================================================
# GROUP 1: Smoke & Primary Entrypoints
# Note: Single smoke gate verifying gda.core.enums.location public exports.
# ==============================================================================


@pytest.mark.smoke
@pytest.mark.unit
def test_location_enums_exposes_expected_public_interface() -> None:
    """Verify gda.core.enums.location exports JurisdictionCategory and LocationType."""
    assert set(location_enums.__all__) == {"JurisdictionCategory", "LocationType"}


# ==============================================================================
# GROUP 2: Core Logic & Happy Paths
# Note: Canonical JurisdictionCategory and LocationType member sets.
# ==============================================================================


@pytest.mark.unit
def test_jurisdiction_category_canonical_members() -> None:
    """Verify JurisdictionCategory members evaluate to expected uppercase tokens."""
    assert JurisdictionCategory.COUNTRY == "COUNTRY"
    assert JurisdictionCategory.STATOID == "STATOID"
    assert JurisdictionCategory.COUNTY_EQUIVALENT == "COUNTY_EQUIVALENT"
    assert JurisdictionCategory.CIVIL_TOWNSHIP == "CIVIL_TOWNSHIP"
    assert JurisdictionCategory.MUNICIPALITY == "MUNICIPALITY"
    assert JurisdictionCategory.UNINCORPORATED_PLACE == "UNINCORPORATED_PLACE"
    assert JurisdictionCategory.SPECIAL_DISTRICT == "SPECIAL_DISTRICT"
    assert len(JurisdictionCategory) == 7


@pytest.mark.unit
def test_location_type_canonical_members() -> None:
    """Verify LocationType civil boundaries evaluate to expected uppercase tokens."""
    expected_types = {
        "CIVIL_JURISDICTION",
        "COUNTRY",
        "STATE",
        "COUNTY",
        "CITY",
        "TOWNSHIP",
        "PARISH",
        "WARD",
        "PRECINCT",
        "OTHER",
        "UNKNOWN",
    }
    assert {lt.value for lt in LocationType} == expected_types
    assert len(LocationType) == 11


# ==============================================================================
# GROUP 4: Error Handling & Validation Failures
# Note: Strict invalid-value rejection on location enums.
# ==============================================================================


@pytest.mark.regression
@pytest.mark.parametrize("bad_value", ["CEMETERY", "county", " STATE ", ""])
def test_location_type_rejects_invalid_and_untrimmed_values(bad_value: str) -> None:
    """Verify LocationType rejects non-jurisdiction venues, lowercase, and padded strings."""
    with pytest.raises(ValueError):
        LocationType(bad_value)


# ==============================================================================
# GROUP 6: Integrity & Invariants
# Note: Linear descending administrative_rank hierarchy invariant.
# ==============================================================================


@pytest.mark.integrity
@pytest.mark.unit
def test_jurisdiction_category_administrative_rank_hierarchy() -> None:
    """Verify administrative_rank property enforces linear descending hierarchy."""
    expected_ranks = {
        JurisdictionCategory.COUNTRY: 10,
        JurisdictionCategory.STATOID: 20,
        JurisdictionCategory.COUNTY_EQUIVALENT: 30,
        JurisdictionCategory.CIVIL_TOWNSHIP: 40,
        JurisdictionCategory.MUNICIPALITY: 50,
        JurisdictionCategory.UNINCORPORATED_PLACE: 60,
        JurisdictionCategory.SPECIAL_DISTRICT: 70,
    }
    for category, expected_rank in expected_ranks.items():
        assert category.administrative_rank == expected_rank

    ordered = list(expected_ranks.keys())
    assert [c.administrative_rank for c in ordered] == sorted(
        c.administrative_rank for c in ordered
    )
