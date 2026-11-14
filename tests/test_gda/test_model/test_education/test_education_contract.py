"""Path: tests/test_gda/test_model/test_education/test_education_contract.py

Public interface and structural contract tests for gda.model.education.

Operational Role:
    Locks down __all__ exports, SourceRecord inheritance, frozen dataclass
    immutability, authoritative field sets, category/record-type class constants,
    and public factory/serialization signatures across AcademicCredentialRecord.
"""

from __future__ import annotations

import dataclasses
import inspect

import pytest

import gda.model.education as edu_pkg
from gda.core.enums.sources import SourceRecordCategory, SourceRecordType
from gda.model.base.source import SourceRecord
from gda.model.education import AcademicCredentialRecord

__version__ = "1.0.0+build.1"

_EXPECTED_EXPORTS: tuple[str, ...] = ("AcademicCredentialRecord",)

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
def test_education_package_public_exports() -> None:
    """Verify gda.model.education.__all__ matches the exact locked export surface."""
    assert tuple(edu_pkg.__all__) == _EXPECTED_EXPORTS
    for symbol in _EXPECTED_EXPORTS:
        assert hasattr(edu_pkg, symbol)


@pytest.mark.unit
@pytest.mark.integrity
def test_academic_credential_contract() -> None:
    """Lock down AcademicCredentialRecord inheritance, immutability, fields, and enum bounds."""
    assert issubclass(AcademicCredentialRecord, SourceRecord)
    assert dataclasses.is_dataclass(AcademicCredentialRecord)
    assert AcademicCredentialRecord.__dataclass_params__.frozen is True  # type: ignore[attr-defined]

    for method_name in ("create", "to_dict", "from_dict", "to_json", "from_json"):
        assert hasattr(AcademicCredentialRecord, method_name)
        assert callable(getattr(AcademicCredentialRecord, method_name))

    create_sig = inspect.signature(AcademicCredentialRecord.create)
    for required_param in ("source_id", "source_urn", "description", "repository_id"):
        assert required_param in create_sig.parameters

    rec_fields = {f.name for f in dataclasses.fields(AcademicCredentialRecord)}
    expected_rec_fields = _BASE_SOURCE_FIELDS | {
        "institution_name_raw",
        "subject_name_raw",
        "date_issued_or_published",
        "education_level",
        "institution_location_id",
        "subject_id",
        "degree_or_credential",
        "graduation_year",
        "publication_title",
        "page_or_plate",
        "credential_note",
    }
    assert rec_fields == expected_rec_fields
    assert AcademicCredentialRecord.ALLOWED_CATEGORIES == frozenset(
        {SourceRecordCategory.EDUCATION}
    )
    assert AcademicCredentialRecord.ALLOWED_RECORD_TYPES == frozenset(
        {
            SourceRecordType.DIPLOMA,
            SourceRecordType.GRADUATION_CERTIFICATE,
            SourceRecordType.YEARBOOK_PAGE,
            SourceRecordType.COMMENCEMENT_PROGRAM,
            SourceRecordType.CLASS_ROSTER,
            SourceRecordType.TRANSCRIPT_REPORT,
        }
    )
