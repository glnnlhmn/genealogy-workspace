"""Path: tests/test_gda/test_core/test_enums/test_sources_enums.py

Targeted behavioral test suite verifying bibliographic and source enums.

Operational Role:
    Validates documentary categories, granular source records,
    educational attainments, and military conflict taxonomies.

Test Structure & Protocol:
    - Atomized tests: 1:1 verification per behavioral contract.
    - Fully decorated: Strictly unit and regression markers.
    - Dependencies: In-memory only; zero physical disk I/O.
"""

from __future__ import annotations

import pytest

from gda.core.enums.sources import (
    EducationLevel,
    MilitaryBranch,
    MilitaryConflict,
    MilitaryWar,
    SourceRecordCategory,
    SourceRecordType,
)

__version__ = "1.0.0+build.3"

# ==============================================================================
# GROUP 1: Document Classifications
# ==============================================================================


@pytest.mark.unit
def test_source_record_category_tokens() -> None:
    """Verify high-level archival category classifications."""
    assert SourceRecordCategory.VITAL == "VITAL"
    assert SourceRecordCategory.CENSUS == "CENSUS"
    assert SourceRecordCategory.CHURCH == "CHURCH"
    assert SourceRecordCategory.MILITARY == "MILITARY"
    assert SourceRecordCategory.PROBATE == "PROBATE"
    assert SourceRecordCategory.LAND == "LAND"


@pytest.mark.unit
def test_source_record_type_vital_and_probate() -> None:
    """Verify granular record document type tokens."""
    assert SourceRecordType.BIRTH_CERTIFICATE == "BIRTH_CERTIFICATE"
    assert SourceRecordType.DEATH_CERTIFICATE == "DEATH_CERTIFICATE"
    assert SourceRecordType.MARRIAGE_LICENSE == "MARRIAGE_LICENSE"
    assert SourceRecordType.LAST_WILL_AND_TESTAMENT == "LAST_WILL_AND_TESTAMENT"
    assert SourceRecordType.POPULATION_SCHEDULE == "POPULATION_SCHEDULE"


# ==============================================================================
# GROUP 2: Education & Military Taxonomies
# ==============================================================================


@pytest.mark.unit
def test_education_level_tokens() -> None:
    """Verify educational attainment tokens."""
    assert EducationLevel.ELEM == "ELEM"
    assert EducationLevel.HS == "HS"
    assert EducationLevel.COLL == "COLL"
    assert EducationLevel.GRAD == "GRAD"


@pytest.mark.unit
def test_military_branch_and_conflicts() -> None:
    """Verify military service branches and historical conflict codes."""
    assert MilitaryBranch.ARMY == "ARMY"
    assert MilitaryBranch.NAVY == "NAVY"
    assert (
        MilitaryConflict.CIVIL_WAR == "CW"
        if hasattr(MilitaryConflict, "CIVIL_WAR")
        else MilitaryConflict.CW == "CW"
    )
    assert MilitaryWar.CIVIL_WAR == "CIVIL_WAR"
    assert MilitaryWar.WWI == "WWI"
    assert MilitaryWar.WWII == "WWII"
