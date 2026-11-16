"""Path: tests/test_gda/test_core/test_enums/test_military_enums.py

Unit test suite verifying gda.core.enums.military enumerations and re-exports.
"""

from __future__ import annotations

from enum import StrEnum

import pytest

import gda.core.enums as enums_pkg
import gda.core.enums.military as mil_enums

__version__ = "1.0.0+build.1"


@pytest.mark.unit
@pytest.mark.integrity
def test_military_enums_all_sorted_and_reexported() -> None:
    """Verify gda.core.enums.military.__all__ is sorted and re-exported from gda.core.enums."""
    assert mil_enums.__all__ == sorted(mil_enums.__all__)
    assert len(mil_enums.__all__) == 22

    for name in mil_enums.__all__:
        enum_cls = getattr(mil_enums, name)
        assert issubclass(enum_cls, StrEnum), f"{name} must be a StrEnum"
        assert getattr(enums_pkg, name) is enum_cls


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
