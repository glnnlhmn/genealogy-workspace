"""Path: src/gda/model/cemetery/registry.py

Cemetery plot ledger, sexton book, and grave survey registry domain models.

Operational Role:
    Defines RegistryInterment (single burial row within a plot), CemeteryPlotEntry
    (a lot/section/row entry grouping one or more interments with optional marker URN
    and condition), and CemeteryRegistryRecord (extending SourceRecord) for
    collection-wide plot ledgers and cemetery surveys with flatten_interments()
    tabular projection (aligned with schemas/sources/cemetery_registry.schema.json).
"""

from __future__ import annotations

import json
from typing import Any, ClassVar

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.enums.site import MarkerCondition
from gda.core.enums.sources import SourceRecordCategory, SourceRecordType
from gda.core.errors import ModelFormatError
from gda.core.introspectable import IntrospectableMixin
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import IndividualID, LocationID, MediaID, RepositoryID, SiteID, SourceID
from gda.model.atom.urn import ArchivalURN, CemeteryPlotUrn, SourceURN
from gda.model.atom.year import HistoricalYear
from gda.model.base.association import AssociatedIndividual
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate
from gda.model.base.source import SourceRecord
from gda.model.base.tombstone import Tombstone

__version__ = "1.0.0+build.2"

__all__ = [
    "CemeteryPlotEntry",
    "CemeteryRegistryRecord",
    "RegistryInterment",
]

