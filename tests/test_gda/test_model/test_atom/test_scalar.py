"""Path: tests/test_gda/test_model/test_atom/test_scalar.py

Comprehensive test suite verifying domain scalar primitives and metrics.

Operational Role:
    Verifies QuayScore, AhnentafelNumber, ConfidenceScore, PubCode, and
    NewsCategoryCode boundaries, calculations, format patterns, and immutability.

Test Structure & Protocol:
    - Atomized tests: 1:1 behavioral contract mapping.
    - Fully decorated: Standard 7-marker taxonomy.
    - Zero production disk I/O.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from gda.core.errors import ModelFormatError, ModelRangeError
from gda.model.atom.scalar import (
    AhnentafelNumber,
    ConfidenceScore,
    NewsCategoryCode,
    PubCode,
    QuayScore,
)

__version__ = "1.0.0+build.7"


# ==============================================================================
# GROUP 1: QUAYSCORE BOUNDARIES
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
@pytest.mark.parametrize("valid_score", [0, 1, 2, 3])
def test_quay_score_valid_values(valid_score: int) -> None:
    """Verify QuayScore instantiates correctly for valid values 0 through 3."""
    qs = QuayScore(valid_score)
    assert qs.value == valid_score
    assert int(qs) == valid_score
    assert repr(qs) == f"QuayScore(value={valid_score})"


@pytest.mark.unit
@pytest.mark.regression
@pytest.mark.parametrize("invalid_score", [-1, 4, 10, -100])
def test_quay_score_out_of_bounds_raises_range_error(invalid_score: int) -> None:
    """Verify QuayScore raises ModelRangeError when value is outside 0..3."""
    with pytest.raises(ModelRangeError, match="out of range"):
        QuayScore(invalid_score)


# ==============================================================================
# GROUP 2: AHNENTAFEL NUMBER INVARIANTS & CALCULATIONS
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_ahnentafel_root_subject() -> None:
    """Verify AhnentafelNumber root subject (1) properties."""
    root = AhnentafelNumber(1)
    assert root.value == 1
    assert int(root) == 1
    assert root.is_male is None
    assert root.is_female is None
    assert root.child_index is None
    assert root.father_index == 2
    assert root.mother_index == 3
    assert repr(root) == "AhnentafelNumber(value=1)"


@pytest.mark.unit
@pytest.mark.smoke
def test_ahnentafel_gender_and_relationships() -> None:
    """Verify AhnentafelNumber gender calculations and familial indexing."""
    father = AhnentafelNumber(2)
    assert father.is_male is True
    assert father.is_female is False
    assert father.child_index == 1
    assert father.father_index == 4
    assert father.mother_index == 5

    mother = AhnentafelNumber(3)
    assert mother.is_male is False
    assert mother.is_female is True
    assert mother.child_index == 1
    assert mother.father_index == 6
    assert mother.mother_index == 7


@pytest.mark.unit
@pytest.mark.regression
@pytest.mark.parametrize("bad_index", [0, -1, -50])
def test_ahnentafel_invalid_value_raises_range_error(bad_index: int) -> None:
    """Verify AhnentafelNumber raises ModelRangeError for integers < 1."""
    with pytest.raises(ModelRangeError, match="must be a positive integer >= 1"):
        AhnentafelNumber(bad_index)


# ==============================================================================
# GROUP 3: CONFIDENCE SCORE BOUNDARIES
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
@pytest.mark.parametrize("valid_conf", [0.0, 0.5, 0.999, 1.0])
def test_confidence_score_valid_values(valid_conf: float) -> None:
    """Verify ConfidenceScore instantiates within boundary 0.0..1.0."""
    cs = ConfidenceScore(valid_conf)
    assert cs.value == valid_conf
    assert float(cs) == valid_conf
    assert repr(cs) == f"ConfidenceScore(value={valid_conf})"


@pytest.mark.unit
@pytest.mark.regression
@pytest.mark.parametrize("invalid_conf", [-0.01, -1.0, 1.01, 2.5])
def test_confidence_score_out_of_bounds_raises_range_error(invalid_conf: float) -> None:
    """Verify ConfidenceScore raises ModelRangeError outside 0.0..1.0."""
    with pytest.raises(ModelRangeError, match="out of range"):
        ConfidenceScore(invalid_conf)


# ==============================================================================
# GROUP 4: PUBCODE & NEWSCATEGORYCODE PATTERNS
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
@pytest.mark.parametrize(
    "valid_pub", ["US_CENSUS", "NH_VITAL", "TOWN_RECORDS_01", "A-B"]
)
def test_pub_code_valid_patterns(valid_pub: str) -> None:
    """Verify PubCode validates alphanumeric uppercase tokens."""
    pub = PubCode(valid_pub)
    assert pub.value == valid_pub
    assert str(pub) == valid_pub
    assert repr(pub) == f"PubCode(value='{valid_pub}')"


@pytest.mark.unit
@pytest.mark.regression
@pytest.mark.parametrize(
    "invalid_pub",
    ["", "A", "a_lower", "HAS SPACE", "TOOLONG_TOKEN_NAME_EXCEEDING_LIMIT"],
)
def test_pub_code_invalid_syntax_raises_format_error(invalid_pub: str) -> None:
    """Verify PubCode raises ModelFormatError when pattern violates '^[A-Z0-9_-]{2,20}$'."""
    with pytest.raises(ModelFormatError, match="Invalid PubCode format"):
        PubCode(invalid_pub)


@pytest.mark.unit
@pytest.mark.smoke
@pytest.mark.parametrize("valid_cat", ["OBIT", "MARR", "BIRTH", "DEATH", "PROBATE"])
def test_news_category_code_valid_patterns(valid_cat: str) -> None:
    """Verify NewsCategoryCode validates uppercase alpha category codes."""
    cat = NewsCategoryCode(valid_cat)
    assert cat.value == valid_cat
    assert str(cat) == valid_cat
    assert repr(cat) == f"NewsCategoryCode(value='{valid_cat}')"


@pytest.mark.unit
@pytest.mark.regression
@pytest.mark.parametrize(
    "invalid_cat", ["", "NO", "lower", "WITH SPACE", "TOO_LONG_CATEGORY_NAME"]
)
def test_news_category_code_invalid_syntax_raises_format_error(
    invalid_cat: str,
) -> None:
    """Verify NewsCategoryCode raises ModelFormatError when pattern violates '^[A-Z]{3,15}$'."""
    with pytest.raises(ModelFormatError, match="Invalid NewsCategoryCode format"):
        NewsCategoryCode(invalid_cat)


# ==============================================================================
# GROUP 5: IMMUTABILITY & INTROSPECTION
# ==============================================================================


@pytest.mark.unit
def test_scalar_atoms_immutability() -> None:
    """Verify scalar atoms are frozen and immutable."""
    qs = QuayScore(2)
    with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
        qs.value = 3  # type: ignore[misc]

    ahn = AhnentafelNumber(4)
    with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
        ahn.value = 5  # type: ignore[misc]


@pytest.mark.unit
def test_scalar_atoms_introspection() -> None:
    """Verify .help() renders on scalar primitives."""
    ahn = AhnentafelNumber(2)
    help_text = ahn.help(as_str=True)
    assert help_text is not None
    assert "=== AhnentafelNumber Public Directory ===" in help_text
    assert "father_index" in help_text
