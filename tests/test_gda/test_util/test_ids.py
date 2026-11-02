"""Path: tests/test_gda/test_util/test_ids.py

Comprehensive unit test suite for gda.util.ids.

Operational Role:
    Verifies IDType and SmartIDPrefix validation, stateless UUID minting,
    smartID minting, decomposition, and prefix-scoped high-water mark extraction
    with 100% statement and branch coverage.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

import gda.util.ids as uids
from gda.enums.core import IDType, SmartIDPrefix
from gda.model.atom.id import LocationID

__version__ = "0.0.2+build.9"


# ==============================================================================
# GROUP 1: Public verify_id Dispatching & Type Constraints
# ==============================================================================


@pytest.mark.unit
def test_verify_id_defaults_to_smart_id_and_accepts_valid() -> None:
    """Verify verify_id defaults to IDType.SMART_ID and validates correct format."""
    assert uids.verify_id("LOC-000104") is True
    assert uids.verify_id("IND-000001") is True
    assert uids.verify_id("INVALID-FORMAT") is False


@pytest.mark.unit
def test_verify_id_enforces_specific_smart_id_prefix() -> None:
    """Verify verify_id strictly validates the requested SmartIDPrefix."""
    assert uids.verify_id("LOC-000104", smart_id_prefix=SmartIDPrefix.LOC) is True
    assert uids.verify_id("LOC-000104", smart_id_prefix=SmartIDPrefix.IND) is False


@pytest.mark.unit
def test_verify_id_validates_uuid_type() -> None:
    """Verify verify_id validates lowercase UUIDv4 format when IDType.UUID is specified."""
    valid_uuid = "c2b5d0e2-6d2b-4fa8-b0a5-29653a99264c"
    assert uids.verify_id(valid_uuid, id_type=IDType.UUID) is True
    assert uids.verify_id(valid_uuid.upper(), id_type=IDType.UUID) is False
    assert uids.verify_id("not-a-uuid", id_type=IDType.UUID) is False


@pytest.mark.regression
def test_verify_id_raises_type_error_for_non_string_val() -> None:
    """Verify verify_id raises TypeError when val is not a string."""
    with pytest.raises(TypeError, match="must be a string"):
        uids.verify_id(None)  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="must be a string"):
        uids.verify_id(123456)  # type: ignore[arg-type]


@pytest.mark.regression
def test_verify_id_raises_value_error_if_prefix_passed_for_uuid() -> None:
    """Verify verify_id raises ValueError if smart_id_prefix is provided with IDType.UUID."""
    with pytest.raises(ValueError, match="cannot be specified for IDType.UUID"):
        uids.verify_id(
            "c2b5d0e2-6d2b-4fa8-b0a5-29653a99264c",
            id_type=IDType.UUID,
            smart_id_prefix=SmartIDPrefix.LOC,
        )


@pytest.mark.regression
def test_verify_id_returns_false_for_empty_or_whitespace_strings() -> None:
    """Verify verify_id returns False on empty or blank candidate strings."""
    assert uids.verify_id("") is False
    assert uids.verify_id("   ") is False


@pytest.mark.regression
def test_verify_id_returns_false_for_unsupported_id_type() -> None:
    """Verify verify_id returns False if an unrecognized IDType is supplied."""
    assert uids.verify_id("LOC-000104", id_type="UNKNOWN") is False  # type: ignore[arg-type]


@pytest.mark.regression
def test_validate_smart_id_rejects_missing_or_multiple_hyphens() -> None:
    """Verify smartID validation rejects strings without hyphens or with multiple hyphens."""
    assert uids.verify_id("NOHYPHENHERE") is False
    assert uids.verify_id("URN-LOC-000104") is False


@pytest.mark.regression
def test_validate_smart_id_handles_missing_atom_class_mapping() -> None:
    """Verify smartID validation returns False if a prefix has no mapped AtomID class."""
    with patch.dict(uids._PREFIX_TO_ATOM_CLASS, {SmartIDPrefix.LOC: None}, clear=False):
        assert uids.verify_id("LOC-000104", smart_id_prefix=SmartIDPrefix.LOC) is False


# ==============================================================================
# GROUP 2: UUIDv4 Minting (mint_uuid)
# ==============================================================================


@pytest.mark.unit
def test_mint_uuid_produces_valid_lowercase_uuid_v4() -> None:
    """Verify mint_uuid returns a lowercase string conforming to RFC 4122 UUIDv4."""
    minted = uids.mint_uuid()
    assert isinstance(minted, str)
    assert uids.verify_id(minted, id_type=IDType.UUID) is True
    assert minted == minted.lower()


# ==============================================================================
# GROUP 3: SmartID Minting & Decomposition
# ==============================================================================


@pytest.mark.unit
def test_mint_smart_id_mints_from_enum_and_sequence_num() -> None:
    """Verify mint_smart_id formats smartIDs from SmartIDPrefix and sequence number."""
    assert uids.mint_smart_id(SmartIDPrefix.LOC, 104) == "LOC-000104"
    assert uids.mint_smart_id(SmartIDPrefix.IND, 42, padding=6) == "IND-000042"


@pytest.mark.regression
def test_mint_smart_id_raises_value_error_on_negative_sequence() -> None:
    """Verify mint_smart_id raises ValueError when sequence_num is negative."""
    with pytest.raises(ValueError, match="cannot be negative"):
        uids.mint_smart_id(SmartIDPrefix.LOC, -1)


@pytest.mark.unit
def test_parse_smart_id_extracts_enum_prefix_and_integer() -> None:
    """Verify parse_smart_id decomposes identifier into SmartIDPrefix and int sequence."""
    prefix, seq = uids.parse_smart_id("LOC-000105")
    assert prefix == SmartIDPrefix.LOC
    assert seq == 105


@pytest.mark.unit
def test_parse_smart_id_supports_value_objects() -> None:
    """Verify parse_smart_id supports objects exposing a .value attribute."""
    prefix, seq = uids.parse_smart_id(LocationID("LOC-000104"))
    assert prefix == SmartIDPrefix.LOC
    assert seq == 104


@pytest.mark.regression
def test_parse_smart_id_raises_value_error_on_invalid_or_compound_inputs() -> None:
    """Verify parse_smart_id strictly raises ValueError on malformed or compound inputs."""
    with pytest.raises(ValueError, match="Cannot parse smartID"):
        uids.parse_smart_id(None)
    with pytest.raises(ValueError, match="Cannot parse smartID"):
        uids.parse_smart_id(12345)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="Cannot parse smartID"):
        uids.parse_smart_id("   ")
    with pytest.raises(ValueError, match="does not conform"):
        uids.parse_smart_id("URN-LOC-000105")
    with pytest.raises(ValueError, match="does not conform"):
        uids.parse_smart_id("LOC-12345")


# ==============================================================================
# GROUP 4: High-Water Mark Sequence Extraction (extract_max_smart_id)
# ==============================================================================


@pytest.mark.unit
def test_extract_max_smart_id_empty_or_scalar_returns_zero() -> None:
    """Verify empty collections, None, or string/byte scalars return default 0."""
    assert uids.extract_max_smart_id([]) == 0
    assert uids.extract_max_smart_id(None) == 0
    assert uids.extract_max_smart_id("LOC-000100") == 0
    assert uids.extract_max_smart_id(b"LOC-000100") == 0


@pytest.mark.unit
def test_extract_max_smart_id_extracts_highest_integer_from_valid_smart_ids() -> None:
    """Verify maximum integer extraction from valid smartID sequences."""
    identifiers = ["LOC-000001", "LOC-000104", "LOC-000012"]
    assert uids.extract_max_smart_id(identifiers) == 104


@pytest.mark.unit
def test_extract_max_smart_id_supports_atom_value_objects() -> None:
    """Verify extraction handles AtomID domain objects exposing a .value attribute."""
    identifiers = [LocationID("LOC-000005"), LocationID("LOC-000250")]
    assert uids.extract_max_smart_id(identifiers) == 250


@pytest.mark.unit
def test_extract_max_smart_id_filters_by_prefix() -> None:
    """Verify extraction filters by SmartIDPrefix to prevent cross-prefix collision."""
    mixed_identifiers = ["LOC-000010", "IND-000500", "LOC-000045"]
    assert uids.extract_max_smart_id(mixed_identifiers, prefix=SmartIDPrefix.LOC) == 45
    assert uids.extract_max_smart_id(mixed_identifiers, prefix=SmartIDPrefix.IND) == 500


@pytest.mark.regression
def test_extract_max_smart_id_ignores_invalid_tokens_by_default() -> None:
    """Verify compound, malformed, or non-string tokens are ignored by default."""
    identifiers = [
        "URN-LOC-000999",
        "LOC-12345",
        None,
        123,
        "LOC-000104",
    ]
    assert uids.extract_max_smart_id(identifiers, ignore_errors=True) == 104


@pytest.mark.regression
def test_extract_max_smart_id_raises_when_ignore_errors_false() -> None:
    """Verify ValueError is raised if ignore_errors is set to False on invalid token."""
    identifiers = ["LOC-000104", "INVALID-ID"]
    with pytest.raises(ValueError, match="does not conform"):
        uids.extract_max_smart_id(identifiers, ignore_errors=False)
