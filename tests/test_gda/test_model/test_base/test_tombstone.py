"""Path: tests/test_gda/test_model/test_base/test_tombstone.py

Test harness for generic Tombstone lifecycle dataclass.
"""

from __future__ import annotations

import pytest

from gda.core.errors import ModelFormatError
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import IndividualID
from gda.model.base.tombstone import Tombstone

__version__ = "1.0.0+build.3"


# ==========================================================================
# GROUP 1: In-Memory Instantiation & Property Validation
# ==========================================================================


@pytest.mark.unit
def test_tombstone_instantiation_default_active_state():
    """Verify default initial state of an active, non-deprecated Tombstone."""
    tombstone: Tombstone[IndividualID] = Tombstone()
    assert tombstone.is_deprecated is False
    assert tombstone.deprecated_at is None
    assert tombstone.superseded_by is None
    assert repr(tombstone) == "Tombstone(is_deprecated=False)"


@pytest.mark.unit
def test_tombstone_auto_clears_fields_when_not_deprecated():
    """Verify active Tombstone auto-clears deprecated_at and superseded_by if passed."""
    tombstone: Tombstone[IndividualID] = Tombstone(
        is_deprecated=False,
        deprecated_at=IsoTimestamp("2026-01-01T00:00:00Z"),
        superseded_by=IndividualID("IND-0000000000000001"),
    )
    assert tombstone.is_deprecated is False
    assert tombstone.deprecated_at is None
    assert tombstone.superseded_by is None


@pytest.mark.unit
def test_tombstone_instantiation_deprecated_state():
    """Verify valid deprecated Tombstone retains timestamp and superseding pointer."""
    ts = IsoTimestamp("2026-05-01T12:00:00Z")
    target_id = IndividualID("IND-0000000000000002")

    tombstone: Tombstone[IndividualID] = Tombstone(
        is_deprecated=True,
        deprecated_at=ts,
        superseded_by=target_id,
    )
    assert tombstone.is_deprecated is True
    assert tombstone.deprecated_at == ts
    assert tombstone.superseded_by == target_id
    assert "superseded_by" in repr(tombstone)


# ==========================================================================
# GROUP 2: Defensive Errors & Retirement Lifecycle
# ==========================================================================


@pytest.mark.regression
def test_tombstone_deprecated_without_timestamp_raises_error():
    """Verify ModelFormatError is raised when is_deprecated=True has no timestamp."""
    with pytest.raises(ModelFormatError, match="must specify a deprecated_at timestamp"):
        Tombstone(is_deprecated=True, deprecated_at=None)


@pytest.mark.unit
def test_tombstone_retire_method():
    """Verify retire method returns an updated deprecated Tombstone instance."""
    active: Tombstone[IndividualID] = Tombstone()
    ts = IsoTimestamp("2026-06-15T08:30:00Z")
    target_id = IndividualID("IND-0000000000000099")

    retired = active.retire(timestamp=ts, superseded_by=target_id)
    assert retired.is_deprecated is True
    assert retired.deprecated_at == ts
    assert retired.superseded_by == target_id


@pytest.mark.unit
def test_tombstone_introspectable_help_callable():
    """Verify IntrospectableMixin .help() executes without raising exceptions."""
    tombstone: Tombstone[IndividualID] = Tombstone()
    tombstone.help()
