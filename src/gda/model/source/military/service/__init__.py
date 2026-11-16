"""Path: src/gda/model/source/military/service/__init__.py

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
from gda.model.source.military.service.base import MilitaryServiceRecord
from gda.model.source.military.service.enlistment import EnlistmentMusterRecord
from gda.model.source.military.service.separation import SeparationDischargeRecord

__version__ = "1.0.0+build.1"

__all__ = [
    "EnlistmentMusterRecord",  # gda.model.source.military.service.enlistment
    "MilitaryBranch",  # gda.core.enums.military
    "MilitaryServiceRecord",  # gda.model.source.military.service.base
    "MusterRollType",  # gda.core.enums.military
    "SeparationCharacter",  # gda.core.enums.military
    "SeparationDischargeRecord",  # gda.model.source.military.service.separation
    "SeparationFormType",  # gda.core.enums.military
    "ServiceComponent",  # gda.core.enums.military
]
