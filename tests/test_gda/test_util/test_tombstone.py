"""Path: tests/test_gda/test_util/test_tombstone.py

Unit and regression test suite for domain-agnostic tombstone utilities.

Operational Role:
    Verifies pure stateless inspection and immutable deprecation stamping routines
    operating on domain entities bearing a Tombstone attribute.
"""

from __future__ import annotations

import dataclasses
from typing import Any

import pytest
from pydantic import BaseModel

from gda.enums.location import JurisdictionCategory
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import LocationID
from gda.model.base.audit import AuditStamp
from gda.model.base.name import NameThing
from gda.model.base.tombstone import Tombstone
from gda.model.entity.location import Location
from gda.util.tombstone import is_tombstoned, stamp_tombstone

__version__ = "1.0.0+build.8"


# ==============================================================================
# SYNTHETIC TEST FIXTURES & VALUE OBJECTS
# ==============================================================================


@dataclasses.dataclass(frozen=True)
class SyntheticCustomTombstone:
    """Synthetic dataclass tombstone bearing deprecation metadata."""

    is_deprecated: bool = False
    deprecated_at: IsoTimestamp | None = None
    superseded_by: str | None = None
    reason: str | None = None


@dataclasses.dataclass(frozen=True)
class SyntheticDataclassEntity:
    """Dataclass fixture bearing a synthetic tombstone attribute."""

    id: str
    tombstone: SyntheticCustomTombstone


class SyntheticPydanticTombstone(BaseModel):
    """Pydantic model tombstone that deliberately does NOT have a retire() method."""

    is_deprecated: bool = False
    deprecated_at: IsoTimestamp | None = None
    superseded_by: str | None = None


class SyntheticPydanticEntity(BaseModel):
    """Pydantic entity holding a SyntheticPydanticTombstone."""

    id: str
    tombstone: SyntheticPydanticTombstone


class SyntheticEntityWithPlainTombstone:
    """Entity whose tombstone lacks retire/model_copy and is not a dataclass."""

    def __init__(self, id_val: str, tombstone: Any) -> None:
        self.id = id_val
        self.tombstone = tombstone

    def model_copy(
        self, update: dict[str, Any] | None = None
    ) -> SyntheticEntityWithPlainTombstone:
        new_tomb = update.get("tombstone") if update else self.tombstone
        return SyntheticEntityWithPlainTombstone(self.id, new_tomb)


class SyntheticUnsupportedEntity:
    """Plain class fixture lacking both model_copy and dataclass mechanics."""

    def __init__(self, id_val: str, tombstone: Any) -> None:
        self.id = id_val
        self.tombstone = tombstone


@pytest.fixture
def active_location() -> Location:
    """Provide a fresh active Location fixture."""
    now = IsoTimestamp.now_utc()
    return Location(
        id=LocationID("LOC-000001"),
        audit=AuditStamp(created_at=now, updated_at=now),
        name=NameThing.create(raw="United States", canonical="United States"),
        category=JurisdictionCategory.COUNTRY,
        canonical_urn="urn:gda:loc:united_states",
        tombstone=Tombstone[LocationID](),
    )


# ==============================================================================
# GROUP 1: TOMBSTONE STATE INSPECTION (is_tombstoned)
# ==============================================================================


@pytest.mark.unit
def test_is_tombstoned_returns_false_for_active_and_true_for_deprecated(
    active_location: Location,
) -> None:
    """Verify is_tombstoned correctly evaluates active vs retired entities."""
    assert is_tombstoned(active_location) is False

    retired = stamp_tombstone(active_location, reason="Obsolete jurisdiction tier")
    assert is_tombstoned(retired) is True


@pytest.mark.unit
def test_is_tombstoned_returns_false_when_tombstone_attr_missing() -> None:
    """Verify is_tombstoned safely returns False for entities lacking a tombstone attribute."""
    assert is_tombstoned("not_an_entity") is False
    assert is_tombstoned({"key": "val"}) is False
    assert is_tombstoned(None) is False


# ==============================================================================
# GROUP 2: IMMUTABLE TOMBSTONE STAMPING (stamp_tombstone)
# ==============================================================================


@pytest.mark.unit
def test_stamp_tombstone_preserves_original_and_returns_new_instance(
    active_location: Location,
) -> None:
    """Verify stamping preserves original instance immutability and returns a distinct copy."""
    replacement_id = LocationID("LOC-000002")
    timestamp = IsoTimestamp.now_utc()

    retired = stamp_tombstone(
        entity=active_location,
        reason="Absorbed into neighbouring parish",
        deprecated_at=timestamp,
        superseded_by=replacement_id,
    )

    assert active_location.tombstone.is_deprecated is False
    assert active_location.tombstone.superseded_by is None

    assert retired is not active_location
    assert retired.tombstone.is_deprecated is True
    assert retired.tombstone.deprecated_at == timestamp
    assert retired.tombstone.superseded_by == replacement_id


@pytest.mark.unit
def test_stamp_tombstone_supports_pydantic_model_copy_without_retire() -> None:
    """Verify stamping falls back to model_copy when tombstone lacks retire()."""
    p_tomb = SyntheticPydanticTombstone(is_deprecated=False)
    p_entity = SyntheticPydanticEntity(id="PY-01", tombstone=p_tomb)

    retired = stamp_tombstone(p_entity, reason="Pydantic copy test")
    assert retired.tombstone.is_deprecated is True
    assert retired.tombstone.superseded_by is None
    assert p_entity.tombstone.is_deprecated is False


@pytest.mark.unit
def test_stamp_tombstone_supports_dataclass_entities_with_and_without_reason() -> None:
    """Verify stamping handles dataclass records with reason and reason=None."""
    initial = SyntheticDataclassEntity(
        id="SYN-01",
        tombstone=SyntheticCustomTombstone(is_deprecated=False),
    )
    assert is_tombstoned(initial) is False

    updated_with_reason = stamp_tombstone(initial, reason="Dataclass deprecation")
    assert is_tombstoned(updated_with_reason) is True
    assert updated_with_reason.tombstone.reason == "Dataclass deprecation"
    assert updated_with_reason.id == "SYN-01"

    updated_without_reason = stamp_tombstone(initial, reason=None)
    assert is_tombstoned(updated_without_reason) is True
    assert updated_without_reason.tombstone.reason is None


@pytest.mark.unit
def test_stamp_tombstone_falls_back_to_default_tombstone_for_plain_object() -> None:
    """Verify stamping creates fresh Tombstone when target has plain object (covers Line 71)."""
    plain_entity = SyntheticEntityWithPlainTombstone("ID-01", object())
    updated = stamp_tombstone(plain_entity, reason="Fallback test")

    assert is_tombstoned(updated) is True
    assert isinstance(updated.tombstone, Tombstone)
    assert updated.tombstone.is_deprecated is True


@pytest.mark.regression
def test_stamp_tombstone_missing_tombstone_raises_attribute_error() -> None:
    """Verify entities missing the tombstone attribute raise AttributeError."""
    with pytest.raises(AttributeError, match="lacks a 'tombstone' attribute"):
        stamp_tombstone("plain_string", reason="Invalid target")


@pytest.mark.regression
def test_stamp_tombstone_unsupported_copy_mechanisms_raises_type_error() -> None:
    """Verify objects lacking copy mechanisms raise TypeError."""
    unsupported = SyntheticUnsupportedEntity(
        "ID-99", SyntheticCustomTombstone(is_deprecated=False)
    )
    with pytest.raises(TypeError, match="does not support immutable copy mechanisms"):
        stamp_tombstone(unsupported, reason="Cannot copy")
