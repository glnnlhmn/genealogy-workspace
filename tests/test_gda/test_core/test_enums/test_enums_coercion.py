"""Path: tests/test_gda/test_core/test_enums/test_enums_coercion.py

Coercion, base-class helper, Pydantic V2, and Hypothesis fuzzing suite
for gda.core.enums.

Operational Role:
    Validates gda.core.enums.coercion.coerce_enum, GDAStrEnum/GDAIntEnum
    classmethods (.from_raw(), .values()), Pydantic V2 validation with
    UPPER_SNAKE_CASE payloads, Hypothesis token-mutation round-trips,
    and strict rejection boundaries for invalid types and untrimmed input.

Test Structure & Protocol:
    - Atomized & parametrized tests: 1:1 behavioral contract mapping.
    - Fully decorated: 5-marker taxonomy (smoke, unit, regression, integrity).
    - Property-based: Hypothesis enum_token_variants from test_core/strategies.py.
    - Companion module: test_enums_contract.py (facade, placement, casing).
"""

from __future__ import annotations

from collections.abc import Callable
from enum import Enum
from typing import Any

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import BaseModel, ValidationError
from tests.test_gda.test_core.strategies import enum_token_variants

import gda.core.enums as ge
from gda.core.errors import ModelFormatError

__version__ = "1.0.0+build.4"


def _get_coerce_enum() -> Callable[..., Any]:
    """Return gda.core.enums.coerce_enum or fail cleanly as a Phase 3 TDD Red gate."""
    fn: object = getattr(ge, "coerce_enum", None)
    assert callable(fn), "gda.core.enums.coerce_enum not yet exported (Phase 3 TDD Red)"
    return fn


# ==============================================================================
# GROUP 1: Smoke & Primary Entrypoints
# Note: Single smoke gate verifying coerce_enum and .from_raw() primary paths.
# ==============================================================================


@pytest.mark.smoke
@pytest.mark.unit
def test_coerce_enum_and_from_raw_smoke() -> None:
    """Verify coerce_enum and GDAStrEnum/GDAIntEnum.from_raw() resolve canonical tokens."""
    coerce_fn = _get_coerce_enum()
    assert coerce_fn(ge.Sex, "male") is ge.Sex.MALE
    assert coerce_fn(ge.QuayScore, "3") is ge.QuayScore.DIRECT_PRIMARY

    assert ge.Sex.from_raw("female") is ge.Sex.FEMALE
    assert ge.QuayScore.from_raw("3") is ge.QuayScore.DIRECT_PRIMARY
    assert ge.QuayScore.from_raw(2) is ge.QuayScore.SECONDARY


# ==============================================================================
# GROUP 2: Core Logic & Happy Paths
# Note: Pydantic V2 standardized payload validation, direct passthrough, and .values().
# ==============================================================================


@pytest.mark.unit
def test_pydantic_validates_standardized_upper_snake_case_payload(
    pydantic_enum_model_cls: type[BaseModel],
    standardized_enum_payload: dict[str, Any],
) -> None:
    """Verify Pydantic validates standardized UPPER_SNAKE_CASE tokens."""
    instance: Any = pydantic_enum_model_cls(**standardized_enum_payload)
    assert instance.sex is ge.Sex.MALE
    assert instance.quay is ge.QuayScore.DIRECT_PRIMARY
    assert instance.fact_type is ge.FactType.BIRTH
    assert instance.census_year is ge.CensusYearUS.Y1880
    assert instance.location_type is ge.LocationType.COUNTY
    assert instance.vital_modifier is ge.VitalModifier.STILLBORN


@pytest.mark.unit
def test_pydantic_accepts_enum_instances_and_optional_none(
    pydantic_enum_model_cls: type[BaseModel],
    standardized_enum_payload: dict[str, Any],
) -> None:
    """Verify Pydantic accepts pre-instantiated enums and None for optional fields."""
    payload = dict(standardized_enum_payload)
    payload["sex"] = ge.Sex.FEMALE
    payload["quay"] = ge.QuayScore.SECONDARY
    payload["optional_sex"] = None
    payload["optional_quay"] = None

    instance: Any = pydantic_enum_model_cls(**payload)
    assert instance.sex is ge.Sex.FEMALE
    assert instance.quay is ge.QuayScore.SECONDARY
    assert instance.optional_sex is None
    assert instance.optional_quay is None


