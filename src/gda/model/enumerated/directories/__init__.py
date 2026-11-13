"""Path: src/gda/model/enumerated/directories/__init__.py

City, business, farmers', and civic/voter directory enumeration records.
"""

from __future__ import annotations

from gda.core.enums.fiscal import ResidentialStatus
from gda.model.enumerated.directories.base import (
    DirectoryEntry,
    DirectoryRollRecord,
)

__version__ = "1.0.0+build.1"

__all__ = [
    "DirectoryEntry",
    "DirectoryRollRecord",
    "ResidentialStatus",
]
