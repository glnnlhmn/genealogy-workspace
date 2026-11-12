"""Path: src/gda/model/military/draft/__init__.py

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
from gda.model.military.draft.base import MilitaryDraftRecord
from gda.model.military.draft.civil_war import CivilWarDraftRecord
from gda.model.military.draft.colonial import ColonialMilitiaRecord
from gda.model.military.draft.modern_sss import ModernSelectiveServiceRecord
from gda.model.military.draft.wwi import (
    WwiDraftCardRecord,
    WwiPhysicalDescription,
)
from gda.model.military.draft.wwii import (
    WwiiDraftCardRecord,
    WwiiPhysicalMetrics,
)

__version__ = "2.1.0+build.1"

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
