"""Path: src/gda/model/base/source_reference.py

Archival citation and source reference representation using Pydantic dataclasses.

Operational Role:
    Defines the evidentiary reference structure ('SourceReference') linking
    facts, events, and entity assertions to archival source repositories. Captures
    source identifiers, citation texts, page coordinates, and evidentiary certainty.

Architecture:
    - SourceReference: Pydantic dataclass linking assertions to sources.
"""

from __future__ import annotations

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

from gda.core.errors import ModelFormatError
from gda.core.introspectable import IntrospectableMixin
from gda.core.logging import GDALogger
from gda.model.atom.id import SourceID
from gda.model.atom.scalar import ConfidenceScore, QuayScore

__version__ = "1.0.0+build.3"

_logger = GDALogger(__name__)


@dataclass(config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True))
class SourceReference(IntrospectableMixin):
    """Archival source pointer attaching evidence to assertions."""

    citation_text: str
    source_id: SourceID | None = None
    page_or_side: str | None = None
    quay: QuayScore | None = None
    confidence: ConfidenceScore | None = None

    def __post_init__(self) -> None:
        if not self.citation_text.strip():
            err_msg = "SourceReference citation_text cannot be empty."
            _logger.debug("SourceReference citation validation failed")
            raise ModelFormatError(err_msg, details={"field": "citation_text"})

    def __str__(self) -> str:
        if self.page_or_side:
            return f"{self.citation_text} (p. {self.page_or_side})"
        return self.citation_text

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(citation_text='{self.citation_text}', "
            f"source_id={self.source_id!r}, page_or_side={self.page_or_side!r}, "
            f"quay={self.quay!r}, confidence={self.confidence!r})"
        )
