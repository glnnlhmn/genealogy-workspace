"""Path: src/gda/enums/archival.py

Backward-compatible re-export facade routing archival/document enums to gda.core.enums.
"""

from __future__ import annotations

from gda.core.enums import (
    DocumentSide,
    Legibility,
    NoteType,
    QualityAssessment,
    QuayScore,
    TestimonyMedium,
    TextQuality,
    TranscriptLegibility,
)

__all__ = [
    "DocumentSide",
    "Legibility",
    "NoteType",
    "QualityAssessment",
    "QuayScore",
    "TestimonyMedium",
    "TextQuality",
    "TranscriptLegibility",
]
