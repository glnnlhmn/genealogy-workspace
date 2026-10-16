# Name: test_dates.py
# Path: tests/test_gda/test_util/test_dates.py

"""Comprehensive unit test suite for gda.util.dates.

Operational Role:
    Verifies pure stateless ISO calendar date and timestamp string validation
    predicates against valid formats, malformed strings, whitespace, and non-string inputs.

Test Structure & Protocol:
    - Atomized tests: 1:1 behavioral contract mapping.
    - Fully decorated: Decorated with @pytest.mark.unit and @pytest.mark.smoke.
    - Dependencies: In-memory evaluation with zero disk I/O.

Note:
    PRERELEASE: Test suite is under active development (version 0.0.1+build.1).
"""

from __future__ import annotations

import pytest

import gda.util.dates as udate

__version__ = "0.0.1+build.1"

# ==============================================================================
# GROUP 1: Calendar Date Validation Predicates (is_iso_date)
# Note: Verification of YYYY, YYYY-MM, and YYYY-MM-DD syntax
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_is_iso_date_accepts_valid_calendar_strings() -> None:
    """Verify is_iso_date returns True for valid YYYY, YYYY-MM, and YYYY-MM-DD formats."""
    assert udate.is_iso_date("1880") is True
    assert udate.is_iso_date("1880-05") is True
    assert udate.is_iso_date("1880-05-14") is True


@pytest.mark.unit
def test_is_iso_date_accepts_valid_strings_with_surrounding_whitespace() -> None:
    """Verify is_iso_date trims surrounding whitespace prior to matching."""
    assert udate.is_iso_date("  1880-05-14  ") is True
    assert udate.is_iso_date("\t1900-11\n") is True


@pytest.mark.unit
def test_is_iso_date_rejects_invalid_date_syntax() -> None:
    """Verify is_iso_date returns False for malformed calendar dates."""
    assert udate.is_iso_date("1880/05/14") is False
    assert udate.is_iso_date("May 14, 1880") is False
    assert udate.is_iso_date("1880-5-14") is False
    assert udate.is_iso_date("80-05-14") is False
    assert udate.is_iso_date("1880-13-01") is False


@pytest.mark.unit
def test_is_iso_date_rejects_none_and_non_string_inputs() -> None:
    """Verify is_iso_date returns False when passed None, empty strings, or non-strings."""
    assert udate.is_iso_date(None) is False
    assert udate.is_iso_date("") is False
    assert udate.is_iso_date(1880) is False  # type: ignore[arg-type]


# ==============================================================================
# GROUP 2: Timestamp Validation Predicates (is_iso_timestamp)
# Note: Verification of ISO extended timestamps with UTC and timezone offsets
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_is_iso_timestamp_accepts_valid_timestamp_strings() -> None:
    """Verify is_iso_timestamp returns True for canonical UTC and offset timestamps."""
    assert udate.is_iso_timestamp("2026-10-16T08:57:00Z") is True
    assert udate.is_iso_timestamp("2026-10-16T08:57:00.123456Z") is True
    assert udate.is_iso_timestamp("2026-10-16T08:57:00-04:00") is True


@pytest.mark.unit
def test_is_iso_timestamp_rejects_invalid_timestamp_syntax() -> None:
    """Verify is_iso_timestamp returns False for malformed or non-ISO timestamp strings."""
    assert udate.is_iso_timestamp("2026-10-16 08:57:00") is False
    assert udate.is_iso_timestamp("2026-10-16T08:57") is False
    assert udate.is_iso_timestamp("not-a-timestamp") is False


@pytest.mark.unit
def test_is_iso_timestamp_rejects_none_and_empty_inputs() -> None:
    """Verify is_iso_timestamp returns False for None and empty string inputs."""
    assert udate.is_iso_timestamp(None) is False
    assert udate.is_iso_timestamp("") is False
    assert udate.is_iso_timestamp("   ") is False
