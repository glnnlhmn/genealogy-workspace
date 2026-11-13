"""Path: tests/test_gda/test_model/test_probate/test_probate_contract.py

Public interface and structural contract tests for gda.model.probate.

Operational Role:
    Locks down __all__ exports, SourceRecord inheritance, frozen dataclass
    immutability, authoritative field sets, category/record-type class constants,
    and public factory/serialization signatures across ProbateRecord, WillBequest,
    EstateInventoryRecord, InventoryLineItem, and ProbateLedgerEntry to prevent
    accidental breaking interface drift.
"""

from __future__ import annotations

import dataclasses
import inspect

import pytest

import gda.model.probate as probate_pkg
from gda.core.enums.sources import SourceRecordCategory, SourceRecordType
from gda.model.base.source import SourceRecord
from gda.model.probate import (
    EstateInventoryRecord,
    InventoryLineItem,
    ProbateLedgerEntry,
    ProbateRecord,
    WillBequest,
)

__version__ = "1.0.0+build.1"

_EXPECTED_EXPORTS: tuple[str, ...] = (
    "EstateInventoryRecord",
    "InventoryLineItem",
    "ProbateLedgerEntry",
    "ProbateRecord",
    "WillBequest",
)

_PROBATE_SOURCE_CLASSES: tuple[type[SourceRecord], ...] = (
    ProbateRecord,
    EstateInventoryRecord,
)

_PROBATE_VALUE_CLASSES: tuple[type[object], ...] = (
    WillBequest,
    InventoryLineItem,
    ProbateLedgerEntry,
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
def test_probate_package_public_exports() -> None:
    """Verify gda.model.probate.__all__ matches the exact locked export surface."""
    assert tuple(probate_pkg.__all__) == _EXPECTED_EXPORTS
    for symbol in _EXPECTED_EXPORTS:
        assert hasattr(probate_pkg, symbol)


@pytest.mark.unit
@pytest.mark.integrity
@pytest.mark.parametrize("record_cls", _PROBATE_SOURCE_CLASSES)
def test_probate_record_inheritance_immutability_and_methods(
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
@pytest.mark.parametrize("value_cls", _PROBATE_VALUE_CLASSES)
def test_probate_value_object_immutability_and_serialization(
    value_cls: type[object],
) -> None:
    """Verify frozen dataclass config and serialization quartet on probate value objects."""
    assert dataclasses.is_dataclass(value_cls)
    assert value_cls.__dataclass_params__.frozen is True  # type: ignore[attr-defined]

    for method_name in ("create", "to_dict", "from_dict", "to_json", "from_json"):
        assert hasattr(value_cls, method_name)
        assert callable(getattr(value_cls, method_name))


@pytest.mark.unit
@pytest.mark.integrity
def test_probate_record_field_and_enum_contract() -> None:
    """Lock down ProbateRecord and WillBequest fields and enum bounds."""
    bequest_fields = {f.name for f in dataclasses.fields(WillBequest)}
    assert bequest_fields == {
        "item_number",
        "beneficiary_name_raw",
        "property_or_amount_raw",
        "beneficiary_id",
        "relationship_raw",
        "bequest_type",
        "conditions_raw",
    }

    rec_fields = {f.name for f in dataclasses.fields(ProbateRecord)}
    expected_rec_fields = _BASE_SOURCE_FIELDS | {
        "court_name",
        "filing_locator",
        "decedent_name_raw",
        "court_location_id",
        "register_or_clerk",
        "estate_file_number",
        "book_and_page",
        "docket_term",
        "decedent_id",
        "decedent_residence_raw",
        "decedent_residence_id",
        "decedent_condition_or_trade",
        "date_written",
        "date_probated",
        "date_letters_granted",
        "provisions_summary",
        "bequests",
    }
    assert rec_fields == expected_rec_fields
    assert ProbateRecord.ALLOWED_CATEGORIES == frozenset(
        {
            SourceRecordCategory.PROBATE,
            SourceRecordCategory.LEGAL,
        }
    )
    assert ProbateRecord.ALLOWED_RECORD_TYPES == frozenset(
        {
            SourceRecordType.LAST_WILL_AND_TESTAMENT,
            SourceRecordType.CODICIL,
            SourceRecordType.LETTERS_TESTAMENTARY,
            SourceRecordType.LETTERS_ADMINISTRATION,
            SourceRecordType.ORPHANS_COURT_ENTRY,
            SourceRecordType.DOCKET_ENTRY,
        }
    )


@pytest.mark.unit
@pytest.mark.integrity
def test_estate_inventory_field_and_enum_contract() -> None:
    """Lock down EstateInventoryRecord, InventoryLineItem, and ProbateLedgerEntry fields."""
    item_fields = {f.name for f in dataclasses.fields(InventoryLineItem)}
    assert item_fields == {
        "line_number",
        "item_description_raw",
        "property_category",
        "appraised_value_raw",
        "appraised_value_numeric",
        "currency_code",
        "remarks_raw",
    }

    ledger_fields = {f.name for f in dataclasses.fields(ProbateLedgerEntry)}
    assert ledger_fields == {
        "line_number",
        "party_name_raw",
        "entry_kind",
        "party_id",
        "purpose_raw",
        "amount_raw",
        "amount_numeric",
    }

    rec_fields = {f.name for f in dataclasses.fields(EstateInventoryRecord)}
    expected_rec_fields = _BASE_SOURCE_FIELDS | {
        "court_name",
        "filing_locator",
        "decedent_name_raw",
        "court_location_id",
        "estate_file_number",
        "book_and_page",
        "decedent_id",
        "parent_probate_source_id",
        "date_appraised_or_accounted",
        "appraisers_or_administrators",
        "total_appraised_value_raw",
        "total_appraised_value_numeric",
        "currency_code",
        "items",
        "ledger_entries",
    }
    assert rec_fields == expected_rec_fields
    assert EstateInventoryRecord.ALLOWED_CATEGORIES == frozenset(
        {
            SourceRecordCategory.PROBATE,
            SourceRecordCategory.LEGAL,
        }
    )
    assert EstateInventoryRecord.ALLOWED_RECORD_TYPES == frozenset(
        {
            SourceRecordType.ESTATE_INVENTORY,
            SourceRecordType.ADMINISTRATION_ACCOUNT,
            SourceRecordType.ORPHANS_COURT_ENTRY,
        }
    )
