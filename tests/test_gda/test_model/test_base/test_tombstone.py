# Name: test_tombstone.py
# Path: tests/test_gda/test_model/test_base/test_tombstone.py

"""Comprehensive test suite verifying TombstoneRecord invariants and lifecycles.

Operational Role:
    Verifies active and deprecated tombstone states, coupled timestamp guards,
    generic ID supersession binding, retirement helpers, and immutability.

Test Structure & Protocol:
    - Atomized tests: 1:1 behavioral contract mapping.
    - Fully decorated: Standard 7-marker taxonomy.
    - Zero production disk I/O.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from gda.model.atom.date import IsoTimestamp
from gda.model.atom.errors import AtomFormatError
from gda.model.atom.id import IndividualID
from gda.model.base.tombstone import TombstoneRecord

__version__ = "1.0.0+build.r3"


# ==============================================================================
# GROUP 1: ACTIVE RECORD INVARIANTS
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_tombstone_active_default_state() -> None:
    """Verify TombstoneRecord default instantiation represents an active record."""
    tb: TombstoneRecord[IndividualID] = TombstoneRecord()
    assert tb.is_deprecated is False
    assert tb.deprecated_at is None
    assert tb.superseded_by is None
    assert repr(tb) == "TombstoneRecord(is_deprecated=False)"


@pytest.mark.unit
@pytest.mark.regression
def test_tombstone_active_with_deprecated_timestamp_raises_error() -> None:
    """Verify active record raises AtomFormatError if deprecated_at is provided."""
    ts = IsoTimestamp("2026-10-16T12:00:00Z")
    with pytest.raises(
        AtomFormatError, match="must not possess a deprecated_at timestamp"
    ):
        TombstoneRecord(is_deprecated=False, deprecated_at=ts)


@pytest.mark.unit
@pytest.mark.regression
def test_tombstone_active_with_superseded_by_raises_error() -> None:
    """Verify active record raises AtomFormatError if superseded_by is provided."""
    target_id = IndividualID("IND-000002")
    with pytest.raises(
        AtomFormatError, match="must not possess a deprecated_at timestamp"
    ):
        TombstoneRecord(is_deprecated=False, superseded_by=target_id)


# ==============================================================================
# GROUP 2: DEPRECATED RECORD INVARIANTS & RETIREMENT
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_tombstone_deprecated_valid_states() -> None:
    """Verify deprecated record with timestamp and optional target ID."""
    ts = IsoTimestamp("2026-10-16T12:00:00Z")
    target_id = IndividualID("IND-000002")

    tb_discarded: TombstoneRecord[IndividualID] = TombstoneRecord(
        is_deprecated=True, deprecated_at=ts
    )
    assert tb_discarded.is_deprecated is True
    assert tb_discarded.deprecated_at == ts
    assert tb_discarded.superseded_by is None
    assert repr(tb_discarded) == (
        "TombstoneRecord(is_deprecated=True, deprecated_at=IsoTimestamp(value='2026-10-16T12:00:00Z'))"
    )

    tb_merged: TombstoneRecord[IndividualID] = TombstoneRecord(
        is_deprecated=True, deprecated_at=ts, superseded_by=target_id
    )
    assert tb_merged.superseded_by == target_id
    assert repr(tb_merged) == (
        "TombstoneRecord(is_deprecated=True, deprecated_at=IsoTimestamp(value='2026-10-16T12:00:00Z'), "
        "superseded_by=IndividualID(value='IND-000002'))"
    )


@pytest.mark.unit
@pytest.mark.regression
def test_tombstone_deprecated_missing_timestamp_raises_error() -> None:
    """Verify deprecated record raises AtomFormatError if deprecated_at is omitted."""
    with pytest.raises(AtomFormatError, match="must specify a deprecated_at timestamp"):
        TombstoneRecord(is_deprecated=True, deprecated_at=None)


@pytest.mark.unit
@pytest.mark.smoke
def test_tombstone_retire_helper() -> None:
    """Verify .retire() returns a new deprecated TombstoneRecord."""
    active: TombstoneRecord[IndividualID] = TombstoneRecord()
    ts = IsoTimestamp("2026-10-16T12:00:00Z")
    target = IndividualID("IND-000003")

    retired = active.retire(timestamp=ts, superseded_by=target)
    assert retired is not active
    assert active.is_deprecated is False
    assert retired.is_deprecated is True
    assert retired.deprecated_at == ts
    assert retired.superseded_by == target


# ==============================================================================
# GROUP 3: INTROSPECTION & IMMUTABILITY
# ==============================================================================


@pytest.mark.unit
def test_tombstone_immutability() -> None:
    """Verify TombstoneRecord is frozen and immutable."""
    tb: TombstoneRecord[IndividualID] = TombstoneRecord()
    with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
        tb.is_deprecated = True  # type: ignore[misc]


@pytest.mark.unit
def test_tombstone_introspection() -> None:
    """Verify .help() renders member directory on TombstoneRecord."""
    tb: TombstoneRecord[IndividualID] = TombstoneRecord()
    help_text = tb.help(as_str=True)
    assert help_text is not None
    assert "=== TombstoneRecord Public Directory ===" in help_text
    assert "retire" in help_text
