"""Path: tests/test_gda/test_model/test_atom/test_date.py

Comprehensive test suite verifying atomic temporal primitives and calendar types.

Operational Role:
    Verifies HistoricalYear, CensusYear, DateString, IsoTimestamp, EventDate,
    EventDateRange, BirthYear, and DeathYear boundary validations, format patterns,
    temporal modifiers, factory constructors, copy-on-write mutators, serialization,
    and immutability invariants with 100% statement and branch coverage.
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

__version__ = "1.0.0+build.12"


# ==============================================================================
# GROUP 1: HISTORICALYEAR, BIRTHYEAR & DEATHYEAR BOUNDARIES
# Note: Verification of range boundaries (1000..2100) and specialized subclasses
# ==============================================================================


@pytest.mark.regression
@pytest.mark.parametrize("valid_year", [1000, 1492, 1880, 1945, 2026, 2100])
def test_historical_year_valid_boundaries(valid_year: int) -> None:
    """Verify HistoricalYear instantiates across bounded range (1000..2100)."""
    hy = HistoricalYear(valid_year)
    assert hy.value == valid_year
    assert int(hy) == valid_year
    assert repr(hy) == f"HistoricalYear(value={valid_year})"


@pytest.mark.regression
@pytest.mark.parametrize("invalid_year", [999, 500, 0, -100, 2101, 3000])
def test_historical_year_out_of_bounds_raises_range_error(invalid_year: int) -> None:
    """Verify HistoricalYear raises ModelRangeError outside 1000..2100."""
    with pytest.raises(ModelRangeError, match="out of range"):
        HistoricalYear(invalid_year)


@pytest.mark.regression
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
# Note: Verification of US Federal Decennial Census years (1790..1950)
# ==============================================================================


@pytest.mark.regression
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


@pytest.mark.regression
@pytest.mark.parametrize("invalid_census", [1885, 1890, 1960, 1780, 2000])
def test_census_year_invalid_schedules_raise_range_error(invalid_census: int) -> None:
    """Verify non-census years and destroyed schedules (1890) raise ModelRangeError."""
    with pytest.raises(
        ModelRangeError,
        match=r"Census enumeration year \(1790\.\.1950, excluding 1890\)",
    ):
        CensusYear(invalid_census)


@pytest.mark.regression
def test_census_year_enum_membership() -> None:
    """Verify CensusYearEnum count matches 16 historical federal decennial schedules."""
    assert len(CensusYearEnum) == 16
    assert 1890 not in {member.value for member in CensusYearEnum}


# ==============================================================================
# GROUP 3: DATESTRING & ISOTIMESTAMP FORMAT VALIDATION
# Note: Verification of textual date encapsulation and ISO 8601 extended syntax
# ==============================================================================


@pytest.mark.regression
def test_date_string_valid_instantiation() -> None:
    """Verify DateString preserves textual date representations."""
    ds = DateString("14 APR 1865")
    assert ds.value == "14 APR 1865"
    assert str(ds) == "14 APR 1865"
    assert repr(ds) == "DateString(value='14 APR 1865')"


@pytest.mark.regression
@pytest.mark.parametrize("empty_val", ["", " ", "\t\n"])
def test_date_string_empty_raises_format_error(empty_val: str) -> None:
    """Verify DateString raises ModelFormatError on empty or whitespace strings."""
    with pytest.raises(ModelFormatError, match="cannot be empty or whitespace"):
        DateString(empty_val)


@pytest.mark.regression
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


@pytest.mark.regression
def test_iso_timestamp_now_utc() -> None:
    """Verify IsoTimestamp.now_utc() generates valid UTC timestamp."""
    ts = IsoTimestamp.now_utc()
    assert ts.value.endswith("Z")
    assert len(ts.value) == 20


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
# GROUP 4: EVENTDATE & EVENTDATERANGE FACTORY & MUTATORS
# Note: Verification of factory methods, string coercions, year extraction, mutators
# ==============================================================================


@pytest.mark.regression
def test_event_date_exact_formatting_and_year() -> None:
    """Verify EventDate formats correctly and extracts calendar year."""
    ed = EventDate.create("12 MAY 1880")
    assert str(ed) == "12 MAY 1880"
    assert ed.year == 1880
    assert ed.year_lower_bound == 1880
    assert repr(ed) == "EventDate(date=DateString(value='12 MAY 1880'))"

    ed_exact = EventDate.create("12 MAY 1880", DateModifier.EXACT)
    assert str(ed_exact) == "12 MAY 1880"
    assert (
        repr(ed_exact)
        == "EventDate(date=DateString(value='12 MAY 1880'), modifier=EXACT)"
    )


@pytest.mark.regression
def test_event_date_qualified_formatting() -> None:
    """Verify EventDate formats with genealogical modifiers (ABT, BEF, AFT, EST, CAL)."""
    assert str(EventDate.create("1880", "ABT")) == "ABT 1880"
    assert str(EventDate.create("1880", "BEFORE")) == "BEF 1880"
    assert str(EventDate.create("1880", "AFT")) == "AFT 1880"
    assert str(EventDate.create("1880", "EST")) == "EST 1880"
    assert str(EventDate.create("1880", "CALCULATED")) == "CAL 1880"

    unparseable = EventDate.create("circa medieval")
    assert unparseable.year is None
    assert unparseable.year_lower_bound is None


@pytest.mark.regression
def test_event_date_copy_on_write_mutators() -> None:
    """Verify EventDate mutators produce updated copies."""
    original = EventDate.create("1880", DateModifier.ABOUT)
    up_date = original.update_date("1885")
    assert up_date is not original
    assert str(up_date) == "ABT 1885"
    assert up_date.year == 1885

    up_mod = up_date.update_modifier(DateModifier.EXACT)
    assert up_mod is not up_date
    assert str(up_mod) == "1885"

    up_mod_alias = up_date.update_modifier("BEFORE")
    assert str(up_mod_alias) == "BEF 1885"


@pytest.mark.regression
def test_event_date_range_factory_and_bounds() -> None:
    """Verify EventDateRange creation, year bounds, string, representation, and mutators."""
    edr = EventDateRange.create("1880", "1890")
    assert str(edr) == "BET 1880 AND 1890"
    assert repr(edr) == (
        "EventDateRange(start_date=EventDate(date=DateString(value='1880')), "
        "end_date=EventDate(date=DateString(value='1890')), modifier=BET)"
    )
    assert edr.start_year == 1880
    assert edr.end_year == 1890
    assert edr.year_lower_bound == 1880

    up_s = edr.update_start("1882")
    assert up_s.start_year == 1882
    up_e = up_s.update_end("1895")
    assert up_e.end_year == 1895


@pytest.mark.regression
def test_temporal_ordering_comparisons() -> None:
    """Verify chronological ordering between EventDate and EventDateRange."""
    d1 = EventDate.create("1850")
    d2 = EventDate.create("1880")
    dr = EventDateRange.create("1860", "1870")

    assert d1 < d2
    assert d1 < dr
    assert dr < d2

    # Tiebreaker when years are equal
    d_early = EventDate.create("1880-01-01")
    d_late = EventDate.create("1880-05-12")
    assert d_early < d_late

    # Range tiebreaker when start years are equal
    dr1 = EventDateRange.create("1880-01-01", "1890")
    dr2 = EventDateRange.create("1880-05-01", "1890")
    assert dr1 < dr2

    d_none = EventDate.create("unknown")
    assert d1 < d_none

    with pytest.raises(TypeError):
        _ = d1 < 1850  # type: ignore[operator]

    with pytest.raises(TypeError):
        _ = dr1 < "not-a-date-range"  # type: ignore[operator]


# ==============================================================================
# GROUP 5: SERIALIZATION & ROUND TRIPS
# Note: Verification of dictionary and JSON string payload conversions
# ==============================================================================


@pytest.mark.integration
def test_event_date_to_dict_and_json_round_trip() -> None:
    """Verify EventDate dictionary and JSON serialization."""
    ed = EventDate.create("1880-05-12", DateModifier.ABOUT)
    data = ed.to_dict()
    assert data == {"date": "1880-05-12", "modifier": "ABT"}

    restored = EventDate.from_dict(data)
    assert restored == ed

    json_str = ed.to_json()
    assert "1880-05-12" in json_str
    assert EventDate.from_json(json_str) == ed


@pytest.mark.integration
def test_event_date_range_to_dict_and_json_round_trip() -> None:
    """Verify EventDateRange dictionary and JSON serialization."""
    edr = EventDateRange.create("1880-01-01", "1885-12-31")
    data = edr.to_dict()
    assert data["start_date"]["date"] == "1880-01-01"
    assert data["end_date"]["date"] == "1885-12-31"
    assert data["modifier"] == "BET"

    restored = EventDateRange.from_dict(data)
    assert restored == edr

    # Test non-dict string endpoints in from_dict
    string_payload = {
        "start_date": "1880-01-01",
        "end_date": "1885-12-31",
        "modifier": "BET",
    }
    restored_str = EventDateRange.from_dict(string_payload)
    assert restored_str == edr

    json_str = edr.to_json()
    assert EventDateRange.from_json(json_str) == edr


@pytest.mark.regression
def test_event_date_deserialization_defensive_errors() -> None:
    """Verify deserializers reject malformed date payloads."""
    with pytest.raises(ModelFormatError, match="must be a dictionary"):
        EventDate.from_dict("not-a-dict")  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="Missing required field 'date'"):
        EventDate.from_dict({"modifier": "EXACT"})

    with pytest.raises(ModelFormatError, match="Failed to parse EventDate JSON"):
        EventDate.from_json("{broken json")

    with pytest.raises(ModelFormatError, match="must be a dictionary"):
        EventDateRange.from_dict("not-a-dict")  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="requires 'start_date' and 'end_date'"):
        EventDateRange.from_dict({"start_date": "1880"})

    with pytest.raises(ModelFormatError, match="Failed to parse EventDateRange JSON"):
        EventDateRange.from_json("{broken json")

    with pytest.raises(ModelFormatError, match="Invalid DateModifier value"):
        EventDate.create("1880", "ALIEN_MODIFIER")


# ==============================================================================
# GROUP 6: IMMUTABILITY & INTROSPECTION
# Note: Verification of frozen immutability and introspection directory
# ==============================================================================


@pytest.mark.regression
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


@pytest.mark.regression
def test_temporal_atoms_introspection() -> None:
    """Verify .help() discovery mixin renders directory on temporal primitives."""
    ed = EventDate.create("1880", DateModifier.EXACT)
    help_text = ed.help(as_str=True)
    assert help_text is not None
    assert "=== EventDate Public Directory ===" in help_text
    assert "year" in help_text
    assert "update_date" in help_text
