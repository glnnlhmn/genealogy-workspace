"""Path: tests/test_gda/test_core/test_enums/test_immigration_enums.py

Targeted behavioral test suite verifying immigration and naturalization enums.

Operational Role:
    Validates gda.core.enums.immigration public exports, package re-export
    parity, ArrivalPassageClass and NaturalizationStage tokens, and strict
    invalid-value rejection.

Test Structure & Protocol:
    - Atomized & parametrized tests: 1:1 behavioral contract mapping.
    - Fully decorated: 5-marker taxonomy (smoke, unit, regression).
    - Dependencies: In-memory only; zero physical disk I/O.
"""

from __future__ import annotations

import pytest

import gda.core.enums as enums_pkg
import gda.core.enums.immigration as imm_enums
from gda.core.enums.immigration import (
    ArrivalPassageClass,
    NaturalizationStage,
)

__version__ = "1.0.0+build.2"


# ==============================================================================
# GROUP 1: Smoke & Primary Entrypoints
# Note: Single smoke gate verifying sorted exports and package re-export parity.
# ==============================================================================


@pytest.mark.smoke
@pytest.mark.unit
def test_immigration_enums_exports_and_reexport_parity() -> None:
    """Verify gda.core.enums.immigration.__all__ is sorted and re-exported."""
    assert imm_enums.__all__ == sorted(imm_enums.__all__)
    assert set(imm_enums.__all__) == {"ArrivalPassageClass", "NaturalizationStage"}
    for name in imm_enums.__all__:
        assert getattr(enums_pkg, name) is getattr(imm_enums, name)


# ==============================================================================
# GROUP 2: Core Logic & Happy Paths
# Note: Canonical UPPER_SNAKE_CASE members for passage and naturalization.
# ==============================================================================


@pytest.mark.unit
def test_immigration_enums_canonical_tokens() -> None:
    """Verify ArrivalPassageClass and NaturalizationStage canonical tokens."""
    assert {m.value for m in ArrivalPassageClass} == {
        "STEERAGE",
        "CABIN",
        "SECOND_CABIN",
        "CREW",
        "OVERLAND",
        "OTHER",
    }
    assert {m.value for m in NaturalizationStage} == {
        "DECLARATION_OF_INTENTION",
        "PETITION",
        "DEPOSITION_OF_WITNESS",
        "OATH_OF_ALLEGIANCE",
        "CERTIFICATE",
        "DENIAL_OR_DISMISSAL",
    }


# ==============================================================================
# GROUP 4: Error Handling & Validation Failures
# Note: Strict invalid-value rejection on immigration enums.
# ==============================================================================


@pytest.mark.regression
@pytest.mark.parametrize("bad_value", ["FIRST_CLASS", "steerage", " CABIN ", ""])
def test_arrival_passage_class_rejects_invalid_values(bad_value: str) -> None:
    """Verify ArrivalPassageClass strictly rejects unregistered and untrimmed tokens."""
    with pytest.raises(ValueError):
        ArrivalPassageClass(bad_value)
