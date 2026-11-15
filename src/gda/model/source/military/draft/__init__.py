"""Path: src/gda/model/source/military/draft/__init__.py

Military draft registration, militia enrollment, and selective service records.
"""

from __future__ import annotations

from gda.core.enums.military import (
    CivilWarConscriptionAllegiance,
    CivilWarEnrollmentClass,
    ColonialMilitiaClass,
    ColonialWarPeriod,
    DraftCardTier,
    ModernDraftEra,
    SssClassification,
    WwiCitizenshipStatus,
    WwiiDraftWave,
)
from gda.model.source.military.draft.base import MilitaryDraftRecord
from gda.model.source.military.draft.civil_war import CivilWarDraftRecord
from gda.model.source.military.draft.colonial import ColonialMilitiaRecord
from gda.model.source.military.draft.modern_sss import ModernSelectiveServiceRecord
from gda.model.source.military.draft.wwi import (
    WwiDraftCardRecord,
    WwiPhysicalDescription,
)
from gda.model.source.military.draft.wwii import (
    WwiiDraftCardRecord,
    WwiiPhysicalMetrics,
)

__version__ = "1.0.0+build.1"

__all__ = [
    "CivilWarConscriptionAllegiance",  # gda.core.enums.military
    "CivilWarDraftRecord",  # gda.model.source.military.draft.civil_war
    "CivilWarEnrollmentClass",  # gda.core.enums.military
    "ColonialMilitiaClass",  # gda.core.enums.military
    "ColonialMilitiaRecord",  # gda.model.source.military.draft.colonial
    "ColonialWarPeriod",  # gda.core.enums.military
    "DraftCardTier",  # gda.core.enums.military
    "MilitaryDraftRecord",  # gda.model.source.military.draft.base
    "ModernDraftEra",  # gda.core.enums.military
    "ModernSelectiveServiceRecord",  # gda.model.source.military.draft.modern_sss
    "SssClassification",  # gda.core.enums.military
    "WwiCitizenshipStatus",  # gda.core.enums.military
    "WwiDraftCardRecord",  # gda.model.source.military.draft.wwi
    "WwiPhysicalDescription",  # gda.model.source.military.draft.wwi
    "WwiiDraftCardRecord",  # gda.model.source.military.draft.wwii
    "WwiiDraftWave",  # gda.core.enums.military
    "WwiiPhysicalMetrics",  # gda.model.source.military.draft.wwii
]
