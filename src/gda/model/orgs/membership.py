"""Path: src/gda/model/orgs/membership.py

Evidentiary record models for individual organization memberships and affiliations.

Operational Role:
    Defines OrganizationMembershipRecord extending SourceRecord to capture primary
    documentary evidence of an individual's participation, initiation, ordination,
    office-holding, or membership standing within a voluntary association,
    religious congregation, fraternal lodge, choir, or civic society.
"""

from __future__ import annotations

from typing import Any, ClassVar

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.enums.orgs import AffiliationType, MembershipStatus, OrganizationCategory
from gda.core.enums.sources import SourceRecordCategory, SourceRecordType
from gda.core.errors import ModelFormatError
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import IndividualID, MediaID, OrganizationID, RepositoryID, SourceID
from gda.model.atom.urn import ArchivalURN, SourceURN
from gda.model.base.association import AssociatedIndividual
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate, TimePeriod
from gda.model.base.source import SourceRecord
from gda.model.base.tombstone import Tombstone

__version__ = "1.0.0+build.1"

__all__ = [
    "OrganizationMembershipRecord",
]

_ORG_SOURCE_CATEGORIES: frozenset[SourceRecordCategory] = frozenset(
    {
        SourceRecordCategory.FRATERNAL,
        SourceRecordCategory.CHURCH,
        SourceRecordCategory.CIVIC,
        SourceRecordCategory.EDUCATION,
        SourceRecordCategory.MILITARY,
        SourceRecordCategory.OTHER,
    }
)


