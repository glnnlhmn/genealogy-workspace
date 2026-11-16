"""Path: tests/test_gda/test_model/test_source/test_publications/test_publications_contract.py

Public interface and structural contract tests for gda.model.source.publications.

Operational Role:
    Locks down __all__ exports, SourceRecord inheritance, frozen dataclass
    immutability, authoritative field sets, category/record-type class constants,
    and public factory/serialization signatures across Publication,
    NewspaperClipRecord, PeriodicalArticleRecord, and PublicationEntry to prevent
    accidental breaking interface drift.
"""

from __future__ import annotations

import dataclasses
import inspect

import pytest

import gda.model.source.publications as pub_pkg
from gda.core.enums.sources import SourceRecordCategory, SourceRecordType
from gda.model.base.source import SourceRecord
from gda.model.source.publications import (
    NewspaperClipRecord,
    PeriodicalArticleRecord,
    Publication,
    PublicationEntry,
)

__version__ = "1.0.0+build.1"

_EXPECTED_EXPORTS: tuple[str, ...] = (
    "NewspaperClipRecord",
    "PeriodicalArticleRecord",
    "Publication",
    "PublicationEntry",
)

_PUBLICATION_SOURCE_CLASSES: tuple[type[SourceRecord], ...] = (
    Publication,
    NewspaperClipRecord,
    PeriodicalArticleRecord,
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
def test_publications_package_public_exports() -> None:
    """Verify gda.model.source.publications.__all__ matches the exact locked export surface."""
    assert tuple(pub_pkg.__all__) == _EXPECTED_EXPORTS
    for symbol in _EXPECTED_EXPORTS:
        assert hasattr(pub_pkg, symbol)


@pytest.mark.unit
@pytest.mark.integrity
@pytest.mark.parametrize("record_cls", _PUBLICATION_SOURCE_CLASSES)
def test_publications_record_inheritance_immutability_and_methods(
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
def test_publication_field_and_enum_contract() -> None:
    """Lock down Publication fields and allowed SourceRecordCategory tokens."""
    field_names = {f.name for f in dataclasses.fields(Publication)}
    expected_fields = _BASE_SOURCE_FIELDS | {
        "title",
        "pub_code",
        "frequency",
        "publisher_raw",
        "place_of_publication_raw",
        "location_id",
        "publication_period",
        "issn_or_lccn",
        "is_active",
    }
    assert field_names == expected_fields
    assert Publication.ALLOWED_CATEGORIES == frozenset(
        {
            SourceRecordCategory.NEWS,
            SourceRecordCategory.EDUCATION,
            SourceRecordCategory.DIRECTORY,
            SourceRecordCategory.NARRATIVE,
            SourceRecordCategory.OTHER,
        }
    )


@pytest.mark.unit
@pytest.mark.integrity
def test_newspaper_clip_record_field_and_enum_contract() -> None:
    """Lock down NewspaperClipRecord fields and allowed category/record_type tokens."""
    field_names = {f.name for f in dataclasses.fields(NewspaperClipRecord)}
    expected_fields = _BASE_SOURCE_FIELDS | {
        "newspaper_name_raw",
        "issue_date",
        "news_category",
        "parent_source_id",
        "pub_code",
        "publication_location_raw",
        "publication_location_id",
        "headline_raw",
        "byline_raw",
        "volume_issue",
        "page_column",
        "edition",
        "article_summary",
    }
    assert field_names == expected_fields
    assert NewspaperClipRecord.ALLOWED_CATEGORIES == frozenset(
        {
            SourceRecordCategory.NEWS,
            SourceRecordCategory.VITAL,
            SourceRecordCategory.LEGAL,
            SourceRecordCategory.OTHER,
        }
    )
    assert NewspaperClipRecord.ALLOWED_RECORD_TYPES == frozenset(
        {
            SourceRecordType.MISC,
            SourceRecordType.AFFIDAVIT,
            SourceRecordType.DOCKET_ENTRY,
            SourceRecordType.DEATH_CERTIFICATE,
            SourceRecordType.MARRIAGE_LICENSE,
            SourceRecordType.BIRTH_CERTIFICATE,
        }
    )


@pytest.mark.unit
@pytest.mark.integrity
def test_periodical_and_entry_field_and_enum_contract() -> None:
    """Lock down PeriodicalArticleRecord and PublicationEntry fields and enum bounds."""
    entry_fields = {f.name for f in dataclasses.fields(PublicationEntry)}
    assert entry_fields == {
        "line_number",
        "subject_name_verbatim",
        "individual_id",
        "role_or_class_raw",
        "page_or_plate",
        "remarks_raw",
    }

    rec_fields = {f.name for f in dataclasses.fields(PeriodicalArticleRecord)}
    expected_rec_fields = _BASE_SOURCE_FIELDS | {
        "publication_title_raw",
        "date_published",
        "publication_kind",
        "parent_source_id",
        "pub_code",
        "institution_or_publisher_raw",
        "institution_org_id",
        "author_or_editor_raw",
        "article_or_chapter_title",
        "volume_issue",
        "page_or_plate",
        "education_level",
        "entries",
    }
    assert rec_fields == expected_rec_fields
    assert PeriodicalArticleRecord.ALLOWED_CATEGORIES == frozenset(
        {
            SourceRecordCategory.EDUCATION,
            SourceRecordCategory.NARRATIVE,
            SourceRecordCategory.NEWS,
            SourceRecordCategory.FRATERNAL,
            SourceRecordCategory.CHURCH,
            SourceRecordCategory.OTHER,
        }
    )
    assert PeriodicalArticleRecord.ALLOWED_RECORD_TYPES == frozenset(
        {
            SourceRecordType.YEARBOOK_PAGE,
            SourceRecordType.COMMENCEMENT_PROGRAM,
            SourceRecordType.CLASS_ROSTER,
            SourceRecordType.MEMOIR,
            SourceRecordType.MISC,
            SourceRecordType.PHOTO,
        }
    )
