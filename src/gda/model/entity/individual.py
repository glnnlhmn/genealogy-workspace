"""Path: src/gda/model/entity/individual.py

Genealogical individual entity model extending BaseEntity[IndividualID].

Operational Role:
    Defines Individual representing genealogical personas across the digital archive.
    Inherits lifecycle management, audit timestamps, soft-deprecation tombstones, and
    embedded Note collections from BaseEntity[IndividualID]. Incorporates NamePerson
    for structured onomastic identity, GenderAtom for biological/birth sex classification,
    temporal vital bounds (EventDate supporting exact, approximate, and BETWEEN ranges),
    copy-on-write mutators, full dictionary/JSON serialization parity, and explicit
    in-memory dirty tracking (_dirty).
"""

from __future__ import annotations

import json
import re
from dataclasses import replace
from typing import Any, ClassVar, Self

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.dates import parse_iso_date_parts, utc_now_iso
from gda.core.enums.archival import NoteType
from gda.core.enums.core import Sex
from gda.core.enums.date import DateModifier
from gda.core.errors import ModelFormatError, ModelRangeError
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.gender import GenderAtom
from gda.model.atom.id import IndividualID, LocationID, NoteID, SiteID
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate
from gda.model.base.entity import BaseEntity
from gda.model.base.name import NamePerson
from gda.model.base.note import Note
from gda.model.base.tombstone import Tombstone

__version__ = "2.0.0+build.4"

__all__ = ["Individual"]

_INDIVIDUAL_ID_PATTERN: re.Pattern[str] = re.compile(r"^IND-\d{6,}$")
_INDIVIDUAL_URN_PATTERN: re.Pattern[str] = re.compile(r"^urn:gda:ind:[a-z0-9_:\-]+$")


def _resolve_vital_date(
    val: EventDate | str | dict[str, Any] | None,
) -> EventDate | None:
    """Resolve raw vital date expression, dict payload, or EventDate into EventDate."""
    if val is None or isinstance(val, EventDate):
        return val
    if isinstance(val, str):
        return EventDate.create(val)
    if isinstance(val, dict):
        if "start_date" in val and "end_date" in val:
            return EventDate.create(
                date=str(val["start_date"]),
                modifier=val.get("modifier", DateModifier.BETWEEN),
                end_date=str(val["end_date"]),
            )
        return EventDate.from_dict(val)
    raise TypeError(f"Unsupported vital date payload type: {type(val).__name__}.")


def _resolve_place_id(
    place_id: LocationID | SiteID | str | None,
) -> LocationID | SiteID | None:
    """Resolve LocationID, SiteID, or prefixed string token into strongly-typed AtomID."""
    if place_id is None or isinstance(place_id, (LocationID, SiteID)):
        return place_id
    token = str(place_id).strip()
    return SiteID(token) if token.startswith("SID-") else LocationID(token)


def _resolve_gender(gender: GenderAtom | Sex | str | None) -> GenderAtom:
    """Resolve GenderAtom, Sex enum, raw string token, or None into GenderAtom."""
    if gender is None:
        return GenderAtom("U")
    if isinstance(gender, GenderAtom):
        return gender
    if isinstance(gender, Sex):
        return GenderAtom(gender.value[0])
    token = str(gender).strip()
    try:
        sex_member = Sex.from_input(token)
        return GenderAtom(sex_member.value[0])
    except ValueError:
        return GenderAtom(token)


