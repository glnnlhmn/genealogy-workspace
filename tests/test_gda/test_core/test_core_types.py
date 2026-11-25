"""Path: tests/test_gda/test_core/test_core_types.py

Comprehensive unit, regression, and property-based test suite for gda.core.types.

Operational Role:
    Verifies declarative regex patterns, compiled regular expressions, ISO
    format directives, entity/archival URN patterns across all 14 namespaces,
    SQL identifier patterns, enum key separator patterns, domain scalar
    invariants, and CIU-B1-001 strict numeric guards (is_strict_int,
    is_finite_number).

Test Structure & Protocol:
    - Atomized & parametrized tests: 1:1 behavioral contract mapping.
    - Fully decorated: 5-marker taxonomy (smoke, unit, regression, integrity).
    - Property-based: Hypothesis strategies imported from test_core/strategies.py.
    - Dependencies: Pure in-memory evaluation with zero disk I/O.
"""

from __future__ import annotations

import re
from decimal import Decimal
from enum import IntEnum, StrEnum
from typing import Any

import pytest
from hypothesis import given
from hypothesis import strategies as st
from tests.test_gda.test_core.strategies import (
    bool_or_non_int,
    iso_date_strings,
    non_finite_floats,
    strict_ints,
    utc_timestamps,
)

import gda.core.types as prim

__version__ = "1.0.0+build.12"


class _SampleIntEnum(IntEnum):
    """Test helper IntEnum to verify int subclasses are accepted by is_strict_int."""

    ONE = 1


class _SampleStrEnum(StrEnum):
    """Test helper StrEnum to verify string enums are rejected by is_strict_int."""

    ONE = "1"


ALL_14_URN_NAMESPACES: set[str] = {
    "SRC",
    "DRAFT",
    "CENSUS",
    "VITAL",
    "CEM",
    "DIPLOMA",
    "IMMIGRATION",
    "NATURALIZATION",
    "LAND",
    "MS",
    "BIBLE",
    "NARRATIVE",
    "OTHER",
    "WILL",
}

URN_NAMESPACE_CASES: list[tuple[str, str, str]] = [
    (
        "SRC",
        "URN:SRC:1917:NH_MERRIMACK:DOC_001",
        "URN:SRC:17:NH_MERRIMACK:DOC_001",
    ),
    (
        "DRAFT",
        "URN:DRAFT:1863:NH_DIST2:ROLL_001",
        "URN:DRAFT:1863:nh_dist2:ROLL_001",
    ),
    (
        "CENSUS",
        "URN:CENSUS:1880:NH_MERRIMACK:ED178_S12A",
        "URN:CENSUS:80:NH_MERRIMACK:ED178_S12A",
    ),
    (
        "VITAL",
        "URN:VITAL:BIRTH:1880:NH_CONCORD:CERT_00101",
        "URN:VITAL:BAPTISM:1880:NH_CONCORD:CERT_00101",
    ),
    (
        "CEM",
        "URN:CEM:NH_BLOSSOM_HILL:SEC_A_LOT_12_G1",
        "URN:CEM:nh_blossom_hill:SEC_A_LOT_12_G1",
    ),
    (
        "DIPLOMA",
        "URN:DIPLOMA:1902:MA_CAMBRIDGE:DIP_04",
        "URN:DIPLOMA:UNDATED:MA_CAMBRIDGE:DIP_04",
    ),
    (
        "IMMIGRATION",
        "URN:IMMIGRATION:1892:NY_ELLIS:MAN_105",
        "URN:IMMIGRATION:92:NY_ELLIS:MAN_105",
    ),
    (
        "NATURALIZATION",
        "URN:NATURALIZATION:1910:NH_HILLSBOROUGH:PET_09",
        "URN:NATURALIZATION:1910:NH_HILLSBOROUGH",
    ),
    (
        "LAND",
        "URN:LAND:1850:NH_MERRIMACK:DEED_12",
        "URN:LAND:1850:nh_merrimack:DEED_12",
    ),
    (
        "MS",
        "URN:MS:UNDATED:NH_CONCORD:LEDGER_01",
        "URN:MS:18A:NH_CONCORD:LEDGER_01",
    ),
    (
        "BIBLE",
        "URN:BIBLE:1845:FAMILY_SMITH:ENTRY_02",
        "URN:BIBLE:45:FAMILY_SMITH:ENTRY_02",
    ),
    (
        "NARRATIVE",
        "URN:NARRATIVE:UNDATED:NH_BOW:MEMOIR_01",
        "URN:NARRATIVE:LATER:NH_BOW:MEMOIR_01",
    ),
    (
        "OTHER",
        "URN:OTHER:1875:NH_BOW:RECEIPT_07",
        "URN:OTHER:1875:NH_BOW",
    ),
    (
        "WILL",
        "URN:WILL:1880:NH_MERRIMACK:PROB_04",
        "URN:WILL:1880:nh_merrimack:PROB_04",
    ),
]


