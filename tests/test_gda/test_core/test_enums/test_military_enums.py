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

import pytest

import gda.core.enums as enums_pkg
import gda.core.enums.military as mil_enums

__version__ = "1.0.0+build.3"


# ==============================================================================
# GROUP 1: Smoke & Primary Entrypoints
# Note: Single smoke gate freezing the 25 sorted military exports.
# ==============================================================================


@pytest.mark.smoke
@pytest.mark.integrity
@pytest.mark.unit
def test_military_enums_all_sorted_and_reexported() -> None:
    """Verify gda.core.enums.military.__all__ has 25 sorted symbols re-exported."""
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
@pytest.mark.parametrize(
    ("enum_name", "member_name", "expected_value"),
    [
        ("MilitaryBranch", "ARMY", "ARMY"),
        ("ServiceComponent", "REGULAR", "REGULAR"),
        ("SeparationCharacter", "HONORABLE", "HONORABLE"),
        ("MusterRollType", "MUSTER_IN", "MUSTER_IN"),
        ("SeparationFormType", "DD_214", "DD_214"),
        ("MilitaryAwardTier", "MEDAL_OF_HONOR", "MEDAL_OF_HONOR"),
        ("AwardScope", "VALOR_IN_COMBAT", "VALOR_IN_COMBAT"),
        ("CasualtyCategory", "KILLED_IN_ACTION", "KILLED_IN_ACTION"),
        ("PowCampType", "OFFICER_CAMP", "OFFICER_CAMP"),
        ("IntermentCemeteryType", "NATIONAL_CEMETERY", "NATIONAL_CEMETERY"),
        ("PensionClaimantRole", "VETERAN", "VETERAN"),
        ("PensionPaymentAuthority", "US_BUREAU_OF_PENSIONS", "US_BUREAU_OF_PENSIONS"),
        ("BountyLandAct", "ACT_OF_1855", "ACT_OF_1855"),
        ("DraftCardTier", "WWI_FIRST", "WWI_FIRST"),
        ("ColonialWarPeriod", "REVOLUTIONARY_WAR", "REVOLUTIONARY_WAR"),
        ("ColonialMilitiaClass", "TRAINBAND", "TRAINBAND"),
        ("CivilWarConscriptionAllegiance", "UNION", "UNION"),
        ("CivilWarEnrollmentClass", "CLASS_1", "CLASS_1"),
        ("WwiCitizenshipStatus", "NATIVE_BORN", "NATIVE_BORN"),
        ("WwiiDraftWave", "FIRST", "FIRST"),
        ("ModernDraftEra", "POST_1980_REGISTRATION", "POST_1980_REGISTRATION"),
        ("SssClassification", "ONE_A", "1-A"),
    ],
)
def test_military_enum_canonical_members(
    enum_name: str,
    member_name: str,
    expected_value: str,
) -> None:
    """Verify canonical members across all 5 military subdomains."""
    enum_cls = getattr(mil_enums, enum_name)
    assert getattr(enum_cls, member_name) == expected_value


@pytest.mark.unit
@pytest.mark.parametrize(
    ("enum_name", "member_name", "expected_value"),
    [
        ("WwiCardType", "CARD_A", "CARD_A"),
        ("WwiCardType", "CARD_B", "CARD_B"),
        ("WwiCardType", "CARD_C", "CARD_C"),
        ("WwiCardType", "UNKNOWN", "UNKNOWN"),
        ("MilitaryDraftType", "DRAFT_REGISTRATION", "DRAFT_REGISTRATION"),
        ("MilitaryWar", "CIVIL_WAR", "CIVIL_WAR"),
        ("MilitaryWar", "WWI", "WWI"),
        ("MilitaryWar", "WWII", "WWII"),
    ],
)
def test_relocated_military_enums_in_military_module(
    enum_name: str,
    member_name: str,
    expected_value: str,
) -> None:
    """Verify WwiCardType, MilitaryDraftType, and MilitaryWar live in military."""
    enum_cls = getattr(mil_enums, enum_name)
    assert getattr(enum_cls, member_name) == expected_value


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
