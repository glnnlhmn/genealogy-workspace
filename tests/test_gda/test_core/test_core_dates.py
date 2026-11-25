"""Path: tests/test_gda/test_core/test_core_dates.py

Comprehensive unit, regression, and property-based test suite for gda.core.dates.

Operational Role:
    Verifies pure stateless ISO calendar date and timestamp string validation
    predicates, Zulu UTC formatting, date component extraction, and
    chronological age calculation against valid formats, leap-day/century
    boundaries, partial dates, IntEnum years, impossible calendar days, and
    Hypothesis-generated historical date pairs.

Test Structure & Protocol:
    - Atomized & parametrized tests: 1:1 behavioral contract mapping.
    - Fully decorated: 5-marker taxonomy (smoke, unit, regression, integrity).
    - Property-based: Hypothesis strategies imported from test_core/strategies.py.
    - Dependencies: Pure in-memory evaluation with zero disk I/O.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta, timezone
from types import SimpleNamespace
from typing import Any

import pytest
from hypothesis import given
from tests.test_gda.test_core.strategies import historical_date_pairs, iso_date_strings

import gda.core.dates as udate
from gda.core.enums import CensusYearUS
from gda.core.errors import ModelFormatError, ModelRangeError

__version__ = "1.0.0+build.6"


# ==============================================================================
# GROUP 1: Smoke & Primary Entrypoints
# Note: Single smoke contract check verifying gda.core.dates public exports.
# ==============================================================================


@pytest.mark.smoke
@pytest.mark.unit
def test_dates_exposes_expected_public_interface() -> None:
    """Verify gda.core.dates exports all 8 canonical temporal functions."""
    expected_exports = {
        "calculate_age_years",
        "format_utc_timestamp",
        "parse_iso_date_parts",
        "parse_iso_timestamp",
        "utc_now_iso",
        "utc_today_iso",
        "validate_iso_date",
        "validate_iso_timestamp",
    }
    assert set(udate.__all__) == expected_exports


# ==============================================================================
# GROUP 2: Core Logic & Happy Paths
# Note: Valid date/timestamp predicates, UTC formatting, parsing, and ages.
# ==============================================================================


@pytest.mark.unit
@pytest.mark.parametrize(
    "valid_date",
    ["1880", "1880-05", "1880-05-14", "1880-02-29", " 1880-05-14 ", "\t1900-11\n"],
)
def test_validate_iso_date_accepts_valid_and_padded_strings(valid_date: str) -> None:
    """Verify validate_iso_date accepts valid YYYY/YYYY-MM/YYYY-MM-DD strings with whitespace."""
    assert udate.validate_iso_date(valid_date) is True


@pytest.mark.unit
@pytest.mark.parametrize(
    "valid_ts",
    [
        "2026-10-16T08:57:00Z",
        "2026-10-16T08:57:00.123456Z",
        "2026-10-16T08:57:00-04:00",
    ],
)
def test_validate_iso_timestamp_accepts_valid_strings(valid_ts: str) -> None:
    """Verify validate_iso_timestamp returns True for canonical UTC and offset timestamps."""
    assert udate.validate_iso_timestamp(valid_ts) is True


@pytest.mark.unit
def test_format_utc_timestamp_converts_utc_offset_naive_and_default(
    fixed_utc_iso_str: str,
) -> None:
    """Verify format_utc_timestamp produces canonical Zulu strings for all datetime forms."""
    dt_utc = datetime(2026, 11, 10, 15, 30, 0, tzinfo=UTC)
    dt_offset = datetime(2026, 11, 10, 15, 30, 0, tzinfo=timezone(timedelta(hours=-5)))
    dt_naive = datetime(2026, 11, 10, 15, 30, 0)

    assert udate.format_utc_timestamp(dt_utc) == "2026-11-10T15:30:00Z"
    assert udate.format_utc_timestamp(dt_offset) == "2026-11-10T20:30:00Z"
    assert udate.format_utc_timestamp(dt_naive) == "2026-11-10T15:30:00Z"
    assert udate.validate_iso_timestamp(fixed_utc_iso_str) is True

    now_result = udate.format_utc_timestamp()
    assert now_result.endswith("Z")
    assert udate.validate_iso_timestamp(now_result) is True


@pytest.mark.unit
def test_utc_now_iso_and_utc_today_iso_generate_valid_strings() -> None:
    """Verify utc_now_iso and utc_today_iso produce valid canonical ISO-8601 strings."""
    now_str = udate.utc_now_iso()
    today_str = udate.utc_today_iso()

    assert now_str.endswith("Z")
    assert udate.validate_iso_timestamp(now_str) is True
    assert len(today_str) == 10
    assert udate.validate_iso_date(today_str) is True


@pytest.mark.unit
@pytest.mark.parametrize(
    ("raw_date", "expected_parts"),
    [
        ("1880", (1880, None, None)),
        ("1880-05", (1880, 5, None)),
        ("1880-05-14", (1880, 5, 14)),
    ],
)
def test_parse_iso_date_parts_extracts_components(
    raw_date: str,
    expected_parts: tuple[int, int | None, int | None],
) -> None:
    """Verify parse_iso_date_parts extracts integer (year, month, day) components."""
    assert udate.parse_iso_date_parts(raw_date) == expected_parts


@pytest.mark.unit
@pytest.mark.parametrize(
    "raw_ts",
    ["2026-11-10T15:30:00Z", "2026-11-10T10:30:00-05:00"],
)
def test_parse_iso_timestamp_normalizes_to_utc(raw_ts: str) -> None:
    """Verify parse_iso_timestamp normalizes Zulu and offset timestamps into UTC."""
    assert udate.parse_iso_timestamp(raw_ts) == datetime(2026, 11, 10, 15, 30, 0, tzinfo=UTC)


@pytest.mark.unit
@pytest.mark.parametrize(
    ("birth", "target", "expected_age"),
    [
        (1880, 1950, 70),
        (1900, 1900, 0),
        (CensusYearUS.Y1880, CensusYearUS.Y1950, 70),
        (SimpleNamespace(value=1880), SimpleNamespace(value="1950-06-01"), 70),
        ("1880-05-14", "1950-06-20", 70),
        ("1880-05-14", "1950-05-14", 70),
        ("1880-05-14", "1950-04-10", 69),
        ("1880-05-14", "1950-05-13", 69),
    ],
)
def test_calculate_age_years_handles_canonical_inputs(
    birth: Any,
    target: Any,
    expected_age: int,
) -> None:
    """Verify calculate_age_years computes accurate ages for ints, enums, atoms, and ISO dates."""
    assert udate.calculate_age_years(birth, target) == expected_age


# ==============================================================================
# GROUP 3: Edge Cases & Boundary Conditions
# Note: Leap-day birthdays, 1900 century non-leap year, and partial pairs (GAP-CORE-08).
# ==============================================================================


@pytest.mark.regression
@pytest.mark.parametrize(
    ("birth", "target", "expected_age"),
    [
        ("1880-02-29", "1881-02-28", 0),  # Day before non-leap anniversary
        ("1880-02-29", "1881-03-01", 1),  # First day after Feb in non-leap year
        ("1880-02-29", "1884-02-29", 4),  # Exact leap-day anniversary
        ("1880-05", "1950-05", 70),  # Partial YYYY-MM same month
        ("1880-05", "1950-04", 69),  # Partial YYYY-MM prior month
    ],
)
def test_calculate_age_years_leap_day_and_partial_date_boundaries(
    birth: str,
    target: str,
    expected_age: int,
) -> None:
    """Verify leap-day birthdays and partial YYYY-MM date pairs compute accurately (GAP-CORE-08)."""
    assert udate.calculate_age_years(birth, target) == expected_age


@pytest.mark.regression
def test_validate_iso_date_rejects_century_non_leap_year_1900() -> None:
    """Verify 1900-02-29 is rejected as a Gregorian century non-leap year (GAP-CORE-08)."""
    assert udate.validate_iso_date("1900-02-29") is False


# ==============================================================================
# GROUP 4: Error Handling & Validation Failures
# Note: Malformed dates/timestamps, impossible calendar days, and range/type errors.
# ==============================================================================


@pytest.mark.regression
@pytest.mark.parametrize(
    "invalid_date",
    [
        "1880/05/14",
        "May 14, 1880",
        "1880-5-14",
        "80-05-14",
        "1880-13-01",
        "1880-02-30",
        "1881-02-29",
        "1900-04-31",
        None,
        "",
        1880,
    ],
)
def test_validate_iso_date_rejects_invalid_and_impossible_inputs(invalid_date: Any) -> None:
    """Verify validate_iso_date returns False for malformed, impossible, or non-str inputs."""
    assert udate.validate_iso_date(invalid_date) is False


@pytest.mark.regression
@pytest.mark.parametrize(
    "invalid_ts",
    ["2026-10-16 08:57:00", "2026-10-16T08:57", "not-a-timestamp", None, "", " "],
)
def test_validate_iso_timestamp_rejects_malformed_and_empty_inputs(invalid_ts: Any) -> None:
    """Verify validate_iso_timestamp returns False for malformed, empty, or non-str inputs."""
    assert udate.validate_iso_timestamp(invalid_ts) is False


@pytest.mark.regression
def test_validate_iso_timestamp_rejects_impossible_calendar_date() -> None:
    """Verify validate_iso_timestamp rejects impossible Gregorian dates like Feb 30 (GAP-CORE-08)."""
    assert udate.validate_iso_timestamp("2026-02-30T12:00:00Z") is False


@pytest.mark.regression
@pytest.mark.parametrize("bad_date", ["invalid-date", "1880-02-31"])
def test_parse_iso_date_parts_raises_model_format_error(bad_date: str) -> None:
    """Verify parse_iso_date_parts raises ModelFormatError on invalid or impossible dates."""
    with pytest.raises(ModelFormatError) as exc_info:
        udate.parse_iso_date_parts(bad_date)
    assert exc_info.value.error_code == "ERR_MODEL_FORMAT"


@pytest.mark.regression
@pytest.mark.parametrize("bad_ts", ["not-a-timestamp", "2026-02-30T12:00:00Z"])
def test_parse_iso_timestamp_raises_model_format_error(bad_ts: str) -> None:
    """Verify parse_iso_timestamp raises ModelFormatError on malformed or impossible timestamps."""
    with pytest.raises(ModelFormatError) as exc_info:
        udate.parse_iso_timestamp(bad_ts)
    assert exc_info.value.error_code == "ERR_MODEL_FORMAT"


@pytest.mark.regression
def test_calculate_age_years_raises_model_range_error_when_preceding() -> None:
    """Verify calculate_age_years raises ModelRangeError if target precedes birth."""
    with pytest.raises(ModelRangeError) as exc_info:
        udate.calculate_age_years(1950, 1880)
    assert exc_info.value.error_code == "ERR_MODEL_RANGE"


@pytest.mark.regression
@pytest.mark.parametrize(
    ("birth", "target"),
    [
        ("invalid-date", 1950),
        (None, 1950),
        (True, 1950),
        (1880, None),
        (1880, False),
    ],
)
def test_calculate_age_years_raises_model_format_error_on_invalid_types(
    birth: Any,
    target: Any,
) -> None:
    """Verify calculate_age_years raises ModelFormatError for invalid or boolean inputs."""
    with pytest.raises(ModelFormatError) as exc_info:
        udate.calculate_age_years(birth, target)
    assert exc_info.value.error_code == "ERR_MODEL_FORMAT"


# ==============================================================================
# GROUP 6: Integrity & Invariants
# Note: Hypothesis property invariants across historical dates (GAP-CORE-04).
# ==============================================================================


@pytest.mark.integrity
@pytest.mark.unit
@given(date_str=iso_date_strings())
def test_validate_and_parse_iso_date_accept_all_hypothesis_iso_dates(
    date_str: str,
) -> None:
    """Verify validate_iso_date and parse_iso_date_parts accept all generated ISO date strings."""
    assert udate.validate_iso_date(date_str) is True
    year, _month, _day = udate.parse_iso_date_parts(date_str)
    assert 1500 <= year <= 2100


@pytest.mark.integrity
@pytest.mark.regression
@given(pair=historical_date_pairs())
def test_calculate_age_years_matches_gregorian_invariants_property(
    pair: tuple[date, date],
) -> None:
    """Verify calculate_age_years is non-negative and matches exact Gregorian math (GAP-CORE-04)."""
    birth, target = pair
    expected = target.year - birth.year - ((target.month, target.day) < (birth.month, birth.day))
    actual = udate.calculate_age_years(birth.isoformat(), target.isoformat())
    assert actual >= 0
    assert actual == expected
