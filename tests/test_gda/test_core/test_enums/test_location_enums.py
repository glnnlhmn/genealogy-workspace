"""Path: tests/test_gda/test_core/test_enums/test_location_enums.py

Targeted behavioral test suite verifying location and administrative enums.

Operational Role:
    Validates civil administrative jurisdictions (JurisdictionCategory),
    hierarchical ranking calculations, and spatial place classifications (LocationType)
    with 100% statement and branch coverage.

Test Structure & Protocol:
    - Atomized tests: 1:1 verification per behavioral contract.
    - Fully decorated: Explicitly decorated with registered pytest markers.
    - Dependencies: In-memory only; zero physical disk I/O.
"""

from __future__ import annotations

import pytest

from gda.core.enums.location import (
    JurisdictionCategory,
    LocationType,
)

__version__ = "1.0.0+build.2"


# ==============================================================================
# GROUP 1: JurisdictionCategory Classifications & Administrative Ranking
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_jurisdiction_category_canonical_members() -> None:
    """Verify JurisdictionCategory members evaluate to expected string values."""
    assert JurisdictionCategory.COUNTRY == "COUNTRY"
    assert JurisdictionCategory.STATOID == "STATOID"
    assert JurisdictionCategory.COUNTY_EQUIVALENT == "COUNTY_EQUIVALENT"
    assert JurisdictionCategory.CIVIL_TOWNSHIP == "CIVIL_TOWNSHIP"
    assert JurisdictionCategory.MUNICIPALITY == "MUNICIPALITY"
    assert JurisdictionCategory.UNINCORPORATED_PLACE == "UNINCORPORATED_PLACE"
    assert JurisdictionCategory.SPECIAL_DISTRICT == "SPECIAL_DISTRICT"
    assert len(JurisdictionCategory) == 7


@pytest.mark.unit
@pytest.mark.regression
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

    assert (
        JurisdictionCategory.COUNTRY.administrative_rank
        < JurisdictionCategory.STATOID.administrative_rank
        < JurisdictionCategory.COUNTY_EQUIVALENT.administrative_rank
        < JurisdictionCategory.CIVIL_TOWNSHIP.administrative_rank
        < JurisdictionCategory.MUNICIPALITY.administrative_rank
        < JurisdictionCategory.UNINCORPORATED_PLACE.administrative_rank
        < JurisdictionCategory.SPECIAL_DISTRICT.administrative_rank
    )


# ==============================================================================
# GROUP 2: LocationType Geographic Jurisdictions
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
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
