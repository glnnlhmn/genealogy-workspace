"""Path: src/gda/model/military/__init__.py

Military evidentiary domain models partitioned by record classification.
"""

from __future__ import annotations

from gda.model.military.awards import (
    AwardScope,
    MilitaryAwardRecord,
    MilitaryAwardTier,
)
from gda.model.military.casualty import (
    CasualtyCategory,
    CombatCasualtyRecord,
    IntermentCemeteryType,
    MilitaryBurialRecord,
    MilitaryCasualtyRecord,
    PowCampType,
    PrisonerOfWarRecord,
)
from gda.model.military.draft import (
    CivilWarConscriptionAllegiance,
    CivilWarDraftRecord,
    CivilWarEnrollmentClass,
    ColonialMilitiaClass,
    ColonialMilitiaRecord,
    ColonialWarPeriod,
    DraftCardTier,
    MilitaryDraftRecord,
    ModernDraftEra,
    ModernSelectiveServiceRecord,
    SssClassification,
    WwiCitizenshipStatus,
    WwiDraftCardRecord,
    WwiiDraftCardRecord,
    WwiiDraftWave,
    WwiiPhysicalMetrics,
    WwiPhysicalDescription,
)
from gda.model.military.pension import (
    BountyLandAct,
    BountyLandWarrantRecord,
    MilitaryPensionRecord,
    PensionClaimantRole,
    PensionPaymentAuthority,
    PensionVeteranClaimRecord,
    PensionWidowDependentRecord,
)
from gda.model.military.service import (
    EnlistmentMusterRecord,
    MilitaryBranch,
    MilitaryServiceRecord,
    MusterRollType,
    SeparationCharacter,
    SeparationDischargeRecord,
    SeparationFormType,
    ServiceComponent,
)

__version__ = "1.0.0+build.4"

__all__ = [
    "AwardScope",
    "BountyLandAct",
    "BountyLandWarrantRecord",
    "CasualtyCategory",
    "CivilWarConscriptionAllegiance",
    "CivilWarDraftRecord",
    "CivilWarEnrollmentClass",
    "ColonialMilitiaClass",
    "ColonialMilitiaRecord",
    "ColonialWarPeriod",
    "CombatCasualtyRecord",
    "DraftCardTier",
    "EnlistmentMusterRecord",
    "IntermentCemeteryType",
    "MilitaryAwardRecord",
    "MilitaryAwardTier",
    "MilitaryBranch",
    "MilitaryBurialRecord",
    "MilitaryCasualtyRecord",
    "MilitaryDraftRecord",
    "MilitaryPensionRecord",
    "MilitaryServiceRecord",
    "ModernDraftEra",
    "ModernSelectiveServiceRecord",
    "MusterRollType",
    "PensionClaimantRole",
    "PensionPaymentAuthority",
    "PensionVeteranClaimRecord",
    "PensionWidowDependentRecord",
    "PowCampType",
    "PrisonerOfWarRecord",
    "SeparationCharacter",
    "SeparationDischargeRecord",
    "SeparationFormType",
    "ServiceComponent",
    "SssClassification",
    "WwiCitizenshipStatus",
    "WwiDraftCardRecord",
    "WwiPhysicalDescription",
    "WwiiDraftCardRecord",
    "WwiiDraftWave",
    "WwiiPhysicalMetrics",
]
