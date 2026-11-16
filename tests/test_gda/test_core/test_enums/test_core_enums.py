"""Path: tests/test_gda/test_core/test_enums/test_core_enums.py

Targeted behavioral test suite verifying foundational gda.core.enums.core models.

Operational Role:
    Verifies Sex code resolution, token normalizers, FactType domain coverage,
    QuayScore integer equivalence, and AssociatedRole mappings.

Test Structure & Protocol:
    - Atomized tests: 1:1 verification per behavioral contract.
    - Fully decorated: Explicitly decorated with registered pytest markers.
    - Dependencies: In-memory only; zero physical disk I/O.
"""

from __future__ import annotations

import pytest

from gda.core.enums.core import (
    AssociatedRole,
    FactType,
    IDType,
    QualityAssessment,
    QuayScore,
    Sex,
    SmartIDPrefix,
)

__version__ = "1.0.0+build.5"


# ==============================================================================
# GROUP 1: Sex Enumeration & Normalizer Mapping
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_sex_enum_canonical_values() -> None:
    """Verify canonical Sex values match descriptive title-case values."""
    assert Sex.MALE == "Male"
    assert Sex.FEMALE == "Female"
    assert Sex.UNKNOWN == "Unknown"
    assert len(Sex) == 3


@pytest.mark.unit
def test_sex_from_input_maps_standard_tokens() -> None:
    """Verify Sex.from_input maps typical transcription tokens into canonical instances."""
    assert Sex.from_input("m") is Sex.MALE
    assert Sex.from_input("M") is Sex.MALE
    assert Sex.from_input("Male") is Sex.MALE
    assert Sex.from_input("boy") is Sex.MALE
    assert Sex.from_input("f") is Sex.FEMALE
    assert Sex.from_input("F") is Sex.FEMALE
    assert Sex.from_input("female") is Sex.FEMALE
    assert Sex.from_input("GIRL") is Sex.FEMALE
    assert Sex.from_input("u") is Sex.UNKNOWN
    assert Sex.from_input("U") is Sex.UNKNOWN
    assert Sex.from_input("unknown") is Sex.UNKNOWN
    assert Sex.from_input("undetermined") is Sex.UNKNOWN


@pytest.mark.unit
@pytest.mark.regression
@pytest.mark.parametrize("invalid_token", ["alien", "X", "Non-Binary", "non-binary", ""])
def test_sex_from_input_rejects_invalid_tokens(invalid_token: str) -> None:
    """Verify Sex.from_input raises ValueError on invalid or unsupported tokens."""
    with pytest.raises(ValueError, match="Cannot map .* to a valid Sex enum member."):
        Sex.from_input(invalid_token)


# ==============================================================================
# GROUP 2: FactType Life Assertion Domain Tokens
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_fact_type_canonical_tokens() -> None:
    """Verify vital and extended life event FactType assertions evaluate in uppercase."""
    assert FactType.BIRTH == "BIRTH"
    assert FactType.DEATH == "DEATH"
    assert FactType.MARRIAGE == "MARRIAGE"
    assert FactType.PROBATE == "PROBATE"
    assert FactType.TRAVEL == "TRAVEL"
    assert FactType.WILL == "WILL"


# ==============================================================================
# GROUP 3: AssociatedRole Kinship & Participation Tokens
# ==============================================================================


@pytest.mark.unit
def test_associated_role_canonical_values() -> None:
    """Verify participant roles evaluate to canonical full-name strings."""
    assert AssociatedRole.WITNESS == "WITNESS"
    assert AssociatedRole.CLERGY == "CLERGY"
    assert AssociatedRole.INFORMANT == "INFORMANT"
    assert AssociatedRole.OFFICIAL == "OFFICIAL"
    assert AssociatedRole.OFFICIANT == "OFFICIANT"
    assert AssociatedRole.PRIMARY == "PRIMARY"
    assert AssociatedRole.CHILD == "CHILD"
    assert AssociatedRole.FATHER == "FATHER"
    assert AssociatedRole.MOTHER == "MOTHER"
    assert AssociatedRole.SPOUSE == "SPOUSE"
    assert AssociatedRole.SIBLING == "SIBLING"


# ==============================================================================
# GROUP 4: QuayScore Evidentiary Certainty Integers & Quality Assessment
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_quay_score_integer_mapping() -> None:
    """Verify QuayScore provides sequential 0 to 3 integers without aliases."""
    assert QuayScore.UNRELIABLE == 0
    assert QuayScore.QUESTIONABLE == 1
    assert QuayScore.SECONDARY == 2
    assert QuayScore.DIRECT_PRIMARY == 3
    assert len(QuayScore) == 4


@pytest.mark.unit
def test_quality_assessment_values() -> None:
    """Verify QualityAssessment textual rating values."""
    assert QualityAssessment.DIRECT_PRIMARY == "DIRECT_PRIMARY"
    assert QualityAssessment.INDIRECT_PRIMARY == "INDIRECT_PRIMARY"
    assert QualityAssessment.SECONDARY == "SECONDARY"
    assert QualityAssessment.UNRELIABLE == "UNRELIABLE"


# ==============================================================================
# GROUP 5: Identifier Categories & Prefixes
# ==============================================================================


@pytest.mark.unit
def test_id_type_and_prefixes() -> None:
    """Verify IDType and SmartIDPrefix enumerations."""
    assert IDType.SMART_ID == "SMART_ID"
    assert IDType.UUID == "UUID"
    assert SmartIDPrefix.IND == "IND"
    assert SmartIDPrefix.FID == "FID"
    assert SmartIDPrefix.LOC == "LOC"
    assert SmartIDPrefix.SID == "SID"
    assert SmartIDPrefix.FAM == "FAM"
