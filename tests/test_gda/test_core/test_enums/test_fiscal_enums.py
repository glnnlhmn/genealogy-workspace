"""Path: tests/test_gda/test_core/test_enums/test_fiscal_enums.py

Targeted behavioral test suite verifying economic, tenure, and directory enums.

Operational Role:
    Validates gda.core.enums.fiscal public exports, historical tax classifications,
    property tenure conditions, citizenship statuses, and directory occupancy
    statuses using canonical UPPER_SNAKE_CASE tokens.

Test Structure & Protocol:
    - Atomized & parametrized tests: 1:1 behavioral contract mapping.
    - Fully decorated: 5-marker taxonomy (smoke, unit, regression).
    - Dependencies: In-memory only; zero physical disk I/O.
"""

from __future__ import annotations

import pytest

import gda.core.enums.fiscal as fiscal_enums
from gda.core.enums.fiscal import (
    CitizenshipStatus,
    HomeOwnership,
    ResidentialStatus,
    TaxpayerClassification,
)

__version__ = "1.0.0+build.3"


# ==============================================================================
# GROUP 1: Smoke & Primary Entrypoints
# Note: Single smoke gate verifying gda.core.enums.fiscal public exports.
# ==============================================================================


@pytest.mark.smoke
@pytest.mark.unit
def test_fiscal_enums_exposes_expected_public_interface() -> None:
    """Verify gda.core.enums.fiscal exports all 4 fiscal and tenure enum classes."""
    expected = {
        "CitizenshipStatus",
        "HomeOwnership",
        "ResidentialStatus",
        "TaxpayerClassification",
    }
    assert set(fiscal_enums.__all__) == expected


# ==============================================================================
# GROUP 2: Core Logic & Happy Paths
# Note: UPPER_SNAKE_CASE canonical tokens across all 4 fiscal enums (Phase 3).
# ==============================================================================


@pytest.mark.unit
def test_taxpayer_classification_upper_snake_case_tokens() -> None:
    """Verify TaxpayerClassification uses UPPER_SNAKE_CASE tokens (Phase 3 TDD Red)."""
    assert TaxpayerClassification.FREEHOLDER == "FREEHOLDER"
    assert TaxpayerClassification.TENANT == "TENANT"
    assert TaxpayerClassification.SINGLE_FREEMAN == "SINGLE_FREEMAN"
    assert TaxpayerClassification.INMATE == "INMATE"
    assert TaxpayerClassification.WIDOW == "WIDOW"


@pytest.mark.unit
def test_home_ownership_upper_snake_case_tokens() -> None:
    """Verify HomeOwnership uses UPPER_SNAKE_CASE tokens (Phase 3 TDD Red)."""
    assert HomeOwnership.OWNED == "OWNED"
    assert HomeOwnership.RENTED == "RENTED"
    assert HomeOwnership.FREE == "FREE"
    assert HomeOwnership.MORTGAGED == "MORTGAGED"
    assert HomeOwnership.UNKNOWN == "UNKNOWN"


@pytest.mark.unit
def test_citizenship_status_upper_snake_case_tokens() -> None:
    """Verify CitizenshipStatus uses UPPER_SNAKE_CASE tokens (Phase 3 TDD Red)."""
    assert CitizenshipStatus.NATIVE_BORN == "NATIVE_BORN"
    assert CitizenshipStatus.NATURALIZED == "NATURALIZED"
    assert CitizenshipStatus.ALIEN == "ALIEN"
    assert CitizenshipStatus.DECLARANT == "DECLARANT"
    assert CitizenshipStatus.NON_DECLARANT == "NON_DECLARANT"


@pytest.mark.unit
def test_residential_status_upper_snake_case_tokens() -> None:
    """Verify ResidentialStatus uses UPPER_SNAKE_CASE tokens (Phase 3 TDD Red)."""
    assert ResidentialStatus.HOUSEHOLDER == "HOUSEHOLDER"
    assert ResidentialStatus.BOARDER == "BOARDER"
    assert ResidentialStatus.ROOMS == "ROOMS"
    assert ResidentialStatus.TENANT == "TENANT"
    assert ResidentialStatus.WIDOW == "WIDOW"


# ==============================================================================
# GROUP 4: Error Handling & Validation Failures
# Note: Strict invalid-value rejection on fiscal enums.
# ==============================================================================


@pytest.mark.regression
@pytest.mark.parametrize("bad_value", ["INVALID", "freeholder", " TENANT ", ""])
def test_taxpayer_classification_rejects_invalid_values(bad_value: str) -> None:
    """Verify TaxpayerClassification rejects unregistered, lowercase, and padded tokens."""
    with pytest.raises(ValueError):
        TaxpayerClassification(bad_value)
