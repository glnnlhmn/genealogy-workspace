"""Path: tests/test_gda/test_model/test_military/test_military_topology.py

Architectural topology and re-export verification suite for gda.model.military.

Operational Role:
    Verifies that all military record domains (draft, service, pension, casualty, awards)
    export canonical entities cleanly without circular imports or __all__ drift.
"""

from __future__ import annotations

import inspect
from pathlib import Path

import pytest

import gda.model.military as military_root
import gda.model.military.awards as awards_mod
import gda.model.military.casualty as casualty_mod
import gda.model.military.draft as draft_mod
import gda.model.military.pension as pension_mod
import gda.model.military.service as service_mod
from gda.model.military import (
    AwardScope,
    BountyLandAct,
    BountyLandWarrantRecord,
    CasualtyCategory,
    CivilWarConscriptionAllegiance,
    CivilWarDraftRecord,
    CivilWarEnrollmentClass,
    ColonialMilitiaClass,
    ColonialMilitiaRecord,
    ColonialWarPeriod,
    CombatCasualtyRecord,
    DraftCardTier,
    EnlistmentMusterRecord,
    IntermentCemeteryType,
    MilitaryAwardRecord,
    MilitaryAwardTier,
    MilitaryBranch,
    MilitaryBurialRecord,
    MilitaryCasualtyRecord,
    MilitaryDraftRecord,
    MilitaryPensionRecord,
    MilitaryServiceRecord,
    ModernDraftEra,
    ModernSelectiveServiceRecord,
    MusterRollType,
    PensionClaimantRole,
    PensionPaymentAuthority,
    PensionVeteranClaimRecord,
    PensionWidowDependentRecord,
    PowCampType,
    PrisonerOfWarRecord,
    SeparationCharacter,
    SeparationDischargeRecord,
    SeparationFormType,
    ServiceComponent,
    SssClassification,
    WwiCitizenshipStatus,
    WwiDraftCardRecord,
    WwiiDraftCardRecord,
    WwiiDraftWave,
)

__version__ = "1.0.0+build.3"


# ==============================================================================
# GROUP 1: INTEGRITY & EXPORT CONSISTENCY
# ==============================================================================


@pytest.mark.integrity
def test_military_root_reexports_match_subpackages() -> None:
    """Verify military root re-exports encapsulate subpackages without drift."""
    subpackages = [draft_mod, service_mod, pension_mod, casualty_mod, awards_mod]
    accumulated_sub_all: set[str] = set()

    for mod in subpackages:
        assert hasattr(mod, "__all__"), f"Module {mod.__name__} missing __all__"
        accumulated_sub_all.update(mod.__all__)

    root_all = set(military_root.__all__)
    missing_in_root = accumulated_sub_all - root_all
    assert not missing_in_root, (
        f"Symbols missing from military root __all__: {missing_in_root}"
    )


@pytest.mark.integrity
def test_military_canonical_entities_instantiable() -> None:
    """Verify all primary domain entities are exposed at military root namespace."""
    expected_entities = [
        # Draft
        MilitaryDraftRecord,
        ColonialMilitiaRecord,
        CivilWarDraftRecord,
        WwiDraftCardRecord,
        WwiiDraftCardRecord,
        ModernSelectiveServiceRecord,
        # Service
        MilitaryServiceRecord,
        EnlistmentMusterRecord,
        SeparationDischargeRecord,
        # Pension
        MilitaryPensionRecord,
        PensionVeteranClaimRecord,
        PensionWidowDependentRecord,
        BountyLandWarrantRecord,
        # Casualty
        MilitaryCasualtyRecord,
        CombatCasualtyRecord,
        PrisonerOfWarRecord,
        MilitaryBurialRecord,
        # Awards
        MilitaryAwardRecord,
    ]
    for cls in expected_entities:
        assert hasattr(military_root, cls.__name__)
        assert inspect.isclass(cls)


@pytest.mark.integrity
def test_military_enums_values_and_members() -> None:
    """Verify canonical enum invariants across all five domains."""
    # Awards
    assert MilitaryAwardTier.MEDAL_OF_HONOR == "MEDAL_OF_HONOR"
    assert AwardScope.VALOR_IN_COMBAT == "VALOR_IN_COMBAT"

    # Casualty
    assert CasualtyCategory.KILLED_IN_ACTION == "KILLED_IN_ACTION"
    assert PowCampType.OFFICER_CAMP == "OFFICER_CAMP"
    assert IntermentCemeteryType.NATIONAL_CEMETERY == "NATIONAL_CEMETERY"

    # Pension
    assert PensionClaimantRole.VETERAN == "VETERAN"
    assert PensionPaymentAuthority.US_BUREAU_OF_PENSIONS == "US_BUREAU_OF_PENSIONS"
    assert BountyLandAct.ACT_OF_1855 == "ACT_OF_1855"

    # Service
    assert MilitaryBranch.ARMY == "ARMY"
    assert ServiceComponent.REGULAR == "REGULAR"
    assert SeparationCharacter.HONORABLE == "HONORABLE"
    assert SeparationFormType.DD_214 == "DD_214"
    assert MusterRollType.MUSTER_IN == "MUSTER_IN"

    # Draft
    assert DraftCardTier.FIRST_REGISTRATION == "FIRST_REGISTRATION"
    assert ColonialMilitiaClass.COMMON_MILITIA == "COMMON_MILITIA"
    assert ColonialWarPeriod.KING_PHILIPS_WAR == "KING_PHILIPS_WAR"
    assert CivilWarEnrollmentClass.CLASS_1 == "CLASS_1"
    assert CivilWarConscriptionAllegiance.UNION == "UNION"
    assert WwiCitizenshipStatus.NATIVE_BORN == "NATIVE_BORN"
    assert WwiiDraftWave.FIRST_WAVE == "FIRST_WAVE"
    assert ModernDraftEra.POST_1980_REGISTRATION == "POST_1980_REGISTRATION"
    assert SssClassification.CLASS_1_A == "CLASS_1_A"


@pytest.mark.integrity
def test_no_legacy_domain_paths_exist() -> None:
    """Verify no stray domain directories exist in source or test trees."""
    root = Path(__file__).resolve().parent.parent.parent.parent.parent
    invalid_src = root / "src" / "gda" / "model" / "domain"
    invalid_tests = root / "tests" / "test_gda" / "test_model" / "test_domain"

    assert not invalid_src.exists(), f"Found invalid source path: {invalid_src}"
    assert not invalid_tests.exists(), f"Found invalid test path: {invalid_tests}"
