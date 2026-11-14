"""Path: tests/test_gda/test_model/test_xref/test_individual_organization_xref.py

Comprehensive unit tests for gda.model.xref.individual_organization_xref.IndividualOrganizationXRef.

Operational Role:
    Exercises IndividualOrganizationXRef creation, OrganizationCategory,
    AffiliationType, and MembershipStatus enum resolution, HistoricalYear
    start/end temporal bounds and range validation, dynamic xref_key and
    sort_key ordering, dict/JSON round-trip serialization, and defensive
    validation boundaries.
"""

from __future__ import annotations

import pytest
from tests.test_gda.test_model.test_xref.conftest import assert_xref_contract

from gda.core.enums.orgs import (
    AffiliationType,
    MembershipStatus,
    OrganizationCategory,
)
from gda.core.errors import ModelFormatError, ModelPrefixMismatchError, ModelRangeError
from gda.model.atom.id import IndividualID, OrganizationID
from gda.model.atom.year import HistoricalYear
from gda.model.xref import IndividualOrganizationXRef

__version__ = "1.0.0+build.2"


@pytest.mark.unit
@pytest.mark.smoke
def test_individual_organization_xref_roundtrip_and_ordering(
    sample_individual_id: IndividualID,
) -> None:
    """Verify IndividualOrganizationXRef creation, dynamic keys, ordering, and serialization."""
    xref = IndividualOrganizationXRef.create(
        organization_id="  org-000005  ",
        individual_id="  ind-000010  ",
        org_category="  fraternal  ",
        affiliation_type="  officer  ",
        membership_status="  active  ",
        start_year=1875,
        end_year=1880,
    )

    assert_xref_contract(xref, IndividualOrganizationXRef)
    assert xref.organization_id == OrganizationID("ORG-000005")
    assert xref.individual_id == sample_individual_id
    assert xref.org_category is OrganizationCategory.FRATERNAL
    assert xref.affiliation_type is AffiliationType.OFFICER
    assert xref.membership_status is MembershipStatus.ACTIVE
    assert xref.start_year == HistoricalYear(1875)
    assert xref.end_year == HistoricalYear(1880)
    assert xref.xref_key == "ORG-000005::IND-000010::OFFICER"
    assert xref.sort_key == ("ORG-000005", 1875, 1880, "IND-000010", "OFFICER")
    assert (
        str(xref)
        == "IndividualOrganizationXRef [ORG-000005::IND-000010::OFFICER] (FRATERNAL/ACTIVE) [1875-1880]"
    )
    assert "IndividualOrganizationXRef(" in repr(xref)

    # Direct typed instances with start_year only and end_year only
    earlier = IndividualOrganizationXRef.create(
        organization_id=OrganizationID("ORG-000005"),
        individual_id=sample_individual_id,
        org_category=OrganizationCategory.FRATERNAL,
        affiliation_type=AffiliationType.MEMBER,
        membership_status=MembershipStatus.ACTIVE,
        start_year=HistoricalYear(1870),
    )
    assert (
        str(earlier)
        == "IndividualOrganizationXRef [ORG-000005::IND-000010::MEMBER] (FRATERNAL/ACTIVE) [1870-?]"
    )

    end_only = IndividualOrganizationXRef.create(
        organization_id=OrganizationID("ORG-000005"),
        individual_id=sample_individual_id,
        org_category=OrganizationCategory.FRATERNAL,
        end_year=HistoricalYear(1890),
    )
    assert (
        str(end_only)
        == "IndividualOrganizationXRef [ORG-000005::IND-000010::MEMBER] (FRATERNAL/ACTIVE) [?-1890]"
    )

    # Undated minimal instance
    undated = IndividualOrganizationXRef.create(
        organization_id="ORG-000005",
        individual_id="IND-000020",
        org_category=OrganizationCategory.RELIGIOUS,
    )
    assert (
        str(undated)
        == "IndividualOrganizationXRef [ORG-000005::IND-000020::MEMBER] (RELIGIOUS/ACTIVE)"
    )
    min_dict = undated.to_dict()
    assert "start_year" not in min_dict
    assert "end_year" not in min_dict
    assert IndividualOrganizationXRef.from_dict(min_dict) == undated

    # Deterministic ordering: earlier (1870) < xref (1875) < end_only (start=9999, end=1890) < undated
    assert earlier < xref < end_only < undated


@pytest.mark.unit
@pytest.mark.integrity
def test_individual_organization_xref_validation_errors() -> None:
    """Verify temporal range and format validation error branches for IndividualOrganizationXRef."""
    with pytest.raises(ModelPrefixMismatchError, match="expected 'ORG'"):
        IndividualOrganizationXRef.create(
            organization_id="IND-000001",
            individual_id="IND-000001",
            org_category=OrganizationCategory.CIVIC_SERVICE,
        )

    with pytest.raises(ModelPrefixMismatchError, match="expected 'IND'"):
        IndividualOrganizationXRef.create(
            organization_id="ORG-000001",
            individual_id="ORG-000002",
            org_category=OrganizationCategory.CIVIC_SERVICE,
        )

    with pytest.raises(ModelFormatError, match="Invalid OrganizationCategory value"):
        IndividualOrganizationXRef.create(
            organization_id="ORG-000001",
            individual_id="IND-000001",
            org_category="INVALID_CAT",
        )

    with pytest.raises(ModelFormatError, match="Invalid AffiliationType value"):
        IndividualOrganizationXRef.create(
            organization_id="ORG-000001",
            individual_id="IND-000001",
            org_category=OrganizationCategory.CIVIC_SERVICE,
            affiliation_type="INVALID_AFFILIATION",
        )

    with pytest.raises(ModelFormatError, match="Invalid MembershipStatus value"):
        IndividualOrganizationXRef.create(
            organization_id="ORG-000001",
            individual_id="IND-000001",
            org_category=OrganizationCategory.CIVIC_SERVICE,
            membership_status="INVALID_STATUS",
        )

    with pytest.raises(
        ModelRangeError,
        match="Affiliation end_year \\(1870\\) cannot precede start_year \\(1880\\)",
    ):
        IndividualOrganizationXRef.create(
            organization_id="ORG-000001",
            individual_id="IND-000001",
            org_category=OrganizationCategory.CIVIC_SERVICE,
            start_year=1880,
            end_year=1870,
        )

    with pytest.raises(ModelRangeError):
        IndividualOrganizationXRef.create(
            organization_id="ORG-000001",
            individual_id="IND-000001",
            org_category=OrganizationCategory.CIVIC_SERVICE,
            start_year=999,
        )

    with pytest.raises(ModelFormatError, match="requires 'organization_id'"):
        IndividualOrganizationXRef.from_dict({"organization_id": "ORG-000001"})
