# Name: test_ids.py
# Path: tests/test_gda/test_util/test_ids.py

"""Comprehensive unit test suite for gda.util.ids.

Operational Role:
    Verifies pure stateless UUIDv4 generation, UUID validation, canonical
    sequential 5-digit entity ID validation, formatting, and decomposition helpers.

Test Structure & Protocol:
    - Atomized tests: 1:1 behavioral contract mapping.
    - Fully decorated: Decorated with @pytest.mark.unit and @pytest.mark.smoke.
    - Dependencies: In-memory evaluation with zero disk I/O.

Note:
    PRERELEASE: Test suite is under active development (version 0.0.1+build.2).
"""

from __future__ import annotations

import pytest

import gda.util.ids as uids

__version__ = "0.0.1+build.2"

# ==============================================================================
# GROUP 1: UUIDv4 Minting and Validation
# Note: Lowercase RFC 4122 compliance and rejection boundaries
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_mint_uuid_produces_valid_lowercase_uuid_v4() -> None:
    """Verify mint_uuid returns a lowercase string conforming to RFC 4122 UUIDv4."""
    minted = uids.mint_uuid()
    assert isinstance(minted, str)
    assert uids.is_valid_uuid(minted) is True
    assert minted == minted.lower()


@pytest.mark.unit
def test_is_valid_uuid_rejects_uppercase_and_malformed_strings() -> None:
    """Verify is_valid_uuid rejects uppercase strings and invalid UUID syntax."""
    valid_lower = "c2b5d0e2-6d2b-4fa8-b0a5-29653a99264c"
    assert uids.is_valid_uuid(valid_lower) is True
    assert uids.is_valid_uuid(valid_lower.upper()) is False
    assert uids.is_valid_uuid("not-a-uuid") is False
    assert uids.is_valid_uuid(None) is False
    assert uids.is_valid_uuid("") is False


# ==============================================================================
# GROUP 2: Entity ID Validation Predicates
# Note: Prefix-specific and generic 5-digit entity ID checks
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_is_valid_entity_id_accepts_all_canonical_prefixes() -> None:
    """Verify is_valid_entity_id returns True for all registered canonical prefixes."""
    assert uids.is_valid_entity_id("IND-00001") is True
    assert uids.is_valid_entity_id("LOC-00042") is True
    assert uids.is_valid_entity_id("SID-00100") is True
    assert uids.is_valid_entity_id("NOT-00500") is True
    assert uids.is_valid_entity_id("REP-00010") is True


@pytest.mark.unit
def test_is_valid_entity_id_rejects_none_empty_and_non_strings() -> None:
    """Verify is_valid_entity_id returns False on None, empty, or non-string inputs."""
    assert uids.is_valid_entity_id(None) is False
    assert uids.is_valid_entity_id("") is False
    assert uids.is_valid_entity_id(12345) is False  # type: ignore[arg-type]


@pytest.mark.unit
def test_is_valid_entity_id_rejects_unregistered_prefix_without_prefix_arg() -> None:
    """Verify is_valid_entity_id returns False when identifier matches no registered prefix."""
    assert uids.is_valid_entity_id("XYZ-00001") is False
    assert uids.is_valid_entity_id("INVALID") is False


@pytest.mark.unit
def test_is_valid_entity_id_respects_explicit_prefix_filtering() -> None:
    """Verify is_valid_entity_id strictly checks requested prefix when provided."""
    assert uids.is_valid_entity_id("IND-00042", prefix="IND") is True
    assert uids.is_valid_entity_id("LOC-00042", prefix="IND") is False
    assert uids.is_valid_entity_id("IND-00042", prefix="INVALID") is False


@pytest.mark.unit
def test_convenience_id_validators_match_target_prefix() -> None:
    """Verify domain-specific validator predicates match their designated prefixes."""
    assert uids.is_valid_person_id("IND-00001") is True
    assert uids.is_valid_person_id("LOC-00001") is False

    assert uids.is_valid_location_id("LOC-00001") is True
    assert uids.is_valid_location_id("SID-00001") is False

    assert uids.is_valid_site_id("SID-00001") is True
    assert uids.is_valid_site_id("IND-00001") is False

    assert uids.is_valid_note_id("NOT-00001") is True
    assert uids.is_valid_note_id("REP-00001") is False

    assert uids.is_valid_repository_id("REP-00001") is True
    assert uids.is_valid_repository_id("NOT-00001") is False


@pytest.mark.unit
def test_entity_id_validators_reject_malformed_padding() -> None:
    """Verify entity ID validators reject strings without exact 5-digit zero-padding."""
    assert uids.is_valid_person_id("IND-1") is False
    assert uids.is_valid_person_id("IND-01") is False
    assert uids.is_valid_person_id("IND-000001") is False
    assert uids.is_valid_person_id("IND-ABCDE") is False


# ==============================================================================
# GROUP 3: Formatting and Decomposition Helpers
# Note: Zero-padding generation and structural decomposition
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_format_entity_id_pads_sequence_correctly() -> None:
    """Verify format_entity_id produces standardized 5-digit padded identifiers."""
    assert uids.format_entity_id("IND", 1) == "IND-00001"
    assert uids.format_entity_id("loc", 42) == "LOC-00042"
    assert uids.format_entity_id("SID", 99999) == "SID-99999"


@pytest.mark.unit
def test_format_entity_id_raises_value_error_for_invalid_inputs() -> None:
    """Verify format_entity_id raises ValueError on unregistered prefixes or out-of-range numbers."""
    with pytest.raises(ValueError, match="Unrecognized entity prefix"):
        uids.format_entity_id("UNKNOWN", 1)

    with pytest.raises(ValueError, match="out of allowable range"):
        uids.format_entity_id("IND", -1)

    with pytest.raises(ValueError, match="out of allowable range"):
        uids.format_entity_id("IND", 100000)


@pytest.mark.unit
def test_parse_entity_id_decomposes_valid_identifier() -> None:
    """Verify parse_entity_id returns the correct prefix string and integer sequence."""
    prefix, seq = uids.parse_entity_id("LOC-00105")
    assert prefix == "LOC"
    assert seq == 105

    prefix_ind, seq_ind = uids.parse_entity_id("IND-00001")
    assert prefix_ind == "IND"
    assert seq_ind == 1


@pytest.mark.unit
def test_parse_entity_id_raises_value_error_on_invalid_identifiers() -> None:
    """Verify parse_entity_id raises ValueError on malformed syntax or unregistered prefixes."""
    with pytest.raises(ValueError, match="Cannot parse entity ID"):
        uids.parse_entity_id(None)

    with pytest.raises(
        ValueError, match="does not conform to entity identifier format"
    ):
        uids.parse_entity_id("INVALID_ID")

    with pytest.raises(ValueError, match="not a registered canonical entity prefix"):
        uids.parse_entity_id("ABC-00100")
