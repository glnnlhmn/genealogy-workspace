"""Path: src/gda/model/source/military/awards/__init__.py

Military awards, valor decorations, unit citations, and campaign medals.
"""

from __future__ import annotations

from gda.core.enums.military import AwardScope, MilitaryAwardTier
from gda.model.source.military.awards.base import MilitaryAwardRecord

__version__ = "1.0.0+build.1"

__all__ = [
    "AwardScope",  # gda.core.enums.military
    "MilitaryAwardRecord",  # gda.model.source.military.awards.base
    "MilitaryAwardTier",  # gda.core.enums.military
]
