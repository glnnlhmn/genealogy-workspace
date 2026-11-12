"""Path: src/gda/model/base/__init__.py

Unified public facade for gda.model.base composite value objects and base entities.
"""

from __future__ import annotations

from gda.model.base.address import Address
from gda.model.base.age import Age
from gda.model.base.association import AssociatedIndividual
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate, TimePeriod
from gda.model.base.entity import BaseEntity, BaseEntityGUID, EntityLifecycleMixin
from gda.model.base.envelope import RegistryEnvelope
from gda.model.base.family import ChildLink, FamilyUnion
from gda.model.base.geo import Coordinates
from gda.model.base.media import DocumentSide, Media
from gda.model.base.name import (
    CanonicalName,
    HistoricalName,
    HistoricVariant,
    NameBase,
    NameLifecycleMixin,
    NamePerson,
    NameThing,
)
from gda.model.base.note import Note
from gda.model.base.source import RecordMetadata, SourceRecord, SourceReference
from gda.model.base.tombstone import Tombstone, is_tombstoned, stamp_tombstone
from gda.model.base.transcript import Legibility, TextQuality, Transcript

__version__ = "1.3.0+build.1"

__all__ = [
    "Address",
    "Age",
    "AssociatedIndividual",
    "AuditStamp",
    "BaseEntity",
    "BaseEntityGUID",
    "CanonicalName",
    "ChildLink",
    "Coordinates",
    "DocumentSide",
    "EntityLifecycleMixin",
    "EventDate",
    "FamilyUnion",
    "HistoricVariant",
    "HistoricalName",
    "Legibility",
    "Media",
    "NameBase",
    "NameLifecycleMixin",
    "NamePerson",
    "NameThing",
    "Note",
    "RecordMetadata",
    "RegistryEnvelope",
    "SourceRecord",
    "SourceReference",
    "TextQuality",
    "TimePeriod",
    "Tombstone",
    "Transcript",
    "is_tombstoned",
    "stamp_tombstone",
]
