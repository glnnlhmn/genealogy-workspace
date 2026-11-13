"""Path: src/gda/model/publications/__init__.py

Serial publications, newspaper clippings, periodicals, and published history models.

Operational Role:
    Exports Publication, NewspaperClipRecord, PeriodicalArticleRecord, and
    PublicationEntry domain models.
"""

from __future__ import annotations

from gda.model.publications.newspaper import NewspaperClipRecord
from gda.model.publications.periodical import PeriodicalArticleRecord, PublicationEntry
from gda.model.publications.publication import Publication

__version__ = "1.1.0+build.1"

__all__ = [
    "NewspaperClipRecord",
    "PeriodicalArticleRecord",
    "Publication",
    "PublicationEntry",
]
