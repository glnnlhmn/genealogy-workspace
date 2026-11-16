"""Path: src/gda/repository/publications/__init__.py

SQLite repositories and in-memory collections for Publications archival source records.
"""

from __future__ import annotations

from gda.repository.publications.collection import (
    NewspaperClipCollection,
    PeriodicalArticleCollection,
    PublicationCollection,
)
from gda.repository.publications.repository import (
    NewspaperClipRepository,
    PeriodicalArticleRepository,
    PublicationRepository,
)

__version__ = "1.0.0+build.2"

__all__ = [
    "NewspaperClipCollection",
    "NewspaperClipRepository",
    "PeriodicalArticleCollection",
    "PeriodicalArticleRepository",
    "PublicationCollection",
    "PublicationRepository",
]
