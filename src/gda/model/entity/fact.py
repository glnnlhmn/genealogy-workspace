"""Path: src/gda/model/entity/fact.py

Genealogical fact and life event entity model representing historical assertions.

Operational Role:
    Defines the Fact domain entity representing evidentiary assertions anchoring personas
    and families to temporal events, micro/macro geographic sites, documentary citations,
    and secondary participants. Inherits BaseEntity[FactID] lifecycle management,
    audit stamping, soft-deprecation tombstones, and embedded Note collections.
    Incorporates FactParticipant for contextual participant linkages, copy-on-write
    mutators, full serialization parity, and explicit in-memory dirty tracking (_dirty).
"""

from __future__ import annotations

import json
import re
from dataclasses import replace
from functools import total_ordering
from typing import Any, ClassVar, Self

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.errors import ModelFormatError
from gda.core.introspectable import IntrospectableMixin
from gda.enums.archival import NoteType
from gda.enums.core import AssociatedRole, FactType
from gda.model.atom.date import EventDate, IsoTimestamp
from gda.model.atom.id import FactID, FamilyID, IndividualID, LocationID, NoteID, SiteID
from gda.model.base.audit import AuditStamp
from gda.model.base.entity import BaseEntity
from gda.model.base.note import Note
from gda.model.base.source import SourceReference
from gda.model.base.time_period import TimePeriod
from gda.model.base.tombstone import Tombstone

__version__ = "1.0.0+build.6"

__all__ = ["Fact", "FactParticipant"]

_FACT_ID_PATTERN: re.Pattern[str] = re.compile(r"^FID-\d{6,}$")
_FACT_URN_PATTERN: re.Pattern[str] = re.compile(r"^urn:gda:fact:[a-z0-9_:\-]+$")

# Authoritative normalization maps
_ROLE_MAP: dict[str, AssociatedRole] = {}
for _member in AssociatedRole:
    _ROLE_MAP[_member.name.upper()] = _member
    _ROLE_MAP[_member.value.upper()] = _member

_FACT_TYPE_MAP: dict[str, FactType] = {}
for _member in FactType:
    _FACT_TYPE_MAP[_member.name.upper()] = _member
    _FACT_TYPE_MAP[_member.value.upper()] = _member


def _normalize_role(role: AssociatedRole | str) -> AssociatedRole:
    """Resolve enum member or raw string token to canonical AssociatedRole."""
    if isinstance(role, AssociatedRole):
        return role
    token = str(role).strip().upper()
    if token in _ROLE_MAP:
        return _ROLE_MAP[token]
    raise ModelFormatError(f"Cannot normalize '{role}' to a valid AssociatedRole.")


def _normalize_fact_type(fact_type: FactType | str) -> FactType:
    """Resolve enum member or raw string token to canonical FactType."""
    if isinstance(fact_type, FactType):
        return fact_type
    token = str(fact_type).strip().upper()
    if token in _FACT_TYPE_MAP:
        return _FACT_TYPE_MAP[token]
    raise ModelFormatError(f"Cannot normalize '{fact_type}' to a valid FactType.")


