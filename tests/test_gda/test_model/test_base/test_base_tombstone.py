"""Path: tests/test_gda/test_model/test_base/test_base_tombstone.py

Comprehensive test suite for generic Tombstone lifecycle dataclass and helpers.

Operational Role:
    Verifies Tombstone instantiation invariants, explicit rejection of active
    tombstones carrying deprecation metadata, .retire() transitions,
    .to_dict()/.from_dict()/.to_json()/.from_json() serialization, and the
    is_tombstoned / stamp_tombstone domain helpers with 100% statement and
    branch coverage.
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from gda.core.dates import validate_iso_timestamp
from gda.core.errors import ModelFormatError
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import IndividualID
from gda.model.base.tombstone import Tombstone, is_tombstoned, stamp_tombstone

__version__ = "1.0.0+build.2"


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
    assert tombstone_no_target.is_deprecated is True
    assert str(tombstone_no_target) == f"Deprecated at {ts_created.value}"
    assert repr(tombstone_no_target) == (
        f"Tombstone(is_deprecated=True, deprecated_at='{ts_created.value}', superseded_by=None)"
    )

    tombstone_with_target: Tombstone[IndividualID] = Tombstone(
        is_deprecated=True,
        deprecated_at=ts_created,
        superseded_by=sample_individual_id,
    )
    assert str(tombstone_with_target) == (
        f"Deprecated at {ts_created.value} (Superseded by {sample_individual_id.value})"
    )
    assert repr(tombstone_with_target) == (
        f"Tombstone(is_deprecated=True, deprecated_at='{ts_created.value}', "
        f"superseded_by='{sample_individual_id.value}')"
    )

    tombstone_no_dt: Tombstone[IndividualID] = Tombstone(is_deprecated=True)
    assert str(tombstone_no_dt) == "Deprecated at Unknown"


# ==============================================================================
# GROUP 2: RETIREMENT TRANSITIONS & SERIALIZATION
# ==============================================================================


@pytest.mark.unit
def test_tombstone_retire_transitions(
    ts_created: IsoTimestamp,
    sample_individual_id: IndividualID,
) -> None:
    """Verify .retire() transitions active Tombstone and rejects double retirement."""
    active: Tombstone[IndividualID] = Tombstone()

    retired_auto = active.retire()
    assert retired_auto.is_deprecated is True
    assert retired_auto.deprecated_at is not None
    assert validate_iso_timestamp(retired_auto.deprecated_at.value) is True

    retired_str = active.retire(
        superseded_by=sample_individual_id,
        timestamp=ts_created.value,
    )
    assert retired_str.deprecated_at == ts_created
    assert retired_str.superseded_by == sample_individual_id

    retired_iso = active.retire(timestamp=ts_created)
    assert retired_iso.deprecated_at == ts_created

    with pytest.raises(ModelFormatError, match="already deprecated"):
        retired_iso.retire()


@pytest.mark.unit
def test_tombstone_dict_and_json_roundtrip(
    ts_created: IsoTimestamp,
    sample_individual_id: IndividualID,
) -> None:
    """Verify Tombstone.to_dict, from_dict, to_json, and from_json round-trip."""
    active: Tombstone[IndividualID] = Tombstone()
    assert Tombstone.from_dict(active) is active
    assert active.to_dict() == {
        "is_deprecated": False,
        "deprecated_at": None,
        "superseded_by": None,
    }
    assert Tombstone.from_dict(active.to_dict()) == active

    dep: Tombstone[IndividualID] = Tombstone(
        is_deprecated=True,
        deprecated_at=ts_created,
        superseded_by=sample_individual_id,
    )
    d = dep.to_dict()
    assert d == {
        "is_deprecated": True,
        "deprecated_at": ts_created.value,
        "superseded_by": sample_individual_id.value,
    }
    assert Tombstone.from_dict(d, id_cls=IndividualID) == dep
    assert (
        Tombstone.from_dict(
            {
                "is_deprecated": True,
                "deprecated_at": ts_created,
                "superseded_by": sample_individual_id,
            }
        )
        == dep
    )
    assert Tombstone.from_json(dep.to_json(), id_cls=IndividualID) == dep

    with pytest.raises(ModelFormatError, match="expected dict"):
        Tombstone.from_dict("not-a-dict")

    with pytest.raises(ModelFormatError, match="must be a boolean"):
        Tombstone.from_dict({"is_deprecated": "yes"})

    with pytest.raises(ModelFormatError, match="Invalid Tombstone 'deprecated_at'"):
        Tombstone.from_dict({"is_deprecated": True, "deprecated_at": 123})

    with pytest.raises(ModelFormatError, match="requires an id_cls wrapper"):
        Tombstone.from_dict({"is_deprecated": True, "superseded_by": "IND-000001"})

    with pytest.raises(ModelFormatError, match="expected str"):
        Tombstone.from_json(123)  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="Invalid Tombstone JSON"):
        Tombstone.from_json("{bad")


# ==============================================================================
# GROUP 3: STRUCTURAL DOMAIN HELPERS (stamp_tombstone, is_tombstoned)
# ==============================================================================


@pytest.mark.unit
def test_stamp_tombstone_and_is_tombstoned_helpers(
    ts_created: IsoTimestamp,
    sample_individual_id: IndividualID,
) -> None:
    """Verify stamp_tombstone and is_tombstoned operate on entities and reject invalid objects."""
    target_id = IndividualID("IND-000002")
    entity = _DummyEntity(id=sample_individual_id, tombstone=Tombstone())
    assert is_tombstoned(entity) is False
    assert is_tombstoned(entity.tombstone) is False

    retired_entity = stamp_tombstone(entity, superseded_by=target_id, timestamp=ts_created)
    assert is_tombstoned(retired_entity) is True
    assert retired_entity.tombstone.superseded_by == target_id
    assert retired_entity.tombstone.deprecated_at == ts_created

    with pytest.raises(AttributeError, match="does not have a valid 'tombstone'"):
        stamp_tombstone(object())

    with pytest.raises(AttributeError, match="does not have a valid 'tombstone'"):
        is_tombstoned(object())
