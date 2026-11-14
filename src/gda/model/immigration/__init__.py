"""Path: src/gda/model/immigration/__init__.py

Historical ship passenger arrival manifests, border crossings, and naturalization models.

Operational Role:
    Exports ImmigrationManifestRecord, ManifestPassenger, NaturalizationRecord,
    and NaturalizationWitness domain models.
"""

from __future__ import annotations

from gda.model.immigration.manifest import ImmigrationManifestRecord, ManifestPassenger
from gda.model.immigration.naturalization import NaturalizationRecord, NaturalizationWitness

__version__ = "1.0.0+build.2"

__all__ = [
    "ImmigrationManifestRecord",
    "ManifestPassenger",
    "NaturalizationRecord",
    "NaturalizationWitness",
]
