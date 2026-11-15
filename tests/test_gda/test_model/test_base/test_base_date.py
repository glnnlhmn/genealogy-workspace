"""Path: tests/test_gda/test_model/test_base/test_base_date.py

Comprehensive test suite verifying EventDate and TimePeriod contracts in gda.model.base.date.

Operational Role:
    Verifies EventDate approximation modifiers, BETWEEN range bounds, GEDCOM
    prefix parsing in .create(), serialization round-trips, TimePeriod full
    (year, month, day) sequence validation, and public interface stability with
    100% statement and branch coverage.
"""

from __future__ import annotations

import dataclasses
from dataclasses import FrozenInstanceError

import pytest
from pydantic import ValidationError

import gda.model.base.date as base_date_mod
from gda.core.enums.date import DateModifier
from gda.core.errors import ModelFormatError, ModelRangeError
from gda.model.atom.date import DateString
from gda.model.base.date import EventDate, TimePeriod

__version__ = "1.0.0+build.3"


# ==============================================================================
# GROUP 1: EVENTDATE CREATION, MODIFIERS & SERIALIZATION
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_event_date_exact_about_and_between_formatting() -> None:
    """Verify EventDate instantiates and formats EXACT, ABOUT, and BETWEEN dates."""
    exact = EventDate(date=DateString("1880-05-14"))
    assert str(exact) == "1880-05-14"
    assert (
        repr(exact)
        == f"EventDate(date=DateString(value='1880-05-14'), modifier={DateModifier.EXACT})"
    )

    abt = EventDate(date=DateString("1880"), modifier=DateModifier.ABOUT)
    assert str(abt) == "ABT 1880"

    bet = EventDate(
        date=DateString("1880-01-01"),
        modifier=DateModifier.BETWEEN,
        end_date=DateString("1880-12-31"),
    )
    assert str(bet) == "BET 1880-01-01 AND 1880-12-31"
    assert "end_date=DateString(value='1880-12-31')" in repr(bet)

    # Identical BETWEEN endpoints satisfy boundary equality (end_key == start_key)
    same_bet = EventDate.create("1880", modifier="BET", end_date="1880")
    assert str(same_bet) == "BET 1880 AND 1880"


@pytest.mark.unit
@pytest.mark.smoke
def test_event_date_create_factory_parses_prefixes_and_atoms() -> None:
    """Verify EventDate.create() parses inline GEDCOM modifier tokens, None, and atoms."""
    parsed_abt = EventDate.create("ABT 1850")
    assert parsed_abt.modifier == DateModifier.ABOUT
    assert parsed_abt.date == DateString("1850")

    parsed_circa = EventDate.create("circa 1865-04")
    assert parsed_circa.modifier == DateModifier.ABOUT
    assert parsed_circa.date == DateString("1865-04")

    from_atom = EventDate.create(DateString("1870"), modifier="BEF")
    assert from_atom.modifier == DateModifier.BEFORE
    assert from_atom.date == DateString("1870")

    none_mod = EventDate.create("1875", modifier=None, end_date="   ")
    assert none_mod.modifier == DateModifier.EXACT
    assert none_mod.end_date is None

    bet_created = EventDate.create(
        DateString("1890"),
        modifier=DateModifier.BETWEEN,
        end_date=DateString("1895"),
    )
    assert bet_created.end_date == DateString("1895")

    non_iso_prefix = EventDate.create("NOT_A_MOD 1842")
    assert non_iso_prefix.modifier == DateModifier.EXACT
    assert non_iso_prefix.date == DateString("NOT_A_MOD 1842")


@pytest.mark.unit
@pytest.mark.regression
def test_event_date_validation_and_factory_errors() -> None:
    """Verify EventDate enforces BETWEEN invariants, chronological order, and input types."""
    with pytest.raises(ModelFormatError, match="modifier BETWEEN requires an end_date"):
        EventDate(date=DateString("1880"), modifier=DateModifier.BETWEEN)

    with pytest.raises(ModelFormatError, match="end_date is only valid when modifier is BETWEEN"):
        EventDate(
            date=DateString("1880"),
            modifier=DateModifier.EXACT,
            end_date=DateString("1885"),
        )

    with pytest.raises(ModelRangeError, match="cannot precede date"):
        EventDate(
            date=DateString("1885"),
            modifier=DateModifier.BETWEEN,
            end_date=DateString("1880"),
        )

    # Same year, inverted month/day must also fail
    with pytest.raises(ModelRangeError, match="cannot precede date"):
        EventDate.create("1880-08", modifier="BET", end_date="1880-02")

    with pytest.raises(ModelFormatError, match="'date' cannot be empty"):
        EventDate.create("   ")

    with pytest.raises(ModelFormatError, match="Invalid EventDate 'date' type"):
        EventDate.create(1880)  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="Invalid DateModifier value"):
        EventDate.create("1880", modifier="NOT_A_MOD")

    with pytest.raises(ModelFormatError, match="Invalid EventDate 'end_date' type"):
        EventDate.create("1880", modifier=DateModifier.BETWEEN, end_date=1885)  # type: ignore[arg-type]

    with pytest.raises(ValidationError):
        EventDate(date="1880")  # type: ignore[arg-type]


