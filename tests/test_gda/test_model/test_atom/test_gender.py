"""Path: tests/test_gda/test_model/test_atom/test_gender.py

Comprehensive test suite verifying GenderAtom primitives and boundaries.

Operational Role:
    Verifies GenderAtom instantiation, raw token normalization, defensive
    value rejections, enum conversions, total ordering, and frozen immutability
    with 100% statement and branch coverage.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from gda.core.errors import ModelFormatError
from gda.enums.core import Sex
from gda.model.atom.gender import GenderAtom

__version__ = "1.0.0+build.1"


# ==============================================================================
# GROUP 1: CANONICAL CODES & NORMALIZATION
# Note: Verification of valid codes and from_input mapping heuristics
# ==============================================================================


@pytest.mark.regression
@pytest.mark.parametrize("code", ["M", "F", "U"])
def test_gender_atom_valid_canonical_codes(code: str) -> None:
    """Verify GenderAtom instantiates with canonical codes M, F, and U."""
    atom = GenderAtom(value=code)
    assert atom.value == code
    assert str(atom) == code
    assert repr(atom) == f"GenderAtom(value='{code}')"
    if code == "M":
        assert atom.is_male is True
        assert atom.is_female is False
        assert atom.is_undetermined is False
    elif code == "F":
        assert atom.is_male is False
        assert atom.is_female is True
        assert atom.is_undetermined is False
    else:
        assert atom.is_male is False
        assert atom.is_female is False
        assert atom.is_undetermined is True


@pytest.mark.regression
@pytest.mark.parametrize(
    ("raw_input", "expected_code"),
    [
        ("m", "M"),
        ("Male", "M"),
        ("boy", "M"),
        ("MAN", "M"),
        ("f", "F"),
        ("FEMALE", "F"),
        ("girl", "F"),
        ("Woman", "F"),
        ("u", "U"),
        ("unknown", "U"),
        ("UNDETERMINED", "U"),
        ("unrecorded", "U"),
        ("?", "U"),
        (None, "U"),
    ],
)
def test_gender_atom_from_input_normalization(raw_input: str | None, expected_code: str) -> None:
    """Verify GenderAtom.from_input maps various tokens to canonical representations."""
    atom = GenderAtom.from_input(raw_input)
    assert atom.value == expected_code


@pytest.mark.regression
def test_gender_atom_from_input_passthrough() -> None:
    """Verify GenderAtom.from_input returns identical instance if already a GenderAtom."""
    original = GenderAtom("M")
    assert GenderAtom.from_input(original) is original


# ==============================================================================
# GROUP 2: ENUM BRIDGING & CONVERSION
# Note: Verification of Sex enum round-tripping and unmapped fallbacks
# ==============================================================================


@pytest.mark.integration
def test_gender_atom_enum_conversions() -> None:
    """Verify conversion to and from authoritative Sex enum members."""
    atom_m = GenderAtom.from_input(Sex.M)
    assert atom_m.value == "M"
    assert atom_m.to_enum() is Sex.M

    atom_f = GenderAtom.from_input(Sex.F)
    assert atom_f.value == "F"
    assert atom_f.to_enum() is Sex.F

    atom_u = GenderAtom.from_input(Sex.U)
    assert atom_u.value == "U"
    assert atom_u.to_enum() is Sex.U

    # Non-binary Sex.X safely defaults to 'U' in gender-at-birth domain
    atom_x = GenderAtom.from_input(Sex.X)
    assert atom_x.value == "U"


# ==============================================================================
# GROUP 3: DEFENSIVE BOUNDARIES & VALIDATIONS
# Note: Verification of invalid input rejections and format errors
# ==============================================================================


@pytest.mark.regression
@pytest.mark.parametrize("invalid_code", ["", " ", "X", "NON-BINARY", "OTHER", "123", "INVALID"])
def test_gender_atom_invalid_code_raises_format_error(invalid_code: str) -> None:
    """Verify GenderAtom rejects non-canonical values in direct instantiation."""
    with pytest.raises(ModelFormatError, match="Invalid GenderAtom code"):
        GenderAtom(value=invalid_code)


@pytest.mark.regression
@pytest.mark.parametrize("alien_input", ["alien", "other", "42", "N/A"])
def test_gender_atom_from_input_rejects_unmapped_strings(alien_input: str) -> None:
    """Verify GenderAtom.from_input raises ModelFormatError on unmappable tokens."""
    with pytest.raises(ModelFormatError, match="Cannot normalize"):
        GenderAtom.from_input(alien_input)


# ==============================================================================
# GROUP 4: TOTAL ORDERING, IMMUTABILITY & INTROSPECTION
# Note: Verification of ordering operators, frozen state, and .help()
# ==============================================================================


@pytest.mark.regression
def test_gender_atom_ordering_and_comparison() -> None:
    """Verify total ordering comparisons against other instances and raw strings."""
    atom_f = GenderAtom("F")
    atom_m = GenderAtom("M")
    atom_u = GenderAtom("U")

    assert atom_f < atom_m < atom_u
    assert atom_f < "M"
    assert atom_m == GenderAtom("M")
    assert atom_f != atom_m
    assert hash(atom_m) == hash(GenderAtom("M"))

    with pytest.raises(TypeError):
        _ = atom_f < 123  # type: ignore[operator]


@pytest.mark.regression
def test_gender_atom_immutability() -> None:
    """Verify GenderAtom is frozen and immutable."""
    atom = GenderAtom("M")
    with pytest.raises((FrozenInstanceError, TypeError)):
        atom.value = "F"  # type: ignore[misc]


@pytest.mark.regression
def test_gender_atom_introspection() -> None:
    """Verify .help() renders public member directory on GenderAtom."""
    atom = GenderAtom("M")
    help_text = atom.help(as_str=True)
    assert help_text is not None
    assert "=== GenderAtom Public Directory ===" in help_text
    assert "is_male" in help_text
    assert "is_female" in help_text
    assert "is_undetermined" in help_text
    assert "to_enum" in help_text
