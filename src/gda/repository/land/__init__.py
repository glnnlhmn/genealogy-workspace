"""Path: src/gda/repository/land/__init__.py

SQLite repositories and in-memory collections for Land archival source records.
"""

from __future__ import annotations

from gda.repository.land.collection import (
    LandDeedCollection,
    LandGrantCollection,
)
from gda.repository.land.repository import (
    LandDeedRepository,
    LandGrantRepository,
)

__version__ = "1.0.0+build.1"

__all__ = [
    "LandDeedCollection",
    "LandDeedRepository",
    "LandGrantCollection",
    "LandGrantRepository",
]
