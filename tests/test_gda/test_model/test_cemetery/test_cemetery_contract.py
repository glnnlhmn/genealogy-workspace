"""Path: tests/test_gda/test_model/test_cemetery/test_cemetery_contract.py

Public interface and structural contract tests for gda.model.cemetery.

Operational Role:
    Locks down __all__ exports, SourceRecord inheritance, frozen dataclass
    immutability, authoritative field sets, record-type class constants, and
    public factory/serialization signatures across CemeteryMarkerRecord,
    MarkerInterment, CemeteryRegistryRecord, CemeteryPlotEntry, and
    RegistryInterment to prevent accidental breaking interface drift.
"""

from __future__ import annotations

import dataclasses
import inspect

import pytest

import gda.model.cemetery as cem_pkg
from gda.core.enums.sources import SourceRecordType
from gda.model.base.source import SourceRecord
from gda.model.cemetery import (
    CemeteryMarkerRecord,
    CemeteryPlotEntry,
    CemeteryRegistryRecord,
    MarkerInterment,
    RegistryInterment,
)

__version__ = "1.0.0+build.1"

_EXPECTED_EXPORTS: tuple[str, ...] = (
    "CemeteryMarkerRecord",
    "CemeteryPlotEntry",
    "CemeteryRegistryRecord",
    "MarkerInterment",
    "RegistryInterment",
)

_CEMETERY_SOURCE_CLASSES: tuple[type[SourceRecord], ...] = (
    CemeteryMarkerRecord,
    CemeteryRegistryRecord,
)

_CEMETERY_VALUE_CLASSES: tuple[type[object], ...] = (
    MarkerInterment,
    CemeteryPlotEntry,
    RegistryInterment,
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
def test_cemetery_package_public_exports() -> None:
    """Verify gda.model.cemetery.__all__ matches the exact locked export surface."""
    assert tuple(cem_pkg.__all__) == _EXPECTED_EXPORTS
    for symbol in _EXPECTED_EXPORTS:
        assert hasattr(cem_pkg, symbol)


@pytest.mark.unit
@pytest.mark.integrity
@pytest.mark.parametrize("record_cls", _CEMETERY_SOURCE_CLASSES)
def test_cemetery_record_inheritance_immutability_and_methods(
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
@pytest.mark.parametrize("value_cls", _CEMETERY_VALUE_CLASSES)
def test_cemetery_value_object_immutability_and_serialization(
    value_cls: type[object],
) -> None:
    """Verify frozen dataclass config and serialization quartet on cemetery value objects."""
    assert dataclasses.is_dataclass(value_cls)
    assert value_cls.__dataclass_params__.frozen is True  # type: ignore[attr-defined]

    for method_name in ("create", "to_dict", "from_dict", "to_json", "from_json"):
        assert hasattr(value_cls, method_name)
        assert callable(getattr(value_cls, method_name))


@pytest.mark.unit
@pytest.mark.integrity
def test_cemetery_marker_field_and_enum_contract() -> None:
    """Lock down CemeteryMarkerRecord and MarkerInterment fields and record types."""
    interment_fields = {f.name for f in dataclasses.fields(MarkerInterment)}
    assert interment_fields == {
        "inscribed_name",
        "individual_id",
        "birth_date",
        "death_date",
        "age_at_death",
        "relationship_inscribed",
    }

    rec_fields = {f.name for f in dataclasses.fields(CemeteryMarkerRecord)}
    expected_rec_fields = _BASE_SOURCE_FIELDS | {
        "cemetery_name_raw",
        "interments",
        "cemetery_site_id",
        "location_id",
        "plot_location",
        "findagrave_id",
        "billiongraves_id",
        "cemetery_grave_id",
        "marker_type",
        "material",
        "carver",
        "physical_condition",
        "inscription_verbatim",
        "survey_date",
    }
    assert rec_fields == expected_rec_fields
    assert CemeteryMarkerRecord.ALLOWED_RECORD_TYPES == frozenset(
        {
            SourceRecordType.CEMETERY_MARKER,
            SourceRecordType.HEADSTONE,
            SourceRecordType.FOOTSTONE,
            SourceRecordType.FAMILY_MONUMENT,
            SourceRecordType.MEMORIAL_PLAQUE,
            SourceRecordType.MAUSOLEUM_CRYPT,
        }
    )


@pytest.mark.unit
@pytest.mark.integrity
def test_cemetery_registry_field_and_enum_contract() -> None:
    """Lock down CemeteryRegistryRecord, CemeteryPlotEntry, and RegistryInterment fields."""
    interment_fields = {f.name for f in dataclasses.fields(RegistryInterment)}
    assert interment_fields == {
        "inscribed_name",
        "individual_id",
        "birth_year",
        "death_year",
        "age_inscribed",
        "relationship_text",
    }

    plot_fields = {f.name for f in dataclasses.fields(CemeteryPlotEntry)}
    assert plot_fields == {
        "plot_locator",
        "interments",
        "marker_urn",
        "marker_source_id",
        "condition",
    }

    rec_fields = {f.name for f in dataclasses.fields(CemeteryRegistryRecord)}
    expected_rec_fields = _BASE_SOURCE_FIELDS | {
        "cemetery_site_id",
        "cemetery_name_raw",
        "plots",
        "location_id",
        "sexton_or_custodian",
        "survey_date",
    }
    assert rec_fields == expected_rec_fields
    assert CemeteryRegistryRecord.ALLOWED_RECORD_TYPES == frozenset(
        {
            SourceRecordType.REGISTER_ENTRY,
            SourceRecordType.CEMETERY_MARKER,
            SourceRecordType.MISC,
        }
    )
