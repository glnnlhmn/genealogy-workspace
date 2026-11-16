"""Path: src/gda/model/source/land/__init__.py

Historical land deeds, conveyances, mortgages, patents, warrants, and survey models.

Operational Role:
    Exports LandDeedRecord, DeedParty, LandParcel, and LandGrantRecord domain models.
"""

from __future__ import annotations

from gda.model.source.land.deed import DeedParty, LandDeedRecord, LandParcel
from gda.model.source.land.grant import LandGrantRecord

__version__ = "1.0.0+build.2"

__all__ = [
    "DeedParty",  # gda.model.source.land.deed
    "LandDeedRecord",  # gda.model.source.land.deed
    "LandGrantRecord",  # gda.model.source.land.grant
    "LandParcel",  # gda.model.source.land.deed
]
