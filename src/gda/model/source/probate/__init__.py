"""Path: src/gda/model/source/probate/__init__.py

Last wills and testaments, codicils, estate inventories, and probate accounting models.

Operational Role:
    Exports ProbateRecord, WillBequest, EstateInventoryRecord, InventoryLineItem,
    and ProbateLedgerEntry domain models.
"""

from __future__ import annotations

from gda.model.source.probate.inventory import (
    EstateInventoryRecord,
    InventoryLineItem,
    ProbateLedgerEntry,
)
from gda.model.source.probate.will import ProbateRecord, WillBequest

__version__ = "1.0.0+build.2"

__all__ = [
    "EstateInventoryRecord",  # gda.model.source.probate.inventory
    "InventoryLineItem",  # gda.model.source.probate.inventory
    "ProbateLedgerEntry",  # gda.model.source.probate.inventory
    "ProbateRecord",  # gda.model.source.probate.will
    "WillBequest",  # gda.model.source.probate.will
]
