"""Path: src/gda/repository/immigration/__init__.py

SQLite repositories and in-memory collections for Immigration archival source records.
"""

from __future__ import annotations

from gda.repository.immigration.collection import (
    ImmigrationManifestCollection,
    NaturalizationCollection,
)
from gda.repository.immigration.repository import (
    ImmigrationManifestRepository,
    NaturalizationRepository,
)

__version__ = "1.0.0+build.1"

__all__ = [
    "ImmigrationManifestCollection",
    "ImmigrationManifestRepository",
    "NaturalizationCollection",
    "NaturalizationRepository",
]
