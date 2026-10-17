# Name: note.py
# Path: src/gda/model/base/note.py

"""Archival research note model using Pydantic dataclasses.

Operational Role:
    Defines the discrete research note structure ('NoteModel') across the
    Genealogy Digital Archive (GDA). Captures textual research memos, citations,
    discrepancy logs, and analytical findings anchored by NoteID and AuditStamp.

Architecture:
    - NoteType: Controlled enumeration for research note categories.
    - NoteModel: Pydantic dataclass validating research note records.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

from gda.core.introspectable import IntrospectableMixin
from gda.core.logging import GDALogger
from gda.model.atom.errors import AtomFormatError
from gda.model.atom.id import NoteID
from gda.model.base.audit import AuditStamp

__version__ = "1.0.0+build.r4"

_logger = GDALogger(__name__)


class NoteType(StrEnum):
    """Controlled classifications for archival research notes."""

    RESEARCH = "RESEARCH"
    CITATION = "CITATION"
    TRANSCRIPTION = "TRANSCRIPTION"
    DISCREPANCY = "DISCREPANCY"
    ANALYSIS = "ANALYSIS"
    GENERAL = "GENERAL"


@dataclass(config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True))
class NoteModel(IntrospectableMixin):
    """Archival research note capturing categorized textual memos and audit stamps."""

    note_id: NoteID
    note_type: NoteType
    text: str
    audit: AuditStamp

    def __post_init__(self) -> None:
        if not self.text.strip():
            err_msg = "NoteModel text cannot be empty or whitespace."
            _logger.debug("NoteModel text validation failed")
            raise AtomFormatError(err_msg, details={"note_id": str(self.note_id)})

    def update_text(self, text: str, audit: AuditStamp) -> NoteModel:
        return NoteModel(
            note_id=self.note_id,
            note_type=self.note_type,
            text=text,
            audit=audit,
        )

    def __repr__(self) -> str:
        return (
            f"NoteModel(note_id={self.note_id!r}, note_type={self.note_type}, "
            f"text='{self.text}', audit={self.audit!r})"
        )