@total_ordering
@dataclass(config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True))
class FactParticipant(IntrospectableMixin):
    """Associative linkage connecting an individual to a fact in a secondary role."""

    individual_id: IndividualID = Field(
        ...,
        description="Canonical IndividualID of the participating individual.",
    )
    role: AssociatedRole = Field(
        default=AssociatedRole.WITNESS,
        description="Role in event: WITNESS, CLERGY, INFORMANT, COMPANION, etc.",
    )
    notes: str | None = Field(
        default=None,
        description="Optional specific notes on participation or testimony.",
    )

    @classmethod
    def create(
        cls,
        individual_id: IndividualID | str,
        role: AssociatedRole | str = AssociatedRole.WITNESS,
        notes: str | None = None,
    ) -> FactParticipant:
        """Factory constructor instantiating a validated FactParticipant."""
        resolved_id = (
            individual_id
            if isinstance(individual_id, IndividualID)
            else IndividualID(individual_id)
        )
        resolved_role = _normalize_role(role)
        clean_notes = notes.strip() if notes is not None else None
        return cls(individual_id=resolved_id, role=resolved_role, notes=clean_notes)

    def update_role(self, role: AssociatedRole | str) -> Self:
        """Return a new immutable copy with updated participation role."""
        resolved_role = _normalize_role(role)
        if resolved_role == self.role:
            return self
        return replace(self, role=resolved_role)

    def update_notes(self, notes: str | None) -> Self:
        """Return a new immutable copy with updated notes."""
        clean = notes.strip() if notes is not None else None
        if clean == self.notes:
            return self
        return replace(self, notes=clean)

    def to_dict(self) -> dict[str, Any]:
        """Serialize FactParticipant to a dictionary."""
        data: dict[str, Any] = {
            "individual_id": self.individual_id.value,
            "role": self.role.value,
        }
        if self.notes is not None:
            data["notes"] = self.notes
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FactParticipant:
        """Deserialize a dictionary payload into an immutable FactParticipant."""
        if not isinstance(data, dict):
            raise ModelFormatError("FactParticipant payload must be a dictionary.")
        ind_id = data.get("individual_id")
        if not ind_id:
            raise ModelFormatError("Missing required field 'individual_id' for FactParticipant.")
        return cls.create(
            individual_id=str(ind_id),
            role=data.get("role", AssociatedRole.WITNESS),
            notes=data.get("notes"),
        )

    def to_json(self) -> str:
        """Serialize FactParticipant to a JSON formatted string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_json(cls, payload: str) -> FactParticipant:
        """Deserialize a JSON string directly into a FactParticipant instance."""
        try:
            data = json.loads(payload)
        except Exception as exc:
            raise ModelFormatError(f"Failed to parse FactParticipant JSON string: {exc}") from exc
        return cls.from_dict(data)

    def __str__(self) -> str:
        """Render concise string representation of the participant."""
        suffix = f" ({self.notes})" if self.notes else ""
        return f"{self.individual_id.value} [{self.role.value}]{suffix}"

    def __lt__(self, other: Any) -> bool:
        """Support deterministic sorting by individual_id and role."""
        if isinstance(other, FactParticipant):
            if self.individual_id != other.individual_id:
                return self.individual_id < other.individual_id
            return self.role.value < other.role.value
        return NotImplemented


@dataclass(
    config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True),
    kw_only=True,
)
class Fact(BaseEntity[FactID]):
    """Evidentiary event assertion anchoring entities to time, place, and citations."""

    canonical_urn: str = Field(
        ...,
        description="Deterministic lookup URN (e.g., 'urn:gda:fact:smith_birth_1842').",
    )
    fact_type: FactType = Field(
        ...,
        description="Standard event classification (BIRTH, DEATH, CENSUS, RESIDENCE, etc.).",
    )
    title: str = Field(
        ...,
        description="Concise summary or headline for timeline displays.",
    )
    primary_subject_id: IndividualID | FamilyID = Field(
        ...,
        description="Primary entity (IndividualID or FamilyID) about whom the fact is asserted.",
    )
    date: EventDate | TimePeriod | None = Field(
        default=None,
        description="Point-in-time EventDate or bounded TimePeriod duration.",
    )
    location_id: LocationID | None = Field(
        default=None,
        description="Macro-jurisdictional geographic anchor (Town, County, State, Country).",
    )
    site_id: SiteID | None = Field(
        default=None,
        description="Micro-physical place anchor (Cemetery, Church, Homestead, Hospital).",
    )
    value: str | None = Field(
        default=None,
        description="Specific assertion attribute (e.g., 'Blacksmith', 'Pneumonia').",
    )
    description: str | None = Field(
        default=None,
        description="Structured transcription extract or itemized factual details.",
    )
    narrative: str | None = Field(
        default=None,
        description="Free-form biographical or life-story prose narrative.",
    )
    participants: list[FactParticipant] = Field(
        default_factory=list,
        description="Secondary individuals involved in the assertion with contextual roles.",
    )
    citations: list[SourceReference] = Field(
        default_factory=list,
        description="Documentary evidentiary citations linking the fact to supporting sources.",
    )
    _dirty: bool = Field(
        default=False,
        description="True if entity has unpersisted state changes in working memory.",
    )

    _ID_PATTERN: ClassVar[re.Pattern[str]] = _FACT_ID_PATTERN
    _URN_PATTERN: ClassVar[re.Pattern[str]] = _FACT_URN_PATTERN

    def __post_init__(self) -> None:
        """Enforce domain invariants, participant uniqueness, and relational integrity."""
        super().__post_init__()

        if not isinstance(self.id, FactID):
            raise TypeError(
                f"Fact 'id' must be an instance of FactID, got {type(self.id).__name__}."
            )

        raw_id = self.id.value
        if not self._ID_PATTERN.match(raw_id):
            raise ModelFormatError(f"Invalid FactID format: '{raw_id}'. Must match 'FID-######'.")

        if not self.canonical_urn or not self._URN_PATTERN.match(self.canonical_urn):
            raise ModelFormatError(
                f"Invalid canonical_urn format: '{self.canonical_urn}'. "
                "Must match 'urn:gda:fact:<slug>'."
            )

        clean_title = self.title.strip() if self.title else ""
        if not clean_title:
            raise ModelFormatError("Fact 'title' cannot be empty or whitespace.")
        object.__setattr__(self, "title", clean_title)

        if not isinstance(self.primary_subject_id, (IndividualID, FamilyID)):
            raise TypeError(
                f"Fact 'primary_subject_id' must be IndividualID or FamilyID, "
                f"got {type(self.primary_subject_id).__name__}."
            )

        if (
            self.tombstone.is_deprecated
            and self.tombstone.superseded_by is not None
            and self.tombstone.superseded_by.value == raw_id
        ):
            raise ModelFormatError("Fact cannot be superseded by itself.")

        participant_ids = [p.individual_id for p in self.participants]
        if len(participant_ids) != len(set(participant_ids)):
            raise ModelFormatError("Duplicate individual entries found in participants.")

        if (
            isinstance(self.primary_subject_id, IndividualID)
            and self.primary_subject_id in participant_ids
        ):
            raise ModelFormatError(
                "Primary subject cannot also be listed as a secondary participant."
            )

    @property
    def participant_ids(self) -> list[IndividualID]:
        """Convenience accessor returning ordered list of participant IndividualIDs."""
        return [p.individual_id for p in self.participants]

    @property
    def citation_count(self) -> int:
        """Total number of evidentiary source citations attached to this fact."""
        return len(self.citations)

    @property
    def participant_count(self) -> int:
        """Total number of secondary participants recorded."""
        return len(self.participants)

    @property
    def is_dirty(self) -> bool:
        """Return True if entity has unpersisted in-memory modifications."""
        return self._dirty

    @property
    def is_family_fact(self) -> bool:
        """Return True if fact subject is a FamilyID."""
        return isinstance(self.primary_subject_id, FamilyID)

    @property
    def is_individual_fact(self) -> bool:
        """Return True if fact subject is an IndividualID."""
        return isinstance(self.primary_subject_id, IndividualID)

    @property
    def year_lower_bound(self) -> int | None:
        """Extract earliest calendar year from date atom or time period bounds."""
        if self.date is None:
            return None
        if isinstance(self.date, EventDate):
            return self.date.year_lower_bound
        if isinstance(self.date, TimePeriod) and self.date.start_date is not None:
            return self.date.start_date.year_lower_bound
        return None

    @property
    def sort_key(self) -> tuple[str, int, str, str]:
        """Deterministic ordering: subject ID, year lower bound, fact type, fact ID."""
        yr = self.year_lower_bound if self.year_lower_bound is not None else 9999
        return (self.primary_subject_id.value, yr, self.fact_type.value, self.id.value)

    @classmethod
    def create(
        cls,
        fact_id: FactID | str,
        canonical_urn: str,
        fact_type: FactType | str,
        title: str,
        primary_subject_id: IndividualID | FamilyID | str,
        date: EventDate | TimePeriod | str | dict[str, Any] | None = None,
        location_id: LocationID | str | None = None,
        site_id: SiteID | str | None = None,
        value: str | None = None,
        description: str | None = None,
        narrative: str | None = None,
        participants: list[FactParticipant | dict[str, Any]] | None = None,
        citations: list[SourceReference | dict[str, Any]] | None = None,
        audit: AuditStamp | None = None,
        tombstone: Tombstone[FactID] | None = None,
        notes: list[Note] | None = None,
    ) -> Fact:
        """Factory constructor instantiating a validated Fact entity."""
        resolved_id = fact_id if isinstance(fact_id, FactID) else FactID(fact_id)
        resolved_type = _normalize_fact_type(fact_type)

        if isinstance(primary_subject_id, (IndividualID, FamilyID)):
            resolved_subject = primary_subject_id
        else:
            subj_str = str(primary_subject_id).strip()
            if subj_str.startswith("FAM-"):
                resolved_subject = FamilyID(subj_str)
            else:
                resolved_subject = IndividualID(subj_str)

        resolved_date: EventDate | TimePeriod | None = None
        if isinstance(date, (EventDate, TimePeriod)):
            resolved_date = date
        elif isinstance(date, str):
            resolved_date = EventDate.create(date)
        elif isinstance(date, dict):
            if "start_date" in date or "end_date" in date:
                s_date = EventDate.create(date["start_date"]) if date.get("start_date") else None
                e_date = EventDate.create(date["end_date"]) if date.get("end_date") else None
                resolved_date = TimePeriod(start_date=s_date, end_date=e_date)
            else:
                resolved_date = EventDate.from_dict(date)

        resolved_loc = (
            location_id
            if (location_id is None or isinstance(location_id, LocationID))
            else LocationID(location_id)
        )
        resolved_site = (
            site_id if (site_id is None or isinstance(site_id, SiteID)) else SiteID(site_id)
        )

        resolved_participants: list[FactParticipant] = []
        if participants is not None:
            for p in participants:
                if isinstance(p, FactParticipant):
                    resolved_participants.append(p)
                elif isinstance(p, dict):
                    resolved_participants.append(FactParticipant.from_dict(p))
                else:
                    raise TypeError(f"Cannot resolve participant from payload: {p!r}")

        resolved_citations: list[SourceReference] = []
        if citations is not None:
            for c in citations:
                if isinstance(c, SourceReference):
                    resolved_citations.append(c)
                elif isinstance(c, dict):
                    resolved_citations.append(SourceReference.from_dict(c))
                else:
                    raise TypeError(f"Cannot resolve citation from payload: {c!r}")

        now_ts = IsoTimestamp.now_utc()
        resolved_audit = (
            audit if audit is not None else AuditStamp(created_at=now_ts, updated_at=now_ts)
        )
        resolved_tombstone = tombstone if tombstone is not None else Tombstone[FactID]()
        resolved_notes = list(notes) if notes is not None else []

        kwargs: dict[str, Any] = {
            "id": resolved_id,
            "canonical_urn": canonical_urn.strip() if canonical_urn else "",
            "fact_type": resolved_type,
            "title": title.strip() if title else "",
            "primary_subject_id": resolved_subject,
            "date": resolved_date,
            "location_id": resolved_loc,
            "site_id": resolved_site,
            "value": value.strip() if value is not None else None,
            "description": description.strip() if description is not None else None,
            "narrative": narrative.strip() if narrative is not None else None,
            "participants": resolved_participants,
            "citations": resolved_citations,
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

    def update_title(self, title: str) -> Self:
        """Return a new immutable copy with updated title summary."""
        clean = title.strip() if title else ""
        if not clean:
            raise ModelFormatError("Fact 'title' cannot be empty or whitespace.")
        if clean == self.title:
            return self
        return replace(
            self,
            title=clean,
            audit=self.audit.touch(IsoTimestamp.now_utc()),
            _dirty=True,
        )

    def update_fact_type(self, fact_type: FactType | str) -> Self:
        """Return a new immutable copy with updated fact classification."""
        resolved = _normalize_fact_type(fact_type)
        if resolved == self.fact_type:
            return self
        return replace(
            self,
            fact_type=resolved,
            audit=self.audit.touch(IsoTimestamp.now_utc()),
            _dirty=True,
        )

    def update_date(self, date: EventDate | TimePeriod | str | None) -> Self:
        """Return a new immutable copy with updated temporal bound."""
        resolved: EventDate | TimePeriod | None = (
            EventDate.create(date) if isinstance(date, str) else date
        )
        if resolved == self.date:
            return self
        return replace(
            self,
            date=resolved,
            audit=self.audit.touch(IsoTimestamp.now_utc()),
            _dirty=True,
        )

    def update_location(self, location_id: LocationID | str | None) -> Self:
        """Return a new immutable copy with updated macro jurisdiction anchor."""
        resolved = (
            location_id
            if (location_id is None or isinstance(location_id, LocationID))
            else LocationID(location_id)
        )
        if resolved == self.location_id:
            return self
        return replace(
            self,
            location_id=resolved,
            audit=self.audit.touch(IsoTimestamp.now_utc()),
            _dirty=True,
        )

    def update_site(self, site_id: SiteID | str | None) -> Self:
        """Return a new immutable copy with updated micro venue anchor."""
        resolved = site_id if (site_id is None or isinstance(site_id, SiteID)) else SiteID(site_id)
        if resolved == self.site_id:
            return self
        return replace(
            self,
            site_id=resolved,
            audit=self.audit.touch(IsoTimestamp.now_utc()),
            _dirty=True,
        )

    def update_value(self, value: str | None) -> Self:
        """Return a new immutable copy with updated assertion value."""
        clean = value.strip() if value is not None else None
        if clean == self.value:
            return self
        return replace(
            self,
            value=clean,
            audit=self.audit.touch(IsoTimestamp.now_utc()),
            _dirty=True,
        )

    def update_description(self, description: str | None) -> Self:
        """Return a new immutable copy with updated structured description."""
        clean = description.strip() if description is not None else None
        if clean == self.description:
            return self
        return replace(
            self,
            description=clean,
            audit=self.audit.touch(IsoTimestamp.now_utc()),
            _dirty=True,
        )

    def update_narrative(self, narrative: str | None) -> Self:
        """Return a new immutable copy with updated prose narrative."""
        clean = narrative.strip() if narrative is not None else None
        if clean == self.narrative:
            return self
        return replace(
            self,
            narrative=clean,
            audit=self.audit.touch(IsoTimestamp.now_utc()),
            _dirty=True,
        )

    def update_urn(self, canonical_urn: str) -> Self:
        """Return a new immutable copy with updated canonical URN."""
        clean_urn = canonical_urn.strip() if canonical_urn else ""
        if not clean_urn or not self._URN_PATTERN.match(clean_urn):
            raise ModelFormatError(
                f"Invalid canonical_urn format: '{clean_urn}'. Must match 'urn:gda:fact:<slug>'."
            )
        if clean_urn == self.canonical_urn:
            return self
        return replace(
            self,
            canonical_urn=clean_urn,
            audit=self.audit.touch(IsoTimestamp.now_utc()),
            _dirty=True,
        )

    def add_participant(
        self,
        individual_id: IndividualID | str,
        role: AssociatedRole | str = AssociatedRole.WITNESS,
        notes: str | None = None,
    ) -> Self:
        """Return a new immutable copy appending a secondary participant."""
        new_part = FactParticipant.create(individual_id, role, notes)

        if (
            isinstance(self.primary_subject_id, IndividualID)
            and new_part.individual_id == self.primary_subject_id
        ):
            raise ModelFormatError(
                "Primary subject cannot also be listed as a secondary participant."
            )

        for p in self.participants:
            if p.individual_id == new_part.individual_id:
                if p.role == new_part.role and p.notes == new_part.notes:
                    return self
                raise ModelFormatError(
                    f"Participant '{new_part.individual_id.value}' is already recorded. "
                    "Use update_participant_role instead."
                )

        return replace(
            self,
            participants=[*self.participants, new_part],
            audit=self.audit.touch(IsoTimestamp.now_utc()),
            _dirty=True,
        )

    def remove_participant(self, individual_id: IndividualID | str) -> Self:
        """Return a new immutable copy with targeted secondary participant removed."""
        target_str = str(individual_id)
        filtered = [p for p in self.participants if p.individual_id.value != target_str]
        if len(filtered) == len(self.participants):
            return self
        return replace(
            self,
            participants=filtered,
            audit=self.audit.touch(IsoTimestamp.now_utc()),
            _dirty=True,
        )

    def update_participant_role(
        self,
        individual_id: IndividualID | str,
        role: AssociatedRole | str,
        notes: str | None = None,
    ) -> Self:
        """Return a new immutable copy updating the role or notes of an existing participant."""
        target_str = str(individual_id)
        resolved_role = _normalize_role(role)
        found = False
        new_participants: list[FactParticipant] = []

        for p in self.participants:
            if p.individual_id.value == target_str:
                found = True
                new_p = p.update_role(resolved_role)
                if notes is not None:
                    new_p = new_p.update_notes(notes)
                new_participants.append(new_p)
            else:
                new_participants.append(p)

        if not found:
            raise ModelFormatError(f"Participant '{target_str}' not found in fact participants.")

        if new_participants == self.participants:
            return self

        return replace(
            self,
            participants=new_participants,
            audit=self.audit.touch(IsoTimestamp.now_utc()),
            _dirty=True,
        )

    def add_citation(self, citation: SourceReference | dict[str, Any]) -> Self:
        """Return a new immutable copy appending a SourceReference citation."""
        resolved = (
            citation
            if isinstance(citation, SourceReference)
            else SourceReference.from_dict(citation)
        )
        if resolved in self.citations:
            return self
        return replace(
            self,
            citations=[*self.citations, resolved],
            audit=self.audit.touch(IsoTimestamp.now_utc()),
            _dirty=True,
        )

    def remove_citation(self, citation_text: str) -> Self:
        """Return a new immutable copy with targeted citation removed by text."""
        clean = citation_text.strip()
        filtered = [c for c in self.citations if c.citation_text != clean]
        if len(filtered) == len(self.citations):
            return self
        return replace(
            self,
            citations=filtered,
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
        """Return a new immutable copy with targeted research note updated."""
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
        """Serialize Fact entity to a dictionary payload."""
        data: dict[str, Any] = {
            "id": self.id.value,
            "canonical_urn": self.canonical_urn,
            "fact_type": self.fact_type.value,
            "title": self.title,
            "primary_subject_id": self.primary_subject_id.value,
            "participants": [p.to_dict() for p in self.participants],
            "citations": [c.to_dict() for c in self.citations],
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

        if self.date is not None:
            if isinstance(self.date, EventDate):
                data["date"] = self.date.to_dict()
            else:
                data["date"] = {
                    "start_date": str(self.date.start_date) if self.date.start_date else None,
                    "end_date": str(self.date.end_date) if self.date.end_date else None,
                }

        if self.location_id is not None:
            data["location_id"] = self.location_id.value
        if self.site_id is not None:
            data["site_id"] = self.site_id.value
        if self.value is not None:
            data["value"] = self.value
        if self.description is not None:
            data["description"] = self.description
        if self.narrative is not None:
            data["narrative"] = self.narrative

        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Fact:
        """Deserialize a dictionary payload into an immutable Fact entity."""
        if not isinstance(data, dict):
            raise ModelFormatError("Fact payload must be a dictionary.")

        raw_id = data.get("id")
        if not raw_id:
            raise ModelFormatError("Missing required field 'id' for Fact.")

        urn = data.get("canonical_urn", "")
        fact_type = data.get("fact_type")
        title = data.get("title")
        subject = data.get("primary_subject_id")

        if not all((fact_type, title, subject)):
            raise ModelFormatError("Fact requires 'fact_type', 'title', and 'primary_subject_id'.")

        audit_payload = data.get("audit")
        audit_obj: AuditStamp | None = None
        if isinstance(audit_payload, dict):
            audit_obj = AuditStamp(
                created_at=IsoTimestamp(audit_payload["created_at"]),
                updated_at=IsoTimestamp(audit_payload["updated_at"]),
            )

        tombstone_payload = data.get("tombstone")
        tombstone_obj: Tombstone[FactID] | None = None
        if isinstance(tombstone_payload, dict):
            tombstone_obj = Tombstone[FactID](
                is_deprecated=tombstone_payload.get("is_deprecated", False),
                deprecated_at=(
                    IsoTimestamp(tombstone_payload["deprecated_at"])
                    if tombstone_payload.get("deprecated_at")
                    else None
                ),
                superseded_by=(
                    FactID(tombstone_payload["superseded_by"])
                    if tombstone_payload.get("superseded_by")
                    else None
                ),
            )

        notes_payload = data.get("notes", [])
        notes_list = [Note.from_dict(n) for n in notes_payload if isinstance(n, dict)]

        participants_payload = data.get("participants", [])
        participants_list = [
            FactParticipant.from_dict(p) if isinstance(p, dict) else FactParticipant.create(str(p))
            for p in participants_payload
        ]

        citations_payload = data.get("citations", [])
        citations_list = [
            SourceReference.from_dict(c) if isinstance(c, dict) else SourceReference.create(str(c))
            for c in citations_payload
        ]

        return cls.create(
            fact_id=str(raw_id),
            canonical_urn=str(urn),
            fact_type=str(fact_type),
            title=str(title),
            primary_subject_id=str(subject),
            date=data.get("date"),
            location_id=data.get("location_id"),
            site_id=data.get("site_id"),
            value=data.get("value"),
            description=data.get("description"),
            narrative=data.get("narrative"),
            participants=participants_list,
            citations=citations_list,
            audit=audit_obj,
            tombstone=tombstone_obj,
            notes=notes_list,
        )

    def to_json(self) -> str:
        """Serialize Fact entity to a JSON formatted string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_json(cls, payload: str) -> Fact:
        """Deserialize a JSON string directly into a Fact instance."""
        try:
            data = json.loads(payload)
        except Exception as exc:
            raise ModelFormatError(f"Failed to parse Fact JSON string: {exc}") from exc
        return cls.from_dict(data)

    def __str__(self) -> str:
        """Render concise human-readable fact summary."""
        date_str = f" on {self.date}" if self.date else ""
        return (
            f"Fact [{self.fact_type.value}] '{self.title}' for "
            f"{self.primary_subject_id.value}{date_str} ({self.id.value})"
        )
