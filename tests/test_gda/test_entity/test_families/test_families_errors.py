"""Path: tests/test_gda/test_entity/test_families/test_families_errors.py

Comprehensive test suite verifying the Family error hierarchy.
"""

from __future__ import annotations

import pytest

from gda.core.errors import GenealogyDeskError
from gda.entity.families.errors import (
    FamilyError,
    FamilyNotFoundError,
    FamilyValidationError,
)

__version__ = "1.0.0+build.1"


@pytest.mark.unit
def test_family_error_default_initialization_sets_canonical_code() -> None:
    """Verify FamilyError inherits from GenealogyDeskError and assigns default error code."""
    err = FamilyError("General family error")

    assert isinstance(err, GenealogyDeskError)
    assert err.error_code == "ERR_FAM"
    assert err.message == "General family error"
    assert err.details == {}


@pytest.mark.unit
def test_family_not_found_error_custom_code_and_details_preserved() -> None:
    """Verify FamilyNotFoundError assigns specific error code and retains details payload."""
    details = {"family_id": "FAM-000123"}
    err = FamilyNotFoundError("Family not found", details=details)

    assert isinstance(err, FamilyError)
    assert err.error_code == "ERR_FAM_NOT_FOUND"
    assert err.message == "Family not found"
    assert err.details == details


@pytest.mark.regression
def test_family_validation_error_custom_code_and_details_override() -> None:
    """Verify FamilyValidationError accepts custom error code and payload."""
    details = {"urn": "urn:invalid"}
    err = FamilyValidationError(
        "Invalid URN",
        error_code="ERR_CUSTOM_FAM_VALIDATION",
        details=details,
    )

    assert isinstance(err, FamilyError)
    assert err.error_code == "ERR_CUSTOM_FAM_VALIDATION"
    assert err.message == "Invalid URN"
    assert err.details == details
