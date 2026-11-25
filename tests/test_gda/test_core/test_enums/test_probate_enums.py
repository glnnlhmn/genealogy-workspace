"""Path: tests/test_gda/test_core/test_enums/test_probate_enums.py

Targeted behavioral test suite verifying probate bequest, inventory, and accounting enums.

Operational Role:
    Validates gda.core.enums.probate public exports, package re-export parity,
    BequestType, EstatePropertyCategory, and ProbateLedgerEntryKind tokens,
    and strict invalid-value rejection.

Test Structure & Protocol:
    - Atomized & parametrized tests: 1:1 behavioral contract mapping.
    - Fully decorated: 5-marker taxonomy (smoke, unit, regression).
    - Dependencies: In-memory only; zero physical disk I/O.
"""

from __future__ import annotations

import pytest

import gda.core.enums as enums_pkg
import gda.core.enums.probate as probate_enums
from gda.core.enums.probate import (
    BequestType,
    EstatePropertyCategory,
    ProbateLedgerEntryKind,
)

__version__ = "1.0.0+build.2"


# ==============================================================================
# GROUP 1: Smoke & Primary Entrypoints
# Note: Single smoke gate verifying sorted exports and package re-export parity.
# ==============================================================================


@pytest.mark.smoke
@pytest.mark.unit
def test_probate_enums_exports_and_reexport_parity() -> None:
    """Verify gda.core.enums.probate.__all__ is sorted and re-exported from gda.core.enums."""
    assert probate_enums.__all__ == sorted(probate_enums.__all__)
    assert set(probate_enums.__all__) == {
        "BequestType",
        "EstatePropertyCategory",
        "ProbateLedgerEntryKind",
    }
    for name in probate_enums.__all__:
        assert getattr(enums_pkg, name) is getattr(probate_enums, name)


# ==============================================================================
# GROUP 2: Core Logic & Happy Paths
# Note: Canonical UPPER_SNAKE_CASE members across all 3 probate enums.
# ==============================================================================


@pytest.mark.unit
def test_probate_enums_canonical_tokens() -> None:
    """Verify BequestType, EstatePropertyCategory, and ProbateLedgerEntryKind tokens."""
    assert {m.value for m in BequestType} == {
        "REAL_ESTATE",
        "PERSONAL_PROPERTY",
        "MONETARY",
        "RESIDUARY",
        "GUARDIANSHIP",
        "OTHER",
    }
    assert {m.value for m in EstatePropertyCategory} == {
        "REAL_ESTATE",
        "LIVESTOCK",
        "HOUSEHOLD",
        "TOOLS",
        "NOTES_RECEIVABLE",
        "CASH",
        "OTHER",
    }
    assert {m.value for m in ProbateLedgerEntryKind} == {
        "RECEIPT",
        "DEBT_PAID",
        "EXPENSE",
        "DISTRIBUTION",
    }


# ==============================================================================
# GROUP 4: Error Handling & Validation Failures
# Note: Strict invalid-value rejection on probate enums.
# ==============================================================================


@pytest.mark.regression
@pytest.mark.parametrize("bad_value", ["INHERITANCE", "monetary", " OTHER ", ""])
def test_bequest_type_rejects_invalid_values(bad_value: str) -> None:
    """Verify BequestType strictly rejects unregistered, lowercase, and padded tokens."""
    with pytest.raises(ValueError):
        BequestType(bad_value)
