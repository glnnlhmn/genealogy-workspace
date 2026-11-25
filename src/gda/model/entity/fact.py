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
from collections.abc import Sequence
from dataclasses import replace
from functools import total_ordering
from typing import Any, ClassVar, Self

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.dates import parse_iso_date_parts, utc_now_iso
from gda.core.enums import coerce_enum
from gda.core.enums.archival import NoteType
from gda.core.enums.core import AssociatedRole, FactType
from gda.core.errors import ModelFormatError
from gda.core.introspectable import IntrospectableMixin
from gda.core.types import ENTITY_ID_REGEXES, ENTITY_URN_REGEXES
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import FactID, FamilyID, IndividualID, LocationID, NoteID, SiteID
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate, TimePeriod
from gda.model.base.entity import BaseEntity
from gda.model.base.note import Note
from gda.model.base.source import SourceReference
from gda.model.base.tombstone import Tombstone

__version__ = "1.0.0+build.7"

__all__ = ["Fact", "FactParticipant"]

# Canonical regex patterns for Fact SmartID ('FID-######') and URN ('urn:gda:fact:...')
_FACT_ID_PATTERN: re.Pattern[str] = ENTITY_ID_REGEXES["FID"]
_FACT_URN_PATTERN: re.Pattern[str] = ENTITY_URN_REGEXES["FID"]


# ==============================================================================
# 1. NORMALIZATION & COERCION HELPERS
# ==============================================================================


def _normalize_role(role: AssociatedRole | str) -> AssociatedRole:
    """Resolve enum member or raw string token to canonical AssociatedRole."""
    try:
        return coerce_enum(AssociatedRole, role, field_name="role")
    except ModelFormatError as exc:
        raise ModelFormatError(f"Cannot normalize '{role}' to a valid AssociatedRole.") from exc


def _normalize_fact_type(fact_type: FactType | str) -> FactType:
    """Resolve enum member or raw string token to canonical FactType."""
    try:
        return coerce_enum(FactType, fact_type, field_name="fact_type")
    except ModelFormatError as exc:
        raise ModelFormatError(f"Cannot normalize '{fact_type}' to a valid FactType.") from exc


def _opt_clean_str(val: str | None) -> str | None:
    """Strip optional string input while preserving None when absent."""
    return val.strip() if val is not None else None


def _opt_location_id(val: LocationID | str | None) -> LocationID | None:
    """Coerce an optional LocationID or string token into LocationID."""
    if val is None or isinstance(val, LocationID):
        return val
    return LocationID(val)


def _opt_site_id(val: SiteID | str | None) -> SiteID | None:
    """Coerce an optional SiteID or string token into SiteID."""
    if val is None or isinstance(val, SiteID):
        return val
    return SiteID(val)


def _resolve_fact_date(
    date: EventDate | TimePeriod | str | dict[str, Any] | None,
) -> EventDate | TimePeriod | None:
    """Resolve raw date payload into canonical EventDate or TimePeriod."""
    # Fast-path for None or already-hydrated temporal objects
    if date is None or isinstance(date, (EventDate, TimePeriod)):
        return date
    if isinstance(date, str):
        return EventDate.create(date)
    # Distinguish bounded TimePeriod dicts from single-point EventDate dicts
    if isinstance(date, dict):
        if "start_date" in date or "end_date" in date:
            return TimePeriod.from_dict(date)
        return EventDate.from_dict(date)
    raise TypeError(f"Unsupported date payload type: {type(date).__name__}.")


def _resolve_primary_subject(
    primary_subject_id: IndividualID | FamilyID | str,
) -> IndividualID | FamilyID:
    """Resolve IndividualID, FamilyID, or prefixed string token."""
    if isinstance(primary_subject_id, (IndividualID, FamilyID)):
        return primary_subject_id
    subj_str = str(primary_subject_id).strip()
    # Route FAM- prefixes to FamilyID and all other persona tokens to IndividualID
    return FamilyID(subj_str) if subj_str.startswith("FAM-") else IndividualID(subj_str)


def _resolve_participants_payload(
    participants: Sequence[FactParticipant | dict[str, Any]] | None,
) -> list[FactParticipant]:
    """Resolve sequence of FactParticipant instances or dict payloads."""
    if participants is None:
        return []
    resolved: list[FactParticipant] = []
    for p in participants:
        if isinstance(p, FactParticipant):
            resolved.append(p)
        elif isinstance(p, dict):
            resolved.append(FactParticipant.from_dict(p))
        else:
            raise TypeError(f"Cannot resolve participant from payload: {p!r}")
    return resolved


