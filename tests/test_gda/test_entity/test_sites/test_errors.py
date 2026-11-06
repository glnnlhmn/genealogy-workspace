"""Path: tests/test_gda/test_entity/test_sites/test_errors.py

Comprehensive test suite verifying the Site error hierarchy.
"""

from __future__ import annotations

import pytest

from gda.core.errors import GenealogyDeskError
from gda.entity.sites.errors import (
    SiteError,
    SiteNotFoundError,
    SiteValidationError,
)

__version__ = "1.0.0+build.1"

# ==============================================================================
# GROUP 1: SITE ERROR HIERARCHY & INITIALIZATION
# Note: Verifies exception inheritance, default error codes, and details payloads
# ==============================================================================


@pytest.mark.unit
def test_site_error_default_initialization_sets_canonical_code() -> None:
    """Verify SiteError inherits from GenealogyDeskError and assigns default error code."""
    err = SiteError("General site error")

    assert isinstance(err, GenealogyDeskError)
    assert err.error_code == "ERR_SITE"
    assert err.message == "General site error"
    assert err.details == {}


@pytest.mark.unit
def test_site_not_found_error_custom_code_and_details_preserved() -> None:
    """Verify SiteNotFoundError assigns specific error code and retains details payload."""
    details = {"site_id": "SID-000123"}
    err = SiteNotFoundError("Site not found", details=details)

    assert isinstance(err, SiteError)
    assert err.error_code == "ERR_SITE_NOT_FOUND"
    assert err.message == "Site not found"
    assert err.details == details


@pytest.mark.regression
def test_site_validation_error_custom_code_and_details_override() -> None:
    """Verify SiteValidationError accepts custom error code and payload."""
    details = {"urn": "urn:invalid"}
    err = SiteValidationError(
        "Invalid URN",
        error_code="ERR_CUSTOM_SITE_VALIDATION",
        details=details,
    )

    assert isinstance(err, SiteError)
    assert err.error_code == "ERR_CUSTOM_SITE_VALIDATION"
    assert err.message == "Invalid URN"
    assert err.details == details
