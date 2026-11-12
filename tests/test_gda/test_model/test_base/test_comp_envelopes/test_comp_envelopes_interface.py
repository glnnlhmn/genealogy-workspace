"""Path: tests/test_gda/test_model/test_base/test_comp_envelopes/test_comp_envelopes_interface.py

Public interface contract lock for Batch 3 composite and base entity envelopes.

Operational Role:
    Guards against accidental signature drift, field renames, or missing
    exports across gda.model.base.source, entity, envelope, and the unified
    gda.model.base package facade.
"""

from __future__ import annotations

import dataclasses

import pytest

import gda.model.base as base_pkg
import gda.model.base.entity as entity_mod
import gda.model.base.envelope as envelope_mod
import gda.model.base.source as source_mod
from gda.model.base.entity import BaseEntity, BaseEntityGUID
from gda.model.base.envelope import RegistryEnvelope
from gda.model.base.source import RecordMetadata, SourceRecord, SourceReference

__version__ = "1.0.0+build.1"

_SERIALIZATION_METHODS = ("create", "to_dict", "from_dict", "to_json", "from_json")


@pytest.mark.unit
@pytest.mark.regression
def test_comp_envelopes_module_exports_contract() -> None:
    """Verify __all__ exports on Batch 3 modules and unified gda.model.base facade."""
    assert source_mod.__all__ == ["RecordMetadata", "SourceRecord", "SourceReference"]
    assert entity_mod.__all__ == ["BaseEntity", "BaseEntityGUID", "EntityLifecycleMixin"]
    assert envelope_mod.__all__ == ["RegistryEnvelope"]

    expected_facade_all = [
        "Address",
        "Age",
        "AssociatedIndividual",
        "AuditStamp",
        "BaseEntity",
        "BaseEntityGUID",
        "CanonicalName",
        "ChildLink",
        "Coordinates",
        "DocumentSide",
        "EntityLifecycleMixin",
        "EventDate",
        "FamilyUnion",
        "HistoricVariant",
        "HistoricalName",
        "Legibility",
        "Media",
        "NameBase",
        "NameLifecycleMixin",
        "NamePerson",
        "NameThing",
        "Note",
        "RecordMetadata",
        "RegistryEnvelope",
        "SourceRecord",
        "SourceReference",
        "TextQuality",
        "TimePeriod",
        "Tombstone",
        "Transcript",
        "is_tombstoned",
        "stamp_tombstone",
    ]
    assert base_pkg.__all__ == expected_facade_all


@pytest.mark.unit
@pytest.mark.regression
def test_comp_envelopes_dataclass_fields_and_methods_contract() -> None:
    """Verify dataclass field ordering, properties, and public methods across Batch 3."""
    expected_fields: dict[type, list[str]] = {
        SourceReference: ["citation_text", "source_id", "page_or_side", "quay", "confidence"],
        RecordMetadata: [
            "source_id",
            "source_urn",
            "record_category",
            "record_type",
            "repository_id",
        ],
        SourceRecord: [
            "source_id",
            "source_urn",
            "record_category",
            "description",
            "repository_id",
            "audit",
            "media_ids",
            "associated_people",
            "tombstone",
        ],
        BaseEntity: ["id", "audit", "tombstone", "notes"],
        BaseEntityGUID: ["id", "audit", "tombstone", "notes"],
        RegistryEnvelope: ["schema_version", "last_modified", "total_count", "records"],
    }

    for cls, fields in expected_fields.items():
        assert dataclasses.is_dataclass(cls)
        assert [f.name for f in dataclasses.fields(cls)] == fields

    for serializable_cls in (SourceReference, RecordMetadata, SourceRecord):
        for method_name in _SERIALIZATION_METHODS:
            assert callable(getattr(serializable_cls, method_name))

    assert callable(RegistryEnvelope.create)
    assert isinstance(SourceRecord.is_deprecated, property)
    assert isinstance(SourceRecord.media_count, property)
    assert isinstance(SourceRecord.participant_count, property)
