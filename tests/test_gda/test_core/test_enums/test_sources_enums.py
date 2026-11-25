"""Path: tests/test_gda/test_core/test_enums/test_sources_enums.py

Targeted behavioral test suite verifying bibliographic and source enums.

Operational Role:
    Validates gda.core.enums.sources public exports (SourceRecordCategory and
    SourceRecordType) following Phase 3 retirement of MilitaryConflict and
    relocation of MilitaryDraftType/MilitaryWar to military.py and
    EducationLevel to vital.py.

Test Structure & Protocol:
    - Atomized & parametrized tests: 1:1 behavioral contract mapping.
    - Fully decorated: 5-marker taxonomy (smoke, unit, regression).
    - Dependencies: In-memory only; zero physical disk I/O.
"""

from __future__ import annotations

import pytest

import gda.core.enums.sources as sources_enums
from gda.core.enums.sources import (
    SourceRecordCategory,
    SourceRecordType,
)

__version__ = "1.0.0+build.5"


# ==============================================================================
# GROUP 1: Smoke & Primary Entrypoints
# Note: Single smoke gate freezing the 2 authoritative source exports (Phase 3).
# ==============================================================================


@pytest.mark.smoke
@pytest.mark.unit
def test_sources_enums_exposes_expected_public_interface() -> None:
    """Verify gda.core.enums.sources exports only SourceRecordCategory and SourceRecordType."""
    assert set(sources_enums.__all__) == {"SourceRecordCategory", "SourceRecordType"}


# ==============================================================================
# GROUP 2: Core Logic & Happy Paths
# Note: High-level source categories and granular document type tokens.
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
# GROUP 4: Error Handling & Validation Failures
# Note: Strict invalid-value rejection on source enums.
# ==============================================================================


@pytest.mark.regression
@pytest.mark.parametrize("bad_value", ["UNKNOWN_CAT", "vital", " CENSUS ", ""])
def test_source_record_category_rejects_invalid_values(bad_value: str) -> None:
    """Verify SourceRecordCategory strictly rejects unregistered and untrimmed tokens."""
    with pytest.raises(ValueError):
        SourceRecordCategory(bad_value)
