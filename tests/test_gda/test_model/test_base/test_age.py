# Name: test_age.py
# Path: tests/test_gda/test_model/test_base/test_age.py

"""Comprehensive test suite verifying AgeRecordModel formatting and boundaries.

Operational Role:
    Verifies that AgeRecordModel parses discrete years, months, and days,
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

from gda.model.atom.errors import AtomFormatError
from gda.model.base.age import AgeRecordModel

__version__ = "1.0.0+build.r2"


# ==============================================================================
# GROUP 1: AGERECORDMODEL CREATION & FORMATTING
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_age_record_full_numeric_units() -> None:
    """Verify AgeRecordModel with years, months, and days formats correctly."""
    age = AgeRecordModel(years=72, months=4, days=12, raw_text="72y 4m 12d")
    assert age.years == 72
    assert age.months == 4
    assert age.days == 12
    assert age.raw_text == "72y 4m 12d"
    assert age.formatted_age == "72y 4m 12d"
    assert str(age) == "72y 4m 12d"
    assert (
        repr(age)
        == "AgeRecordModel(raw_text='72y 4m 12d', years=72, months=4, days=12)"
    )


@pytest.mark.unit
@pytest.mark.smoke
def test_age_record_years_only() -> None:
    """Verify AgeRecordModel formats correctly with only years defined."""
    age = AgeRecordModel(years=45)
    assert age.formatted_age == "45y"
    assert str(age) == "45y"


@pytest.mark.unit
@pytest.mark.smoke
def test_age_record_raw_text_only() -> None:
    """Verify AgeRecordModel falls back to raw_text when numeric parts are None."""
    age = AgeRecordModel(raw_text="about 30 years")
    assert age.formatted_age == "about 30 years"
    assert str(age) == "about 30 years"


# ==============================================================================
# GROUP 2: DEFENSIVE BOUNDARIES & INVALID ATTRIBUTES
# ==============================================================================


@pytest.mark.unit
@pytest.mark.regression
def test_age_record_empty_raises_error() -> None:
    """Verify AgeRecordModel raises AtomFormatError when completely unpopulated."""
    with pytest.raises(
        AtomFormatError, match="must specify raw_text or at least one of"
    ):
        AgeRecordModel()


@pytest.mark.unit
@pytest.mark.regression
def test_age_record_negative_years_raises_error() -> None:
    """Verify AgeRecordModel raises AtomFormatError on negative years."""
    with pytest.raises(AtomFormatError, match="cannot be negative"):
        AgeRecordModel(years=-1)


@pytest.mark.unit
@pytest.mark.regression
@pytest.mark.parametrize("bad_month", [-1, 12, 100])
def test_age_record_invalid_months_raises_error(bad_month: int) -> None:
    """Verify AgeRecordModel raises AtomFormatError when months outside 0..11."""
    with pytest.raises(AtomFormatError, match="must be between 0 and 11"):
        AgeRecordModel(months=bad_month)


@pytest.mark.unit
@pytest.mark.regression
@pytest.mark.parametrize("bad_day", [-1, 32, 100])
def test_age_record_invalid_days_raises_error(bad_day: int) -> None:
    """Verify AgeRecordModel raises AtomFormatError when days outside 0..31."""
    with pytest.raises(AtomFormatError, match="must be between 0 and 31"):
        AgeRecordModel(days=bad_day)


@pytest.mark.unit
def test_age_record_immutability() -> None:
    """Verify AgeRecordModel is frozen and immutable."""
    age = AgeRecordModel(years=50)
    with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
        age.years = 51  # type: ignore[misc]


@pytest.mark.unit
def test_age_record_introspection() -> None:
    """Verify .help() renders on AgeRecordModel."""
    age = AgeRecordModel(years=50)
    help_text = age.help(as_str=True)
    assert help_text is not None
    assert "=== AgeRecordModel Public Directory ===" in help_text
    assert "formatted_age" in help_text
