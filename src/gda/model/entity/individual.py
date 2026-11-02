"""Path: src/gda/model/entity/individual.py

Genealogical individual entity model extending BaseEntity[IndividualID].

Operational Role:
    Defines Individual representing genealogical personas across the digital archive.
    Inherits lifecycle management, audit timestamps, soft-deprecation tombstones, and
    embedded Note collections from BaseEntity[IndividualID]. Incorporates NamePerson
    for structured onomastic identity, GenderAtom for biological/birth sex classification,
    temporal vital bounds (birth/death dates and places), copy-on-write mutators, full
    dictionary/JSON serialization parity, and explicit in-memory dirty tracking (_dirty).
"""

from __future__ import annotations

import json
import re
from dataclasses import replace
from typing import Any, ClassVar, Self

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.errors import ModelFormatError, ModelRangeError
from gda.enums.archival import NoteType
from gda.enums.core import Sex
from gda.model.atom.date import EventDate, EventDateRange, IsoTimestamp
from gda.model.atom.gender import GenderAtom
from gda.model.atom.id import IndividualID, LocationID, NoteID, SiteID
from gda.model.base.audit import AuditStamp
from gda.model.base.entity import BaseEntity
from gda.model.base.name import NamePerson
from gda.model.base.note import Note
from gda.model.base.tombstone import Tombstone

__version__ = "1.0.0+build.8"

__all__ = ["Individual"]

_INDIVIDUAL_ID_PATTERN: re.Pattern[str] = re.compile(r"^IND-\d{6,}$")
_INDIVIDUAL_URN_PATTERN: re.Pattern[str] = re.compile(r"^urn:gda:ind:[a-z0-9_:\-]+$")


