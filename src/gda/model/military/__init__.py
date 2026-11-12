"""Path: src/gda/model/military/__init__.py

Authoritative military service, draft, pension, casualty, and awards domain models.
"""

from __future__ import annotations

from gda.core.enums.military import (
    AwardScope,
    BountyLandAct,
    CasualtyCategory,
    CivilWarConscriptionAllegiance,
    CivilWarEnrollmentClass,
    ColonialMilitiaClass,
    ColonialWarPeriod,
    DraftCardTier,
    IntermentCemeteryType,
    MilitaryAwardTier,
    MilitaryBranch,
    ModernDraftEra,
    MusterRollType,
    PensionClaimantRole,
    PensionPaymentAuthority,
    PowCampType,
    SeparationCharacter,
    SeparationFormType,
    ServiceComponent,
    SssClassification,
    WwiCitizenshipStatus,
    WwiiDraftWave,
)
from gda.model.military.awards import MilitaryAwardRecord
from gda.model.military.casualty import (
    CombatCasualtyRecord,
    MilitaryBurialRecord,
    MilitaryCasualtyRecord,
    PrisonerOfWarRecord,
)
from gda.model.military.draft import (
    CivilWarDraftRecord,
    ColonialMilitiaRecord,
    MilitaryDraftRecord,
    ModernSelectiveServiceRecord,
    WwiDraftCardRecord,
    WwiiDraftCardRecord,
    WwiiPhysicalMetrics,
    WwiPhysicalDescription,
)
from gda.model.military.pension import (
    BountyLandWarrantRecord,
    MilitaryPensionRecord,
    PensionVeteranClaimRecord,
    PensionWidowDependentRecord,
)
from gda.model.military.service import (
    EnlistmentMusterRecord,
    MilitaryServiceRecord,
    SeparationDischargeRecord,
)

__version__ = "2.1.0+build.1"

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