# ==============================================================================
# GROUP 1: Smoke & Primary Entrypoints
# Note: Verifies gda.core.types exposes its core regexes, bounds, and guards.
# ==============================================================================


@pytest.mark.smoke
@pytest.mark.unit
def test_types_exposes_expected_public_interface() -> None:
    """Verify gda.core.types exports canonical patterns, bounds, and CIU-B1-001 guards."""
    required_exports = {
        "ENTITY_ID_REGEXES",
        "ENTITY_URN_REGEXES",
        "ISO_DATE_REGEX",
        "ISO_TIMESTAMP_REGEX",
        "SHA256_REGEX",
        "SQL_IDENTIFIER_REGEX",
        "URN_BASE_REGEX",
        "URN_REGEXES",
        "UUID_V4_REGEX",
        "is_finite_number",
        "is_strict_int",
    }
    assert required_exports.issubset(set(prim.__all__))


# ==============================================================================
# GROUP 2: Core Logic & Happy Paths
# Note: Canonical format tokens, valid regex matches, and Hypothesis properties.
# ==============================================================================


@pytest.mark.unit
def test_iso_format_constants_match_expected_directives() -> None:
    """Verify that ISO format string tokens declare standard strftime directives."""
    assert prim.ISO_YEAR_FMT == "%Y"
    assert prim.ISO_MONTH_FMT == "%Y-%m"
    assert prim.ISO_DATE_FMT == "%Y-%m-%d"
    assert prim.ISO_TIMESTAMP_FMT == "%Y-%m-%dT%H:%M:%SZ"


@pytest.mark.unit
def test_uuid_v4_regex_accepts_valid_lowercase_uuid(sample_uuid_v4: str) -> None:
    """Verify UUID_V4_REGEX matches valid canonical lowercase RFC 4122 UUIDv4 strings."""
    assert prim.UUID_V4_REGEX.match(sample_uuid_v4) is not None


@pytest.mark.unit
@pytest.mark.parametrize("valid_date", ["1880", "1880-05", "1880-05-14"])
def test_iso_date_regex_matches_valid_year_month_day(valid_date: str) -> None:
    """Verify ISO_DATE_REGEX matches year-only, year-month, and full date strings."""
    assert prim.ISO_DATE_REGEX.match(valid_date) is not None


@pytest.mark.unit
@given(date_str=iso_date_strings())
def test_iso_date_regex_accepts_hypothesis_iso_dates(date_str: str) -> None:
    """Verify ISO_DATE_REGEX accepts all Hypothesis-generated YYYY/YYYY-MM/YYYY-MM-DD strings."""
    assert prim.ISO_DATE_REGEX.match(date_str) is not None


@pytest.mark.unit
@pytest.mark.parametrize(
    "valid_timestamp",
    [
        "2026-10-16T08:57:00Z",
        "2026-10-16T08:57:00.123456Z",
        "2026-10-16T08:57:00-04:00",
    ],
)
def test_iso_timestamp_regex_matches_utc_and_offset_timestamps(
    valid_timestamp: str,
) -> None:
    """Verify ISO_TIMESTAMP_REGEX matches extended ISO 8601 UTC and offset strings."""
    assert prim.ISO_TIMESTAMP_REGEX.match(valid_timestamp) is not None


@pytest.mark.unit
@given(ts_str=utc_timestamps())
def test_iso_timestamp_regex_accepts_hypothesis_utc_timestamps(ts_str: str) -> None:
    """Verify ISO_TIMESTAMP_REGEX accepts all Hypothesis-generated Zulu UTC timestamps."""
    assert prim.ISO_TIMESTAMP_REGEX.match(ts_str) is not None