@dataclass(
    repr=False,
    config=ConfigDict(frozen=True, extra="forbid", strict=True),
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
    birth_date: EventDate | None = Field(
        default=None,
        description="Point or BETWEEN range date for birth/baptism with modifier support.",
    )
    death_date: EventDate | None = Field(
        default=None,
        description="Point or BETWEEN range date for death/burial with modifier support.",
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

        clean_urn = self.canonical_urn.strip() if self.canonical_urn else ""
        if not clean_urn or not self._URN_PATTERN.match(clean_urn):
            raise ModelFormatError(
                f"Invalid canonical_urn format: '{self.canonical_urn}'. "
                "Must match 'urn:gda:ind:<slug>'."
            )
        if clean_urn != self.canonical_urn:
            object.__setattr__(self, "canonical_urn", clean_urn)

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
        return (
            parse_iso_date_parts(self.birth_date.date.value)[0]
            if self.birth_date is not None
            else None
        )

    @property
    def death_year(self) -> int | None:
        """Extract lower-bound death year directly from temporal atom."""
        return (
            parse_iso_date_parts(self.death_date.date.value)[0]
            if self.death_date is not None
            else None
        )

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
        birth_date: EventDate | str | dict[str, Any] | None = None,
        death_date: EventDate | str | dict[str, Any] | None = None,
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
                raise ModelFormatError("Individual 'name' cannot be empty or whitespace.")
            resolved_name = NamePerson.create(raw=clean_str)
        else:
            raise TypeError(
                f"Individual 'name' must be an instance of NamePerson or str, got {type(name).__name__}."
            )

        resolved_gender = _resolve_gender(gender)
        resolved_birth_date = _resolve_vital_date(birth_date)
        resolved_death_date = _resolve_vital_date(death_date)
        resolved_birth_place = _resolve_place_id(birth_place_id)
        resolved_death_place = _resolve_place_id(death_place_id)
        resolved_deceased = is_deceased if is_deceased is not None else True

        now_ts = IsoTimestamp(utc_now_iso())
        resolved_audit = (
            audit if audit is not None else AuditStamp(created_at=now_ts, updated_at=now_ts)
        )
        resolved_tombstone = tombstone if tombstone is not None else Tombstone[IndividualID]()
        resolved_notes = list(notes) if notes is not None else []

        return cls(
            id=resolved_id,
            name=resolved_name,
            canonical_urn=canonical_urn.strip() if canonical_urn else "",
            gender=resolved_gender,
            birth_date=resolved_birth_date,
            death_date=resolved_death_date,
            birth_place_id=resolved_birth_place,
            death_place_id=resolved_death_place,
            is_deceased=resolved_deceased,
            audit=resolved_audit,
            tombstone=resolved_tombstone,
            notes=resolved_notes,
            _dirty=False,
        )

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
            audit=self.audit.touch(IsoTimestamp(utc_now_iso())),
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
            audit=self.audit.touch(IsoTimestamp(utc_now_iso())),
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
            audit=self.audit.touch(IsoTimestamp(utc_now_iso())),
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
            audit=self.audit.touch(IsoTimestamp(utc_now_iso())),
            _dirty=True,
        )

    def update_name(self, name: NamePerson | str) -> Self:
        """Return a new immutable copy with updated onomastic personal name."""
        if isinstance(name, NamePerson):
            new_name = name
        elif isinstance(name, str):
            clean_str = name.strip()
            if not clean_str:
                raise ModelFormatError("Individual 'name' cannot be empty or whitespace.")
            new_name = NamePerson.create(raw=clean_str)
        else:
            raise TypeError(
                f"Individual 'name' must be an instance of NamePerson or str, got {type(name).__name__}."
            )
        if new_name == self.name:
            return self
        return replace(
            self,
            name=new_name,
            audit=self.audit.touch(IsoTimestamp(utc_now_iso())),
            _dirty=True,
        )

    def update_gender(self, gender: GenderAtom | Sex | str) -> Self:
        """Return a new immutable copy with updated gender at birth atom."""
        res_gender = _resolve_gender(gender)
        if res_gender == self.gender:
            return self
        return replace(
            self,
            gender=res_gender,
            audit=self.audit.touch(IsoTimestamp(utc_now_iso())),
            _dirty=True,
        )

    def update_birth(
        self,
        birth_date: EventDate | str | dict[str, Any] | None = None,
        birth_place_id: LocationID | SiteID | str | None = None,
    ) -> Self:
        """Return a new immutable copy with updated birth event bounds."""
        resolved_date = _resolve_vital_date(birth_date)
        final_date = resolved_date if resolved_date is not None else self.birth_date
        final_place = (
            _resolve_place_id(birth_place_id) if birth_place_id is not None else self.birth_place_id
        )

        if final_date == self.birth_date and final_place == self.birth_place_id:
            return self

        return replace(
            self,
            birth_date=final_date,
            birth_place_id=final_place,
            audit=self.audit.touch(IsoTimestamp(utc_now_iso())),
            _dirty=True,
        )

    def update_death(
        self,
        death_date: EventDate | str | dict[str, Any] | None = None,
        death_place_id: LocationID | SiteID | str | None = None,
        is_deceased: bool = True,
    ) -> Self:
        """Return a new immutable copy with updated death event bounds."""
        resolved_date = _resolve_vital_date(death_date)
        final_date = resolved_date if resolved_date is not None else self.death_date
        final_place = (
            _resolve_place_id(death_place_id) if death_place_id is not None else self.death_place_id
        )

        if (
            final_date == self.death_date
            and final_place == self.death_place_id
            and is_deceased == self.is_deceased
        ):
            return self

        return replace(
            self,
            death_date=final_date,
            death_place_id=final_place,
            is_deceased=is_deceased,
            audit=self.audit.touch(IsoTimestamp(utc_now_iso())),
            _dirty=True,
        )

    def update_urn(self, canonical_urn: str) -> Self:
        """Return a new immutable copy with updated canonical URN."""
        clean_urn = canonical_urn.strip() if canonical_urn else ""
        if not clean_urn or not self._URN_PATTERN.match(clean_urn):
            raise ModelFormatError(
                f"Invalid canonical_urn format: '{clean_urn}'. Must match 'urn:gda:ind:<slug>'."
            )
        if clean_urn == self.canonical_urn:
            return self
        return replace(
            self,
            canonical_urn=clean_urn,
            audit=self.audit.touch(IsoTimestamp(utc_now_iso())),
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
        updated = super().update_note(
            note_id=note_id,
            text=text,
            title=title,
            note_type=note_type,
            tags=tags,
        )
        if updated is self:
            return self
        return replace(updated, _dirty=True)

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
                "deprecated_at": (
                    str(self.tombstone.deprecated_at)
                    if self.tombstone.deprecated_at is not None
                    else None
                ),
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
            canonical_urn=str(data.get("canonical_urn", "")),
            audit=audit_obj,
            tombstone=tombstone_obj,
            notes=notes_list,
            gender=data.get("gender", "U"),
            birth_date=data.get("birth_date"),
            death_date=data.get("death_date"),
            birth_place_id=data.get("birth_place_id"),
            death_place_id=data.get("death_place_id"),
            is_deceased=bool(data.get("is_deceased", True)),
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
            raise ModelFormatError(f"Failed to parse Individual JSON string: {exc}") from exc
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

    def __repr__(self) -> str:
        return (
            f"Individual(id={self.id!r}, full_name={self.full_name!r}, "
            f"gender={self.gender!r}, canonical_urn={self.canonical_urn!r})"
        )
