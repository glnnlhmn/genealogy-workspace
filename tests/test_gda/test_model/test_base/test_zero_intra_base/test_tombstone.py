"""Path: tests/test_gda/test_model/test_base/test_zero_intra_base/test_tombstone.py

Comprehensive test suite for generic Tombstone lifecycle dataclass and helpers.

Operational Role:
    Verifies Tombstone instantiation invariants, explicit rejection of active
    tombstones carrying deprecation metadata, .retire() transitions, and the
    is_tombstoned / stamp_tombstone domain helpers with 100% statement and
    branch coverage.
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest
from pydantic import ValidationError

from gda.core.dates import validate_iso_timestamp
from gda.core.errors import ModelFormatError
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import IndividualID
from gda.model.base.tombstone import Tombstone, is_tombstoned, stamp_tombstone

__version__ = "1.1.0+build.1"


@dataclass(frozen=True)
class _DummyEntity:
    """In-memory frozen dataclass carrier for testing tombstone helpers."""

    id: IndividualID
    tombstone: Tombstone[IndividualID]


# ==============================================================================
# GROUP 1: IN-MEMORY INSTANTIATION & PROPERTY VALIDATION
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_tombstone_instantiation_default_active_state() -> None:
    """Verify default initial state of an active, non-deprecated Tombstone."""
    tombstone: Tombstone[IndividualID] = Tombstone()
    assert tombstone.is_deprecated is False
    assert tombstone.deprecated_at is None
    assert tombstone.superseded_by is None
    assert str(tombstone) == "Active"
    assert repr(tombstone) == "Tombstone(is_deprecated=False)"


@pytest.mark.unit
@pytest.mark.regression
def test_tombstone_active_with_deprecation_metadata_raises_error(
    ts_created: IsoTimestamp,
    sample_individual_id: IndividualID,
) -> None:
    """Verify active Tombstone raises ModelFormatError if deprecated_at or superseded_by is set."""
    with pytest.raises(ModelFormatError, match="cannot specify deprecated_at or superseded_by"):
        Tombstone(is_deprecated=False, deprecated_at=ts_created)

    with pytest.raises(ModelFormatError, match="cannot specify deprecated_at or superseded_by"):
        Tombstone(is_deprecated=False, superseded_by=sample_individual_id)


@pytest.mark.unit
@pytest.mark.smoke
def test_tombstone_instantiation_deprecated_state(
    ts_created: IsoTimestamp,
    sample_individual_id: IndividualID,
) -> None:
    """Verify valid deprecated Tombstone retains timestamp and superseding pointer."""
    tombstone_no_target: Tombstone[IndividualID] = Tombstone(
        is_deprecated=True,
        deprecated_at=ts_created,
    )
    assert str(tombstone_no_target) == "Deprecated (2026-10-16T10:00:00Z)"
    assert repr(tombstone_no_target) == (
        "Tombstone(is_deprecated=True, deprecated_at=IsoTimestamp(value='2026-10-16T10:00:00Z'))"
    )

    tombstone_with_target: Tombstone[IndividualID] = Tombstone(
        is_deprecated=True,
        deprecated_at=ts_created,
        superseded_by=sample_individual_id,
    )
    assert tombstone_with_target.is_deprecated is True
    assert tombstone_with_target.deprecated_at == ts_created
    assert tombstone_with_target.superseded_by == sample_individual_id
    assert str(tombstone_with_target) == "Deprecated (2026-10-16T10:00:00Z -> IND-000101)"
    assert "superseded_by=IndividualID(value='IND-000101')" in repr(tombstone_with_target)


@pytest.mark.unit
@pytest.mark.regression
def test_tombstone_strict_mode_rejects_int_for_bool() -> None:
    """Verify strict=True rejects integer 1 or 0 for is_deprecated."""
    with pytest.raises(ValidationError):
        Tombstone(is_deprecated=1)  # type: ignore[arg-type]


# ==============================================================================
# GROUP 2: DEFENSIVE ERRORS, RETIREMENT & ENTITY HELPERS
# ==============================================================================


@pytest.mark.unit
@pytest.mark.regression
def test_tombstone_deprecated_without_timestamp_raises_error() -> None:
    """Verify ModelFormatError is raised when is_deprecated=True has no timestamp."""
    with pytest.raises(ModelFormatError, match="must specify a deprecated_at timestamp"):
        Tombstone(is_deprecated=True, deprecated_at=None)


@pytest.mark.unit
@pytest.mark.smoke
def test_tombstone_retire_method(
    ts_updated: IsoTimestamp,
    sample_individual_id: IndividualID,
) -> None:
    """Verify retire() returns an updated deprecated Tombstone with explicit or current UTC timestamp."""
    active: Tombstone[IndividualID] = Tombstone()

    retired_explicit = active.retire(timestamp=ts_updated, superseded_by=sample_individual_id)
    assert retired_explicit.is_deprecated is True
    assert retired_explicit.deprecated_at == ts_updated
    assert retired_explicit.superseded_by == sample_individual_id

    retired_now = active.retire()
    assert retired_now.is_deprecated is True
    assert retired_now.deprecated_at is not None
    assert validate_iso_timestamp(retired_now.deprecated_at.value) is True


@pytest.mark.unit
def test_tombstone_entity_helpers(
    sample_individual_id: IndividualID,
    ts_updated: IsoTimestamp,
) -> None:
    """Verify is_tombstoned() and stamp_tombstone() across valid and invalid carriers."""
    assert is_tombstoned(object()) is False

    entity = _DummyEntity(id=sample_individual_id, tombstone=Tombstone())
    assert is_tombstoned(entity) is False

    target_id = IndividualID("IND-000999")
    stamped = stamp_tombstone(entity, deprecated_at=ts_updated, superseded_by=target_id)
    assert is_tombstoned(stamped) is True
    assert stamped.tombstone.deprecated_at == ts_updated
    assert stamped.tombstone.superseded_by == target_id

    stamped_now = stamp_tombstone(entity)
    assert is_tombstoned(stamped_now) is True

    with pytest.raises(AttributeError, match="lacks a 'tombstone' attribute"):
        stamp_tombstone(object())

    class _NonDataclassCarrier:
        tombstone = Tombstone()

    with pytest.raises(TypeError, match="must be an immutable dataclass instance"):
        stamp_tombstone(_NonDataclassCarrier())


@pytest.mark.unit
def test_tombstone_introspectable_help_callable() -> None:
    """Verify IntrospectableMixin .help() executes without raising exceptions."""
    tombstone: Tombstone[IndividualID] = Tombstone()
    assert tombstone.help(as_str=True) is not None
