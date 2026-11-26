"""Path: tests/test_gda/test_core/test_core_types_regexes.py

Unit, regression, and property-based tests for regex patterns and registries in gda.core.types.

Operational Role:
    Verifies ISO format directives, UUIDv4, ISO date/timestamp, SHA-256,
    SQL identifier, enum key separator, atom/publication/news regexes, entity
    ID/URN patterns, all 14 archival URN namespaces, and MappingProxyType
    immutability across exported regex registries.

Test Structure & Protocol:
    - Atomized & parametrized tests: 1:1 behavioral contract mapping.
    - Fully decorated: 5-marker taxonomy (smoke, unit, regression, integrity).
    - Property-based: Hypothesis strategies imported from test_core/strategies.py.
    - Dependencies: Pure in-memory evaluation with zero disk I/O.
"""

from __future__ import annotations

import re
from types import MappingProxyType
from typing import Any

import pytest
from hypothesis import given
from tests.test_gda.test_core.strategies import iso_date_strings, utc_timestamps

import gda.core.types as prim

__version__ = "1.0.0+build.1"

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
# Note: Verifies gda.core.types exposes canonical regexes and registries.
# ==============================================================================


@pytest.mark.smoke
@pytest.mark.unit
def test_types_regexes_exposes_expected_public_interface() -> None:
    """Verify gda.core.types exports canonical patterns and regex registries."""
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


# ==============================================================================
# GROUP 3: Edge Cases & Boundary Conditions
# Note: Strict digit-width boundaries and all 14 archival URN namespaces.
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
    """Verify URN_PATTERNS and URN_REGEXES declare all 14 archival URN namespaces."""
    assert set(prim.URN_PATTERNS.keys()) == ALL_14_URN_NAMESPACES
    assert set(prim.URN_REGEXES.keys()) == ALL_14_URN_NAMESPACES


@pytest.mark.unit
@pytest.mark.parametrize(("namespace", "valid_urn", "_invalid_urn"), URN_NAMESPACE_CASES)
def test_urn_regexes_accept_valid_samples_across_all_14_namespaces(
    namespace: str,
    valid_urn: str,
    _invalid_urn: str,
) -> None:
    """Verify each of the 14 URN_REGEXES entries matches its valid sample URN."""
    assert prim.URN_REGEXES[namespace].match(valid_urn) is not None


@pytest.mark.regression
@pytest.mark.parametrize(("namespace", "_valid_urn", "invalid_urn"), URN_NAMESPACE_CASES)
def test_urn_regexes_reject_malformed_samples_across_all_14_namespaces(
    namespace: str,
    _valid_urn: str,
    invalid_urn: str,
) -> None:
    """Verify each of the 14 URN_REGEXES entries rejects malformed URNs."""
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
# Note: Invalid regex formats against UUID, date, timestamp, and SHA-256 regexes.
# ==============================================================================


@pytest.mark.regression
def test_uuid_v4_regex_rejects_uppercase_letters(sample_uuid_v4: str) -> None:
    """Verify UUID_V4_REGEX strictly rejects uppercase hex characters."""
    assert prim.UUID_V4_REGEX.match(sample_uuid_v4.upper()) is None


@pytest.mark.regression
@pytest.mark.parametrize(
    "invalid_uuid",
    [
        "a1b2c3d4-e5f6-1a1b-8c2d-3e4f5a6b7c8d",
        "a1b2c3d4-e5f6-4a1b-0c2d-3e4f5a6b7c8d",
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


# ==============================================================================
# GROUP 6: Integrity & Invariants
# Note: Read-only MappingProxyType enforcement across all 6 regex registries.
# ==============================================================================


@pytest.mark.integrity
@pytest.mark.unit
@pytest.mark.parametrize(
    "registry_name",
    [
        "ENTITY_ID_PATTERNS",
        "ENTITY_ID_REGEXES",
        "ENTITY_URN_PATTERNS",
        "ENTITY_URN_REGEXES",
        "URN_PATTERNS",
        "URN_REGEXES",
    ],
)
def test_exported_regex_registries_are_immutable_mapping_proxies(
    registry_name: str,
) -> None:
    """Verify all 6 exported regex registries are MappingProxyType and reject mutation."""
    registry: Any = getattr(prim, registry_name)
    assert isinstance(registry, MappingProxyType)
    with pytest.raises(TypeError):
        registry["__MUTATION_TEST__"] = "invalid"  # type: ignore[index]
