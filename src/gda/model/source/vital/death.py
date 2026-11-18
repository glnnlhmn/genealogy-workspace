"""Path: src/gda/model/source/vital/death.py

Civil death certificate, coroner inquest, transit permit, and death register models.

Operational Role:
    Defines DeathRecord extending SourceRecord to capture primary documentary
    evidence from civil death certificates, fetal death certificates, coroner
    inquests, burial/transit permits, delayed death records, and town/civil
    death register entries (aligned with schemas/sources/death_certificate.schema.json).
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any, ClassVar, cast

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.enums.core import Sex
from gda.core.enums.sources import SourceRecordCategory, SourceRecordType
from gda.core.enums.vital import DispositionType, MannerOfDeath, MaritalStatus
from gda.core.errors import ModelFormatError
from gda.model.atom.id import IndividualID, LocationID, MediaID, RepositoryID, SiteID, SourceID
from gda.model.atom.urn import ArchivalURN, SourceURN, VitalCertificateUrn
from gda.model.base.age import Age
from gda.model.base.association import AssociatedIndividual
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate
from gda.model.base.source import SourceRecord
from gda.model.base.tombstone import Tombstone
from gda.util.enums import coerce_enum

__version__ = "1.0.0+build.5"

__all__ = [
    "DeathRecord",
]

_DEATH_RECORD_TYPES: frozenset[SourceRecordType] = frozenset(
    {
        SourceRecordType.DEATH_CERTIFICATE,
        SourceRecordType.FETAL_DEATH,
        SourceRecordType.CORONER_INQUEST,
        SourceRecordType.TRANSIT_PERMIT,
        SourceRecordType.REGISTER_ENTRY,
        SourceRecordType.DELAYED_DEATH,
    }
)


# ==============================================================================
# 1. COERCION & NORMALIZATION HELPERS
# ==============================================================================


def _resolve_vital_urn(raw: ArchivalURN | str) -> ArchivalURN:
    """Coerce a raw URN string into VitalCertificateUrn or SourceURN."""
    if isinstance(raw, ArchivalURN):
        return raw
    token = str(raw).strip()
    if token.startswith("URN:VITAL:"):
        return VitalCertificateUrn(token)
    return SourceURN(token)


def _deserialize_event_date(raw: Any, field_name: str) -> EventDate:
    """Coerce an EventDate instance, dictionary, or compact date string."""
    if isinstance(raw, EventDate):
        return raw
    if isinstance(raw, (dict, str)):
        return EventDate.from_dict(raw)
    raise ModelFormatError(f"Invalid '{field_name}' payload: expected EventDate, dict, or str.")


def _opt_event_date(raw: Any, field_name: str) -> EventDate | None:
    """Coerce an optional EventDate input or return None when absent."""
    return _deserialize_event_date(raw, field_name) if raw is not None else None


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


def _opt_age(raw: Any, field_name: str) -> Age | None:
    """Coerce an optional Age input or return None when absent."""
    return _deserialize_age(raw, field_name) if raw is not None else None


def _coerce_id[TID](val: TID | str, id_cls: type[TID]) -> TID:
    """Coerce a required typed ID or string token into id_cls."""
    return val if isinstance(val, id_cls) else id_cls(val)  # type: ignore[call-arg]


def _opt_id[TID](val: TID | str | None, id_cls: type[TID]) -> TID | None:
    """Coerce an optional typed ID or string token into id_cls, or return None."""
    if val is None:
        return None
    return val if isinstance(val, id_cls) else id_cls(val)  # type: ignore[call-arg]


def _opt_enum[E](enum_cls: type[E], raw: Any, field_name: str) -> E | None:
    """Coerce an optional StrEnum value or return None when absent."""
    if raw is None:
        return None
    return coerce_enum(enum_cls, raw, field_name=field_name)  # type: ignore[type-var]


def _coerce_media_list(media_ids: Iterable[MediaID | str] | None) -> list[MediaID]:
    """Hydrate an optional sequence of MediaID instances or strings into a list."""
    if not media_ids:
        return []
    return [m if isinstance(m, MediaID) else MediaID(m) for m in media_ids]


# ==============================================================================
# 2. DEATH RECORD DOMAIN MODEL
# ==============================================================================


@dataclass(
    repr=False,
    config=ConfigDict(frozen=True, extra="forbid", strict=True),
    kw_only=True,
)
class DeathRecord(SourceRecord):
    """Primary archival record documenting a death, coroner inquest, or transit permit."""

    record_category: SourceRecordCategory = Field(
        default=SourceRecordCategory.VITAL,
        description="High-level archival domain category (restricted to VITAL).",
    )
    record_type: SourceRecordType = Field(
        default=SourceRecordType.DEATH_CERTIFICATE,
        description="Specific death documentary record classification.",
    )
    decedent_name_raw: str = Field(
        ...,
        description="Verbatim full name of the decedent as inscribed on the death record.",
    )
    date_of_death: EventDate = Field(
        ...,
        description="Recorded date of death assertion.",
    )
    place_of_death_raw: str = Field(
        ...,
        description="Verbatim place of death (town, county, state, or hospital).",
    )
    decedent_id: IndividualID | None = Field(
        default=None,
        description="Resolved canonical IndividualID of the decedent if linked.",
    )
    sex: Sex = Field(
        default=Sex.UNKNOWN,
        description="Recorded biological sex of the decedent.",
    )
    is_stillborn: bool = Field(
        default=False,
        description="True if the record documents a fetal death or stillbirth.",
    )
    marital_status: MaritalStatus | None = Field(
        default=None,
        description="Marital status of the decedent at death.",
    )
    spouse_name_raw: str | None = Field(
        default=None,
        description="Verbatim surviving or deceased spouse name recorded on the certificate.",
    )
    date_of_birth: EventDate | None = Field(
        default=None,
        description="Date of birth stated on the death certificate.",
    )
    age_at_death: Age | None = Field(
        default=None,
        description="Structured age at death (years, months, days, or raw text).",
    )
    time_of_death: str | None = Field(
        default=None,
        description="Verbatim hour/minute of death if recorded.",
    )
    place_of_death_id: LocationID | None = Field(
        default=None,
        description="Resolved canonical LocationID for the place of death.",
    )
    residence_raw: str | None = Field(
        default=None,
        description="Verbatim usual residence of the decedent.",
    )
    occupation_raw: str | None = Field(
        default=None,
        description="Verbatim usual occupation or trade of the decedent.",
    )
    father_name_raw: str | None = Field(
        default=None,
        description="Verbatim father's name recorded on the death certificate.",
    )
    mother_maiden_name_raw: str | None = Field(
        default=None,
        description="Verbatim mother's maiden name recorded on the death certificate.",
    )
    manner_of_death: MannerOfDeath | None = Field(
        default=None,
        description="Categorical manner of death (Natural, Accident, Suicide, Homicide, etc.).",
    )
    cause_of_death_raw: str | None = Field(
        default=None,
        description="Verbatim primary and contributory medical cause of death.",
    )
    attending_physician_raw: str | None = Field(
        default=None,
        description="Verbatim attending physician, coroner, or medical examiner name.",
    )
    informant_name_raw: str | None = Field(
        default=None,
        description="Verbatim informant name recorded on the death return.",
    )
    disposition_type: DispositionType | None = Field(
        default=None,
        description="Manner of mortal disposition (Burial, Cremation, Removal, Entombment, etc.).",
    )
    disposition_date: EventDate | None = Field(
        default=None,
        description="Date of burial, cremation, or removal.",
    )
    disposition_place_raw: str | None = Field(
        default=None,
        description="Verbatim cemetery, crematory, or destination name.",
    )
    disposition_site_id: SiteID | None = Field(
        default=None,
        description="Resolved canonical SiteID of the cemetery or disposition venue.",
    )
    undertaker_raw: str | None = Field(
        default=None,
        description="Verbatim funeral director or undertaker name.",
    )
    certificate_number: str | None = Field(
        default=None,
        description="Official state, county, or local death file number.",
    )
    date_filed: EventDate | None = Field(
        default=None,
        description="Date the death certificate or transit permit was filed.",
    )

    ALLOWED_RECORD_TYPES: ClassVar[frozenset[SourceRecordType]] = _DEATH_RECORD_TYPES

    def __post_init__(self) -> None:
        """Enforce category, record_type, and non-empty string boundaries."""
        super().__post_init__()

        if self.record_category is not SourceRecordCategory.VITAL:
            raise ModelFormatError(
                f"{self.__class__.__name__} requires record_category VITAL, "
                f"got '{self.record_category.value}'."
            )

        if self.record_type not in self.ALLOWED_RECORD_TYPES:
            raise ModelFormatError(
                f"{self.__class__.__name__} requires record_type in "
                f"{sorted(t.value for t in self.ALLOWED_RECORD_TYPES)}, "
                f"got '{self.record_type.value}'."
            )

        for field_name in ("decedent_name_raw", "place_of_death_raw"):
            raw_val = getattr(self, field_name)
            cleaned = raw_val.strip()
            if not cleaned:
                raise ModelFormatError(
                    f"{self.__class__.__name__} '{field_name}' cannot be empty or whitespace."
                )
            if cleaned != raw_val:
                object.__setattr__(self, field_name, cleaned)

    @classmethod
    def create(  # type: ignore[override]
        cls,
        source_id: SourceID | str,
        source_urn: ArchivalURN | str,
        description: str,
        repository_id: RepositoryID | str,
        decedent_name_raw: str,
        date_of_death: EventDate | dict[str, Any] | str,
        place_of_death_raw: str,
        record_type: SourceRecordType | str = SourceRecordType.DEATH_CERTIFICATE,
        decedent_id: IndividualID | str | None = None,
        sex: Sex | str = Sex.UNKNOWN,
        is_stillborn: bool = False,
        marital_status: MaritalStatus | str | None = None,
        spouse_name_raw: str | None = None,
        date_of_birth: EventDate | dict[str, Any] | str | None = None,
        age_at_death: Age | dict[str, Any] | int | str | None = None,
        time_of_death: str | None = None,
        place_of_death_id: LocationID | str | None = None,
        residence_raw: str | None = None,
        occupation_raw: str | None = None,
        father_name_raw: str | None = None,
        mother_maiden_name_raw: str | None = None,
        manner_of_death: MannerOfDeath | str | None = None,
        cause_of_death_raw: str | None = None,
        attending_physician_raw: str | None = None,
        informant_name_raw: str | None = None,
        disposition_type: DispositionType | str | None = None,
        disposition_date: EventDate | dict[str, Any] | str | None = None,
        disposition_place_raw: str | None = None,
        disposition_site_id: SiteID | str | None = None,
        undertaker_raw: str | None = None,
        certificate_number: str | None = None,
        date_filed: EventDate | dict[str, Any] | str | None = None,
        audit: AuditStamp | None = None,
        media_ids: list[MediaID | str] | None = None,
        associated_people: list[AssociatedIndividual] | None = None,
        tombstone: Tombstone[SourceID] | None = None,
    ) -> DeathRecord:
        """Factory constructor instantiating a validated DeathRecord."""
        res_sex = sex if isinstance(sex, Sex) else Sex.from_input(str(sex))
        return cls(
            source_id=_coerce_id(source_id, SourceID),
            source_urn=_resolve_vital_urn(source_urn),
            record_category=SourceRecordCategory.VITAL,
            record_type=coerce_enum(SourceRecordType, record_type, field_name="record_type"),
            description=description.strip() if isinstance(description, str) else description,
            repository_id=_coerce_id(repository_id, RepositoryID),
            audit=audit or AuditStamp.now(),
            media_ids=_coerce_media_list(media_ids),
            associated_people=associated_people or [],
            tombstone=tombstone,
            decedent_name_raw=decedent_name_raw,
            date_of_death=_deserialize_event_date(date_of_death, "date_of_death"),
            place_of_death_raw=place_of_death_raw,
            decedent_id=_opt_id(decedent_id, IndividualID),
            sex=res_sex,
            is_stillborn=is_stillborn,
            marital_status=_opt_enum(MaritalStatus, marital_status, "marital_status"),
            spouse_name_raw=spouse_name_raw,
            date_of_birth=_opt_event_date(date_of_birth, "date_of_birth"),
            age_at_death=_opt_age(age_at_death, "age_at_death"),
            time_of_death=time_of_death,
            place_of_death_id=_opt_id(place_of_death_id, LocationID),
            residence_raw=residence_raw,
            occupation_raw=occupation_raw,
            father_name_raw=father_name_raw,
            mother_maiden_name_raw=mother_maiden_name_raw,
            manner_of_death=_opt_enum(MannerOfDeath, manner_of_death, "manner_of_death"),
            cause_of_death_raw=cause_of_death_raw,
            attending_physician_raw=attending_physician_raw,
            informant_name_raw=informant_name_raw,
            disposition_type=_opt_enum(DispositionType, disposition_type, "disposition_type"),
            disposition_date=_opt_event_date(disposition_date, "disposition_date"),
            disposition_place_raw=disposition_place_raw,
            disposition_site_id=_opt_id(disposition_site_id, SiteID),
            undertaker_raw=undertaker_raw,
            certificate_number=certificate_number,
            date_filed=_opt_event_date(date_filed, "date_filed"),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize DeathRecord to a dictionary."""
        return super().to_dict()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DeathRecord:
        """Deserialize a dictionary payload into a DeathRecord."""
        if not isinstance(data, dict):
            raise ModelFormatError("DeathRecord payload must be a dictionary.")

        sid = data.get("source_id")
        raw_urn = data.get("source_urn")
        desc = data.get("description")
        rep = data.get("repository_id")
        audit_payload = data.get("audit")
        decedent_name = data.get("decedent_name_raw")
        raw_dod = data.get("date_of_death")
        place_raw = data.get("place_of_death_raw")

        if not all((sid, raw_urn, desc, rep, audit_payload, decedent_name, raw_dod, place_raw)):
            raise ModelFormatError(
                "DeathRecord requires source_id, source_urn, description, repository_id, "
                "audit, decedent_name_raw, date_of_death, and place_of_death_raw."
            )

        raw_cat = data.get("record_category", SourceRecordCategory.VITAL.value)
        if str(raw_cat).strip().upper() != SourceRecordCategory.VITAL.value:
            raise ModelFormatError(f"DeathRecord requires record_category VITAL, got '{raw_cat}'.")

        if not isinstance(audit_payload, (AuditStamp, dict)):
            raise ModelFormatError("DeathRecord audit must be an AuditStamp or dictionary.")
        audit_obj = AuditStamp.from_dict(audit_payload)

        tombstone_payload = data.get("tombstone")
        tombstone_obj = (
            Tombstone.from_dict(tombstone_payload, id_cls=SourceID)
            if isinstance(tombstone_payload, dict)
            else None
        )

        return cls.create(
            source_id=str(sid),
            source_urn=str(raw_urn),
            description=str(desc),
            repository_id=str(rep),
            decedent_name_raw=str(decedent_name),
            date_of_death=cast(Any, raw_dod),
            place_of_death_raw=str(place_raw),
            record_type=data.get("record_type", SourceRecordType.DEATH_CERTIFICATE),
            decedent_id=data.get("decedent_id"),
            sex=data.get("sex", Sex.UNKNOWN),
            is_stillborn=bool(data.get("is_stillborn", False)),
            marital_status=data.get("marital_status"),
            spouse_name_raw=data.get("spouse_name_raw"),
            date_of_birth=data.get("date_of_birth"),
            age_at_death=data.get("age_at_death"),
            time_of_death=data.get("time_of_death"),
            place_of_death_id=data.get("place_of_death_id"),
            residence_raw=data.get("residence_raw"),
            occupation_raw=data.get("occupation_raw"),
            father_name_raw=data.get("father_name_raw"),
            mother_maiden_name_raw=data.get("mother_maiden_name_raw"),
            manner_of_death=data.get("manner_of_death"),
            cause_of_death_raw=data.get("cause_of_death_raw"),
            attending_physician_raw=data.get("attending_physician_raw"),
            informant_name_raw=data.get("informant_name_raw"),
            disposition_type=data.get("disposition_type"),
            disposition_date=data.get("disposition_date"),
            disposition_place_raw=data.get("disposition_place_raw"),
            disposition_site_id=data.get("disposition_site_id"),
            undertaker_raw=data.get("undertaker_raw"),
            certificate_number=data.get("certificate_number"),
            date_filed=data.get("date_filed"),
            audit=audit_obj,
            media_ids=data.get("media_ids", []),
            associated_people=[
                AssociatedIndividual.from_dict(p) for p in data.get("associated_people", [])
            ],
            tombstone=tombstone_obj,
        )

    def __str__(self) -> str:
        return f"DeathRecord [{self.decedent_name_raw}] ({self.date_of_death})"