@pytest.mark.unit
def test_enum_values_classmethod_returns_member_value_tuple(
    sample_coercible_enums: tuple[type[Enum], ...],
) -> None:
    """Verify GDAStrEnum/GDAIntEnum.values() returns a tuple of raw member values."""
    for enum_cls in sample_coercible_enums:
        values_fn = getattr(enum_cls, "values", None)
        assert callable(values_fn), f"{enum_cls.__name__}.values() missing"
        assert values_fn() == tuple(m.value for m in enum_cls)


@pytest.mark.unit
@pytest.mark.parametrize(
    ("raw_token", "expected"),
    [
        ("direct_primary", ge.QuayScore.DIRECT_PRIMARY),
        ("direct-primary", ge.QuayScore.DIRECT_PRIMARY),
        ("  SECONDARY  ", ge.QuayScore.SECONDARY),
    ],
)
def test_coerce_enum_int_enum_resolves_member_name_strings(
    raw_token: str,
    expected: ge.QuayScore,
) -> None:
    """Verify coerce_enum resolves GDAIntEnum members by normalized member name."""
    coerce_fn = _get_coerce_enum()
    assert coerce_fn(ge.QuayScore, raw_token) is expected


# ==============================================================================
# GROUP 3: Edge Cases & Boundary Conditions (Hypothesis Fuzzing)
# Note: Mixed casing, hyphens, spaces, and surrounding whitespace via strategies.py.
# ==============================================================================


@pytest.mark.unit
@pytest.mark.regression
@given(
    token_pair=st.one_of(
        enum_token_variants(ge.Sex).map(lambda t: (ge.Sex, t)),
        enum_token_variants(ge.FactType).map(lambda t: (ge.FactType, t)),
        enum_token_variants(ge.DateModifier).map(lambda t: (ge.DateModifier, t)),
        enum_token_variants(ge.QuayScore).map(lambda t: (ge.QuayScore, t)),
    )
)
def test_coerce_enum_hypothesis_token_variants(
    token_pair: tuple[type[Enum], tuple[Enum, Any]],
) -> None:
    """Verify coerce_enum resolves fuzzed casing and whitespace mutations."""
    coerce_fn = _get_coerce_enum()
    enum_cls, (expected_member, raw_token) = token_pair
    assert coerce_fn(enum_cls, raw_token) is expected_member


# ==============================================================================
# GROUP 4: Error Handling & Validation Failures
# Note: Strict StrEnum rejection, Pydantic errors, and hostile coerce_enum inputs.
# ==============================================================================


@pytest.mark.regression
@pytest.mark.parametrize("bad_sex", ["male", " MALE ", "NonExistentSex"])
def test_strenum_strict_case_and_whitespace_rejection(bad_sex: str) -> None:
    """Verify StrEnum direct construction rejects lowercase, untrimmed, or unknown tokens."""
    with pytest.raises(ValueError):
        ge.Sex(bad_sex)


@pytest.mark.regression
def test_pydantic_rejects_invalid_token_with_validation_error(
    pydantic_enum_model_cls: type[BaseModel],
    standardized_enum_payload: dict[str, Any],
) -> None:
    """Verify Pydantic raises ValidationError on unregistered enum tokens."""
    payload = dict(standardized_enum_payload)
    payload["sex"] = "NON_EXISTENT_SEX"
    with pytest.raises(ValidationError):
        pydantic_enum_model_cls(**payload)


@pytest.mark.regression
@pytest.mark.parametrize(
    "bad_raw",
    [
        True,
        False,
        None,
        "",
        "   ",
        99,
        "99",
        "BOGUS_QUAY",
        3.14,
        float("nan"),
        float("inf"),
        ["MALE"],
    ],
)
def test_coerce_enum_rejects_bool_non_finite_and_invalid_types(bad_raw: Any) -> None:
    """Verify coerce_enum rejects booleans, None, blanks, out-of-range ints, and invalid types."""
    coerce_fn = _get_coerce_enum()
    with pytest.raises(ModelFormatError) as exc_info:
        coerce_fn(ge.QuayScore, bad_raw, field_name="quay")
    assert exc_info.value.error_code == "ERR_MODEL_FORMAT"


@pytest.mark.regression
@pytest.mark.parametrize("bad_raw", [123, "   ", "NOT_A_SEX"])
def test_coerce_enum_strenum_rejects_non_string_blank_and_unmapped_without_field_name(
    bad_raw: Any,
) -> None:
    """Verify StrEnum coercion rejects non-strings, blanks, and unmapped tokens with field_name=None."""
    coerce_fn = _get_coerce_enum()
    with pytest.raises(ModelFormatError) as exc_info:
        coerce_fn(ge.Sex, bad_raw)
    assert exc_info.value.error_code == "ERR_MODEL_FORMAT"