@pytest.mark.unit
def test_entity_id_patterns_cover_all_canonical_prefixes() -> None:
    """Verify ENTITY_ID_PATTERNS and ENTITY_ID_REGEXES cover all 9 canonical prefixes."""
    expected_prefixes = {"IND", "FID", "LOC", "SID", "FAM", "NOT", "REP", "DRF", "ORG"}
    assert set(prim.ENTITY_ID_PATTERNS.keys()) == expected_prefixes
    assert set(prim.ENTITY_ID_REGEXES.keys()) == expected_prefixes


@pytest.mark.unit
def test_entity_urn_patterns_cover_all_master_entities() -> None:
    """Verify ENTITY_URN_PATTERNS and ENTITY_URN_REGEXES cover all 6 master entity prefixes."""
    expected_entity_prefixes = {"IND", "FAM", "FID", "LOC", "ORG", "SID"}
    assert set(prim.ENTITY_URN_PATTERNS.keys()) == expected_entity_prefixes
    assert set(prim.ENTITY_URN_REGEXES.keys()) == expected_entity_prefixes


@pytest.mark.unit
@pytest.mark.parametrize(
    ("prefix", "valid_urn"),
    [
        ("IND", "urn:gda:ind:smith_john_1842"),
        ("FAM", "urn:gda:fam:smith_jones_1865"),
        ("FID", "urn:gda:fact:birth_1842_01"),
        ("LOC", "urn:gda:loc:us:nh:merrimack:concord"),
        ("ORG", "urn:gda:org:us:nh:concord:vfw_post_411"),
        ("SID", "urn:gda:site:us:nh:concord:blossom_hill"),
    ],
)
def test_entity_urn_regex_matches_lowercase_and_rejects_uppercase(
    prefix: str,
    valid_urn: str,
) -> None:
    """Verify each entity URN regex accepts canonical lowercase URNs and rejects uppercase."""
    assert prim.ENTITY_URN_REGEXES[prefix].match(valid_urn) is not None
    assert prim.ENTITY_URN_REGEXES[prefix].match(valid_urn.upper()) is None


@pytest.mark.unit
def test_sha256_regex_accepts_valid_lowercase_digest() -> None:
    """Verify SHA256_REGEX matches valid 64-character lowercase hex strings."""
    valid_hash = "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
    assert prim.SHA256_REGEX.match(valid_hash) is not None


@pytest.mark.unit
@pytest.mark.parametrize(
    ("candidate", "should_match"),
    [
        ("vital_births", True),
        ("_private_col_1", True),
        ("1_leading_digit", False),
        ("users; DROP TABLE", False),
    ],
)
def test_sql_identifier_regex_enforces_identifier_syntax(
    candidate: str,
    should_match: bool,
) -> None:
    """Verify SQL_IDENTIFIER_REGEX accepts valid SQLite identifiers and rejects SQL injection."""
    assert (prim.SQL_IDENTIFIER_REGEX.match(candidate) is not None) is should_match


@pytest.mark.unit
@pytest.mark.parametrize(
    ("raw_key", "expected"),
    [
        ("direct primary", "direct_primary"),
        ("non-binary", "non_binary"),
        ("widow / dependent", "widow_dependent"),
    ],
)
def test_enum_key_separator_regex_normalizes_separators(
    raw_key: str,
    expected: str,
) -> None:
    """Verify ENUM_KEY_SEPARATOR_REGEX collapses spaces, hyphens, and slashes to underscores."""
    assert prim.ENUM_KEY_SEPARATOR_REGEX.sub("_", raw_key) == expected


@pytest.mark.unit
@pytest.mark.parametrize(
    ("candidate", "should_match"),
    [
        ("URN:SRC:1917:NH_MERRIMACK:DOC_001", True),
        ("urn:lowercase:bad", False),
        ("NOT_A_URN", False),
    ],
)
def test_urn_base_regex_enforces_archival_urn_envelope(
    candidate: str,
    should_match: bool,
) -> None:
    """Verify URN_BASE_REGEX matches canonical archival URN envelopes and rejects malformed ones."""
    assert (prim.URN_BASE_REGEX.match(candidate) is not None) is should_match


