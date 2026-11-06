"""Path: tests/test_gda/test_enums/test_fiscal_enums.py

Targeted behavioral test suite verifying economic, tenure, and directory enums.

Operational Role:
    Validates historical tax classifications, property tenure conditions,
    citizenship statuses, and directory occupancy statuses.

Test Structure & Protocol:
    - Atomized tests: 1:1 verification per behavioral contract.
    - Fully decorated: Explicitly decorated with registered pytest markers.
    - Dependencies: In-memory only; zero physical disk I/O.
"""

from __future__ import annotations

import pytest

from gda.enums.fiscal import (
    CitizenshipStatus,
    HomeOwnership,
    ResidentialStatus,
    TaxpayerClassification,
)

__version__ = "0.1.0+build.1"

# ==============================================================================
# GROUP 1: Taxpayer & Property Tenure Classifications
# Note: Verification of TaxpayerClassification and HomeOwnership
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_taxpayer_classification_tokens() -> None:
    """Verify TaxpayerClassification tokens match historical tax schedules."""
    assert TaxpayerClassification.FREEHOLDER == "Freeholder"
    assert TaxpayerClassification.TENANT == "Tenant"
    assert TaxpayerClassification.SINGLE_FREEMAN == "Single Freeman"
    assert TaxpayerClassification.INMATE == "Inmate"
    assert TaxpayerClassification.WIDOW == "Widow"


@pytest.mark.unit
def test_home_ownership_tokens() -> None:
    """Verify HomeOwnership tenure classifications."""
    assert HomeOwnership.OWNED == "Owned"
    assert HomeOwnership.RENTED == "Rented"
    assert HomeOwnership.FREE == "Free"
    assert HomeOwnership.MORTGAGED == "Mortgaged"
    assert HomeOwnership.UNKNOWN == "Unknown"


# ==============================================================================
# GROUP 2: Citizenship & Directory Residential Statuses
# Note: Verification of CitizenshipStatus and ResidentialStatus
# ==============================================================================


@pytest.mark.unit
def test_citizenship_status_tokens() -> None:
    """Verify CitizenshipStatus legal residency and naturalization tokens."""
    assert CitizenshipStatus.NATIVE_BORN == "Native Born"
    assert CitizenshipStatus.NATURALIZED == "Naturalized"
    assert CitizenshipStatus.ALIEN == "Alien"
    assert CitizenshipStatus.DECLARANT == "Declarant"
    assert CitizenshipStatus.NON_DECLARANT == "Non-Declarant"


@pytest.mark.unit
def test_residential_status_tokens() -> None:
    """Verify ResidentialStatus city and business directory strings."""
    assert ResidentialStatus.HOUSEHOLDER == "Householder"
    assert ResidentialStatus.BOARDER == "Boarder"
    assert ResidentialStatus.ROOMS == "Rooms"
    assert ResidentialStatus.TENANT == "Tenant"
    assert ResidentialStatus.WIDOW == "Widow"
