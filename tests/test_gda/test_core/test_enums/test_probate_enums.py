"""Path: tests/test_gda/test_core/test_enums/test_probate_enums.py

Targeted behavioral test suite verifying probate bequest, inventory, and accounting enums.

Operational Role:
    Validates BequestType, EstatePropertyCategory, and ProbateLedgerEntryKind
    enum member tokens, StrEnum inheritance, and package re-export parity.
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

__version__ = "1.0.0+build.1"


@pytest.mark.unit
@pytest.mark.smoke
def test_probate_enums_canonical_tokens_and_reexports() -> None:
    """Verify BequestType, EstatePropertyCategory, and ProbateLedgerEntryKind tokens."""
    assert probate_enums.__all__ == sorted(probate_enums.__all__)
    for name in probate_enums.__all__:
        assert getattr(enums_pkg, name) is getattr(probate_enums, name)

    assert BequestType.REAL_ESTATE == "REAL_ESTATE"
    assert BequestType.PERSONAL_PROPERTY == "PERSONAL_PROPERTY"
    assert BequestType.MONETARY == "MONETARY"
    assert BequestType.RESIDUARY == "RESIDUARY"
    assert BequestType.GUARDIANSHIP == "GUARDIANSHIP"
    assert BequestType.OTHER == "OTHER"
    assert len(BequestType) == 6

    assert EstatePropertyCategory.REAL_ESTATE == "REAL_ESTATE"
    assert EstatePropertyCategory.LIVESTOCK == "LIVESTOCK"
    assert EstatePropertyCategory.HOUSEHOLD == "HOUSEHOLD"
    assert EstatePropertyCategory.TOOLS == "TOOLS"
    assert EstatePropertyCategory.NOTES_RECEIVABLE == "NOTES_RECEIVABLE"
    assert EstatePropertyCategory.CASH == "CASH"
    assert EstatePropertyCategory.OTHER == "OTHER"
    assert len(EstatePropertyCategory) == 7

    assert ProbateLedgerEntryKind.RECEIPT == "RECEIPT"
    assert ProbateLedgerEntryKind.DEBT_PAID == "DEBT_PAID"
    assert ProbateLedgerEntryKind.EXPENSE == "EXPENSE"
    assert ProbateLedgerEntryKind.DISTRIBUTION == "DISTRIBUTION"
    assert len(ProbateLedgerEntryKind) == 4
