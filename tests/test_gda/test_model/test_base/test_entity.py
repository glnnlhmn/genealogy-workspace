# Name: test_entity.py
# Path: tests/test_gda/test_model/test_base/test_entity.py

"""Comprehensive test suite verifying generic EntityModel assembly and delegation.

Operational Role:
    Verifies that EntityModel cleanly binds AtomID subclasses (IndividualID, FactID),
    inherits AuditableModel properties, enforces matching superseded_by types,
    delegates tombstone state, and guarantees immutability.

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
from gda.model.base.entity import EntityModel
from gda.model.base.tombstone import TombstoneRecord

__version__ = "1.0.0+build.r4"


# ==============================================================================
# GROUP 1: ENTITYMODEL CREATION & DELEGATION
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_entity_model_default_creation() -> None:
    """Verify EntityModel instantiates with default tombstone and empty notes."""
    eid = IndividualID("IND-000001")
    t1 = IsoTimestamp("2026-10-16T12:00:00Z")
    audit = AuditStamp(created_at=t1, updated_at=t1)

    entity: EntityModel[IndividualID] = EntityModel(id=eid, audit=audit)
    assert entity.id == eid
    assert entity.audit == audit
    assert entity.created_at == t1
    assert entity.updated_at == t1
    assert entity.tombstone.is_deprecated is False
    assert entity.is_deprecated is False
    assert entity.notes == []
    assert repr(entity) == (
        "EntityModel(id=IndividualID(value='IND-000001'), "
        "audit=AuditStamp(created_at=IsoTimestamp(value='2026-10-16T12:00:00Z'), "
        "updated_at=IsoTimestamp(value='2026-10-16T12:00:00Z')), "
        "tombstone=TombstoneRecord(is_deprecated=False), notes=[])"
    )


@pytest.mark.unit
@pytest.mark.smoke
def test_entity_model_with_fact_id() -> None:
    """Verify EntityModel cleanly parameterizes with FactID."""
    fid = FactID("FID-000001")
    t1 = IsoTimestamp("2026-10-16T12:00:00Z")
    audit = AuditStamp(created_at=t1, updated_at=t1)

    entity: EntityModel[FactID] = EntityModel(id=fid, audit=audit)
    assert entity.id == fid
    assert entity.id.prefix == "FID"


@pytest.mark.unit
@pytest.mark.smoke
def test_entity_model_deprecated_with_notes() -> None:
    """Verify EntityModel with deprecated tombstone and populated NoteIDs."""
    eid = IndividualID("IND-000001")
    t1 = IsoTimestamp("2026-10-16T12:00:00Z")
    t2 = IsoTimestamp("2026-10-16T15:00:00Z")
    audit = AuditStamp(created_at=t1, updated_at=t2)
    tombstone = TombstoneRecord[IndividualID](
        is_deprecated=True, deprecated_at=t2, superseded_by=IndividualID("IND-000002")
    )
    note_id = NoteID("NOT-000042")

    entity: EntityModel[IndividualID] = EntityModel(
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
def test_entity_model_superseded_by_type_mismatch_raises_type_error() -> None:
    """Verify EntityModel raises TypeError if superseded_by ID type conflicts with entity ID."""
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
        EntityModel(id=eid, audit=audit, tombstone=tombstone)


# ==============================================================================
# GROUP 2: IMMUTABILITY & INTROSPECTION
# ==============================================================================


@pytest.mark.unit
def test_entity_model_immutability() -> None:
    """Verify EntityModel is frozen and immutable."""
    eid = IndividualID("IND-000001")
    t1 = IsoTimestamp("2026-10-16T12:00:00Z")
    audit = AuditStamp(created_at=t1, updated_at=t1)

    entity: EntityModel[IndividualID] = EntityModel(id=eid, audit=audit)
    with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
        entity.notes = [NoteID("NOT-999999")]  # type: ignore[misc]


@pytest.mark.unit
def test_entity_model_introspection() -> None:
    """Verify .help() renders member directory on EntityModel."""
    eid = IndividualID("IND-000001")
    t1 = IsoTimestamp("2026-10-16T12:00:00Z")
    audit = AuditStamp(created_at=t1, updated_at=t1)

    entity: EntityModel[IndividualID] = EntityModel(id=eid, audit=audit)
    help_text = entity.help(as_str=True)
    assert help_text is not None
    assert "=== EntityModel Public Directory ===" in help_text
    assert "is_deprecated" in help_text
