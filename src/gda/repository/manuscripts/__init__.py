"""Path: src/gda/repository/manuscripts/__init__.py

SQLite repositories and in-memory collections for Manuscripts archival sources.
"""

from __future__ import annotations

from gda.repository.manuscripts.collection import (
    FamilyBibleCollection,
    NarrativeManuscriptCollection,
)
from gda.repository.manuscripts.repository import (
    FamilyBibleRepository,
    NarrativeManuscriptRepository,
)

__version__ = "1.0.0+build.2"

__all__ = [
    "FamilyBibleCollection",
    "FamilyBibleRepository",
    "NarrativeManuscriptCollection",
    "NarrativeManuscriptRepository",
]