@pytest.mark.unit
@given(value=strict_ints())
def test_is_strict_int_accepts_true_integers(value: int) -> None:
    """Verify is_strict_int returns True for all true integers (CIU-B1-001)."""
    assert prim.is_strict_int(value) is True


@pytest.mark.unit
def test_is_strict_int_accepts_int_enum_instances() -> None:
    """Verify is_strict_int returns True for IntEnum values (CIU-B1-001)."""
    assert prim.is_strict_int(_SampleIntEnum.ONE) is True


@pytest.mark.unit
@given(
    value=st.one_of(
        strict_ints(),
        st.floats(allow_nan=False, allow_infinity=False),
    )
)
def test_is_finite_number_accepts_finite_ints_and_floats(value: int | float) -> None:
    """Verify is_finite_number returns True for all finite ints and floats (CIU-B1-001)."""
    assert prim.is_finite_number(value) is True


# ==============================================================================
# GROUP 3: Edge Cases & Boundary Conditions
# Note: Strict digit-width boundaries and all 14 archival URN namespaces (GAP-CORE-11).
# ==============================================================================


@pytest.mark.regression
def test_entity_id_patterns_enforce_strict_six_digit_identifiers() -> None:
    """Verify each entity prefix regex matches exact 6-digit IDs and rejects 5-digit or 7+ digit IDs."""
    for prefix, pattern in prim.ENTITY_ID_PATTERNS.items():
        regex = re.compile(pattern)
        compiled = prim.ENTITY_ID_REGEXES[prefix]
        assert regex.match(f"{prefix}-000042") is not None
        assert compiled.match(f"{prefix}-000042") is not None
        assert regex.match(f"{prefix}-42") is None
        assert regex.match(f"{prefix}-12345") is None
        assert regex.match(f"{prefix}-1234567") is None
        assert regex.match(f"{prefix}-12345678") is None
        assert regex.match(f"{prefix.lower()}-000042") is None


@pytest.mark.unit
def test_urn_regexes_cover_all_fourteen_namespaces() -> None:
    """Verify URN_PATTERNS and URN_REGEXES declare all 14 archival URN namespaces (GAP-CORE-11)."""
    assert set(prim.URN_PATTERNS.keys()) == ALL_14_URN_NAMESPACES
    assert set(prim.URN_REGEXES.keys()) == ALL_14_URN_NAMESPACES


@pytest.mark.unit
@pytest.mark.parametrize(("namespace", "valid_urn", "_invalid_urn"), URN_NAMESPACE_CASES)
def test_urn_regexes_accept_valid_samples_across_all_14_namespaces(
    namespace: str,
    valid_urn: str,
    _invalid_urn: str,
) -> None:
    """Verify each of the 14 URN_REGEXES entries matches its valid sample URN (GAP-CORE-11)."""
    assert prim.URN_REGEXES[namespace].match(valid_urn) is not None


@pytest.mark.regression
@pytest.mark.parametrize(("namespace", "_valid_urn", "invalid_urn"), URN_NAMESPACE_CASES)
def test_urn_regexes_reject_malformed_samples_across_all_14_namespaces(
    namespace: str,
    _valid_urn: str,
    invalid_urn: str,
) -> None:
    """Verify each of the 14 URN_REGEXES entries rejects malformed URNs (GAP-CORE-11)."""
    assert prim.URN_REGEXES[namespace].match(invalid_urn) is None


@pytest.mark.unit
def test_atom_id_pub_code_and_news_category_regexes() -> None:
    """Verify ATOM_ID_REGEX, PUB_CODE_REGEX, and NEWS_CATEGORY_REGEX against sample inputs."""
    assert prim.ATOM_ID_REGEX.match("IND-000001") is not None
    assert prim.ATOM_ID_REGEX.match("ABC-000001") is not None
    assert prim.ATOM_ID_REGEX.match("IND-0000001") is None
    assert prim.PUB_CODE_REGEX.match("PA-CARL-HERALD") is not None
    assert prim.NEWS_CATEGORY_REGEX.match("OBIT") is not None


# ==============================================================================
# GROUP 4: Error Handling & Validation Failures
# Note: Invalid regex formats, bool-as-int traps, and NaN/Inf rejection guards.
# ==============================================================================


