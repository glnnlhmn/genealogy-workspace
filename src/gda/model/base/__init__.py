"""Path: src/gda/model/base/__init__.py

Base model value objects, audit envelopes, and tombstoning contracts.
"""

from __future__ import annotations

from gda.model.base.address import Address
from gda.model.base.age import Age
from gda.model.base.association import AssociatedIndividual, AssociationRole
from gda.model.base.audit import AuditStamp
from gda.model.base.envelope import RegistryEnvelope
from gda.model.base.media import DocumentSide, Media
from gda.model.base.name import CanonicalName
from gda.model.base.note import Note, NoteType
from gda.model.base.record_metadata import RecordMetadata
from gda.model.base.source_reference import SourceReference
from gda.model.base.tombstone import TombstoneRecord
from gda.model.base.transcript import Legibility, TextQuality, Transcript

__version__ = "1.0.0+build.6"

__all__ = [
    "Address",
    "Age",
    "AssociatedIndividual",
    "AssociationRole",
    "AuditStamp",
    "CanonicalName",
    "DocumentSide",
    "Legibility",
    "Media",
    "Note",
    "NoteType",
    "RecordMetadata",
    "RegistryEnvelope",
    "SourceReference",
    "TextQuality",
    "TombstoneRecord",
    "Transcript",
]
