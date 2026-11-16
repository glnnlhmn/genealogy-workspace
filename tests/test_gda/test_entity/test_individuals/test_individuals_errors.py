"""Path: tests/test_gda/test_entity/test_individuals/test_individuals_errors.py

Comprehensive test suite verifying the Individual error hierarchy.
"""

from __future__ import annotations

import pytest

from gda.core.errors import GenealogyDeskError
from gda.entity.individuals.errors import (
    IndividualError,
    IndividualNotFoundError,
    IndividualValidationError,
)

__version__ = "1.0.0+build.1"


@pytest.mark.unit
def test_individual_error_default_initialization_sets_canonical_code() -> None:
    """Verify IndividualError inherits from GenealogyDeskError and assigns default error code."""
    err = IndividualError("General individual error")

    assert isinstance(err, GenealogyDeskError)
    assert err.error_code == "ERR_IND"
    assert err.message == "General individual error"
    assert err.details == {}


@pytest.mark.unit
def test_individual_not_found_error_custom_code_and_details_preserved() -> None:
    """Verify IndividualNotFoundError assigns specific error code and retains details payload."""
    details = {"individual_id": "IND-000123"}
    err = IndividualNotFoundError("Individual not found", details=details)

    assert isinstance(err, IndividualError)
    assert err.error_code == "ERR_IND_NOT_FOUND"
    assert err.message == "Individual not found"
    assert err.details == details


@pytest.mark.regression
def test_individual_validation_error_custom_code_and_details_override() -> None:
    """Verify IndividualValidationError accepts custom error code and payload."""
    details = {"urn": "urn:invalid"}
    err = IndividualValidationError(
        "Invalid URN",
        error_code="ERR_CUSTOM_IND_VALIDATION",
        details=details,
    )

    assert isinstance(err, IndividualError)
    assert err.error_code == "ERR_CUSTOM_IND_VALIDATION"
    assert err.message == "Invalid URN"
    assert err.details == details
