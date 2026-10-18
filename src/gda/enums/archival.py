# Name: archival.py
# Path: src/gda/enums/archival.py

"""Archival notes, transcription clarity, physical media orientation, and formats."""

from __future__ import annotations

from enum import StrEnum

__version__ = "0.1.0+build.r1"

__all__ = [
    "DocumentSide",
    "NoteCategory",
    "NoteType",
    "PublicationFrequency",
    "SelectiveServiceClass",
    "TestimonyMedium",
    "TranscriptLegibility",
    "WwiCardType",
]


class NoteType(StrEnum):
    """Archival contextual note classification."""

    RESEARCH = "RESEARCH"
    HISTORICAL = "HISTORICAL"
    TRANSCRIPTION = "TRANSCRIPTION"
    DISCREPANCY = "DISCREPANCY"
    PROVENANCE = "PROVENANCE"
    GENERAL = "GENERAL"


class NoteCategory(StrEnum):
    """Archival workflow and anomaly taxonomy for research notes."""

    GENERAL = "GENERAL"
    RESEARCH_TODO = "RESEARCH_TODO"
    ANOMALY = "ANOMALY"
    RESEARCH = "RESEARCH"
    DISCREPANCY = "DISCREPANCY"
    TRANSCRIPTION = "TRANSCRIPTION"
    CORRECTION = "CORRECTION"
    PROVENANCE = "PROVENANCE"
    UNKNOWN = "UNKNOWN"


class DocumentSide(StrEnum):
    """Physical archival document side or orientation."""

    FRONT = "FRONT"
    BACK = "BACK"
    INSIDE = "INSIDE"
    OUTSIDE = "OUTSIDE"
    ENCLOSURE = "ENCLOSURE"
    UNKNOWN = "UNKNOWN"


class TranscriptLegibility(StrEnum):
    """Visual legibility ratings for source record text."""

    CLEAR = "CLEAR"
    FAINT = "FAINT"
    DAMAGED = "DAMAGED"
    PARTIAL = "PARTIAL"
    ILLEGIBLE = "ILLEGIBLE"


class PublicationFrequency(StrEnum):
    """Periodicity of serial publications and newspapers."""

    DAILY = "Daily"
    WEEKLY = "Weekly"
    SEMI_WEEKLY = "Semi-Weekly"
    MONTHLY = "Monthly"


class TestimonyMedium(StrEnum):
    """Physical format of personal testimony, memoirs, and narratives."""

    MANUSCRIPT = "Manuscript (Handwritten)"
    TYPESCRIPT = "Typescript"
    PRINTED_BIBLE_REGISTER = "Printed Bible Register"
    AUDIO_RECORDING_TRANSCRIPT = "Audio Recording Transcript"
    PHOTOCOPY = "Photocopy"
    OTHER = "Other"


class SelectiveServiceClass(StrEnum):
    """Selective service military classification codes."""

    CLASS_1_A = "1-A"
    CLASS_1_C = "1-C"
    CLASS_2_A = "2-A"
    CLASS_2_B = "2-B"
    CLASS_3_A = "3-A"
    CLASS_4_A = "4-A"
    CLASS_4_D = "4-D"
    CLASS_4_F = "4-F"
    UNKNOWN = "UNKNOWN"


class WwiCardType(StrEnum):
    """WWI draft registration schedule card classification."""

    CARD_A = "Card A (1917)"
    CARD_B = "Card B (1918)"
    CARD_C = "Card C (1918)"
    UNKNOWN = "Unknown"