@pytest.mark.regression
def test_uuid_v4_regex_rejects_uppercase_letters(sample_uuid_v4: str) -> None:
    """Verify UUID_V4_REGEX strictly rejects uppercase hex characters."""
    assert prim.UUID_V4_REGEX.match(sample_uuid_v4.upper()) is None


@pytest.mark.regression
@pytest.mark.parametrize(
    "invalid_uuid",
    [
        "a1b2c3d4-e5f6-1a1b-8c2d-3e4f5a6b7c8d",  # Version 1 instead of 4
        "a1b2c3d4-e5f6-4a1b-0c2d-3e4f5a6b7c8d",  # Invalid RFC variant nibble
    ],
)
def test_uuid_v4_regex_rejects_non_version_4_variant(invalid_uuid: str) -> None:
    """Verify UUID_V4_REGEX rejects UUIDs lacking version 4 or RFC variant bits."""
    assert prim.UUID_V4_REGEX.match(invalid_uuid) is None


@pytest.mark.regression
@pytest.mark.parametrize(
    "invalid_date",
    ["1880-13-01", "1880-00-01", "1880-05-32", "1880-05-00"],
)
def test_iso_date_regex_rejects_out_of_range_calendar_units(invalid_date: str) -> None:
    """Verify ISO_DATE_REGEX rejects month > 12 and day > 31."""
    assert prim.ISO_DATE_REGEX.match(invalid_date) is None


@pytest.mark.regression
@pytest.mark.parametrize(
    "invalid_timestamp",
    ["2026-10-16 08:57:00", "2026-10-16T08:57"],
)
def test_iso_timestamp_regex_rejects_malformed_time_strings(
    invalid_timestamp: str,
) -> None:
    """Verify ISO_TIMESTAMP_REGEX rejects missing timezone or invalid separators."""
    assert prim.ISO_TIMESTAMP_REGEX.match(invalid_timestamp) is None


@pytest.mark.regression
@pytest.mark.parametrize(
    "invalid_hash",
    [
        "B94D27B9934D3E08A52E52D7DA7DABFAC484EFE37A5380EE9088F7ACE2EFCDE9",
        "z" * 64,
        "a" * 63,
        "a" * 65,
    ],
)
def test_sha256_regex_rejects_uppercase_and_non_hex(invalid_hash: str) -> None:
    """Verify SHA256_REGEX rejects uppercase letters, non-hex chars, and wrong lengths."""
    assert prim.SHA256_REGEX.match(invalid_hash) is None


@pytest.mark.regression
@pytest.mark.parametrize(
    "non_strict_val",
    [
        True,
        False,
        1.0,
        -2.0,
        Decimal("10"),
        _SampleStrEnum.ONE,
        "1",
        None,
        [1],
    ],
)
def test_is_strict_int_rejects_explicit_non_int_types(non_strict_val: Any) -> None:
    """Verify is_strict_int rejects bool, float, Decimal, StrEnum, and containers."""
    assert prim.is_strict_int(non_strict_val) is False


@pytest.mark.regression
@given(value=bool_or_non_int())
def test_is_strict_int_rejects_booleans_and_non_integers(value: Any) -> None:
    """Verify is_strict_int rejects booleans, floats, strings, None, and containers (CIU-B1-001)."""
    assert prim.is_strict_int(value) is False


@pytest.mark.regression
@pytest.mark.parametrize(
    "non_finite_val",
    [True, False, float("nan"), float("inf"), float("-inf"), "42", None],
)
def test_is_finite_number_rejects_explicit_booleans_and_non_finite_values(
    non_finite_val: Any,
) -> None:
    """Verify is_finite_number rejects bool, NaN, +/-Inf, strings, and None."""
    assert prim.is_finite_number(non_finite_val) is False


@pytest.mark.regression
@given(
    value=st.one_of(
        st.booleans(),
        non_finite_floats(),
        st.text(max_size=8),
        st.none(),
    )
)
def test_is_finite_number_rejects_booleans_and_non_finite_floats(value: Any) -> None:
    """Verify is_finite_number rejects booleans, NaN, Inf, -Inf, strings, and None (CIU-B1-001)."""
    assert prim.is_finite_number(value) is False


