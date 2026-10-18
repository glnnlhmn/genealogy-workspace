"""Path: tests/test_gda/test_model/test_base/test_age.py

Comprehensive test suite verifying Age formatting and boundaries.

Operational Role:
    Verifies that Age parses discrete years, months, and days,
    preserves verbatim text, validates boundary constraints, formats cleanly,
    and enforces immutability.

Test Structure & Protocol:
    - Atomized tests: 1:1 behavioral contract mapping.
    - Fully decorated: Standard 7-marker taxonomy.
    - Zero production disk I/O.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from gda.core.errors import ModelFormatError
from gda.model.base.age import Age

__version__ = "1.0.0+build.3"


# ==============================================================================
# GROUP 1: AGE CREATION & FORMATTING
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_age_full_numeric_units() -> None:
    """Verify Age with years, months, and days formats correctly."""
    age = Age(years=72, months=4, days=12, raw_text="72y 4m 12d")
    assert age.years == 72
    assert age.months == 4
    assert age.days == 12
    assert age.raw_text == "72y 4m 12d"
    assert age.formatted_age == "72y 4m 12d"
    assert str(age) == "72y 4m 12d"
    assert repr(age) == "Age(raw_text='72y 4m 12d', years=72, months=4, days=12)"


@pytest.mark.unit
@pytest.mark.smoke
def test_age_years_only() -> None:
    """Verify Age formats correctly with only years defined."""
    age = Age(years=45)
    assert age.formatted_age == "45y"
    assert str(age) == "45y"


@pytest.mark.unit
@pytest.mark.smoke
def test_age_raw_text_only() -> None:
    """Verify Age falls back to raw_text when numeric parts are None."""
    age = Age(raw_text="about 30 years")
    assert age.formatted_age == "about 30 years"
    assert str(age) == "about 30 years"


# ==============================================================================
# GROUP 2: DEFENSIVE BOUNDARIES & INVALID ATTRIBUTES
# ==============================================================================


@pytest.mark.unit
@pytest.mark.regression
def test_age_empty_raises_error() -> None:
    """Verify Age raises ModelFormatError when completely unpopulated."""
    with pytest.raises(
        ModelFormatError, match="must specify raw_text or at least one of"
    ):
        Age()


@pytest.mark.unit
@pytest.mark.regression
def test_age_negative_years_raises_error() -> None:
    """Verify Age raises ModelFormatError on negative years."""
    with pytest.raises(ModelFormatError, match="cannot be negative"):
        Age(years=-1)


@pytest.mark.unit
@pytest.mark.regression
@pytest.mark.parametrize("bad_month", [-1, 12, 100])
def test_age_invalid_months_raises_error(bad_month: int) -> None:
    """Verify Age raises ModelFormatError when months outside 0..11."""
    with pytest.raises(ModelFormatError, match="must be between 0 and 11"):
        Age(months=bad_month)


@pytest.mark.unit
@pytest.mark.regression
@pytest.mark.parametrize("bad_day", [-1, 32, 100])
def test_age_invalid_days_raises_error(bad_day: int) -> None:
    """Verify Age raises ModelFormatError when days outside 0..31."""
    with pytest.raises(ModelFormatError, match="must be between 0 and 31"):
        Age(days=bad_day)


@pytest.mark.unit
def test_age_immutability() -> None:
    """Verify Age is frozen and immutable."""
    age = Age(years=50)
    with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
        age.years = 51  # type: ignore[misc]


@pytest.mark.unit
def test_age_introspection() -> None:
    """Verify .help() renders on Age."""
    age = Age(years=50)
    help_text = age.help(as_str=True)
    assert help_text is not None
    assert "=== Age Public Directory ===" in help_text
    assert "formatted_age" in help_text
