"""Path: src/gda/model/base/__init__.py

Foundational composite value objects, entity envelopes, and lifecycle mixins.

Operational Role:
    Unified public export facade for Tier-1 and Tier-2 composite value objects,
    temporal spans, geospatial coordinates, audit stamps, tombstone lifecycle
    helpers, onomastic structures, archival source citations, base entity
    classes, and registry persistence envelopes.
"""

from __future__ import annotations

from gda.model.base.address import Address
from gda.model.base.age import Age
from gda.model.base.association import AssociatedIndividual
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate, TimePeriod
from gda.model.base.entity import (
    BaseEntity,
    BaseEntityGUID,
    EntityLifecycleMixin,
)
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
from gda.model.base.source import (
    RecordMetadata,
    SourceRecord,
    SourceReference,
)
from gda.model.base.tombstone import (
    Tombstone,
    is_tombstoned,
    stamp_tombstone,
)
from gda.model.base.transcript import (
    Legibility,
    TextQuality,
    Transcript,
)

__version__ = "1.0.0+build.2"

__all__ = [
    "Address",  # address.py
    "Age",  # age.py
    "AssociatedIndividual",  # association.py
    "AuditStamp",  # audit.py
    "BaseEntity",  # entity.py
    "BaseEntityGUID",  # entity.py
    "CanonicalName",  # name.py
    "ChildLink",  # family.py
    "Coordinates",  # geo.py
    "DocumentSide",  # media.py
    "EntityLifecycleMixin",  # entity.py
    "EventDate",  # date.py
    "FamilyUnion",  # family.py
    "HistoricVariant",  # name.py
    "HistoricalName",  # name.py
    "Legibility",  # transcript.py
    "Media",  # media.py
    "NameBase",  # name.py
    "NameLifecycleMixin",  # name.py
    "NamePerson",  # name.py
    "NameThing",  # name.py
    "Note",  # note.py
    "RecordMetadata",  # source.py
    "RegistryEnvelope",  # envelope.py
    "SourceRecord",  # source.py
    "SourceReference",  # source.py
    "TextQuality",  # transcript.py
    "TimePeriod",  # date.py
    "Tombstone",  # tombstone.py
    "Transcript",  # transcript.py
    "is_tombstoned",  # tombstone.py
    "stamp_tombstone",  # tombstone.py
]
