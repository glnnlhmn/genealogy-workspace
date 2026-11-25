"""Path: tests/test_gda/test_core/test_enums/test_military_enums.py

Targeted behavioral test suite verifying gda.core.enums.military enumerations.

Operational Role:
    Validates the 25 authoritative military enums in gda.core.enums.military,
    including package re-export parity, canonical members across all 5 military
    subdomains, and the 3 enums relocated from archival.py and sources.py
    (WwiCardType, MilitaryDraftType, MilitaryWar).

Test Structure & Protocol:
    - Atomized & parametrized tests: 1:1 behavioral contract mapping.
    - Fully decorated: 5-marker taxonomy (smoke, unit, regression, integrity).
    - Dependencies: In-memory only; zero physical disk I/O.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

import pytest

import gda.core.enums as enums_pkg
import gda.core.enums.military as mil_enums

__version__ = "1.0.0+build.2"


# ==============================================================================
# GROUP 1: Smoke & Primary Entrypoints
# Note: Single smoke gate freezing the 25 sorted military exports (Phase 3).
# ==============================================================================


@pytest.mark.smoke
@pytest.mark.integrity
@pytest.mark.unit
def test_military_enums_all_sorted_and_reexported() -> None:
    """Verify gda.core.enums.military.__all__ has 25 sorted symbols re-exported (Phase 3)."""
    assert mil_enums.__all__ == sorted(mil_enums.__all__)
    assert len(mil_enums.__all__) == 25

    for name in mil_enums.__all__:
        enum_cls = getattr(mil_enums, name)
        assert issubclass(enum_cls, StrEnum), f"{name} must be a StrEnum"
        assert getattr(enums_pkg, name) is enum_cls


# ==============================================================================
# GROUP 2: Core Logic & Happy Paths
# Note: Canonical members across all 5 military subdomains + relocated enums.
# ==============================================================================


@pytest.mark.unit
def test_military_enum_canonical_members() -> None:
    """Verify canonical members across all 5 military subdomains."""
    assert mil_enums.MilitaryBranch.ARMY == "ARMY"
    assert mil_enums.ServiceComponent.REGULAR == "REGULAR"
    assert mil_enums.SeparationCharacter.HONORABLE == "HONORABLE"
    assert mil_enums.MusterRollType.MUSTER_IN == "MUSTER_IN"
    assert mil_enums.SeparationFormType.DD_214 == "DD_214"

    assert mil_enums.MilitaryAwardTier.MEDAL_OF_HONOR == "MEDAL_OF_HONOR"
    assert mil_enums.AwardScope.VALOR_IN_COMBAT == "VALOR_IN_COMBAT"

    assert mil_enums.CasualtyCategory.KILLED_IN_ACTION == "KILLED_IN_ACTION"
    assert mil_enums.PowCampType.OFFICER_CAMP == "OFFICER_CAMP"
    assert mil_enums.IntermentCemeteryType.NATIONAL_CEMETERY == "NATIONAL_CEMETERY"

    assert mil_enums.PensionClaimantRole.VETERAN == "VETERAN"
    assert mil_enums.PensionPaymentAuthority.US_BUREAU_OF_PENSIONS == "US_BUREAU_OF_PENSIONS"
    assert mil_enums.BountyLandAct.ACT_OF_1855 == "ACT_OF_1855"

    assert mil_enums.DraftCardTier.WWI_FIRST == "WWI_FIRST"
    assert mil_enums.ColonialWarPeriod.REVOLUTIONARY_WAR == "REVOLUTIONARY_WAR"
    assert mil_enums.ColonialMilitiaClass.TRAINBAND == "TRAINBAND"
    assert mil_enums.CivilWarConscriptionAllegiance.UNION == "UNION"
    assert mil_enums.CivilWarEnrollmentClass.CLASS_1 == "CLASS_1"
    assert mil_enums.WwiCitizenshipStatus.NATIVE_BORN == "NATIVE_BORN"
    assert mil_enums.WwiiDraftWave.FIRST == "FIRST"
    assert mil_enums.ModernDraftEra.POST_1980_REGISTRATION == "POST_1980_REGISTRATION"
    assert mil_enums.SssClassification.ONE_A == "1-A"


@pytest.mark.unit
def test_relocated_military_enums_in_military_module() -> None:
    """Verify WwiCardType, MilitaryDraftType, and MilitaryWar live in military (Phase 3)."""
    wwi_card: Any = getattr(mil_enums, "WwiCardType", None)
    draft_type: Any = getattr(mil_enums, "MilitaryDraftType", None)
    military_war: Any = getattr(mil_enums, "MilitaryWar", None)

    assert wwi_card is not None, "WwiCardType not yet relocated to military.py"
    assert draft_type is not None, "MilitaryDraftType not yet relocated to military.py"
    assert military_war is not None, "MilitaryWar not yet relocated to military.py"

    assert wwi_card.CARD_A == "CARD_A"
    assert wwi_card.CARD_B == "CARD_B"
    assert wwi_card.CARD_C == "CARD_C"
    assert wwi_card.UNKNOWN == "UNKNOWN"
    assert draft_type.DRAFT_REGISTRATION == "DRAFT_REGISTRATION"
    assert military_war.CIVIL_WAR == "CIVIL_WAR"
    assert military_war.WWI == "WWI"
    assert military_war.WWII == "WWII"


# ==============================================================================
# GROUP 4: Error Handling & Validation Failures
# Note: Strict invalid-value rejection on military enums.
# ==============================================================================


@pytest.mark.regression
@pytest.mark.parametrize("bad_value", ["SPACE_FORCE_INVALID", "army", " NAVY ", ""])
def test_military_branch_rejects_invalid_values(bad_value: str) -> None:
    """Verify MilitaryBranch strictly rejects unregistered, lowercase, and padded tokens."""
    with pytest.raises(ValueError):
        mil_enums.MilitaryBranch(bad_value)
