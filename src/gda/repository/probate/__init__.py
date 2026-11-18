"""Path: src/gda/repository/probate/__init__.py

SQLite repositories and in-memory collections for Probate archival source records.
"""

from __future__ import annotations

from gda.repository.probate.collection import (
    EstateInventoryCollection,
    ProbateCollection,
)
from gda.repository.probate.repository import (
    EstateInventoryRepository,
    ProbateRepository,
)

__version__ = "1.0.0+build.1"

__all__ = [
    "EstateInventoryCollection",
    "EstateInventoryRepository",
    "ProbateCollection",
    "ProbateRepository",
]
