"""Path: src/gda/model/source/vital/__init__.py

Vital and sacramental event record definitions.

Operational Role:
    Exports BirthRecord, MarriageRecord, DeathRecord, DivorceRecord, and
    BaptismRecord domain models.
"""

from __future__ import annotations

from gda.model.source.vital.baptism import BaptismRecord
from gda.model.source.vital.birth import BirthRecord
from gda.model.source.vital.death import DeathRecord
from gda.model.source.vital.divorce import DivorceRecord
from gda.model.source.vital.marriage import MarriageRecord

__version__ = "1.0.0+build.2"

__all__ = [
    "BaptismRecord",  # gda.model.source.vital.baptism
    "BirthRecord",  # gda.model.source.vital.birth
    "DeathRecord",  # gda.model.source.vital.death
    "DivorceRecord",  # gda.model.source.vital.divorce
    "MarriageRecord",  # gda.model.source.vital.marriage
]
