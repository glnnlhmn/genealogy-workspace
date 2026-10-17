# Name: __init__.py
# Path: src/gda/model/base/__init__.py

"""Base model primitives, audit envelopes, family graphs, and tombstoning contracts."""

from __future__ import annotations

from gda.model.base.address import StreetAddressModel
from gda.model.base.age import AgeRecordModel
from gda.model.base.association import AssociatedPersonModel, AssociationRole
from gda.model.base.audit import AuditStamp
from gda.model.base.auditable import AuditableModel
from gda.model.base.entity import EntityModel
from gda.model.base.envelope import RegistryEnvelope
from gda.model.base.family import (
    BaseFamilyModel,
    FamilyChildModel,
    PedigreeLinkType,
    UnionType,
)
from gda.model.base.media import DocumentSide, MediaModel
from gda.model.base.name import CanonicalNameModel
from gda.model.base.note import NoteModel, NoteType
from gda.model.base.record_metadata import RecordMetadataModel
from gda.model.base.source_ref import SourceReferenceModel
from gda.model.base.tombstone import TombstoneRecord
from gda.model.base.transcript import Legibility, TextQuality, TranscriptModel

__version__ = "1.0.0+build.r5"

__all__ = [
    "AgeRecordModel",
    "AssociatedPersonModel",
    "AssociationRole",
    "AuditStamp",
    "AuditableModel",
    "BaseFamilyModel",
    "CanonicalNameModel",
    "DocumentSide",
    "EntityModel",
    "FamilyChildModel",
    "Legibility",
    "MediaModel",
    "NoteModel",
    "NoteType",
    "PedigreeLinkType",
    "RecordMetadataModel",
    "RegistryEnvelope",
    "SourceReferenceModel",
    "StreetAddressModel",
    "TextQuality",
    "TombstoneRecord",
    "TranscriptModel",
    "UnionType",
]
