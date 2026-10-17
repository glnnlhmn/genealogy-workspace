# Name: test_transcript.py
# Path: tests/test_gda/test_model/test_base/test_transcript.py

"""Comprehensive test suite verifying TranscriptModel and quality enumerations.

Operational Role:
    Verifies that TranscriptModel enforces valid TranscriptIDs, non-empty verbatim text,
    accurate word count calculations, text truncation display, and immutability.

Test Structure & Protocol:
    - Atomized tests: 1:1 behavioral contract mapping.
    - Fully decorated: Standard 7-marker taxonomy.
    - Zero production disk I/O.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from gda.model.atom.date import IsoTimestamp
from gda.model.atom.errors import AtomFormatError
from gda.model.atom.id import TranscriptID
from gda.model.base.audit import AuditStamp
from gda.model.base.transcript import Legibility, TextQuality, TranscriptModel

__version__ = "1.0.0+build.r9"


# ==============================================================================
# GROUP 1: TRANSCRIPTMODEL CREATION & CALCULATED PROPERTIES
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_transcript_model_valid_creation() -> None:
    """Verify TranscriptModel instantiates and accurately computes word_count."""
    tid = TranscriptID("b2c3d4e5-f6a7-4b8c-9d0e-1f2a3b4c5d6e")
    t1 = IsoTimestamp("2026-10-16T12:00:00Z")
    audit = AuditStamp(created_at=t1, updated_at=t1)

    transcript = TranscriptModel(
        transcript_id=tid,
        verbatim_text="In the year of our Lord eighteen hundred and eighty.",
        abstract="Opening statement of deed transfer.",
        keywords=["deed", "eighteen hundred"],
        text_quality=TextQuality.VERBATIM,
        legibility=Legibility.CLEAR,
        audit=audit,
    )
    assert transcript.transcript_id == tid
    assert (
        transcript.verbatim_text
        == "In the year of our Lord eighteen hundred and eighty."
    )
    assert transcript.abstract == "Opening statement of deed transfer."
    assert transcript.keywords == ["deed", "eighteen hundred"]
    assert transcript.text_quality == TextQuality.VERBATIM
    assert transcript.legibility == Legibility.CLEAR
    assert transcript.word_count == 10
    assert str(transcript) == "In the year of our Lord eighteen hundred and eighty."
    assert repr(transcript) == (
        "TranscriptModel(transcript_id=TranscriptID(value='b2c3d4e5-f6a7-4b8c-9d0e-1f2a3b4c5d6e'), "
        "words=10, quality=VERBATIM, legibility=CLEAR, "
        "audit=AuditStamp(created_at=IsoTimestamp(value='2026-10-16T12:00:00Z'), "
        "updated_at=IsoTimestamp(value='2026-10-16T12:00:00Z')))"
    )


@pytest.mark.unit
@pytest.mark.smoke
def test_transcript_model_long_text_truncation() -> None:
    """Verify TranscriptModel str representation truncates strings exceeding 60 characters."""
    tid = TranscriptID("b2c3d4e5-f6a7-4b8c-9d0e-1f2a3b4c5d6e")
    t1 = IsoTimestamp("2026-10-16T12:00:00Z")
    audit = AuditStamp(created_at=t1, updated_at=t1)
    long_text = "This is an exceptionally long historical transcription string that extends well past sixty characters."

    transcript = TranscriptModel(
        transcript_id=tid,
        verbatim_text=long_text,
        audit=audit,
    )
    assert len(str(transcript)) == 60
    assert str(transcript).endswith("...")


# ==============================================================================
# GROUP 2: DEFENSIVE BOUNDARIES & IMMUTABILITY
# ==============================================================================


@pytest.mark.unit
@pytest.mark.regression
@pytest.mark.parametrize("blank_text", ["", "   ", "\t\n"])
def test_transcript_model_blank_text_raises_error(blank_text: str) -> None:
    """Verify TranscriptModel raises AtomFormatError if verbatim_text is blank."""
    tid = TranscriptID("b2c3d4e5-f6a7-4b8c-9d0e-1f2a3b4c5d6e")
    t1 = IsoTimestamp("2026-10-16T12:00:00Z")
    audit = AuditStamp(created_at=t1, updated_at=t1)

    with pytest.raises(AtomFormatError, match="verbatim_text cannot be empty"):
        TranscriptModel(
            transcript_id=tid,
            verbatim_text=blank_text,
            audit=audit,
        )


@pytest.mark.unit
def test_transcript_enumerations_members() -> None:
    """Verify TextQuality and Legibility contain expected classifications."""
    expected_quality = {"VERBATIM", "PARTIAL", "ABSTRACT", "DAMAGED", "ILLEGIBLE"}
    expected_legibility = {
        "CLEAR",
        "FADED",
        "TORN",
        "STAINED",
        "POOR_HANDWRITING",
        "PARTIALLY_ILLEGIBLE",
        "ILLEGIBLE",
    }
    assert {quality.value for quality in TextQuality} == expected_quality
    assert {legibility.value for legibility in Legibility} == expected_legibility


@pytest.mark.unit
def test_transcript_model_immutability() -> None:
    """Verify TranscriptModel is frozen and immutable."""
    tid = TranscriptID("b2c3d4e5-f6a7-4b8c-9d0e-1f2a3b4c5d6e")
    t1 = IsoTimestamp("2026-10-16T12:00:00Z")
    audit = AuditStamp(created_at=t1, updated_at=t1)

    transcript = TranscriptModel(
        transcript_id=tid,
        verbatim_text="Sample text.",
        audit=audit,
    )
    with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
        transcript.verbatim_text = "New text."  # type: ignore[misc]