# ==============================================================================
# GROUP 6: Integrity & Invariants
# Note: Authoritative domain scalar bounds, military eras, and census year sets.
# ==============================================================================


@pytest.mark.integrity
@pytest.mark.unit
def test_centralized_domain_bounds_and_code_sets() -> None:
    """Verify canonical gender codes, historical year bounds, coordinate bounds, and scalar limits."""
    assert prim.GENDER_CODES == frozenset({"M", "F", "U"})
    assert (prim.MIN_HISTORICAL_YEAR, prim.MAX_HISTORICAL_YEAR) == (1000, 2100)
    assert (prim.MIN_LATITUDE, prim.MAX_LATITUDE) == (-90.0, 90.0)
    assert (prim.MIN_LONGITUDE, prim.MAX_LONGITUDE) == (-180.0, 180.0)
    assert (prim.MIN_QUAY_SCORE, prim.MAX_QUAY_SCORE) == (0, 3)
    assert prim.MIN_AHNENTAFEL == 1
    assert (prim.MIN_CONFIDENCE_SCORE, prim.MAX_CONFIDENCE_SCORE) == (0.0, 1.0)


@pytest.mark.integrity
@pytest.mark.unit
def test_military_domain_bounds_and_era_year_sets() -> None:
    """Verify centralized military scalar bounds and historical draft era year sets."""
    assert (prim.MIN_ENLISTMENT_TERM_MONTHS, prim.MAX_ENLISTMENT_TERM_MONTHS) == (1, 120)
    assert prim.MAX_FOREIGN_SERVICE_MONTHS == 600
    assert prim.MAX_BOUNTY_LAND_ACREAGE == 1000
    assert prim.MAX_MINOR_CHILDREN_COUNT == 25
    assert (prim.MIN_VIETNAM_LOTTERY_NUMBER, prim.MAX_VIETNAM_LOTTERY_NUMBER) == (1, 366)
    assert (prim.MIN_HEIGHT_INCHES, prim.MAX_HEIGHT_INCHES) == (36, 96)
    assert (prim.MIN_WEIGHT_LBS, prim.MAX_WEIGHT_LBS) == (50, 500)
    assert (prim.COLONIAL_MILITIA_MIN_YEAR, prim.COLONIAL_MILITIA_MAX_YEAR) == (1607, 1815)
    assert prim.CIVIL_WAR_DRAFT_YEARS == frozenset({1862, 1863, 1864, 1865})
    assert prim.WWI_DRAFT_YEARS == frozenset({1917, 1918})
    assert prim.WWII_DRAFT_YEARS == frozenset({1940, 1941, 1942, 1943, 1944, 1945, 1946})
    assert prim.MODERN_SSS_MIN_YEAR == 1948


@pytest.mark.integrity
@pytest.mark.unit
def test_enumerated_schedule_bounds_and_era_year_sets() -> None:
    """Verify centralized census and tax assessment bounds and historical year sets."""
    assert prim.CENSUS_SHEET_SIDES == frozenset({"A", "B"})
    assert prim.MAX_CENSUS_LINE_NUMBER == 200
    assert prim.TAX_ASSESSMENT_MIN_YEAR == 1600
    assert prim.US_FEDERAL_CENSUS_TALLY_YEARS == frozenset({1790, 1800, 1810, 1820, 1830, 1840})
    assert prim.US_FEDERAL_CENSUS_1850_1870_YEARS == frozenset({1850, 1860, 1870})
    assert prim.US_FEDERAL_CENSUS_1900_1910_YEARS == frozenset({1900, 1910})
    assert len(prim.US_FEDERAL_CENSUS_YEARS) == 17
    assert prim.US_MORTALITY_SCHEDULE_YEARS == frozenset({1850, 1860, 1870, 1880, 1885})
    assert prim.US_AGRICULTURAL_SCHEDULE_YEARS == frozenset({1850, 1860, 1870, 1880})
    assert prim.US_MANUFACTURING_SCHEDULE_YEARS == frozenset({1810, 1820, 1850, 1860, 1870, 1880})
    assert prim.US_SLAVE_SCHEDULE_YEARS == frozenset({1850, 1860})
    assert prim.US_VETERANS_SCHEDULE_YEAR == 1890
