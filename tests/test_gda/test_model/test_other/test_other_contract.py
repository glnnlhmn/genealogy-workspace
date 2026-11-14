"""Path: tests/test_gda/test_model/test_other/test_other_contract.py

Public interface and structural contract tests for gda.model.other.

Operational Role:
    Locks down __all__ exports, SourceRecord inheritance, frozen dataclass
    immutability, authoritative field sets, category/record-type class constants,
    and public factory/serialization signatures across OtherMiscellaneousRecord.
"""

from __future__ import annotations

import dataclasses
import inspect

import pytest

import gda.model.other as other_pkg
from gda.core.enums.sources import SourceRecordCategory, SourceRecordType
from gda.model.base.source import SourceRecord
from gda.model.other import OtherMiscellaneousRecord

__version__ = "1.0.0+build.1"

_EXPECTED_EXPORTS: tuple[str, ...] = ("OtherMiscellaneousRecord",)

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
def test_other_package_public_exports() -> None:
    """Verify gda.model.other.__all__ matches the exact locked export surface."""
    assert tuple(other_pkg.__all__) == _EXPECTED_EXPORTS
    for symbol in _EXPECTED_EXPORTS:
        assert hasattr(other_pkg, symbol)


@pytest.mark.unit
@pytest.mark.integrity
def test_other_miscellaneous_contract() -> None:
    """Lock down OtherMiscellaneousRecord inheritance, immutability, fields, and enum bounds."""
    assert issubclass(OtherMiscellaneousRecord, SourceRecord)
    assert dataclasses.is_dataclass(OtherMiscellaneousRecord)
    assert OtherMiscellaneousRecord.__dataclass_params__.frozen is True  # type: ignore[attr-defined]

    for method_name in ("create", "to_dict", "from_dict", "to_json", "from_json"):
        assert hasattr(OtherMiscellaneousRecord, method_name)
        assert callable(getattr(OtherMiscellaneousRecord, method_name))

    create_sig = inspect.signature(OtherMiscellaneousRecord.create)
    for required_param in ("source_id", "source_urn", "description", "repository_id"):
        assert required_param in create_sig.parameters

    rec_fields = {f.name for f in dataclasses.fields(OtherMiscellaneousRecord)}
    expected_rec_fields = _BASE_SOURCE_FIELDS | {
        "item_date",
        "organization_or_entity_name",
        "organization_location_id",
        "custom_fields",
        "item_note",
    }
    assert rec_fields == expected_rec_fields
    assert OtherMiscellaneousRecord.ALLOWED_CATEGORIES == frozenset(
        {
            SourceRecordCategory.OTHER,
            SourceRecordCategory.FRATERNAL,
            SourceRecordCategory.CIVIC,
            SourceRecordCategory.EPHEMERA,
            SourceRecordCategory.FINANCIAL,
        }
    )
    assert OtherMiscellaneousRecord.ALLOWED_RECORD_TYPES == frozenset(
        {
            SourceRecordType.BIBLE,
            SourceRecordType.DIARY,
            SourceRecordType.CORRESP,
            SourceRecordType.FIN,
            SourceRecordType.EPHEM,
            SourceRecordType.PHOTO,
            SourceRecordType.LODGE_RECORD,
            SourceRecordType.MEMBERSHIP_ROSTER,
            SourceRecordType.RECEIPT,
            SourceRecordType.MISC,
        }
    )
