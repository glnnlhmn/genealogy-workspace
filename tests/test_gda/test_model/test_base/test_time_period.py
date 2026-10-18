"""Path: tests/test_gda/test_model/test_base/test_time_period.py

Comprehensive test suite verifying TimePeriod contracts and boundaries.

Operational Role:
    Verifies that TimePeriod enforces at least one non-null date boundary,
    validates chronological ordering when calendar years are extractable,
    handles asymmetric and non-numeric historical date strings gracefully,
    and guarantees immutability.

Test Structure & Protocol:
    - Atomized tests: 1:1 behavioral contract mapping.
    - Fully decorated: Standard 7-marker taxonomy.
    - Zero production disk I/O.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from gda.core.errors import ModelFormatError, ModelRangeError
from gda.model.atom.date import DateModifier, DateString, EventDate
from gda.model.base.time_period import TimePeriod

__version__ = "1.0.0+build.1"


# ==============================================================================
# GROUP 1: TIMEPERIOD CREATION & FORMATTING
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_time_period_fully_bounded() -> None:
    """Verify TimePeriod instantiates with start and end dates and reports is_bounded."""
    d_start = EventDate(date=DateString("1750"), modifier=DateModifier.EXACT)
    d_end = EventDate(date=DateString("1820"), modifier=DateModifier.EXACT)

    period = TimePeriod(start_date=d_start, end_date=d_end)
    assert period.start_date == d_start
    assert period.end_date == d_end
    assert period.is_bounded is True
    assert str(period) == "1750 - 1820"
    assert repr(period) == (
        "TimePeriod(start_date=EventDate(date=DateString(value='1750'), modifier=EXACT), "
        "end_date=EventDate(date=DateString(value='1820'), modifier=EXACT))"
    )


@pytest.mark.unit
@pytest.mark.smoke
def test_time_period_start_date_only() -> None:
    """Verify TimePeriod instantiates with start_date only and formats correctly."""
    d_start = EventDate(date=DateString("1850"), modifier=DateModifier.ABOUT)

    period = TimePeriod(start_date=d_start)
    assert period.start_date == d_start
    assert period.end_date is None
    assert period.is_bounded is False
    assert str(period) == "from ABT 1850"


@pytest.mark.unit
@pytest.mark.smoke
def test_time_period_end_date_only() -> None:
    """Verify TimePeriod instantiates with end_date only and formats correctly."""
    d_end = EventDate(date=DateString("1910"), modifier=DateModifier.BEFORE)

    period = TimePeriod(end_date=d_end)
    assert period.start_date is None
    assert period.end_date == d_end
    assert period.is_bounded is False
    assert str(period) == "until BEF 1910"


# ==============================================================================
# GROUP 2: DEFENSIVE BOUNDARIES & TEMPORAL VALIDATION
# ==============================================================================


@pytest.mark.unit
@pytest.mark.regression
def test_time_period_both_none_raises_error() -> None:
    """Verify TimePeriod raises ModelFormatError if both boundaries are None."""
    with pytest.raises(
        ModelFormatError, match="must define at least one boundary date"
    ):
        TimePeriod(start_date=None, end_date=None)


@pytest.mark.unit
@pytest.mark.regression
def test_time_period_inverted_years_raises_range_error() -> None:
    """Verify TimePeriod raises ModelRangeError if conclusion precedes inception year."""
    d_start = EventDate(date=DateString("1890"), modifier=DateModifier.EXACT)
    d_end = EventDate(date=DateString("1850"), modifier=DateModifier.EXACT)

    with pytest.raises(
        ModelRangeError, match="Conclusion year .* cannot precede inception year"
    ):
        TimePeriod(start_date=d_start, end_date=d_end)


@pytest.mark.unit
@pytest.mark.smoke
def test_time_period_equal_years_valid() -> None:
    """Verify TimePeriod allows inception and conclusion within the identical calendar year."""
    d_start = EventDate(date=DateString("1880"), modifier=DateModifier.EXACT)
    d_end = EventDate(date=DateString("1880"), modifier=DateModifier.EXACT)

    period = TimePeriod(start_date=d_start, end_date=d_end)
    assert period.start_date == d_start
    assert period.end_date == d_end


@pytest.mark.unit
@pytest.mark.regression
def test_time_period_both_non_numeric_dates_pass() -> None:
    """Verify TimePeriod passes validation when neither date contains a 4-digit year."""
    d_start = EventDate(
        date=DateString("Colonial Settlement"), modifier=DateModifier.ABOUT
    )
    d_end = EventDate(date=DateString("Antebellum Era"), modifier=DateModifier.ABOUT)

    period = TimePeriod(start_date=d_start, end_date=d_end)
    assert period.start_date == d_start
    assert period.end_date == d_end


@pytest.mark.unit
@pytest.mark.regression
def test_time_period_start_numeric_end_non_numeric_passes() -> None:
    """Verify TimePeriod passes when start date has a year but end date has no 4-digit match."""
    d_start = EventDate(date=DateString("1800"), modifier=DateModifier.EXACT)
    d_end = EventDate(date=DateString("Late Colonial Era"), modifier=DateModifier.ABOUT)

    period = TimePeriod(start_date=d_start, end_date=d_end)
    assert period.start_date == d_start
    assert period.end_date == d_end


@pytest.mark.unit
@pytest.mark.regression
def test_time_period_start_non_numeric_end_numeric_passes() -> None:
    """Verify TimePeriod passes when start date has no year but end date has a 4-digit match."""
    d_start = EventDate(date=DateString("Early Spring"), modifier=DateModifier.ABOUT)
    d_end = EventDate(date=DateString("1850"), modifier=DateModifier.EXACT)

    period = TimePeriod(start_date=d_start, end_date=d_end)
    assert period.start_date == d_start
    assert period.end_date == d_end


# ==============================================================================
# GROUP 3: IMMUTABILITY & INTROSPECTION
# ==============================================================================


@pytest.mark.unit
def test_time_period_immutability() -> None:
    """Verify TimePeriod is frozen and immutable."""
    d_start = EventDate(date=DateString("1800"), modifier=DateModifier.EXACT)
    period = TimePeriod(start_date=d_start)

    with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
        period.start_date = EventDate(
            date=DateString("1850"), modifier=DateModifier.EXACT
        )  # type: ignore[misc]


@pytest.mark.unit
def test_time_period_introspection() -> None:
    """Verify .help() renders public member directory on TimePeriod."""
    d_start = EventDate(date=DateString("1800"), modifier=DateModifier.EXACT)
    period = TimePeriod(start_date=d_start)

    help_text = period.help(as_str=True)
    assert help_text is not None
    assert "=== TimePeriod Public Directory ===" in help_text
    assert "is_bounded" in help_text