@dataclass(
    config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True),
    kw_only=True,
)
class Individual(BaseEntity[IndividualID]):
    """Genealogical individual record capturing intrinsic identity, vital bounds, and anchors."""

    name: NamePerson = Field(
        ..., description="Standard structured personal name for primary identity."
    )
    canonical_urn: str = Field(
        ...,
        description="Deterministic lookup URN (e.g., 'urn:gda:ind:smith_john_1842').",
    )
    gender: GenderAtom = Field(
        default_factory=lambda: GenderAtom("U"),
        description="Biological sex or gender recorded at birth ('M', 'F', or 'U').",
    )
    birth_date: EventDate | EventDateRange | None = Field(
        default=None,
        description="Point date or date range for birth/baptism with modifier support.",
    )
    death_date: EventDate | EventDateRange | None = Field(
        default=None,
        description="Point date or date range for death/burial with modifier support.",
    )
    birth_place_id: LocationID | SiteID | None = Field(
        default=None,
        description="Jurisdiction (LOC) or physical venue (SID) of vital origin.",
    )
    death_place_id: LocationID | SiteID | None = Field(
        default=None,
        description="Jurisdiction (LOC) or physical venue (SID) of vital conclusion.",
    )
    is_deceased: bool = Field(
        default=True,
        description="Death status flag; distinguishes confirmed deceased from living individuals.",
    )
    _dirty: bool = Field(
        default=False,
        description="True if entity has unpersisted state changes in working memory.",
    )

    _ID_PATTERN: ClassVar[re.Pattern[str]] = _INDIVIDUAL_ID_PATTERN
    _URN_PATTERN: ClassVar[re.Pattern[str]] = _INDIVIDUAL_URN_PATTERN

    def __post_init__(self) -> None:
        """Enforce domain invariants, regex formatting, and boundary guards."""
        super().__post_init__()

        if not isinstance(self.id, IndividualID):
            raise TypeError(
                f"Individual 'id' must be an instance of IndividualID, got {type(self.id).__name__}."
            )

        raw_id = self.id.value
        if not self._ID_PATTERN.match(raw_id):
            raise ModelFormatError(
                f"Invalid IndividualID format: '{raw_id}'. Must match 'IND-######'."
            )

        if not self.canonical_urn or not self._URN_PATTERN.match(self.canonical_urn):
            raise ModelFormatError(
                f"Invalid canonical_urn format: '{self.canonical_urn}'. "
                "Must match 'urn:gda:ind:<slug>'."
            )

        if (
            self.tombstone.is_deprecated
            and self.tombstone.superseded_by is not None
            and self.tombstone.superseded_by.value == raw_id
        ):
            raise ModelFormatError("Individual cannot be superseded by itself.")

        if not self.is_deceased:
            if self.death_date is not None:
                raise ModelFormatError(
                    "Individual cannot define death_date while is_deceased is False."
                )
            if self.death_place_id is not None:
                raise ModelFormatError(
                    "Individual cannot define death_place_id while is_deceased is False."
                )

        b_year = self.birth_year
        d_year = self.death_year
        if b_year is not None and d_year is not None and d_year < b_year:
            raise ModelRangeError(
                f"Death year ({d_year}) cannot precede birth year ({b_year}).",
                details={"birth_year": b_year, "death_year": d_year},
            )

    @property
    def canonical_name(self) -> str:
        """Forward standardized canonical modern string."""
        return self.name.canonical

    @property
    def full_name(self) -> str:
        """Forward structured personal display name."""
        return self.name.full_name

    @property
    def given(self) -> str | None:
        """Forward given name component."""
        return self.name.given

    @property
    def surname(self) -> str | None:
        """Forward surname component."""
        return self.name.surname

    @property
    def sex(self) -> str:
        """Backward-compatibility property returning single-character gender code."""
        return self.gender.value

    @property
    def married_names(self) -> list[str]:
        """Forward list of married surnames."""
        return self.name.married

    @property
    def aliases(self) -> list[str]:
        """Forward vernacular monikers or colloquial nicknames."""
        return self.name.aliases

    @property
    def alternate_names(self) -> list[str]:
        """Backward-compatibility accessor returning aliases list."""
        return self.name.aliases

    @property
    def is_dirty(self) -> bool:
        """Return True if entity has unpersisted in-memory modifications."""
        return self._dirty

    @property
    def birth_year(self) -> int | None:
        """Extract lower-bound birth year directly from temporal atom."""
        return self.birth_date.year_lower_bound if self.birth_date is not None else None

    @property
    def death_year(self) -> int | None:
        """Extract lower-bound death year directly from temporal atom."""
        return self.death_date.year_lower_bound if self.death_date is not None else None

    @property
    def approximate_age(self) -> int | None:
        """Calculate estimated lifespan duration in calendar years."""
        b_year = self.birth_year
        d_year = self.death_year
        if b_year is not None and d_year is not None:
            return d_year - b_year
        return None

    @property
    def sort_key(self) -> tuple[str, str, int, str]:
        """Deterministic Register Sort: (surname, given, birth_year_lower_bound, id)."""
        surname_key = (self.name.surname or "").lower()
        given_key = (self.name.given or "").lower()
        birth_year_key = self.birth_year if self.birth_year is not None else 9999
        return (surname_key, given_key, birth_year_key, self.id.value)

    @classmethod
    def create(
        cls,
        individual_id: IndividualID | str,
        name: NamePerson | str,
        canonical_urn: str,
        audit: AuditStamp | None = None,
        tombstone: Tombstone[IndividualID] | None = None,
        notes: list[Note] | None = None,
        gender: GenderAtom | Sex | str | None = None,
        birth_date: EventDate | EventDateRange | str | None = None,
        death_date: EventDate | EventDateRange | str | None = None,
        birth_place_id: LocationID | SiteID | str | None = None,
        death_place_id: LocationID | SiteID | str | None = None,
        is_deceased: bool | None = None,
    ) -> Individual:
        """Factory constructor instantiating a validated Individual entity."""
        resolved_id = (
            individual_id
            if isinstance(individual_id, IndividualID)
            else IndividualID(individual_id)
        )

        if isinstance(name, NamePerson):
            resolved_name = name
        elif isinstance(name, str):
            clean_str = name.strip()
            if not clean_str:
                raise ModelFormatError(
                    "Individual 'name' cannot be empty or whitespace."
                )
            resolved_name = NamePerson.create(raw=clean_str)
        else:
            raise TypeError(
                f"Individual 'name' must be an instance of NamePerson or str, got {type(name).__name__}."
            )

        resolved_gender = GenderAtom.from_input(gender)

        resolved_birth_date: EventDate | EventDateRange | None = None
        if birth_date is not None:
            resolved_birth_date = (
                birth_date
                if isinstance(birth_date, (EventDate, EventDateRange))
                else EventDate.create(birth_date)
            )

        resolved_death_date: EventDate | EventDateRange | None = None
        if death_date is not None:
            resolved_death_date = (
                death_date
                if isinstance(death_date, (EventDate, EventDateRange))
                else EventDate.create(death_date)
            )

        resolved_birth_place: LocationID | SiteID | None = None
        if birth_place_id is not None:
            if isinstance(birth_place_id, (LocationID, SiteID)):
                resolved_birth_place = birth_place_id
            else:
                str_bp = str(birth_place_id).strip()
                resolved_birth_place = (
                    SiteID(str_bp) if str_bp.startswith("SID-") else LocationID(str_bp)
                )

        resolved_death_place: LocationID | SiteID | None = None
        if death_place_id is not None:
            if isinstance(death_place_id, (LocationID, SiteID)):
                resolved_death_place = death_place_id
            else:
                str_dp = str(death_place_id).strip()
                resolved_death_place = (
                    SiteID(str_dp) if str_dp.startswith("SID-") else LocationID(str_dp)
                )

        if is_deceased is not None:
            resolved_deceased = is_deceased
        else:
            resolved_deceased = True

        now_ts = IsoTimestamp.now_utc()
        resolved_audit = (
            audit
            if audit is not None
            else AuditStamp(created_at=now_ts, updated_at=now_ts)
        )
        resolved_tombstone = (
            tombstone if tombstone is not None else Tombstone[IndividualID]()
        )
        resolved_notes = list(notes) if notes is not None else []

        kwargs: dict[str, Any] = {
            "id": resolved_id,
            "name": resolved_name,
            "canonical_urn": canonical_urn.strip() if canonical_urn else "",
            "gender": resolved_gender,
            "birth_date": resolved_birth_date,
            "death_date": resolved_death_date,
            "birth_place_id": resolved_birth_place,
            "death_place_id": resolved_death_place,
            "is_deceased": resolved_deceased,
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

    def add_alias(self, alias: str) -> Self:
        """Return a new immutable copy with unique alias appended to naming value object."""
        updated_name = self.name.add_alias(alias)
        if updated_name is self.name:
            return self
        return replace(
            self,
            name=updated_name,
            audit=self.audit.touch(IsoTimestamp.now_utc()),
            _dirty=True,
        )

    def remove_alias(self, alias: str) -> Self:
        """Return a new immutable copy with alias removed from naming value object."""
        updated_name = self.name.remove_alias(alias)
        if updated_name is self.name:
            return self
        return replace(
            self,
            name=updated_name,
            audit=self.audit.touch(IsoTimestamp.now_utc()),
            _dirty=True,
        )

    def add_married(self, married_name: str) -> Self:
        """Return a new immutable copy with unique married surname appended."""
        updated_name = self.name.add_married(married_name)
        if updated_name is self.name:
            return self
        return replace(
            self,
            name=updated_name,
            audit=self.audit.touch(IsoTimestamp.now_utc()),
            _dirty=True,
        )

    def remove_married(self, married_name: str) -> Self:
        """Return a new immutable copy with married surname removed."""
        updated_name = self.name.remove_married(married_name)
        if updated_name is self.name:
            return self
        return replace(
            self,
            name=updated_name,
            audit=self.audit.touch(IsoTimestamp.now_utc()),
            _dirty=True,
        )

    def update_name(self, name: NamePerson | str) -> Self:
        """Return a new immutable copy with updated onomastic personal name."""
        if isinstance(name, NamePerson):
            new_name = name
        elif isinstance(name, str):
            clean_str = name.strip()
            if not clean_str:
                raise ModelFormatError(
                    "Individual 'name' cannot be empty or whitespace."
                )
            new_name = NamePerson.create(raw=clean_str)
        else:
            raise TypeError(
                f"Individual 'name' must be an instance of NamePerson or str, got {type(name).__name__}."
            )
        return replace(
            self,
            name=new_name,
            audit=self.audit.touch(IsoTimestamp.now_utc()),
            _dirty=True,
        )

    def update_gender(self, gender: GenderAtom | Sex | str) -> Self:
        """Return a new immutable copy with updated gender at birth atom."""
        res_gender = GenderAtom.from_input(gender)
        return replace(
            self,
            gender=res_gender,
            audit=self.audit.touch(IsoTimestamp.now_utc()),
            _dirty=True,
        )

    def update_birth(
        self,
        birth_date: EventDate | EventDateRange | str | None = None,
        birth_place_id: LocationID | SiteID | str | None = None,
    ) -> Self:
        """Return a new immutable copy with updated birth event bounds."""
        resolved_date = (
            birth_date
            if (
                birth_date is None
                or isinstance(birth_date, (EventDate, EventDateRange))
            )
            else EventDate.create(birth_date)
        )

        resolved_place: LocationID | SiteID | None = None
        if birth_place_id is not None:
            if isinstance(birth_place_id, (LocationID, SiteID)):
                resolved_place = birth_place_id
            else:
                str_bp = str(birth_place_id).strip()
                resolved_place = (
                    SiteID(str_bp) if str_bp.startswith("SID-") else LocationID(str_bp)
                )
        else:
            resolved_place = self.birth_place_id

        return replace(
            self,
            birth_date=resolved_date if resolved_date is not None else self.birth_date,
            birth_place_id=resolved_place,
            audit=self.audit.touch(IsoTimestamp.now_utc()),
            _dirty=True,
        )

    def update_death(
        self,
        death_date: EventDate | EventDateRange | str | None = None,
        death_place_id: LocationID | SiteID | str | None = None,
        is_deceased: bool = True,
    ) -> Self:
        """Return a new immutable copy with updated death event bounds."""
        resolved_date = (
            death_date
            if (
                death_date is None
                or isinstance(death_date, (EventDate, EventDateRange))
            )
            else EventDate.create(death_date)
        )

        resolved_place: LocationID | SiteID | None = None
        if death_place_id is not None:
            if isinstance(death_place_id, (LocationID, SiteID)):
                resolved_place = death_place_id
            else:
                str_dp = str(death_place_id).strip()
                resolved_place = (
                    SiteID(str_dp) if str_dp.startswith("SID-") else LocationID(str_dp)
                )
        else:
            resolved_place = self.death_place_id

        return replace(
            self,
            death_date=resolved_date if resolved_date is not None else self.death_date,
            death_place_id=resolved_place,
            is_deceased=is_deceased,
            audit=self.audit.touch(IsoTimestamp.now_utc()),
            _dirty=True,
        )

    def update_urn(self, canonical_urn: str) -> Self:
        """Return a new immutable copy with updated canonical URN."""
        clean_urn = canonical_urn.strip() if canonical_urn else ""
        if not clean_urn or not self._URN_PATTERN.match(clean_urn):
            raise ModelFormatError(
                f"Invalid canonical_urn format: '{clean_urn}'. "
                "Must match 'urn:gda:ind:<slug>'."
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
        """Serialize Individual entity, domain attributes, and embedded notes to a dictionary."""
        data: dict[str, Any] = {
            "id": self.id.value,
            "name": self.name.to_dict(),
            "canonical_urn": self.canonical_urn,
            "gender": self.gender.value,
            "is_deceased": self.is_deceased,
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
        if self.birth_date is not None:
            data["birth_date"] = self.birth_date.to_dict()
        if self.death_date is not None:
            data["death_date"] = self.death_date.to_dict()
        if self.birth_place_id is not None:
            data["birth_place_id"] = self.birth_place_id.value
        if self.death_place_id is not None:
            data["death_place_id"] = self.death_place_id.value
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Individual:
        """Deserialize a dictionary payload into an immutable Individual entity."""
        if not isinstance(data, dict):
            raise ModelFormatError("Individual payload must be a dictionary.")

        raw_id = data.get("id")
        if not raw_id:
            raise ModelFormatError("Missing required field 'id' for Individual.")

        raw_name = data.get("name")
        if not raw_name:
            raise ModelFormatError("Missing required field 'name' for Individual.")
        name_obj = (
            NamePerson.from_dict(raw_name)
            if isinstance(raw_name, dict)
            else NamePerson.create(raw=str(raw_name))
        )

        b_date_payload = data.get("birth_date")
        birth_date: EventDate | EventDateRange | None = None
        if isinstance(b_date_payload, dict):
            birth_date = (
                EventDateRange.from_dict(b_date_payload)
                if "start_date" in b_date_payload
                else EventDate.from_dict(b_date_payload)
            )

        d_date_payload = data.get("death_date")
        death_date: EventDate | EventDateRange | None = None
        if isinstance(d_date_payload, dict):
            death_date = (
                EventDateRange.from_dict(d_date_payload)
                if "start_date" in d_date_payload
                else EventDate.from_dict(d_date_payload)
            )

        audit_payload = data.get("audit")
        audit_obj: AuditStamp | None = None
        if isinstance(audit_payload, dict):
            audit_obj = AuditStamp(
                created_at=IsoTimestamp(audit_payload["created_at"]),
                updated_at=IsoTimestamp(audit_payload["updated_at"]),
            )

        tombstone_payload = data.get("tombstone")
        tombstone_obj: Tombstone[IndividualID] | None = None
        if isinstance(tombstone_payload, dict):
            tombstone_obj = Tombstone[IndividualID](
                is_deprecated=tombstone_payload.get("is_deprecated", False),
                deprecated_at=(
                    IsoTimestamp(tombstone_payload["deprecated_at"])
                    if tombstone_payload.get("deprecated_at")
                    else None
                ),
                superseded_by=(
                    IndividualID(tombstone_payload["superseded_by"])
                    if tombstone_payload.get("superseded_by")
                    else None
                ),
            )

        notes_payload = data.get("notes", [])
        notes_list = [Note.from_dict(n) for n in notes_payload if isinstance(n, dict)]

        return cls.create(
            individual_id=str(raw_id),
            name=name_obj,
            canonical_urn=data.get("canonical_urn", ""),
            audit=audit_obj,
            tombstone=tombstone_obj,
            notes=notes_list,
            gender=data.get("gender", "U"),
            birth_date=birth_date,
            death_date=death_date,
            birth_place_id=data.get("birth_place_id"),
            death_place_id=data.get("death_place_id"),
            is_deceased=data.get("is_deceased", True),
        )

    def to_json(self) -> str:
        """Serialize Individual entity to a JSON formatted string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_json(cls, payload: str) -> Individual:
        """Deserialize a JSON string directly into an Individual instance."""
        try:
            data = json.loads(payload)
        except Exception as exc:
            raise ModelFormatError(
                f"Failed to parse Individual JSON string: {exc}"
            ) from exc
        return cls.from_dict(data)

    def __str__(self) -> str:
        """Render concise human-readable individual summary."""
        dates: list[str] = []
        if self.birth_date:
            dates.append(f"b. {self.birth_date}")
        if self.death_date:
            dates.append(f"d. {self.death_date}")
        elif not self.is_deceased:
            dates.append("living")
        elif dates:
            dates.append("d. unk")

        span_str = f" ({', '.join(dates)})" if dates else ""
        return f"{self.full_name} [{self.gender.value}]{span_str} ({self.id.value})"
