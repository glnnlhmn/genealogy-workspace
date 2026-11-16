"""Path: tests/test_gda/test_model/test_base/test_base_contract.py

Authoritative public interface and contract verification suite for gda.model.base.

Operational Role:
    Freezes and validates the exact 15-submodule topology, 32-symbol package
    __all__ facade, submodule __all__ exports, frozen/extra='forbid' Pydantic
    dataclass invariants, IntrospectableMixin inheritance, dataclass field
    ordering, properties, and serialization method contracts across all
    Tier-1 and Tier-2 composite models and entity envelopes in gda.model.base.
"""

from __future__ import annotations

import dataclasses
import pkgutil

import pytest
from pydantic import ValidationError

import gda.model.base as base_pkg
import gda.model.base.address as address_mod
import gda.model.base.age as age_mod
import gda.model.base.association as association_mod
import gda.model.base.audit as audit_mod
import gda.model.base.date as date_mod
import gda.model.base.entity as entity_mod
import gda.model.base.envelope as envelope_mod
import gda.model.base.family as family_mod
import gda.model.base.geo as geo_mod
import gda.model.base.media as media_mod
import gda.model.base.name as name_mod
import gda.model.base.note as note_mod
import gda.model.base.source as source_mod
import gda.model.base.tombstone as tombstone_mod
import gda.model.base.transcript as transcript_mod
from gda.core.introspectable import IntrospectableMixin
from gda.model.base import (
    Address,
    Age,
    AssociatedIndividual,
    AuditStamp,
    BaseEntity,
    BaseEntityGUID,
    ChildLink,
    Coordinates,
    EventDate,
    FamilyUnion,
    HistoricVariant,
    Media,
    NameBase,
    NamePerson,
    NameThing,
    Note,
    RecordMetadata,
    RegistryEnvelope,
    SourceRecord,
    SourceReference,
    TimePeriod,
    Tombstone,
    Transcript,
)

__version__ = "1.0.0+build.4"

_EXPECTED_SUBMODULES = {
    "address",
    "age",
    "association",
    "audit",
    "date",
    "entity",
    "envelope",
    "family",
    "geo",
    "media",
    "name",
    "note",
    "source",
    "tombstone",
    "transcript",
}

