"""Path: tests/test_gda/test_util/test_enums.py

Unit test suite for gda.util.enums (coerce_enum).

Operational Role:
    Verifies case-insensitive value matching, member name matching, space/hyphen
    normalization, IntEnum resolution, boolean rejection, and structured
    ModelFormatError diagnostics with 100% statement and branch coverage.
"""

from __future__ import annotations

import pytest

from gda.core.enums import (
    CensusYearUS,
    FactType,
    MarkerType,
    QuayScore,
    Sex,
)
from gda.core.errors import ModelFormatError
from gda.util.enums import coerce_enum

__version__ = "1.0.0+build.2"


@pytest.mark.unit
@pytest.mark.smoke
def test_coerce_enum_returns_existing_enum_instance_unchanged() -> None:
    """Verify coerce_enum returns an already-valid Enum or IntEnum member directly."""
    assert coerce_enum(FactType, FactType.BIRTH) is FactType.BIRTH
    assert coerce_enum(Sex, Sex.FEMALE) is Sex.FEMALE
    assert coerce_enum(CensusYearUS, CensusYearUS.Y1880) is CensusYearUS.Y1880


@pytest.mark.unit
def test_coerce_enum_resolves_exact_and_case_insensitive_string_values() -> None:
    """Verify coerce_enum matches exact, lowercase, uppercase, and padded string values."""
    assert coerce_enum(FactType, "BIRTH") is FactType.BIRTH
    assert coerce_enum(FactType, "  birth  ") is FactType.BIRTH
    assert coerce_enum(Sex, "Male") is Sex.MALE
    assert coerce_enum(Sex, "male") is Sex.MALE
    assert coerce_enum(Sex, "MALE") is Sex.MALE


@pytest.mark.unit
def test_coerce_enum_resolves_member_names_and_title_case_variants() -> None:
    """Verify coerce_enum matches member names and space/hyphen-separated variants."""
    # MarkerType.UPRIGHT_HEADSTONE has value "Upright Headstone"
    assert coerce_enum(MarkerType, "Upright Headstone") is MarkerType.UPRIGHT_HEADSTONE
    assert coerce_enum(MarkerType, "upright headstone") is MarkerType.UPRIGHT_HEADSTONE
    assert coerce_enum(MarkerType, "UPRIGHT_HEADSTONE") is MarkerType.UPRIGHT_HEADSTONE
    assert coerce_enum(MarkerType, "upright-headstone") is MarkerType.UPRIGHT_HEADSTONE


@pytest.mark.unit
def test_coerce_enum_resolves_int_and_numeric_string_for_intenum() -> None:
    """Verify coerce_enum resolves integer and numeric string inputs for IntEnum classes."""
    assert coerce_enum(CensusYearUS, 1880) is CensusYearUS.Y1880
    assert coerce_enum(CensusYearUS, "1880") is CensusYearUS.Y1880
    assert coerce_enum(CensusYearUS, "Y1880") is CensusYearUS.Y1880
    assert coerce_enum(QuayScore, 3) is QuayScore.DIRECT_PRIMARY


@pytest.mark.regression
def test_coerce_enum_rejects_booleans_and_invalid_values() -> None:
    """Verify coerce_enum raises ModelFormatError on booleans, unknown values, and wrong types."""
    with pytest.raises(ModelFormatError, match="boolean"):
        coerce_enum(QuayScore, True, field_name="quay")

    with pytest.raises(ModelFormatError, match="not a valid CensusYearUS"):
        coerce_enum(CensusYearUS, 1881)

    with pytest.raises(ModelFormatError, match="not a valid CensusYearUS"):
        coerce_enum(CensusYearUS, "1881")

    with pytest.raises(ModelFormatError, match="not a valid FactType"):
        coerce_enum(FactType, "NON_EXISTENT_FACT")

    with pytest.raises(ModelFormatError, match="not a valid FactType"):
        coerce_enum(FactType, "   ")

    with pytest.raises(ModelFormatError, match="expected FactType or str"):
        coerce_enum(FactType, ["BIRTH"], field_name="fact_type")
