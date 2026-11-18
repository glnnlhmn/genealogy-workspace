"""Path: src/gda/model/source/vital/baptism.py

Ecclesiastical baptismal, christening, and cradle roll record models.

Operational Role:
    Defines BaptismRecord extending SourceRecord to capture primary documentary
    evidence from church baptismal registers, baptismal certificates, christening
    entries, and cradle rolls (aligned with schemas/sources/church_baptism.schema.json).
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any, ClassVar, cast

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.enums.core import Sex
from gda.core.enums.sources import SourceRecordCategory, SourceRecordType
from gda.core.errors import ModelFormatError
from gda.model.atom.id import (
    IndividualID,
    LocationID,
    MediaID,
    OrganizationID,
    RepositoryID,
    SiteID,
    SourceID,
)
from gda.model.atom.urn import ArchivalURN, SourceURN
from gda.model.base.association import AssociatedIndividual
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate
from gda.model.base.source import SourceRecord
from gda.model.base.tombstone import Tombstone
from gda.util.enums import coerce_enum

__version__ = "1.0.0+build.4"

__all__ = [
    "BaptismRecord",
]

_BAPTISM_CATEGORIES: frozenset[SourceRecordCategory] = frozenset(
    {
        SourceRecordCategory.CHURCH,
        SourceRecordCategory.VITAL,
    }
)

_BAPTISM_RECORD_TYPES: frozenset[SourceRecordType] = frozenset(
    {
        SourceRecordType.BAPTISM_REGISTER,
        SourceRecordType.BAPTISM_CERTIFICATE,
        SourceRecordType.CHRISTENING_ENTRY,
        SourceRecordType.CRADLE_ROLL,
    }
)


# ==============================================================================
# 1. COERCION & NORMALIZATION HELPERS
# ==============================================================================


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


def _coerce_id[TID](val: TID | str, id_cls: type[TID]) -> TID:
    """Coerce a required typed ID or string token into id_cls."""
    return val if isinstance(val, id_cls) else id_cls(val)  # type: ignore[call-arg]


def _opt_id[TID](val: TID | str | None, id_cls: type[TID]) -> TID | None:
    """Coerce an optional typed ID or string token into id_cls, or return None."""
    if val is None:
        return None
    return val if isinstance(val, id_cls) else id_cls(val)  # type: ignore[call-arg]


def _opt_sex(sex: Sex | str | None) -> Sex | None:
    """Resolve optional Sex enum or raw token."""
    if sex is None or isinstance(sex, Sex):
        return sex
    return Sex.from_input(str(sex))


def _coerce_media_list(media_ids: Iterable[MediaID | str] | None) -> list[MediaID]:
    """Hydrate an optional sequence of MediaID instances or strings into a list."""
    if not media_ids:
        return []
    return [m if isinstance(m, MediaID) else MediaID(m) for m in media_ids]


# ==============================================================================
# 2. BAPTISM RECORD DOMAIN MODEL
# ==============================================================================


@dataclass(
    repr=False,
    config=ConfigDict(frozen=True, extra="forbid", strict=True),
    kw_only=True,
)
class BaptismRecord(SourceRecord):
    """Primary archival record documenting an ecclesiastical baptism, christening, or dedication."""

    record_category: SourceRecordCategory = Field(
        default=SourceRecordCategory.CHURCH,
        description="High-level archival domain category (CHURCH or VITAL).",
    )
    record_type: SourceRecordType = Field(
        default=SourceRecordType.BAPTISM_REGISTER,
        description="Specific baptismal documentary record classification.",
    )
    church_name_raw: str = Field(
        ...,
        description="Verbatim name of the church, parish, or congregation.",
    )
    baptized_name_raw: str = Field(
        ...,
        description="Verbatim full name of the baptized or christened individual.",
    )
    date_of_baptism: EventDate = Field(
        ...,
        description="Recorded date of baptism or christening ceremony.",
    )
    church_org_id: OrganizationID | None = Field(
        default=None,
        description="Resolved canonical OrganizationID of the congregation if linked.",
    )
    church_site_id: SiteID | None = Field(
        default=None,
        description="Resolved canonical SiteID of the church building if linked.",
    )
    location_id: LocationID | None = Field(
        default=None,
        description="Resolved canonical LocationID of the parish jurisdiction.",
    )
    denomination: str | None = Field(
        default=None,
        description="Religious denomination or tradition (e.g., 'Congregational', 'Roman Catholic').",
    )
    volume_title: str | None = Field(
        default=None,
        description="Title or designation of the parish register book.",
    )
    register_locator: str | None = Field(
        default=None,
        description="Page, folio, or entry number inside the parish register.",
    )
    individual_id: IndividualID | None = Field(
        default=None,
        description="Resolved canonical IndividualID of the baptized person if linked.",
    )
    sex: Sex | None = Field(
        default=None,
        description="Recorded biological sex if noted in the baptismal register.",
    )
    date_of_birth: EventDate | None = Field(
        default=None,
        description="Date of birth stated in the baptismal entry.",
    )
    place_of_birth_raw: str | None = Field(
        default=None,
        description="Verbatim birthplace or parental residence recorded in the register.",
    )
    officiant_name_raw: str | None = Field(
        default=None,
        description="Verbatim name and title of the officiating clergy member.",
    )
    father_name_raw: str | None = Field(
        default=None,
        description="Verbatim father's name recorded in the register.",
    )
    mother_name_raw: str | None = Field(
        default=None,
        description="Verbatim mother's name (maiden or married) recorded in the register.",
    )
    sponsors_or_godparents: list[str] = Field(
        default_factory=list,
        description="Verbatim names of godparents, sponsors, or witnesses.",
    )

    ALLOWED_CATEGORIES: ClassVar[frozenset[SourceRecordCategory]] = _BAPTISM_CATEGORIES
    ALLOWED_RECORD_TYPES: ClassVar[frozenset[SourceRecordType]] = _BAPTISM_RECORD_TYPES

    def __post_init__(self) -> None:
        """Enforce category, record_type, church name, and baptized name boundaries."""
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

        for field_name in ("church_name_raw", "baptized_name_raw"):
            raw_val = getattr(self, field_name)
            clean_val = raw_val.strip()
            if not clean_val:
                raise ModelFormatError(
                    f"{self.__class__.__name__} '{field_name}' cannot be empty or whitespace."
                )
            if clean_val != raw_val:
                object.__setattr__(self, field_name, clean_val)

    @classmethod
    def create(  # type: ignore[override]
        cls,
        source_id: SourceID | str,
        source_urn: ArchivalURN | str,
        description: str,
        repository_id: RepositoryID | str,
        church_name_raw: str,
        baptized_name_raw: str,
        date_of_baptism: EventDate | dict[str, Any] | str,
        record_category: SourceRecordCategory | str = SourceRecordCategory.CHURCH,
        record_type: SourceRecordType | str = SourceRecordType.BAPTISM_REGISTER,
        church_org_id: OrganizationID | str | None = None,
        church_site_id: SiteID | str | None = None,
        location_id: LocationID | str | None = None,
        denomination: str | None = None,
        volume_title: str | None = None,
        register_locator: str | None = None,
        individual_id: IndividualID | str | None = None,
        sex: Sex | str | None = None,
        date_of_birth: EventDate | dict[str, Any] | str | None = None,
        place_of_birth_raw: str | None = None,
        officiant_name_raw: str | None = None,
        father_name_raw: str | None = None,
        mother_name_raw: str | None = None,
        sponsors_or_godparents: list[str] | None = None,
        audit: AuditStamp | None = None,
        media_ids: list[MediaID | str] | None = None,
        associated_people: list[AssociatedIndividual] | None = None,
        tombstone: Tombstone[SourceID] | None = None,
    ) -> BaptismRecord:
        """Factory constructor instantiating a validated BaptismRecord."""
        resolved_urn = (
            source_urn if isinstance(source_urn, ArchivalURN) else SourceURN(str(source_urn))
        )
        return cls(
            source_id=_coerce_id(source_id, SourceID),
            source_urn=resolved_urn,
            record_category=coerce_enum(
                SourceRecordCategory, record_category, field_name="record_category"
            ),
            record_type=coerce_enum(SourceRecordType, record_type, field_name="record_type"),
            description=description.strip() if isinstance(description, str) else description,
            repository_id=_coerce_id(repository_id, RepositoryID),
            audit=audit or AuditStamp.now(),
            media_ids=_coerce_media_list(media_ids),
            associated_people=associated_people or [],
            tombstone=tombstone,
            church_name_raw=church_name_raw,
            baptized_name_raw=baptized_name_raw,
            date_of_baptism=_deserialize_event_date(date_of_baptism, "date_of_baptism"),
            church_org_id=_opt_id(church_org_id, OrganizationID),
            church_site_id=_opt_id(church_site_id, SiteID),
            location_id=_opt_id(location_id, LocationID),
            denomination=denomination,
            volume_title=volume_title,
            register_locator=register_locator,
            individual_id=_opt_id(individual_id, IndividualID),
            sex=_opt_sex(sex),
            date_of_birth=_opt_event_date(date_of_birth, "date_of_birth"),
            place_of_birth_raw=place_of_birth_raw,
            officiant_name_raw=officiant_name_raw,
            father_name_raw=father_name_raw,
            mother_name_raw=mother_name_raw,
            sponsors_or_godparents=list(sponsors_or_godparents) if sponsors_or_godparents else [],
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize BaptismRecord to a dictionary."""
        data = super().to_dict()
        data["sponsors_or_godparents"] = list(self.sponsors_or_godparents)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BaptismRecord:
        """Deserialize a dictionary payload into a BaptismRecord."""
        if not isinstance(data, dict):
            raise ModelFormatError("BaptismRecord payload must be a dictionary.")

        sid = data.get("source_id")
        raw_urn = data.get("source_urn")
        desc = data.get("description")
        rep = data.get("repository_id")
        audit_payload = data.get("audit")
        church_name = data.get("church_name_raw")
        baptized_name = data.get("baptized_name_raw")
        raw_bap_date = data.get("date_of_baptism")

        if not all(
            (
                sid,
                raw_urn,
                desc,
                rep,
                audit_payload,
                church_name,
                baptized_name,
                raw_bap_date,
            )
        ):
            raise ModelFormatError(
                "BaptismRecord requires source_id, source_urn, description, repository_id, "
                "audit, church_name_raw, baptized_name_raw, and date_of_baptism."
            )

        if not isinstance(audit_payload, (AuditStamp, dict)):
            raise ModelFormatError("BaptismRecord audit must be an AuditStamp or dictionary.")
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
            church_name_raw=str(church_name),
            baptized_name_raw=str(baptized_name),
            date_of_baptism=cast(Any, raw_bap_date),
            record_category=data.get("record_category", SourceRecordCategory.CHURCH),
            record_type=data.get("record_type", SourceRecordType.BAPTISM_REGISTER),
            church_org_id=data.get("church_org_id"),
            church_site_id=data.get("church_site_id"),
            location_id=data.get("location_id"),
            denomination=data.get("denomination"),
            volume_title=data.get("volume_title"),
            register_locator=data.get("register_locator"),
            individual_id=data.get("individual_id"),
            sex=data.get("sex"),
            date_of_birth=data.get("date_of_birth"),
            place_of_birth_raw=data.get("place_of_birth_raw"),
            officiant_name_raw=data.get("officiant_name_raw"),
            father_name_raw=data.get("father_name_raw"),
            mother_name_raw=data.get("mother_name_raw"),
            sponsors_or_godparents=data.get("sponsors_or_godparents"),
            audit=audit_obj,
            media_ids=data.get("media_ids", []),
            associated_people=[
                AssociatedIndividual.from_dict(p) for p in data.get("associated_people", [])
            ],
            tombstone=tombstone_obj,
        )

    def __str__(self) -> str:
        return f"BaptismRecord [{self.baptized_name_raw} @ {self.church_name_raw}] ({self.date_of_baptism})"
