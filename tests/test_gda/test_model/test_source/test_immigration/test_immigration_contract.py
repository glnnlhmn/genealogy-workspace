"""Path: tests/test_gda/test_model/test_source/test_immigration/test_immigration_contract.py

Public interface and structural contract tests for gda.model.source.immigration.

Operational Role:
    Locks down __all__ exports, SourceRecord inheritance, frozen dataclass
    immutability, authoritative field sets, category/record-type class constants,
    and public factory/serialization signatures across ImmigrationManifestRecord,
    ManifestPassenger, NaturalizationRecord, and NaturalizationWitness to prevent
    accidental breaking interface drift.
"""

from __future__ import annotations

import dataclasses
import inspect

import pytest

import gda.model.source.immigration as imm_pkg
from gda.core.enums.sources import SourceRecordCategory, SourceRecordType
from gda.model.base.source import SourceRecord
from gda.model.source.immigration import (
    ImmigrationManifestRecord,
    ManifestPassenger,
    NaturalizationRecord,
    NaturalizationWitness,
)

__version__ = "1.0.0+build.1"

_EXPECTED_EXPORTS: tuple[str, ...] = (
    "ImmigrationManifestRecord",
    "ManifestPassenger",
    "NaturalizationRecord",
    "NaturalizationWitness",
)

_IMMIGRATION_SOURCE_CLASSES: tuple[type[SourceRecord], ...] = (
    ImmigrationManifestRecord,
    NaturalizationRecord,
)

_IMMIGRATION_VALUE_CLASSES: tuple[type[object], ...] = (
    ManifestPassenger,
    NaturalizationWitness,
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
def test_immigration_package_public_exports() -> None:
    """Verify gda.model.source.immigration.__all__ matches the exact locked export surface."""
    assert tuple(imm_pkg.__all__) == _EXPECTED_EXPORTS
    for symbol in _EXPECTED_EXPORTS:
        assert hasattr(imm_pkg, symbol)


@pytest.mark.unit
@pytest.mark.integrity
@pytest.mark.parametrize("record_cls", _IMMIGRATION_SOURCE_CLASSES)
def test_immigration_record_inheritance_immutability_and_methods(
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
@pytest.mark.parametrize("value_cls", _IMMIGRATION_VALUE_CLASSES)
def test_immigration_value_object_immutability_and_serialization(
    value_cls: type[object],
) -> None:
    """Verify frozen dataclass config and serialization quartet on immigration value objects."""
    assert dataclasses.is_dataclass(value_cls)
    assert value_cls.__dataclass_params__.frozen is True  # type: ignore[attr-defined]

    for method_name in ("create", "to_dict", "from_dict", "to_json", "from_json"):
        assert hasattr(value_cls, method_name)
        assert callable(getattr(value_cls, method_name))


@pytest.mark.unit
@pytest.mark.integrity
def test_immigration_manifest_field_and_enum_contract() -> None:
    """Lock down ImmigrationManifestRecord and ManifestPassenger fields and enum bounds."""
    passenger_fields = {f.name for f in dataclasses.fields(ManifestPassenger)}
    assert passenger_fields == {
        "full_name",
        "line_number",
        "individual_id",
        "age_raw",
        "sex",
        "marital_status",
        "occupation",
        "passage_class",
        "nationality_or_race_raw",
        "last_permanent_residence_raw",
        "last_permanent_residence_id",
        "final_destination_raw",
        "final_destination_id",
        "relative_joined_name",
        "relative_joined_relationship",
        "relative_joined_address",
    }

    rec_fields = {f.name for f in dataclasses.fields(ImmigrationManifestRecord)}
    expected_rec_fields = _BASE_SOURCE_FIELDS | {
        "port_of_arrival_raw",
        "arrival_date",
        "manifest_locator",
        "passengers",
        "port_of_arrival_id",
        "ship_name",
        "master_or_captain",
        "shipping_line",
        "port_of_departure_raw",
        "port_of_departure_id",
        "list_number",
    }
    assert rec_fields == expected_rec_fields
    assert ImmigrationManifestRecord.ALLOWED_CATEGORIES == frozenset(
        {
            SourceRecordCategory.IMMIGRATION,
            SourceRecordCategory.TRAVEL,
            SourceRecordCategory.CUSTOMS,
        }
    )
    assert ImmigrationManifestRecord.ALLOWED_RECORD_TYPES == frozenset(
        {
            SourceRecordType.PASSENGER_MANIFEST,
            SourceRecordType.CUSTOMS_LIST,
            SourceRecordType.OATH_OF_ALLEGIANCE_LIST,
            SourceRecordType.BORDER_CROSSING_CARD,
            SourceRecordType.CREW_LIST,
        }
    )


@pytest.mark.unit
@pytest.mark.integrity
def test_naturalization_record_field_and_enum_contract() -> None:
    """Lock down NaturalizationRecord and NaturalizationWitness fields and enum bounds."""
    witness_fields = {f.name for f in dataclasses.fields(NaturalizationWitness)}
    assert witness_fields == {
        "name",
        "individual_id",
        "occupation",
        "residence",
    }

    rec_fields = {f.name for f in dataclasses.fields(NaturalizationRecord)}
    expected_rec_fields = _BASE_SOURCE_FIELDS | {
        "court_name",
        "docket_locator",
        "applicant_name_raw",
        "event_date",
        "court_location_id",
        "presiding_judge_or_clerk",
        "volume_page",
        "certificate_stub_number",
        "stage",
        "applicant_id",
        "current_residence_raw",
        "current_residence_id",
        "date_of_birth",
        "place_of_birth_raw",
        "place_of_birth_id",
        "country_of_prior_allegiance",
        "port_of_entry_raw",
        "arrival_date",
        "vessel_name",
        "witnesses",
    }
    assert rec_fields == expected_rec_fields
    assert NaturalizationRecord.ALLOWED_CATEGORIES == frozenset(
        {
            SourceRecordCategory.LEGAL,
            SourceRecordCategory.CITIZENSHIP,
            SourceRecordCategory.IMMIGRATION,
        }
    )
    assert NaturalizationRecord.ALLOWED_RECORD_TYPES == frozenset(
        {
            SourceRecordType.DECLARATION_OF_INTENTION,
            SourceRecordType.PETITION_FOR_NATURALIZATION,
            SourceRecordType.CERTIFICATE_OF_CITIZENSHIP,
            SourceRecordType.OATH_OF_ALLEGIANCE,
            SourceRecordType.ORDER_OF_COURT,
        }
    )
