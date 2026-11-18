"""Path: src/gda/model/source/vital/marriage.py

Civil and ecclesiastical marriage license, certificate, bond, and register models.

Operational Role:
    Defines MarriageRecord extending SourceRecord to capture primary documentary
    evidence from marriage applications, licenses, certificates, minister/justice
    returns, marriage bonds, and civil or parish marriage registers (aligned with
    schemas/sources/marriage_license.schema.json).
"""

from __future__ import annotations

from typing import Any, ClassVar

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.enums.sources import SourceRecordCategory, SourceRecordType
from gda.core.enums.vital import MaritalHistoryDissolution, MaritalStatus, UnionType
from gda.core.errors import ModelFormatError
from gda.model.atom.id import IndividualID, LocationID, MediaID, RepositoryID, SourceID
from gda.model.atom.urn import ArchivalURN, SourceURN, VitalCertificateUrn
from gda.model.base.age import Age
from gda.model.base.association import AssociatedIndividual
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate
from gda.model.base.source import SourceRecord
from gda.model.base.tombstone import Tombstone
from gda.util.enums import coerce_enum

__version__ = "1.0.0+build.4"

__all__ = [
    "MarriageRecord",
]

_MARRIAGE_CATEGORIES: frozenset[SourceRecordCategory] = frozenset(
    {
        SourceRecordCategory.VITAL,
        SourceRecordCategory.CHURCH,
    }
)

_MARRIAGE_RECORD_TYPES: frozenset[SourceRecordType] = frozenset(
    {
        SourceRecordType.MARRIAGE_LICENSE,
        SourceRecordType.MARRIAGE_CERTIFICATE,
        SourceRecordType.MARRIAGE_REGISTER,
        SourceRecordType.MINISTERS_RETURN,
        SourceRecordType.MARRIAGE_BOND,
    }
)


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


