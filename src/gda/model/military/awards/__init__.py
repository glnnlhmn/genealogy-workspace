"""Path: src/gda/model/military/awards/__init__.py

Military awards, valor decorations, unit citations, and campaign medals.
"""

from __future__ import annotations

from enum import StrEnum

__version__ = "1.0.0+build.2"

__all__ = [
    "AwardScope",
    "MilitaryAwardRecord",
    "MilitaryAwardTier",
]


class MilitaryAwardTier(StrEnum):
    """Precedence hierarchy and classification of armed forces awards."""

    MEDAL_OF_HONOR = "MEDAL_OF_HONOR"
    DISTINGUISHED_SERVICE_CROSS = "DISTINGUISHED_SERVICE_CROSS"
    NAVY_CROSS = "NAVY_CROSS"
    AIR_FORCE_CROSS = "AIR_FORCE_CROSS"
    SILVER_STAR = "SILVER_STAR"
    DISTINGUISHED_FLYING_CROSS = "DISTINGUISHED_FLYING_CROSS"
    BRONZE_STAR = "BRONZE_STAR"
    PURPLE_HEART = "PURPLE_HEART"
    COMMENDATION_MEDAL = "COMMENDATION_MEDAL"
    ACHIEVEMENT_MEDAL = "ACHIEVEMENT_MEDAL"
    CAMPAIGN_MEDAL = "CAMPAIGN_MEDAL"
    EXPEDITIONARY_MEDAL = "EXPEDITIONARY_MEDAL"
    SERVICE_MEDAL = "SERVICE_MEDAL"
    UNIT_CITATION = "UNIT_CITATION"
    FOREIGN_DECORATION = "FOREIGN_DECORATION"
    OTHER = "OTHER"


class AwardScope(StrEnum):
    """Operational or commemorative scope of military recognition."""

    VALOR_IN_COMBAT = "VALOR_IN_COMBAT"
    MERITORIOUS_SERVICE = "MERITORIOUS_SERVICE"
    WOUND_IN_ACTION = "WOUND_IN_ACTION"
    CAMPAIGN_PARTICIPATION = "CAMPAIGN_PARTICIPATION"
    LONGEVITY_SERVICE = "LONGEVITY_SERVICE"
    MARKSMANSHIP = "MARKSMANSHIP"
    OTHER = "OTHER"


# Downstream domain model imports
from gda.model.military.awards.base import MilitaryAwardRecord  # noqa: E402
