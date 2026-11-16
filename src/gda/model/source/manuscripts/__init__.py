"""Path: src/gda/model/source/manuscripts/__init__.py

Family Bible vital registers, manuscript collections, correspondence, diaries, and narratives.

Operational Role:
    Exports FamilyBibleRecord, BibleRegisterEntry, and NarrativeManuscriptRecord
    domain models.
"""

from __future__ import annotations

from gda.model.source.manuscripts.bible import BibleRegisterEntry, FamilyBibleRecord
from gda.model.source.manuscripts.narrative import NarrativeManuscriptRecord

__version__ = "1.0.0+build.3"

__all__ = [
    "BibleRegisterEntry",  # gda.model.source.manuscripts.bible
    "FamilyBibleRecord",  # gda.model.source.manuscripts.bible
    "NarrativeManuscriptRecord",  # gda.model.source.manuscripts.narrative
]
