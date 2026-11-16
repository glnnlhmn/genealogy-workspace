"""Path: src/gda/repository/military/__init__.py

SQLite repositories and in-memory collections for Military archival source records.
"""

from __future__ import annotations

from gda.repository.military.collection import (
    BountyLandWarrantCollection,
    MilitaryAwardCollection,
    MilitaryCasualtyCollection,
    MilitaryDraftCollection,
    MilitaryPensionCollection,
    MilitaryServiceCollection,
)
from gda.repository.military.repository import (
    BountyLandWarrantRepository,
    MilitaryAwardRepository,
    MilitaryCasualtyRepository,
    MilitaryDraftRepository,
    MilitaryPensionRepository,
    MilitaryServiceRepository,
)

__version__ = "1.0.0+build.1"

__all__ = [
    "BountyLandWarrantCollection",
    "BountyLandWarrantRepository",
    "MilitaryAwardCollection",
    "MilitaryAwardRepository",
    "MilitaryCasualtyCollection",
    "MilitaryCasualtyRepository",
    "MilitaryDraftCollection",
    "MilitaryDraftRepository",
    "MilitaryPensionCollection",
    "MilitaryPensionRepository",
    "MilitaryServiceCollection",
    "MilitaryServiceRepository",
]