def _resolve_citations_payload(
    citations: Sequence[SourceReference | dict[str, Any]] | None,
) -> list[SourceReference]:
    """Resolve sequence of SourceReference instances or dict payloads."""
    if citations is None:
        return []
    resolved: list[SourceReference] = []
    for c in citations:
        if isinstance(c, SourceReference):
            resolved.append(c)
        elif isinstance(c, dict):
            resolved.append(SourceReference.from_dict(c))
        else:
            raise TypeError(f"Cannot resolve citation from payload: {c!r}")
    return resolved


def _parse_dict_participants(raw_list: Sequence[Any]) -> list[FactParticipant]:
    """Hydrate participant list from serialized dictionary or string entries."""
    return [
        FactParticipant.from_dict(p) if isinstance(p, dict) else FactParticipant.create(str(p))
        for p in raw_list
    ]


def _parse_dict_citations(raw_list: Sequence[Any]) -> list[SourceReference]:
    """Hydrate citation list from serialized dictionary or string entries."""
    return [
        SourceReference.from_dict(c) if isinstance(c, dict) else SourceReference.create(str(c))
        for c in raw_list
    ]


# ==============================================================================
# 2. FACT PARTICIPANT VALUE OBJECT
# ==============================================================================


@total_ordering
@dataclass(
    repr=False,
    config=ConfigDict(frozen=True, extra="forbid", strict=True),
)
class FactParticipant(IntrospectableMixin):
    """Associative linkage connecting an individual to a fact in a secondary role."""

    individual_id: IndividualID = Field(
        ...,
        description="Canonical IndividualID of the participating individual.",
    )
    role: AssociatedRole = Field(
        default=AssociatedRole.WITNESS,
        description="Role in event: WITNESS, CLERGY, INFORMANT, OFFICIAL, OFFICIANT, etc.",
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
        return cls(
            individual_id=resolved_id,
            role=resolved_role,
            notes=_opt_clean_str(notes),
        )

    def update_role(self, role: AssociatedRole | str) -> Self:
        """Return a new immutable copy with updated participation role."""
        resolved_role = _normalize_role(role)
        if resolved_role == self.role:
            return self
        return replace(self, role=resolved_role)

    def update_notes(self, notes: str | None) -> Self:
        """Return a new immutable copy with updated notes."""
        clean = _opt_clean_str(notes)
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
        suffix = f" ({self.notes})" if self.notes else ""
        return f"{self.individual_id.value} [{self.role.value}]{suffix}"

    def __repr__(self) -> str:
        return (
            f"FactParticipant(individual_id={self.individual_id!r}, "
            f"role={self.role!r}, notes={self.notes!r})"
        )

    def __lt__(self, other: Any) -> bool:
        if isinstance(other, FactParticipant):
            if self.individual_id != other.individual_id:
                return self.individual_id < other.individual_id
            return self.role.value < other.role.value
        return NotImplemented


# ==============================================================================
# 3. FACT ENTITY INVARIANT VALIDATORS
# ==============================================================================


def _validate_fact_identity_and_text(fact: Fact) -> None:
    """Validate FactID prefix, canonical URN syntax, and non-empty title."""
    if not isinstance(fact.id, FactID):
        raise TypeError(f"Fact 'id' must be an instance of FactID, got {type(fact.id).__name__}.")

    raw_id = fact.id.value
    if not fact._ID_PATTERN.match(raw_id):
        raise ModelFormatError(f"Invalid FactID format: '{raw_id}'. Must match 'FID-######'.")

    clean_urn = fact.canonical_urn.strip() if fact.canonical_urn else ""
    if not clean_urn or not fact._URN_PATTERN.match(clean_urn):
        raise ModelFormatError(
            f"Invalid canonical_urn format: '{fact.canonical_urn}'. "
            "Must match 'urn:gda:fact:<slug>'."
        )
    if clean_urn != fact.canonical_urn:
        object.__setattr__(fact, "canonical_urn", clean_urn)

    clean_title = fact.title.strip() if fact.title else ""
    if not clean_title:
        raise ModelFormatError("Fact 'title' cannot be empty or whitespace.")
    if clean_title != fact.title:
        object.__setattr__(fact, "title", clean_title)


def _validate_fact_relationships(fact: Fact) -> None:
    """Validate primary subject type, tombstone supersession, and participant uniqueness."""
    if not isinstance(fact.primary_subject_id, (IndividualID, FamilyID)):
        raise TypeError(
            f"Fact 'primary_subject_id' must be IndividualID or FamilyID, "
            f"got {type(fact.primary_subject_id).__name__}."
        )

    # Guard against self-referential tombstone supersession
    if (
        fact.tombstone.is_deprecated
        and fact.tombstone.superseded_by is not None
        and fact.tombstone.superseded_by.value == fact.id.value
    ):
        raise ModelFormatError("Fact cannot be superseded by itself.")

    # Guard against duplicate or self-referential secondary participants
    participant_ids = [p.individual_id for p in fact.participants]
    if len(participant_ids) != len(set(participant_ids)):
        raise ModelFormatError("Duplicate individual entries found in participants.")

    if (
        isinstance(fact.primary_subject_id, IndividualID)
        and fact.primary_subject_id in participant_ids
    ):
        raise ModelFormatError("Primary subject cannot also be listed as a secondary participant.")


# ==============================================================================
# 4. FACT DOMAIN ENTITY
# ==============================================================================


@dataclass(
    repr=False,
    config=ConfigDict(frozen=True, extra="forbid", strict=True),
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
        _validate_fact_identity_and_text(self)
        _validate_fact_relationships(self)

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
        if isinstance(self.date, EventDate):
            return parse_iso_date_parts(self.date.date.value)[0]
        if isinstance(self.date, TimePeriod) and self.date.start_date is not None:
            return parse_iso_date_parts(self.date.start_date.date.value)[0]
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
        participants: Sequence[FactParticipant | dict[str, Any]] | None = None,
        citations: Sequence[SourceReference | dict[str, Any]] | None = None,
        audit: AuditStamp | None = None,
        tombstone: Tombstone[FactID] | None = None,
        notes: Sequence[Note] | None = None,
    ) -> Fact:
        """Factory constructor instantiating a validated Fact entity."""
        resolved_id = fact_id if isinstance(fact_id, FactID) else FactID(fact_id)
        return cls(
            id=resolved_id,
            canonical_urn=_opt_clean_str(canonical_urn) or "",
            fact_type=_normalize_fact_type(fact_type),
            title=_opt_clean_str(title) or "",
            primary_subject_id=_resolve_primary_subject(primary_subject_id),
            date=_resolve_fact_date(date),
            location_id=_opt_location_id(location_id),
            site_id=_opt_site_id(site_id),
            value=_opt_clean_str(value),
            description=_opt_clean_str(description),
            narrative=_opt_clean_str(narrative),
            participants=_resolve_participants_payload(participants),
            citations=_resolve_citations_payload(citations),
            audit=audit or AuditStamp.now(),
            tombstone=tombstone or Tombstone[FactID](),
            notes=list(notes) if notes is not None else [],
            _dirty=False,
        )

    # --- Lifecycle & Copy-on-Write Mutators ---

    def _mutate(self, **changes: Any) -> Self:
        """Return a touched, dirty-marked immutable copy with applied field changes."""
        return replace(
            self,
            **changes,
            audit=self.audit.touch(IsoTimestamp(utc_now_iso())),
            _dirty=True,
        )

    def mark_clean(self) -> Self:
        """Return a new immutable copy marking entity as clean (persisted to storage)."""
        return self if not self._dirty else replace(self, _dirty=False)

    def mark_dirty(self) -> Self:
        """Return a new immutable copy marking entity as modified in memory."""
        return self if self._dirty else replace(self, _dirty=True)

    def update_title(self, title: str) -> Self:
        """Return a new immutable copy with updated title summary."""
        clean = _opt_clean_str(title) or ""
        if not clean:
            raise ModelFormatError("Fact 'title' cannot be empty or whitespace.")
        return self if clean == self.title else self._mutate(title=clean)

    def update_fact_type(self, fact_type: FactType | str) -> Self:
        """Return a new immutable copy with updated fact classification."""
        resolved = _normalize_fact_type(fact_type)
        return self if resolved == self.fact_type else self._mutate(fact_type=resolved)

    def update_date(self, date: EventDate | TimePeriod | str | dict[str, Any] | None) -> Self:
        """Return a new immutable copy with updated temporal bound."""
        resolved = _resolve_fact_date(date)
        return self if resolved == self.date else self._mutate(date=resolved)

    def update_location(self, location_id: LocationID | str | None) -> Self:
        """Return a new immutable copy with updated macro jurisdiction anchor."""
        resolved = _opt_location_id(location_id)
        return self if resolved == self.location_id else self._mutate(location_id=resolved)

    def update_site(self, site_id: SiteID | str | None) -> Self:
        """Return a new immutable copy with updated micro venue anchor."""
        resolved = _opt_site_id(site_id)
        return self if resolved == self.site_id else self._mutate(site_id=resolved)

    def update_value(self, value: str | None) -> Self:
        """Return a new immutable copy with updated assertion value."""
        clean = _opt_clean_str(value)
        return self if clean == self.value else self._mutate(value=clean)

    def update_description(self, description: str | None) -> Self:
        """Return a new immutable copy with updated structured description."""
        clean = _opt_clean_str(description)
        return self if clean == self.description else self._mutate(description=clean)

    def update_narrative(self, narrative: str | None) -> Self:
        """Return a new immutable copy with updated prose narrative."""
        clean = _opt_clean_str(narrative)
        return self if clean == self.narrative else self._mutate(narrative=clean)

    def update_urn(self, canonical_urn: str) -> Self:
        """Return a new immutable copy with updated canonical URN."""
        clean_urn = _opt_clean_str(canonical_urn) or ""
        if not clean_urn or not self._URN_PATTERN.match(clean_urn):
            raise ModelFormatError(
                f"Invalid canonical_urn format: '{clean_urn}'. Must match 'urn:gda:fact:<slug>'."
            )
        return self if clean_urn == self.canonical_urn else self._mutate(canonical_urn=clean_urn)

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

        return self._mutate(participants=[*self.participants, new_part])

    def remove_participant(self, individual_id: IndividualID | str) -> Self:
        """Return a new immutable copy with targeted secondary participant removed."""
        target_str = str(individual_id)
        filtered = [p for p in self.participants if p.individual_id.value != target_str]
        if len(filtered) == len(self.participants):
            return self
        return self._mutate(participants=filtered)

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

        return self._mutate(participants=new_participants)

    def add_citation(self, citation: SourceReference | dict[str, Any]) -> Self:
        """Return a new immutable copy appending a SourceReference citation."""
        resolved = (
            citation
            if isinstance(citation, SourceReference)
            else SourceReference.from_dict(citation)
        )
        if resolved in self.citations:
            return self
        return self._mutate(citations=[*self.citations, resolved])

    def remove_citation(self, citation_text: str) -> Self:
        """Return a new immutable copy with targeted citation removed by text."""
        clean = citation_text.strip()
        filtered = [c for c in self.citations if c.citation_text != clean]
        if len(filtered) == len(self.citations):
            return self
        return self._mutate(citations=filtered)

    def update_note(
        self,
        note_id: NoteID | str,
        text: str | None = None,
        title: str | None = None,
        note_type: NoteType | str | None = None,
        tags: list[str] | None = None,
    ) -> Self:
        """Return a new immutable copy with targeted research note updated."""
        updated = super().update_note(
            note_id=note_id,
            text=text,
            title=title,
            note_type=note_type,
            tags=tags,
        )
        return self if updated is self else replace(updated, _dirty=True)

    # --- Serialization & Deserialization ---

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
            "audit": self.audit.to_dict(),
            "tombstone": self.tombstone.to_dict(),
            "notes": [n.to_dict() for n in self.notes],
        }

        if self.date is not None:
            data["date"] = self.date.to_dict()
        if self.location_id is not None:
            data["location_id"] = self.location_id.value
        if self.site_id is not None:
            data["site_id"] = self.site_id.value
        for opt_key in ("value", "description", "narrative"):
            opt_val = getattr(self, opt_key)
            if opt_val is not None:
                data[opt_key] = opt_val

        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Fact:
        """Deserialize a dictionary payload into an immutable Fact entity."""
        if not isinstance(data, dict):
            raise ModelFormatError("Fact payload must be a dictionary.")

        raw_id = data.get("id")
        if not raw_id:
            raise ModelFormatError("Missing required field 'id' for Fact.")

        fact_type = data.get("fact_type")
        title = data.get("title")
        subject = data.get("primary_subject_id")
        if not all((fact_type, title, subject)):
            raise ModelFormatError("Fact requires 'fact_type', 'title', and 'primary_subject_id'.")

        audit_raw = data.get("audit")
        tomb_raw = data.get("tombstone")
        notes_raw = data.get("notes", [])

        return cls.create(
            fact_id=str(raw_id),
            canonical_urn=str(data.get("canonical_urn", "")),
            fact_type=str(fact_type),
            title=str(title),
            primary_subject_id=str(subject),
            date=data.get("date"),
            location_id=data.get("location_id"),
            site_id=data.get("site_id"),
            value=data.get("value"),
            description=data.get("description"),
            narrative=data.get("narrative"),
            participants=_parse_dict_participants(data.get("participants", [])),
            citations=_parse_dict_citations(data.get("citations", [])),
            audit=AuditStamp.from_dict(audit_raw) if isinstance(audit_raw, dict) else None,
            tombstone=(
                Tombstone.from_dict(tomb_raw, id_cls=FactID) if isinstance(tomb_raw, dict) else None
            ),
            notes=[Note.from_dict(n) for n in notes_raw if isinstance(n, dict)],
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
        date_str = f" on {self.date}" if self.date else ""
        return (
            f"Fact [{self.fact_type.value}] '{self.title}' for "
            f"{self.primary_subject_id.value}{date_str} ({self.id.value})"
        )

    def __repr__(self) -> str:
        return (
            f"Fact(id={self.id!r}, fact_type={self.fact_type!r}, "
            f"title={self.title!r}, primary_subject_id={self.primary_subject_id!r})"
        )
