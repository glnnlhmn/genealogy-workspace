"""Path: tests/test_gda/test_model/test_atom/test_date.py

Comprehensive test suite verifying atomic temporal primitives and calendar types.

Operational Role:
    Verifies HistoricalYear, CensusYear, DateString, IsoTimestamp, EventDate,
    EventDateRange, BirthYear, and DeathYear boundary validations, format patterns,
    temporal modifiers, and immutability invariants.

Test Structure & Protocol:
    - Atomized tests: 1:1 behavioral contract mapping.
    - Fully decorated: Standard 7-marker taxonomy.
    - Zero production disk I/O.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from gda.core.errors import ModelFormatError, ModelRangeError
from gda.model.atom.date import (
    BirthYear,
    CensusYear,
    CensusYearEnum,
    DateModifier,
    DateString,
    DeathYear,
    EventDate,
    EventDateRange,
    HistoricalYear,
    IsoTimestamp,
)

__version__ = "1.0.0+build.8"


# ==============================================================================
# GROUP 1: HISTORICALYEAR, BIRTHYEAR & DEATHYEAR BOUNDARIES
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
@pytest.mark.parametrize("valid_year", [1000, 1492, 1880, 1945, 2026, 2100])
def test_historical_year_valid_boundaries(valid_year: int) -> None:
    """Verify HistoricalYear instantiates across bounded range (1000..2100)."""
    hy = HistoricalYear(valid_year)
    assert hy.value == valid_year
    assert int(hy) == valid_year
    assert repr(hy) == f"HistoricalYear(value={valid_year})"


@pytest.mark.unit
@pytest.mark.regression
@pytest.mark.parametrize("invalid_year", [999, 500, 0, -100, 2101, 3000])
def test_historical_year_out_of_bounds_raises_range_error(invalid_year: int) -> None:
    """Verify HistoricalYear raises ModelRangeError outside 1000..2100."""
    with pytest.raises(ModelRangeError, match="out of range"):
        HistoricalYear(invalid_year)


@pytest.mark.unit
@pytest.mark.smoke
def test_birth_and_death_year_subclasses() -> None:
    """Verify BirthYear and DeathYear specialize HistoricalYear invariants."""
    by = BirthYear(1865)
    dy = DeathYear(1942)

    assert isinstance(by, HistoricalYear)
    assert isinstance(dy, HistoricalYear)
    assert by.value == 1865
    assert dy.value == 1942
    assert repr(by) == "BirthYear(value=1865)"
    assert repr(dy) == "DeathYear(value=1942)"


# ==============================================================================
# GROUP 2: CENSUSYEAR ENUMERATION & INVARIANTS
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
@pytest.mark.parametrize(
    "census_year",
    [
        1790,
        1800,
        1810,
        1820,
        1830,
        1840,
        1850,
        1860,
        1870,
        1880,
        1900,
        1910,
        1920,
        1930,
        1940,
        1950,
    ],
)
def test_census_year_valid_schedules(census_year: int) -> None:
    """Verify CensusYear validates against federal decennial enumeration schedules."""
    cy = CensusYear(census_year)
    assert cy.value == census_year
    assert int(cy) == census_year
    assert repr(cy) == f"CensusYear(value={census_year})"


@pytest.mark.unit
@pytest.mark.regression
@pytest.mark.parametrize("invalid_census", [1885, 1890, 1960, 1780, 2000])
def test_census_year_invalid_schedules_raise_range_error(invalid_census: int) -> None:
    """Verify non-census years and destroyed schedules (1890) raise ModelRangeError."""
    with pytest.raises(
        ModelRangeError,
        match=r"Census enumeration year \(1790\.\.1950, excluding 1890\)",
    ):
        CensusYear(invalid_census)


@pytest.mark.unit
def test_census_year_enum_membership() -> None:
    """Verify CensusYearEnum count matches 16 historical federal decennial schedules."""
    assert len(CensusYearEnum) == 16
    assert 1890 not in {member.value for member in CensusYearEnum}


# ==============================================================================
# GROUP 3: DATESTRING & ISOTIMESTAMP FORMAT VALIDATION
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_date_string_valid_instantiation() -> None:
    """Verify DateString preserves textual date representations."""
    ds = DateString("14 APR 1865")
    assert ds.value == "14 APR 1865"
    assert str(ds) == "14 APR 1865"
    assert repr(ds) == "DateString(value='14 APR 1865')"


@pytest.mark.unit
@pytest.mark.regression
@pytest.mark.parametrize("empty_val", ["", "   ", "\t\n"])
def test_date_string_empty_raises_format_error(empty_val: str) -> None:
    """Verify DateString raises ModelFormatError on empty or whitespace strings."""
    with pytest.raises(ModelFormatError, match="cannot be empty or whitespace"):
        DateString(empty_val)


@pytest.mark.unit
@pytest.mark.smoke
@pytest.mark.parametrize(
    "valid_iso",
    [
        "2026-10-16T12:00:00Z",
        "2026-10-16T12:00:00.123456Z",
        "2026-10-16T08:00:00-04:00",
        "2026-10-16T17:30:00+05:30",
    ],
)
def test_iso_timestamp_valid_formats(valid_iso: str) -> None:
    """Verify IsoTimestamp validates extended ISO 8601 UTC and offset representations."""
    ts = IsoTimestamp(valid_iso)
    assert ts.value == valid_iso
    assert str(ts) == valid_iso
    assert repr(ts) == f"IsoTimestamp(value='{valid_iso}')"


@pytest.mark.unit
@pytest.mark.smoke
def test_iso_timestamp_now_utc() -> None:
    """Verify IsoTimestamp.now_utc() generates valid UTC timestamp."""
    ts = IsoTimestamp.now_utc()
    assert ts.value.endswith("Z")
    assert len(ts.value) == 20


@pytest.mark.unit
@pytest.mark.regression
@pytest.mark.parametrize(
    "invalid_iso",
    [
        "",
        "2026-10-16",
        "2026-10-16 12:00:00",
        "12:00:00Z",
        "not-a-timestamp",
    ],
)
def test_iso_timestamp_invalid_syntax_raises_format_error(invalid_iso: str) -> None:
    """Verify IsoTimestamp raises ModelFormatError on malformed timestamps."""
    with pytest.raises(ModelFormatError, match="Must match ISO 8601 extended format"):
        IsoTimestamp(invalid_iso)


# ==============================================================================
# GROUP 4: EVENTDATE & EVENTDATERANGE COMPOSITION
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_event_date_exact_formatting() -> None:
    """Verify EventDate formats correctly with default or EXACT modifier."""
    d = DateString("12 MAY 1880")
    ed_default = EventDate(date=d)
    assert str(ed_default) == "12 MAY 1880"
    assert repr(ed_default) == "EventDate(date=DateString(value='12 MAY 1880'))"

    ed_exact = EventDate(date=d, modifier=DateModifier.EXACT)
    assert str(ed_exact) == "12 MAY 1880"
    assert (
        repr(ed_exact)
        == "EventDate(date=DateString(value='12 MAY 1880'), modifier=EXACT)"
    )


@pytest.mark.unit
@pytest.mark.smoke
def test_event_date_qualified_formatting() -> None:
    """Verify EventDate formats with genealogical modifiers (ABT, BEF, AFT, EST, CAL)."""
    d = DateString("1880")
    ed_abt = EventDate(date=d, modifier=DateModifier.ABOUT)
    assert str(ed_abt) == "ABT 1880"

    ed_bef = EventDate(date=d, modifier=DateModifier.BEFORE)
    assert str(ed_bef) == "BEF 1880"

    ed_aft = EventDate(date=d, modifier=DateModifier.AFTER)
    assert str(ed_aft) == "AFT 1880"

    ed_est = EventDate(date=d, modifier=DateModifier.ESTIMATED)
    assert str(ed_est) == "EST 1880"

    ed_cal = EventDate(date=d, modifier=DateModifier.CALCULATED)
    assert str(ed_cal) == "CAL 1880"


@pytest.mark.unit
@pytest.mark.smoke
def test_event_date_range_formatting() -> None:
    """Verify EventDateRange structures interval spans using standard modifiers."""
    start = EventDate(date=DateString("1880"), modifier=DateModifier.EXACT)
    end = EventDate(date=DateString("1890"), modifier=DateModifier.EXACT)

    edr = EventDateRange(start_date=start, end_date=end, modifier=DateModifier.BETWEEN)
    assert str(edr) == "BET 1880 AND 1890"
    assert repr(edr) == (
        "EventDateRange(start_date=EventDate(date=DateString(value='1880'), modifier=EXACT), "
        "end_date=EventDate(date=DateString(value='1890'), modifier=EXACT), modifier=BET)"
    )


# ==============================================================================
# GROUP 5: IMMUTABILITY & INTROSPECTION
# ==============================================================================


@pytest.mark.unit
def test_temporal_atoms_immutability() -> None:
    """Verify temporal primitives are frozen and immutable."""
    hy = HistoricalYear(1900)
    with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
        hy.value = 1901  # type: ignore[misc]

    ds = DateString("1880")
    with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
        ds.value = "1881"  # type: ignore[misc]

    ed = EventDate(date=ds)
    with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
        ed.modifier = DateModifier.ABOUT  # type: ignore[misc]


@pytest.mark.unit
def test_temporal_atoms_introspection() -> None:
    """Verify .help() discovery mixin renders directory on temporal primitives."""
    ed = EventDate(date=DateString("1880"), modifier=DateModifier.EXACT)
    help_text = ed.help(as_str=True)
    assert help_text is not None
    assert "=== EventDate Public Directory ===" in help_text
