"""Path: tests/test_gda/test_model/test_base/test_name.py

Comprehensive test suite verifying CanonicalName, HistoricalName, and NameStatus.

Operational Role:
    Verifies that CanonicalName formats discrete personal name parts,
    HistoricalName enforces raw and canonical name integrity, deduplicates
    alternate spellings, composes TimePeriod boundaries, and ensures immutability.

Test Structure & Protocol:
    - Atomized tests: 1:1 behavioral contract mapping.
    - Fully decorated: Standard 7-marker taxonomy.
    - Zero production disk I/O.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from gda.core.errors import ModelFormatError
from gda.model.atom.date import DateModifier, DateString, EventDate
from gda.model.base.name import CanonicalName, HistoricalName, NameStatus
from gda.model.base.time_period import TimePeriod

__version__ = "1.0.0+build.4"


# ==============================================================================
# FIXTURES: GOLDEN & BOUNDARY CONFIGURATIONS
# ==============================================================================


@pytest.fixture
def golden_time_period() -> TimePeriod:
    """Fixture providing a standard bounded TimePeriod."""
    return TimePeriod(
        start_date=EventDate(date=DateString("1751"), modifier=DateModifier.EXACT),
        end_date=EventDate(date=DateString("1810"), modifier=DateModifier.EXACT),
    )


@pytest.fixture
def golden_canonical_name() -> CanonicalName:
    """Fixture providing a populated CanonicalName instance."""
    return CanonicalName(
        raw_name="Col. John Quincy Adams Jr.",
        given="John",
        middle="Quincy",
        surname="Adams",
        suffix="Jr.",
        maiden_name=None,
    )


@pytest.fixture
def golden_historical_name(golden_time_period: TimePeriod) -> HistoricalName:
    """Fixture providing a complete HistoricalName instance."""
    return HistoricalName(
        raw_name="Derryfield",
        canonical_name="Manchester",
        status=NameStatus.HISTORICAL,
        valid_period=golden_time_period,
        alternate_spellings=["Derry-field", "Derry Field"],
        notes="Chartered in 1751, renamed Manchester in 1810.",
    )


# ==============================================================================
# GROUP 1: CANONICALNAME CREATION & FORMATTING
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_canonical_name_full_segments(golden_canonical_name: CanonicalName) -> None:
    """Verify CanonicalName constructs full display name from all segments."""
    assert golden_canonical_name.raw_name == "Col. John Quincy Adams Jr."
    assert golden_canonical_name.given == "John"
    assert golden_canonical_name.middle == "Quincy"
    assert golden_canonical_name.surname == "Adams"
    assert golden_canonical_name.suffix == "Jr."
    assert golden_canonical_name.maiden_name is None
    assert golden_canonical_name.full_name == "John Quincy Adams Jr."
    assert str(golden_canonical_name) == "John Quincy Adams Jr."


@pytest.mark.unit
@pytest.mark.smoke
def test_canonical_name_raw_only_fallback() -> None:
    """Verify CanonicalName falls back to raw_name when segments are absent."""
    name = CanonicalName(raw_name="Widow Johnson")
    assert name.full_name == "Widow Johnson"
    assert str(name) == "Widow Johnson"


@pytest.mark.unit
@pytest.mark.regression
@pytest.mark.parametrize("blank_name", ["", "   ", "\t\n"])
def test_canonical_name_empty_raw_name_raises_error(blank_name: str) -> None:
    """Verify CanonicalName raises ModelFormatError if raw_name is empty or whitespace."""
    with pytest.raises(
        ModelFormatError,
        match="CanonicalName 'raw_name' cannot be empty or whitespace.",
    ):
        CanonicalName(raw_name=blank_name)


# ==============================================================================
# GROUP 2: HISTORICALNAME CREATION & EVOLUTION
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_name_status_members() -> None:
    """Verify NameStatus enumerates expected classifications."""
    expected = {"PRIMARY", "HISTORICAL", "COLLOQUIAL", "INDIGENOUS", "COLONIAL"}
    assert {s.value for s in NameStatus} == expected


@pytest.mark.unit
@pytest.mark.smoke
def test_historical_name_golden_contract(
    golden_historical_name: HistoricalName, golden_time_period: TimePeriod
) -> None:
    """Verify HistoricalName instantiates with canonical normalization and TimePeriod."""
    assert golden_historical_name.raw_name == "Derryfield"
    assert golden_historical_name.canonical_name == "Manchester"
    assert golden_historical_name.display_name == "Manchester"
    assert golden_historical_name.status == NameStatus.HISTORICAL
    assert golden_historical_name.valid_period == golden_time_period
    assert golden_historical_name.alternate_spellings == ["Derry-field", "Derry Field"]
    assert str(golden_historical_name) == "Manchester (HISTORICAL: 1751 - 1810)"


@pytest.mark.unit
@pytest.mark.smoke
def test_historical_name_raw_only_fallback() -> None:
    """Verify HistoricalName display_name falls back to raw_name when canonical is None."""
    hn = HistoricalName(raw_name="Bean Town", status=NameStatus.COLLOQUIAL)
    assert hn.display_name == "Bean Town"
    assert str(hn) == "Bean Town (COLLOQUIAL)"


@pytest.mark.unit
@pytest.mark.regression
@pytest.mark.parametrize("blank_name", ["", "   ", "\t\n"])
def test_historical_name_blank_raw_name_raises_error(blank_name: str) -> None:
    """Verify HistoricalName raises ModelFormatError on empty raw_name."""
    with pytest.raises(
        ModelFormatError,
        match="HistoricalName 'raw_name' cannot be empty or whitespace.",
    ):
        HistoricalName(raw_name=blank_name)


@pytest.mark.unit
@pytest.mark.regression
@pytest.mark.parametrize("blank_canonical", ["", "   ", "\t\n"])
def test_historical_name_blank_canonical_name_raises_error(
    blank_canonical: str,
) -> None:
    """Verify HistoricalName raises ModelFormatError if canonical_name is provided but blank."""
    with pytest.raises(
        ModelFormatError,
        match="HistoricalName 'canonical_name' cannot be empty or whitespace if provided.",
    ):
        HistoricalName(raw_name="Valid Raw", canonical_name=blank_canonical)


@pytest.mark.unit
@pytest.mark.regression
def test_historical_name_duplicate_spellings_raises_error() -> None:
    """Verify HistoricalName rejects duplicate alternate spellings."""
    with pytest.raises(
        ModelFormatError,
        match="Duplicate entries found in alternate_spellings.",
    ):
        HistoricalName(
            raw_name="Bow",
            alternate_spellings=["Bowe", "Bowe"],
        )


# ==============================================================================
# GROUP 3: IMMUTABILITY & INTROSPECTION
# ==============================================================================


@pytest.mark.unit
def test_naming_models_immutability(golden_canonical_name: CanonicalName) -> None:
    """Verify CanonicalName and HistoricalName are frozen and immutable."""
    with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
        golden_canonical_name.given = "Jane"  # type: ignore[misc]

    h_name = HistoricalName(raw_name="Bow")
    with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
        h_name.raw_name = "Concord"  # type: ignore[misc]


@pytest.mark.unit
def test_naming_models_introspection() -> None:
    """Verify .help() renders member directory on naming models."""
    h_name = HistoricalName(raw_name="Bow")
    help_text = h_name.help(as_str=True)
    assert help_text is not None
    assert "=== HistoricalName Public Directory ===" in help_text
    assert "display_name" in help_text
