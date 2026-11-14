"""Path: tests/test_gda/test_model/test_manuscripts/test_manuscripts_contract.py

Public interface and structural contract tests for gda.model.manuscripts.

Operational Role:
    Locks down __all__ exports, SourceRecord inheritance, frozen dataclass
    immutability, authoritative field sets, category/record-type class constants,
    and public factory/serialization signatures across FamilyBibleRecord,
    BibleRegisterEntry, and NarrativeManuscriptRecord.
"""

from __future__ import annotations

import dataclasses
import inspect

import pytest

import gda.model.manuscripts as ms_pkg
from gda.core.enums.sources import SourceRecordCategory, SourceRecordType
from gda.model.base.source import SourceRecord
from gda.model.manuscripts import (
    BibleRegisterEntry,
    FamilyBibleRecord,
    NarrativeManuscriptRecord,
)

__version__ = "1.0.0+build.1"

_EXPECTED_EXPORTS: tuple[str, ...] = (
    "BibleRegisterEntry",
    "FamilyBibleRecord",
    "NarrativeManuscriptRecord",
)

_BASE_SOURCE_FIELDS: frozenset[str] = frozenset(
    {
        "source_id",
        "source_urn",
        "record_category",
        "record_type",
        "description",
        "repository_id",
        "audit",
        "media_ids",
        "associated_people",
        "tombstone",
    }
)


@pytest.mark.unit
@pytest.mark.integrity
def test_manuscripts_package_public_exports() -> None:
    """Verify gda.model.manuscripts.__all__ matches the exact locked export surface."""
    assert tuple(ms_pkg.__all__) == _EXPECTED_EXPORTS
    for symbol in _EXPECTED_EXPORTS:
        assert hasattr(ms_pkg, symbol)


@pytest.mark.unit
@pytest.mark.integrity
@pytest.mark.parametrize("record_cls", (FamilyBibleRecord, NarrativeManuscriptRecord))
def test_manuscripts_record_inheritance_immutability_and_methods(
    record_cls: type[SourceRecord],
) -> None:
    """Verify SourceRecord inheritance, frozen dataclass config, and core methods."""
    assert issubclass(record_cls, SourceRecord)
    assert dataclasses.is_dataclass(record_cls)
    assert record_cls.__dataclass_params__.frozen is True  # type: ignore[attr-defined]

    for method_name in ("create", "to_dict", "from_dict", "to_json", "from_json"):
        assert hasattr(record_cls, method_name)
        assert callable(getattr(record_cls, method_name))

    create_sig = inspect.signature(record_cls.create)
    for required_param in ("source_id", "source_urn", "description", "repository_id"):
        assert required_param in create_sig.parameters


@pytest.mark.unit
@pytest.mark.integrity
def test_bible_and_narrative_field_and_enum_contracts() -> None:
    """Lock down FamilyBibleRecord, BibleRegisterEntry, and NarrativeManuscriptRecord contracts."""
    assert dataclasses.is_dataclass(BibleRegisterEntry)
    assert BibleRegisterEntry.__dataclass_params__.frozen is True  # type: ignore[attr-defined]
    entry_fields = {f.name for f in dataclasses.fields(BibleRegisterEntry)}
    assert entry_fields == {
        "line_number",
        "event_type",
        "subject_name_raw",
        "subject_id",
        "secondary_name_raw",
        "secondary_id",
        "event_date",
        "place_raw",
        "place_id",
        "transcription_raw",
    }

    bible_fields = {f.name for f in dataclasses.fields(FamilyBibleRecord)}
    assert bible_fields == _BASE_SOURCE_FIELDS | {
        "family_surname",
        "edition_imprint",
        "publication_year",
        "original_owner_raw",
        "original_owner_id",
        "custodian_or_provenance",
        "entries",
    }
    assert FamilyBibleRecord.ALLOWED_CATEGORIES == frozenset(
        {
            SourceRecordCategory.MANUSCRIPT,
            SourceRecordCategory.VITAL,
            SourceRecordCategory.OTHER,
        }
    )
    assert FamilyBibleRecord.ALLOWED_RECORD_TYPES == frozenset(
        {
            SourceRecordType.BIBLE,
            SourceRecordType.BIBLE_RECORD,
        }
    )

    narr_fields = {f.name for f in dataclasses.fields(NarrativeManuscriptRecord)}
    assert narr_fields == _BASE_SOURCE_FIELDS | {
        "title_or_subject",
        "author_or_sender_raw",
        "author_or_sender_id",
        "recipient_raw",
        "recipient_id",
        "collection_name",
        "box_folder_or_page",
        "origin_place_raw",
        "origin_place_id",
        "destination_place_raw",
        "destination_place_id",
        "date_written_or_published",
        "transcript_excerpt",
    }
    assert NarrativeManuscriptRecord.ALLOWED_CATEGORIES == frozenset(
        {
            SourceRecordCategory.MANUSCRIPT,
            SourceRecordCategory.NARRATIVE,
            SourceRecordCategory.LEGAL,
            SourceRecordCategory.OTHER,
        }
    )
    assert NarrativeManuscriptRecord.ALLOWED_RECORD_TYPES == frozenset(
        {
            SourceRecordType.AFFIDAVIT,
            SourceRecordType.DEPOSITION,
            SourceRecordType.MEMOIR,
            SourceRecordType.ORAL_HISTORY,
            SourceRecordType.INTERVIEW_TRANSCRIPT,
            SourceRecordType.PERSONAL_LETTER,
            SourceRecordType.DIARY,
            SourceRecordType.CORRESP,
        }
    )
