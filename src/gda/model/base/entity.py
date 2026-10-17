# Name: entity.py
# Path: src/gda/model/base/entity.py

"""Core generic entity base model using Pydantic dataclasses.

Operational Role:
    Defines the fundamental building block ('EntityModel') for all master registry
    records (Individuals, Facts, Locations, Sites, Families) in the Genealogy Digital
    Archive (GDA). Combines AtomID identification, AuditStamp tracking via
    AuditableModel, in-place TombstoneRecord lifecycle, and research NoteIDs.

Architecture:
    - EntityModel[ID_T]: Generic Pydantic dataclass anchoring core domain entities.
"""

from __future__ import annotations

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.logging import GDALogger
from gda.model.atom.id import AtomID, NoteID
from gda.model.base.auditable import AuditableModel
from gda.model.base.tombstone import TombstoneRecord

__version__ = "1.0.0+build.r4"

_logger = GDALogger(__name__)


@dataclass(config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True))
class EntityModel[ID_T: AtomID](AuditableModel):
    """Generic base class uniting identity, audit, lifecycle, and archival notes."""

    id: ID_T
    tombstone: TombstoneRecord[ID_T] = Field(default_factory=TombstoneRecord)
    notes: list[NoteID] = Field(default_factory=list)

    def __post_init__(self) -> None:
        if self.tombstone.superseded_by is not None:
            if not isinstance(self.tombstone.superseded_by, type(self.id)):
                err_msg = (
                    f"EntityModel superseded_by type mismatch: expected {type(self.id).__name__}, "
                    f"got {type(self.tombstone.superseded_by).__name__}."
                )
                _logger.debug("EntityModel superseded_by type mismatch detected")
                raise TypeError(err_msg)

    @property
    def is_deprecated(self) -> bool:
        return self.tombstone.is_deprecated

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(id={self.id!r}, audit={self.audit!r}, "
            f"tombstone={self.tombstone!r}, notes={self.notes!r})"
        )
