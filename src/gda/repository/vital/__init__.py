"""Path: src/gda/repository/vital/__init__.py

SQLite repositories and in-memory collections for Vital archival source records.
"""

from __future__ import annotations

from gda.repository.vital.collection import (
    BaptismCollection,
    BirthCollection,
    DeathCollection,
    DivorceCollection,
    MarriageCollection,
)
from gda.repository.vital.repository import (
    BaptismRepository,
    BirthRepository,
    DeathRepository,
    DivorceRepository,
    MarriageRepository,
)

__version__ = "1.0.0+build.2"

__all__ = [
    "BaptismCollection",
    "BaptismRepository",
    "BirthCollection",
    "BirthRepository",
    "DeathCollection",
    "DeathRepository",
    "DivorceCollection",
    "DivorceRepository",
    "MarriageCollection",
    "MarriageRepository",
]
