"""Path: tests/test_gda/test_entity/test_organizations/test_organizations_errors.py

Comprehensive test suite verifying the Organization error hierarchy.
"""

from __future__ import annotations

import pytest

from gda.core.errors import GenealogyDeskError
from gda.entity.organizations.errors import (
    OrganizationError,
    OrganizationHierarchyError,
    OrganizationNotFoundError,
    OrganizationValidationError,
)

__version__ = "1.0.0+build.1"


@pytest.mark.unit
def test_organization_error_default_initialization_sets_canonical_code() -> None:
    """Verify OrganizationError inherits from GenealogyDeskError and assigns default error code."""
    err = OrganizationError("General organization error")

    assert isinstance(err, GenealogyDeskError)
    assert err.error_code == "ERR_ORG"
    assert err.message == "General organization error"
    assert err.details == {}


@pytest.mark.unit
def test_organization_not_found_error_custom_code_and_details_preserved() -> None:
    """Verify OrganizationNotFoundError assigns specific error code and retains details payload."""
    details = {"org_id": "ORG-000123"}
    err = OrganizationNotFoundError("Organization not found", details=details)

    assert isinstance(err, OrganizationError)
    assert err.error_code == "ERR_ORG_NOT_FOUND"
    assert err.message == "Organization not found"
    assert err.details == details


@pytest.mark.unit
def test_organization_hierarchy_error_default_and_custom_details() -> None:
    """Verify OrganizationHierarchyError assigns ERR_ORG_HIERARCHY and retains details."""
    details = {"parent_org_id": "ORG-000001"}
    err = OrganizationHierarchyError("Parent mismatch", details=details)

    assert isinstance(err, OrganizationError)
    assert err.error_code == "ERR_ORG_HIERARCHY"
    assert err.message == "Parent mismatch"
    assert err.details == details


@pytest.mark.regression
def test_organization_validation_error_custom_code_and_details_override() -> None:
    """Verify OrganizationValidationError accepts custom error code and payload."""
    details = {"urn": "urn:invalid"}
    err = OrganizationValidationError(
        "Invalid URN",
        error_code="ERR_CUSTOM_ORG_VALIDATION",
        details=details,
    )

    assert isinstance(err, OrganizationError)
    assert err.error_code == "ERR_CUSTOM_ORG_VALIDATION"
    assert err.message == "Invalid URN"
    assert err.details == details
