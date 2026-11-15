"""Path: tests/test_gda/test_model/test_atom/test_atom_scalar.py

Comprehensive test suite verifying domain scalar primitives and metrics.

Operational Role:
    Verifies QuayScore, AhnentafelNumber, ConfidenceScore, PubCode, and
    NewsCategoryCode boundaries, calculations, format patterns, strict type enforcement,
    primitive equality, homogeneous ordering, and immutability.

Test Structure & Protocol:
    - Atomized tests: 1:1 behavioral contract mapping.
    - Fully decorated: Pytest marker taxonomy (1 @pytest.mark.smoke).
    - Zero production disk I/O.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from typing import Any

import pytest
from tests.test_gda.test_model.test_atom.conftest import (
    INVALID_NON_NUMERIC_VALUES,
    INVALID_NON_STRING_VALUES,
)

from gda.core.errors import ModelFormatError, ModelRangeError
from gda.model.atom.scalar import (
    AhnentafelNumber,
    ConfidenceScore,
    NewsCategoryCode,
    PubCode,
    QuayScore,
)

__version__ = "1.0.0+build.10"


# ==============================================================================
# GROUP 1: QUAYSCORE BOUNDARIES & TYPE SAFETY
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
@pytest.mark.parametrize("valid_score", [0, 1, 2, 3])
def test_quay_score_valid_values(valid_score: int) -> None:
    """Verify QuayScore instantiates correctly for valid values 0 through 3."""
    qs = QuayScore(valid_score)
    assert qs.value == valid_score
    assert int(qs) == valid_score
    assert str(qs) == str(valid_score)
    assert repr(qs) == f"QuayScore(value={valid_score})"


@pytest.mark.unit
@pytest.mark.regression
@pytest.mark.parametrize("invalid_score", [-1, 4, 10, -100])
def test_quay_score_out_of_bounds_raises_range_error(invalid_score: int) -> None:
    """Verify QuayScore raises ModelRangeError when value is outside 0..3."""
    with pytest.raises(ModelRangeError, match="out of range"):
        QuayScore(invalid_score)


@pytest.mark.unit
@pytest.mark.regression
@pytest.mark.parametrize("bad_type", [*INVALID_NON_NUMERIC_VALUES, 1.5])
def test_quay_score_invalid_type_raises_error(bad_type: Any) -> None:
    """Verify QuayScore rejects booleans, floats, and strings."""
    with pytest.raises((ModelFormatError, TypeError, ValueError)):
        QuayScore(bad_type)


# ==============================================================================
# GROUP 2: AHNENTAFEL NUMBER INVARIANTS & CALCULATIONS
# ==============================================================================


@pytest.mark.unit
def test_ahnentafel_root_subject() -> None:
    """Verify AhnentafelNumber root subject (1) properties."""
    root = AhnentafelNumber(1)
    assert root.value == 1
    assert int(root) == 1
    assert str(root) == "1"
    assert root.is_male is None
    assert root.is_female is None
    assert root.child_index is None
    assert root.father_index == 2
    assert root.mother_index == 3
    assert repr(root) == "AhnentafelNumber(value=1)"


@pytest.mark.unit
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


@pytest.mark.unit
@pytest.mark.regression
@pytest.mark.parametrize("bad_type", [*INVALID_NON_NUMERIC_VALUES, 2.5])
def test_ahnentafel_invalid_type_raises_error(bad_type: Any) -> None:
    """Verify AhnentafelNumber rejects booleans, floats, and strings."""
    with pytest.raises((ModelFormatError, TypeError, ValueError)):
        AhnentafelNumber(bad_type)


# ==============================================================================
# GROUP 3: CONFIDENCE SCORE BOUNDARIES
# ==============================================================================


@pytest.mark.unit
@pytest.mark.parametrize("valid_conf", [0.0, 0.5, 0.999, 1.0])
def test_confidence_score_valid_values(valid_conf: float) -> None:
    """Verify ConfidenceScore instantiates within boundary 0.0..1.0."""
    cs = ConfidenceScore(valid_conf)
    assert cs.value == valid_conf
    assert float(cs) == valid_conf
    assert str(cs) == f"{valid_conf:.4f}"
    assert repr(cs) == f"ConfidenceScore(value={valid_conf})"


@pytest.mark.unit
def test_confidence_score_int_normalized_to_float() -> None:
    """Verify ConfidenceScore normalizes exact integer 0 or 1 to float."""
    cs0 = ConfidenceScore(0)
    cs1 = ConfidenceScore(1)
    assert type(cs0.value) is float and cs0.value == 0.0
    assert type(cs1.value) is float and cs1.value == 1.0


@pytest.mark.unit
@pytest.mark.regression
@pytest.mark.parametrize("invalid_conf", [-0.0001, -0.01, -1.0, 1.0001, 1.01, 2.5])
def test_confidence_score_out_of_bounds_raises_range_error(invalid_conf: float) -> None:
    """Verify ConfidenceScore raises ModelRangeError outside 0.0..1.0."""
    with pytest.raises(ModelRangeError, match="out of range"):
        ConfidenceScore(invalid_conf)


@pytest.mark.unit
@pytest.mark.regression
@pytest.mark.parametrize("bad_type", INVALID_NON_NUMERIC_VALUES)
def test_confidence_score_invalid_type_raises_error(bad_type: Any) -> None:
    """Verify ConfidenceScore rejects booleans, strings, and None."""
    with pytest.raises((ModelFormatError, TypeError, ValueError)):
        ConfidenceScore(bad_type)


# ==============================================================================
# GROUP 4: PUBCODE & NEWSCATEGORYCODE PATTERNS
# ==============================================================================


@pytest.mark.unit
@pytest.mark.parametrize(
    "valid_pub",
    ["AB", "US_CENSUS", "NH_VITAL", "TOWN_RECORDS_01", "A-B", "A" * 20],
)
def test_pub_code_valid_patterns(valid_pub: str) -> None:
    """Verify PubCode validates alphanumeric uppercase tokens (2..20 chars)."""
    pub = PubCode(valid_pub)
    assert pub.value == valid_pub
    assert str(pub) == valid_pub
    assert repr(pub) == f"PubCode(value='{valid_pub}')"


@pytest.mark.unit
@pytest.mark.regression
@pytest.mark.parametrize(
    "invalid_pub",
    [
        "",
        " ",
        " US_CENSUS ",
        "A",
        "a_lower",
        "HAS SPACE",
        "A" * 21,
    ],
)
def test_pub_code_invalid_syntax_raises_format_error(invalid_pub: str) -> None:
    """Verify PubCode raises ModelFormatError when pattern violates '^[A-Z0-9_-]{2,20}$'."""
    with pytest.raises(ModelFormatError, match="Invalid PubCode format"):
        PubCode(invalid_pub)


@pytest.mark.unit
@pytest.mark.parametrize(
    "valid_cat", ["ABC", "OBIT", "MARR", "BIRTH", "DEATH", "PROBATE", "A" * 15]
)
def test_news_category_code_valid_patterns(valid_cat: str) -> None:
    """Verify NewsCategoryCode validates uppercase alpha category codes (3..15 chars)."""
    cat = NewsCategoryCode(valid_cat)
    assert cat.value == valid_cat
    assert str(cat) == valid_cat
    assert repr(cat) == f"NewsCategoryCode(value='{valid_cat}')"


@pytest.mark.unit
@pytest.mark.regression
@pytest.mark.parametrize(
    "invalid_cat",
    [
        "",
        " ",
        " OBIT ",
        "NO",
        "lower",
        "OBIT1",
        "WITH SPACE",
        "A" * 16,
    ],
)
def test_news_category_code_invalid_syntax_raises_format_error(
    invalid_cat: str,
) -> None:
    """Verify NewsCategoryCode raises ModelFormatError when pattern violates '^[A-Z]{3,15}$'."""
    with pytest.raises(ModelFormatError, match="Invalid NewsCategoryCode format"):
        NewsCategoryCode(invalid_cat)


@pytest.mark.unit
@pytest.mark.regression
@pytest.mark.parametrize("bad_type", INVALID_NON_STRING_VALUES)
def test_code_atoms_non_string_raises_error(bad_type: Any) -> None:
    """Verify PubCode and NewsCategoryCode reject non-string types."""
    with pytest.raises((ModelFormatError, TypeError, ValueError)):
        PubCode(bad_type)
    with pytest.raises((ModelFormatError, TypeError, ValueError)):
        NewsCategoryCode(bad_type)


# ==============================================================================
# GROUP 5: DEFENSIVE POST-INIT TYPE GUARDS, EQUALITY & HOMOGENEOUS ORDERING
# ==============================================================================


@pytest.mark.unit
@pytest.mark.regression
def test_scalar_atoms_defensive_post_init_type_guards() -> None:
    """Verify __post_init__ defensive type checks trigger if Pydantic __init__ is bypassed."""
    for cls, bad_val in [
        (QuayScore, True),
        (AhnentafelNumber, False),
        (PubCode, 123),
        (NewsCategoryCode, 123),
    ]:
        raw = object.__new__(cls)
        object.__setattr__(raw, "value", bad_val)
        with pytest.raises(ModelFormatError):
            raw.__post_init__()


@pytest.mark.unit
def test_scalar_atoms_equality_and_homogeneous_ordering() -> None:
    """Verify primitive equality, atom equality, hashing, and homogeneous ordering."""
    q1, q2 = QuayScore(1), QuayScore(3)
    assert q1 == QuayScore(1)
    assert q1 == 1
    assert (q1 == True) is False  # noqa: E712  # type: ignore[comparison-overlap]
    assert (q1 == "1") is False  # type: ignore[comparison-overlap]
    assert q1 < q2 and hash(q1) == hash(1)

    a1, a2 = AhnentafelNumber(2), AhnentafelNumber(4)
    assert a1 == AhnentafelNumber(2)
    assert a1 == 2
    assert (a1 == "2") is False  # type: ignore[comparison-overlap]
    assert a1 < a2 and hash(a1) == hash(2)

    c1, c2 = ConfidenceScore(0.25), ConfidenceScore(0.75)
    assert c1 == ConfidenceScore(0.25)
    assert c1 == 0.25
    assert ConfidenceScore(1.0) == 1
    assert (ConfidenceScore(1.0) == True) is False  # noqa: E712  # type: ignore[comparison-overlap]
    assert (c1 == "0.25") is False  # type: ignore[comparison-overlap]
    assert c1 < c2 and hash(c1) == hash(0.25)

    p1, p2 = PubCode("ALPHA"), PubCode("BETA")
    assert p1 == PubCode("ALPHA")
    assert p1 == "ALPHA"
    assert (p1 == 123) is False  # type: ignore[comparison-overlap]
    assert p1 < p2 and hash(p1) == hash("ALPHA")

    n1, n2 = NewsCategoryCode("BIRTH"), NewsCategoryCode("DEATH")
    assert n1 == NewsCategoryCode("BIRTH")
    assert n1 == "BIRTH"
    assert (n1 == 123) is False  # type: ignore[comparison-overlap]
    assert n1 < n2 and hash(n1) == hash("BIRTH")

    # Cross-type ordering must raise TypeError
    with pytest.raises(TypeError):
        _ = q1 < a1  # type: ignore[operator]
    with pytest.raises(TypeError):
        _ = a1 < q1  # type: ignore[operator]
    with pytest.raises(TypeError):
        _ = c1 < 0.75  # type: ignore[operator]
    with pytest.raises(TypeError):
        _ = p1 < n1  # type: ignore[operator]
    with pytest.raises(TypeError):
        _ = n1 < p1  # type: ignore[operator]


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
