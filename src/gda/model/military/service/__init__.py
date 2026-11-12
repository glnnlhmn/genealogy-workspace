"""Path: src/gda/model/military/service/__init__.py

Military service, enlistment, muster-in/out, CMSR, and discharge separation records.
"""

from __future__ import annotations

from gda.core.enums.military import (
    MilitaryBranch,
    MusterRollType,
    SeparationCharacter,
    SeparationFormType,
    ServiceComponent,
)
from gda.model.military.service.base import MilitaryServiceRecord
from gda.model.military.service.enlistment import EnlistmentMusterRecord
from gda.model.military.service.separation import SeparationDischargeRecord

__version__ = "2.1.0+build.1"

__all__ = [
    "EnlistmentMusterRecord",
    "MilitaryBranch",
    "MilitaryServiceRecord",
    "MusterRollType",
    "SeparationCharacter",
    "SeparationDischargeRecord",
    "SeparationFormType",
    "ServiceComponent",
]