@pytest.mark.unit
def test_event_date_serialization_round_trip() -> None:
    """Verify EventDate to_dict, from_dict, to_json, and from_json round-trip fidelity."""
    exact = EventDate.create("1880")
    assert exact.to_dict() == {"date": "1880", "modifier": "EXACT"}

    bet = EventDate.create("1880-01", modifier="BET", end_date="1880-06")
    payload = bet.to_dict()
    assert payload == {"date": "1880-01", "modifier": "BET", "end_date": "1880-06"}
    assert EventDate.from_dict(payload) == bet
    assert EventDate.from_dict("ABT 1880") == EventDate.create("ABT 1880")

    json_str = bet.to_json()
    assert EventDate.from_json(json_str) == bet

    with pytest.raises(ModelFormatError, match="must be a dictionary or string"):
        EventDate.from_dict(123)  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="Missing required field 'date'"):
        EventDate.from_dict({"modifier": "EXACT"})

    with pytest.raises(ModelFormatError, match="Failed to parse EventDate JSON"):
        EventDate.from_json("{bad-json")


# ==============================================================================
# GROUP 2: TIMEPERIOD CREATION, CHRONOLOGICAL VALIDATION & SERIALIZATION
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_time_period_bounded_and_open_ended_ranges(
    event_date_1850: EventDate,
    event_date_1910: EventDate,
) -> None:
    """Verify TimePeriod instantiates with full bounds or single open-ended boundary."""
    bounded = TimePeriod(start_date=event_date_1850, end_date=event_date_1910)
    assert bounded.is_bounded is True
    assert str(bounded) == "1850 - 1910"
    assert repr(bounded) == (
        f"TimePeriod(start_date=EventDate(date=DateString(value='1850'), modifier={DateModifier.EXACT}), "
        f"end_date=EventDate(date=DateString(value='1910'), modifier={DateModifier.EXACT}))"
    )

    start_only = TimePeriod(start_date=EventDate.create("ABT 1850"))
    assert start_only.is_bounded is False
    assert str(start_only) == "from ABT 1850"

    end_only = TimePeriod(end_date=EventDate.create("BEF 1910"))
    assert end_only.is_bounded is False
    assert str(end_only) == "until BEF 1910"


@pytest.mark.unit
@pytest.mark.regression
def test_time_period_chronological_validation_and_edge_cases(
    event_date_1850: EventDate,
    event_date_1910: EventDate,
) -> None:
    """Verify TimePeriod rejects inverted year/month/day ranges and allows equal dates."""
    with pytest.raises(ModelFormatError, match="must define at least one boundary date"):
        TimePeriod(start_date=None, end_date=None)

    with pytest.raises(ModelRangeError, match="cannot precede inception date"):
        TimePeriod(start_date=event_date_1910, end_date=event_date_1850)

    # Same year, inverted month
    with pytest.raises(ModelRangeError, match="cannot precede inception date"):
        TimePeriod(
            start_date=EventDate.create("1880-09-15"),
            end_date=EventDate.create("1880-03-10"),
        )

    # Same year and month, inverted day
    with pytest.raises(ModelRangeError, match="cannot precede inception date"):
        TimePeriod(
            start_date=EventDate.create("1880-05-20"),
            end_date=EventDate.create("1880-05-10"),
        )

    # Equal date passes cleanly
    same_year = TimePeriod(start_date=event_date_1850, end_date=event_date_1850)
    assert same_year.is_bounded is True


@pytest.mark.unit
def test_time_period_serialization_immutability_and_introspection(
    event_date_1850: EventDate,
    event_date_1910: EventDate,
) -> None:
    """Verify TimePeriod serialization, immutability, and IntrospectableMixin .help()."""
    period = TimePeriod(start_date=event_date_1850, end_date=event_date_1910)
    payload = period.to_dict()
    assert payload == {
        "start_date": {"date": "1850", "modifier": "EXACT"},
        "end_date": {"date": "1910", "modifier": "EXACT"},
    }
    assert TimePeriod.from_dict(payload) == period
    assert (
        TimePeriod.from_dict({"start_date": event_date_1850, "end_date": None}).start_date
        == event_date_1850
    )

    open_end = TimePeriod(start_date=event_date_1850)
    assert open_end.to_dict() == {
        "start_date": {"date": "1850", "modifier": "EXACT"},
        "end_date": None,
    }
    assert TimePeriod.from_dict(open_end.to_dict()) == open_end

    json_str = period.to_json()
    assert TimePeriod.from_json(json_str) == period

    with pytest.raises(ModelFormatError, match="must be a dictionary"):
        TimePeriod.from_dict("not-a-dict")  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="Failed to parse TimePeriod JSON"):
        TimePeriod.from_json("{bad-json")

    with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
        period.start_date = event_date_1910  # type: ignore[misc]

    help_text = period.help(as_str=True)
    assert help_text is not None
    assert "=== TimePeriod Public Directory ===" in help_text
    assert "is_bounded" in help_text


# ==============================================================================
# GROUP 3: PUBLIC INTERFACE CONTRACT LOCK
# ==============================================================================


@pytest.mark.unit
@pytest.mark.regression
def test_base_date_module_public_interface_contract() -> None:
    """Verify gda.model.base.date exports, dataclass fields, and public methods do not drift."""
    assert base_date_mod.__all__ == ["EventDate", "TimePeriod"]

    event_fields = [f.name for f in dataclasses.fields(EventDate)]
    assert event_fields == ["date", "modifier", "end_date"]
    for attr in ("create", "to_dict", "from_dict", "to_json", "from_json"):
        assert callable(getattr(EventDate, attr))

    period_fields = [f.name for f in dataclasses.fields(TimePeriod)]
    assert period_fields == ["start_date", "end_date"]
    assert isinstance(TimePeriod.is_bounded, property)
    for attr in ("to_dict", "from_dict", "to_json", "from_json"):
        assert callable(getattr(TimePeriod, attr))
