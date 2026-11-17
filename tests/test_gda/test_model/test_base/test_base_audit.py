"""Path: tests/test_gda/test_model/test_base/test_base_audit.py

Comprehensive test suite for AuditStamp lifecycle dataclass and helpers.

Operational Role:
    Verifies AuditStamp creation, chronological ordering constraints, .now()
    and .touch() transitions, .to_dict()/.from_dict()/.to_json()/.from_json()
    serialization, and touch_audit / is_modified domain helpers with full
    statement and branch coverage.
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from gda.core.dates import validate_iso_timestamp
from gda.core.errors import ModelFormatError, ModelRangeError
from gda.model.atom.date import IsoTimestamp
from gda.model.base.audit import AuditStamp, is_modified, touch_audit

__version__ = "1.0.0+build.4"


@dataclass(frozen=True)
class _DummyAuditedEntity:
    """In-memory frozen dataclass carrier for testing audit helpers."""

    name: str
    audit: AuditStamp


@pytest.mark.unit
@pytest.mark.smoke
def test_audit_stamp_instantiation_and_representations(
    ts_created: IsoTimestamp,
    ts_updated: IsoTimestamp,
) -> None:
    """Verify AuditStamp stores timestamps and formats str/repr cleanly."""
    stamp = AuditStamp(created_at=ts_created, updated_at=ts_updated)
    assert stamp.created_at == ts_created
    assert stamp.updated_at == ts_updated
    assert str(stamp) == f"Created: {ts_created.value} | Updated: {ts_updated.value}"
    assert repr(stamp) == (
        f"AuditStamp(created_at='{ts_created.value}', updated_at='{ts_updated.value}')"
    )


@pytest.mark.unit
@pytest.mark.regression
def test_audit_stamp_updated_before_created_raises_range_error(
    ts_created: IsoTimestamp,
    ts_updated: IsoTimestamp,
) -> None:
    """Verify AuditStamp raises ModelRangeError if updated_at precedes created_at."""
    with pytest.raises(ModelRangeError, match="cannot precede created_at"):
        AuditStamp(created_at=ts_updated, updated_at=ts_created)


@pytest.mark.unit
def test_audit_stamp_now_and_touch_transitions(
    ts_created: IsoTimestamp,
    ts_updated: IsoTimestamp,
) -> None:
    """Verify AuditStamp.now() and .touch() transitions with default, str, and IsoTimestamp."""
    fresh = AuditStamp.now()
    assert fresh.created_at == fresh.updated_at
    assert validate_iso_timestamp(fresh.created_at.value) is True
    assert is_modified(fresh) is False

    base = AuditStamp(created_at=ts_created, updated_at=ts_created)
    touched_iso = base.touch(ts_updated)
    assert touched_iso.created_at == ts_created
    assert touched_iso.updated_at == ts_updated
    assert is_modified(touched_iso) is True

    touched_str = base.touch(ts_updated.value)
    assert touched_str.updated_at == ts_updated

    touched_auto = base.touch()
    assert validate_iso_timestamp(touched_auto.updated_at.value) is True


@pytest.mark.unit
def test_audit_stamp_dict_and_json_roundtrip(
    ts_created: IsoTimestamp,
    ts_updated: IsoTimestamp,
) -> None:
    """Verify AuditStamp.to_dict, from_dict, to_json, and from_json round-trip."""
    stamp = AuditStamp(created_at=ts_created, updated_at=ts_updated)
    assert AuditStamp.from_dict(stamp) is stamp

    d = stamp.to_dict()
    assert d == {"created_at": ts_created.value, "updated_at": ts_updated.value}
    assert AuditStamp.from_dict(d) == stamp
    assert AuditStamp.from_dict({"created_at": ts_created, "updated_at": ts_updated}) == stamp

    raw_json = stamp.to_json()
    assert AuditStamp.from_json(raw_json) == stamp

    with pytest.raises(ModelFormatError, match="expected dict"):
        AuditStamp.from_dict("not-a-dict")

    with pytest.raises(ModelFormatError, match="requires both"):
        AuditStamp.from_dict({"created_at": ts_created.value})

    with pytest.raises(ModelFormatError, match="expected str"):
        AuditStamp.from_json(123)  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="Invalid AuditStamp JSON"):
        AuditStamp.from_json("{bad_json")


@pytest.mark.unit
def test_touch_audit_and_is_modified_helpers(
    ts_created: IsoTimestamp,
    ts_updated: IsoTimestamp,
) -> None:
    """Verify touch_audit and is_modified operate on audited entities and reject invalid objects."""
    entity = _DummyAuditedEntity(
        name="Record",
        audit=AuditStamp(created_at=ts_created, updated_at=ts_created),
    )
    assert is_modified(entity) is False

    updated_entity = touch_audit(entity, ts_updated)
    assert updated_entity.audit.updated_at == ts_updated
    assert is_modified(updated_entity) is True

    with pytest.raises(AttributeError, match="does not have a valid 'audit'"):
        touch_audit(object())

    with pytest.raises(AttributeError, match="does not have a valid 'audit'"):
        is_modified(object())
