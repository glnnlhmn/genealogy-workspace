"""Path: tests/test_gda/test_model/test_atom/test_id.py

Comprehensive test suite verifying AtomID and UUIDv4Str identifier primitives.

Operational Role:
    Verifies that AtomID enforces the 'AAA-######' format, validates specialized prefixes
    (IND, FID, LOC, SID, FAM, NOT, REP), executes total ordering, and validates
    RFC 4122 lowercase UUIDv4 identifiers including SourceID, MediaID, and TranscriptID.

Test Structure & Protocol:
    - Atomized tests: 1:1 behavioral contract mapping.
    - Fully decorated: Standard 7-marker taxonomy.
    - Zero production disk I/O.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from gda.core.errors import ModelFormatError, ModelPrefixMismatchError
from gda.model.atom.id import (
    AtomID,
    FactID,
    FamilyID,
    IndividualID,
    LocationID,
    MediaID,
    NoteID,
    RepositoryID,
    SiteID,
    SourceID,
    TranscriptID,
    UUIDv4Str,
)

__version__ = "1.0.0+build.9"


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


@pytest.mark.unit
@pytest.mark.regression
@pytest.mark.parametrize(
    "invalid_id",
    [
        "",
        "   ",
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
@pytest.mark.smoke
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
@pytest.mark.smoke
def test_specialized_atom_subclasses_valid_instantiation() -> None:
    """Verify each specialized AtomID subclass instantiates with its expected prefix."""
    assert IndividualID("IND-000001").prefix == "IND"
    assert FactID("FID-000002").prefix == "FID"
    assert LocationID("LOC-000003").prefix == "LOC"
    assert SiteID("SID-000004").prefix == "SID"
    assert FamilyID("FAM-000005").prefix == "FAM"
    assert NoteID("NOT-000006").prefix == "NOT"
    assert RepositoryID("REP-000007").prefix == "REP"


@pytest.mark.unit
@pytest.mark.regression
def test_individual_id_prefix_mismatch_raises_error() -> None:
    """Verify IndividualID raises ModelPrefixMismatchError when passed non-IND prefix."""
    with pytest.raises(
        ModelPrefixMismatchError, match="Prefix mismatch for IndividualID"
    ):
        IndividualID("FID-000001")


@pytest.mark.unit
@pytest.mark.regression
def test_fact_id_prefix_mismatch_raises_error() -> None:
    """Verify FactID raises ModelPrefixMismatchError when passed non-FID prefix."""
    with pytest.raises(ModelPrefixMismatchError, match="Prefix mismatch for FactID"):
        FactID("IND-000001")


@pytest.mark.unit
@pytest.mark.regression
def test_location_id_prefix_mismatch_raises_error() -> None:
    """Verify LocationID raises ModelPrefixMismatchError when passed non-LOC prefix."""
    with pytest.raises(
        ModelPrefixMismatchError, match="Prefix mismatch for LocationID"
    ):
        LocationID("SID-000001")


@pytest.mark.unit
@pytest.mark.regression
def test_site_id_prefix_mismatch_raises_error() -> None:
    """Verify SiteID raises ModelPrefixMismatchError when passed non-SID prefix."""
    with pytest.raises(ModelPrefixMismatchError, match="Prefix mismatch for SiteID"):
        SiteID("LOC-000001")


@pytest.mark.unit
@pytest.mark.regression
def test_family_id_prefix_mismatch_raises_error() -> None:
    """Verify FamilyID raises ModelPrefixMismatchError when passed non-FAM prefix."""
    with pytest.raises(ModelPrefixMismatchError, match="Prefix mismatch for FamilyID"):
        FamilyID("IND-000001")


@pytest.mark.unit
@pytest.mark.regression
def test_note_id_prefix_mismatch_raises_error() -> None:
    """Verify NoteID raises ModelPrefixMismatchError when passed non-NOT prefix."""
    with pytest.raises(ModelPrefixMismatchError, match="Prefix mismatch for NoteID"):
        NoteID("REP-000001")


@pytest.mark.unit
@pytest.mark.regression
def test_repository_id_prefix_mismatch_raises_error() -> None:
    """Verify RepositoryID raises ModelPrefixMismatchError when passed non-REP prefix."""
    with pytest.raises(
        ModelPrefixMismatchError, match="Prefix mismatch for RepositoryID"
    ):
        RepositoryID("NOT-000001")


# ==============================================================================
# GROUP 3: ATOMID TOTAL ORDERING & COMPARISON
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_atom_id_total_ordering() -> None:
    """Verify AtomID instances sort correctly and compare with strings."""
    id1 = IndividualID("IND-000001")
    id2 = IndividualID("IND-000002")
    id3 = AtomID("IND-000003")

    assert id1 < id2
    assert id2 > id1
    assert id1 <= id2
    assert id2 >= id1
    assert id1 == IndividualID("IND-000001")
    assert id1 != id2
    assert id1 < "IND-000002"
    assert id2 > "IND-000001"
    assert sorted([id3, id1, id2]) == [id1, id2, id3]


@pytest.mark.unit
def test_atom_id_comparison_with_incompatible_type_returns_not_implemented() -> None:
    """Verify AtomID comparison against non-string/non-AtomID returns False or TypeError."""
    id1 = IndividualID("IND-000001")
    assert (id1 == 123) is False  # type: ignore[comparison-overlap]
    with pytest.raises(TypeError):
        _ = id1 < 123  # type: ignore[operator]


# ==============================================================================
# GROUP 4: UUIDV4 IDENTIFIERS
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
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

    assert source_u.value == valid_uuid
    assert media_u.value == valid_uuid
    assert transcript_u.value == valid_uuid


@pytest.mark.unit
@pytest.mark.regression
@pytest.mark.parametrize(
    "invalid_uuid",
    [
        "",
        "   ",
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
@pytest.mark.smoke
def test_uuidv4_total_ordering() -> None:
    """Verify UUIDv4Str instances sort correctly and compare with strings."""
    u1 = UUIDv4Str("00000000-0000-4000-8000-000000000001")
    u2 = UUIDv4Str("00000000-0000-4000-8000-000000000002")

    assert u1 < u2
    assert u2 > u1
    assert u1 <= u2
    assert u2 >= u1
    assert u1 == UUIDv4Str("00000000-0000-4000-8000-000000000001")
    assert u1 != u2
    assert u1 < "00000000-0000-4000-8000-000000000002"
    assert sorted([u2, u1]) == [u1, u2]


@pytest.mark.unit
def test_uuidv4_comparison_with_incompatible_type_returns_not_implemented() -> None:
    """Verify UUIDv4Str comparison against non-string/non-UUIDv4 returns False or TypeError."""
    u1 = UUIDv4Str("00000000-0000-4000-8000-000000000001")
    assert (u1 == 999) is False  # type: ignore[comparison-overlap]
    with pytest.raises(TypeError):
        _ = u1 < 999  # type: ignore[operator]


# ==============================================================================
# GROUP 5: IMMUTABILITY & INTROSPECTION
# ==============================================================================


@pytest.mark.unit
def test_atom_id_immutability() -> None:
    """Verify that attempting to mutate a frozen identifier raises an error."""
    ind = IndividualID("IND-000001")
    with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
        ind.value = "IND-000002"  # type: ignore[misc]

    uid = UUIDv4Str("00000000-0000-4000-8000-000000000001")
    with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
        uid.value = "00000000-0000-4000-8000-000000000002"  # type: ignore[misc]


@pytest.mark.unit
def test_atom_id_introspection() -> None:
    """Verify .help() renders member directory on AtomID subclasses."""
    ind = IndividualID("IND-000001")
    help_text = ind.help(as_str=True)
    assert help_text is not None
    assert "=== IndividualID Public Directory ===" in help_text
    assert "prefix" in help_text
    assert "suffix" in help_text
