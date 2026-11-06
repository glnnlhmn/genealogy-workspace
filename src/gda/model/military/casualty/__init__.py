"""Path: src/gda/model/military/casualty/__init__.py

Military casualty reports, combat actions, prisoner of war records, and burials.
"""

from __future__ import annotations

from enum import StrEnum

__version__ = "1.0.0+build.2"

__all__ = [
    "CasualtyCategory",
    "CombatCasualtyRecord",
    "IntermentCemeteryType",
    "MilitaryBurialRecord",
    "MilitaryCasualtyRecord",
    "PowCampType",
    "PrisonerOfWarRecord",
]


class CasualtyCategory(StrEnum):
    """Classification of military casualty event."""

    KILLED_IN_ACTION = "KILLED_IN_ACTION"
    DIED_OF_WOUNDS = "DIED_OF_WOUNDS"
    WOUNDED_IN_ACTION = "WOUNDED_IN_ACTION"
    MISSING_IN_ACTION = "MISSING_IN_ACTION"
    PRISONER_OF_WAR = "PRISONER_OF_WAR"
    DIED_OF_DISEASE = "DIED_OF_DISEASE"
    DIED_IN_SERVICE = "DIED_IN_SERVICE"
    NON_COMBAT_DEATH = "NON_COMBAT_DEATH"
    ACCIDENTAL = "ACCIDENTAL"
    OTHER = "OTHER"


class PowCampType(StrEnum):
    """Prisoner of war camp administrative category."""

    OFFICER_CAMP = "OFFICER_CAMP"  # e.g., Oflag
    ENLISTED_CAMP = "ENLISTED_CAMP"  # e.g., Stalag
    CIVIL_WAR_STOCKADE = "CIVIL_WAR_STOCKADE"  # e.g., Andersonville, Elmira
    INTERNMENT_CENTER = "INTERNMENT_CENTER"
    TEMPORARY_HOLDING = "TEMPORARY_HOLDING"
    OTHER = "OTHER"


class IntermentCemeteryType(StrEnum):
    """Type or jurisdiction of military burial facility."""

    NATIONAL_CEMETERY = "NATIONAL_CEMETERY"
    STATE_VETERANS_CEMETERY = "STATE_VETERANS_CEMETERY"
    ABMC_OVERSEAS = "ABMC_OVERSEAS"
    PRIVATE_CEMETERY = "PRIVATE_CEMETERY"
    POST_CEMETERY = "POST_CEMETERY"
    BATTLEFIELD_BURIAL = "BATTLEFIELD_BURIAL"
    UNKNOWN = "UNKNOWN"


# Downstream domain model imports
from gda.model.military.casualty.base import MilitaryCasualtyRecord  # noqa: E402
from gda.model.military.casualty.burial import MilitaryBurialRecord  # noqa: E402
from gda.model.military.casualty.combat import CombatCasualtyRecord  # noqa: E402
from gda.model.military.casualty.pow import PrisonerOfWarRecord  # noqa: E402
