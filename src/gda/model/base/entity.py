"""Path: src/gda/model/base/entity.py

Foundational base entity schemas and lifecycle mixin for domain entities and assets.

Operational Role:
    Defines EntityLifecycleMixin providing unified audit management, tombstone
    deprecation, and copy-on-write container operations for embedded Note value
    objects. Defines generic BaseEntity parameterized by AtomID subclasses for canonical
    domain entities, and BaseEntityGUID for primary source, media, and citation assets.

Classes:
    EntityLifecycleMixin: Reusable lifecycle and embedded note manager mixin.
    BaseEntity: Generic base node parameterized by ID_T (bound to AtomID).
    BaseEntityGUID: Base node parameterized by string-based UUIDv4 identifiers.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from typing import Any, Literal, Self

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.introspectable import IntrospectableMixin
from gda.core.logging import GDALogger
from gda.enums.archival import NoteType
from gda.enums.core import SmartIDPrefix
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import AtomID, NoteID, SourceID
from gda.model.base.audit import AuditStamp
from gda.model.base.note import Note
from gda.model.base.tombstone import Tombstone
from gda.util.ids import extract_max_smart_id, mint_smart_id

__version__ = "1.1.0+build.7"

__all__ = ["BaseEntity", "BaseEntityGUID", "EntityLifecycleMixin"]

_logger = GDALogger(__name__)


class EntityLifecycleMixin(IntrospectableMixin):
    """Reusable lifecycle, deprecation, and embedded note management mixin.

    Provides copy-on-write state mutators for audit timestamps, tombstone lifecycle
    transitions, and embedded Note collection operations across all entity models.
    """

    id: Any
    audit: AuditStamp
    tombstone: Any
    notes: list[Note]

    # ==========================================================================
    # SECTION 1: AUDIT ATTRIBUTE HELPERS
    # ==========================================================================

    @property
    def created_at(self) -> IsoTimestamp:
        """Expose record creation timestamp from audit stamp."""
        return self.audit.created_at

    @property
    def updated_at(self) -> IsoTimestamp:
        """Expose record updated timestamp from audit stamp."""
        return self.audit.updated_at

    @property
    def is_modified(self) -> bool:
        """Return True if updated_at timestamp is strictly after created_at."""
        return self.audit.updated_at.value > self.audit.created_at.value

    def touch(self, timestamp: IsoTimestamp | None = None) -> Self:
        """Return a copy with refreshed updated_at timestamp on the audit stamp."""
        new_ts = timestamp if timestamp is not None else IsoTimestamp.now_utc()
        _logger.debug(
            "Touching entity lifecycle timestamp",
            details={"entity_id": str(self.id), "timestamp": str(new_ts)},
        )
        return replace(self, audit=self.audit.touch(new_ts))

    # ==========================================================================
    # SECTION 2: TOMBSTONE ATTRIBUTE HELPERS
    # ==========================================================================

    @property
    def is_deprecated(self) -> bool:
        """Expose deprecation status from tombstone."""
        return self.tombstone.is_deprecated

    @property
    def superseded_by(self) -> Any:
        """Expose superseding identifier if deprecated; None otherwise."""
        return self.tombstone.superseded_by

    def deprecate(
        self,
        superseded_by: Any = None,
        timestamp: IsoTimestamp | None = None,
    ) -> Self:
        """Return a copy marked as deprecated with optional successor reference."""
        now_ts = timestamp if timestamp is not None else IsoTimestamp.now_utc()
        _logger.debug(
            "Deprecating entity",
            details={"entity_id": str(self.id), "superseded_by": str(superseded_by)},
        )
        new_tombstone = self.tombstone.retire(timestamp=now_ts, superseded_by=superseded_by)
        return replace(self, audit=self.audit.touch(now_ts), tombstone=new_tombstone)

    def restore(self, timestamp: IsoTimestamp | None = None) -> Self:
        """Return a copy with tombstone restored to active state."""
        now_ts = timestamp if timestamp is not None else IsoTimestamp.now_utc()
        _logger.debug("Restoring deprecated entity", details={"entity_id": str(self.id)})
        target_tombstone_cls = type(self.tombstone)
        restored_tombstone = target_tombstone_cls(is_deprecated=False, superseded_by=None)
        return replace(self, audit=self.audit.touch(now_ts), tombstone=restored_tombstone)

    # ==========================================================================
    # SECTION 3: EMBEDDED NOTE CONTAINER HELPERS
    # ==========================================================================

    @property
    def has_notes(self) -> bool:
        """Return True if entity has at least one embedded research note."""
        return bool(self.notes)

    @property
    def note_count(self) -> int:
        """Return integer count of embedded research notes."""
        return len(self.notes)

    def add_note(
        self,
        text: str,
        note_type: NoteType | str = NoteType.GENERAL,
        title: str | None = None,
        sources: list[SourceID | str] | None = None,
        tags: list[str] | None = None,
    ) -> Self:
        """Return a copy with an embedded note appended and refreshed audit."""
        max_seq = extract_max_smart_id(self.notes, prefix=SmartIDPrefix.NOT)
        next_note_id = NoteID(mint_smart_id(SmartIDPrefix.NOT, max_seq + 1, padding=6))

        _logger.debug(
            "Minting embedded note for entity",
            details={
                "entity_id": str(self.id),
                "note_id": str(next_note_id),
                "note_type": str(note_type),
            },
        )

        new_note = Note.create(
            note_id=next_note_id,
            note_type=note_type,
            text=text,
            title=title,
            sources=sources,
            tags=tags,
        )
        return replace(
            self,
            audit=self.audit.touch(IsoTimestamp.now_utc()),
            notes=[*self.notes, new_note],
        )

    def delete_note(self, note_id: NoteID | str) -> Self:
        """Return a copy removing target note without compacting sibling IDs."""
        target_str = str(note_id)
        filtered = [n for n in self.notes if str(n.note_id) != target_str]
        if len(filtered) == len(self.notes):
            _logger.debug(
                "Delete note no-op: note not found",
                details={"entity_id": str(self.id), "target_note_id": target_str},
            )
            return self

        _logger.debug(
            "Deleting embedded note from entity",
            details={"entity_id": str(self.id), "deleted_note_id": target_str},
        )
        return replace(
            self,
            audit=self.audit.touch(IsoTimestamp.now_utc()),
            notes=filtered,
        )

    def get_note(self, note_id: NoteID | str) -> Note | None:
        """Retrieve a specific embedded note by NoteID or string identifier."""
        target_str = str(note_id)
        for n in self.notes:
            if str(n.note_id) == target_str:
                return n
        return None

    def find_notes(
        self,
        text: str | None = None,
        note_type: NoteType | str | None = None,
        tag: str | None = None,
        sort_by: Literal["id", "note_type", "updated_at", "title"] | None = None,
        reverse: bool = False,
    ) -> list[Note]:
        """Filter and sort embedded notes by text, note_type, tag, or field."""
        results = list(self.notes)

        if note_type is not None:
            resolved_type = note_type if isinstance(note_type, NoteType) else NoteType(note_type)
            results = [n for n in results if n.note_type == resolved_type]

        if tag is not None:
            clean_tag = tag.strip().lower()
            results = [n for n in results if clean_tag in [t.lower() for t in n.tags]]

        if text is not None:
            sub = text.strip().lower()
            results = [
                n for n in results if sub in n.text.lower() or (n.title and sub in n.title.lower())
            ]

        if sort_by is not None:
            sort_keys: dict[str, Callable[[Note], Any]] = {
                "note_type": lambda n: n.note_type.value,
                "updated_at": lambda n: n.audit.updated_at.value,
                "title": lambda n: (n.title or "").lower(),
                "id": lambda n: str(n.note_id),
            }
            key_func = sort_keys.get(sort_by)
            if key_func is not None:
                results.sort(key=key_func, reverse=reverse)

        return results

    # ==========================================================================
    # SECTION 4: SERIALIZATION HELPERS
    # ==========================================================================

    def to_dict(self) -> dict[str, Any]:
        """Serialize entity lifecycle properties and embedded notes to a dictionary."""
        return {
            "id": str(self.id),
            "audit": {
                "created_at": str(self.audit.created_at),
                "updated_at": str(self.audit.updated_at),
            },
            "tombstone": {
                "is_deprecated": self.tombstone.is_deprecated,
                "superseded_by": (
                    str(self.tombstone.superseded_by)
                    if self.tombstone.superseded_by is not None
                    else None
                ),
            },
            "notes": [n.to_dict() for n in self.notes],
        }


# ==========================================================================
# SECTION 5: CANONICAL CONCRETE ENTITY NODES
# ==========================================================================


@dataclass(
    config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True),
    kw_only=True,
)
class BaseEntity[ID_T: AtomID](EntityLifecycleMixin):
    """Generic archival entity node composing identity, audit, tombstone, and notes."""

    id: ID_T = Field(..., description="Canonical strongly-typed domain identifier.")
    audit: AuditStamp = Field(..., description="Lifecycle audit metadata.")
    tombstone: Tombstone[ID_T] = Field(
        default_factory=Tombstone,
        description="Lifecycle deprecation and supersession status.",
    )
    notes: list[Note] = Field(
        default_factory=list,
        description="Associated embedded archival research note value objects.",
    )

    def __post_init__(self) -> None:
        """Enforce identity and supersession type alignment."""
        if self.tombstone.superseded_by is not None:
            if not isinstance(self.tombstone.superseded_by, type(self.id)):
                raise TypeError(
                    f"superseded_by type mismatch: expected {type(self.id).__name__}, "
                    f"got {type(self.tombstone.superseded_by).__name__}."
                )

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(id={self.id!r}, audit={self.audit!r}, "
            f"tombstone={self.tombstone!r}, notes={self.notes!r})"
        )


@dataclass(
    config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True),
    kw_only=True,
)
class BaseEntityGUID(EntityLifecycleMixin):
    """Archival digital asset entity identified by a UUIDv4 surrogate identifier."""

    id: str = Field(..., description="Canonical UUIDv4 surrogate identifier.")
    audit: AuditStamp = Field(..., description="Lifecycle audit metadata.")
    tombstone: Tombstone[str] = Field(
        default_factory=Tombstone,
        description="Lifecycle deprecation and supersession status.",
    )
    notes: list[Note] = Field(
        default_factory=list,
        description="Associated embedded archival research note value objects.",
    )

    def __post_init__(self) -> None:
        """Enforce string-based identity and supersession type alignment."""
        if self.tombstone.superseded_by is not None:
            if not isinstance(self.tombstone.superseded_by, str):
                raise TypeError(
                    f"superseded_by type mismatch: expected str, "
                    f"got {type(self.tombstone.superseded_by).__name__}."
                )

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(id={self.id!r}, audit={self.audit!r}, "
            f"tombstone={self.tombstone!r}, notes={self.notes!r})"
        )
