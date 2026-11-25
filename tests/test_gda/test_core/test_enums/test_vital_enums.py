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

from typing import Any

import pytest

import gda.core.enums.vital as vital_enums
from gda.core.enums.vital import (
    BirthPlurality,
    DispositionType,
    DivorceDecreeType,
    HistoricNameType,
    LegalPlaintiff,
    MannerOfDeath,
    MaritalStatus,
    PedigreeType,
    UnionDissolutionType,
    UnionType,
    VitalModifier,
)

__version__ = "1.0.0+build.5"


# ==============================================================================
# GROUP 1: Smoke & Primary Entrypoints
# Note: Single smoke gate freezing the 15 authoritative vital exports (Phase 3).
# ==============================================================================


@pytest.mark.smoke
@pytest.mark.unit
def test_vital_enums_exposes_expected_public_interface() -> None:
    """Verify gda.core.enums.vital exports all 15 authoritative enums (Phase 3 TDD Red)."""
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
def test_historic_name_type_and_vital_modifier_values() -> None:
    """Verify HistoricNameType and VitalModifier canonical uppercase values."""
    assert HistoricNameType.PRIMARY == "PRIMARY"
    assert HistoricNameType.HISTORICAL == "HISTORICAL"
    assert HistoricNameType.COLLOQUIAL == "COLLOQUIAL"
    assert HistoricNameType.COLONIAL == "COLONIAL"
    assert HistoricNameType.INDIGENOUS == "INDIGENOUS"
    assert len(HistoricNameType) == 5

    assert VitalModifier.STILLBORN == "STILLBORN"
    assert VitalModifier.INFANT == "INFANT"
    assert VitalModifier.ILLEGITIMATE == "ILLEGITIMATE"
    assert VitalModifier.POSTHUMOUS == "POSTHUMOUS"
    assert VitalModifier.LEGITIMATED == "LEGITIMATED"
    assert len(VitalModifier) == 5


@pytest.mark.unit
def test_union_and_dissolution_types() -> None:
    """Verify UnionType and consolidated UnionDissolutionType string values."""
    assert UnionType.MARRIED == "MARRIED"
    assert UnionType.COMMON_LAW == "COMMON_LAW"
    assert UnionDissolutionType.DIVORCE == "DIVORCE"
    assert UnionDissolutionType.DEATH == "DEATH"


@pytest.mark.unit
def test_pedigree_type_upper_snake_case_values() -> None:
    """Verify PedigreeType uses UPPER_SNAKE_CASE tokens (Phase 3 TDD Red)."""
    assert PedigreeType.BIRTH == "BIRTH"
    assert PedigreeType.ADOPTED == "ADOPTED"
    assert PedigreeType.STEP == "STEP"
    assert PedigreeType.FOSTER == "FOSTER"


@pytest.mark.unit
def test_vital_and_mortuary_upper_snake_case_values() -> None:
    """Verify mortuary, marital, and decree enums use UPPER_SNAKE_CASE (Phase 3 TDD Red)."""
    assert MannerOfDeath.NATURAL == "NATURAL"
    assert MannerOfDeath.ACCIDENT == "ACCIDENT"
    assert BirthPlurality.SINGLE == "SINGLE"
    assert BirthPlurality.TWIN == "TWIN"
    assert DispositionType.BURIAL == "BURIAL"
    assert DispositionType.CREMATION == "CREMATION"
    assert MaritalStatus.MARRIED == "MARRIED"
    assert MaritalStatus.WIDOWED == "WIDOWED"
    assert LegalPlaintiff.HUSBAND == "HUSBAND"
    assert DivorceDecreeType.ABSOLUTE == "ABSOLUTE"


@pytest.mark.unit
def test_relocated_biographical_enums_in_vital_module() -> None:
    """Verify EyeColor, HairColor, PhysicalBuild, and EducationLevel live in vital (Phase 3)."""
    eye_color: Any = getattr(vital_enums, "EyeColor", None)
    hair_color: Any = getattr(vital_enums, "HairColor", None)
    physical_build: Any = getattr(vital_enums, "PhysicalBuild", None)
    education_level: Any = getattr(vital_enums, "EducationLevel", None)

    assert eye_color is not None, "EyeColor not yet relocated to vital.py"
    assert hair_color is not None, "HairColor not yet relocated to vital.py"
    assert physical_build is not None, "PhysicalBuild not yet relocated to vital.py"
    assert education_level is not None, "EducationLevel not yet relocated to vital.py"

    assert {m.value for m in eye_color} == {"BLUE", "BROWN", "GREY", "HAZEL", "BLACK"}
    assert {m.value for m in hair_color} == {"BLONDE", "BROWN", "BLACK", "RED", "GREY", "BALD"}
    assert physical_build.MEDIUM == "MEDIUM"
    assert education_level.COLL == "COLL"


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