@dataclass(repr=False, config=ConfigDict(kw_only=True, frozen=True, extra="forbid", strict=True))
class OrganizationMembershipRecord(SourceRecord):
    """Primary archival record documenting an individual's organizational affiliation."""

    record_category: SourceRecordCategory = Field(
        default=SourceRecordCategory.FRATERNAL,
        description="High-level archival domain category (FRATERNAL, CHURCH, CIVIC, etc.).",
    )
    record_type: SourceRecordType = Field(
        default=SourceRecordType.LODGE_RECORD,
        description="Specific documentary record type (e.g., LODGE_RECORD, BAPTISM_REGISTER).",
    )
    individual_id: IndividualID = Field(
        ...,
        description="Canonical IndividualID of the member or participant.",
    )
    organization_name_raw: str = Field(
        ...,
        description="Verbatim organization, lodge, choir, or congregation name on the source.",
    )
    org_id: OrganizationID | None = Field(
        default=None,
        description="Resolved canonical OrganizationID if linked to a master Organization entity.",
    )
    org_category: OrganizationCategory = Field(
        default=OrganizationCategory.OTHER,
        description="Taxonomic classification of the organization.",
    )
    affiliation_type: AffiliationType = Field(
        default=AffiliationType.MEMBER,
        description="Functional capacity in which the individual participated.",
    )
    membership_status: MembershipStatus = Field(
        default=MembershipStatus.ACTIVE,
        description="Standing or lifecycle status recorded on the document.",
    )
    role_or_title_raw: str | None = Field(
        default=None,
        description="Verbatim office, voice part, or title (e.g., 'Worshipful Master', 'First Tenor').",
    )
    degree_or_rank_raw: str | None = Field(
        default=None,
        description="Verbatim fraternal degree, ecclesiastical order, or rank (e.g., 'Master Mason').",
    )
    membership_period: TimePeriod | None = Field(
        default=None,
        description="Structured temporal span covering initiation/admission through demit/exit.",
    )
    dues_or_contribution_raw: str | None = Field(
        default=None,
        description="Verbatim dues, initiation fee, or pledge notation recorded on the ledger.",
    )

    ALLOWED_CATEGORIES: ClassVar[frozenset[SourceRecordCategory]] = _ORG_SOURCE_CATEGORIES

    def __post_init__(self) -> None:
        """Enforce category bounds and verbatim organization name hygiene."""
        super().__post_init__()

        if self.record_category not in self.ALLOWED_CATEGORIES:
            raise ModelFormatError(
                f"{self.__class__.__name__} requires record_category in "
                f"{sorted(c.value for c in self.ALLOWED_CATEGORIES)}, "
                f"got '{self.record_category.value}'."
            )

        clean_org_name = self.organization_name_raw.strip()
        if not clean_org_name:
            raise ModelFormatError(
                f"{self.__class__.__name__} 'organization_name_raw' cannot be empty or whitespace."
            )
        if clean_org_name != self.organization_name_raw:
            object.__setattr__(self, "organization_name_raw", clean_org_name)

    @property
    def date_joined(self) -> EventDate | None:
        """Convenience accessor for initiation/admission date from membership_period."""
        return self.membership_period.start_date if self.membership_period is not None else None

    @property
    def date_ended(self) -> EventDate | None:
        """Convenience accessor for demit/termination date from membership_period."""
        return self.membership_period.end_date if self.membership_period is not None else None

    @classmethod
    def create(  # type: ignore[override]
        cls,
        source_id: SourceID | str,
        source_urn: ArchivalURN | str,
        description: str,
        repository_id: RepositoryID | str,
        individual_id: IndividualID | str,
        organization_name_raw: str,
        record_category: SourceRecordCategory | str = SourceRecordCategory.FRATERNAL,
        record_type: SourceRecordType | str = SourceRecordType.LODGE_RECORD,
        org_id: OrganizationID | str | None = None,
        org_category: OrganizationCategory | str = OrganizationCategory.OTHER,
        affiliation_type: AffiliationType | str = AffiliationType.MEMBER,
        membership_status: MembershipStatus | str = MembershipStatus.ACTIVE,
        role_or_title_raw: str | None = None,
        degree_or_rank_raw: str | None = None,
        membership_period: TimePeriod | None = None,
        dues_or_contribution_raw: str | None = None,
        audit: AuditStamp | None = None,
        media_ids: list[MediaID | str] | None = None,
        associated_people: list[AssociatedIndividual] | None = None,
        tombstone: Tombstone[SourceID] | None = None,
    ) -> OrganizationMembershipRecord:
        """Factory constructor instantiating a validated OrganizationMembershipRecord."""
        resolved_sid = source_id if isinstance(source_id, SourceID) else SourceID(source_id)
        resolved_urn = (
            source_urn if isinstance(source_urn, ArchivalURN) else SourceURN(str(source_urn))
        )
        resolved_rep = (
            repository_id
            if isinstance(repository_id, RepositoryID)
            else RepositoryID(repository_id)
        )
        resolved_ind = (
            individual_id
            if isinstance(individual_id, IndividualID)
            else IndividualID(individual_id)
        )
        resolved_org_id = (
            org_id
            if (org_id is None or isinstance(org_id, OrganizationID))
            else OrganizationID(org_id)
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
        res_org_cat = (
            org_category
            if isinstance(org_category, OrganizationCategory)
            else OrganizationCategory(str(org_category).strip().upper())
        )
        res_aff = (
            affiliation_type
            if isinstance(affiliation_type, AffiliationType)
            else AffiliationType(str(affiliation_type).strip().upper())
        )
        res_status = (
            membership_status
            if isinstance(membership_status, MembershipStatus)
            else MembershipStatus(str(membership_status).strip().upper())
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
            individual_id=resolved_ind,
            organization_name_raw=organization_name_raw,
            org_id=resolved_org_id,
            org_category=res_org_cat,
            affiliation_type=res_aff,
            membership_status=res_status,
            role_or_title_raw=role_or_title_raw,
            degree_or_rank_raw=degree_or_rank_raw,
            membership_period=membership_period,
            dues_or_contribution_raw=dues_or_contribution_raw,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize OrganizationMembershipRecord to a dictionary."""
        data = super().to_dict()
        data.update(
            {
                "record_type": self.record_type.value,
                "individual_id": str(self.individual_id),
                "organization_name_raw": self.organization_name_raw,
                "org_category": self.org_category.value,
                "affiliation_type": self.affiliation_type.value,
                "membership_status": self.membership_status.value,
            }
        )
        if self.org_id is not None:
            data["org_id"] = str(self.org_id)
        if self.role_or_title_raw is not None:
            data["role_or_title_raw"] = self.role_or_title_raw
        if self.degree_or_rank_raw is not None:
            data["degree_or_rank_raw"] = self.degree_or_rank_raw
        if self.membership_period is not None:
            data["membership_period"] = self.membership_period.to_dict()
        if self.dues_or_contribution_raw is not None:
            data["dues_or_contribution_raw"] = self.dues_or_contribution_raw
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> OrganizationMembershipRecord:
        """Deserialize a dictionary payload into an OrganizationMembershipRecord."""
        if not isinstance(data, dict):
            raise ModelFormatError("OrganizationMembershipRecord payload must be a dictionary.")

        sid = data.get("source_id")
        raw_urn = data.get("source_urn")
        desc = data.get("description")
        rep = data.get("repository_id")
        audit_payload = data.get("audit")
        ind_id = data.get("individual_id")
        org_name = data.get("organization_name_raw")

        if not all((sid, raw_urn, desc, rep, audit_payload, ind_id, org_name)):
            raise ModelFormatError(
                "OrganizationMembershipRecord requires source_id, source_urn, description, "
                "repository_id, audit, individual_id, and organization_name_raw."
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
                "OrganizationMembershipRecord audit must be an AuditStamp or dictionary."
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

        raw_period = data.get("membership_period")
        resolved_period: TimePeriod | None = None
        if isinstance(raw_period, TimePeriod):
            resolved_period = raw_period
        elif isinstance(raw_period, dict) and (
            raw_period.get("start_date") is not None or raw_period.get("end_date") is not None
        ):
            resolved_period = TimePeriod.from_dict(raw_period)

        return cls.create(
            source_id=str(sid),
            source_urn=str(raw_urn),
            description=str(desc),
            repository_id=str(rep),
            individual_id=str(ind_id),
            organization_name_raw=str(org_name),
            record_category=data.get("record_category", SourceRecordCategory.FRATERNAL),
            record_type=data.get("record_type", SourceRecordType.LODGE_RECORD),
            org_id=data.get("org_id"),
            org_category=data.get("org_category", OrganizationCategory.OTHER),
            affiliation_type=data.get("affiliation_type", AffiliationType.MEMBER),
            membership_status=data.get("membership_status", MembershipStatus.ACTIVE),
            role_or_title_raw=data.get("role_or_title_raw"),
            degree_or_rank_raw=data.get("degree_or_rank_raw"),
            membership_period=resolved_period,
            dues_or_contribution_raw=data.get("dues_or_contribution_raw"),
            audit=audit_obj,
            media_ids=data.get("media_ids", []),
            associated_people=[
                AssociatedIndividual.from_dict(p) for p in data.get("associated_people", [])
            ],
            tombstone=tombstone_obj,
        )

    def __str__(self) -> str:
        return (
            f"Membership [{self.organization_name_raw}] "
            f"{self.individual_id} ({self.membership_status.value})"
        )
