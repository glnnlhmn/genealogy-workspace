"""Path: tests/test_gda/test_enums/test_archival_enums.py

Regression test suite for archival domain enumerations.

Operational Role:
    Verifies membership, string serialization, immutability, edge boundaries,
    and invalid coercion rejection across DocumentSide, TestimonyMedium,
    TranscriptLegibility, NoteType, PublicationFrequency, SelectiveServiceClass,
    WwiCardType, PhysicalBuild, EyeColor, and HairColor.
"""

from __future__ import annotations

import pytest

from gda.enums.archival import (
    DocumentSide,
    EyeColor,
    HairColor,
    NoteType,
    PhysicalBuild,
    PublicationFrequency,
    SelectiveServiceClass,
    TestimonyMedium,
    TranscriptLegibility,
    WwiCardType,
)

__version__ = "1.1.0+build.3"

# Prevent pytest test collection on TestimonyMedium
TestimonyMedium.__test__ = False


# ==============================================================================
# GROUP 1: ARCHIVAL DOCUMENT & EVIDENCE ENUMS
# Note: Verification of DocumentSide, TestimonyMedium, and TranscriptLegibility
# ==============================================================================


@pytest.mark.regression
def test_document_side_values() -> None:
    """Verify DocumentSide members and exact string values."""
    assert DocumentSide.FRONT == "FRONT"
    assert DocumentSide.BACK == "BACK"
    assert DocumentSide.INSIDE == "INSIDE"
    assert DocumentSide.OUTSIDE == "OUTSIDE"
    assert DocumentSide.ENCLOSURE == "ENCLOSURE"
    assert DocumentSide.UNKNOWN == "UNKNOWN"


@pytest.mark.regression
def test_testimony_medium_values() -> None:
    """Verify TestimonyMedium members and exact string values."""
    assert TestimonyMedium.MANUSCRIPT == "Manuscript (Handwritten)"
    assert TestimonyMedium.TYPESCRIPT == "Typescript"
    assert TestimonyMedium.PRINTED_BIBLE_REGISTER == "Printed Bible Register"
    assert TestimonyMedium.AUDIO_RECORDING_TRANSCRIPT == "Audio Recording Transcript"
    assert TestimonyMedium.PHOTOCOPY == "Photocopy"
    assert TestimonyMedium.OTHER == "Other"


@pytest.mark.regression
def test_transcript_legibility_values() -> None:
    """Verify TranscriptLegibility members and exact string values."""
    assert TranscriptLegibility.CLEAR == "CLEAR"
    assert TranscriptLegibility.FAINT == "FAINT"
    assert TranscriptLegibility.DAMAGED == "DAMAGED"
    assert TranscriptLegibility.PARTIAL == "PARTIAL"
    assert TranscriptLegibility.ILLEGIBLE == "ILLEGIBLE"


# ==============================================================================
# GROUP 2: NOTE TAXONOMY ENUMS & EDGE BOUNDARIES
# Note: Verification of NoteType values, lookup parity, and defensive rejection
# ==============================================================================


@pytest.mark.regression
def test_note_type_members() -> None:
    """Verify NoteType classifications conform to archival standard."""
    expected = {"GENERAL", "RESEARCH", "DISCREPANCY", "PROOF"}
    assert {e.value for e in NoteType} == expected


@pytest.mark.regression
def test_note_type_string_and_hash_invariants() -> None:
    """Verify NoteType members evaluate as strings and work in set/dict keys."""
    assert isinstance(NoteType.PROOF, str)
    assert f"{NoteType.PROOF}" == "PROOF"
    lookup = {NoteType.RESEARCH: "lead"}
    assert lookup["RESEARCH"] == "lead"


@pytest.mark.regression
def test_note_type_invalid_value_rejection() -> None:
    """Verify attempting to instantiate NoteType with invalid string raises ValueError."""
    with pytest.raises(ValueError):
        NoteType("INVALID_TYPE")
    with pytest.raises(ValueError):
        NoteType("CITATION")


@pytest.mark.regression
def test_note_type_case_and_whitespace_rejection() -> None:
    """Verify NoteType strictly rejects mixed-case and untrimmed whitespace."""
    with pytest.raises(ValueError):
        NoteType("proof")
    with pytest.raises(ValueError):
        NoteType(" GENERAL ")
    with pytest.raises(ValueError):
        NoteType("")


@pytest.mark.regression
def test_note_type_key_lookup_error() -> None:
    """Verify dictionary-style member lookup raises KeyError for invalid keys."""
    assert NoteType["DISCREPANCY"] is NoteType.DISCREPANCY
    with pytest.raises(KeyError):
        _ = NoteType["NON_EXISTENT"]


# ==============================================================================
# GROUP 3: PUBLICATION & SERVICE ENUMS
# Note: Verification of PublicationFrequency, SelectiveServiceClass, and WwiCardType
# ==============================================================================


@pytest.mark.regression
def test_publication_frequency_values() -> None:
    """Verify PublicationFrequency enum members."""
    assert PublicationFrequency.DAILY == "Daily"
    assert PublicationFrequency.WEEKLY == "Weekly"
    assert PublicationFrequency.SEMI_WEEKLY == "Semi-Weekly"
    assert PublicationFrequency.MONTHLY == "Monthly"


@pytest.mark.regression
def test_selective_service_class_values() -> None:
    """Verify SelectiveServiceClass formatted hyphenated values."""
    assert SelectiveServiceClass.CLASS_1_A == "1-A"
    assert SelectiveServiceClass.CLASS_1_C == "1-C"
    assert SelectiveServiceClass.CLASS_2_A == "2-A"
    assert SelectiveServiceClass.CLASS_2_B == "2-B"
    assert SelectiveServiceClass.CLASS_3_A == "3-A"
    assert SelectiveServiceClass.CLASS_4_A == "4-A"
    assert SelectiveServiceClass.CLASS_4_D == "4-D"
    assert SelectiveServiceClass.CLASS_4_F == "4-F"
    assert SelectiveServiceClass.UNKNOWN == "UNKNOWN"


@pytest.mark.regression
def test_wwi_card_type_values() -> None:
    """Verify WwiCardType questionnaire classification tokens."""
    assert WwiCardType.CARD_A == "Card A (1917)"
    assert WwiCardType.CARD_B == "Card B (1918)"
    assert WwiCardType.CARD_C == "Card C (1918)"
    assert WwiCardType.UNKNOWN == "Unknown"


# ==============================================================================
# GROUP 4: BIOGRAPHICAL PHYSICAL ATTRIBUTE ENUMS
# Note: Verification of PhysicalBuild, EyeColor, and HairColor
# ==============================================================================


@pytest.mark.regression
def test_physical_build_values() -> None:
    """Verify PhysicalBuild members and values."""
    assert PhysicalBuild.SLENDER == "SLENDER"
    assert PhysicalBuild.MEDIUM == "MEDIUM"
    assert PhysicalBuild.STOUT == "STOUT"


@pytest.mark.regression
def test_eye_color_values() -> None:
    """Verify EyeColor members and values."""
    expected = {"BLUE", "BROWN", "GREY", "HAZEL", "BLACK"}
    assert {e.value for e in EyeColor} == expected


@pytest.mark.regression
def test_hair_color_values() -> None:
    """Verify HairColor members and values."""
    expected = {"BLONDE", "BROWN", "BLACK", "RED", "GREY", "BALD"}
    assert {e.value for e in HairColor} == expected
