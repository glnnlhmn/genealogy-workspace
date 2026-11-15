"""Path: src/gda/model/source/immigration/__init__.py

Historical ship passenger arrival manifests, border crossings, and naturalization models.

Operational Role:
    Exports ImmigrationManifestRecord, ManifestPassenger, NaturalizationRecord,
    and NaturalizationWitness domain models.
"""

from __future__ import annotations

from gda.model.source.immigration.manifest import ImmigrationManifestRecord, ManifestPassenger
from gda.model.source.immigration.naturalization import NaturalizationRecord, NaturalizationWitness

__version__ = "1.0.0+build.3"

__all__ = [
    "ImmigrationManifestRecord",  # gda.model.source.immigration.manifest
    "ManifestPassenger",  # gda.model.source.immigration.manifest
    "NaturalizationRecord",  # gda.model.source.immigration.naturalization
    "NaturalizationWitness",  # gda.model.source.immigration.naturalization
]
