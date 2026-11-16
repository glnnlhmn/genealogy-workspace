"""Path: tests/test_gda/test_core/test_core_types.py

Comprehensive unit test suite for gda.core.types.

Operational Role:
    Verifies declarative regex patterns, compiled regular expressions, ISO
    format directives, entity URN patterns, archival URN patterns, and domain
    scalar invariants against canonical examples and invalid boundary strings.

Test Structure & Protocol:
    - Atomized tests: 1:1 behavioral contract mapping.
    - Fully decorated: Strictly unit and regression markers.
    - Dependencies: In-memory evaluation with zero disk I/O.
"""

from __future__ import annotations

import re

import pytest

import gda.core.types as prim

__version__ = "1.0.0+build.4"


# ==============================================================================
# GROUP 1: ISO FORMAT CONSTANTS
# ==============================================================================


@pytest.mark.unit
def test_iso_format_constants_match_expected_directives() -> None:
    """Verify that ISO format string tokens declare standard strftime directives."""
    assert prim.ISO_YEAR_FMT == "%Y"
    assert prim.ISO_MONTH_FMT == "%Y-%m"
    assert prim.ISO_DATE_FMT == "%Y-%m-%d"
    assert prim.ISO_TIMESTAMP_FMT == "%Y-%m-%dT%H:%M:%SZ"


# ==============================================================================
# GROUP 2: UUID V4 PATTERN CONTRACTS
# ==============================================================================


@pytest.mark.unit
def test_uuid_v4_regex_accepts_valid_lowercase_uuid() -> None:
    """Verify UUID_V4_REGEX matches valid canonical lowercase RFC 4122 UUIDv4 strings."""
    valid_uuid = "a1b2c3d4-e5f6-4a1b-8c2d-3e4f5a6b7c8d"
    assert prim.UUID_V4_REGEX.match(valid_uuid) is not None


@pytest.mark.regression
def test_uuid_v4_regex_rejects_uppercase_letters() -> None:
    """Verify UUID_V4_REGEX strictly rejects uppercase hex characters."""
    upper_uuid = "A1B2C3D4-E5F6-4A1B-8C2D-3E4F5A6B7C8D"
    assert prim.UUID_V4_REGEX.match(upper_uuid) is None


@pytest.mark.regression
def test_uuid_v4_regex_rejects_non_version_4_variant() -> None:
    """Verify UUID_V4_REGEX rejects UUIDs lacking version 4 or RFC variant bits."""
    v1_uuid = "a1b2c3d4-e5f6-1a1b-8c2d-3e4f5a6b7c8d"
    assert prim.UUID_V4_REGEX.match(v1_uuid) is None
    bad_variant_uuid = "a1b2c3d4-e5f6-4a1b-0c2d-3e4f5a6b7c8d"
    assert prim.UUID_V4_REGEX.match(bad_variant_uuid) is None


# ==============================================================================
# GROUP 3: ISO DATE & TIMESTAMP CONTRACTS
# ==============================================================================


@pytest.mark.unit
def test_iso_date_regex_matches_valid_year_month_day() -> None:
    """Verify ISO_DATE_REGEX matches year-only, year-month, and full date strings."""
    assert prim.ISO_DATE_REGEX.match("1880") is not None
    assert prim.ISO_DATE_REGEX.match("1880-05") is not None
    assert prim.ISO_DATE_REGEX.match("1880-05-14") is not None


@pytest.mark.regression
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


@pytest.mark.regression
def test_iso_timestamp_regex_rejects_malformed_time_strings() -> None:
    """Verify ISO_TIMESTAMP_REGEX rejects missing timezone or invalid separators."""
    assert prim.ISO_TIMESTAMP_REGEX.match("2026-10-16 08:57:00") is None
    assert prim.ISO_TIMESTAMP_REGEX.match("2026-10-16T08:57") is None


# ==============================================================================
# GROUP 4: ENTITY IDENTIFIER & ENTITY URN PATTERN CONTRACTS
# ==============================================================================


