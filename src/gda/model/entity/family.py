"""Path: src/gda/model/entity/family.py

Genealogical family entity model representing nuclear and domestic relations.

Operational Role:
    Defines the Family domain entity representing conjugal unions, parental partnerships,
    and child lineage attachments across the digital archive. Inherits lifecycle management,
    audit stamps, soft-deprecation tombstones, and embedded Note collections from
    BaseEntity[FamilyID]. Incorporates FamilyUnion for union lifecycle bounds, ChildLink
    for filiation pedigree links, copy-on-write mutators, full serialization parity,
    and explicit in-memory dirty tracking (_dirty).
"""

from __future__ import annotations

import json
import re
from dataclasses import replace
from typing import Any, ClassVar, Self

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.errors import ModelFormatError
from gda.enums.archival import NoteType
from gda.enums.vital import PedigreeType, UnionDissolutionType, UnionType
from gda.model.atom.date import EventDate, IsoTimestamp
from gda.model.atom.id import FamilyID, IndividualID, NoteID
from gda.model.base.audit import AuditStamp
from gda.model.base.entity import BaseEntity
from gda.model.base.family import ChildLink, FamilyUnion
from gda.model.base.note import Note
from gda.model.base.time_period import TimePeriod
from gda.model.base.tombstone import Tombstone

__version__ = "1.0.0+build.2"

__all__ = ["Family"]

_FAMILY_ID_PATTERN: re.Pattern[str] = re.compile(r"^FAM-\d{6,}$")
_FAMILY_URN_PATTERN: re.Pattern[str] = re.compile(r"^urn:gda:fam:[a-z0-9_:\-]+$")


