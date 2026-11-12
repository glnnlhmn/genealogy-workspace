"""Path: tests/test_gda/test_core/test_dates.py

Comprehensive unit test suite for gda.core.dates.

Operational Role:
    Verifies pure stateless ISO calendar date and timestamp string validation
    predicates, Zulu UTC formatting, date component extraction, and age calculation
    against valid formats, boundary errors, and non-string inputs with 100% statement
    and branch coverage.

Test Structure & Protocol:
    - Atomized tests: 1:1 behavioral contract mapping.
    - Fully decorated: Strictly unit and regression markers.
    - Dependencies: In-memory evaluation with zero disk I/O.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

import gda.core.dates as udate
from gda.core.errors import ModelFormatError, ModelRangeError

__version__ = "1.0.0+build.4"

# ==============================================================================
# GROUP 1: Calendar Date Validation Predicates (validate_iso_date)
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_validate_iso_date_accepts_valid_calendar_strings() -> None:
    """Verify validate_iso_date returns True for valid YYYY, YYYY-MM, and YYYY-MM-DD formats."""
    assert udate.validate_iso_date("1880") is True
    assert udate.validate_iso_date("1880-05") is True
    assert udate.validate_iso_date("1880-05-14") is True


@pytest.mark.unit
def test_validate_iso_date_accepts_valid_strings_with_surrounding_whitespace() -> None:
    """Verify validate_iso_date trims surrounding whitespace prior to matching."""
    assert udate.validate_iso_date("  1880-05-14  ") is True
    assert udate.validate_iso_date("\t1900-11\n") is True


@pytest.mark.regression
def test_validate_iso_date_rejects_invalid_date_syntax() -> None:
    """Verify validate_iso_date returns False for malformed calendar dates."""
    assert udate.validate_iso_date("1880/05/14") is False
    assert udate.validate_iso_date("May 14, 1880") is False
    assert udate.validate_iso_date("1880-5-14") is False
    assert udate.validate_iso_date("80-05-14") is False
    assert udate.validate_iso_date("1880-13-01") is False


@pytest.mark.regression
def test_validate_iso_date_rejects_none_and_non_string_inputs() -> None:
    """Verify validate_iso_date returns False when passed None, empty strings, or non-strings."""
    assert udate.validate_iso_date(None) is False
    assert udate.validate_iso_date("") is False
    assert udate.validate_iso_date(1880) is False  # type: ignore[arg-type]


# ==============================================================================
# GROUP 2: Timestamp Validation Predicates (validate_iso_timestamp)
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_validate_iso_timestamp_accepts_valid_timestamp_strings() -> None:
    """Verify validate_iso_timestamp returns True for canonical UTC and offset timestamps."""
    assert udate.validate_iso_timestamp("2026-10-16T08:57:00Z") is True
    assert udate.validate_iso_timestamp("2026-10-16T08:57:00.123456Z") is True
    assert udate.validate_iso_timestamp("2026-10-16T08:57:00-04:00") is True


@pytest.mark.regression
def test_validate_iso_timestamp_rejects_invalid_timestamp_syntax() -> None:
    """Verify validate_iso_timestamp returns False for malformed or non-ISO timestamp strings."""
    assert udate.validate_iso_timestamp("2026-10-16 08:57:00") is False
    assert udate.validate_iso_timestamp("2026-10-16T08:57") is False
    assert udate.validate_iso_timestamp("not-a-timestamp") is False


@pytest.mark.regression
def test_validate_iso_timestamp_rejects_none_and_empty_inputs() -> None:
    """Verify validate_iso_timestamp returns False for None and empty string inputs."""
    assert udate.validate_iso_timestamp(None) is False
    assert udate.validate_iso_timestamp("") is False
    assert udate.validate_iso_timestamp("   ") is False


# ==============================================================================
# GROUP 3: UTC Timestamp Formatting & Current Generators
# ==============================================================================


@pytest.mark.unit
def test_format_utc_timestamp_default_and_explicit() -> None:
    """Verify format_utc_timestamp produces valid canonical Zulu format."""
    dt_utc = datetime(2026, 11, 10, 15, 30, 0, tzinfo=UTC)
    assert udate.format_utc_timestamp(dt_utc) == "2026-11-10T15:30:00Z"

    dt_offset = datetime(2026, 11, 10, 15, 30, 0, tzinfo=timezone(timedelta(hours=-5)))
    assert udate.format_utc_timestamp(dt_offset) == "2026-11-10T20:30:00Z"

    dt_naive = datetime(2026, 11, 10, 15, 30, 0)
    assert udate.format_utc_timestamp(dt_naive) == "2026-11-10T15:30:00Z"

    result = udate.format_utc_timestamp()
    assert result.endswith("Z")
    assert udate.validate_iso_timestamp(result) is True


@pytest.mark.unit
def test_utc_now_iso_generates_valid_timestamp() -> None:
    """Verify utc_now_iso generates a valid current Zulu timestamp."""
    result = udate.utc_now_iso()
    assert result.endswith("Z")
    assert udate.validate_iso_timestamp(result) is True


@pytest.mark.unit
def test_utc_today_iso_generates_valid_calendar_date() -> None:
    """Verify utc_today_iso generates a valid YYYY-MM-DD date matching validate_iso_date."""
    result = udate.utc_today_iso()
    assert len(result) == 10
    assert result[4] == "-" and result[7] == "-"
    assert udate.validate_iso_date(result) is True


# ==============================================================================
# GROUP 4: Date and Timestamp Parsing & Component Extraction
# ==============================================================================


@pytest.mark.unit
def test_parse_iso_date_parts_extracts_components() -> None:
    """Verify parse_iso_date_parts extracts integer year, month, and day components."""
    assert udate.parse_iso_date_parts("1880") == (1880, None, None)
    assert udate.parse_iso_date_parts("1880-05") == (1880, 5, None)
    assert udate.parse_iso_date_parts("1880-05-14") == (1880, 5, 14)


@pytest.mark.regression
def test_parse_iso_date_parts_raises_model_format_error_on_invalid() -> None:
    """Verify parse_iso_date_parts raises ModelFormatError on invalid date format."""
    with pytest.raises(ModelFormatError) as exc_info:
        udate.parse_iso_date_parts("invalid-date")
    assert exc_info.value.error_code == "ERR_MODEL_FORMAT"


@pytest.mark.unit
def test_parse_iso_timestamp_valid() -> None:
    """Verify parse_iso_timestamp successfully parses UTC and offset ISO strings."""
    parsed_z = udate.parse_iso_timestamp("2026-11-10T15:30:00Z")
    assert parsed_z == datetime(2026, 11, 10, 15, 30, 0, tzinfo=UTC)

    parsed_offset = udate.parse_iso_timestamp("2026-11-10T10:30:00-05:00")
    assert parsed_offset == datetime(2026, 11, 10, 15, 30, 0, tzinfo=UTC)


@pytest.mark.regression
def test_parse_iso_timestamp_invalid_raises_model_format_error() -> None:
    """Verify parse_iso_timestamp raises ModelFormatError on malformed timestamp."""
    with pytest.raises(ModelFormatError) as exc_info:
        udate.parse_iso_timestamp("not-a-timestamp")
    assert exc_info.value.error_code == "ERR_MODEL_FORMAT"


# ==============================================================================
# GROUP 5: Chronological Age Calculations (calculate_age_years)
# ==============================================================================


@pytest.mark.unit
def test_calculate_age_years_integer_and_atom_value_objects() -> None:
    """Verify calculate_age_years computes differences for ints and .value atom objects."""
    assert udate.calculate_age_years(1880, 1950) == 70
    assert udate.calculate_age_years(1900, 1900) == 0
    assert (
        udate.calculate_age_years(SimpleNamespace(value=1880), SimpleNamespace(value="1950-06-01"))
        == 70
    )  # type: ignore[arg-type]


@pytest.mark.unit
def test_calculate_age_years_full_iso_dates_anniversary_passed() -> None:
    """Verify calculate_age_years accounts for passed birthday anniversaries."""
    assert udate.calculate_age_years("1880-05-14", "1950-06-20") == 70
    assert udate.calculate_age_years("1880-05-14", "1950-05-14") == 70


@pytest.mark.unit
def test_calculate_age_years_full_iso_dates_anniversary_not_passed() -> None:
    """Verify calculate_age_years subtracts a year if birthday anniversary has not passed."""
    assert udate.calculate_age_years("1880-05-14", "1950-04-10") == 69
    assert udate.calculate_age_years("1880-05-14", "1950-05-13") == 69


@pytest.mark.regression
def test_calculate_age_years_raises_model_range_error_when_preceding() -> None:
    """Verify calculate_age_years raises ModelRangeError if target precedes birth."""
    with pytest.raises(ModelRangeError) as exc_info:
        udate.calculate_age_years(1950, 1880)
    assert exc_info.value.error_code == "ERR_MODEL_RANGE"


@pytest.mark.regression
def test_calculate_age_years_raises_model_format_error_on_invalid_types() -> None:
    """Verify calculate_age_years raises ModelFormatError for invalid birth or target types."""
    with pytest.raises(ModelFormatError) as exc_info:
        udate.calculate_age_years("invalid-date", 1950)
    assert exc_info.value.error_code == "ERR_MODEL_FORMAT"

    with pytest.raises(ModelFormatError, match="Unsupported birth date type") as exc_info2:
        udate.calculate_age_years(None, 1950)  # type: ignore[arg-type]
    assert exc_info2.value.error_code == "ERR_MODEL_FORMAT"

    with pytest.raises(ModelFormatError, match="Unsupported target date type") as exc_info3:
        udate.calculate_age_years(1880, None)  # type: ignore[arg-type]
    assert exc_info3.value.error_code == "ERR_MODEL_FORMAT"
