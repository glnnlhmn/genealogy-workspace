"""Path: src/gda/enums/core.py

Backward-compatible re-export facade routing core enums to gda.core.enums.
"""

from __future__ import annotations

from gda.core.enums import (
    AssociatedRole,
    FactType,
    IDType,
    OperationalStatus,
    Sex,
    SmartIDPrefix,
)

__all__ = [
    "AssociatedRole",
    "FactType",
    "IDType",
    "OperationalStatus",
    "Sex",
    "SmartIDPrefix",
]
