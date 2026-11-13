"""Path: tests/test_gda/test_core/test_enums/test_orgs.py

Atomized unit tests for gda.core.enums.orgs and OrganizationID.

Operational Role:
    Verifies enum member values, StrEnum string parity, and OrganizationID
    prefix enforcement ('ORG-######').
"""

from __future__ import annotations

import pytest

from gda.core.enums.core import SmartIDPrefix
from gda.core.enums.orgs import (
    AffiliationType,
    MembershipStatus,
    OrganizationCategory,
)
from gda.core.errors import ModelPrefixMismatchError
from gda.model.atom.id import OrganizationID

__version__ = "1.0.0+build.1"


@pytest.mark.unit
@pytest.mark.smoke
def test_orgs_enums_and_organization_id() -> None:
    """Verify OrganizationCategory, MembershipStatus, AffiliationType, and OrganizationID."""
    assert SmartIDPrefix.ORG == "ORG"
    assert SmartIDPrefix.ORG.value == "ORG"

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

    org_id = OrganizationID("ORG-000411")
    assert org_id == "ORG-000411"
    assert org_id.prefix == "ORG"
    assert org_id.suffix == "000411"

    with pytest.raises(ModelPrefixMismatchError):
        OrganizationID("IND-000411")
