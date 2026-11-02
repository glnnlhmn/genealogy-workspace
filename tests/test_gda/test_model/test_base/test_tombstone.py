"""Path: tests/test_gda/test_model/test_base/test_tombstone.py

Unit and regression test suite for the generic Tombstone model.
"""

from __future__ import annotations

import pytest

from gda.core.errors import ModelFormatError
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import LocationID
from gda.model.base.tombstone import Tombstone

__version__ = "1.0.0+build.1"


# ==========================================================================
# GROUP 1: Invariant & Auto-Clearing Logic
# Note: Verifies default values, auto-clearing on active records, and guards.
# ==========================================================================


@pytest.mark.unit
def test_tombstone_default_initialization_is_active() -> None:
    """Verify default initialization produces an active record without timestamps."""
    tb = Tombstone[LocationID]()
    assert tb.is_deprecated is False
    assert tb.deprecated_at is None
    assert tb.superseded_by is None
    assert repr(tb) == "Tombstone(is_deprecated=False)"


@pytest.mark.unit
def test_tombstone_auto_clears_fields_when_active() -> None:
    """Verify active record with provided timestamps or superseded_by is auto-cleared."""
    now = IsoTimestamp.now_utc()
    target_id = LocationID("LOC-000002")

    tb = Tombstone[LocationID](
        is_deprecated=False,
        deprecated_at=now,
        superseded_by=target_id,
    )
    assert tb.is_deprecated is False
    assert tb.deprecated_at is None
    assert tb.superseded_by is None


@pytest.mark.regression
def test_tombstone_deprecated_without_timestamp_raises_model_format_error() -> None:
    """Verify deprecated tombstone missing deprecated_at raises ModelFormatError."""
    with pytest.raises(
        ModelFormatError, match="must specify a deprecated_at timestamp"
    ):
        Tombstone[LocationID](is_deprecated=True, deprecated_at=None)


# ==========================================================================
# GROUP 2: Lifecycle Retirement
# Note: Verifies retire method immutability and representation.
# ==========================================================================


@pytest.mark.unit
def test_tombstone_retire_returns_new_deprecated_instance() -> None:
    """Verify retire produces a new Tombstone instance stamped with target parameters."""
    active = Tombstone[LocationID]()
    now = IsoTimestamp.now_utc()
    target_id = LocationID("LOC-000002")

    retired = active.retire(timestamp=now, superseded_by=target_id)

    assert active.is_deprecated is False
    assert retired.is_deprecated is True
    assert retired.deprecated_at == now
    assert retired.superseded_by == target_id
    assert "superseded_by=" in repr(retired)
