"""Path: src/gda/model/source/cemetery/__init__.py

Cemetery marker, monument, plot ledger, and grave survey domain models.

Operational Role:
    Exports CemeteryMarkerRecord, MarkerInterment, CemeteryRegistryRecord,
    CemeteryPlotEntry, and RegistryInterment domain models.
"""

from __future__ import annotations

from gda.model.source.cemetery.marker import CemeteryMarkerRecord, MarkerInterment
from gda.model.source.cemetery.registry import (
    CemeteryPlotEntry,
    CemeteryRegistryRecord,
    RegistryInterment,
)

__version__ = "1.0.0+build.2"

__all__ = [
    "CemeteryMarkerRecord",  # gda.model.source.cemetery.marker
    "CemeteryPlotEntry",  # gda.model.source.cemetery.registry
    "CemeteryRegistryRecord",  # gda.model.source.cemetery.registry
    "MarkerInterment",  # gda.model.source.cemetery.marker
    "RegistryInterment",  # gda.model.source.cemetery.registry
]
