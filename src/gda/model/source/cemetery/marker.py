"""Path: src/gda/model/source/cemetery/marker.py

Cemetery marker, headstone, monument, mausoleum crypt, and memorial inscription models.

Operational Role:
    Defines MarkerInterment (an inscribed person entry on a physical stone or plaque)
    and CemeteryMarkerRecord (extending SourceRecord) to capture primary documentary
    and epigraphic evidence from headstones, footstones, family monuments, obelisks,
    memorial plaques, and mausoleum crypts (aligned with
    schemas/sources/cemetery_marker.schema.json).
"""

from __future__ import annotations

import json
from typing import Any, ClassVar

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.enums.site import MarkerCondition, MarkerMaterial, MarkerType
from gda.core.enums.sources import SourceRecordCategory, SourceRecordType
from gda.core.errors import ModelFormatError
from gda.core.introspectable import IntrospectableMixin
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import IndividualID, LocationID, MediaID, RepositoryID, SiteID, SourceID
from gda.model.atom.urn import ArchivalURN, CemeteryPlotUrn, SourceURN
from gda.model.base.age import Age
from gda.model.base.association import AssociatedIndividual
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate
from gda.model.base.source import SourceRecord
from gda.model.base.tombstone import Tombstone

__version__ = "1.0.0+build.2"

__all__ = [
    "CemeteryMarkerRecord",
    "MarkerInterment",
]

_MARKER_RECORD_TYPES: frozenset[SourceRecordType] = frozenset(
    {
        SourceRecordType.CEMETERY_MARKER,
        SourceRecordType.HEADSTONE,
        SourceRecordType.FOOTSTONE,
        SourceRecordType.FAMILY_MONUMENT,
        SourceRecordType.MEMORIAL_PLAQUE,
        SourceRecordType.MAUSOLEUM_CRYPT,
    }
)


def _resolve_cemetery_urn(raw: ArchivalURN | str) -> ArchivalURN:
    """Coerce a raw URN string into CemeteryPlotUrn or SourceURN."""
    if isinstance(raw, ArchivalURN):
        return raw
    token = str(raw).strip()
    if token.startswith("URN:CEM:"):
        return CemeteryPlotUrn(token)
    return SourceURN(token)


def _deserialize_event_date(raw: Any, field_name: str) -> EventDate:
    """Coerce an EventDate instance, dictionary, or compact date string."""
    if isinstance(raw, EventDate):
        return raw
    if isinstance(raw, (dict, str)):
        return EventDate.from_dict(raw)
    raise ModelFormatError(f"Invalid '{field_name}' payload: expected EventDate, dict, or str.")


def _deserialize_age(raw: Any, field_name: str) -> Age:
    """Coerce an Age instance, dictionary, integer years, or raw text string."""
    if isinstance(raw, Age):
        return raw
    if isinstance(raw, dict):
        return Age(
            raw_text=raw.get("raw_text"),
            years=raw.get("years"),
            months=raw.get("months"),
            days=raw.get("days"),
        )
    if isinstance(raw, int) and not isinstance(raw, bool):
        return Age(years=raw)
    if isinstance(raw, str):
        return Age(raw_text=raw)
    raise ModelFormatError(f"Invalid '{field_name}' payload: expected Age, dict, int, or str.")


def _serialize_age(age: Age) -> dict[str, Any]:
    """Serialize an Age value object to a dictionary."""
    data: dict[str, Any] = {}
    if age.raw_text is not None:
        data["raw_text"] = age.raw_text
    if age.years is not None:
        data["years"] = age.years
    if age.months is not None:
        data["months"] = age.months
    if age.days is not None:
        data["days"] = age.days
    return data


def _parse_marker_enum[E](enum_cls: type[E], raw: Any, field_name: str) -> E:
    """Resolve a site marker enum by enum instance, exact value, or uppercase member name."""
    if isinstance(raw, enum_cls):
        return raw
    token = str(raw).strip()
    for member in enum_cls:  # type: ignore[attr-defined]
        if token.upper() in (member.name, member.value.upper()):
            return member  # type: ignore[no-any-return]
    raise ModelFormatError(f"Invalid {field_name} value: '{raw}'.")


