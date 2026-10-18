# Name: test_enums.py
# Path: tests/test_gda/test_enums/test_enums.py

"""Comprehensive behavioral test suite verifying all authoritative enumeration contracts.

Operational Role:
    Verifies that all StrEnum and IntEnum definitions in gda.enums conform to
    their expected tokens, base classes, JSON serializability, Pydantic V2
    validation, and strict case/whitespace rejection boundaries.

Test Structure & Protocol:
    - Atomized tests: 1:1 verification per behavioral contract.
    - Fully decorated: Explicitly decorated with registered pytest markers.
    - Dependencies: In-memory only; zero physical disk I/O.
"""

from __future__ import annotations

import json
from enum import Enum, IntEnum, StrEnum
from typing import Any

import pytest
from pydantic import BaseModel, ValidationError

import gda.enums as ge

__version__ = "0.1.0+build.r1"

# ==============================================================================
# GROUP 1: General Enum Invariants & Structural Integrity
# Note: Structural inheritance, unique member mapping, and export parity
# ==============================================================================


@pytest.mark.unit
@pytest.mark.integrity
def test_all_enums_inherit_proper_base_types(
    all_enum_classes: tuple[type[Enum], ...],
) -> None:
    """Verify every registered enum inherits strictly from StrEnum or IntEnum."""
    for enum_cls in all_enum_classes:
        is_str = issubclass(enum_cls, StrEnum)
        is_int = issubclass(enum_cls, IntEnum)
        assert is_str or is_int, (
            f"{enum_cls.__name__} does not inherit from StrEnum or IntEnum"
        )


@pytest.mark.unit
@pytest.mark.integrity
def test_all_enum_members_have_unique_values(
    all_enum_classes: tuple[type[Enum], ...],
) -> None:
    """Verify no duplicate values exist across distinct members within each enum class."""
    for enum_cls in all_enum_classes:
        values = [member.value for member in enum_cls]
        unique_values = set(values)
        assert len(values) == len(unique_values), (
            f"{enum_cls.__name__} contains duplicate member values"
        )


@pytest.mark.unit
@pytest.mark.integrity
def test_all_enum_classes_are_exported_in_dunder_all(
    all_enum_classes: tuple[type[Enum], ...],
) -> None:
    """Verify that gda.enums.__all__ precisely matches the exported enum classes."""
    exported_names = set(ge.__all__)
    assert len(exported_names) == len(all_enum_classes), (
        "Discrepancy between __all__ and exported classes"
    )
    for enum_cls in all_enum_classes:
        assert enum_cls.__name__ in exported_names, (
            f"{enum_cls.__name__} missing from __all__"
        )


# ==============================================================================
# GROUP 2: Canonical Tokens & Domain Boundary Specifications
# Note: Specific token validation matching schemas and architectural constraints
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_sex_enum_tokens_match_single_letter_spec() -> None:
    """Verify Sex contains exactly M, F, and U matching schema specifications."""
    assert ge.Sex.M == "M"
    assert ge.Sex.F == "F"
    assert ge.Sex.U == "U"
    assert len(ge.Sex) == 3


@pytest.mark.unit
@pytest.mark.smoke
def test_quay_score_integer_mapping_and_order() -> None:
    """Verify QuayScore provides sequential 0 to 3 integers for evidentiary ranking."""
    assert ge.QuayScore.UNRELIABLE == 0
    assert ge.QuayScore.QUESTIONABLE == 1
    assert ge.QuayScore.SECONDARY == 2
    assert ge.QuayScore.DIRECT_PRIMARY == 3


@pytest.mark.unit
def test_location_type_and_site_type_boundary() -> None:
    """Verify LocationType (jurisdictions) is strictly partitioned from SiteType (venues)."""
    assert ge.LocationType.COUNTY == "COUNTY"
    assert ge.LocationType.STATE == "STATE"
    assert ge.SiteType.CEMETERY == "CEMETERY"
    assert ge.SiteType.CHURCH == "CHURCH"
    assert "COUNTY" not in [m.value for m in ge.SiteType]
    assert "STATE" not in [m.value for m in ge.SiteType]


@pytest.mark.unit
def test_census_years_are_strictly_valid_historical_integers() -> None:
    """Verify CensusYear members evaluate to canonical decennial census integers."""
    assert ge.CensusYear.Y1790 == 1790
    assert ge.CensusYear.Y1880 == 1880
    assert ge.CensusYear.Y1950 == 1950
    for year in ge.CensusYear:
        assert isinstance(year.value, int)
        assert 1790 <= year.value <= 1950


@pytest.mark.unit
def test_fiscal_taxpayer_classification_tokens() -> None:
    """Verify TaxpayerClassification matches historical tax roll categories."""
    assert ge.TaxpayerClassification.FREEHOLDER == "Freeholder"
    assert ge.TaxpayerClassification.TENANT == "Tenant"
    assert ge.TaxpayerClassification.SINGLE_FREEMAN == "Single Freeman"
    assert ge.TaxpayerClassification.INMATE == "Inmate"
    assert ge.TaxpayerClassification.WIDOW == "Widow"


