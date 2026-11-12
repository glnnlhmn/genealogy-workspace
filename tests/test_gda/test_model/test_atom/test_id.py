"""Path: tests/test_gda/test_model/test_atom/test_id.py

Comprehensive test suite verifying AtomID and UUIDv4Str identifier primitives.

Operational Role:
    Verifies that AtomID enforces the 'AAA-######' format without silent mutation,
    validates specialized prefixes (IND, FID, LOC, SID, FAM, NOT, REP, DRF), executes
    homogeneous total ordering, and validates RFC 4122 lowercase UUIDv4 identifiers.

Test Structure & Protocol:
    - Atomized tests: 1:1 behavioral contract mapping.
    - Fully decorated: Pytest marker taxonomy (1 @pytest.mark.smoke).
    - Zero production disk I/O.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from typing import Any

import pytest
from tests.test_gda.test_model.test_atom.conftest import INVALID_NON_STRING_VALUES

from gda.core.errors import ModelFormatError, ModelPrefixMismatchError
from gda.model.atom.id import (
    AtomID,
    DraftRecordID,
    FactID,
    FamilyID,
    IndividualID,
    LocationID,
    MediaID,
    NoteID,
    RepositoryID,
    ServiceRecordID,
    SiteID,
    SourceID,
    TranscriptID,
    UUIDv4Str,
)

__version__ = "1.0.1+build.3"


# ==============================================================================
# GROUP 1: BASE ATOMID FORMAT VALIDATION
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_atom_id_valid_formats() -> None:
    """Verify AtomID instantiates correctly with standard 6-digit and extended identifiers."""
    id_6 = AtomID("IND-000001")
    id_8 = AtomID("LOC-12345678")

    assert id_6.value == "IND-000001"
    assert id_6.prefix == "IND"
    assert id_6.suffix == "000001"
    assert id_6.number == "000001"
    assert str(id_6) == "IND-000001"
    assert repr(id_6) == "AtomID(value='IND-000001')"

    assert id_8.prefix == "LOC"
    assert id_8.suffix == "12345678"
    assert id_8.number == "12345678"


@pytest.mark.unit
@pytest.mark.regression
@pytest.mark.parametrize(
    "invalid_id",
    [
        "",
        "   ",
        " IND-000001",  # Leading whitespace forbidden
        "IND-000001 ",  # Trailing whitespace forbidden
        "IND000001",
        "IN-000001",
        "IND-12345",  # 5 digits (minimum is 6)
        "ind-000001",  # lowercase prefix
        "IND-00000A",  # alphanumeric suffix
        "IND--000001",
        "IND_000001",
    ],
)
def test_atom_id_invalid_syntax_raises_format_error(invalid_id: str) -> None:
    """Verify AtomID raises ModelFormatError when syntax deviates from 'AAA-######'."""
    with pytest.raises(ModelFormatError, match="Invalid AtomID format"):
        AtomID(invalid_id)


@pytest.mark.unit
@pytest.mark.regression
@pytest.mark.parametrize("bad_type", INVALID_NON_STRING_VALUES)
def test_atom_id_non_string_raises_error(bad_type: Any) -> None:
    """Verify AtomID rejects non-string inputs without coercion."""
    with pytest.raises((ModelFormatError, TypeError, ValueError)):
        AtomID(bad_type)


@pytest.mark.unit
def test_atom_id_explicit_expected_prefix_override() -> None:
    """Verify AtomID validates against explicitly passed expected_prefix parameter."""
    atom = AtomID("ABC-000001", expected_prefix="ABC")
    assert atom.prefix == "ABC"

    with pytest.raises(ModelPrefixMismatchError, match="Prefix mismatch for AtomID"):
        AtomID("ABC-000001", expected_prefix="XYZ")


# ==============================================================================
# GROUP 2: SPECIALIZED ATOM SUBCLASSES & PREFIX GUARDS
# ==============================================================================


@pytest.mark.unit
def test_specialized_atom_subclasses_valid_instantiation() -> None:
    """Verify each specialized AtomID subclass instantiates with expected prefix and suffix accessors."""
    ind = IndividualID("IND-000001")
    assert ind.prefix == "IND"
    assert ind.suffix == "000001"
    assert ind.number == "000001"

    assert FactID("FID-000002").prefix == "FID"
    assert LocationID("LOC-000003").prefix == "LOC"
    assert SiteID("SID-000004").prefix == "SID"
    assert FamilyID("FAM-000005").prefix == "FAM"
    assert NoteID("NOT-000006").prefix == "NOT"
    assert RepositoryID("REP-000007").prefix == "REP"

    drf = DraftRecordID("DRF-999999999")
    assert drf.prefix == "DRF"
    assert drf.suffix == "999999999"
    assert drf.number == "999999999"


@pytest.mark.unit
@pytest.mark.regression
@pytest.mark.parametrize(
    ("cls", "bad_value", "cls_name"),
    [
        (IndividualID, "FID-000001", "IndividualID"),
        (FactID, "IND-000001", "FactID"),
        (LocationID, "SID-000001", "LocationID"),
        (SiteID, "LOC-000001", "SiteID"),
        (FamilyID, "IND-000001", "FamilyID"),
        (NoteID, "REP-000001", "NoteID"),
        (RepositoryID, "NOT-000001", "RepositoryID"),
        (DraftRecordID, "IND-000001", "DraftRecordID"),
    ],
)
def test_specialized_atom_id_prefix_mismatch_raises_error(
    cls: type[AtomID],
    bad_value: str,
    cls_name: str,
) -> None:
    """Verify specialized AtomID subclasses raise ModelPrefixMismatchError on wrong prefix."""
    with pytest.raises(ModelPrefixMismatchError, match=f"Prefix mismatch for {cls_name}"):
        cls(bad_value)


# ==============================================================================
# GROUP 3: ATOMID HOMOGENEOUS TOTAL ORDERING & EQUALITY
# ==============================================================================


@pytest.mark.unit
def test_atom_id_homogeneous_ordering_and_equality(
    sample_individual_id: IndividualID,
    sample_fact_id: FactID,
) -> None:
    """Verify same-class ordering works, string equality holds, and cross-class < raises TypeError."""
    id2 = IndividualID("IND-000002")
    id3 = IndividualID("IND-000003")

    assert sample_individual_id < id2
    assert id2 > sample_individual_id
    assert sample_individual_id <= id2
    assert id2 >= sample_individual_id
    assert sample_individual_id == IndividualID("IND-000001")
    assert sample_individual_id == "IND-000001"
    assert sample_individual_id != id2
    assert hash(sample_individual_id) == hash("IND-000001")
    assert sorted([id3, sample_individual_id, id2]) == [sample_individual_id, id2, id3]

    # Cross-type ordering must raise TypeError
    with pytest.raises(TypeError):
        _ = sample_individual_id < sample_fact_id  # type: ignore[operator]
    with pytest.raises(TypeError):
        _ = sample_individual_id < AtomID("IND-000002")  # type: ignore[operator]
    with pytest.raises(TypeError):
        _ = sample_individual_id < "IND-000002"  # type: ignore[operator]


@pytest.mark.unit
def test_atom_id_comparison_with_incompatible_type_returns_not_implemented(
    sample_individual_id: IndividualID,
) -> None:
    """Verify AtomID comparison against non-string/non-AtomID returns False or TypeError."""
    assert (sample_individual_id == 123) is False  # type: ignore[comparison-overlap]
    with pytest.raises(TypeError):
        _ = sample_individual_id < 123  # type: ignore[operator]


# ==============================================================================
# GROUP 4: UUIDV4 IDENTIFIERS
# ==============================================================================


@pytest.mark.unit
def test_uuidv4_valid_instantiation() -> None:
    """Verify UUIDv4Str and specialized subclasses validate standard UUIDv4 strings."""
    valid_uuid = "c9a646d3-9c61-4a70-8b14-c48c8b417c8d"

    base_u = UUIDv4Str(valid_uuid)
    assert base_u.value == valid_uuid
    assert str(base_u) == valid_uuid
    assert repr(base_u) == f"UUIDv4Str(value='{valid_uuid}')"

    source_u = SourceID(valid_uuid)
    media_u = MediaID(valid_uuid)
    transcript_u = TranscriptID(valid_uuid)
    service_u = ServiceRecordID(valid_uuid)

    assert source_u.value == valid_uuid
    assert media_u.value == valid_uuid
    assert transcript_u.value == valid_uuid
    assert service_u.value == valid_uuid


@pytest.mark.unit
@pytest.mark.regression
@pytest.mark.parametrize(
    "invalid_uuid",
    [
        "",
        "   ",
        " c9a646d3-9c61-4a70-8b14-c48c8b417c8d ",  # Padded whitespace forbidden
        "c9a646d3-9c61-1a70-8b14-c48c8b417c8d",  # Version 1 instead of 4
        "C9A646D3-9C61-4A70-8B14-C48C8B417C8D",  # Uppercase not allowed
        "c9a646d39c614a708b14c48c8b417c8d",  # Missing hyphens
        "c9a646d3-9c61-4a70-cb14-c48c8b417c8d",  # Invalid variant (c instead of 8,9,a,b)
        "not-a-uuid",
    ],
)
def test_uuidv4_invalid_format_raises_error(invalid_uuid: str) -> None:
    """Verify UUIDv4Str raises ModelFormatError when input is not RFC 4122 lowercase UUIDv4."""
    with pytest.raises(ModelFormatError, match="Invalid UUIDv4 format"):
        UUIDv4Str(invalid_uuid)


@pytest.mark.unit
def test_uuidv4_homogeneous_ordering_and_equality() -> None:
    """Verify UUIDv4Str instances sort homogeneously and compare with strings for equality."""
    u1 = UUIDv4Str("00000000-0000-4000-8000-000000000001")
    u2 = UUIDv4Str("00000000-0000-4000-8000-000000000002")
    s1 = SourceID("00000000-0000-4000-8000-000000000001")

    assert u1 < u2
    assert u2 > u1
    assert u1 <= u2
    assert u2 >= u1
    assert u1 == UUIDv4Str("00000000-0000-4000-8000-000000000001")
    assert u1 == "00000000-0000-4000-8000-000000000001"
    assert u1 != u2
    assert hash(u1) == hash("00000000-0000-4000-8000-000000000001")
    assert sorted([u2, u1]) == [u1, u2]

    # Cross-type ordering must raise TypeError
    with pytest.raises(TypeError):
        _ = u1 < s1  # type: ignore[operator]
    with pytest.raises(TypeError):
        _ = u1 < "00000000-0000-4000-8000-000000000002"  # type: ignore[operator]


@pytest.mark.unit
def test_uuidv4_comparison_with_incompatible_type_returns_not_implemented(
    sample_uuid: UUIDv4Str,
) -> None:
    """Verify UUIDv4Str comparison against non-string/non-UUIDv4 returns False or TypeError."""
    assert (sample_uuid == 999) is False  # type: ignore[comparison-overlap]
    with pytest.raises(TypeError):
        _ = sample_uuid < 999  # type: ignore[operator]


# ==============================================================================
# GROUP 5: IMMUTABILITY & INTROSPECTION
# ==============================================================================


@pytest.mark.unit
def test_atom_id_immutability(
    sample_individual_id: IndividualID,
    sample_uuid: UUIDv4Str,
) -> None:
    """Verify that attempting to mutate a frozen identifier raises an error."""
    with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
        sample_individual_id.value = "IND-000002"  # type: ignore[misc]

    with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
        sample_uuid.value = "00000000-0000-4000-8000-000000000002"  # type: ignore[misc]


@pytest.mark.unit
def test_atom_id_introspection(sample_individual_id: IndividualID) -> None:
    """Verify .help() renders member directory on AtomID subclasses."""
    help_text = sample_individual_id.help(as_str=True)
    assert help_text is not None
    assert "=== IndividualID Public Directory ===" in help_text
    assert "prefix" in help_text
    assert "suffix" in help_text
