"""Path: src/gda/model/base/source_record.py

Canonical composite entity representing an evidentiary source record.

Operational Role:
    Defines the foundational document-level source representation for citations,
    archival repository linkages, decoupled media assets, collateral participant
    associations, and soft-deprecation lifecycle metadata.
"""

from __future__ import annotations

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.errors import ModelFormatError
from gda.core.introspectable import IntrospectableMixin
from gda.enums.sources import SourceRecordCategory
from gda.model.atom.id import MediaID, RepositoryID, SourceID
from gda.model.atom.urn import ArchivalURN
from gda.model.base.association import AssociatedIndividual
from gda.model.base.audit import AuditStamp
from gda.model.base.tombstone import TombstoneRecord

__version__ = "1.0.0+build.2"

__all__ = ["SourceRecord"]


@dataclass(config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True))
class SourceRecord(IntrospectableMixin):
    """Canonical composite representing an evidentiary source document."""

    source_id: SourceID
    source_urn: ArchivalURN
    record_category: SourceRecordCategory
    description: str
    repository_id: RepositoryID
    audit: AuditStamp
    media_ids: list[MediaID] = Field(default_factory=list)
    associated_people: list[AssociatedIndividual] = Field(default_factory=list)
    tombstone: TombstoneRecord | None = Field(default=None)

    def __post_init__(self) -> None:
        """Enforce composite invariants on string boundaries and soft deprecation."""
        desc = self.description.strip()
        if not desc:
            raise ModelFormatError(
                "SourceRecord 'description' cannot be empty or whitespace-only.",
                details={"source_id": str(self.source_id)},
            )
        object.__setattr__(self, "description", desc)

        if not isinstance(self.source_urn, ArchivalURN):
            raise ModelFormatError(
                f"SourceRecord 'source_urn' must be an instance of ArchivalURN, "
                f"got {type(self.source_urn).__name__}."
            )

        if not isinstance(self.repository_id, RepositoryID):
            raise ModelFormatError(
                f"SourceRecord 'repository_id' must be an instance of RepositoryID, "
                f"got {type(self.repository_id).__name__}."
            )

    @property
    def is_deprecated(self) -> bool:
        """Return whether the record is soft-deprecated via an attached tombstone."""
        return self.tombstone.is_deprecated if self.tombstone is not None else False

    @property
    def media_count(self) -> int:
        """Return the count of attached media references."""
        return len(self.media_ids)

    @property
    def participant_count(self) -> int:
        """Return the count of collateral associated individuals."""
        return len(self.associated_people)

    def __str__(self) -> str:
        return f"SourceRecord [{self.record_category.value}] {self.source_urn} ({self.source_id})"
