"""Path: tests/test_gda/test_entity/test_facts/test_facts_errors.py

Comprehensive test suite verifying the Fact error hierarchy.
"""

from __future__ import annotations

import pytest

from gda.core.errors import GenealogyDeskError
from gda.entity.facts.errors import (
    FactError,
    FactNotFoundError,
    FactValidationError,
)

__version__ = "1.0.0+build.1"


@pytest.mark.unit
def test_fact_error_default_initialization_sets_canonical_code() -> None:
    """Verify FactError inherits from GenealogyDeskError and assigns default error code."""
    err = FactError("General fact error")

    assert isinstance(err, GenealogyDeskError)
    assert err.error_code == "ERR_FACT"
    assert err.message == "General fact error"
    assert err.details == {}


@pytest.mark.unit
def test_fact_not_found_error_custom_code_and_details_preserved() -> None:
    """Verify FactNotFoundError assigns specific error code and retains details payload."""
    details = {"fact_id": "FID-000123"}
    err = FactNotFoundError("Fact not found", details=details)

    assert isinstance(err, FactError)
    assert err.error_code == "ERR_FACT_NOT_FOUND"
    assert err.message == "Fact not found"
    assert err.details == details


@pytest.mark.regression
def test_fact_validation_error_custom_code_and_details_override() -> None:
    """Verify FactValidationError accepts custom error code and payload."""
    details = {"urn": "urn:invalid"}
    err = FactValidationError(
        "Invalid URN",
        error_code="ERR_CUSTOM_FACT_VALIDATION",
        details=details,
    )

    assert isinstance(err, FactError)
    assert err.error_code == "ERR_CUSTOM_FACT_VALIDATION"
    assert err.message == "Invalid URN"
    assert err.details == details
