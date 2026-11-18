"""Path: src/gda/repository/other/__init__.py

SQLite repository and in-memory collection for Other Miscellaneous archival sources.
"""

from __future__ import annotations

from gda.repository.other.collection import OtherMiscellaneousCollection
from gda.repository.other.repository import OtherMiscellaneousRepository

__version__ = "1.0.0+build.1"

__all__ = [
    "OtherMiscellaneousCollection",
    "OtherMiscellaneousRepository",
]