@dataclass(
    repr=False,
    config=ConfigDict(frozen=True, extra="forbid", strict=True),
    kw_only=True,
)
class MarriageRecord(SourceRecord):
    """Primary archival record documenting a marriage license, ceremony, bond, or register entry."""

    record_category: SourceRecordCategory = Field(
        default=SourceRecordCategory.VITAL,
        description="High-level archival domain category (VITAL or CHURCH).",
    )
    record_type: SourceRecordType = Field(
        default=SourceRecordType.MARRIAGE_LICENSE,
        description="Specific marriage documentary record classification.",
    )
    groom_name_raw: str = Field(
        ...,
        description="Verbatim full name of the groom or first party.",
    )
    bride_name_raw: str = Field(
        ...,
        description="Verbatim full name of the bride or second party.",
    )
    union_type: UnionType = Field(
        default=UnionType.MARRIED,
        description="Classification of domestic union inception.",
    )
    license_number: str | None = Field(
        default=None,
        description="Official state, county, or local marriage license number.",
    )
    date_issued: EventDate | None = Field(
        default=None,
        description="Date the marriage license or bond was issued.",
    )
    issuing_jurisdiction_raw: str | None = Field(
        default=None,
        description="Court, county, or town clerk office issuing the license.",
    )
    groom_id: IndividualID | None = Field(
        default=None,
        description="Resolved canonical IndividualID of the groom if linked.",
    )
    groom_age: Age | None = Field(
        default=None,
        description="Age of the groom recorded on the license or register.",
    )
    groom_marital_status: MaritalStatus | None = Field(
        default=None,
        description="Prior marital status of the groom.",
    )
    groom_prior_dissolution: MaritalHistoryDissolution | None = Field(
        default=None,
        description="How groom's prior marriage ended (Death, Divorce, Annulment, None).",
    )
    groom_residence_raw: str | None = Field(
        default=None,
        description="Verbatim residence of the groom at time of marriage.",
    )
    bride_id: IndividualID | None = Field(
        default=None,
        description="Resolved canonical IndividualID of the bride if linked.",
    )
    bride_maiden_name_raw: str | None = Field(
        default=None,
        description="Verbatim maiden surname of the bride if married previously.",
    )
    bride_age: Age | None = Field(
        default=None,
        description="Age of the bride recorded on the license or register.",
    )
    bride_marital_status: MaritalStatus | None = Field(
        default=None,
        description="Prior marital status of the bride.",
    )
    bride_prior_dissolution: MaritalHistoryDissolution | None = Field(
        default=None,
        description="How bride's prior marriage ended (Death, Divorce, Annulment, None).",
    )
    bride_residence_raw: str | None = Field(
        default=None,
        description="Verbatim residence of the bride at time of marriage.",
    )
    date_of_marriage: EventDate | None = Field(
        default=None,
        description="Recorded date of the marriage ceremony or solemnization.",
    )
    place_of_marriage_raw: str | None = Field(
        default=None,
        description="Verbatim church, town, county, or state where solemnized.",
    )
    place_of_marriage_id: LocationID | None = Field(
        default=None,
        description="Resolved canonical LocationID for the marriage jurisdiction.",
    )
    officiant_name_raw: str | None = Field(
        default=None,
        description="Verbatim name of minister, priest, rabbi, or justice of the peace.",
    )
    officiant_title_raw: str | None = Field(
        default=None,
        description="Verbatim title of officiant (e.g., 'Rev.', 'Justice of the Peace').",
    )
    religious_denomination: str | None = Field(
        default=None,
        description="Religious denomination of church or officiant if recorded.",
    )
    witnesses: list[str] = Field(
        default_factory=list,
        description="Verbatim names of subscribing witnesses on the return or register.",
    )

    ALLOWED_CATEGORIES: ClassVar[frozenset[SourceRecordCategory]] = _MARRIAGE_CATEGORIES
    ALLOWED_RECORD_TYPES: ClassVar[frozenset[SourceRecordType]] = _MARRIAGE_RECORD_TYPES

    def __post_init__(self) -> None:
        """Enforce category, record_type, and spouse name boundaries."""
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

        clean_groom = self.groom_name_raw.strip()
        if not clean_groom:
            raise ModelFormatError(
                f"{self.__class__.__name__} 'groom_name_raw' cannot be empty or whitespace."
            )
        if clean_groom != self.groom_name_raw:
            object.__setattr__(self, "groom_name_raw", clean_groom)

        clean_bride = self.bride_name_raw.strip()
        if not clean_bride:
            raise ModelFormatError(
                f"{self.__class__.__name__} 'bride_name_raw' cannot be empty or whitespace."
            )
        if clean_bride != self.bride_name_raw:
            object.__setattr__(self, "bride_name_raw", clean_bride)

    @classmethod
    def create(  # type: ignore[override]
        cls,
        source_id: SourceID | str,
        source_urn: ArchivalURN | str,
        description: str,
        repository_id: RepositoryID | str,
        groom_name_raw: str,
        bride_name_raw: str,
        record_category: SourceRecordCategory | str = SourceRecordCategory.VITAL,
        record_type: SourceRecordType | str = SourceRecordType.MARRIAGE_LICENSE,
        union_type: UnionType | str = UnionType.MARRIED,
        license_number: str | None = None,
        date_issued: EventDate | dict[str, Any] | str | None = None,
        issuing_jurisdiction_raw: str | None = None,
        groom_id: IndividualID | str | None = None,
        groom_age: Age | dict[str, Any] | int | str | None = None,
        groom_marital_status: MaritalStatus | str | None = None,
        groom_prior_dissolution: MaritalHistoryDissolution | str | None = None,
        groom_residence_raw: str | None = None,
        bride_id: IndividualID | str | None = None,
        bride_maiden_name_raw: str | None = None,
        bride_age: Age | dict[str, Any] | int | str | None = None,
        bride_marital_status: MaritalStatus | str | None = None,
        bride_prior_dissolution: MaritalHistoryDissolution | str | None = None,
        bride_residence_raw: str | None = None,
        date_of_marriage: EventDate | dict[str, Any] | str | None = None,
        place_of_marriage_raw: str | None = None,
        place_of_marriage_id: LocationID | str | None = None,
        officiant_name_raw: str | None = None,
        officiant_title_raw: str | None = None,
        religious_denomination: str | None = None,
        witnesses: list[str] | None = None,
        audit: AuditStamp | None = None,
        media_ids: list[MediaID | str] | None = None,
        associated_people: list[AssociatedIndividual] | None = None,
        tombstone: Tombstone[SourceID] | None = None,
    ) -> MarriageRecord:
        """Factory constructor instantiating a validated MarriageRecord."""
        resolved_sid = source_id if isinstance(source_id, SourceID) else SourceID(source_id)
        resolved_urn = _resolve_vital_urn(source_urn)
        resolved_rep = (
            repository_id
            if isinstance(repository_id, RepositoryID)
            else RepositoryID(repository_id)
        )
        res_cat = coerce_enum(SourceRecordCategory, record_category, field_name="record_category")
        res_type = coerce_enum(SourceRecordType, record_type, field_name="record_type")
        res_union = coerce_enum(UnionType, union_type, field_name="union_type")
        res_groom_id = (
            groom_id
            if (groom_id is None or isinstance(groom_id, IndividualID))
            else IndividualID(groom_id)
        )
        res_bride_id = (
            bride_id
            if (bride_id is None or isinstance(bride_id, IndividualID))
            else IndividualID(bride_id)
        )
        res_place_id = (
            place_of_marriage_id
            if (place_of_marriage_id is None or isinstance(place_of_marriage_id, LocationID))
            else LocationID(place_of_marriage_id)
        )
        res_groom_ms = (
            coerce_enum(MaritalStatus, groom_marital_status, field_name="groom_marital_status")
            if groom_marital_status is not None
            else None
        )
        res_bride_ms = (
            coerce_enum(MaritalStatus, bride_marital_status, field_name="bride_marital_status")
            if bride_marital_status is not None
            else None
        )
        res_groom_dis = (
            coerce_enum(
                MaritalHistoryDissolution,
                groom_prior_dissolution,
                field_name="groom_prior_dissolution",
            )
            if groom_prior_dissolution is not None
            else None
        )
        res_bride_dis = (
            coerce_enum(
                MaritalHistoryDissolution,
                bride_prior_dissolution,
                field_name="bride_prior_dissolution",
            )
            if bride_prior_dissolution is not None
            else None
        )

        res_issued = (
            _deserialize_event_date(date_issued, "date_issued") if date_issued is not None else None
        )
        res_dom = (
            _deserialize_event_date(date_of_marriage, "date_of_marriage")
            if date_of_marriage is not None
            else None
        )
        res_groom_age = _deserialize_age(groom_age, "groom_age") if groom_age is not None else None
        res_bride_age = _deserialize_age(bride_age, "bride_age") if bride_age is not None else None

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
            groom_name_raw=groom_name_raw,
            bride_name_raw=bride_name_raw,
            union_type=res_union,
            license_number=license_number,
            date_issued=res_issued,
            issuing_jurisdiction_raw=issuing_jurisdiction_raw,
            groom_id=res_groom_id,
            groom_age=res_groom_age,
            groom_marital_status=res_groom_ms,
            groom_prior_dissolution=res_groom_dis,
            groom_residence_raw=groom_residence_raw,
            bride_id=res_bride_id,
            bride_maiden_name_raw=bride_maiden_name_raw,
            bride_age=res_bride_age,
            bride_marital_status=res_bride_ms,
            bride_prior_dissolution=res_bride_dis,
            bride_residence_raw=bride_residence_raw,
            date_of_marriage=res_dom,
            place_of_marriage_raw=place_of_marriage_raw,
            place_of_marriage_id=res_place_id,
            officiant_name_raw=officiant_name_raw,
            officiant_title_raw=officiant_title_raw,
            religious_denomination=religious_denomination,
            witnesses=list(witnesses) if witnesses is not None else [],
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize MarriageRecord to a dictionary."""
        data = super().to_dict()
        data["witnesses"] = list(self.witnesses)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MarriageRecord:
        """Deserialize a dictionary payload into a MarriageRecord."""
        if not isinstance(data, dict):
            raise ModelFormatError("MarriageRecord payload must be a dictionary.")

        sid = data.get("source_id")
        raw_urn = data.get("source_urn")
        desc = data.get("description")
        rep = data.get("repository_id")
        audit_payload = data.get("audit")
        groom_name = data.get("groom_name_raw")
        bride_name = data.get("bride_name_raw")

        if not all((sid, raw_urn, desc, rep, audit_payload, groom_name, bride_name)):
            raise ModelFormatError(
                "MarriageRecord requires source_id, source_urn, description, repository_id, "
                "audit, groom_name_raw, and bride_name_raw."
            )

        if not isinstance(audit_payload, (AuditStamp, dict)):
            raise ModelFormatError("MarriageRecord audit must be an AuditStamp or dictionary.")
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
            groom_name_raw=str(groom_name),
            bride_name_raw=str(bride_name),
            record_category=data.get("record_category", SourceRecordCategory.VITAL),
            record_type=data.get("record_type", SourceRecordType.MARRIAGE_LICENSE),
            union_type=data.get("union_type", UnionType.MARRIED),
            license_number=data.get("license_number"),
            date_issued=data.get("date_issued"),
            issuing_jurisdiction_raw=data.get("issuing_jurisdiction_raw"),
            groom_id=data.get("groom_id"),
            groom_age=data.get("groom_age"),
            groom_marital_status=data.get("groom_marital_status"),
            groom_prior_dissolution=data.get("groom_prior_dissolution"),
            groom_residence_raw=data.get("groom_residence_raw"),
            bride_id=data.get("bride_id"),
            bride_maiden_name_raw=data.get("bride_maiden_name_raw"),
            bride_age=data.get("bride_age"),
            bride_marital_status=data.get("bride_marital_status"),
            bride_prior_dissolution=data.get("bride_prior_dissolution"),
            bride_residence_raw=data.get("bride_residence_raw"),
            date_of_marriage=data.get("date_of_marriage"),
            place_of_marriage_raw=data.get("place_of_marriage_raw"),
            place_of_marriage_id=data.get("place_of_marriage_id"),
            officiant_name_raw=data.get("officiant_name_raw"),
            officiant_title_raw=data.get("officiant_title_raw"),
            religious_denomination=data.get("religious_denomination"),
            witnesses=data.get("witnesses"),
            audit=audit_obj,
            media_ids=data.get("media_ids", []),
            associated_people=[
                AssociatedIndividual.from_dict(p) for p in data.get("associated_people", [])
            ],
            tombstone=tombstone_obj,
        )

    def __str__(self) -> str:
        return f"MarriageRecord [{self.groom_name_raw} & {self.bride_name_raw}]"
