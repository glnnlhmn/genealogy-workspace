"""Path: src/gda/model/immigration/manifest.py

Historical ship passenger arrival manifests, customs lists, border crossings, and crew lists.

Operational Role:
    Defines ManifestPassenger (single passenger or crew member row on an arrival
    schedule) and ImmigrationManifestRecord (extending SourceRecord) to capture
    primary documentary evidence from maritime passenger arrival manifests, customs
    lists, oath-of-allegiance lists, border inspection cards, and crew lists with
    flatten_passengers() tabular projection (aligned with
    schemas/sources/immigration_manifest.schema.json).
"""

from __future__ import annotations

import json
import re
from typing import Any, ClassVar

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.enums.core import Sex
from gda.core.enums.immigration import ArrivalPassageClass
from gda.core.enums.sources import SourceRecordCategory, SourceRecordType
from gda.core.enums.vital import MaritalStatus
from gda.core.errors import ModelFormatError
from gda.core.introspectable import IntrospectableMixin
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import IndividualID, LocationID, MediaID, RepositoryID, SourceID
from gda.model.atom.urn import ArchivalURN, SourceURN
from gda.model.base.association import AssociatedIndividual
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate
from gda.model.base.source import SourceRecord
from gda.model.base.tombstone import Tombstone

__version__ = "1.0.0+build.1"

__all__ = [
    "ImmigrationManifestRecord",
    "ManifestPassenger",
]

_MANIFEST_CATEGORIES: frozenset[SourceRecordCategory] = frozenset(
    {
        SourceRecordCategory.IMMIGRATION,
        SourceRecordCategory.TRAVEL,
        SourceRecordCategory.CUSTOMS,
    }
)

_MANIFEST_RECORD_TYPES: frozenset[SourceRecordType] = frozenset(
    {
        SourceRecordType.PASSENGER_MANIFEST,
        SourceRecordType.CUSTOMS_LIST,
        SourceRecordType.OATH_OF_ALLEGIANCE_LIST,
        SourceRecordType.BORDER_CROSSING_CARD,
        SourceRecordType.CREW_LIST,
    }
)

_IMMIGRATION_URN_PATTERN: re.Pattern[str] = re.compile(
    r"^URN:IMMIGRATION:[0-9]{4}:[A-Z0-9_]+:[A-Za-z0-9_.-]+$"
)


def _resolve_immigration_urn(raw: ArchivalURN | str) -> ArchivalURN:
    """Coerce a raw URN string into ArchivalURN (URN:IMMIGRATION:...) or SourceURN (URN:SRC:...)."""
    if isinstance(raw, ArchivalURN):
        return raw
    token = str(raw).strip()
    if token.startswith("URN:IMMIGRATION:"):
        if not _IMMIGRATION_URN_PATTERN.match(token):
            raise ModelFormatError(
                f"Invalid Immigration URN syntax: '{token}'. "
                "Must match 'URN:IMMIGRATION:<YEAR>:<JURISDICTION>:<LOCATOR>'."
            )
        return ArchivalURN(token)
    return SourceURN(token)


def _deserialize_event_date(raw: Any, field_name: str) -> EventDate:
    """Coerce an EventDate instance, dictionary, or compact date string."""
    if isinstance(raw, EventDate):
        return raw
    if isinstance(raw, (dict, str)):
        return EventDate.from_dict(raw)
    raise ModelFormatError(f"Invalid '{field_name}' payload: expected EventDate, dict, or str.")


def _parse_enum_token[E](enum_cls: type[E], raw: Any, field_name: str) -> E:
    """Resolve a StrEnum by instance, exact value, or case-insensitive member name/value."""
    if isinstance(raw, enum_cls):
        return raw
    token = str(raw).strip()
    upper_token = token.upper()
    for member in enum_cls:  # type: ignore[attr-defined]
        if token == member.value or upper_token in (member.name, str(member.value).upper()):
            return member  # type: ignore[no-any-return]
    raise ModelFormatError(f"Invalid {field_name} value: '{raw}'.")


