"""Path: tests/test_gda/test_model/test_base/test_entity.py

Comprehensive test suite verifying BaseEntity and BaseEntityGUID contracts.

Operational Role:
    Verifies that BaseEntity cleanly binds AtomID subclasses, BaseEntityGUID
    binds UUIDv4 surrogate strings, enforces matching superseded_by types,
    delegates audit and tombstone properties, and guarantees immutability.

Test Structure & Protocol:
    - Atomized tests: 1:1 behavioral contract mapping.
    - Fully decorated: Standard 7-marker taxonomy.
    - Zero production disk I/O.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import FactID, IndividualID, NoteID
from gda.model.base.audit import AuditStamp
from gda.model.base.entity import BaseEntity, BaseEntityGUID
from gda.model.base.tombstone import TombstoneRecord

__version__ = "1.0.0+build.2"


# ==============================================================================
# GROUP 1: BASEENTITY CREATION & DELEGATION
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_base_entity_default_creation() -> None:
    """Verify BaseEntity instantiates with default tombstone and empty notes."""
    eid = IndividualID("IND-000001")
    t1 = IsoTimestamp("2026-10-16T12:00:00Z")
    audit = AuditStamp(created_at=t1, updated_at=t1)

    entity: BaseEntity[IndividualID] = BaseEntity(id=eid, audit=audit)
    assert entity.id == eid
    assert entity.audit == audit
    assert entity.created_at == t1
    assert entity.updated_at == t1
    assert entity.is_deprecated is False
    assert entity.notes == []
    assert repr(entity) == (
        "BaseEntity(id=IndividualID(value='IND-000001'), "
        "audit=AuditStamp(created_at=IsoTimestamp(value='2026-10-16T12:00:00Z'), "
        "updated_at=IsoTimestamp(value='2026-10-16T12:00:00Z')), "
        "tombstone=TombstoneRecord(is_deprecated=False), notes=[])"
    )


@pytest.mark.unit
@pytest.mark.smoke
def test_base_entity_deprecated_with_notes() -> None:
    """Verify BaseEntity with deprecated tombstone and note references."""
    eid = IndividualID("IND-000001")
    t1 = IsoTimestamp("2026-10-16T12:00:00Z")
    t2 = IsoTimestamp("2026-10-16T15:00:00Z")
    audit = AuditStamp(created_at=t1, updated_at=t2)
    tombstone = TombstoneRecord[IndividualID](
        is_deprecated=True, deprecated_at=t2, superseded_by=IndividualID("IND-000002")
    )
    note_id = NoteID("NOT-000042")

    entity: BaseEntity[IndividualID] = BaseEntity(
        id=eid,
        audit=audit,
        tombstone=tombstone,
        notes=[note_id],
    )
    assert entity.is_deprecated is True
    assert entity.tombstone.deprecated_at == t2
    assert entity.tombstone.superseded_by == IndividualID("IND-000002")
    assert entity.notes == [note_id]


@pytest.mark.unit
@pytest.mark.regression
def test_base_entity_superseded_by_type_mismatch_raises_type_error() -> None:
    """Verify BaseEntity raises TypeError if superseded_by ID type conflicts with entity ID."""
    eid = IndividualID("IND-000001")
    t1 = IsoTimestamp("2026-10-16T12:00:00Z")
    audit = AuditStamp(created_at=t1, updated_at=t1)
    conflicting_target = FactID("FID-000002")

    tombstone = TombstoneRecord(
        is_deprecated=True,
        deprecated_at=t1,
        superseded_by=conflicting_target,  # type: ignore[arg-type]
    )

    with pytest.raises(TypeError, match="superseded_by type mismatch"):
        BaseEntity(id=eid, audit=audit, tombstone=tombstone)


# ==============================================================================
# GROUP 2: BASEENTITYGUID CREATION & PROPERTIES
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_base_entity_guid_valid_creation() -> None:
    """Verify BaseEntityGUID instantiates with string surrogate ID and delegates audit."""
    guid = "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"
    t1 = IsoTimestamp("2026-10-16T12:00:00Z")
    t2 = IsoTimestamp("2026-10-16T14:00:00Z")
    audit = AuditStamp(created_at=t1, updated_at=t2)

    entity = BaseEntityGUID(id=guid, audit=audit)
    assert entity.id == guid
    assert entity.audit == audit
    assert entity.created_at == t1
    assert entity.updated_at == t2
    assert entity.is_deprecated is False
    assert entity.notes == []
    assert repr(entity) == (
        "BaseEntityGUID(id='a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d', "
        "audit=AuditStamp(created_at=IsoTimestamp(value='2026-10-16T12:00:00Z'), "
        "updated_at=IsoTimestamp(value='2026-10-16T14:00:00Z')), "
        "tombstone=TombstoneRecord(is_deprecated=False), notes=[])"
    )


@pytest.mark.unit
@pytest.mark.smoke
def test_base_entity_guid_deprecated_with_superseded_by() -> None:
    """Verify BaseEntityGUID handles matching string superseded_by tombstone."""
    guid = "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"
    target_guid = "b2c3d4e5-f6a7-4b8c-9d0e-1f2a3b4c5d6e"
    t1 = IsoTimestamp("2026-10-16T12:00:00Z")
    audit = AuditStamp(created_at=t1, updated_at=t1)
    tombstone = TombstoneRecord[str](
        is_deprecated=True, deprecated_at=t1, superseded_by=target_guid
    )

    entity = BaseEntityGUID(id=guid, audit=audit, tombstone=tombstone)
    assert entity.is_deprecated is True
    assert entity.tombstone.superseded_by == target_guid


@pytest.mark.unit
@pytest.mark.regression
def test_base_entity_guid_superseded_by_type_mismatch_raises_type_error() -> None:
    """Verify BaseEntityGUID raises TypeError if superseded_by is not a string."""
    guid = "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"
    t1 = IsoTimestamp("2026-10-16T12:00:00Z")
    audit = AuditStamp(created_at=t1, updated_at=t1)
    wrong_target = IndividualID("IND-000002")

    tombstone = TombstoneRecord(
        is_deprecated=True,
        deprecated_at=t1,
        superseded_by=wrong_target,  # type: ignore[arg-type]
    )

    with pytest.raises(TypeError, match="superseded_by type mismatch: expected str"):
        BaseEntityGUID(id=guid, audit=audit, tombstone=tombstone)


# ==============================================================================
# GROUP 3: IMMUTABILITY & INTROSPECTION
# ==============================================================================


@pytest.mark.unit
def test_base_entity_immutability() -> None:
    """Verify BaseEntity and BaseEntityGUID instances are frozen and immutable."""
    eid = IndividualID("IND-000001")
    t1 = IsoTimestamp("2026-10-16T12:00:00Z")
    entity = BaseEntity(id=eid, audit=AuditStamp(created_at=t1, updated_at=t1))

    with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
        entity.notes = [NoteID("NOT-999999")]  # type: ignore[misc]

    guid_entity = BaseEntityGUID(
        id="guid-123", audit=AuditStamp(created_at=t1, updated_at=t1)
    )
    with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
        guid_entity.id = "guid-456"  # type: ignore[misc]


@pytest.mark.unit
def test_base_entity_introspection() -> None:
    """Verify .help() renders member directory on BaseEntity and BaseEntityGUID."""
    eid = IndividualID("IND-000001")
    t1 = IsoTimestamp("2026-10-16T12:00:00Z")
    entity = BaseEntity(id=eid, audit=AuditStamp(created_at=t1, updated_at=t1))

    help_text = entity.help(as_str=True)
    assert help_text is not None
    assert "=== BaseEntity Public Directory ===" in help_text
    assert "is_deprecated" in help_text

    guid_entity = BaseEntityGUID(
        id="guid-123", audit=AuditStamp(created_at=t1, updated_at=t1)
    )
    guid_help = guid_entity.help(as_str=True)
    assert guid_help is not None
    assert "=== BaseEntityGUID Public Directory ===" in guid_help
