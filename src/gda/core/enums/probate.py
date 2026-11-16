"""Path: src/gda/core/enums/probate.py

Probate bequest, estate inventory property, and administration accounting enums.

Operational Role:
    Defines controlled categorical enumerations for testamentary devise/legacy
    classifications, estate appraisal asset categories, and administration
    accounting ledger entry kinds.
"""

from __future__ import annotations

from enum import StrEnum

__version__ = "1.0.0+build.1"

__all__ = [
    "BequestType",
    "EstatePropertyCategory",
    "ProbateLedgerEntryKind",
]


class BequestType(StrEnum):
    """Classification of testamentary devises, legacies, and guardianship provisions."""

    REAL_ESTATE = "REAL_ESTATE"
    PERSONAL_PROPERTY = "PERSONAL_PROPERTY"
    MONETARY = "MONETARY"
    RESIDUARY = "RESIDUARY"
    GUARDIANSHIP = "GUARDIANSHIP"
    OTHER = "OTHER"


class EstatePropertyCategory(StrEnum):
    """Taxonomic asset classifications on historical estate appraisal inventories."""

    REAL_ESTATE = "REAL_ESTATE"
    LIVESTOCK = "LIVESTOCK"
    HOUSEHOLD = "HOUSEHOLD"
    TOOLS = "TOOLS"
    NOTES_RECEIVABLE = "NOTES_RECEIVABLE"
    CASH = "CASH"
    OTHER = "OTHER"


class ProbateLedgerEntryKind(StrEnum):
    """Accounting line classifications in estate administration and guardian accounts."""

    RECEIPT = "RECEIPT"
    DEBT_PAID = "DEBT_PAID"
    EXPENSE = "EXPENSE"
    DISTRIBUTION = "DISTRIBUTION"
