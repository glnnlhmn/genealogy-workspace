"""Path: tests/test_gda/test_core/test_enums/test_archival_enums.py

Targeted behavioral test suite for gda.core.enums.archival.

Operational Role:
    Verifies the 6 authoritative archival enums (DocumentSide, Legibility,
    NoteType, PublicationFrequency, TestimonyMedium, TextQuality) following
    Phase 3 retirement of TranscriptLegibility/SelectiveServiceClass and
    relocation of military/physical enums to military.py and vital.py.

Test Structure & Protocol:
    - Atomized & parametrized tests: 1:1 behavioral contract mapping.
    - Fully decorated: 5-marker taxonomy (smoke, unit, regression).
    - Dependencies: In-memory only; zero physical disk I/O.
"""

from __future__ import annotations

import pytest

import gda.core.enums.archival as archival_enums
from gda.core.enums.archival import (
    DocumentSide,
    Legibility,
    NoteType,
    PublicationFrequency,
    TextQuality,
)
from gda.core.enums.archival import (
    TestimonyMedium as _TestimonyMedium,
)

__version__ = "1.0.0+build.7"


# ==============================================================================
# GROUP 1: Smoke & Primary Entrypoints
# Note: Single smoke gate freezing the 6 authoritative archival exports (Phase 3).
# ==============================================================================


@pytest.mark.smoke
@pytest.mark.unit
def test_archival_enums_exposes_expected_public_interface() -> None:
    """Verify gda.core.enums.archival exports only the 6 archival enums (Phase 3 TDD Red)."""
    expected = {
        "DocumentSide",
        "Legibility",
        "NoteType",
        "PublicationFrequency",
        "TestimonyMedium",
        "TextQuality",
    }
    assert set(archival_enums.__all__) == expected


# ==============================================================================
# GROUP 2: Core Logic & Happy Paths
# Note: Canonical UPPER_SNAKE_CASE values across all 6 archival enums.
# ==============================================================================


@pytest.mark.unit
def test_document_side_and_legibility_values() -> None:
    """Verify DocumentSide and canonical Legibility members and string values."""
    assert DocumentSide.FRONT == "FRONT"
    assert DocumentSide.BACK == "BACK"
    assert DocumentSide.INSIDE == "INSIDE"
    assert DocumentSide.OUTSIDE == "OUTSIDE"
    assert DocumentSide.ENCLOSURE == "ENCLOSURE"
    assert DocumentSide.UNKNOWN == "UNKNOWN"

    assert Legibility.CLEAR == "CLEAR"
    assert Legibility.FAINT == "FAINT"
    assert Legibility.DAMAGED == "DAMAGED"
    assert Legibility.PARTIAL == "PARTIAL"
    assert Legibility.ILLEGIBLE == "ILLEGIBLE"


@pytest.mark.unit
def test_note_type_and_text_quality_values() -> None:
    """Verify NoteType and TextQuality canonical archival classifications."""
    assert {m.value for m in NoteType} == {"GENERAL", "RESEARCH", "DISCREPANCY", "PROOF"}
    assert TextQuality.VERBATIM == "VERBATIM"
    assert len(TextQuality) >= 1


@pytest.mark.unit
def test_testimony_medium_upper_snake_case_values() -> None:
    """Verify TestimonyMedium uses UPPER_SNAKE_CASE tokens (Phase 3 TDD Red)."""
    assert _TestimonyMedium.MANUSCRIPT == "MANUSCRIPT"
    assert _TestimonyMedium.TYPESCRIPT == "TYPESCRIPT"
    assert _TestimonyMedium.PRINTED_BIBLE_REGISTER == "PRINTED_BIBLE_REGISTER"
    assert _TestimonyMedium.AUDIO_RECORDING_TRANSCRIPT == "AUDIO_RECORDING_TRANSCRIPT"
    assert _TestimonyMedium.PHOTOCOPY == "PHOTOCOPY"
    assert _TestimonyMedium.OTHER == "OTHER"


@pytest.mark.unit
def test_publication_frequency_upper_snake_case_values() -> None:
    """Verify PublicationFrequency uses UPPER_SNAKE_CASE tokens (Phase 3 TDD Red)."""
    assert PublicationFrequency.DAILY == "DAILY"
    assert PublicationFrequency.WEEKLY == "WEEKLY"
    assert PublicationFrequency.SEMI_WEEKLY == "SEMI_WEEKLY"
    assert PublicationFrequency.MONTHLY == "MONTHLY"


# ==============================================================================
# GROUP 3: Edge Cases & Boundary Conditions
# Note: String/hash interoperability for NoteType dictionary keys.
# ==============================================================================


@pytest.mark.unit
def test_note_type_string_and_hash_invariants() -> None:
    """Verify NoteType members evaluate as strings and work in set/dict keys."""
    assert isinstance(NoteType.PROOF, str)
    assert f"{NoteType.PROOF}" == "PROOF"
    lookup: dict[str, str] = {NoteType.RESEARCH: "lead"}
    assert lookup["RESEARCH"] == "lead"
    assert NoteType["DISCREPANCY"] is NoteType.DISCREPANCY


# ==============================================================================
# GROUP 4: Error Handling & Validation Failures
# Note: Strict invalid value, casing, whitespace, and key-lookup rejection.
# ==============================================================================


@pytest.mark.regression
@pytest.mark.parametrize("bad_value", ["INVALID_TYPE", "CITATION", "proof", " GENERAL ", ""])
def test_note_type_rejects_invalid_case_and_whitespace_values(bad_value: str) -> None:
    """Verify NoteType strictly rejects unregistered, mixed-case, and padded values."""
    with pytest.raises(ValueError):
        NoteType(bad_value)


@pytest.mark.regression
def test_note_type_key_lookup_error() -> None:
    """Verify dictionary-style member lookup raises KeyError for invalid keys."""
    with pytest.raises(KeyError):
        _ = NoteType["NON_EXISTENT"]