@dataclass(repr=False, config=ConfigDict(kw_only=True, frozen=True, extra="forbid", strict=True))
class ManifestPassenger(IntrospectableMixin):
    """Single passenger or crew member entry on a ship or border arrival manifest."""

    full_name: str = Field(
        ...,
        description="Verbatim or canonical full name of the passenger or crew member.",
    )
    line_number: int | None = Field(
        default=None,
        ge=1,
        description="1-based line number on the manifest page or inspection card.",
    )
    individual_id: IndividualID | None = Field(
        default=None,
        description="Resolved canonical IndividualID if linked to a person entity.",
    )
    age_raw: str | None = Field(
        default=None,
        description="Verbatim age stated on the manifest (e.g., '28', '11 mos').",
    )
    sex: Sex | None = Field(
        default=None,
        description="Standardized sex classification (Sex.MALE, Sex.FEMALE, Sex.UNKNOWN).",
    )
    marital_status: MaritalStatus | None = Field(
        default=None,
        description="Standardized marital status recorded on the manifest.",
    )
    occupation: str | None = Field(
        default=None,
        description="Verbatim trade, calling, or occupation stated on the manifest.",
    )
    passage_class: ArrivalPassageClass | None = Field(
        default=None,
        description="Accommodation or manifest class (STEERAGE, CABIN, SECOND_CABIN, CREW, OVERLAND, OTHER).",
    )
    nationality_or_race_raw: str | None = Field(
        default=None,
        description="Verbatim nationality, country of allegiance, or race/people entry.",
    )
    last_permanent_residence_raw: str | None = Field(
        default=None,
        description="Verbatim town, parish, or country of last permanent residence.",
    )
    last_permanent_residence_id: LocationID | None = Field(
        default=None,
        description="Resolved canonical LocationID for the last permanent residence.",
    )
    final_destination_raw: str | None = Field(
        default=None,
        description="Verbatim intended city, town, or state of destination.",
    )
    final_destination_id: LocationID | None = Field(
        default=None,
        description="Resolved canonical LocationID for the intended final destination.",
    )
    relative_joined_name: str | None = Field(
        default=None,
        description="Verbatim name of relative or friend the passenger is joining.",
    )
    relative_joined_relationship: str | None = Field(
        default=None,
        description="Verbatim relationship to the person being joined (e.g., 'brother', 'husband').",
    )
    relative_joined_address: str | None = Field(
        default=None,
        description="Verbatim street or town address of the relative or friend being joined.",
    )

    def __post_init__(self) -> None:
        """Enforce non-empty full_name hygiene."""
        clean_name = self.full_name.strip()
        if not clean_name:
            raise ModelFormatError("ManifestPassenger 'full_name' cannot be empty or whitespace.")
        if clean_name != self.full_name:
            object.__setattr__(self, "full_name", clean_name)

    @classmethod
    def create(
        cls,
        full_name: str,
        line_number: int | None = None,
        individual_id: IndividualID | str | None = None,
        age_raw: str | None = None,
        sex: Sex | str | None = None,
        marital_status: MaritalStatus | str | None = None,
        occupation: str | None = None,
        passage_class: ArrivalPassageClass | str | None = None,
        nationality_or_race_raw: str | None = None,
        last_permanent_residence_raw: str | None = None,
        last_permanent_residence_id: LocationID | str | None = None,
        final_destination_raw: str | None = None,
        final_destination_id: LocationID | str | None = None,
        relative_joined_name: str | None = None,
        relative_joined_relationship: str | None = None,
        relative_joined_address: str | None = None,
    ) -> ManifestPassenger:
        """Factory constructor instantiating a validated ManifestPassenger."""
        res_ind = (
            individual_id
            if (individual_id is None or isinstance(individual_id, IndividualID))
            else IndividualID(individual_id)
        )
        res_sex = _parse_enum_token(Sex, sex, "Sex") if sex is not None else None
        res_marital = (
            _parse_enum_token(MaritalStatus, marital_status, "MaritalStatus")
            if marital_status is not None
            else None
        )
        res_class = (
            _parse_enum_token(ArrivalPassageClass, passage_class, "ArrivalPassageClass")
            if passage_class is not None
            else None
        )
        res_last_loc = (
            last_permanent_residence_id
            if (
                last_permanent_residence_id is None
                or isinstance(last_permanent_residence_id, LocationID)
            )
            else LocationID(last_permanent_residence_id)
        )
        res_dest_loc = (
            final_destination_id
            if (final_destination_id is None or isinstance(final_destination_id, LocationID))
            else LocationID(final_destination_id)
        )
        return cls(
            full_name=full_name,
            line_number=line_number,
            individual_id=res_ind,
            age_raw=age_raw,
            sex=res_sex,
            marital_status=res_marital,
            occupation=occupation,
            passage_class=res_class,
            nationality_or_race_raw=nationality_or_race_raw,
            last_permanent_residence_raw=last_permanent_residence_raw,
            last_permanent_residence_id=res_last_loc,
            final_destination_raw=final_destination_raw,
            final_destination_id=res_dest_loc,
            relative_joined_name=relative_joined_name,
            relative_joined_relationship=relative_joined_relationship,
            relative_joined_address=relative_joined_address,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize ManifestPassenger to a dictionary."""
        data: dict[str, Any] = {
            "full_name": self.full_name,
        }
        if self.line_number is not None:
            data["line_number"] = self.line_number
        if self.individual_id is not None:
            data["individual_id"] = str(self.individual_id)
        if self.age_raw is not None:
            data["age_raw"] = self.age_raw
        if self.sex is not None:
            data["sex"] = self.sex.value
        if self.marital_status is not None:
            data["marital_status"] = self.marital_status.value
        if self.occupation is not None:
            data["occupation"] = self.occupation
        if self.passage_class is not None:
            data["passage_class"] = self.passage_class.value
        if self.nationality_or_race_raw is not None:
            data["nationality_or_race_raw"] = self.nationality_or_race_raw
        if self.last_permanent_residence_raw is not None:
            data["last_permanent_residence_raw"] = self.last_permanent_residence_raw
        if self.last_permanent_residence_id is not None:
            data["last_permanent_residence_id"] = str(self.last_permanent_residence_id)
        if self.final_destination_raw is not None:
            data["final_destination_raw"] = self.final_destination_raw
        if self.final_destination_id is not None:
            data["final_destination_id"] = str(self.final_destination_id)
        if self.relative_joined_name is not None:
            data["relative_joined_name"] = self.relative_joined_name
        if self.relative_joined_relationship is not None:
            data["relative_joined_relationship"] = self.relative_joined_relationship
        if self.relative_joined_address is not None:
            data["relative_joined_address"] = self.relative_joined_address
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ManifestPassenger:
        """Deserialize a dictionary payload into a ManifestPassenger."""
        if not isinstance(data, dict):
            raise ModelFormatError("ManifestPassenger payload must be a dictionary.")
        name = data.get("full_name")
        if name is None:
            raise ModelFormatError("ManifestPassenger requires 'full_name'.")
        raw_line = data.get("line_number")
        return cls.create(
            full_name=str(name),
            line_number=int(raw_line) if raw_line is not None else None,
            individual_id=data.get("individual_id"),
            age_raw=data.get("age_raw"),
            sex=data.get("sex"),
            marital_status=data.get("marital_status"),
            occupation=data.get("occupation"),
            passage_class=data.get("passage_class"),
            nationality_or_race_raw=data.get("nationality_or_race_raw"),
            last_permanent_residence_raw=data.get("last_permanent_residence_raw"),
            last_permanent_residence_id=data.get("last_permanent_residence_id"),
            final_destination_raw=data.get("final_destination_raw"),
            final_destination_id=data.get("final_destination_id"),
            relative_joined_name=data.get("relative_joined_name"),
            relative_joined_relationship=data.get("relative_joined_relationship"),
            relative_joined_address=data.get("relative_joined_address"),
        )

    def to_json(self) -> str:
        """Serialize ManifestPassenger to a JSON formatted string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_json(cls, payload: str) -> ManifestPassenger:
        """Deserialize a JSON string directly into a ManifestPassenger."""
        try:
            data = json.loads(payload)
        except Exception as exc:
            raise ModelFormatError(f"Failed to parse ManifestPassenger JSON string: {exc}") from exc
        return cls.from_dict(data)

    def __str__(self) -> str:
        if self.line_number is not None:
            return f"Line {self.line_number}: {self.full_name}"
        return self.full_name


@dataclass(repr=False, config=ConfigDict(kw_only=True, frozen=True, extra="forbid", strict=True))
class ImmigrationManifestRecord(SourceRecord):
    """Primary archival record documenting a passenger arrival manifest or border crossing."""

    record_category: SourceRecordCategory = Field(
        default=SourceRecordCategory.IMMIGRATION,
        description="High-level archival domain category (IMMIGRATION, TRAVEL, CUSTOMS).",
    )
    record_type: SourceRecordType = Field(
        default=SourceRecordType.PASSENGER_MANIFEST,
        description="Specific manifest classification.",
    )
    port_of_arrival_raw: str = Field(
        ...,
        description="Verbatim port of entry or border station name.",
    )
    arrival_date: EventDate = Field(
        ...,
        description="Date the vessel or traveler arrived at the port of entry.",
    )
    manifest_locator: str = Field(
        ...,
        description="Primary NARA microfilm roll, manifest ID, or archival call locator.",
    )
    passengers: tuple[ManifestPassenger, ...] = Field(
        ...,
        description="Ordered tuple of one or more passenger or crew entries on this manifest.",
    )
    port_of_arrival_id: LocationID | None = Field(
        default=None,
        description="Resolved canonical LocationID for the port of arrival.",
    )
    ship_name: str | None = Field(
        default=None,
        description="Verbatim name of the steamship, sailing packet, or vessel.",
    )
    master_or_captain: str | None = Field(
        default=None,
        description="Name of the vessel's master or captain.",
    )
    shipping_line: str | None = Field(
        default=None,
        description="Operating steamship line or packet company.",
    )
    port_of_departure_raw: str | None = Field(
        default=None,
        description="Verbatim port of embarkation or departure.",
    )
    port_of_departure_id: LocationID | None = Field(
        default=None,
        description="Resolved canonical LocationID for the port of departure.",
    )
    list_number: str | None = Field(
        default=None,
        description="Manifest sheet, list, or page designation.",
    )

    ALLOWED_CATEGORIES: ClassVar[frozenset[SourceRecordCategory]] = _MANIFEST_CATEGORIES
    ALLOWED_RECORD_TYPES: ClassVar[frozenset[SourceRecordType]] = _MANIFEST_RECORD_TYPES

    def __post_init__(self) -> None:
        """Enforce category, record_type, required strings, and non-empty passengers."""
        super().__post_init__()

        if self.record_category not in self.ALLOWED_CATEGORIES:
            raise ModelFormatError(
                f"{self.__class__.__name__} requires record_category in "
                f"{sorted(c.value for c in self.ALLOWED_CATEGORIES)}, "
                f"got '{self.record_category.value}'."
            )

        if self.record_type not in self.ALLOWED_RECORD_TYPES:
            raise ModelFormatError(
                f"{self.__class__.__name__} requires record_type in "
                f"{sorted(t.value for t in self.ALLOWED_RECORD_TYPES)}, "
                f"got '{self.record_type.value}'."
            )

        for field_name in ("port_of_arrival_raw", "manifest_locator"):
            raw_val = getattr(self, field_name)
            cleaned = raw_val.strip()
            if not cleaned:
                raise ModelFormatError(
                    f"{self.__class__.__name__} '{field_name}' cannot be empty or whitespace."
                )
            if cleaned != raw_val:
                object.__setattr__(self, field_name, cleaned)

        if not self.passengers:
            raise ModelFormatError(
                f"{self.__class__.__name__} requires at least one ManifestPassenger."
            )

    @property
    def passenger_count(self) -> int:
        """Return count of passengers recorded on this manifest extract."""
        return len(self.passengers)

    def flatten_passengers(self) -> tuple[dict[str, Any], ...]:
        """Flatten voyage and manifest header context with each passenger row."""
        header: dict[str, Any] = {
            "source_id": str(self.source_id),
            "source_urn": str(self.source_urn),
            "record_category": self.record_category.value,
            "record_type": self.record_type.value,
            "port_of_arrival_raw": self.port_of_arrival_raw,
            "arrival_date": str(self.arrival_date),
            "ship_name": self.ship_name,
            "port_of_departure_raw": self.port_of_departure_raw,
            "manifest_locator": self.manifest_locator,
            "list_number": self.list_number,
        }
        return tuple({**header, **passenger.to_dict()} for passenger in self.passengers)

    @classmethod
    def create(  # type: ignore[override]
        cls,
        source_id: SourceID | str,
        source_urn: ArchivalURN | str,
        description: str,
        repository_id: RepositoryID | str,
        port_of_arrival_raw: str,
        arrival_date: EventDate | dict[str, Any] | str,
        manifest_locator: str,
        passengers: list[ManifestPassenger | dict[str, Any]] | tuple[ManifestPassenger, ...],
        record_category: SourceRecordCategory | str = SourceRecordCategory.IMMIGRATION,
        record_type: SourceRecordType | str = SourceRecordType.PASSENGER_MANIFEST,
        port_of_arrival_id: LocationID | str | None = None,
        ship_name: str | None = None,
        master_or_captain: str | None = None,
        shipping_line: str | None = None,
        port_of_departure_raw: str | None = None,
        port_of_departure_id: LocationID | str | None = None,
        list_number: str | None = None,
        audit: AuditStamp | None = None,
        media_ids: list[MediaID | str] | None = None,
        associated_people: list[AssociatedIndividual] | None = None,
        tombstone: Tombstone[SourceID] | None = None,
    ) -> ImmigrationManifestRecord:
        """Factory constructor instantiating a validated ImmigrationManifestRecord."""
        resolved_sid = source_id if isinstance(source_id, SourceID) else SourceID(source_id)
        resolved_urn = _resolve_immigration_urn(source_urn)
        resolved_rep = (
            repository_id
            if isinstance(repository_id, RepositoryID)
            else RepositoryID(repository_id)
        )
        res_cat = (
            record_category
            if isinstance(record_category, SourceRecordCategory)
            else SourceRecordCategory(str(record_category).strip().upper())
        )
        res_type = (
            record_type
            if isinstance(record_type, SourceRecordType)
            else SourceRecordType(str(record_type).strip().upper())
        )
        res_arr_loc = (
            port_of_arrival_id
            if (port_of_arrival_id is None or isinstance(port_of_arrival_id, LocationID))
            else LocationID(port_of_arrival_id)
        )
        res_dep_loc = (
            port_of_departure_id
            if (port_of_departure_id is None or isinstance(port_of_departure_id, LocationID))
            else LocationID(port_of_departure_id)
        )
        res_arrival_dt = _deserialize_event_date(arrival_date, "arrival_date")

        resolved_passengers: tuple[ManifestPassenger, ...] = tuple(
            p if isinstance(p, ManifestPassenger) else ManifestPassenger.from_dict(p)
            for p in passengers
        )

        resolved_audit = audit if audit is not None else AuditStamp.now()
        resolved_media = [m if isinstance(m, MediaID) else MediaID(m) for m in (media_ids or [])]

        return cls(
            source_id=resolved_sid,
            source_urn=resolved_urn,
            record_category=res_cat,
            record_type=res_type,
            description=description.strip() if isinstance(description, str) else description,
            repository_id=resolved_rep,
            audit=resolved_audit,
            media_ids=resolved_media,
            associated_people=associated_people or [],
            tombstone=tombstone,
            port_of_arrival_raw=port_of_arrival_raw,
            arrival_date=res_arrival_dt,
            manifest_locator=manifest_locator,
            passengers=resolved_passengers,
            port_of_arrival_id=res_arr_loc,
            ship_name=ship_name,
            master_or_captain=master_or_captain,
            shipping_line=shipping_line,
            port_of_departure_raw=port_of_departure_raw,
            port_of_departure_id=res_dep_loc,
            list_number=list_number,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize ImmigrationManifestRecord to a dictionary."""
        data = super().to_dict()
        data.update(
            {
                "record_type": self.record_type.value,
                "port_of_arrival_raw": self.port_of_arrival_raw,
                "arrival_date": self.arrival_date.to_dict(),
                "manifest_locator": self.manifest_locator,
                "passengers": [p.to_dict() for p in self.passengers],
            }
        )
        if self.port_of_arrival_id is not None:
            data["port_of_arrival_id"] = str(self.port_of_arrival_id)
        if self.ship_name is not None:
            data["ship_name"] = self.ship_name
        if self.master_or_captain is not None:
            data["master_or_captain"] = self.master_or_captain
        if self.shipping_line is not None:
            data["shipping_line"] = self.shipping_line
        if self.port_of_departure_raw is not None:
            data["port_of_departure_raw"] = self.port_of_departure_raw
        if self.port_of_departure_id is not None:
            data["port_of_departure_id"] = str(self.port_of_departure_id)
        if self.list_number is not None:
            data["list_number"] = self.list_number
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ImmigrationManifestRecord:
        """Deserialize a dictionary payload into an ImmigrationManifestRecord."""
        if not isinstance(data, dict):
            raise ModelFormatError("ImmigrationManifestRecord payload must be a dictionary.")

        sid = data.get("source_id")
        raw_urn = data.get("source_urn")
        desc = data.get("description")
        rep = data.get("repository_id")
        audit_payload = data.get("audit")
        port = data.get("port_of_arrival_raw")
        raw_arrival = data.get("arrival_date")
        locator = data.get("manifest_locator")
        raw_passengers = data.get("passengers")

        if not all(
            (sid, raw_urn, desc, rep, audit_payload, port, raw_arrival, locator, raw_passengers)
        ):
            raise ModelFormatError(
                "ImmigrationManifestRecord requires source_id, source_urn, description, "
                "repository_id, audit, port_of_arrival_raw, arrival_date, manifest_locator, "
                "and passengers."
            )

        if not isinstance(raw_passengers, (list, tuple)):
            raise ModelFormatError(
                "ImmigrationManifestRecord 'passengers' must be a list or tuple."
            )

        if isinstance(audit_payload, AuditStamp):
            audit_obj = audit_payload
        elif isinstance(audit_payload, dict):
            audit_obj = AuditStamp(
                created_at=IsoTimestamp(audit_payload["created_at"]),
                updated_at=IsoTimestamp(audit_payload["updated_at"]),
            )
        else:
            raise ModelFormatError(
                "ImmigrationManifestRecord audit must be an AuditStamp or dictionary."
            )

        tombstone_payload = data.get("tombstone")
        tombstone_obj: Tombstone[SourceID] | None = None
        if isinstance(tombstone_payload, dict):
            raw_sup = tombstone_payload.get("superseded_by")
            sup_id = (
                raw_sup
                if (raw_sup is None or isinstance(raw_sup, SourceID))
                else SourceID(str(raw_sup))
            )
            tombstone_obj = Tombstone[SourceID](
                is_deprecated=tombstone_payload.get("is_deprecated", False),
                deprecated_at=(
                    IsoTimestamp(tombstone_payload["deprecated_at"])
                    if tombstone_payload.get("deprecated_at")
                    else None
                ),
                superseded_by=sup_id,
            )

        return cls.create(
            source_id=str(sid),
            source_urn=str(raw_urn),
            description=str(desc),
            repository_id=str(rep),
            port_of_arrival_raw=str(port),
            arrival_date=raw_arrival,
            manifest_locator=str(locator),
            passengers=list(raw_passengers),
            record_category=data.get("record_category", SourceRecordCategory.IMMIGRATION),
            record_type=data.get("record_type", SourceRecordType.PASSENGER_MANIFEST),
            port_of_arrival_id=data.get("port_of_arrival_id"),
            ship_name=data.get("ship_name"),
            master_or_captain=data.get("master_or_captain"),
            shipping_line=data.get("shipping_line"),
            port_of_departure_raw=data.get("port_of_departure_raw"),
            port_of_departure_id=data.get("port_of_departure_id"),
            list_number=data.get("list_number"),
            audit=audit_obj,
            media_ids=data.get("media_ids", []),
            associated_people=[
                AssociatedIndividual.from_dict(p) for p in data.get("associated_people", [])
            ],
            tombstone=tombstone_obj,
        )

    def __str__(self) -> str:
        vessel = f" on {self.ship_name}" if self.ship_name else ""
        return (
            f"ImmigrationManifestRecord [{self.record_type.value}] "
            f"{self.port_of_arrival_raw}{vessel} ({self.manifest_locator})"
        )
