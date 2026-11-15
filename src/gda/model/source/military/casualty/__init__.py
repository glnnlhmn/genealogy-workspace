"""Path: src/gda/model/source/military/casualty/__init__.py

Military casualty reports, combat actions, prisoner of war records, and burials.
"""

from __future__ import annotations

from gda.core.enums.military import (
    CasualtyCategory,
    IntermentCemeteryType,
    PowCampType,
)
from gda.model.source.military.casualty.base import MilitaryCasualtyRecord
from gda.model.source.military.casualty.burial import MilitaryBurialRecord
from gda.model.source.military.casualty.combat import CombatCasualtyRecord
from gda.model.source.military.casualty.pow import PrisonerOfWarRecord

__version__ = "1.0.0+build.1"

__all__ = [
    "CasualtyCategory",  # gda.core.enums.military
    "CombatCasualtyRecord",  # gda.model.source.military.casualty.combat
    "IntermentCemeteryType",  # gda.core.enums.military
    "MilitaryBurialRecord",  # gda.model.source.military.casualty.burial
    "MilitaryCasualtyRecord",  # gda.model.source.military.casualty.base
    "PowCampType",  # gda.core.enums.military
    "PrisonerOfWarRecord",  # gda.model.source.military.casualty.pow
]
