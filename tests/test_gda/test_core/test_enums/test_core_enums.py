"""Path: tests/test_gda/test_core/test_enums/test_core_enums.py

Targeted behavioral test suite verifying foundational gda.core.enums.core models.

Operational Role:
    Verifies public exports, Sex UPPER_SNAKE_CASE canonical values and input
    normalizer, FactType domain tokens, AssociatedRole kinship mappings,
    QuayScore integer certainty levels, QualityAssessment ratings, and
    identifier category/prefix enums.

Test Structure & Protocol:
    - Atomized & parametrized tests: 1:1 behavioral contract mapping.
    - Fully decorated: 5-marker taxonomy (smoke, unit, regression).
    - Dependencies: In-memory only; zero physical disk I/O.
"""

from __future__ import annotations

import pytest

import gda.core.enums.core as core_enums
from gda.core.enums.core import (
    AssociatedRole,
    FactType,
    IDType,
    QualityAssessment,
    QuayScore,
    Sex,
    SmartIDPrefix,
)

__version__ = "1.0.0+build.6"


# ==============================================================================
# GROUP 1: Smoke & Primary Entrypoints
# Note: Single smoke gate verifying gda.core.enums.core public exports.
# ==============================================================================


@pytest.mark.smoke
@pytest.mark.unit
def test_core_enums_exposes_expected_public_interface() -> None:
    """Verify gda.core.enums.core exports all 7 foundational enum classes."""
    expected = {
        "AssociatedRole",
        "FactType",
        "IDType",
        "QualityAssessment",
        "QuayScore",
        "Sex",
        "SmartIDPrefix",
    }
    assert set(core_enums.__all__) == expected


# ==============================================================================
# GROUP 2: Core Logic & Happy Paths
# Note: Canonical member values across core domain enums.
# ==============================================================================


@pytest.mark.unit
def test_sex_enum_canonical_values() -> None:
    """Verify canonical Sex values use UPPER_SNAKE_CASE tokens (Phase 3 TDD Red)."""
    assert Sex.MALE == "MALE"
    assert Sex.FEMALE == "FEMALE"
    assert Sex.UNKNOWN == "UNKNOWN"
    assert len(Sex) == 3


@pytest.mark.unit
def test_fact_type_and_associated_role_canonical_tokens() -> None:
    """Verify FactType life assertions and AssociatedRole kinship tokens."""
    assert FactType.BIRTH == "BIRTH"
    assert FactType.DEATH == "DEATH"
    assert FactType.MARRIAGE == "MARRIAGE"
    assert FactType.PROBATE == "PROBATE"
    assert FactType.TRAVEL == "TRAVEL"
    assert FactType.WILL == "WILL"

    for role_name in (
        "WITNESS",
        "CLERGY",
        "INFORMANT",
        "OFFICIAL",
        "OFFICIANT",
        "PRIMARY",
        "CHILD",
        "FATHER",
        "MOTHER",
        "SPOUSE",
        "SIBLING",
    ):
        assert getattr(AssociatedRole, role_name) == role_name


@pytest.mark.unit
def test_quay_score_and_quality_assessment_values() -> None:
    """Verify QuayScore sequential 0-3 integers and QualityAssessment strings."""
    assert QuayScore.UNRELIABLE == 0
    assert QuayScore.QUESTIONABLE == 1
    assert QuayScore.SECONDARY == 2
    assert QuayScore.DIRECT_PRIMARY == 3
    assert len(QuayScore) == 4

    assert QualityAssessment.DIRECT_PRIMARY == "DIRECT_PRIMARY"
    assert QualityAssessment.INDIRECT_PRIMARY == "INDIRECT_PRIMARY"
    assert QualityAssessment.SECONDARY == "SECONDARY"
    assert QualityAssessment.UNRELIABLE == "UNRELIABLE"


@pytest.mark.unit
def test_id_type_and_smart_id_prefixes() -> None:
    """Verify IDType and SmartIDPrefix canonical tokens."""
    assert IDType.SMART_ID == "SMART_ID"
    assert IDType.UUID == "UUID"
    assert SmartIDPrefix.IND == "IND"
    assert SmartIDPrefix.FID == "FID"
    assert SmartIDPrefix.LOC == "LOC"
    assert SmartIDPrefix.SID == "SID"
    assert SmartIDPrefix.FAM == "FAM"


# ==============================================================================
# GROUP 3: Edge Cases & Boundary Conditions
# Note: Transcription token normalization via Sex.from_input.
# ==============================================================================


@pytest.mark.unit
@pytest.mark.parametrize(
    ("raw_token", "expected"),
    [
        ("m", Sex.MALE),
        ("M", Sex.MALE),
        ("Male", Sex.MALE),
        ("boy", Sex.MALE),
        ("f", Sex.FEMALE),
        ("F", Sex.FEMALE),
        ("female", Sex.FEMALE),
        ("GIRL", Sex.FEMALE),
        ("u", Sex.UNKNOWN),
        ("U", Sex.UNKNOWN),
        ("unknown", Sex.UNKNOWN),
        ("undetermined", Sex.UNKNOWN),
    ],
)
def test_sex_from_input_maps_standard_tokens(raw_token: str, expected: Sex) -> None:
    """Verify Sex.from_input maps typical transcription tokens into canonical instances."""
    assert Sex.from_input(raw_token) is expected


# ==============================================================================
# GROUP 4: Error Handling & Validation Failures
# Note: Rejection of unsupported tokens in Sex.from_input.
# ==============================================================================


@pytest.mark.regression
@pytest.mark.parametrize("invalid_token", ["alien", "X", "Non-Binary", "non-binary", ""])
def test_sex_from_input_rejects_invalid_tokens(invalid_token: str) -> None:
    """Verify Sex.from_input raises ValueError on invalid or unsupported tokens."""
    with pytest.raises(ValueError, match="Cannot map .* to a valid Sex enum member."):
        Sex.from_input(invalid_token)
