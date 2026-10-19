"""Path: tests/test_gda/test_enums/test_archival_enums.py

Targeted behavioral test suite verifying archival document and transcript enums.

Operational Role:
    Validates physical document orientation, visual legibility ratings,
    note classifications, publication frequencies, and historical draft cards.

Test Structure & Protocol:
    - Atomized tests: 1:1 verification per behavioral contract.
    - Fully decorated: Explicitly decorated with registered pytest markers.
    - Dependencies: In-memory only; zero physical disk I/O.
"""

from __future__ import annotations

import pytest

from gda.enums.archival import (
    DocumentSide,
    NoteCategory,
    NoteType,
    PublicationFrequency,
    SelectiveServiceClass,
    TestimonyMedium,
    TranscriptLegibility,
    WwiCardType,
)

__version__ = "0.1.0+build.2"

# Prevent pytest from attempting to collect the enum as a test class due to the "Test*" prefix
TestimonyMedium.__test__ = False


# ==============================================================================
# GROUP 1: Document Orientation & Physical Media
# Note: Verification of DocumentSide, TestimonyMedium, and TranscriptLegibility
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_document_side_tokens() -> None:
    """Verify DocumentSide physical orientations."""
    assert DocumentSide.FRONT == "FRONT"
    assert DocumentSide.BACK == "BACK"
    assert DocumentSide.INSIDE == "INSIDE"
    assert DocumentSide.OUTSIDE == "OUTSIDE"
    assert DocumentSide.ENCLOSURE == "ENCLOSURE"
    assert DocumentSide.UNKNOWN == "UNKNOWN"


@pytest.mark.unit
def test_transcript_legibility_ratings() -> None:
    """Verify TranscriptLegibility visual clarity ratings."""
    assert TranscriptLegibility.CLEAR == "CLEAR"
    assert TranscriptLegibility.FAINT == "FAINT"
    assert TranscriptLegibility.DAMAGED == "DAMAGED"
    assert TranscriptLegibility.PARTIAL == "PARTIAL"
    assert TranscriptLegibility.ILLEGIBLE == "ILLEGIBLE"


@pytest.mark.unit
def test_testimony_medium_descriptive_strings() -> None:
    """Verify TestimonyMedium descriptive string representations."""
    assert TestimonyMedium.MANUSCRIPT == "Manuscript (Handwritten)"
    assert TestimonyMedium.TYPESCRIPT == "Typescript"
    assert TestimonyMedium.PRINTED_BIBLE_REGISTER == "Printed Bible Register"


# ==============================================================================
# GROUP 2: Editorial & Research Notes
# Note: Verification of NoteType and NoteCategory workflow boundaries
# ==============================================================================


@pytest.mark.unit
def test_note_type_tokens() -> None:
    """Verify NoteType contextual classifications."""
    assert NoteType.RESEARCH == "RESEARCH"
    assert NoteType.HISTORICAL == "HISTORICAL"
    assert NoteType.TRANSCRIPTION == "TRANSCRIPTION"
    assert NoteType.DISCREPANCY == "DISCREPANCY"
    assert NoteType.PROVENANCE == "PROVENANCE"
    assert NoteType.GENERAL == "GENERAL"


@pytest.mark.unit
def test_note_category_workflow_tokens() -> None:
    """Verify NoteCategory research workflow taxonomies."""
    assert NoteCategory.GENERAL == "GENERAL"
    assert NoteCategory.RESEARCH_TODO == "RESEARCH_TODO"
    assert NoteCategory.ANOMALY == "ANOMALY"
    assert NoteCategory.CORRECTION == "CORRECTION"


# ==============================================================================
# GROUP 3: Periodicals & Selective Service Classifications
# Note: Verification of PublicationFrequency, SelectiveServiceClass, and WwiCardType
# ==============================================================================


@pytest.mark.unit
def test_publication_frequency_tokens() -> None:
    """Verify PublicationFrequency serial periodicity strings."""
    assert PublicationFrequency.DAILY == "Daily"
    assert PublicationFrequency.WEEKLY == "Weekly"
    assert PublicationFrequency.MONTHLY == "Monthly"


@pytest.mark.unit
def test_selective_service_and_wwi_draft_cards() -> None:
    """Verify selective service classifications and WWI card categories."""
    assert SelectiveServiceClass.CLASS_1_A == "1-A"
    assert SelectiveServiceClass.CLASS_4_F == "4-F"
    assert WwiCardType.CARD_A == "Card A (1917)"
    assert WwiCardType.CARD_B == "Card B (1918)"
