"""Path: tests/test_gda/test_model/test_atom/test_gender.py

Targeted behavioral test suite verifying the GenderAtom value object.

Operational Role:
    Verifies canonical gender classification codes (M, F, U), strict non-mutation
    rejection of whitespace and non-canonical strings, raw string equality,
    homogeneous total ordering, immutability, and introspection discovery.

Test Structure & Protocol:
    - Atomized tests: 1:1 verification per behavioral contract.
    - Fully decorated: Pytest marker taxonomy (1 @pytest.mark.smoke).
    - Dependencies: In-memory only; zero physical disk I/O.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from typing import Any

import pytest
from tests.test_gda.test_model.test_atom.conftest import (
    INVALID_NON_STRING_VALUES,
    PADDED_WHITESPACE_SAMPLES,
)

from gda.core.errors import ModelFormatError
from gda.model.atom.gender import GenderAtom

__version__ = "1.0.0+build.9"


# ==============================================================================
# GROUP 1: Canonical Code Construction & Predicates
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
@pytest.mark.parametrize("code", ["M", "F", "U"])
def test_gender_atom_valid_canonical_codes(code: str) -> None:
    """Verify GenderAtom instantiates with exact canonical codes M, F, and U."""
    atom = GenderAtom(code)
    assert atom.value == code
    assert str(atom) == code
    assert repr(atom) == f"GenderAtom(value='{code}')"
    assert atom.is_male is (code == "M")
    assert atom.is_female is (code == "F")
    assert atom.is_undetermined is (code == "U")


# ==============================================================================
# GROUP 2: Defensive Validation & Rejection Boundaries
# ==============================================================================


@pytest.mark.unit
@pytest.mark.regression
@pytest.mark.parametrize(
    "invalid_code",
    [
        "",
        " ",
        "m",
        "f",
        "u",
        "Male",
        "Female",
        "Unknown",
        "X",
        "NON-BINARY",
        "OTHER",
        "123",
        *PADDED_WHITESPACE_SAMPLES,
    ],
)
def test_gender_atom_invalid_code_raises_format_error(invalid_code: str) -> None:
    """Verify GenderAtom rejects lowercase, unnormalized whitespace, and non-canonical tokens."""
    with pytest.raises(ModelFormatError, match="Invalid GenderAtom code"):
        GenderAtom(invalid_code)


@pytest.mark.unit
@pytest.mark.regression
@pytest.mark.parametrize("bad_type", INVALID_NON_STRING_VALUES)
def test_gender_atom_non_string_raises_error(bad_type: Any) -> None:
    """Verify GenderAtom rejects non-string inputs without coercion."""
    with pytest.raises((ModelFormatError, TypeError, ValueError)):
        GenderAtom(bad_type)


# ==============================================================================
# GROUP 3: Equality, Homogeneous Ordering, Immutability & Introspection
# ==============================================================================


@pytest.mark.unit
def test_gender_atom_equality_and_hashing(sample_gender: GenderAtom) -> None:
    """Verify GenderAtom supports raw string equality, atom equality, and set hashing."""
    m2 = GenderAtom("M")
    f = GenderAtom("F")

    assert sample_gender == m2
    assert sample_gender == "M"
    assert sample_gender != f
    assert sample_gender != "F"
    assert (sample_gender == 123) is False  # type: ignore[comparison-overlap]
    assert hash(sample_gender) == hash(m2) == hash("M")
    assert len({sample_gender, m2, f}) == 2


@pytest.mark.unit
def test_gender_atom_homogeneous_ordering(sample_gender: GenderAtom) -> None:
    """Verify total ordering works across GenderAtom instances and rejects cross-type <."""
    f = GenderAtom("F")
    u = GenderAtom("U")

    assert f < sample_gender < u
    assert f <= sample_gender <= u
    assert u > sample_gender > f
    assert sorted([u, sample_gender, f]) == [f, sample_gender, u]

    with pytest.raises(TypeError):
        _ = sample_gender < "Z"  # type: ignore[operator]
    with pytest.raises(TypeError):
        _ = sample_gender < 123  # type: ignore[operator]


@pytest.mark.unit
def test_gender_atom_immutability(sample_gender: GenderAtom) -> None:
    """Verify GenderAtom instances are frozen and immutable."""
    with pytest.raises((FrozenInstanceError, AttributeError)):
        sample_gender.value = "F"  # type: ignore[misc]


@pytest.mark.unit
def test_gender_atom_introspection(sample_gender: GenderAtom) -> None:
    """Verify GenderAtom inherits IntrospectableMixin with working .help()."""
    help_text = sample_gender.help(as_str=True)
    assert help_text is not None
    assert "GenderAtom" in help_text
    assert "is_male" in help_text
