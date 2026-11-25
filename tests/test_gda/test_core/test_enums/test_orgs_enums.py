"""Path: tests/test_gda/test_core/test_enums/test_orgs_enums.py

Targeted behavioral test suite verifying organizational affiliation enums.

Operational Role:
    Verifies gda.core.enums.orgs public exports, package re-export parity,
    OrganizationCategory, MembershipStatus, and AffiliationType member tokens,
    and strict invalid-value rejection.

Test Structure & Protocol:
    - Atomized & parametrized tests: 1:1 behavioral contract mapping.
    - Fully decorated: 5-marker taxonomy (smoke, unit, regression).
    - Dependencies: In-memory only; zero physical disk I/O.
"""

from __future__ import annotations

import pytest

import gda.core.enums as enums_pkg
import gda.core.enums.orgs as orgs_enums
from gda.core.enums.orgs import (
    AffiliationType,
    MembershipStatus,
    OrganizationCategory,
)

__version__ = "1.0.0+build.3"


# ==============================================================================
# GROUP 1: Smoke & Primary Entrypoints
# Note: Single smoke gate verifying sorted exports and package re-export parity.
# ==============================================================================


@pytest.mark.smoke
@pytest.mark.unit
def test_orgs_enums_exports_and_reexport_parity() -> None:
    """Verify gda.core.enums.orgs.__all__ is sorted and re-exported from gda.core.enums."""
    assert orgs_enums.__all__ == sorted(orgs_enums.__all__)
    assert set(orgs_enums.__all__) == {
        "AffiliationType",
        "MembershipStatus",
        "OrganizationCategory",
    }
    for name in orgs_enums.__all__:
        assert getattr(enums_pkg, name) is getattr(orgs_enums, name)


# ==============================================================================
# GROUP 2: Core Logic & Happy Paths
# Note: Canonical UPPER_SNAKE_CASE members across all 3 organization enums.
# ==============================================================================


@pytest.mark.unit
def test_orgs_enums_canonical_members() -> None:
    """Verify OrganizationCategory, MembershipStatus, and AffiliationType members."""
    assert {m.value for m in OrganizationCategory} == {
        "FRATERNAL",
        "RELIGIOUS",
        "CULTURAL_ARTS",
        "CIVIC_SERVICE",
        "LABOR_GUILD",
        "VETERANS",
        "MUTUAL_AID",
        "EDUCATIONAL",
        "POLITICAL",
        "OTHER",
    }
    assert {m.value for m in MembershipStatus} == {
        "ACTIVE",
        "CHARTER",
        "INITIATED",
        "DEMITTED",
        "SUSPENDED",
        "EXPELLED",
        "INACTIVE",
        "DECEASED",
        "HONORARY",
        "UNKNOWN",
    }
    assert {m.value for m in AffiliationType} == {
        "MEMBER",
        "OFFICER",
        "CLERGY_MINISTER",
        "DIRECTOR_LEADER",
        "CANDIDATE_NOVICE",
        "BENEFACTOR_PATRON",
        "GUEST_VISITOR",
        "OTHER",
    }


# ==============================================================================
# GROUP 4: Error Handling & Validation Failures
# Note: Strict invalid-value rejection on organization enums.
# ==============================================================================


@pytest.mark.regression
@pytest.mark.parametrize("bad_value", ["CLUB", "fraternal", " RELIGIOUS ", ""])
def test_organization_category_rejects_invalid_values(bad_value: str) -> None:
    """Verify OrganizationCategory strictly rejects unregistered and untrimmed tokens."""
    with pytest.raises(ValueError):
        OrganizationCategory(bad_value)
