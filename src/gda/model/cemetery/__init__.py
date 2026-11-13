"""Path: src/gda/model/cemetery/__init__.py

Cemetery marker, monument, plot ledger, and grave survey domain models.

Operational Role:
    Exports CemeteryMarkerRecord, MarkerInterment, CemeteryRegistryRecord,
    CemeteryPlotEntry, and RegistryInterment domain models.
"""

from __future__ import annotations

from gda.model.cemetery.marker import CemeteryMarkerRecord, MarkerInterment
from gda.model.cemetery.registry import (
    CemeteryPlotEntry,
    CemeteryRegistryRecord,
    RegistryInterment,
)

__version__ = "1.1.0+build.1"

__all__ = [
    "CemeteryMarkerRecord",
    "CemeteryPlotEntry",
    "CemeteryRegistryRecord",
    "MarkerInterment",
    "RegistryInterment",
]
