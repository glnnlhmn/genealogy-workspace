"""Path: src/gda/model/source/military/__init__.py

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
from gda.model.source.military.awards import MilitaryAwardRecord
from gda.model.source.military.casualty import (
    CombatCasualtyRecord,
    MilitaryBurialRecord,
    MilitaryCasualtyRecord,
    PrisonerOfWarRecord,
)
from gda.model.source.military.draft import (
    CivilWarDraftRecord,
    ColonialMilitiaRecord,
    MilitaryDraftRecord,
    ModernSelectiveServiceRecord,
    WwiDraftCardRecord,
    WwiiDraftCardRecord,
    WwiiPhysicalMetrics,
    WwiPhysicalDescription,
)
from gda.model.source.military.pension import (
    BountyLandWarrantRecord,
    MilitaryPensionRecord,
    PensionVeteranClaimRecord,
    PensionWidowDependentRecord,
)
from gda.model.source.military.service import (
    EnlistmentMusterRecord,
    MilitaryServiceRecord,
    SeparationDischargeRecord,
)

__version__ = "1.0.0+build.1"

__all__ = [
    "AwardScope",  # gda.core.enums.military
    "BountyLandAct",  # gda.core.enums.military
    "BountyLandWarrantRecord",  # gda.model.source.military.pension
    "CasualtyCategory",  # gda.core.enums.military
    "CivilWarConscriptionAllegiance",  # gda.core.enums.military
    "CivilWarDraftRecord",  # gda.model.source.military.draft
    "CivilWarEnrollmentClass",  # gda.core.enums.military
    "ColonialMilitiaClass",  # gda.core.enums.military
    "ColonialMilitiaRecord",  # gda.model.source.military.draft
    "ColonialWarPeriod",  # gda.core.enums.military
    "CombatCasualtyRecord",  # gda.model.source.military.casualty
    "DraftCardTier",  # gda.core.enums.military
    "EnlistmentMusterRecord",  # gda.model.source.military.service
    "IntermentCemeteryType",  # gda.core.enums.military
    "MilitaryAwardRecord",  # gda.model.source.military.awards
    "MilitaryAwardTier",  # gda.core.enums.military
    "MilitaryBranch",  # gda.core.enums.military
    "MilitaryBurialRecord",  # gda.model.source.military.casualty
    "MilitaryCasualtyRecord",  # gda.model.source.military.casualty
    "MilitaryDraftRecord",  # gda.model.source.military.draft
    "MilitaryPensionRecord",  # gda.model.source.military.pension
    "MilitaryServiceRecord",  # gda.model.source.military.service
    "ModernDraftEra",  # gda.core.enums.military
    "ModernSelectiveServiceRecord",  # gda.model.source.military.draft
    "MusterRollType",  # gda.core.enums.military
    "PensionClaimantRole",  # gda.core.enums.military
    "PensionPaymentAuthority",  # gda.core.enums.military
    "PensionVeteranClaimRecord",  # gda.model.source.military.pension
    "PensionWidowDependentRecord",  # gda.model.source.military.pension
    "PowCampType",  # gda.core.enums.military
    "PrisonerOfWarRecord",  # gda.model.source.military.casualty
    "SeparationCharacter",  # gda.core.enums.military
    "SeparationDischargeRecord",  # gda.model.source.military.service
    "SeparationFormType",  # gda.core.enums.military
    "ServiceComponent",  # gda.core.enums.military
    "SssClassification",  # gda.core.enums.military
    "WwiCitizenshipStatus",  # gda.core.enums.military
    "WwiDraftCardRecord",  # gda.model.source.military.draft
    "WwiPhysicalDescription",  # gda.model.source.military.draft
    "WwiiDraftCardRecord",  # gda.model.source.military.draft
    "WwiiDraftWave",  # gda.core.enums.military
    "WwiiPhysicalMetrics",  # gda.model.source.military.draft
]
