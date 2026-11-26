"""Path: tests/test_gda/test_core/test_enums/test_vital_enums.py

Targeted behavioral test suite verifying demographic and vital event enums.

Operational Role:
    Verifies the 15 authoritative vital/biographical enums in gda.core.enums.vital,
    including HistoricNameType, UnionType, UnionDissolutionType, PedigreeType,
    vital/mortuary assertions, VitalModifier, and the 4 enums relocated from
    archival.py and sources.py (EyeColor, HairColor, PhysicalBuild, EducationLevel).

Test Structure & Protocol:
    - Atomized & parametrized tests: 1:1 behavioral contract mapping.
    - Fully decorated: 5-marker taxonomy (smoke, unit, regression).
    - Dependencies: In-memory only; zero physical disk I/O.
"""

from __future__ import annotations

import pytest

import gda.core.enums.vital as vital_enums
from gda.core.enums.vital import (
    BirthPlurality,
    DispositionType,
    DivorceDecreeType,
    EducationLevel,
    EyeColor,
    HairColor,
    HistoricNameType,
    LegalPlaintiff,
    MannerOfDeath,
    MaritalStatus,
    PedigreeType,
    PhysicalBuild,
    UnionDissolutionType,
    UnionType,
    VitalModifier,
)

__version__ = "1.0.0+build.7"


# ==============================================================================
# GROUP 1: Smoke & Primary Entrypoints
# Note: Single smoke gate freezing the 15 authoritative vital exports.
# ==============================================================================


@pytest.mark.smoke
@pytest.mark.unit
def test_vital_enums_exposes_expected_public_interface() -> None:
    """Verify gda.core.enums.vital exports all 15 authoritative enums."""
    expected = {
        "BirthPlurality",
        "DispositionType",
        "DivorceDecreeType",
        "EducationLevel",
        "EyeColor",
        "HairColor",
        "HistoricNameType",
        "LegalPlaintiff",
        "MannerOfDeath",
        "MaritalStatus",
        "PedigreeType",
        "PhysicalBuild",
        "UnionDissolutionType",
        "UnionType",
        "VitalModifier",
    }
    assert set(vital_enums.__all__) == expected


# ==============================================================================
# GROUP 2: Core Logic & Happy Paths
# Note: Onomastic, domestic, lineage, mortuary, and relocated physical enums.
# ==============================================================================


@pytest.mark.unit
@pytest.mark.parametrize(
    ("enum_cls", "expected_values"),
    [
        (
            HistoricNameType,
            {"PRIMARY", "HISTORICAL", "COLLOQUIAL", "COLONIAL", "INDIGENOUS"},
        ),
        (
            VitalModifier,
            {"STILLBORN", "INFANT", "ILLEGITIMATE", "POSTHUMOUS", "LEGITIMATED"},
        ),
    ],
)
def test_historic_name_type_and_vital_modifier_values(
    enum_cls: type[HistoricNameType] | type[VitalModifier],
    expected_values: set[str],
) -> None:
    """Verify HistoricNameType and VitalModifier canonical uppercase values."""
    assert {m.value for m in enum_cls} == expected_values


@pytest.mark.unit
def test_union_and_dissolution_types() -> None:
    """Verify UnionType and consolidated UnionDissolutionType string values."""
    assert UnionType.MARRIED == "MARRIED"
    assert UnionType.COMMON_LAW == "COMMON_LAW"
    assert UnionDissolutionType.DIVORCE == "DIVORCE"
    assert UnionDissolutionType.DEATH == "DEATH"


@pytest.mark.unit
def test_pedigree_type_upper_snake_case_values() -> None:
    """Verify PedigreeType uses UPPER_SNAKE_CASE tokens."""
    assert PedigreeType.BIRTH == "BIRTH"
    assert PedigreeType.ADOPTED == "ADOPTED"
    assert PedigreeType.STEP == "STEP"
    assert PedigreeType.FOSTER == "FOSTER"


@pytest.mark.unit
@pytest.mark.parametrize(
    ("member", "expected_value"),
    [
        (MannerOfDeath.NATURAL, "NATURAL"),
        (MannerOfDeath.ACCIDENT, "ACCIDENT"),
        (BirthPlurality.SINGLE, "SINGLE"),
        (BirthPlurality.TWIN, "TWIN"),
        (DispositionType.BURIAL, "BURIAL"),
        (DispositionType.CREMATION, "CREMATION"),
        (MaritalStatus.MARRIED, "MARRIED"),
        (MaritalStatus.WIDOWED, "WIDOWED"),
        (LegalPlaintiff.HUSBAND, "HUSBAND"),
        (DivorceDecreeType.ABSOLUTE, "ABSOLUTE"),
    ],
)
def test_vital_and_mortuary_upper_snake_case_values(
    member: str,
    expected_value: str,
) -> None:
    """Verify mortuary, marital, and decree enums use UPPER_SNAKE_CASE."""
    assert member == expected_value


@pytest.mark.unit
def test_relocated_biographical_enums_member_sets() -> None:
    """Verify EyeColor and HairColor declare complete canonical member sets."""
    assert {m.value for m in EyeColor} == {
        "BLUE",
        "BROWN",
        "GREY",
        "HAZEL",
        "BLACK",
        "GREEN",
        "OTHER",
        "UNKNOWN",
    }
    assert {m.value for m in HairColor} == {
        "BLONDE",
        "BROWN",
        "BLACK",
        "RED",
        "GREY",
        "BALD",
        "WHITE",
        "OTHER",
        "UNKNOWN",
    }


@pytest.mark.unit
def test_relocated_biographical_enums_coercion_and_samples() -> None:
    """Verify relocated biographical enums support from_raw coercion and canonical members."""
    assert EyeColor.from_raw("green") is EyeColor.GREEN
    assert HairColor.from_raw("white") is HairColor.WHITE
    assert PhysicalBuild.MEDIUM == "MEDIUM"
    assert EducationLevel.COLL == "COLL"


# ==============================================================================
# GROUP 4: Error Handling & Validation Failures
# Note: Strict invalid-value rejection on vital domain enums.
# ==============================================================================


@pytest.mark.regression
@pytest.mark.parametrize("bad_value", ["invalid", "DIVORCED", " MARRIED ", ""])
def test_union_dissolution_type_rejects_invalid_values(bad_value: str) -> None:
    """Verify UnionDissolutionType strictly rejects unregistered and untrimmed tokens."""
    with pytest.raises(ValueError):
        UnionDissolutionType(bad_value)
