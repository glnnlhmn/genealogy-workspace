"""Path: tests/test_gda/test_core/test_enums/test_orgs_enums.py

Targeted behavioral test suite verifying organizational affiliation enums.

Operational Role:
    Verifies OrganizationCategory, MembershipStatus, and AffiliationType
    enum member values, StrEnum string parity, and export parity.
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

__version__ = "1.0.0+build.2"


@pytest.mark.unit
@pytest.mark.smoke
def test_orgs_enums_canonical_members_and_reexports() -> None:
    """Verify OrganizationCategory, MembershipStatus, and AffiliationType members."""
    assert orgs_enums.__all__ == sorted(orgs_enums.__all__)
    for name in orgs_enums.__all__:
        assert getattr(enums_pkg, name) is getattr(orgs_enums, name)

    assert OrganizationCategory.FRATERNAL == "FRATERNAL"
    assert OrganizationCategory.RELIGIOUS == "RELIGIOUS"
    assert OrganizationCategory.CULTURAL_ARTS == "CULTURAL_ARTS"
    assert OrganizationCategory.CIVIC_SERVICE == "CIVIC_SERVICE"
    assert OrganizationCategory.LABOR_GUILD == "LABOR_GUILD"
    assert OrganizationCategory.VETERANS == "VETERANS"
    assert OrganizationCategory.MUTUAL_AID == "MUTUAL_AID"
    assert OrganizationCategory.EDUCATIONAL == "EDUCATIONAL"
    assert OrganizationCategory.POLITICAL == "POLITICAL"
    assert OrganizationCategory.OTHER == "OTHER"
    assert len(OrganizationCategory) == 10

    assert MembershipStatus.ACTIVE == "ACTIVE"
    assert MembershipStatus.CHARTER == "CHARTER"
    assert MembershipStatus.INITIATED == "INITIATED"
    assert MembershipStatus.DEMITTED == "DEMITTED"
    assert MembershipStatus.SUSPENDED == "SUSPENDED"
    assert MembershipStatus.EXPELLED == "EXPELLED"
    assert MembershipStatus.INACTIVE == "INACTIVE"
    assert MembershipStatus.DECEASED == "DECEASED"
    assert MembershipStatus.HONORARY == "HONORARY"
    assert MembershipStatus.UNKNOWN == "UNKNOWN"
    assert len(MembershipStatus) == 10

    assert AffiliationType.MEMBER == "MEMBER"
    assert AffiliationType.OFFICER == "OFFICER"
    assert AffiliationType.CLERGY_MINISTER == "CLERGY_MINISTER"
    assert AffiliationType.DIRECTOR_LEADER == "DIRECTOR_LEADER"
    assert AffiliationType.CANDIDATE_NOVICE == "CANDIDATE_NOVICE"
    assert AffiliationType.BENEFACTOR_PATRON == "BENEFACTOR_PATRON"
    assert AffiliationType.GUEST_VISITOR == "GUEST_VISITOR"
    assert AffiliationType.OTHER == "OTHER"
    assert len(AffiliationType) == 8
