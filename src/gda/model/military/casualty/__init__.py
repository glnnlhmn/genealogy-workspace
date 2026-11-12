"""Path: src/gda/model/military/casualty/__init__.py

Military casualty reports, combat actions, prisoner of war records, and burials.
"""

from __future__ import annotations

from gda.core.enums.military import (
    CasualtyCategory,
    IntermentCemeteryType,
    PowCampType,
)
from gda.model.military.casualty.base import MilitaryCasualtyRecord
from gda.model.military.casualty.burial import MilitaryBurialRecord
from gda.model.military.casualty.combat import CombatCasualtyRecord
from gda.model.military.casualty.pow import PrisonerOfWarRecord

__version__ = "2.1.0+build.1"

__all__ = [
    "CasualtyCategory",
    "CombatCasualtyRecord",
    "IntermentCemeteryType",
    "MilitaryBurialRecord",
    "MilitaryCasualtyRecord",
    "PowCampType",
    "PrisonerOfWarRecord",
]