@pytest.mark.unit
def test_entity_id_patterns_cover_all_canonical_prefixes() -> None:
    """Verify ENTITY_ID_PATTERNS and ENTITY_ID_REGEXES cover all 9 canonical prefixes."""
    expected_prefixes = {"IND", "FID", "LOC", "SID", "FAM", "NOT", "REP", "DRF", "ORG"}
    assert set(prim.ENTITY_ID_PATTERNS.keys()) == expected_prefixes
    assert set(prim.ENTITY_ID_REGEXES.keys()) == expected_prefixes


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
def test_entity_urn_patterns_cover_all_master_entities() -> None:
    """Verify ENTITY_URN_PATTERNS and ENTITY_URN_REGEXES cover all 6 master entity prefixes."""
    expected_entity_prefixes = {"IND", "FAM", "FID", "LOC", "ORG", "SID"}
    assert set(prim.ENTITY_URN_PATTERNS.keys()) == expected_entity_prefixes
    assert set(prim.ENTITY_URN_REGEXES.keys()) == expected_entity_prefixes

    samples = {
        "IND": "urn:gda:ind:smith_john_1842",
        "FAM": "urn:gda:fam:smith_jones_1865",
        "FID": "urn:gda:fact:birth_1842_01",
        "LOC": "urn:gda:loc:us:nh:merrimack:concord",
        "ORG": "urn:gda:org:us:nh:concord:vfw_post_411",
        "SID": "urn:gda:site:us:nh:concord:blossom_hill",
    }
    for prefix, valid_urn in samples.items():
        assert prim.ENTITY_URN_REGEXES[prefix].match(valid_urn) is not None
        assert prim.ENTITY_URN_REGEXES[prefix].match(valid_urn.upper()) is None


# ==============================================================================
# GROUP 5: SHA-256 HASH PATTERN CONTRACTS
# ==============================================================================


@pytest.mark.unit
def test_sha256_regex_accepts_valid_lowercase_digest() -> None:
    """Verify SHA256_REGEX matches valid 64-character lowercase hex strings."""
    valid_hash = "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
    assert prim.SHA256_REGEX.match(valid_hash) is not None


@pytest.mark.regression
def test_sha256_regex_rejects_uppercase_and_non_hex() -> None:
    """Verify SHA256_REGEX rejects uppercase letters and non-hex characters."""
    upper_hash = "B94D27B9934D3E08A52E52D7DA7DABFAC484EFE37A5380EE9088F7ACE2EFCDE9"
    assert prim.SHA256_REGEX.match(upper_hash) is None
    assert prim.SHA256_REGEX.match("z" * 64) is None
    assert prim.SHA256_REGEX.match("a" * 63) is None
    assert prim.SHA256_REGEX.match("a" * 65) is None


# ==============================================================================
# GROUP 6: CENTRALIZED DOMAIN SCALAR INVARIANTS & URN REGEXES
# ==============================================================================


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


@pytest.mark.unit
def test_centralized_urn_and_scalar_regexes() -> None:
    """Verify ATOM_ID_REGEX, PUB_CODE_REGEX, NEWS_CATEGORY_REGEX, and all 14 URN_REGEXES."""
    assert prim.ATOM_ID_REGEX.match("IND-000001") is not None
    assert prim.ATOM_ID_REGEX.match("IND-0000001") is None
    assert prim.PUB_CODE_REGEX.match("US_CENSUS") is not None
    assert prim.NEWS_CATEGORY_REGEX.match("OBIT") is not None
    expected_nids = {
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
    assert set(prim.URN_REGEXES.keys()) == expected_nids
    assert prim.URN_REGEXES["SRC"].match("URN:SRC:1917:NH_MERRIMACK:DOC_001") is not None
    assert prim.URN_REGEXES["LAND"].match("URN:LAND:1850:NH_MERRIMACK:DEED_12") is not None
    assert prim.URN_REGEXES["WILL"].match("URN:WILL:1880:NH_MERRIMACK:PROB_04") is not None
