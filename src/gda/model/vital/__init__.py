"""Path: src/gda/model/vital/__init__.py

Vital and sacramental event record definitions.

Operational Role:
    Exports BirthRecord, MarriageRecord, DeathRecord, DivorceRecord, and
    BaptismRecord domain models.
"""

from __future__ import annotations

from gda.model.vital.baptism import BaptismRecord
from gda.model.vital.birth import BirthRecord
from gda.model.vital.death import DeathRecord
from gda.model.vital.divorce import DivorceRecord
from gda.model.vital.marriage import MarriageRecord

__version__ = "1.1.0+build.1"

__all__ = [
    "BaptismRecord",
    "BirthRecord",
    "DeathRecord",
    "DivorceRecord",
    "MarriageRecord",
]
