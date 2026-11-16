"""Path: src/gda/core/enums/archival.py

Controlled enumerations for physical documents, transcripts, and archival artifacts.

Operational Role:
    Defines controlled vocabularies for physical media orientations, transcript
    accuracy metrics, legibility ratings, draft registration artifacts, and
    extracted physical trait classifications.
"""

from __future__ import annotations

from enum import StrEnum

__version__ = "1.0.0+build.1"

__all__ = [
    "DocumentSide",
    "EyeColor",
    "HairColor",
    "Legibility",
    "NoteType",
    "PhysicalBuild",
    "PublicationFrequency",
    "SelectiveServiceClass",
    "TestimonyMedium",
    "TextQuality",
    "TranscriptLegibility",
    "WwiCardType",
]


class DocumentSide(StrEnum):
    """Controlled orientation or face of physical document media."""

    FRONT = "FRONT"
    BACK = "BACK"
    INSIDE = "INSIDE"
    OUTSIDE = "OUTSIDE"
    ENVELOPE = "ENVELOPE"
    ATTACHMENT = "ATTACHMENT"
    FULL_SPREAD = "FULL_SPREAD"
    ENCLOSURE = "ENCLOSURE"
    UNKNOWN = "UNKNOWN"


class TextQuality(StrEnum):
    """Controlled classification of transcription accuracy."""

    VERBATIM = "VERBATIM"
    PARTIAL = "PARTIAL"
    ABSTRACT = "ABSTRACT"
    DAMAGED = "DAMAGED"
    ILLEGIBLE = "ILLEGIBLE"


class TranscriptLegibility(StrEnum):
    """Controlled classification of primary document legibility."""

    CLEAR = "CLEAR"
    FAINT = "FAINT"
    DAMAGED = "DAMAGED"
    PARTIAL = "PARTIAL"
    FADED = "FADED"
    TORN = "TORN"
    STAINED = "STAINED"
    POOR_HANDWRITING = "POOR_HANDWRITING"
    PARTIALLY_ILLEGIBLE = "PARTIALLY_ILLEGIBLE"
    ILLEGIBLE = "ILLEGIBLE"


# Canonical alias aligning model/base/transcript with archival enums
Legibility = TranscriptLegibility


class NoteType(StrEnum):
    """Taxonomic classification of archival research and analysis notes."""

    GENERAL = "GENERAL"
    RESEARCH = "RESEARCH"
    DISCREPANCY = "DISCREPANCY"
    PROOF = "PROOF"


class TestimonyMedium(StrEnum):
    """Authoritative physical or recorded medium for oral/written testimony."""

    MANUSCRIPT = "Manuscript (Handwritten)"
    TYPESCRIPT = "Typescript"
    PRINTED_BIBLE_REGISTER = "Printed Bible Register"
    AUDIO_RECORDING_TRANSCRIPT = "Audio Recording Transcript"
    PHOTOCOPY = "Photocopy"
    OTHER = "Other"


class PublicationFrequency(StrEnum):
    """Serial publication schedule classifications for periodicals."""

    DAILY = "Daily"
    WEEKLY = "Weekly"
    SEMI_WEEKLY = "Semi-Weekly"
    MONTHLY = "Monthly"


class SelectiveServiceClass(StrEnum):
    """Selective Service military draft classification codes."""

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
    """World War I draft registration card types based on registration dates."""

    CARD_A = "Card A (1917)"
    CARD_B = "Card B (1918)"
    CARD_C = "Card C (1918)"
    UNKNOWN = "Unknown"


class PhysicalBuild(StrEnum):
    """Physical build classifications extracted from historical draft records."""

    SLENDER = "SLENDER"
    MEDIUM = "MEDIUM"
    STOUT = "STOUT"


class EyeColor(StrEnum):
    """Eye color categories extracted from historical draft or identification cards."""

    BLUE = "BLUE"
    BROWN = "BROWN"
    GREY = "GREY"
    HAZEL = "HAZEL"
    BLACK = "BLACK"


class HairColor(StrEnum):
    """Hair color categories extracted from historical draft or identification cards."""

    BLONDE = "BLONDE"
    BROWN = "BROWN"
    BLACK = "BLACK"
    RED = "RED"
    GREY = "GREY"
    BALD = "BALD"
