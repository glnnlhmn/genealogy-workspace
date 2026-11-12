"""Path: src/gda/model/military/awards/__init__.py

Military awards, valor decorations, unit citations, and campaign medals.
"""

from __future__ import annotations

from gda.core.enums.military import AwardScope, MilitaryAwardTier
from gda.model.military.awards.base import MilitaryAwardRecord

__version__ = "2.1.0+build.1"

__all__ = [
    "AwardScope",
    "MilitaryAwardRecord",
    "MilitaryAwardTier",
]
