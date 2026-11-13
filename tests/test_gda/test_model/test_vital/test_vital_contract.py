"""Path: tests/test_gda/test_model/test_vital/test_vital_contract.py

Public interface and structural contract tests for gda.model.vital.

Operational Role:
    Locks down __all__ exports, SourceRecord inheritance, frozen dataclass
    immutability, authoritative field names, category/record-type class constants,
    and public factory/serialization signatures across BirthRecord, MarriageRecord,
    DeathRecord, DivorceRecord, and BaptismRecord to prevent accidental breaking
    interface drift.
"""

from __future__ import annotations

import dataclasses
import inspect

import pytest

import gda.model.vital as vital_pkg
from gda.core.enums.sources import SourceRecordCategory, SourceRecordType
from gda.model.base.source import SourceRecord
from gda.model.vital import (
    BaptismRecord,
    BirthRecord,
    DeathRecord,
    DivorceRecord,
    MarriageRecord,
)

__version__ = "1.0.0+build.2"

_EXPECTED_EXPORTS: tuple[str, ...] = (
    "BaptismRecord",
    "BirthRecord",
    "DeathRecord",
    "DivorceRecord",
    "MarriageRecord",
)

_VITAL_CLASSES: tuple[type[SourceRecord], ...] = (
    BirthRecord,
    MarriageRecord,
    DeathRecord,
    DivorceRecord,
    BaptismRecord,
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
def test_vital_package_public_exports() -> None:
    """Verify gda.model.vital.__all__ matches the exact locked export surface."""
    assert tuple(vital_pkg.__all__) == _EXPECTED_EXPORTS
    for symbol in _EXPECTED_EXPORTS:
        assert hasattr(vital_pkg, symbol)


@pytest.mark.unit
@pytest.mark.integrity
@pytest.mark.parametrize("record_cls", _VITAL_CLASSES)
def test_vital_record_inheritance_immutability_and_methods(
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
def test_birth_record_field_and_enum_contract() -> None:
    """Lock down BirthRecord fields and allowed SourceRecordType tokens."""
    field_names = {f.name for f in dataclasses.fields(BirthRecord)}
    expected_fields = _BASE_SOURCE_FIELDS | {
        "child_name_raw",
        "date_of_birth",
        "place_of_birth_raw",
        "child_id",
        "sex",
        "plurality",
        "birth_order",
        "is_stillborn",
        "vital_modifier",
        "time_of_birth",
        "place_of_birth_id",
        "legitimacy",
        "certificate_number",
        "registration_district",
        "date_filed",
        "father_name_raw",
        "mother_maiden_name_raw",
    }
    assert field_names == expected_fields
    assert BirthRecord.ALLOWED_RECORD_TYPES == frozenset(
        {
            SourceRecordType.BIRTH_CERTIFICATE,
            SourceRecordType.DELAYED_BIRTH,
            SourceRecordType.REGISTER_ENTRY,
            SourceRecordType.STILLBORN_RECORD,
            SourceRecordType.HOSPITAL_CERTIFICATE,
        }
    )


@pytest.mark.unit
@pytest.mark.integrity
def test_marriage_record_field_and_enum_contract() -> None:
    """Lock down MarriageRecord fields and allowed category/record_type tokens."""
    field_names = {f.name for f in dataclasses.fields(MarriageRecord)}
    expected_fields = _BASE_SOURCE_FIELDS | {
        "groom_name_raw",
        "bride_name_raw",
        "union_type",
        "license_number",
        "date_issued",
        "issuing_jurisdiction_raw",
        "groom_id",
        "groom_age",
        "groom_marital_status",
        "groom_prior_dissolution",
        "groom_residence_raw",
        "bride_id",
        "bride_maiden_name_raw",
        "bride_age",
        "bride_marital_status",
        "bride_prior_dissolution",
        "bride_residence_raw",
        "date_of_marriage",
        "place_of_marriage_raw",
        "place_of_marriage_id",
        "officiant_name_raw",
        "officiant_title_raw",
        "religious_denomination",
        "witnesses",
    }
    assert field_names == expected_fields
    assert MarriageRecord.ALLOWED_CATEGORIES == frozenset(
        {
            SourceRecordCategory.VITAL,
            SourceRecordCategory.CHURCH,
        }
    )
    assert MarriageRecord.ALLOWED_RECORD_TYPES == frozenset(
        {
            SourceRecordType.MARRIAGE_LICENSE,
            SourceRecordType.MARRIAGE_CERTIFICATE,
            SourceRecordType.MARRIAGE_REGISTER,
            SourceRecordType.MINISTERS_RETURN,
            SourceRecordType.MARRIAGE_BOND,
        }
    )


@pytest.mark.unit
@pytest.mark.integrity
def test_death_record_field_and_enum_contract() -> None:
    """Lock down DeathRecord fields and allowed SourceRecordType tokens."""
    field_names = {f.name for f in dataclasses.fields(DeathRecord)}
    expected_fields = _BASE_SOURCE_FIELDS | {
        "decedent_name_raw",
        "date_of_death",
        "place_of_death_raw",
        "decedent_id",
        "sex",
        "is_stillborn",
        "marital_status",
        "spouse_name_raw",
        "date_of_birth",
        "age_at_death",
        "time_of_death",
        "place_of_death_id",
        "residence_raw",
        "occupation_raw",
        "father_name_raw",
        "mother_maiden_name_raw",
        "manner_of_death",
        "cause_of_death_raw",
        "attending_physician_raw",
        "informant_name_raw",
        "disposition_type",
        "disposition_date",
        "disposition_place_raw",
        "disposition_site_id",
        "undertaker_raw",
        "certificate_number",
        "date_filed",
    }
    assert field_names == expected_fields
    assert DeathRecord.ALLOWED_RECORD_TYPES == frozenset(
        {
            SourceRecordType.DEATH_CERTIFICATE,
            SourceRecordType.FETAL_DEATH,
            SourceRecordType.CORONER_INQUEST,
            SourceRecordType.TRANSIT_PERMIT,
            SourceRecordType.REGISTER_ENTRY,
            SourceRecordType.DELAYED_DEATH,
        }
    )


@pytest.mark.unit
@pytest.mark.integrity
def test_divorce_record_field_and_enum_contract() -> None:
    """Lock down DivorceRecord fields and allowed category/record_type tokens."""
    field_names = {f.name for f in dataclasses.fields(DivorceRecord)}
    expected_fields = _BASE_SOURCE_FIELDS | {
        "court_name",
        "husband_name_raw",
        "wife_name_raw",
        "date_decree_granted",
        "docket_number",
        "state_file_number",
        "jurisdiction_raw",
        "jurisdiction_id",
        "husband_id",
        "wife_id",
        "wife_maiden_name_raw",
        "date_of_marriage",
        "place_of_marriage_raw",
        "date_of_separation",
        "plaintiff",
        "decree_type",
        "legal_grounds",
        "minor_children_count",
        "alimony_awarded",
    }
    assert field_names == expected_fields
    assert DivorceRecord.ALLOWED_CATEGORIES == frozenset(
        {
            SourceRecordCategory.LEGAL,
            SourceRecordCategory.VITAL,
        }
    )
    assert DivorceRecord.ALLOWED_RECORD_TYPES == frozenset(
        {
            SourceRecordType.DIVORCE_REPORT,
            SourceRecordType.DIVORCE_DECREE,
            SourceRecordType.DOCKET_ENTRY,
            SourceRecordType.ANNULMENT,
        }
    )


@pytest.mark.unit
@pytest.mark.integrity
def test_baptism_record_field_and_enum_contract() -> None:
    """Lock down BaptismRecord fields and allowed category/record_type tokens."""
    field_names = {f.name for f in dataclasses.fields(BaptismRecord)}
    expected_fields = _BASE_SOURCE_FIELDS | {
        "church_name_raw",
        "baptized_name_raw",
        "date_of_baptism",
        "church_org_id",
        "church_site_id",
        "location_id",
        "denomination",
        "volume_title",
        "register_locator",
        "individual_id",
        "sex",
        "date_of_birth",
        "place_of_birth_raw",
        "officiant_name_raw",
        "father_name_raw",
        "mother_name_raw",
        "sponsors_or_godparents",
    }
    assert field_names == expected_fields
    assert BaptismRecord.ALLOWED_CATEGORIES == frozenset(
        {
            SourceRecordCategory.CHURCH,
            SourceRecordCategory.VITAL,
        }
    )
    assert BaptismRecord.ALLOWED_RECORD_TYPES == frozenset(
        {
            SourceRecordType.BAPTISM_REGISTER,
            SourceRecordType.BAPTISM_CERTIFICATE,
            SourceRecordType.CHRISTENING_ENTRY,
            SourceRecordType.CRADLE_ROLL,
        }
    )