# ==============================================================================
# GROUP 3: Native JSON Serialization & String Formats
# Note: Direct serializability to plain JSON strings and integers
# ==============================================================================


@pytest.mark.unit
def test_strenum_native_json_dump_emits_raw_string() -> None:
    """Verify that StrEnum members serialize directly to raw strings in JSON."""
    payload = {
        "sex": ge.Sex.M,
        "fact": ge.FactType.BIRTH,
        "marker": ge.MarkerType.UPRIGHT_HEADSTONE,
    }
    encoded = json.dumps(payload)
    decoded = json.loads(encoded)

    assert decoded["sex"] == "M"
    assert decoded["fact"] == "Birth"
    assert decoded["marker"] == "Upright Headstone"


@pytest.mark.unit
def test_intenum_native_json_dump_emits_raw_integer() -> None:
    """Verify that IntEnum members serialize directly to numeric integers in JSON."""
    payload = {
        "quay": ge.QuayScore.DIRECT_PRIMARY,
        "census_year": ge.CensusYear.Y1850,
    }
    encoded = json.dumps(payload)
    decoded = json.loads(encoded)

    assert decoded["quay"] == 3
    assert decoded["census_year"] == 1850


@pytest.mark.unit
def test_strenum_str_comparison_and_formatting() -> None:
    """Verify StrEnum members behave identically to native str in equality and formatting."""
    assert ge.Sex.M == "M"
    assert f"Sex is {ge.Sex.F}" == "Sex is F"
    assert ge.Sex.M.startswith("M")


# ==============================================================================
# GROUP 4: Pydantic V2 Validation & Coercion
# Note: Automatic type coercion, rejection, and optional handling
# ==============================================================================


@pytest.mark.unit
def test_pydantic_validates_raw_string_into_enum_instance(
    pydantic_enum_model_cls: type[BaseModel],
    valid_enum_payload: dict[str, Any],
) -> None:
    """Verify Pydantic coerces raw strings and ints into corresponding enum instances."""
    instance = pydantic_enum_model_cls(**valid_enum_payload)

    assert instance.sex is ge.Sex.M
    assert instance.quay is ge.QuayScore.DIRECT_PRIMARY
    assert instance.fact_type is ge.FactType.BIRTH
    assert instance.census_year is ge.CensusYear.Y1880


@pytest.mark.unit
def test_pydantic_accepts_enum_instances_directly(
    pydantic_enum_model_cls: type[BaseModel],
    valid_enum_payload: dict[str, Any],
) -> None:
    """Verify Pydantic accepts pre-instantiated enum members directly."""
    payload = dict(valid_enum_payload)
    payload["sex"] = ge.Sex.F
    payload["quay"] = ge.QuayScore.SECONDARY

    instance = pydantic_enum_model_cls(**payload)
    assert instance.sex is ge.Sex.F
    assert instance.quay is ge.QuayScore.SECONDARY


@pytest.mark.unit
def test_pydantic_rejects_invalid_token_with_validation_error(
    pydantic_enum_model_cls: type[BaseModel],
    valid_enum_payload: dict[str, Any],
) -> None:
    """Verify Pydantic raises ValidationError when encountering unregistered tokens."""
    payload = dict(valid_enum_payload)
    payload["sex"] = "NonExistentSex"

    with pytest.raises(ValidationError) as exc_info:
        pydantic_enum_model_cls(**payload)

    assert "Input should be 'M', 'F' or 'U'" in str(exc_info.value)


@pytest.mark.unit
def test_pydantic_handles_optional_and_none_values(
    pydantic_enum_model_cls: type[BaseModel],
    valid_enum_payload: dict[str, Any],
) -> None:
    """Verify Pydantic accepts None for nullable/optional enum fields."""
    payload = dict(valid_enum_payload)
    payload["optional_sex"] = None
    payload["optional_quay"] = None

    instance = pydantic_enum_model_cls(**payload)
    assert instance.optional_sex is None
    assert instance.optional_quay is None

    payload["optional_sex"] = "U"
    instance_with_val = pydantic_enum_model_cls(**payload)
    assert instance_with_val.optional_sex is ge.Sex.U


# ==============================================================================
# GROUP 5: Defensive Boundaries & Strictness
# Note: Case sensitivity and untrimmed whitespace rejection
# ==============================================================================


@pytest.mark.unit
@pytest.mark.regression
def test_strenum_strict_case_sensitivity_rejection() -> None:
    """Verify StrEnum raises ValueError on lowercase or invalid casing."""
    with pytest.raises(ValueError):
        ge.Sex("m")

    with pytest.raises(ValueError):
        ge.FactType("birth")


@pytest.mark.unit
@pytest.mark.regression
def test_strenum_whitespace_tolerance_rejection() -> None:
    """Verify StrEnum rejects untrimmed whitespace to enforce upstream sanitization."""
    with pytest.raises(ValueError):
        ge.Sex(" M ")

    with pytest.raises(ValueError):
        ge.FactType("Birth ")
