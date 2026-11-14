"""Path: src/gda/model/manuscripts/__init__.py

Family Bible vital registers, manuscript collections, correspondence, diaries, and narratives.

Operational Role:
    Exports FamilyBibleRecord, BibleRegisterEntry, and NarrativeManuscriptRecord
    domain models.
"""

from __future__ import annotations

from gda.model.manuscripts.bible import BibleRegisterEntry, FamilyBibleRecord
from gda.model.manuscripts.narrative import NarrativeManuscriptRecord

__version__ = "1.0.0+build.2"

__all__ = [
    "BibleRegisterEntry",
    "FamilyBibleRecord",
    "NarrativeManuscriptRecord",
]
