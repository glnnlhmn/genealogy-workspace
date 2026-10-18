# Name: test_primitives.py
# Path: tests/test_gda/test_types/test_primitives.py

"""Comprehensive unit test suite for gda.types.primitives.

Operational Role:
    Verifies declarative regex patterns, compiled regular expressions, and ISO
    format directives against canonical examples and invalid boundary strings.

Test Structure & Protocol:
    - Atomized tests: 1:1 behavioral contract mapping.
    - Fully decorated: Decorated with @pytest.mark.unit and @pytest.mark.smoke.
    - Dependencies: In-memory evaluation with zero disk I/O.

Note:
    PRERELEASE: Test suite is under active development (version 0.0.1+build.2).
"""

from __future__ import annotations

import re

import pytest

import gda.types.primitives as prim

__version__ = "0.0.1+build.2"

# ==============================================================================
# GROUP 1: Format String Constants
# Note: Invariant checks on strftime directives
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_iso_format_constants_match_expected_directives() -> None:
    """Verify that ISO format string tokens declare standard strftime directives."""
    assert prim.ISO_YEAR_FMT == "%Y"
    assert prim.ISO_MONTH_FMT == "%Y-%m"
    assert prim.ISO_DATE_FMT == "%Y-%m-%d"
    assert prim.ISO_TIMESTAMP_FMT == "%Y-%m-%dT%H:%M:%SZ"


# ==============================================================================
# GROUP 2: UUIDv4 Regex Pattern Verification
# Note: Lowercase RFC 4122 compliance and rejection boundaries
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_uuid_v4_regex_accepts_valid_lowercase_uuid() -> None:
    """Verify UUID_V4_REGEX matches valid canonical lowercase RFC 4122 UUIDv4 strings."""
    valid_uuid = "a1b2c3d4-e5f6-4a1b-8c2d-3e4f5a6b7c8d"
    assert prim.UUID_V4_REGEX.match(valid_uuid) is not None


@pytest.mark.unit
def test_uuid_v4_regex_rejects_uppercase_letters() -> None:
    """Verify UUID_V4_REGEX strictly rejects uppercase hex characters."""
    upper_uuid = "A1B2C3D4-E5F6-4A1B-8C2D-3E4F5A6B7C8D"
    assert prim.UUID_V4_REGEX.match(upper_uuid) is None


@pytest.mark.unit
def test_uuid_v4_regex_rejects_non_version_4_variant() -> None:
    """Verify UUID_V4_REGEX rejects UUIDs lacking version 4 or RFC variant bits."""
    v1_uuid = "a1b2c3d4-e5f6-1a1b-8c2d-3e4f5a6b7c8d"
    assert prim.UUID_V4_REGEX.match(v1_uuid) is None
    bad_variant_uuid = "a1b2c3d4-e5f6-4a1b-0c2d-3e4f5a6b7c8d"
    assert prim.UUID_V4_REGEX.match(bad_variant_uuid) is None


# ==============================================================================
# GROUP 3: ISO Date and Timestamp Pattern Verification
# Note: Calendar and timestamp boundary conformance
# ==============================================================================


@pytest.mark.unit
def test_iso_date_regex_matches_valid_year_month_day() -> None:
    """Verify ISO_DATE_REGEX matches year-only, year-month, and full date strings."""
    assert prim.ISO_DATE_REGEX.match("1880") is not None
    assert prim.ISO_DATE_REGEX.match("1880-05") is not None
    assert prim.ISO_DATE_REGEX.match("1880-05-14") is not None


@pytest.mark.unit
def test_iso_date_regex_rejects_out_of_range_calendar_units() -> None:
    """Verify ISO_DATE_REGEX rejects month > 12 and day > 31."""
    assert prim.ISO_DATE_REGEX.match("1880-13-01") is None
    assert prim.ISO_DATE_REGEX.match("1880-00-01") is None
    assert prim.ISO_DATE_REGEX.match("1880-05-32") is None
    assert prim.ISO_DATE_REGEX.match("1880-05-00") is None


@pytest.mark.unit
def test_iso_timestamp_regex_matches_utc_and_offset_timestamps() -> None:
    """Verify ISO_TIMESTAMP_REGEX matches extended ISO 8601 UTC and offset strings."""
    assert prim.ISO_TIMESTAMP_REGEX.match("2026-10-16T08:57:00Z") is not None
    assert prim.ISO_TIMESTAMP_REGEX.match("2026-10-16T08:57:00.123456Z") is not None
    assert prim.ISO_TIMESTAMP_REGEX.match("2026-10-16T08:57:00-04:00") is not None


@pytest.mark.unit
def test_iso_timestamp_regex_rejects_malformed_time_strings() -> None:
    """Verify ISO_TIMESTAMP_REGEX rejects missing timezone or invalid separators."""
    assert prim.ISO_TIMESTAMP_REGEX.match("2026-10-16 08:57:00") is None
    assert prim.ISO_TIMESTAMP_REGEX.match("2026-10-16T08:57") is None


# ==============================================================================
# GROUP 4: Canonical Entity ID Patterns
# Note: Prefix matching for IND, LOC, SID, NOT, REP
# ==============================================================================


@pytest.mark.unit
def test_entity_id_patterns_cover_all_canonical_prefixes() -> None:
    """Verify ENTITY_ID_PATTERNS contains exact regex mappings for IND, LOC, SID, NOT, and REP."""
    expected_prefixes = {"IND", "LOC", "SID", "NOT", "REP"}
    assert set(prim.ENTITY_ID_PATTERNS.keys()) == expected_prefixes


@pytest.mark.unit
def test_entity_id_patterns_validate_five_digit_padded_identifiers() -> None:
    """Verify each entity prefix regex matches valid 5-digit padded IDs and rejects malformed ones."""
    for prefix, pattern in prim.ENTITY_ID_PATTERNS.items():
        regex = re.compile(pattern)
        assert regex.match(f"{prefix}-00042") is not None
        assert regex.match(f"{prefix}-12345") is not None
        assert regex.match(f"{prefix}-42") is None
        assert regex.match(f"{prefix}-000042") is None
        assert regex.match(f"{prefix.lower()}-00042") is None


# ==============================================================================
# GROUP 5: SHA-256 Hash Patterns
# Note: Lowercase 64-character hexadecimal digest validation
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_sha256_regex_accepts_valid_lowercase_digest() -> None:
    """Verify SHA256_REGEX matches valid 64-character lowercase hex strings."""
    valid_hash = "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
    assert prim.SHA256_REGEX.match(valid_hash) is not None


@pytest.mark.unit
def test_sha256_regex_rejects_uppercase_and_non_hex() -> None:
    """Verify SHA256_REGEX rejects uppercase letters and non-hex characters."""
    upper_hash = "B94D27B9934D3E08A52E52D7DA7DABFAC484EFE37A5380EE9088F7ACE2EFCDE9"
    assert prim.SHA256_REGEX.match(upper_hash) is None
    assert prim.SHA256_REGEX.match("z" * 64) is None
    assert prim.SHA256_REGEX.match("a" * 63) is None
    assert prim.SHA256_REGEX.match("a" * 65) is None