_REGISTRY_RECORD_TYPES: frozenset[SourceRecordType] = frozenset(
    {
        SourceRecordType.REGISTER_ENTRY,
        SourceRecordType.CEMETERY_MARKER,
        SourceRecordType.MISC,
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


def _parse_condition(raw: MarkerCondition | str) -> MarkerCondition:
    """Resolve MarkerCondition by enum instance, value, or uppercase member name."""
    if isinstance(raw, MarkerCondition):
        return raw
    token = str(raw).strip()
    for member in MarkerCondition:
        if token.upper() in (member.name, member.value.upper()):
            return member
    raise ModelFormatError(f"Invalid MarkerCondition value: '{raw}'.")


@dataclass(repr=False, config=ConfigDict(kw_only=True, frozen=True, extra="forbid", strict=True))
class RegistryInterment(IntrospectableMixin):
    """Single burial entry recorded inside a cemetery plot ledger or survey."""

    inscribed_name: str = Field(
        ...,
        description="Verbatim or standardized full name recorded in the plot ledger.",
    )
    individual_id: IndividualID | None = Field(
        default=None,
        description="Resolved canonical IndividualID if linked to a person entity.",
    )
    birth_year: HistoricalYear | None = Field(
        default=None,
        description="Four-digit birth year recorded in the sexton book or survey.",
    )
    death_year: HistoricalYear | None = Field(
        default=None,
        description="Four-digit death or burial year recorded in the sexton book or survey.",
    )
    age_inscribed: str | None = Field(
        default=None,
        description="Verbatim age notation recorded in the ledger (e.g., '64y 3m 12d').",
    )
    relationship_text: str | None = Field(
        default=None,
        description="Verbatim relationship or lot-owner note (e.g., 'Son of George W. Abbott').",
    )

    def __post_init__(self) -> None:
        """Enforce non-empty inscribed_name hygiene."""
        cleaned = self.inscribed_name.strip()
        if not cleaned:
            raise ModelFormatError(
                "RegistryInterment 'inscribed_name' cannot be empty or whitespace."
            )
        if cleaned != self.inscribed_name:
            object.__setattr__(self, "inscribed_name", cleaned)

    @classmethod
    def create(
        cls,
        inscribed_name: str,
        individual_id: IndividualID | str | None = None,
        birth_year: HistoricalYear | int | None = None,
        death_year: HistoricalYear | int | None = None,
        age_inscribed: str | None = None,
        relationship_text: str | None = None,
    ) -> RegistryInterment:
        """Factory constructor instantiating a validated RegistryInterment."""
        res_ind = (
            individual_id
            if (individual_id is None or isinstance(individual_id, IndividualID))
            else IndividualID(individual_id)
        )
        res_birth = (
            birth_year
            if (birth_year is None or isinstance(birth_year, HistoricalYear))
            else HistoricalYear(int(birth_year))
        )
        res_death = (
            death_year
            if (death_year is None or isinstance(death_year, HistoricalYear))
            else HistoricalYear(int(death_year))
        )
        return cls(
            inscribed_name=inscribed_name,
            individual_id=res_ind,
            birth_year=res_birth,
            death_year=res_death,
            age_inscribed=age_inscribed,
            relationship_text=relationship_text,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize RegistryInterment to a dictionary."""
        data: dict[str, Any] = {
            "inscribed_name": self.inscribed_name,
        }
        if self.individual_id is not None:
            data["individual_id"] = str(self.individual_id)
        if self.birth_year is not None:
            data["birth_year"] = self.birth_year.value
        if self.death_year is not None:
            data["death_year"] = self.death_year.value
        if self.age_inscribed is not None:
            data["age_inscribed"] = self.age_inscribed
        if self.relationship_text is not None:
            data["relationship_text"] = self.relationship_text
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RegistryInterment:
        """Deserialize a dictionary payload into a RegistryInterment."""
        if not isinstance(data, dict):
            raise ModelFormatError("RegistryInterment payload must be a dictionary.")
        name = data.get("inscribed_name")
        if name is None:
            raise ModelFormatError("RegistryInterment requires 'inscribed_name'.")
        return cls.create(
            inscribed_name=str(name),
            individual_id=data.get("individual_id"),
            birth_year=data.get("birth_year"),
            death_year=data.get("death_year"),
            age_inscribed=data.get("age_inscribed"),
            relationship_text=data.get("relationship_text"),
        )

    def to_json(self) -> str:
        """Serialize RegistryInterment to a JSON formatted string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_json(cls, payload: str) -> RegistryInterment:
        """Deserialize a JSON string directly into a RegistryInterment."""
        try:
            data = json.loads(payload)
        except Exception as exc:
            raise ModelFormatError(f"Failed to parse RegistryInterment JSON string: {exc}") from exc
        return cls.from_dict(data)

    def __str__(self) -> str:
        return self.inscribed_name


@dataclass(repr=False, config=ConfigDict(kw_only=True, frozen=True, extra="forbid", strict=True))
class CemeteryPlotEntry(IntrospectableMixin):
    """Single plot, lot, section, or tomb row in a cemetery registry or grave survey."""

    plot_locator: str = Field(
        ...,
        description="Lot, Section, Row, or Tomb coordinate within the cemetery.",
    )
    interments: tuple[RegistryInterment, ...] = Field(
        ...,
        description="Ordered tuple of one or more burials recorded in this plot.",
    )
    marker_urn: ArchivalURN | None = Field(
        default=None,
        description="Optional URN linking to a detailed CemeteryMarkerRecord.",
    )
    marker_source_id: SourceID | None = Field(
        default=None,
        description="Optional surrogate SourceID linking to a CemeteryMarkerRecord.",
    )
    condition: MarkerCondition | None = Field(
        default=None,
        description="Physical condition of the plot or monument recorded during survey.",
    )

    def __post_init__(self) -> None:
        """Enforce non-empty plot_locator and non-empty interments."""
        clean_loc = self.plot_locator.strip()
        if not clean_loc:
            raise ModelFormatError(
                "CemeteryPlotEntry 'plot_locator' cannot be empty or whitespace."
            )
        if clean_loc != self.plot_locator:
            object.__setattr__(self, "plot_locator", clean_loc)

        if not self.interments:
            raise ModelFormatError(
                f"CemeteryPlotEntry '{self.plot_locator}' requires at least one RegistryInterment."
            )

    @classmethod
    def create(
        cls,
        plot_locator: str,
        interments: list[RegistryInterment | dict[str, Any]] | tuple[RegistryInterment, ...],
        marker_urn: ArchivalURN | str | None = None,
        marker_source_id: SourceID | str | None = None,
        condition: MarkerCondition | str | None = None,
    ) -> CemeteryPlotEntry:
        """Factory constructor instantiating a validated CemeteryPlotEntry."""
        res_urn = _resolve_cemetery_urn(marker_urn) if marker_urn is not None else None
        res_sid = (
            marker_source_id
            if (marker_source_id is None or isinstance(marker_source_id, SourceID))
            else SourceID(marker_source_id)
        )
        res_cond = _parse_condition(condition) if condition is not None else None
        resolved_interments: tuple[RegistryInterment, ...] = tuple(
            i if isinstance(i, RegistryInterment) else RegistryInterment.from_dict(i)
            for i in interments
        )
        return cls(
            plot_locator=plot_locator,
            interments=resolved_interments,
            marker_urn=res_urn,
            marker_source_id=res_sid,
            condition=res_cond,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize CemeteryPlotEntry to a dictionary."""
        data: dict[str, Any] = {
            "plot_locator": self.plot_locator,
            "interments": [i.to_dict() for i in self.interments],
        }
        if self.marker_urn is not None:
            data["marker_urn"] = str(self.marker_urn)
        if self.marker_source_id is not None:
            data["marker_source_id"] = str(self.marker_source_id)
        if self.condition is not None:
            data["condition"] = self.condition.value
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CemeteryPlotEntry:
        """Deserialize a dictionary payload into a CemeteryPlotEntry."""
        if not isinstance(data, dict):
            raise ModelFormatError("CemeteryPlotEntry payload must be a dictionary.")
        loc = data.get("plot_locator")
        raw_interments = data.get("interments")
        if loc is None or raw_interments is None:
            raise ModelFormatError("CemeteryPlotEntry requires 'plot_locator' and 'interments'.")
        if not isinstance(raw_interments, (list, tuple)):
            raise ModelFormatError("CemeteryPlotEntry 'interments' must be a list or tuple.")
        return cls.create(
            plot_locator=str(loc),
            interments=list(raw_interments),
            marker_urn=data.get("marker_urn"),
            marker_source_id=data.get("marker_source_id"),
            condition=data.get("condition"),
        )

    def to_json(self) -> str:
        """Serialize CemeteryPlotEntry to a JSON formatted string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_json(cls, payload: str) -> CemeteryPlotEntry:
        """Deserialize a JSON string directly into a CemeteryPlotEntry."""
        try:
            data = json.loads(payload)
        except Exception as exc:
            raise ModelFormatError(f"Failed to parse CemeteryPlotEntry JSON string: {exc}") from exc
        return cls.from_dict(data)

    def __str__(self) -> str:
        return f"Plot {self.plot_locator} ({len(self.interments)} interments)"


@dataclass(repr=False, config=ConfigDict(kw_only=True, frozen=True, extra="forbid", strict=True))
class CemeteryRegistryRecord(SourceRecord):
    """Collection-wide cemetery plot ledger, sexton book, or grave survey container."""

    record_category: SourceRecordCategory = Field(
        default=SourceRecordCategory.CEMETERY,
        description="High-level archival domain category (restricted to CEMETERY).",
    )
    record_type: SourceRecordType = Field(
        default=SourceRecordType.REGISTER_ENTRY,
        description="Specific cemetery registry classification (REGISTER_ENTRY, CEMETERY_MARKER, MISC).",
    )
    cemetery_site_id: SiteID = Field(
        ...,
        description="Mandatory foreign key reference to the physical cemetery SiteID.",
    )
    cemetery_name_raw: str = Field(
        ...,
        description="Verbatim name of the cemetery, churchyard, or burial ground.",
    )
    plots: tuple[CemeteryPlotEntry, ...] = Field(
        ...,
        description="Ordered tuple of unique cemetery plot entries in this ledger or survey.",
    )
    location_id: LocationID | None = Field(
        default=None,
        description="Resolved canonical LocationID for the cemetery's civil jurisdiction.",
    )
    sexton_or_custodian: str | None = Field(
        default=None,
        description="Name of the sexton, superintendent, or historical society compiler.",
    )
    survey_date: EventDate | None = Field(
        default=None,
        description="Date the sexton book was compiled or the grave survey was conducted.",
    )

    ALLOWED_RECORD_TYPES: ClassVar[frozenset[SourceRecordType]] = _REGISTRY_RECORD_TYPES

    def __post_init__(self) -> None:
        """Enforce category, record_type, cemetery name, and unique plot_locator values."""
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

        if not self.plots:
            raise ModelFormatError(
                f"{self.__class__.__name__} requires at least one CemeteryPlotEntry."
            )

        seen_plots: set[str] = set()
        for plot in self.plots:
            if plot.plot_locator in seen_plots:
                raise ModelFormatError(
                    f"Duplicate CemeteryPlotEntry plot_locator '{plot.plot_locator}' within registry."
                )
            seen_plots.add(plot.plot_locator)

    @property
    def plot_count(self) -> int:
        """Return total number of plots in this cemetery registry."""
        return len(self.plots)

    @property
    def total_interment_count(self) -> int:
        """Return total number of interments across all plots in this registry."""
        return sum(len(plot.interments) for plot in self.plots)

    def get_plot(self, plot_locator: str) -> CemeteryPlotEntry | None:
        """Retrieve a plot entry by its plot_locator coordinate."""
        target = plot_locator.strip()
        for plot in self.plots:
            if plot.plot_locator == target:
                return plot
        return None

    def flatten_interments(self) -> tuple[dict[str, Any], ...]:
        """Flatten registry and plot context with every interment for collection-wide indexing."""
        rows: list[dict[str, Any]] = []
        base_header: dict[str, Any] = {
            "source_id": str(self.source_id),
            "source_urn": str(self.source_urn),
            "record_category": self.record_category.value,
            "record_type": self.record_type.value,
            "cemetery_site_id": str(self.cemetery_site_id),
            "cemetery_name_raw": self.cemetery_name_raw,
            "location_id": str(self.location_id) if self.location_id else None,
        }
        for plot in self.plots:
            plot_ctx = {
                **base_header,
                "plot_locator": plot.plot_locator,
                "marker_urn": str(plot.marker_urn) if plot.marker_urn else None,
                "marker_source_id": str(plot.marker_source_id) if plot.marker_source_id else None,
                "condition": plot.condition.value if plot.condition else None,
            }
            for interment in plot.interments:
                rows.append({**plot_ctx, **interment.to_dict()})
        return tuple(rows)

    @classmethod
    def create(  # type: ignore[override]
        cls,
        source_id: SourceID | str,
        source_urn: ArchivalURN | str,
        description: str,
        repository_id: RepositoryID | str,
        cemetery_site_id: SiteID | str,
        cemetery_name_raw: str,
        plots: list[CemeteryPlotEntry | dict[str, Any]] | tuple[CemeteryPlotEntry, ...],
        record_type: SourceRecordType | str = SourceRecordType.REGISTER_ENTRY,
        location_id: LocationID | str | None = None,
        sexton_or_custodian: str | None = None,
        survey_date: EventDate | dict[str, Any] | str | None = None,
        audit: AuditStamp | None = None,
        media_ids: list[MediaID | str] | None = None,
        associated_people: list[AssociatedIndividual] | None = None,
        tombstone: Tombstone[SourceID] | None = None,
    ) -> CemeteryRegistryRecord:
        """Factory constructor instantiating a validated CemeteryRegistryRecord."""
        resolved_sid = source_id if isinstance(source_id, SourceID) else SourceID(source_id)
        resolved_urn = _resolve_cemetery_urn(source_urn)
        resolved_rep = (
            repository_id
            if isinstance(repository_id, RepositoryID)
            else RepositoryID(repository_id)
        )
        res_site = (
            cemetery_site_id if isinstance(cemetery_site_id, SiteID) else SiteID(cemetery_site_id)
        )
        res_type = (
            record_type
            if isinstance(record_type, SourceRecordType)
            else SourceRecordType(str(record_type).strip().upper())
        )
        res_loc = (
            location_id
            if (location_id is None or isinstance(location_id, LocationID))
            else LocationID(location_id)
        )
        res_survey = (
            _deserialize_event_date(survey_date, "survey_date") if survey_date is not None else None
        )

        resolved_plots: tuple[CemeteryPlotEntry, ...] = tuple(
            p if isinstance(p, CemeteryPlotEntry) else CemeteryPlotEntry.from_dict(p) for p in plots
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
            cemetery_site_id=res_site,
            cemetery_name_raw=cemetery_name_raw,
            plots=resolved_plots,
            location_id=res_loc,
            sexton_or_custodian=sexton_or_custodian,
            survey_date=res_survey,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize CemeteryRegistryRecord to a dictionary."""
        data = super().to_dict()
        data.update(
            {
                "record_type": self.record_type.value,
                "cemetery_site_id": str(self.cemetery_site_id),
                "cemetery_name_raw": self.cemetery_name_raw,
                "plots": [p.to_dict() for p in self.plots],
            }
        )
        if self.location_id is not None:
            data["location_id"] = str(self.location_id)
        if self.sexton_or_custodian is not None:
            data["sexton_or_custodian"] = self.sexton_or_custodian
        if self.survey_date is not None:
            data["survey_date"] = self.survey_date.to_dict()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CemeteryRegistryRecord:
        """Deserialize a dictionary payload into a CemeteryRegistryRecord."""
        if not isinstance(data, dict):
            raise ModelFormatError("CemeteryRegistryRecord payload must be a dictionary.")

        sid = data.get("source_id")
        raw_urn = data.get("source_urn")
        desc = data.get("description")
        rep = data.get("repository_id")
        audit_payload = data.get("audit")
        site_id = data.get("cemetery_site_id")
        cem_name = data.get("cemetery_name_raw")
        raw_plots = data.get("plots")

        if not all((sid, raw_urn, desc, rep, audit_payload, site_id, cem_name, raw_plots)):
            raise ModelFormatError(
                "CemeteryRegistryRecord requires source_id, source_urn, description, repository_id, "
                "audit, cemetery_site_id, cemetery_name_raw, and plots."
            )

        raw_cat = data.get("record_category", SourceRecordCategory.CEMETERY.value)
        if str(raw_cat).strip().upper() != SourceRecordCategory.CEMETERY.value:
            raise ModelFormatError(
                f"CemeteryRegistryRecord requires record_category CEMETERY, got '{raw_cat}'."
            )

        if not isinstance(raw_plots, (list, tuple)):
            raise ModelFormatError("CemeteryRegistryRecord 'plots' must be a list or tuple.")

        if isinstance(audit_payload, AuditStamp):
            audit_obj = audit_payload
        elif isinstance(audit_payload, dict):
            audit_obj = AuditStamp(
                created_at=IsoTimestamp(audit_payload["created_at"]),
                updated_at=IsoTimestamp(audit_payload["updated_at"]),
            )
        else:
            raise ModelFormatError(
                "CemeteryRegistryRecord audit must be an AuditStamp or dictionary."
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
            cemetery_site_id=str(site_id),
            cemetery_name_raw=str(cem_name),
            plots=list(raw_plots),
            record_type=data.get("record_type", SourceRecordType.REGISTER_ENTRY),
            location_id=data.get("location_id"),
            sexton_or_custodian=data.get("sexton_or_custodian"),
            survey_date=data.get("survey_date"),
            audit=audit_obj,
            media_ids=data.get("media_ids", []),
            associated_people=[
                AssociatedIndividual.from_dict(p) for p in data.get("associated_people", [])
            ],
            tombstone=tombstone_obj,
        )

    def __str__(self) -> str:
        return (
            f"CemeteryRegistryRecord [{self.cemetery_name_raw}] "
            f"({self.plot_count} plots, {self.total_interment_count} interments)"
        )
