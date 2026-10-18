"""Path: src/gda/model/base/entity.py

Foundational base entity schemas for graph nodes and digital assets.

Operational Role:
    Defines generic BaseEntity parameterized by AtomID subclasses for canonical
    domain entities, and BaseEntityGUID for primary source, media, and citation assets
    minted strictly with UUIDv4 surrogates. Implements unified audit and tombstone delegation.

Classes:
    BaseEntity: Generic base node parameterized by ID_T (bound to AtomID).
    BaseEntityGUID: Base node parameterized by string-based UUIDv4 identifiers.
"""

from __future__ import annotations

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.introspectable import IntrospectableMixin
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import AtomID, NoteID
from gda.model.base.audit import AuditStamp
from gda.model.base.tombstone import TombstoneRecord

__version__ = "1.0.0+build.2"


@dataclass(config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True))
class BaseEntity[ID_T: AtomID](IntrospectableMixin):
    """Generic archival entity node composing identity, audit, and tombstone records."""

    id: ID_T = Field(..., description="Canonical strongly-typed domain identifier.")
    audit: AuditStamp = Field(..., description="Lifecycle audit metadata.")
    tombstone: TombstoneRecord[ID_T] = Field(
        default_factory=TombstoneRecord,
        description="Lifecycle deprecation and supersession status.",
    )
    notes: list[NoteID] = Field(
        default_factory=list,
        description="Associated archival research note identifiers.",
    )

    def __post_init__(self) -> None:
        """Enforce identity and supersession type alignment."""
        if self.tombstone.superseded_by is not None:
            if not isinstance(self.tombstone.superseded_by, type(self.id)):
                raise TypeError(
                    f"superseded_by type mismatch: expected {type(self.id).__name__}, "
                    f"got {type(self.tombstone.superseded_by).__name__}."
                )

    @property
    def created_at(self) -> IsoTimestamp:
        """Expose record creation timestamp from audit stamp."""
        return self.audit.created_at

    @property
    def updated_at(self) -> IsoTimestamp:
        """Expose record updated timestamp from audit stamp."""
        return self.audit.updated_at

    @property
    def is_deprecated(self) -> bool:
        """Expose deprecation status from tombstone."""
        return self.tombstone.is_deprecated

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(id={self.id!r}, audit={self.audit!r}, "
            f"tombstone={self.tombstone!r}, notes={self.notes!r})"
        )


@dataclass(config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True))
class BaseEntityGUID(IntrospectableMixin):
    """Archival digital asset entity identified by a UUIDv4 surrogate identifier."""

    id: str = Field(..., description="Canonical UUIDv4 surrogate identifier.")
    audit: AuditStamp = Field(..., description="Lifecycle audit metadata.")
    tombstone: TombstoneRecord[str] = Field(
        default_factory=TombstoneRecord,
        description="Lifecycle deprecation and supersession status.",
    )
    notes: list[NoteID] = Field(
        default_factory=list,
        description="Associated archival research note identifiers.",
    )

    def __post_init__(self) -> None:
        """Enforce string-based identity and supersession type alignment."""
        if self.tombstone.superseded_by is not None:
            if not isinstance(self.tombstone.superseded_by, str):
                raise TypeError(
                    f"superseded_by type mismatch: expected str, "
                    f"got {type(self.tombstone.superseded_by).__name__}."
                )

    @property
    def created_at(self) -> IsoTimestamp:
        """Expose record creation timestamp from audit stamp."""
        return self.audit.created_at

    @property
    def updated_at(self) -> IsoTimestamp:
        """Expose record updated timestamp from audit stamp."""
        return self.audit.updated_at

    @property
    def is_deprecated(self) -> bool:
        """Expose deprecation status from tombstone."""
        return self.tombstone.is_deprecated

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(id={self.id!r}, audit={self.audit!r}, "
            f"tombstone={self.tombstone!r}, notes={self.notes!r})"
        )
