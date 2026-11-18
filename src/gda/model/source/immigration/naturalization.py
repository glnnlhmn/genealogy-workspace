"""Path: src/gda/model/source/immigration/naturalization.py

Historical naturalization declarations of intention, petitions, oaths, and certificates.

Operational Role:
    Defines NaturalizationWitness (subscribing witness on a petition or oath) and
    NaturalizationRecord (extending SourceRecord) to capture primary documentary
    evidence from Declarations of Intention ('First Papers'), Petitions for
    Naturalization ('Second/Final Papers'), Certificates of Citizenship, Oaths of
    Allegiance, and Court Naturalization Orders (aligned with
    schemas/sources/naturalization_record.schema.json).
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from typing import Any, ClassVar, cast

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.enums.immigration import NaturalizationStage
from gda.core.enums.sources import SourceRecordCategory, SourceRecordType
from gda.core.errors import ModelFormatError
from gda.core.introspectable import IntrospectableMixin
from gda.core.types import URN_REGEXES
from gda.model.atom.id import IndividualID, LocationID, MediaID, RepositoryID, SourceID
from gda.model.atom.urn import ArchivalURN, SourceURN
from gda.model.base.association import AssociatedIndividual
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate
from gda.model.base.source import SourceRecord
from gda.model.base.tombstone import Tombstone
from gda.util.enums import coerce_enum

__version__ = "1.0.0+build.6"

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

_NATURALIZATION_URN_PATTERN: re.Pattern[str] = URN_REGEXES["NATURALIZATION"]


# ==============================================================================
# 1. COERCION & NORMALIZATION HELPERS
# ==============================================================================


def _resolve_naturalization_urn(raw: ArchivalURN | str) -> ArchivalURN:
    """Coerce a raw URN string into ArchivalURN (URN:NATURALIZATION:...) or SourceURN (URN:SRC:...)."""
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


def _opt_event_date(raw: Any, field_name: str) -> EventDate | None:
    """Coerce an optional EventDate input or return None when absent."""
    return _deserialize_event_date(raw, field_name) if raw is not None else None


def _parse_stage(raw: NaturalizationStage | str) -> NaturalizationStage:
    """Resolve NaturalizationStage by enum instance, exact value, or uppercase member name."""
    try:
        return coerce_enum(NaturalizationStage, raw, field_name="stage")
    except ModelFormatError as err:
        raise ModelFormatError(f"Invalid NaturalizationStage value: '{raw}'.") from err


def _coerce_id[TID](val: TID | str, id_cls: type[TID]) -> TID:
    """Coerce a required typed ID or string token into id_cls."""
    return val if isinstance(val, id_cls) else id_cls(val)  # type: ignore[call-arg]


def _opt_id[TID](val: TID | str | None, id_cls: type[TID]) -> TID | None:
    """Coerce an optional typed ID or string token into id_cls, or return None."""
    if val is None:
        return None
    return val if isinstance(val, id_cls) else id_cls(val)  # type: ignore[call-arg]


def _coerce_witnesses_tuple(
    witnesses: Iterable[NaturalizationWitness | dict[str, Any]] | None,
) -> tuple[NaturalizationWitness, ...]:
    """Hydrate an optional sequence of NaturalizationWitness objects or dicts into a tuple."""
    if not witnesses:
        return ()
    return tuple(
        w if isinstance(w, NaturalizationWitness) else NaturalizationWitness.from_dict(w)
        for w in witnesses
    )


def _coerce_media_list(media_ids: Iterable[MediaID | str] | None) -> list[MediaID]:
    """Hydrate an optional sequence of MediaID instances or strings into a list."""
    if not media_ids:
        return []
    return [m if isinstance(m, MediaID) else MediaID(m) for m in media_ids]


# ==============================================================================
# 2. NATURALIZATION WITNESS VALUE OBJECT
# ==============================================================================


@dataclass(
    repr=False,
    config=ConfigDict(frozen=True, extra="forbid", strict=True),
    kw_only=True,
)
class NaturalizationWitness(IntrospectableMixin):
    """Subscribing witness attesting to an applicant's residence and character."""

    name: str = Field(
        ...,
        description="Verbatim full name of the subscribing witness.",
    )
    individual_id: IndividualID | None = Field(
        default=None,
        description="Resolved canonical IndividualID of the witness if linked.",
    )
    occupation: str | None = Field(
        default=None,
        description="Verbatim occupation of the witness stated on the petition.",
    )
    residence: str | None = Field(
        default=None,
        description="Verbatim street or town residence of the witness.",
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
        return cls(
            name=name,
            individual_id=_opt_id(individual_id, IndividualID),
            occupation=occupation,
            residence=residence,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize NaturalizationWitness to a dictionary."""
        data: dict[str, Any] = {
            "name": self.name,
        }
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


# ==============================================================================
# 3. NATURALIZATION RECORD DOMAIN MODEL
# ==============================================================================


@dataclass(
    repr=False,
    config=ConfigDict(frozen=True, extra="forbid", strict=True),
    kw_only=True,
)
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
        description="Name of the presiding judge, clerk, or prothonotary.",
    )
    volume_page: str | None = Field(
        default=None,
        description="Volume, book, and page/folio number in the naturalization docket.",
    )
    certificate_stub_number: str | None = Field(
        default=None,
        description="Certificate of Naturalization or stub number.",
    )
    stage: NaturalizationStage | None = Field(
        default=None,
        description="Procedural stage (FIRST_PAPERS, FINAL_PAPERS, DERIVATIVE, MILITARY, OTHER).",
    )
    applicant_id: IndividualID | None = Field(
        default=None,
        description="Resolved canonical IndividualID of the applicant.",
    )
    current_residence_raw: str | None = Field(
        default=None,
        description="Verbatim street, town, or county residence of the applicant.",
    )
    current_residence_id: LocationID | None = Field(
        default=None,
        description="Resolved canonical LocationID for the applicant's residence.",
    )
    date_of_birth: EventDate | None = Field(
        default=None,
        description="Applicant's date of birth or age-derived birth date stated on the instrument.",
    )
    place_of_birth_raw: str | None = Field(
        default=None,
        description="Verbatim town, province, and country of birth.",
    )
    place_of_birth_id: LocationID | None = Field(
        default=None,
        description="Resolved canonical LocationID for the applicant's birthplace.",
    )
    country_of_prior_allegiance: str | None = Field(
        default=None,
        description="Foreign sovereign or state whose allegiance is renounced.",
    )
    port_of_entry_raw: str | None = Field(
        default=None,
        description="Verbatim port of arrival stated on the declaration or petition.",
    )
    arrival_date: EventDate | None = Field(
        default=None,
        description="Date of arrival in the United States stated on the instrument.",
    )
    vessel_name: str | None = Field(
        default=None,
        description="Vessel or carrier of arrival stated on the declaration or petition.",
    )
    witnesses: tuple[NaturalizationWitness, ...] = Field(
        default=(),
        description="Ordered tuple of subscribing witnesses on the petition or oath.",
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
        return cls(
            source_id=_coerce_id(source_id, SourceID),
            source_urn=_resolve_naturalization_urn(source_urn),
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
            court_name=court_name,
            docket_locator=docket_locator,
            applicant_name_raw=applicant_name_raw,
            event_date=_deserialize_event_date(event_date, "event_date"),
            court_location_id=_opt_id(court_location_id, LocationID),
            presiding_judge_or_clerk=presiding_judge_or_clerk,
            volume_page=volume_page,
            certificate_stub_number=certificate_stub_number,
            stage=_parse_stage(stage) if stage is not None else None,
            applicant_id=_opt_id(applicant_id, IndividualID),
            current_residence_raw=current_residence_raw,
            current_residence_id=_opt_id(current_residence_id, LocationID),
            date_of_birth=_opt_event_date(date_of_birth, "date_of_birth"),
            place_of_birth_raw=place_of_birth_raw,
            place_of_birth_id=_opt_id(place_of_birth_id, LocationID),
            country_of_prior_allegiance=country_of_prior_allegiance,
            port_of_entry_raw=port_of_entry_raw,
            arrival_date=_opt_event_date(arrival_date, "arrival_date"),
            vessel_name=vessel_name,
            witnesses=_coerce_witnesses_tuple(witnesses),
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
        for id_key in (
            "court_location_id",
            "applicant_id",
            "current_residence_id",
            "place_of_birth_id",
        ):
            id_val = getattr(self, id_key)
            if id_val is not None:
                data[id_key] = str(id_val)

        for str_key in (
            "presiding_judge_or_clerk",
            "volume_page",
            "certificate_stub_number",
            "current_residence_raw",
            "place_of_birth_raw",
            "country_of_prior_allegiance",
            "port_of_entry_raw",
            "vessel_name",
        ):
            str_val = getattr(self, str_key)
            if str_val is not None:
                data[str_key] = str_val

        if self.stage is not None:
            data["stage"] = self.stage.value
        if self.date_of_birth is not None:
            data["date_of_birth"] = self.date_of_birth.to_dict()
        if self.arrival_date is not None:
            data["arrival_date"] = self.arrival_date.to_dict()
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
            (
                sid,
                raw_urn,
                desc,
                rep,
                audit_payload,
                court_name,
                locator,
                applicant,
                raw_event_dt,
            )
        ):
            raise ModelFormatError(
                "NaturalizationRecord requires source_id, source_urn, description, repository_id, "
                "audit, court_name, docket_locator, applicant_name_raw, and event_date."
            )

        if not isinstance(audit_payload, (AuditStamp, dict)):
            raise ModelFormatError(
                "NaturalizationRecord audit must be an AuditStamp or dictionary."
            )
        audit_obj = AuditStamp.from_dict(audit_payload)

        tombstone_payload = data.get("tombstone")
        tombstone_obj = (
            Tombstone.from_dict(tombstone_payload, id_cls=SourceID)
            if isinstance(tombstone_payload, dict)
            else None
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
            event_date=cast(Any, raw_event_dt),
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
            f"NaturalizationRecord [{self.record_type.value}] {self.applicant_name_raw} "
            f"({self.docket_locator})"
        )
