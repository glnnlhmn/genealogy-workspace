"""Path: tests/test_gda/test_model/test_base/test_composites/test_composites_interface.py

Public interface contract lock for Batch 2 composite value objects.

Operational Role:
    Guards against accidental signature drift, field renames, or missing
    exports across gda.model.base.address, note, media, transcript, name,
    and family so downstream Tier-2 composites and entities remain stable.
"""

from __future__ import annotations

import dataclasses

import pytest

import gda.model.base as base_pkg
import gda.model.base.address as address_mod
import gda.model.base.family as family_mod
import gda.model.base.media as media_mod
import gda.model.base.name as name_mod
import gda.model.base.note as note_mod
import gda.model.base.transcript as transcript_mod
from gda.model.base.address import Address
from gda.model.base.family import ChildLink, FamilyUnion
from gda.model.base.media import Media
from gda.model.base.name import HistoricVariant, NameBase, NamePerson, NameThing
from gda.model.base.note import Note
from gda.model.base.transcript import Transcript

__version__ = "1.0.0+build.1"

_SERIALIZATION_METHODS = ("create", "to_dict", "from_dict", "to_json", "from_json")


@pytest.mark.unit
@pytest.mark.regression
def test_composites_module_exports_contract() -> None:
    """Verify __all__ exports on each Batch 2 module and gda.model.base facade."""
    assert address_mod.__all__ == ["Address"]
    assert note_mod.__all__ == ["Note"]
    assert media_mod.__all__ == ["DocumentSide", "Media"]
    assert transcript_mod.__all__ == ["Legibility", "TextQuality", "Transcript"]
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
    assert family_mod.__all__ == ["ChildLink", "FamilyUnion"]

    expected_facade_symbols = {
        "Address",
        "ChildLink",
        "DocumentSide",
        "FamilyUnion",
        "HistoricVariant",
        "CanonicalName",
        "HistoricalName",
        "Legibility",
        "Media",
        "NameBase",
        "NameLifecycleMixin",
        "NamePerson",
        "NameThing",
        "Note",
        "TextQuality",
        "Transcript",
    }
    assert expected_facade_symbols.issubset(set(base_pkg.__all__))


@pytest.mark.unit
@pytest.mark.regression
def test_composites_dataclass_fields_and_methods_contract() -> None:
    """Verify dataclass field ordering, properties, and public methods across Batch 2."""
    expected_fields: dict[type, list[str]] = {
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
    ):
        for method_name in _SERIALIZATION_METHODS:
            assert callable(getattr(serializable_cls, method_name))

    assert isinstance(Address.formatted_address, property)
    assert isinstance(Note.value, property)
    assert isinstance(Transcript.word_count, property)
    assert isinstance(NamePerson.full_name, property)
