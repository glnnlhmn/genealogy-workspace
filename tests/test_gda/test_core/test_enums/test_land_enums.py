"""Path: tests/test_gda/test_core/test_enums/test_land_enums.py

Targeted behavioral test suite verifying real-property conveyance and land grant enums.

Operational Role:
    Validates gda.core.enums.land public exports, package re-export parity,
    DeedPartyRole and LandGrantBasis tokens, and strict invalid-value rejection.

Test Structure & Protocol:
    - Atomized & parametrized tests: 1:1 behavioral contract mapping.
    - Fully decorated: 5-marker taxonomy (smoke, unit, regression).
    - Dependencies: In-memory only; zero physical disk I/O.
"""

from __future__ import annotations

import pytest

import gda.core.enums as enums_pkg
import gda.core.enums.land as land_enums
from gda.core.enums.land import (
    DeedPartyRole,
    LandGrantBasis,
)

__version__ = "1.0.0+build.2"


# ==============================================================================
# GROUP 1: Smoke & Primary Entrypoints
# Note: Single smoke gate verifying sorted exports and package re-export parity.
# ==============================================================================


@pytest.mark.smoke
@pytest.mark.unit
def test_land_enums_exports_and_reexport_parity() -> None:
    """Verify gda.core.enums.land.__all__ is sorted and re-exported from gda.core.enums."""
    assert land_enums.__all__ == sorted(land_enums.__all__)
    assert set(land_enums.__all__) == {"DeedPartyRole", "LandGrantBasis"}
    for name in land_enums.__all__:
        assert getattr(enums_pkg, name) is getattr(land_enums, name)


# ==============================================================================
# GROUP 2: Core Logic & Happy Paths
# Note: Canonical UPPER_SNAKE_CASE members for deed roles and land grants.
# ==============================================================================


@pytest.mark.unit
def test_deed_party_role_and_land_grant_basis_tokens() -> None:
    """Verify DeedPartyRole and LandGrantBasis canonical tokens."""
    assert {m.value for m in DeedPartyRole} == {"GRANTOR", "GRANTEE"}
    assert {m.value for m in LandGrantBasis} == {
        "CASH_ENTRY",
        "HOMESTEAD",
        "BOUNTY_LAND",
        "PREEMPTION",
        "PROPRIETARY_GRANT",
        "OTHER",
    }


# ==============================================================================
# GROUP 4: Error Handling & Validation Failures
# Note: Strict invalid-value rejection on land enums.
# ==============================================================================


@pytest.mark.regression
@pytest.mark.parametrize("bad_value", ["BUYER", "grantor", " GRANTEE ", ""])
def test_deed_party_role_rejects_invalid_values(bad_value: str) -> None:
    """Verify DeedPartyRole strictly rejects unregistered, lowercase, and padded tokens."""
    with pytest.raises(ValueError):
        DeedPartyRole(bad_value)
