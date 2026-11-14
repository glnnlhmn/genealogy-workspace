"""Path: src/gda/model/immigration/naturalization.py

Historical naturalization declarations of intention, petitions, oaths, and certificates.

Operational Role:
    Defines NaturalizationWitness (deponent or character witness supporting a
    petition) and NaturalizationRecord (extending SourceRecord) to capture primary
    documentary evidence from judicial naturalization proceedings (aligned with
    schemas/sources/naturalization_record.schema.json).
"""

from __future__ import annotations

import json
import re
from typing import Any, ClassVar

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.enums.immigration import NaturalizationStage
from gda.core.enums.sources import SourceRecordCategory, SourceRecordType
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
    "NaturalizationRecord",
    "NaturalizationWitness",
]

_NATURALIZATION_CATEGORIES: frozenset[SourceRecordCategory] = frozenset(
    {
        SourceRecordCategory.LEGAL,
        SourceRecordCategory.CITIZENSHIP,
        SourceRecordCategory.IMMIGRATION,
    }
)

_NATURALIZATION_RECORD_TYPES: frozenset[SourceRecordType] = frozenset(
    {
        SourceRecordType.DECLARATION_OF_INTENTION,
        SourceRecordType.PETITION_FOR_NATURALIZATION,
        SourceRecordType.CERTIFICATE_OF_CITIZENSHIP,
        SourceRecordType.OATH_OF_ALLEGIANCE,
        SourceRecordType.ORDER_OF_COURT,
    }
)

_NATURALIZATION_URN_PATTERN: re.Pattern[str] = re.compile(
    r"^URN:NATURALIZATION:[0-9]{4}:[A-Z0-9_]+:[A-Za-z0-9_.-]+$"
)


