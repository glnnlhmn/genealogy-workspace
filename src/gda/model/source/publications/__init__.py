"""Path: src/gda/model/source/publications/__init__.py

Serial publications, newspaper clippings, periodicals, and published history models.

Operational Role:
    Exports Publication, NewspaperClipRecord, PeriodicalArticleRecord, and
    PublicationEntry domain models.
"""

from __future__ import annotations

from gda.model.source.publications.newspaper import NewspaperClipRecord
from gda.model.source.publications.periodical import PeriodicalArticleRecord, PublicationEntry
from gda.model.source.publications.publication import Publication

__version__ = "1.0.0+build.2"

__all__ = [
    "NewspaperClipRecord",  # gda.model.source.publications.newspaper
    "PeriodicalArticleRecord",  # gda.model.source.publications.periodical
    "Publication",  # gda.model.source.publications.publication
    "PublicationEntry",  # gda.model.source.publications.periodical
]
