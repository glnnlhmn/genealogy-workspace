"""Path: src/gda/model/military/service/__init__.py

Military service, enlistment, muster-in/out, CMSR, and discharge separation records.
"""

from __future__ import annotations

from enum import StrEnum

__version__ = "1.0.0+build.1"

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


class MilitaryBranch(StrEnum):
    """Armed force branch designation across historical periods."""

    ARMY = "ARMY"
    NAVY = "NAVY"
    MARINE_CORPS = "MARINE_CORPS"
    AIR_FORCE = "AIR_FORCE"
    COAST_GUARD = "COAST_GUARD"
    CONTINENTAL_ARMY = "CONTINENTAL_ARMY"
    CONTINENTAL_NAVY = "CONTINENTAL_NAVY"
    STATE_MILITIA = "STATE_MILITIA"
    CONFEDERATE_ARMY = "CONFEDERATE_ARMY"
    CONFEDERATE_NAVY = "CONFEDERATE_NAVY"
    MERCHANT_MARINE = "MERCHANT_MARINE"
    OTHER = "OTHER"


class ServiceComponent(StrEnum):
    """Component classification of armed forces service."""

    REGULAR = "REGULAR"
    VOLUNTEER = "VOLUNTEER"
    NATIONAL_GUARD = "NATIONAL_GUARD"
    RESERVE = "RESERVE"
    SELECTIVE_SERVICE_CONSCRIPT = "SELECTIVE_SERVICE_CONSCRIPT"


class SeparationCharacter(StrEnum):
    """Character of discharge or release from military active duty."""

    HONORABLE = "HONORABLE"
    GENERAL_UNDER_HONORABLE = "GENERAL_UNDER_HONORABLE"
    OTHER_THAN_HONORABLE = "OTHER_THAN_HONORABLE"
    BAD_CONDUCT = "BAD_CONDUCT"
    DISHONORABLE = "DISHONORABLE"
    UNCHARACTERIZED = "UNCHARACTERIZED"
    DIED_IN_SERVICE = "DIED_IN_SERVICE"


# Downstream domain model imports
from gda.model.military.service.base import MilitaryServiceRecord  # noqa: E402
from gda.model.military.service.enlistment import (  # noqa: E402
    EnlistmentMusterRecord,
    MusterRollType,
)
from gda.model.military.service.separation import (  # noqa: E402
    SeparationDischargeRecord,
    SeparationFormType,
)
