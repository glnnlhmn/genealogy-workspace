"""Path: tests/test_gda/test_core/test_enums/test_vital_enums.py

Targeted behavioral test suite verifying demographic and vital event enums.

Operational Role:
    Verifies HistoricNameType onomastic categories, domestic union models,
    pedigree relations, mortal disposition classifications, and vital condition
    modifiers (VitalModifier).

Test Structure & Protocol:
    - Atomized tests: 1:1 verification per behavioral contract.
    - Fully decorated: Explicitly decorated with registered pytest markers.
    - Dependencies: In-memory only; zero physical disk I/O.
"""

from __future__ import annotations

import pytest

from gda.core.enums.vital import (
    BirthPlurality,
    DispositionType,
    DivorceDecreeType,
    HistoricNameType,
    LegalPlaintiff,
    MannerOfDeath,
    MaritalHistoryDissolution,
    MaritalStatus,
    PedigreeType,
    UnionDissolutionType,
    UnionType,
    VitalModifier,
)

__version__ = "1.0.0+build.4"


# ==============================================================================
# GROUP 1: HistoricNameType Onomastic Classifications
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_historic_name_type_enum_members() -> None:
    """Verify HistoricNameType includes all cultural and historical name classifications."""
    assert HistoricNameType.PRIMARY == "PRIMARY"
    assert HistoricNameType.HISTORICAL == "HISTORICAL"
    assert HistoricNameType.COLLOQUIAL == "COLLOQUIAL"
    assert HistoricNameType.COLONIAL == "COLONIAL"
    assert HistoricNameType.INDIGENOUS == "INDIGENOUS"
    assert len(HistoricNameType) == 5


# ==============================================================================
# GROUP 2: Domestic Relations & Lineage
# ==============================================================================


@pytest.mark.unit
def test_union_and_dissolution_types() -> None:
    """Verify UnionType and UnionDissolutionType string representations."""
    assert UnionType.MARRIED == "MARRIED"
    assert UnionType.COMMON_LAW == "COMMON_LAW"
    assert UnionDissolutionType.DIVORCE == "DIVORCE"
    assert UnionDissolutionType.DEATH == "DEATH"


@pytest.mark.unit
def test_pedigree_type_values() -> None:
    """Verify PedigreeType lineage relationship classifications."""
    assert PedigreeType.BIRTH == "Birth"
    assert PedigreeType.ADOPTED == "Adopted"
    assert PedigreeType.STEP == "Step"
    assert PedigreeType.FOSTER == "Foster"


# ==============================================================================
# GROUP 3: Vital Events & Mortuary Assertions
# ==============================================================================


@pytest.mark.unit
def test_vital_assertions() -> None:
    """Verify manner of death, plurality, and disposition types."""
    assert MannerOfDeath.NATURAL == "Natural"
    assert MannerOfDeath.ACCIDENT == "Accident"
    assert BirthPlurality.SINGLE == "Single"
    assert BirthPlurality.TWIN == "Twin"
    assert DispositionType.BURIAL == "Burial"
    assert DispositionType.CREMATION == "Cremation"
    assert MaritalStatus.MARRIED == "Married"
    assert MaritalStatus.WIDOWED == "Widowed"
    assert LegalPlaintiff.HUSBAND == "Husband"
    assert DivorceDecreeType.ABSOLUTE == "Absolute (A Vinculo Matrimonii)"
    assert MaritalHistoryDissolution.DIVORCE == "Divorce"


# ==============================================================================
# GROUP 4: VitalModifier Invariants
# ==============================================================================


@pytest.mark.unit
def test_vital_modifier_values() -> None:
    """Verify VitalModifier classifications and string values."""
    assert VitalModifier.STILLBORN == "STILLBORN"
    assert VitalModifier.INFANT == "INFANT"
    assert VitalModifier.ILLEGITIMATE == "ILLEGITIMATE"
    assert VitalModifier.POSTHUMOUS == "POSTHUMOUS"
    assert VitalModifier.LEGITIMATED == "LEGITIMATED"
    assert len(VitalModifier) == 5
