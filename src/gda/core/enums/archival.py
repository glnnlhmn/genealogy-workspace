"""Path: src/gda/core/enums/archival.py

Controlled enumerations for physical documents, transcripts, and archival artifacts.

Operational Role:
    Defines controlled vocabularies for physical media orientations, transcript
    accuracy metrics, legibility ratings, archival note types, testimony media,
    and serial publication frequencies.
"""

from __future__ import annotations

from gda.core.enums.base import GDAStrEnum

__version__ = "1.0.0+build.2"

__all__ = [
    "DocumentSide",
    "Legibility",
    "NoteType",
    "PublicationFrequency",
    "TestimonyMedium",
    "TextQuality",
]


class DocumentSide(GDAStrEnum):
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


class TextQuality(GDAStrEnum):
    """Controlled classification of transcription accuracy."""

    VERBATIM = "VERBATIM"
    PARTIAL = "PARTIAL"
    ABSTRACT = "ABSTRACT"
    DAMAGED = "DAMAGED"
    ILLEGIBLE = "ILLEGIBLE"


class Legibility(GDAStrEnum):
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


class NoteType(GDAStrEnum):
    """Taxonomic classification of archival research and analysis notes."""

    GENERAL = "GENERAL"
    RESEARCH = "RESEARCH"
    DISCREPANCY = "DISCREPANCY"
    PROOF = "PROOF"


class TestimonyMedium(GDAStrEnum):
    """Authoritative physical or recorded medium for oral/written testimony."""

    MANUSCRIPT = "MANUSCRIPT"
    TYPESCRIPT = "TYPESCRIPT"
    PRINTED_BIBLE_REGISTER = "PRINTED_BIBLE_REGISTER"
    AUDIO_RECORDING_TRANSCRIPT = "AUDIO_RECORDING_TRANSCRIPT"
    PHOTOCOPY = "PHOTOCOPY"
    OTHER = "OTHER"


class PublicationFrequency(GDAStrEnum):
    """Serial publication schedule classifications for periodicals."""

    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    SEMI_WEEKLY = "SEMI_WEEKLY"
    MONTHLY = "MONTHLY"
