"""Path: tests/test_gda/test_enums/test_core_enums.py

Targeted behavioral test suite verifying foundational gda.enums.core models.

Operational Role:
    Verifies Sex code resolution, token normalizers, FactType domain coverage,
    QuayScore integer equivalence and aliases, and AssociatedRole mappings.

Test Structure & Protocol:
    - Atomized tests: 1:1 verification per behavioral contract.
    - Fully decorated: Explicitly decorated with registered pytest markers.
    - Dependencies: In-memory only; zero physical disk I/O.
"""

from __future__ import annotations

import pytest

from gda.enums.core import (
    AssociatedRole,
    DateModifier,
    FactType,
    QualityAssessment,
    QuayScore,
    Sex,
    VitalModifier,
)

__version__ = "0.1.0+build.1"

# ==============================================================================
# GROUP 1: Sex Enumeration & Normalizer Mapping
# Note: Verification of canonical codes, aliases, and from_input normalization
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_sex_enum_canonical_values() -> None:
    """Verify canonical Sex values match standard single-character codes."""
    assert Sex.M == "M"
    assert Sex.F == "F"
    assert Sex.X == "X"
    assert Sex.U == "U"


@pytest.mark.unit
def test_sex_enum_semantic_aliases() -> None:
    """Verify descriptive aliases resolve to canonical underlying single-character codes."""
    assert Sex.MALE == Sex.M
    assert Sex.FEMALE == Sex.F
    assert Sex.NON_BINARY == Sex.X
    assert Sex.UNKNOWN == Sex.U


@pytest.mark.unit
def test_sex_from_input_maps_standard_tokens() -> None:
    """Verify Sex.from_input maps typical transcription tokens into canonical instances."""
    assert Sex.from_input("m") is Sex.M
    assert Sex.from_input("Male") is Sex.M
    assert Sex.from_input("boy") is Sex.M
    assert Sex.from_input("f") is Sex.F
    assert Sex.from_input("female") is Sex.F
    assert Sex.from_input("GIRL") is Sex.F
    assert Sex.from_input("X") is Sex.X
    assert Sex.from_input("Non-Binary") is Sex.X
    assert Sex.from_input("u") is Sex.U
    assert Sex.from_input("unknown") is Sex.U
    assert Sex.from_input("undetermined") is Sex.U


@pytest.mark.unit
@pytest.mark.regression
def test_sex_from_input_rejects_invalid_tokens() -> None:
    """Verify Sex.from_input raises ValueError on invalid or unrecognized strings."""
    with pytest.raises(
        ValueError, match="Cannot map 'alien' to a valid Sex enum member."
    ):
        Sex.from_input("alien")


# ==============================================================================
# GROUP 2: FactType Life Assertion Domain Tokens
# Note: Verification of uppercase assertion categories and extended life events
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
# Note: Verification of participant roles, kinship abbreviations, and aliases
# ==============================================================================


@pytest.mark.unit
def test_associated_role_aliases_and_values() -> None:
    """Verify full-name and abbreviated roles resolve to canonical values."""
    assert AssociatedRole.WITNESS == "WITN"
    assert AssociatedRole.WITN == "WITN"
    assert AssociatedRole.CLERGY == "CLERGY"
    assert AssociatedRole.INFORMANT == "INFORMANT"
    assert AssociatedRole.PRIMARY == "PRIMARY"
    assert AssociatedRole.CHILD == "CHIL"
    assert AssociatedRole.FATHER == "FATH"
    assert AssociatedRole.MOTHER == "MOTH"


# ==============================================================================
# GROUP 4: QuayScore Evidentiary Certainty Integers & Quality Assessment
# Note: Verification of 0-3 scale and string certainty metrics
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_quay_score_integer_mapping_and_aliases() -> None:
    """Verify QuayScore provides sequential 0 to 3 integers and supports aliases."""
    assert QuayScore.UNRELIABLE == 0
    assert QuayScore.QUESTIONABLE == 1
    assert QuayScore.SECONDARY == 2
    assert QuayScore.DIRECT_PRIMARY == 3
    assert QuayScore.DIRECT == 3
    assert QuayScore.PRIMARY == 3


@pytest.mark.unit
def test_quality_assessment_values() -> None:
    """Verify QualityAssessment textual rating values."""
    assert QualityAssessment.DIRECT_PRIMARY == "DIRECT_PRIMARY"
    assert QualityAssessment.INDIRECT_PRIMARY == "INDIRECT_PRIMARY"
    assert QualityAssessment.SECONDARY == "SECONDARY"
    assert QualityAssessment.UNRELIABLE == "UNRELIABLE"


# ==============================================================================
# GROUP 5: Modifiers
# Note: Verification of DateModifier and VitalModifier string values
# ==============================================================================


@pytest.mark.unit
def test_date_and_vital_modifiers() -> None:
    """Verify date and vital status modifier strings."""
    assert DateModifier.EXACT == "EXACT"
    assert DateModifier.ABOUT == "ABOUT"
    assert DateModifier.BETWEEN == "BETWEEN"
    assert VitalModifier.STILLBORN == "STILLBORN"
    assert VitalModifier.INFANT == "INFANT"