@dataclass(repr=False, config=ConfigDict(kw_only=True, frozen=True, extra="forbid", strict=True))
class MarkerInterment(IntrospectableMixin):
    """Single person inscription engraved on a cemetery headstone, monument, or crypt."""

    inscribed_name: str = Field(
        ...,
        description="Verbatim or standardized full name carved on the marker.",
    )
    individual_id: IndividualID | None = Field(
        default=None,
        description="Resolved canonical IndividualID if linked to a person entity.",
    )
    birth_date: EventDate | None = Field(
        default=None,
        description="Birth date inscribed or calculated on the marker.",
    )
    death_date: EventDate | None = Field(
        default=None,
        description="Death date inscribed on the marker.",
    )
    age_at_death: Age | None = Field(
        default=None,
        description="Structured age at death inscribed on the marker.",
    )
    relationship_inscribed: str | None = Field(
        default=None,
        description="Verbatim kinship phrase carved on the stone (e.g., 'Wife of John H. Abbott').",
    )

    def __post_init__(self) -> None:
        """Enforce non-empty inscribed_name hygiene."""
        cleaned = self.inscribed_name.strip()
        if not cleaned:
            raise ModelFormatError(
                "MarkerInterment 'inscribed_name' cannot be empty or whitespace."
            )
        if cleaned != self.inscribed_name:
            object.__setattr__(self, "inscribed_name", cleaned)

    @classmethod
    def create(
        cls,
        inscribed_name: str,
        individual_id: IndividualID | str | None = None,
        birth_date: EventDate | dict[str, Any] | str | None = None,
        death_date: EventDate | dict[str, Any] | str | None = None,
        age_at_death: Age | dict[str, Any] | int | str | None = None,
        relationship_inscribed: str | None = None,
    ) -> MarkerInterment:
        """Factory constructor instantiating a validated MarkerInterment."""
        res_ind = (
            individual_id
            if (individual_id is None or isinstance(individual_id, IndividualID))
            else IndividualID(individual_id)
        )
        res_birth = (
            _deserialize_event_date(birth_date, "birth_date") if birth_date is not None else None
        )
        res_death = (
            _deserialize_event_date(death_date, "death_date") if death_date is not None else None
        )
        res_age = (
            _deserialize_age(age_at_death, "age_at_death") if age_at_death is not None else None
        )
        return cls(
            inscribed_name=inscribed_name,
            individual_id=res_ind,
            birth_date=res_birth,
            death_date=res_death,
            age_at_death=res_age,
            relationship_inscribed=relationship_inscribed,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize MarkerInterment to a dictionary."""
        data: dict[str, Any] = {
            "inscribed_name": self.inscribed_name,
        }
        if self.individual_id is not None:
            data["individual_id"] = str(self.individual_id)
        if self.birth_date is not None:
            data["birth_date"] = self.birth_date.to_dict()
        if self.death_date is not None:
            data["death_date"] = self.death_date.to_dict()
        if self.age_at_death is not None:
            data["age_at_death"] = _serialize_age(self.age_at_death)
        if self.relationship_inscribed is not None:
            data["relationship_inscribed"] = self.relationship_inscribed
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MarkerInterment:
        """Deserialize a dictionary payload into a MarkerInterment."""
        if not isinstance(data, dict):
            raise ModelFormatError("MarkerInterment payload must be a dictionary.")
        name = data.get("inscribed_name")
        if name is None:
            raise ModelFormatError("MarkerInterment requires 'inscribed_name'.")
        return cls.create(
            inscribed_name=str(name),
            individual_id=data.get("individual_id"),
            birth_date=data.get("birth_date"),
            death_date=data.get("death_date"),
            age_at_death=data.get("age_at_death"),
            relationship_inscribed=data.get("relationship_inscribed"),
        )

    def to_json(self) -> str:
        """Serialize MarkerInterment to a JSON formatted string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_json(cls, payload: str) -> MarkerInterment:
        """Deserialize a JSON string directly into a MarkerInterment."""
        try:
            data = json.loads(payload)
        except Exception as exc:
            raise ModelFormatError(f"Failed to parse MarkerInterment JSON string: {exc}") from exc
        return cls.from_dict(data)

    def __str__(self) -> str:
        return self.inscribed_name


@dataclass(repr=False, config=ConfigDict(kw_only=True, frozen=True, extra="forbid", strict=True))
class CemeteryMarkerRecord(SourceRecord):
    """Primary epigraphic record documenting a cemetery marker, monument, or crypt."""

    record_category: SourceRecordCategory = Field(
        default=SourceRecordCategory.CEMETERY,
        description="High-level archival domain category (restricted to CEMETERY).",
    )
    record_type: SourceRecordType = Field(
        default=SourceRecordType.CEMETERY_MARKER,
        description="Specific cemetery marker classification.",
    )
    cemetery_name_raw: str = Field(
        ...,
        description="Verbatim name of the cemetery, churchyard, or burial ground.",
    )
    interments: tuple[MarkerInterment, ...] = Field(
        ...,
        description="Ordered tuple of one or more inscribed persons commemorated on the marker.",
    )
    cemetery_site_id: SiteID | None = Field(
        default=None,
        description="Resolved canonical SiteID of the physical cemetery venue.",
    )
    location_id: LocationID | None = Field(
        default=None,
        description="Resolved canonical LocationID for the cemetery's civil jurisdiction.",
    )
    plot_location: str | None = Field(
        default=None,
        description="Section, lot, range, or grave coordinate within the cemetery.",
    )
    findagrave_id: str | None = Field(
        default=None,
        description="External Find A Grave memorial identifier if cross-referenced.",
    )
    billiongraves_id: str | None = Field(
        default=None,
        description="External BillionGraves headstone identifier if cross-referenced.",
    )
    cemetery_grave_id: str | None = Field(
        default=None,
        description="Official sexton or cemetery office grave/lot number.",
    )
    marker_type: MarkerType | None = Field(
        default=None,
        description="Physical typology of the monument (Upright Headstone, Obelisk, Ledger, etc.).",
    )
    material: MarkerMaterial | None = Field(
        default=None,
        description="Stone or metal material composition (Granite, Marble, Slate, etc.).",
    )
    carver: str | None = Field(
        default=None,
        description="Monument maker or stonecarver signature if present.",
    )
    physical_condition: MarkerCondition | None = Field(
        default=None,
        description="Current preservation state of the stone (Sound, Weathered, Sunken, etc.).",
    )
    inscription_verbatim: str | None = Field(
        default=None,
        description="Full verbatim transcription of epitaph, verses, and front/back faces.",
    )
    survey_date: EventDate | None = Field(
        default=None,
        description="Date the marker was photographed or transcribed in the field.",
    )

    ALLOWED_RECORD_TYPES: ClassVar[frozenset[SourceRecordType]] = _MARKER_RECORD_TYPES

    def __post_init__(self) -> None:
        """Enforce category, record_type, cemetery name, and non-empty interments."""
        super().__post_init__()

        if self.record_category is not SourceRecordCategory.CEMETERY:
            raise ModelFormatError(
                f"{self.__class__.__name__} requires record_category CEMETERY, "
                f"got '{self.record_category.value}'."
            )

        if self.record_type not in self.ALLOWED_RECORD_TYPES:
            raise ModelFormatError(
                f"{self.__class__.__name__} requires record_type in "
                f"{sorted(t.value for t in self.ALLOWED_RECORD_TYPES)}, "
                f"got '{self.record_type.value}'."
            )

        clean_cem = self.cemetery_name_raw.strip()
        if not clean_cem:
            raise ModelFormatError(
                f"{self.__class__.__name__} 'cemetery_name_raw' cannot be empty or whitespace."
            )
        if clean_cem != self.cemetery_name_raw:
            object.__setattr__(self, "cemetery_name_raw", clean_cem)

        if not self.interments:
            raise ModelFormatError(
                f"{self.__class__.__name__} requires at least one MarkerInterment."
            )

    @property
    def interment_count(self) -> int:
        """Return the number of persons inscribed on this marker."""
        return len(self.interments)

    def flatten_interments(self) -> tuple[dict[str, Any], ...]:
        """Flatten marker context with each inscribed interment for collection-wide indexing."""
        header: dict[str, Any] = {
            "source_id": str(self.source_id),
            "source_urn": str(self.source_urn),
            "record_category": self.record_category.value,
            "record_type": self.record_type.value,
            "cemetery_name_raw": self.cemetery_name_raw,
            "cemetery_site_id": str(self.cemetery_site_id) if self.cemetery_site_id else None,
            "location_id": str(self.location_id) if self.location_id else None,
            "plot_location": self.plot_location,
            "marker_type": self.marker_type.value if self.marker_type else None,
        }
        return tuple({**header, **item.to_dict()} for item in self.interments)

    @classmethod
    def create(  # type: ignore[override]
        cls,
        source_id: SourceID | str,
        source_urn: ArchivalURN | str,
        description: str,
        repository_id: RepositoryID | str,
        cemetery_name_raw: str,
        interments: list[MarkerInterment | dict[str, Any]] | tuple[MarkerInterment, ...],
        record_type: SourceRecordType | str = SourceRecordType.CEMETERY_MARKER,
        cemetery_site_id: SiteID | str | None = None,
        location_id: LocationID | str | None = None,
        plot_location: str | None = None,
        findagrave_id: str | None = None,
        billiongraves_id: str | None = None,
        cemetery_grave_id: str | None = None,
        marker_type: MarkerType | str | None = None,
        material: MarkerMaterial | str | None = None,
        carver: str | None = None,
        physical_condition: MarkerCondition | str | None = None,
        inscription_verbatim: str | None = None,
        survey_date: EventDate | dict[str, Any] | str | None = None,
        audit: AuditStamp | None = None,
        media_ids: list[MediaID | str] | None = None,
        associated_people: list[AssociatedIndividual] | None = None,
        tombstone: Tombstone[SourceID] | None = None,
    ) -> CemeteryMarkerRecord:
        """Factory constructor instantiating a validated CemeteryMarkerRecord."""
        resolved_sid = source_id if isinstance(source_id, SourceID) else SourceID(source_id)
        resolved_urn = _resolve_cemetery_urn(source_urn)
        resolved_rep = (
            repository_id
            if isinstance(repository_id, RepositoryID)
            else RepositoryID(repository_id)
        )
        res_type = (
            record_type
            if isinstance(record_type, SourceRecordType)
            else SourceRecordType(str(record_type).strip().upper())
        )
        res_site = (
            cemetery_site_id
            if (cemetery_site_id is None or isinstance(cemetery_site_id, SiteID))
            else SiteID(cemetery_site_id)
        )
        res_loc = (
            location_id
            if (location_id is None or isinstance(location_id, LocationID))
            else LocationID(location_id)
        )
        res_mtype = (
            _parse_marker_enum(MarkerType, marker_type, "marker_type")
            if marker_type is not None
            else None
        )
        res_mat = (
            _parse_marker_enum(MarkerMaterial, material, "material")
            if material is not None
            else None
        )
        res_cond = (
            _parse_marker_enum(MarkerCondition, physical_condition, "physical_condition")
            if physical_condition is not None
            else None
        )
        res_survey = (
            _deserialize_event_date(survey_date, "survey_date") if survey_date is not None else None
        )

        resolved_interments: tuple[MarkerInterment, ...] = tuple(
            i if isinstance(i, MarkerInterment) else MarkerInterment.from_dict(i)
            for i in interments
        )

        resolved_audit = audit if audit is not None else AuditStamp.now()
        resolved_media = [m if isinstance(m, MediaID) else MediaID(m) for m in (media_ids or [])]

        return cls(
            source_id=resolved_sid,
            source_urn=resolved_urn,
            record_category=SourceRecordCategory.CEMETERY,
            record_type=res_type,
            description=description.strip() if isinstance(description, str) else description,
            repository_id=resolved_rep,
            audit=resolved_audit,
            media_ids=resolved_media,
            associated_people=associated_people or [],
            tombstone=tombstone,
            cemetery_name_raw=cemetery_name_raw,
            interments=resolved_interments,
            cemetery_site_id=res_site,
            location_id=res_loc,
            plot_location=plot_location,
            findagrave_id=findagrave_id,
            billiongraves_id=billiongraves_id,
            cemetery_grave_id=cemetery_grave_id,
            marker_type=res_mtype,
            material=res_mat,
            carver=carver,
            physical_condition=res_cond,
            inscription_verbatim=inscription_verbatim,
            survey_date=res_survey,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize CemeteryMarkerRecord to a dictionary."""
        data = super().to_dict()
        data.update(
            {
                "record_type": self.record_type.value,
                "cemetery_name_raw": self.cemetery_name_raw,
                "interments": [i.to_dict() for i in self.interments],
            }
        )
        if self.cemetery_site_id is not None:
            data["cemetery_site_id"] = str(self.cemetery_site_id)
        if self.location_id is not None:
            data["location_id"] = str(self.location_id)
        if self.plot_location is not None:
            data["plot_location"] = self.plot_location
        if self.findagrave_id is not None:
            data["findagrave_id"] = self.findagrave_id
        if self.billiongraves_id is not None:
            data["billiongraves_id"] = self.billiongraves_id
        if self.cemetery_grave_id is not None:
            data["cemetery_grave_id"] = self.cemetery_grave_id
        if self.marker_type is not None:
            data["marker_type"] = self.marker_type.value
        if self.material is not None:
            data["material"] = self.material.value
        if self.carver is not None:
            data["carver"] = self.carver
        if self.physical_condition is not None:
            data["physical_condition"] = self.physical_condition.value
        if self.inscription_verbatim is not None:
            data["inscription_verbatim"] = self.inscription_verbatim
        if self.survey_date is not None:
            data["survey_date"] = self.survey_date.to_dict()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CemeteryMarkerRecord:
        """Deserialize a dictionary payload into a CemeteryMarkerRecord."""
        if not isinstance(data, dict):
            raise ModelFormatError("CemeteryMarkerRecord payload must be a dictionary.")

        sid = data.get("source_id")
        raw_urn = data.get("source_urn")
        desc = data.get("description")
        rep = data.get("repository_id")
        audit_payload = data.get("audit")
        cem_name = data.get("cemetery_name_raw")
        raw_interments = data.get("interments")

        if not all((sid, raw_urn, desc, rep, audit_payload, cem_name, raw_interments)):
            raise ModelFormatError(
                "CemeteryMarkerRecord requires source_id, source_urn, description, repository_id, "
                "audit, cemetery_name_raw, and interments."
            )

        raw_cat = data.get("record_category", SourceRecordCategory.CEMETERY.value)
        if str(raw_cat).strip().upper() != SourceRecordCategory.CEMETERY.value:
            raise ModelFormatError(
                f"CemeteryMarkerRecord requires record_category CEMETERY, got '{raw_cat}'."
            )

        if not isinstance(raw_interments, (list, tuple)):
            raise ModelFormatError("CemeteryMarkerRecord 'interments' must be a list or tuple.")

        if isinstance(audit_payload, AuditStamp):
            audit_obj = audit_payload
        elif isinstance(audit_payload, dict):
            audit_obj = AuditStamp(
                created_at=IsoTimestamp(audit_payload["created_at"]),
                updated_at=IsoTimestamp(audit_payload["updated_at"]),
            )
        else:
            raise ModelFormatError(
                "CemeteryMarkerRecord audit must be an AuditStamp or dictionary."
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
            cemetery_name_raw=str(cem_name),
            interments=list(raw_interments),
            record_type=data.get("record_type", SourceRecordType.CEMETERY_MARKER),
            cemetery_site_id=data.get("cemetery_site_id"),
            location_id=data.get("location_id"),
            plot_location=data.get("plot_location"),
            findagrave_id=data.get("findagrave_id"),
            billiongraves_id=data.get("billiongraves_id"),
            cemetery_grave_id=data.get("cemetery_grave_id"),
            marker_type=data.get("marker_type"),
            material=data.get("material"),
            carver=data.get("carver"),
            physical_condition=data.get("physical_condition"),
            inscription_verbatim=data.get("inscription_verbatim"),
            survey_date=data.get("survey_date"),
            audit=audit_obj,
            media_ids=data.get("media_ids", []),
            associated_people=[
                AssociatedIndividual.from_dict(p) for p in data.get("associated_people", [])
            ],
            tombstone=tombstone_obj,
        )

    def __str__(self) -> str:
        primary = self.interments[0].inscribed_name
        extra = f" (+{len(self.interments) - 1})" if len(self.interments) > 1 else ""
        return f"CemeteryMarkerRecord [{primary}{extra}] @ {self.cemetery_name_raw}"