AUTHORITATIVE_BASE_EXPORTS = [
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

_SERIALIZATION_METHODS = ("create", "to_dict", "from_dict", "to_json", "from_json")


@pytest.mark.unit
@pytest.mark.smoke
@pytest.mark.integrity
def test_base_package_submodule_topology_and_facade_exports() -> None:
    """Verify exact submodule set and sorted __all__ facade exports for gda.model.base."""
    discovered = {m.name for m in pkgutil.iter_modules(base_pkg.__path__)}
    assert discovered == _EXPECTED_SUBMODULES
    assert base_pkg.__all__ == AUTHORITATIVE_BASE_EXPORTS
    assert base_pkg.__all__ == sorted(base_pkg.__all__)
    assert len(base_pkg.__all__) == 32

    for symbol in AUTHORITATIVE_BASE_EXPORTS:
        assert hasattr(base_pkg, symbol), f"Missing exported symbol: {symbol}"


@pytest.mark.unit
@pytest.mark.integrity
def test_base_submodule_exports_contract() -> None:
    """Verify exact __all__ lists across all 15 gda.model.base submodules."""
    assert address_mod.__all__ == ["Address"]
    assert age_mod.__all__ == ["Age"]
    assert association_mod.__all__ == ["AssociatedIndividual"]
    assert audit_mod.__all__ == ["AuditStamp"]
    assert date_mod.__all__ == ["EventDate", "TimePeriod"]
    assert entity_mod.__all__ == ["BaseEntity", "BaseEntityGUID", "EntityLifecycleMixin"]
    assert envelope_mod.__all__ == ["RegistryEnvelope"]
    assert family_mod.__all__ == ["ChildLink", "FamilyUnion"]
    assert geo_mod.__all__ == ["Coordinates"]
    assert media_mod.__all__ == ["DocumentSide", "Media"]
    assert name_mod.__all__ == [
        "CanonicalName",
        "HistoricNameType",
        "HistoricVariant",
        "HistoricalName",
        "NameBase",
        "NameLifecycleMixin",
        "NamePerson",
        "NameThing",
    ]
    assert note_mod.__all__ == ["Note"]
    assert source_mod.__all__ == ["RecordMetadata", "SourceRecord", "SourceReference"]
    assert tombstone_mod.__all__ == ["Tombstone", "is_tombstoned", "stamp_tombstone"]
    assert transcript_mod.__all__ == ["Legibility", "TextQuality", "Transcript"]


@pytest.mark.unit
@pytest.mark.integrity
def test_all_base_dataclasses_enforce_frozen_extra_forbid_and_introspection() -> None:
    """Verify every dataclass exported by gda.model.base enforces frozen, extra='forbid', and IntrospectableMixin."""
    dataclass_types = [
        getattr(base_pkg, name)
        for name in AUTHORITATIVE_BASE_EXPORTS
        if isinstance(getattr(base_pkg, name), type)
        and dataclasses.is_dataclass(getattr(base_pkg, name))
    ]
    assert len(dataclass_types) == 25

    for cls in dataclass_types:
        assert issubclass(cls, IntrospectableMixin), (
            f"{cls.__name__} must inherit IntrospectableMixin"
        )
        params = cls.__dataclass_params__
        assert params.frozen is True, f"{cls.__name__} must be frozen=True"

        with pytest.raises(ValidationError):
            cls(__unexpected_forbid_probe__="bad")  # type: ignore[call-arg]


@pytest.mark.unit
@pytest.mark.integrity
def test_base_dataclass_fields_and_methods_contract() -> None:
    """Verify dataclass field ordering, properties, and public methods across gda.model.base."""
    expected_fields: dict[type, list[str]] = {
        Age: ["raw_text", "years", "months", "days"],
        AssociatedIndividual: [
            "role",
            "individual_id",
            "name_raw",
            "role_verbatim",
            "tertiary_roles",
            "residence",
            "comment",
        ],
        AuditStamp: ["created_at", "updated_at"],
        Coordinates: ["latitude", "longitude"],
        EventDate: ["date", "modifier", "end_date"],
        TimePeriod: ["start_date", "end_date"],
        Tombstone: ["is_deprecated", "deprecated_at", "superseded_by"],
        Address: [
            "address_line_1",
            "address_line_2",
            "city",
            "state",
            "postal_code",
            "coordinates",
        ],
        Note: ["note_id", "note_type", "text", "audit", "title", "sources", "tags"],
        Media: ["media_id", "file_name", "mime_type", "audit", "side", "description"],
        Transcript: [
            "transcript_id",
            "verbatim_text",
            "audit",
            "abstract",
            "keywords",
            "text_quality",
            "legibility",
        ],
        HistoricVariant: ["raw", "name", "historic_name_type", "valid_period", "comment"],
        NameBase: ["raw", "canonical", "aliases", "alt_spellings", "comment"],
        NamePerson: [
            "raw",
            "canonical",
            "aliases",
            "alt_spellings",
            "comment",
            "prefix",
            "given",
            "middle",
            "surname",
            "suffix",
            "married",
        ],
        NameThing: ["raw", "canonical", "aliases", "alt_spellings", "comment", "historic"],
        ChildLink: ["child_id", "pedigree"],
        FamilyUnion: ["union_type", "dissolution_type", "period"],
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

    for serializable_cls in (
        Address,
        Note,
        Media,
        Transcript,
        NamePerson,
        NameThing,
        ChildLink,
        FamilyUnion,
        SourceReference,
        RecordMetadata,
        SourceRecord,
    ):
        for method_name in _SERIALIZATION_METHODS:
            assert callable(getattr(serializable_cls, method_name))

    assert callable(RegistryEnvelope.create)
    assert isinstance(Address.formatted_address, property)
    assert isinstance(Note.value, property)
    assert isinstance(Transcript.word_count, property)
    assert isinstance(NamePerson.full_name, property)
    assert isinstance(SourceRecord.is_deprecated, property)
    assert isinstance(SourceRecord.media_count, property)
    assert isinstance(SourceRecord.participant_count, property)
