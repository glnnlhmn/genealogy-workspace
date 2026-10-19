"""Path: tests/test_gda/test_enums/test_vital_enums.py

Targeted behavioral test suite verifying demographic and vital event enums.

Operational Role:
    Verifies NameStatus onomastic categories, domestic union models,
    pedigree relations, and mortal disposition classifications.

Test Structure & Protocol:
    - Atomized tests: 1:1 verification per behavioral contract.
    - Fully decorated: Explicitly decorated with registered pytest markers.
    - Dependencies: In-memory only; zero physical disk I/O.
"""

from __future__ import annotations

import pytest

from gda.enums.vital import (
    BirthPlurality,
    DispositionType,
    DivorceDecreeType,
    LegalPlaintiff,
    MannerOfDeath,
    MaritalHistoryDissolution,
    MaritalStatus,
    NameStatus,
    PedigreeType,
    UnionDissolutionType,
    UnionType,
)

__version__ = "0.1.0+build.1"

# ==============================================================================
# GROUP 1: NameStatus Onomastic Classifications
# Note: Verification of personal name categorization
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_name_status_enum_members() -> None:
    """Verify NameStatus includes all cultural and historical name classifications."""
    assert NameStatus.PRIMARY == "PRIMARY"
    assert NameStatus.HISTORICAL == "HISTORICAL"
    assert NameStatus.COLLOQUIAL == "COLLOQUIAL"
    assert NameStatus.COLONIAL == "COLONIAL"
    assert NameStatus.INDIGENOUS == "INDIGENOUS"


# ==============================================================================
# GROUP 2: Domestic Relations & Lineage
# Note: Verification of UnionType, Dissolution, and Pedigree models
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
# Note: Verification of MannerOfDeath, BirthPlurality, and Dispositions
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
