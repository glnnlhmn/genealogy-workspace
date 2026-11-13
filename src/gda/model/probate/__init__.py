"""Path: src/gda/model/probate/__init__.py

Last wills and testaments, codicils, estate inventories, and probate accounting models.

Operational Role:
    Exports ProbateRecord, WillBequest, EstateInventoryRecord, InventoryLineItem,
    and ProbateLedgerEntry domain models.
"""

from __future__ import annotations

from gda.model.probate.inventory import (
    EstateInventoryRecord,
    InventoryLineItem,
    ProbateLedgerEntry,
)
from gda.model.probate.will import ProbateRecord, WillBequest

__version__ = "1.1.0+build.1"

__all__ = [
    "EstateInventoryRecord",
    "InventoryLineItem",
    "ProbateLedgerEntry",
    "ProbateRecord",
    "WillBequest",
]
