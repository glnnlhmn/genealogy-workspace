"""Path: tests/test_gda/test_model/test_base/test_transcript.py

Test harness for archival Transcript dataclass and enums.
"""

from __future__ import annotations

import pytest

from gda.core.errors import ModelFormatError
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import TranscriptID
from gda.model.base.audit import AuditStamp
from gda.model.base.transcript import Legibility, TextQuality, Transcript

__version__ = "1.0.0+build.6"

VALID_UUID_1 = "11111111-1111-4111-8111-111111111111"
VALID_UUID_2 = "22222222-2222-4222-8222-222222222222"
VALID_UUID_3 = "33333333-3333-4333-8333-333333333333"


@pytest.fixture
def sample_audit() -> AuditStamp:
    """Fixture providing a standard valid AuditStamp."""
    ts = IsoTimestamp("2026-01-01T00:00:00Z")
    return AuditStamp(created_at=ts, updated_at=ts)


# ==========================================================================
# GROUP 1: Instantiation & Properties
# ==========================================================================


@pytest.mark.unit
def test_transcript_instantiation_minimal(sample_audit: AuditStamp):
    """Verify default instantiation of Transcript with valid fields."""
    tid = TranscriptID(VALID_UUID_1)
    transcript = Transcript(
        transcript_id=tid,
        verbatim_text="In the name of God, Amen. I, John Doe...",
        audit=sample_audit,
    )
    assert transcript.transcript_id == tid
    assert transcript.word_count == 9
    assert transcript.text_quality == TextQuality.VERBATIM
    assert transcript.legibility == Legibility.CLEAR
    assert transcript.abstract is None
    assert str(transcript) == "In the name of God, Amen. I, John Doe..."


@pytest.mark.unit
def test_transcript_instantiation_with_metadata(sample_audit: AuditStamp):
    """Verify instantiation with abstracts, keywords, and explicit quality tiers."""
    tid = TranscriptID(VALID_UUID_2)
    long_text = "Word " * 20
    transcript = Transcript(
        transcript_id=tid,
        verbatim_text=long_text.strip(),
        audit=sample_audit,
        abstract="Summary of testamentary bequest.",
        keywords=["will", "probate", "1850"],
        text_quality=TextQuality.PARTIAL,
        legibility=Legibility.FADED,
    )
    assert transcript.word_count == 20
    assert transcript.text_quality == TextQuality.PARTIAL
    assert transcript.legibility == Legibility.FADED
    assert str(transcript).endswith("...")
    assert "Transcript" in repr(transcript)


# ==========================================================================
# GROUP 2: Validation Failure & Defensive Invariants
# ==========================================================================


@pytest.mark.regression
def test_transcript_empty_text_raises_model_format_error(sample_audit: AuditStamp):
    """Verify empty or whitespace-only verbatim text raises ModelFormatError."""
    tid = TranscriptID(VALID_UUID_3)
    with pytest.raises(ModelFormatError, match="verbatim_text cannot be empty"):
        Transcript(
            transcript_id=tid,
            verbatim_text="   ",
            audit=sample_audit,
        )


@pytest.mark.unit
def test_transcript_introspectable_help_callable(sample_audit: AuditStamp):
    """Verify IntrospectableMixin .help() executes without raising exceptions."""
    tid = TranscriptID(VALID_UUID_1)
    transcript = Transcript(
        transcript_id=tid,
        verbatim_text="Sample text for testing",
        audit=sample_audit,
    )
    transcript.help()
