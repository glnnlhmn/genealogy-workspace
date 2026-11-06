"""Path: src/gda/model/military/draft/__init__.py

Military draft registration, militia enrollment, and selective service records.
"""

from __future__ import annotations

from enum import StrEnum

__version__ = "1.0.0+build.2"

__all__ = [
    "CivilWarConscriptionAllegiance",
    "CivilWarDraftRecord",
    "CivilWarEnrollmentClass",
    "ColonialMilitiaClass",
    "ColonialMilitiaRecord",
    "ColonialWarPeriod",
    "DraftCardTier",
    "MilitaryDraftRecord",
    "ModernDraftEra",
    "ModernSelectiveServiceRecord",
    "SssClassification",
    "WwiCitizenshipStatus",
    "WwiDraftCardRecord",
    "WwiPhysicalDescription",
    "WwiiDraftCardRecord",
    "WwiiDraftWave",
    "WwiiPhysicalMetrics",
]


class ColonialWarPeriod(StrEnum):
    """Historical colonial conflict eras."""

    PEQUOT_WAR = "PEQUOT_WAR"
    KING_PHILIPS_WAR = "KING_PHILIPS_WAR"
    KING_WILLIAMS_WAR = "KING_WILLIAMS_WAR"
    QUEEN_ANNES_WAR = "QUEEN_ANNES_WAR"
    FRENCH_AND_INDIAN_WAR = "FRENCH_AND_INDIAN_WAR"
    LORD_DUNMORES_WAR = "LORD_DUNMORES_WAR"
    OTHER = "OTHER"


class ColonialMilitiaClass(StrEnum):
    """Statutory colonial militia enrollment classification."""

    COMMON_MILITIA = "COMMON_MILITIA"
    MINUTEMAN = "MINUTEMAN"
    TRAINBAND = "TRAINBAND"
    ALARM_LIST = "ALARM_LIST"
    VOLUNTEER_EXPEDITIONARY = "VOLUNTEER_EXPEDITIONARY"
    EXEMPT = "EXEMPT"


class CivilWarEnrollmentClass(StrEnum):
    """Enrollment Act of 1863 statutory conscription classes."""

    CLASS_1 = "CLASS_1"
    CLASS_2 = "CLASS_2"
    VOLUNTEER_ENLISTED = "VOLUNTEER_ENLISTED"
    EXEMPT = "EXEMPT"


class CivilWarConscriptionAllegiance(StrEnum):
    """Conscription authority and allegiance during the American Civil War."""

    UNION = "UNION"
    CONFEDERATE = "CONFEDERATE"


class DraftCardTier(StrEnum):
    """WWI Selective Service registration tiers/waves."""

    FIRST_REGISTRATION = "FIRST_REGISTRATION"
    SECOND_REGISTRATION = "SECOND_REGISTRATION"
    THIRD_REGISTRATION = "THIRD_REGISTRATION"


class WwiCitizenshipStatus(StrEnum):
    """Citizenship declarations on WWI draft registration forms."""

    NATIVE_BORN = "NATIVE_BORN"
    NATURALIZED_CITIZEN = "NATURALIZED_CITIZEN"
    ALIEN_DECLARED_INTENTION = "ALIEN_DECLARED_INTENTION"
    NON_DECLARANT_ALIEN = "NON_DECLARANT_ALIEN"


class WwiiDraftWave(StrEnum):
    """WWII Selective Training and Service Act registration waves."""

    FIRST_WAVE = "FIRST_WAVE"
    SECOND_WAVE = "SECOND_WAVE"
    THIRD_WAVE = "THIRD_WAVE"
    FOURTH_WAVE_OLD_MANS_DRAFT = "FOURTH_WAVE_OLD_MANS_DRAFT"
    FIFTH_WAVE = "FIFTH_WAVE"
    SIXTH_WAVE = "SIXTH_WAVE"


class ModernDraftEra(StrEnum):
    """Post-1948 Selective Service registration eras."""

    POST_1980_REGISTRATION = "POST_1980_REGISTRATION"
    VIETNAM_LOTTERY = "VIETNAM_LOTTERY"
    KOREAN_WAR_DRAFT = "KOREAN_WAR_DRAFT"


class SssClassification(StrEnum):
    """Selective Service System registrant classifications."""

    CLASS_1_A = "CLASS_1_A"
    CLASS_1_A_O = "CLASS_1_A_O"
    CLASS_1_C = "CLASS_1_C"
    CLASS_1_D = "CLASS_1_D"
    CLASS_1_O = "CLASS_1_O"
    CLASS_2_S = "CLASS_2_S"
    CLASS_3_A = "CLASS_3_A"
    CLASS_4_A = "CLASS_4_A"
    CLASS_4_D = "CLASS_4_D"
    CLASS_4_F = "CLASS_4_F"


# Downstream domain model imports
from gda.model.military.draft.base import MilitaryDraftRecord  # noqa: E402
from gda.model.military.draft.civil_war import CivilWarDraftRecord  # noqa: E402
from gda.model.military.draft.colonial import ColonialMilitiaRecord  # noqa: E402
from gda.model.military.draft.modern_sss import ModernSelectiveServiceRecord  # noqa: E402
from gda.model.military.draft.wwi import (  # noqa: E402
    WwiDraftCardRecord,
    WwiPhysicalDescription,
)
from gda.model.military.draft.wwii import (  # noqa: E402
    WwiiDraftCardRecord,
    WwiiPhysicalMetrics,
)
