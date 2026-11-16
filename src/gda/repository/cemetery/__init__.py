"""Path: src/gda/repository/cemetery/__init__.py

SQLite repositories and in-memory collections for Cemetery archival source records.
"""

from __future__ import annotations

from gda.repository.cemetery.collection import (
    CemeteryMarkerCollection,
    CemeteryRegistryCollection,
)
from gda.repository.cemetery.repository import (
    CemeteryMarkerRepository,
    CemeteryRegistryRepository,
)

__version__ = "1.0.0+build.2"

__all__ = [
    "CemeteryMarkerCollection",
    "CemeteryMarkerRepository",
    "CemeteryRegistryCollection",
    "CemeteryRegistryRepository",
]
