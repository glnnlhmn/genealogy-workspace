"""Path: tests/test_gda/test_model/test_base/test_composites/test_transcript.py

Comprehensive test suite for archival Transcript dataclass and enums.

Operational Role:
    Verifies Transcript instantiation, word_count calculation, .create() factory,
    copy-on-write mutators, strict validation invariants, and JSON/dict
    serialization round-trips with 100% statement and branch coverage.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from gda.core.enums.archival import Legibility, TextQuality
from gda.core.errors import ModelFormatError
from gda.model.atom.id import TranscriptID
from gda.model.base.audit import AuditStamp
from gda.model.base.transcript import Transcript

__version__ = "1.1.0+build.1"

VALID_UUID_1 = "11111111-1111-4111-8111-111111111111"
VALID_UUID_2 = "22222222-2222-4222-8222-222222222222"
VALID_UUID_3 = "33333333-3333-4333-8333-333333333333"


# ==========================================================================
# GROUP 1: INSTANTIATION, FACTORY & MUTATORS
# ==========================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_transcript_instantiation_minimal(golden_audit: AuditStamp) -> None:
    """Verify default instantiation of Transcript with valid fields."""
    tid = TranscriptID(VALID_UUID_1)
    transcript = Transcript(
        transcript_id=tid,
        verbatim_text="In the name of God, Amen. I, John Doe...",
        audit=golden_audit,
    )
    assert transcript.transcript_id == tid
    assert transcript.word_count == 9
    assert transcript.text_quality == TextQuality.VERBATIM
    assert transcript.legibility == Legibility.CLEAR
    assert transcript.abstract is None
    assert str(transcript) == "In the name of God, Amen. I, John Doe..."


@pytest.mark.unit
def test_transcript_instantiation_with_metadata(golden_audit: AuditStamp) -> None:
    """Verify instantiation with abstracts, keywords, and explicit quality tiers."""
    tid = TranscriptID(VALID_UUID_2)
    long_text = "Word " * 20
    transcript = Transcript(
        transcript_id=tid,
        verbatim_text=long_text.strip(),
        audit=golden_audit,
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


@pytest.mark.unit
def test_transcript_create_factory_and_mutators(sample_transcript: Transcript) -> None:
    """Verify Transcript.create() normalization and copy-on-write mutators."""
    created = Transcript.create(
        transcript_id=VALID_UUID_2,
        verbatim_text="  Full verbatim extract.  ",
        abstract="  Short abstract  ",
        keywords=["probate", "  probate  ", "deed", ""],
        text_quality="abstract",
        legibility="poor_handwriting",
    )
    assert created.verbatim_text == "Full verbatim extract."
    assert created.abstract == "Short abstract"
    assert created.keywords == ["probate", "deed"]
    assert created.text_quality == TextQuality.ABSTRACT
    assert created.legibility == Legibility.POOR_HANDWRITING

    with pytest.raises(ModelFormatError, match="Invalid TextQuality value"):
        Transcript.create(
            transcript_id=VALID_UUID_2,
            verbatim_text="Text",
            text_quality="BAD_QUALITY",
        )

    with pytest.raises(ModelFormatError, match="Invalid TextQuality type"):
        Transcript.create(
            transcript_id=VALID_UUID_2,
            verbatim_text="Text",
            text_quality=123,  # type: ignore[arg-type]
        )

    with pytest.raises(ModelFormatError, match="Invalid Legibility value"):
        Transcript.create(
            transcript_id=VALID_UUID_2,
            verbatim_text="Text",
            legibility="BAD_LEGIBILITY",
        )

    with pytest.raises(ModelFormatError, match="Invalid Legibility type"):
        Transcript.create(
            transcript_id=VALID_UUID_2,
            verbatim_text="Text",
            legibility=123,  # type: ignore[arg-type]
        )

    up_text = sample_transcript.update_text("  Updated transcript text  ")
    assert up_text is not sample_transcript
    assert up_text.verbatim_text == "Updated transcript text"

    up_abs = sample_transcript.update_abstract("  Concise abstract  ")
    assert up_abs is not sample_transcript
    assert up_abs.abstract == "Concise abstract"
    assert up_abs.update_abstract("Concise abstract") is up_abs
    assert up_abs.update_abstract(None).abstract is None


# ==========================================================================
# GROUP 2: VALIDATION FAILURE, SERIALIZATION & INTROSPECTION
# ==========================================================================


@pytest.mark.unit
@pytest.mark.regression
def test_transcript_validation_failures(golden_audit: AuditStamp) -> None:
    """Verify empty text, blank abstract, blank/duplicate keywords, and strict mode errors."""
    tid = TranscriptID(VALID_UUID_3)
    with pytest.raises(ModelFormatError, match="verbatim_text cannot be empty"):
        Transcript(transcript_id=tid, verbatim_text="   ", audit=golden_audit)

    with pytest.raises(ModelFormatError, match="Transcript abstract cannot be blank"):
        Transcript(
            transcript_id=tid,
            verbatim_text="Valid text",
            audit=golden_audit,
            abstract="   ",
        )

    with pytest.raises(ModelFormatError, match="Transcript keywords cannot contain empty"):
        Transcript(
            transcript_id=tid,
            verbatim_text="Valid text",
            audit=golden_audit,
            keywords=["   "],
        )

    with pytest.raises(ModelFormatError, match="Duplicate keyword entries detected"):
        Transcript(
            transcript_id=tid,
            verbatim_text="Valid text",
            audit=golden_audit,
            keywords=["will", "will"],
        )

    with pytest.raises(ValidationError):
        Transcript(
            transcript_id=VALID_UUID_3,  # type: ignore[arg-type]
            verbatim_text="Valid text",
            audit=golden_audit,
        )


@pytest.mark.unit
def test_transcript_serialization_round_trip(
    sample_transcript: Transcript, golden_audit: AuditStamp
) -> None:
    """Verify Transcript to_dict, from_dict, to_json, and from_json round-trip fidelity."""
    min_payload = sample_transcript.to_dict()
    assert "abstract" not in min_payload
    assert Transcript.from_dict(min_payload) == sample_transcript

    rich = Transcript.create(
        transcript_id=VALID_UUID_2,
        verbatim_text="Full record text",
        audit=golden_audit,
        abstract="Abstract summary",
        keywords=["census"],
    )
    rich_payload = rich.to_dict()
    assert rich_payload["abstract"] == "Abstract summary"
    assert Transcript.from_dict(rich_payload) == rich

    obj_payload = dict(rich_payload)
    obj_payload["audit"] = golden_audit
    assert Transcript.from_dict(obj_payload) == rich

    json_str = rich.to_json()
    assert Transcript.from_json(json_str) == rich

    with pytest.raises(ModelFormatError, match="Transcript payload must be a dictionary"):
        Transcript.from_dict("bad")  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="Missing required fields for Transcript"):
        Transcript.from_dict({"transcript_id": VALID_UUID_1})

    with pytest.raises(ModelFormatError, match="Audit dictionary missing created_at"):
        Transcript.from_dict(
            {
                "transcript_id": VALID_UUID_1,
                "verbatim_text": "Text",
                "audit": {"created_at": "2026-01-01T00:00:00Z"},
            }
        )

    with pytest.raises(ModelFormatError, match="Transcript audit must be an AuditStamp"):
        Transcript.from_dict(
            {
                "transcript_id": VALID_UUID_1,
                "verbatim_text": "Text",
                "audit": "bad",
            }
        )

    with pytest.raises(ModelFormatError, match="Failed to parse Transcript JSON"):
        Transcript.from_json("{invalid-json")


@pytest.mark.unit
def test_transcript_introspectable_help_callable(sample_transcript: Transcript) -> None:
    """Verify IntrospectableMixin .help() executes cleanly."""
    help_text = sample_transcript.help(as_str=True)
    assert help_text is not None
    assert "=== Transcript Public Directory ===" in help_text
