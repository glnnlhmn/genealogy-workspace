"""Path: tests/test_gda/test_core/test_enums/test_land_enums.py

Targeted behavioral test suite verifying real-property conveyance and land grant enums.

Operational Role:
    Validates DeedPartyRole and LandGrantBasis enum member tokens,
    StrEnum inheritance, and package re-export parity.
"""

from __future__ import annotations

import pytest

import gda.core.enums as enums_pkg
import gda.core.enums.land as land_enums
from gda.core.enums.land import (
    DeedPartyRole,
    LandGrantBasis,
)

__version__ = "1.0.0+build.1"


@pytest.mark.unit
@pytest.mark.smoke
def test_deed_party_role_and_land_grant_basis_tokens() -> None:
    """Verify DeedPartyRole and LandGrantBasis canonical tokens and package re-exports."""
    assert land_enums.__all__ == sorted(land_enums.__all__)
    for name in land_enums.__all__:
        assert getattr(enums_pkg, name) is getattr(land_enums, name)

    assert DeedPartyRole.GRANTOR == "GRANTOR"
    assert DeedPartyRole.GRANTEE == "GRANTEE"
    assert len(DeedPartyRole) == 2

    assert LandGrantBasis.CASH_ENTRY == "CASH_ENTRY"
    assert LandGrantBasis.HOMESTEAD == "HOMESTEAD"
    assert LandGrantBasis.BOUNTY_LAND == "BOUNTY_LAND"
    assert LandGrantBasis.PREEMPTION == "PREEMPTION"
    assert LandGrantBasis.PROPRIETARY_GRANT == "PROPRIETARY_GRANT"
    assert LandGrantBasis.OTHER == "OTHER"
    assert len(LandGrantBasis) == 6