def _resolve_naturalization_urn(raw: ArchivalURN | str) -> ArchivalURN:
    """Coerce a raw URN string into ArchivalURN (URN:NATURALIZATION:...) or SourceURN."""
    if isinstance(raw, ArchivalURN):
        return raw
    token = str(raw).strip()
    if token.startswith("URN:NATURALIZATION:"):
        if not _NATURALIZATION_URN_PATTERN.match(token):
            raise ModelFormatError(
                f"Invalid Naturalization URN syntax: '{token}'. "
                "Must match 'URN:NATURALIZATION:<YEAR>:<JURISDICTION>:<LOCATOR>'."
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


def _parse_stage(raw: NaturalizationStage | str) -> NaturalizationStage:
    """Resolve NaturalizationStage by enum instance, exact value, or uppercase member name."""
    if isinstance(raw, NaturalizationStage):
        return raw
    token = str(raw).strip().upper()
    for member in NaturalizationStage:
        if token in (member.name, member.value):
            return member
    raise ModelFormatError(f"Invalid NaturalizationStage value: '{raw}'.")


@dataclass(repr=False, config=ConfigDict(kw_only=True, frozen=True, extra="forbid", strict=True))
class NaturalizationWitness(IntrospectableMixin):
    """Single deponent or character witness attesting to a naturalization petition."""

    name: str = Field(
        ...,
        description="Verbatim full name of the witness or voucher.",
    )
    individual_id: IndividualID | None = Field(
        default=None,
        description="Resolved canonical IndividualID if linked to a person entity.",
    )
    occupation: str | None = Field(
        default=None,
        description="Verbatim occupation stated by the witness.",
    )
    residence: str | None = Field(
        default=None,
        description="Verbatim street, town, or county residence stated by the witness.",
    )

    def __post_init__(self) -> None:
        """Enforce non-empty witness name hygiene."""
        clean_name = self.name.strip()
        if not clean_name:
            raise ModelFormatError("NaturalizationWitness 'name' cannot be empty or whitespace.")
        if clean_name != self.name:
            object.__setattr__(self, "name", clean_name)

    @classmethod
    def create(
        cls,
        name: str,
        individual_id: IndividualID | str | None = None,
        occupation: str | None = None,
        residence: str | None = None,
    ) -> NaturalizationWitness:
        """Factory constructor instantiating a validated NaturalizationWitness."""
        res_ind = (
            individual_id
            if (individual_id is None or isinstance(individual_id, IndividualID))
            else IndividualID(individual_id)
        )
        return cls(
            name=name,
            individual_id=res_ind,
            occupation=occupation,
            residence=residence,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize NaturalizationWitness to a dictionary."""
        data: dict[str, Any] = {"name": self.name}
        if self.individual_id is not None:
            data["individual_id"] = str(self.individual_id)
        if self.occupation is not None:
            data["occupation"] = self.occupation
        if self.residence is not None:
            data["residence"] = self.residence
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> NaturalizationWitness:
        """Deserialize a dictionary payload into a NaturalizationWitness."""
        if not isinstance(data, dict):
            raise ModelFormatError("NaturalizationWitness payload must be a dictionary.")
        name = data.get("name")
        if name is None:
            raise ModelFormatError("NaturalizationWitness requires 'name'.")
        return cls.create(
            name=str(name),
            individual_id=data.get("individual_id"),
            occupation=data.get("occupation"),
            residence=data.get("residence"),
        )

    def to_json(self) -> str:
        """Serialize NaturalizationWitness to a JSON formatted string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_json(cls, payload: str) -> NaturalizationWitness:
        """Deserialize a JSON string directly into a NaturalizationWitness."""
        try:
            data = json.loads(payload)
        except Exception as exc:
            raise ModelFormatError(
                f"Failed to parse NaturalizationWitness JSON string: {exc}"
            ) from exc
        return cls.from_dict(data)

    def __str__(self) -> str:
        return self.name


@dataclass(repr=False, config=ConfigDict(kw_only=True, frozen=True, extra="forbid", strict=True))
class NaturalizationRecord(SourceRecord):
    """Primary archival record documenting a naturalization declaration, petition, or certificate."""

    record_category: SourceRecordCategory = Field(
        default=SourceRecordCategory.LEGAL,
        description="High-level archival domain category (LEGAL, CITIZENSHIP, IMMIGRATION).",
    )
    record_type: SourceRecordType = Field(
        default=SourceRecordType.DECLARATION_OF_INTENTION,
        description="Specific naturalization instrument classification.",
    )
    court_name: str = Field(
        ...,
        description="Verbatim name of the Federal, District, Circuit, or County Court.",
    )
    docket_locator: str = Field(
        ...,
        description="Primary petition number, declaration number, or archival call locator.",
    )
    applicant_name_raw: str = Field(
        ...,
        description="Verbatim name of the declarant, petitioner, or newly naturalized citizen.",
    )
    event_date: EventDate = Field(
        ...,
        description="Date the declaration, petition, oath, or court order was executed.",
    )
    court_location_id: LocationID | None = Field(
        default=None,
        description="Resolved canonical LocationID for the naturalizing court.",
    )
    presiding_judge_or_clerk: str | None = Field(
        default=None,
        description="Name of the presiding judge, clerk, or deputy clerk.",
    )
    volume_page: str | None = Field(
        default=None,
        description="Recorded volume and page reference.",
    )
    certificate_stub_number: str | None = Field(
        default=None,
        description="Official certificate of naturalization stub or serial number.",
    )
    stage: NaturalizationStage | None = Field(
        default=None,
        description="Procedural stage within the naturalization sequence.",
    )
    applicant_id: IndividualID | None = Field(
        default=None,
        description="Resolved canonical IndividualID of the applicant.",
    )
    current_residence_raw: str | None = Field(
        default=None,
        description="Verbatim residence of the applicant at the time of filing.",
    )
    current_residence_id: LocationID | None = Field(
        default=None,
        description="Resolved canonical LocationID for the applicant's current residence.",
    )
    date_of_birth: EventDate | None = Field(
        default=None,
        description="Date of birth stated by the applicant.",
    )
    place_of_birth_raw: str | None = Field(
        default=None,
        description="Verbatim birthplace stated by the applicant.",
    )
    place_of_birth_id: LocationID | None = Field(
        default=None,
        description="Resolved canonical LocationID for the applicant's birthplace.",
    )
    country_of_prior_allegiance: str | None = Field(
        default=None,
        description="Verbatim sovereign ruler or nation renounced by the applicant.",
    )
    port_of_entry_raw: str | None = Field(
        default=None,
        description="Verbatim port of arrival recited in the naturalization filing.",
    )
    arrival_date: EventDate | None = Field(
        default=None,
        description="Date of arrival recited in the naturalization filing.",
    )
    vessel_name: str | None = Field(
        default=None,
        description="Name of the vessel recited in the naturalization filing.",
    )
    witnesses: tuple[NaturalizationWitness, ...] = Field(
        default=(),
        description="Ordered tuple of supporting witnesses or character vouchers.",
    )

    ALLOWED_CATEGORIES: ClassVar[frozenset[SourceRecordCategory]] = _NATURALIZATION_CATEGORIES
    ALLOWED_RECORD_TYPES: ClassVar[frozenset[SourceRecordType]] = _NATURALIZATION_RECORD_TYPES

    def __post_init__(self) -> None:
        """Enforce category, record_type, and required string hygiene."""
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

        for field_name in ("court_name", "docket_locator", "applicant_name_raw"):
            raw_val = getattr(self, field_name)
            cleaned = raw_val.strip()
            if not cleaned:
                raise ModelFormatError(
                    f"{self.__class__.__name__} '{field_name}' cannot be empty or whitespace."
                )
            if cleaned != raw_val:
                object.__setattr__(self, field_name, cleaned)

    @property
    def witness_count(self) -> int:
        """Return count of supporting witnesses on this instrument."""
        return len(self.witnesses)

    @classmethod
    def create(  # type: ignore[override]
        cls,
        source_id: SourceID | str,
        source_urn: ArchivalURN | str,
        description: str,
        repository_id: RepositoryID | str,
        court_name: str,
        docket_locator: str,
        applicant_name_raw: str,
        event_date: EventDate | dict[str, Any] | str,
        record_category: SourceRecordCategory | str = SourceRecordCategory.LEGAL,
        record_type: SourceRecordType | str = SourceRecordType.DECLARATION_OF_INTENTION,
        court_location_id: LocationID | str | None = None,
        presiding_judge_or_clerk: str | None = None,
        volume_page: str | None = None,
        certificate_stub_number: str | None = None,
        stage: NaturalizationStage | str | None = None,
        applicant_id: IndividualID | str | None = None,
        current_residence_raw: str | None = None,
        current_residence_id: LocationID | str | None = None,
        date_of_birth: EventDate | dict[str, Any] | str | None = None,
        place_of_birth_raw: str | None = None,
        place_of_birth_id: LocationID | str | None = None,
        country_of_prior_allegiance: str | None = None,
        port_of_entry_raw: str | None = None,
        arrival_date: EventDate | dict[str, Any] | str | None = None,
        vessel_name: str | None = None,
        witnesses: (
            list[NaturalizationWitness | dict[str, Any]] | tuple[NaturalizationWitness, ...] | None
        ) = None,
        audit: AuditStamp | None = None,
        media_ids: list[MediaID | str] | None = None,
        associated_people: list[AssociatedIndividual] | None = None,
        tombstone: Tombstone[SourceID] | None = None,
    ) -> NaturalizationRecord:
        """Factory constructor instantiating a validated NaturalizationRecord."""
        resolved_sid = source_id if isinstance(source_id, SourceID) else SourceID(source_id)
        resolved_urn = _resolve_naturalization_urn(source_urn)
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
        res_court_loc = (
            court_location_id
            if (court_location_id is None or isinstance(court_location_id, LocationID))
            else LocationID(court_location_id)
        )
        res_stage = _parse_stage(stage) if stage is not None else None
        res_app_id = (
            applicant_id
            if (applicant_id is None or isinstance(applicant_id, IndividualID))
            else IndividualID(applicant_id)
        )
        res_curr_loc = (
            current_residence_id
            if (current_residence_id is None or isinstance(current_residence_id, LocationID))
            else LocationID(current_residence_id)
        )
        res_pob_loc = (
            place_of_birth_id
            if (place_of_birth_id is None or isinstance(place_of_birth_id, LocationID))
            else LocationID(place_of_birth_id)
        )
        res_event_dt = _deserialize_event_date(event_date, "event_date")
        res_dob = (
            _deserialize_event_date(date_of_birth, "date_of_birth")
            if date_of_birth is not None
            else None
        )
        res_arr_dt = (
            _deserialize_event_date(arrival_date, "arrival_date")
            if arrival_date is not None
            else None
        )

        resolved_witnesses: tuple[NaturalizationWitness, ...] = tuple(
            w if isinstance(w, NaturalizationWitness) else NaturalizationWitness.from_dict(w)
            for w in (witnesses or ())
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
            court_name=court_name,
            docket_locator=docket_locator,
            applicant_name_raw=applicant_name_raw,
            event_date=res_event_dt,
            court_location_id=res_court_loc,
            presiding_judge_or_clerk=presiding_judge_or_clerk,
            volume_page=volume_page,
            certificate_stub_number=certificate_stub_number,
            stage=res_stage,
            applicant_id=res_app_id,
            current_residence_raw=current_residence_raw,
            current_residence_id=res_curr_loc,
            date_of_birth=res_dob,
            place_of_birth_raw=place_of_birth_raw,
            place_of_birth_id=res_pob_loc,
            country_of_prior_allegiance=country_of_prior_allegiance,
            port_of_entry_raw=port_of_entry_raw,
            arrival_date=res_arr_dt,
            vessel_name=vessel_name,
            witnesses=resolved_witnesses,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize NaturalizationRecord to a dictionary."""
        data = super().to_dict()
        data.update(
            {
                "record_type": self.record_type.value,
                "court_name": self.court_name,
                "docket_locator": self.docket_locator,
                "applicant_name_raw": self.applicant_name_raw,
                "event_date": self.event_date.to_dict(),
                "witnesses": [w.to_dict() for w in self.witnesses],
            }
        )
        if self.court_location_id is not None:
            data["court_location_id"] = str(self.court_location_id)
        if self.presiding_judge_or_clerk is not None:
            data["presiding_judge_or_clerk"] = self.presiding_judge_or_clerk
        if self.volume_page is not None:
            data["volume_page"] = self.volume_page
        if self.certificate_stub_number is not None:
            data["certificate_stub_number"] = self.certificate_stub_number
        if self.stage is not None:
            data["stage"] = self.stage.value
        if self.applicant_id is not None:
            data["applicant_id"] = str(self.applicant_id)
        if self.current_residence_raw is not None:
            data["current_residence_raw"] = self.current_residence_raw
        if self.current_residence_id is not None:
            data["current_residence_id"] = str(self.current_residence_id)
        if self.date_of_birth is not None:
            data["date_of_birth"] = self.date_of_birth.to_dict()
        if self.place_of_birth_raw is not None:
            data["place_of_birth_raw"] = self.place_of_birth_raw
        if self.place_of_birth_id is not None:
            data["place_of_birth_id"] = str(self.place_of_birth_id)
        if self.country_of_prior_allegiance is not None:
            data["country_of_prior_allegiance"] = self.country_of_prior_allegiance
        if self.port_of_entry_raw is not None:
            data["port_of_entry_raw"] = self.port_of_entry_raw
        if self.arrival_date is not None:
            data["arrival_date"] = self.arrival_date.to_dict()
        if self.vessel_name is not None:
            data["vessel_name"] = self.vessel_name
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> NaturalizationRecord:
        """Deserialize a dictionary payload into a NaturalizationRecord."""
        if not isinstance(data, dict):
            raise ModelFormatError("NaturalizationRecord payload must be a dictionary.")

        sid = data.get("source_id")
        raw_urn = data.get("source_urn")
        desc = data.get("description")
        rep = data.get("repository_id")
        audit_payload = data.get("audit")
        court_name = data.get("court_name")
        locator = data.get("docket_locator")
        applicant = data.get("applicant_name_raw")
        raw_event_dt = data.get("event_date")

        if not all(
            (sid, raw_urn, desc, rep, audit_payload, court_name, locator, applicant, raw_event_dt)
        ):
            raise ModelFormatError(
                "NaturalizationRecord requires source_id, source_urn, description, repository_id, "
                "audit, court_name, docket_locator, applicant_name_raw, and event_date."
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
                "NaturalizationRecord audit must be an AuditStamp or dictionary."
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

        raw_witnesses = data.get("witnesses", [])
        if not isinstance(raw_witnesses, (list, tuple)):
            raise ModelFormatError("NaturalizationRecord 'witnesses' must be a list or tuple.")

        return cls.create(
            source_id=str(sid),
            source_urn=str(raw_urn),
            description=str(desc),
            repository_id=str(rep),
            court_name=str(court_name),
            docket_locator=str(locator),
            applicant_name_raw=str(applicant),
            event_date=raw_event_dt,
            record_category=data.get("record_category", SourceRecordCategory.LEGAL),
            record_type=data.get("record_type", SourceRecordType.DECLARATION_OF_INTENTION),
            court_location_id=data.get("court_location_id"),
            presiding_judge_or_clerk=data.get("presiding_judge_or_clerk"),
            volume_page=data.get("volume_page"),
            certificate_stub_number=data.get("certificate_stub_number"),
            stage=data.get("stage"),
            applicant_id=data.get("applicant_id"),
            current_residence_raw=data.get("current_residence_raw"),
            current_residence_id=data.get("current_residence_id"),
            date_of_birth=data.get("date_of_birth"),
            place_of_birth_raw=data.get("place_of_birth_raw"),
            place_of_birth_id=data.get("place_of_birth_id"),
            country_of_prior_allegiance=data.get("country_of_prior_allegiance"),
            port_of_entry_raw=data.get("port_of_entry_raw"),
            arrival_date=data.get("arrival_date"),
            vessel_name=data.get("vessel_name"),
            witnesses=list(raw_witnesses),
            audit=audit_obj,
            media_ids=data.get("media_ids", []),
            associated_people=[
                AssociatedIndividual.from_dict(p) for p in data.get("associated_people", [])
            ],
            tombstone=tombstone_obj,
        )

    def __str__(self) -> str:
        return (
            f"NaturalizationRecord [{self.record_type.value}] "
            f"{self.applicant_name_raw} ({self.docket_locator})"
        )