@dataclass(
    config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True),
    kw_only=True,
)
class Family(BaseEntity[FamilyID]):
    """Genealogical family nexus binding partners, children, and union state."""

    canonical_urn: str = Field(
        ...,
        description="Deterministic lookup URN (e.g., 'urn:gda:fam:smith_jones_1865').",
    )
    union: FamilyUnion = Field(
        default_factory=FamilyUnion,
        description="Union characterization, dissolution details, and lifespan bounds.",
    )
    partner_ids: list[IndividualID] = Field(
        default_factory=list,
        description="Primary parental or spousal partner identifiers (0, 1, or 2).",
    )
    children: list[ChildLink] = Field(
        default_factory=list,
        description="Ordered list of child links with lineage pedigree classifications.",
    )
    _dirty: bool = Field(
        default=False,
        description="True if entity has unpersisted state changes in working memory.",
    )

    _ID_PATTERN: ClassVar[re.Pattern[str]] = _FAMILY_ID_PATTERN
    _URN_PATTERN: ClassVar[re.Pattern[str]] = _FAMILY_URN_PATTERN

    def __post_init__(self) -> None:
        """Enforce domain invariants, relational uniqueness, and boundary guards."""
        super().__post_init__()

        if not isinstance(self.id, FamilyID):
            raise TypeError(
                f"Family 'id' must be an instance of FamilyID, got {type(self.id).__name__}."
            )

        raw_id = self.id.value
        if not self._ID_PATTERN.match(raw_id):
            raise ModelFormatError(
                f"Invalid FamilyID format: '{raw_id}'. Must match 'FAM-######'."
            )

        if not self.canonical_urn or not self._URN_PATTERN.match(self.canonical_urn):
            raise ModelFormatError(
                f"Invalid canonical_urn format: '{self.canonical_urn}'. "
                "Must match 'urn:gda:fam:<slug>'."
            )

        if (
            self.tombstone.is_deprecated
            and self.tombstone.superseded_by is not None
            and self.tombstone.superseded_by.value == raw_id
        ):
            raise ModelFormatError("Family cannot be superseded by itself.")

        if len(self.partner_ids) != len(set(self.partner_ids)):
            raise ModelFormatError("Duplicate entries found in partner_ids.")

        if len(self.partner_ids) > 2:
            raise ModelFormatError(
                f"Family partner_ids cannot exceed 2 partners, got {len(self.partner_ids)}."
            )

        child_ids = [link.child_id for link in self.children]
        if len(child_ids) != len(set(child_ids)):
            raise ModelFormatError(
                "Duplicate child entries found in family children links."
            )

        partner_set = set(self.partner_ids)
        if any(c_id in partner_set for c_id in child_ids):
            raise ModelFormatError(
                "An individual cannot be both a partner and a child within the same family unit."
            )

    @property
    def child_ids(self) -> list[IndividualID]:
        """Convenience accessor returning ordered flat list of child IndividualIDs."""
        return [link.child_id for link in self.children]

    @property
    def partner_count(self) -> int:
        """Total number of registered partners in the family unit."""
        return len(self.partner_ids)

    @property
    def child_count(self) -> int:
        """Total number of registered children in the family unit."""
        return len(self.children)

    @property
    def is_dirty(self) -> bool:
        """Return True if entity has unpersisted in-memory modifications."""
        return self._dirty

    @property
    def union_type(self) -> UnionType:
        """Forward classification of union formation."""
        return self.union.union_type

    @property
    def dissolution_type(self) -> UnionDissolutionType | None:
        """Forward classification of union termination."""
        return self.union.dissolution_type

    @property
    def period(self) -> TimePeriod | None:
        """Forward chronological bounds of the union."""
        return self.union.period

    @property
    def marriage_date(self) -> EventDate | None:
        """Forward union inception date if defined."""
        return self.union.period.start_date if self.union.period is not None else None

    @property
    def dissolution_date(self) -> EventDate | None:
        """Forward union dissolution date if defined."""
        return self.union.period.end_date if self.union.period is not None else None

    @property
    def marriage_year(self) -> int | None:
        """Extract lower-bound marriage calendar year."""
        m_date = self.marriage_date
        return m_date.year_lower_bound if m_date is not None else None

    @property
    def sort_key(self) -> tuple[str, str, int, str]:
        """Deterministic ordering: primary partner, secondary partner, marriage year, family id."""
        p1 = self.partner_ids[0].value if len(self.partner_ids) > 0 else ""
        p2 = self.partner_ids[1].value if len(self.partner_ids) > 1 else ""
        m_yr = self.marriage_year if self.marriage_year is not None else 9999
        return (p1, p2, m_yr, self.id.value)

    @classmethod
    def create(
        cls,
        family_id: FamilyID | str,
        canonical_urn: str,
        partner_ids: list[IndividualID | str] | None = None,
        children: list[
            ChildLink | tuple[IndividualID | str, PedigreeType | str] | dict[str, Any]
        ]
        | None = None,
        union: FamilyUnion | dict[str, Any] | None = None,
        audit: AuditStamp | None = None,
        tombstone: Tombstone[FamilyID] | None = None,
        notes: list[Note] | None = None,
    ) -> Family:
        """Factory constructor instantiating a validated Family entity."""
        resolved_id = (
            family_id if isinstance(family_id, FamilyID) else FamilyID(family_id)
        )

        resolved_partners: list[IndividualID] = []
        if partner_ids is not None:
            resolved_partners = [
                pid if isinstance(pid, IndividualID) else IndividualID(pid)
                for pid in partner_ids
            ]

        resolved_children: list[ChildLink] = []
        if children is not None:
            for item in children:
                if isinstance(item, ChildLink):
                    resolved_children.append(item)
                elif isinstance(item, tuple) and len(item) == 2:
                    resolved_children.append(ChildLink.create(item[0], item[1]))
                elif isinstance(item, dict):
                    resolved_children.append(ChildLink.from_dict(item))
                else:
                    raise TypeError(f"Cannot resolve child link from payload: {item!r}")

        if isinstance(union, FamilyUnion):
            resolved_union = union
        elif isinstance(union, dict):
            resolved_union = FamilyUnion.from_dict(union)
        else:
            resolved_union = FamilyUnion.create()

        now_ts = IsoTimestamp.now_utc()
        resolved_audit = (
            audit
            if audit is not None
            else AuditStamp(created_at=now_ts, updated_at=now_ts)
        )
        resolved_tombstone = (
            tombstone if tombstone is not None else Tombstone[FamilyID]()
        )
        resolved_notes = list(notes) if notes is not None else []

        kwargs: dict[str, Any] = {
            "id": resolved_id,
            "canonical_urn": canonical_urn.strip() if canonical_urn else "",
            "partner_ids": resolved_partners,
            "children": resolved_children,
            "union": resolved_union,
            "audit": resolved_audit,
            "tombstone": resolved_tombstone,
            "notes": resolved_notes,
            "_dirty": False,
        }

        return cls(**kwargs)

    def mark_clean(self) -> Self:
        """Return a new immutable copy marking entity as clean (persisted to storage)."""
        if not self._dirty:
            return self
        return replace(self, _dirty=False)

    def mark_dirty(self) -> Self:
        """Return a new immutable copy marking entity as modified in memory."""
        if self._dirty:
            return self
        return replace(self, _dirty=True)

    def add_partner(self, partner_id: IndividualID | str) -> Self:
        """Return a new immutable copy appending a partner IndividualID."""
        resolved_pid = (
            partner_id
            if isinstance(partner_id, IndividualID)
            else IndividualID(partner_id)
        )
        if resolved_pid in self.partner_ids:
            return self

        if len(self.partner_ids) >= 2:
            raise ModelFormatError("Family partner_ids cannot exceed 2 partners.")

        if resolved_pid in self.child_ids:
            raise ModelFormatError(
                "An individual cannot be both a partner and a child within the same family unit."
            )

        return replace(
            self,
            partner_ids=[*self.partner_ids, resolved_pid],
            audit=self.audit.touch(IsoTimestamp.now_utc()),
            _dirty=True,
        )

    def remove_partner(self, partner_id: IndividualID | str) -> Self:
        """Return a new immutable copy with target partner removed."""
        target_str = str(partner_id)
        filtered = [pid for pid in self.partner_ids if pid.value != target_str]
        if len(filtered) == len(self.partner_ids):
            return self

        return replace(
            self,
            partner_ids=filtered,
            audit=self.audit.touch(IsoTimestamp.now_utc()),
            _dirty=True,
        )

    def add_child(
        self,
        child_id: IndividualID | str,
        pedigree: PedigreeType | str = PedigreeType.BIRTH,
    ) -> Self:
        """Return a new immutable copy appending a ChildLink."""
        new_link = ChildLink.create(child_id=child_id, pedigree=pedigree)

        if new_link.child_id in self.partner_ids:
            raise ModelFormatError(
                "An individual cannot be both a partner and a child within the same family unit."
            )

        for existing in self.children:
            if existing.child_id == new_link.child_id:
                if existing.pedigree == new_link.pedigree:
                    return self
                raise ModelFormatError(
                    f"Child '{new_link.child_id.value}' is already registered with a different pedigree. "
                    "Use update_child_pedigree instead."
                )

        return replace(
            self,
            children=[*self.children, new_link],
            audit=self.audit.touch(IsoTimestamp.now_utc()),
            _dirty=True,
        )

    def remove_child(self, child_id: IndividualID | str) -> Self:
        """Return a new immutable copy with target child removed."""
        target_str = str(child_id)
        filtered = [c for c in self.children if c.child_id.value != target_str]
        if len(filtered) == len(self.children):
            return self

        return replace(
            self,
            children=filtered,
            audit=self.audit.touch(IsoTimestamp.now_utc()),
            _dirty=True,
        )

    def update_child_pedigree(
        self,
        child_id: IndividualID | str,
        pedigree: PedigreeType | str,
    ) -> Self:
        """Return a new immutable copy with updated pedigree classification on an existing child link."""
        target_str = str(child_id)
        found = False
        updated_links: list[ChildLink] = []

        for c in self.children:
            if c.child_id.value == target_str:
                found = True
                new_c = c.update_pedigree(pedigree)
                updated_links.append(new_c)
            else:
                updated_links.append(c)

        if not found:
            raise ModelFormatError(
                f"Child '{target_str}' not found in family children."
            )

        if updated_links == self.children:
            return self

        return replace(
            self,
            children=updated_links,
            audit=self.audit.touch(IsoTimestamp.now_utc()),
            _dirty=True,
        )

    def update_union(self, union: FamilyUnion) -> Self:
        """Return a new immutable copy with updated FamilyUnion composite."""
        if union == self.union:
            return self
        return replace(
            self,
            union=union,
            audit=self.audit.touch(IsoTimestamp.now_utc()),
            _dirty=True,
        )

    def update_union_type(self, union_type: UnionType | str) -> Self:
        """Return a new immutable copy with updated union formation type."""
        new_union = self.union.update_type(union_type)
        if new_union is self.union:
            return self
        return replace(
            self,
            union=new_union,
            audit=self.audit.touch(IsoTimestamp.now_utc()),
            _dirty=True,
        )

    def update_dissolution(
        self, dissolution_type: UnionDissolutionType | str | None
    ) -> Self:
        """Return a new immutable copy with updated union dissolution type."""
        new_union = self.union.update_dissolution(dissolution_type)
        if new_union is self.union:
            return self
        return replace(
            self,
            union=new_union,
            audit=self.audit.touch(IsoTimestamp.now_utc()),
            _dirty=True,
        )

    def update_period(self, period: TimePeriod | None) -> Self:
        """Return a new immutable copy with updated union temporal period."""
        new_union = self.union.update_period(period)
        if new_union is self.union:
            return self
        return replace(
            self,
            union=new_union,
            audit=self.audit.touch(IsoTimestamp.now_utc()),
            _dirty=True,
        )

    def update_marriage_date(self, date: EventDate | str | None) -> Self:
        """Return a new immutable copy with updated union inception date."""
        new_union = self.union.update_marriage_date(date)
        if new_union is self.union:
            return self
        return replace(
            self,
            union=new_union,
            audit=self.audit.touch(IsoTimestamp.now_utc()),
            _dirty=True,
        )

    def update_dissolution_date(self, date: EventDate | str | None) -> Self:
        """Return a new immutable copy with updated union dissolution date."""
        new_union = self.union.update_dissolution_date(date)
        if new_union is self.union:
            return self
        return replace(
            self,
            union=new_union,
            audit=self.audit.touch(IsoTimestamp.now_utc()),
            _dirty=True,
        )

    def update_urn(self, canonical_urn: str) -> Self:
        """Return a new immutable copy with updated canonical URN."""
        clean_urn = canonical_urn.strip() if canonical_urn else ""
        if not clean_urn or not self._URN_PATTERN.match(clean_urn):
            raise ModelFormatError(
                f"Invalid canonical_urn format: '{clean_urn}'. "
                "Must match 'urn:gda:fam:<slug>'."
            )
        return replace(
            self,
            canonical_urn=clean_urn,
            audit=self.audit.touch(IsoTimestamp.now_utc()),
            _dirty=True,
        )

    def update_note(
        self,
        note_id: NoteID | str,
        text: str | None = None,
        title: str | None = None,
        note_type: NoteType | str | None = None,
        tags: list[str] | None = None,
    ) -> Self:
        """Return a new immutable copy with the targeted embedded note updated."""
        target_str = str(note_id)
        found = False
        new_notes: list[Note] = []
        for n in self.notes:
            if str(n.note_id) == target_str:
                found = True
                updated_n = n
                if text is not None:
                    updated_n = updated_n.update_text(text)
                if title is not None:
                    updated_n = updated_n.update_title(title)
                if note_type is not None:
                    updated_n = updated_n.update_type(note_type)
                if tags is not None:
                    updated_n = updated_n.update_tags(tags)
                new_notes.append(updated_n)
            else:
                new_notes.append(n)

        if not found:
            return self
        return replace(
            self,
            notes=new_notes,
            audit=self.audit.touch(IsoTimestamp.now_utc()),
            _dirty=True,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize Family entity, union state, links, and embedded notes to a dictionary."""
        return {
            "id": self.id.value,
            "canonical_urn": self.canonical_urn,
            "partner_ids": [pid.value for pid in self.partner_ids],
            "children": [c.to_dict() for c in self.children],
            "union": self.union.to_dict(),
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

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Family:
        """Deserialize a dictionary payload into an immutable Family entity."""
        if not isinstance(data, dict):
            raise ModelFormatError("Family payload must be a dictionary.")

        raw_id = data.get("id")
        if not raw_id:
            raise ModelFormatError("Missing required field 'id' for Family.")

        union_payload = data.get("union", {})
        union_obj = (
            FamilyUnion.from_dict(union_payload)
            if isinstance(union_payload, dict)
            else FamilyUnion.create()
        )

        partner_ids = [str(pid) for pid in data.get("partner_ids", [])]

        children_payload = data.get("children", [])
        children_objs = [
            ChildLink.from_dict(c) if isinstance(c, dict) else ChildLink.create(str(c))
            for c in children_payload
        ]

        audit_payload = data.get("audit")
        audit_obj: AuditStamp | None = None
        if isinstance(audit_payload, dict):
            audit_obj = AuditStamp(
                created_at=IsoTimestamp(audit_payload["created_at"]),
                updated_at=IsoTimestamp(audit_payload["updated_at"]),
            )

        tombstone_payload = data.get("tombstone")
        tombstone_obj: Tombstone[FamilyID] | None = None
        if isinstance(tombstone_payload, dict):
            tombstone_obj = Tombstone[FamilyID](
                is_deprecated=tombstone_payload.get("is_deprecated", False),
                deprecated_at=(
                    IsoTimestamp(tombstone_payload["deprecated_at"])
                    if tombstone_payload.get("deprecated_at")
                    else None
                ),
                superseded_by=(
                    FamilyID(tombstone_payload["superseded_by"])
                    if tombstone_payload.get("superseded_by")
                    else None
                ),
            )

        notes_payload = data.get("notes", [])
        notes_list = [Note.from_dict(n) for n in notes_payload if isinstance(n, dict)]

        return cls.create(
            family_id=str(raw_id),
            canonical_urn=data.get("canonical_urn", ""),
            partner_ids=partner_ids,
            children=children_objs,
            union=union_obj,
            audit=audit_obj,
            tombstone=tombstone_obj,
            notes=notes_list,
        )

    def to_json(self) -> str:
        """Serialize Family entity to a JSON formatted string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_json(cls, payload: str) -> Family:
        """Deserialize a JSON string directly into a Family instance."""
        try:
            data = json.loads(payload)
        except Exception as exc:
            raise ModelFormatError(
                f"Failed to parse Family JSON string: {exc}"
            ) from exc
        return cls.from_dict(data)

    def __str__(self) -> str:
        """Render concise human-readable family summary."""
        partner_str = (
            " & ".join(p.value for p in self.partner_ids)
            if self.partner_ids
            else "None"
        )
        union_summary = f"[{self.union.union_type.value}"
        if self.union.dissolution_type:
            union_summary += f"/{self.union.dissolution_type.value}"
        union_summary += "]"

        period_str = f" ({self.union.period})" if self.union.period else ""
        return (
            f"Family {union_summary}{period_str}: "
            f"Partners({partner_str}), Children({self.child_count}) ({self.id.value})"
        )
