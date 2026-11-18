"""Path: src/gda/model/xref/individual_organization_xref.py

Cross-reference bridge and index model linking institutional organizations to affiliated individuals.

Operational Role:
    Defines IndividualOrganizationXRef (frozen Pydantic dataclass) as a derived
    relational index row linking an active OrganizationID ('ORG-######') to an
    affiliated IndividualID ('IND-######'), capturing OrganizationCategory,
    AffiliationType, MembershipStatus, optional start_year and end_year
    HistoricalYear bounds, chronological span validation, and direct construction
    from an active Organization entity via from_organization().
"""

from __future__ import annotations

import json
from functools import total_ordering
from typing import Any

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.enums.orgs import (
    AffiliationType,
    MembershipStatus,
    OrganizationCategory,
)
from gda.core.errors import ModelFormatError, ModelRangeError
from gda.core.introspectable import IntrospectableMixin
from gda.model.atom.id import IndividualID, OrganizationID
from gda.model.atom.year import HistoricalYear
from gda.model.entity.organization import Organization
from gda.util.enums import coerce_enum

__version__ = "1.0.0+build.2"

__all__ = [
    "IndividualOrganizationXRef",
]


def _parse_org_category(raw: OrganizationCategory | str) -> OrganizationCategory:
    """Resolve OrganizationCategory by enum instance, exact value, or uppercase member name."""
    try:
        return coerce_enum(OrganizationCategory, raw, field_name="org_category")
    except ModelFormatError as err:
        raise ModelFormatError(f"Invalid OrganizationCategory value: '{raw}'.") from err


def _parse_affiliation_type(raw: AffiliationType | str) -> AffiliationType:
    """Resolve AffiliationType by enum instance, exact value, or uppercase member name."""
    try:
        return coerce_enum(AffiliationType, raw, field_name="affiliation_type")
    except ModelFormatError as err:
        raise ModelFormatError(f"Invalid AffiliationType value: '{raw}'.") from err


def _parse_membership_status(raw: MembershipStatus | str) -> MembershipStatus:
    """Resolve MembershipStatus by enum instance, exact value, or uppercase member name."""
    try:
        return coerce_enum(MembershipStatus, raw, field_name="membership_status")
    except ModelFormatError as err:
        raise ModelFormatError(f"Invalid MembershipStatus value: '{raw}'.") from err


def _resolve_year(raw: HistoricalYear | int | None) -> HistoricalYear | None:
    """Resolve HistoricalYear instance, strict integer year, or None."""
    if raw is None or isinstance(raw, HistoricalYear):
        return raw
    return HistoricalYear(raw)


@total_ordering
@dataclass(
    repr=False,
    config=ConfigDict(frozen=True, extra="forbid", strict=True),
    kw_only=True,
)
class IndividualOrganizationXRef(IntrospectableMixin):
    """Immutable derived index row linking an OrganizationID to an affiliated IndividualID."""

    organization_id: OrganizationID = Field(
        ...,
        description="Canonical OrganizationID ('ORG-######') of the institution or society.",
    )
    individual_id: IndividualID = Field(
        ...,
        description="Canonical IndividualID ('IND-######') of the affiliated person.",
    )
    org_category: OrganizationCategory = Field(
        ...,
        description="Denormalized OrganizationCategory for institutional filtering.",
    )
    affiliation_type: AffiliationType = Field(
        default=AffiliationType.MEMBER,
        description="Standardized functional role or affiliation capacity within the organization.",
    )
    membership_status: MembershipStatus = Field(
        default=MembershipStatus.ACTIVE,
        description="Standing or lifecycle status of the affiliation.",
    )
    start_year: HistoricalYear | None = Field(
        default=None,
        description="Optional validated 4-digit calendar year (1000..2100) marking affiliation start.",
    )
    end_year: HistoricalYear | None = Field(
        default=None,
        description="Optional validated 4-digit calendar year (1000..2100) marking affiliation end.",
    )

    def __post_init__(self) -> None:
        """Enforce chronological boundary guards when both start_year and end_year are present."""
        if (
            self.start_year is not None
            and self.end_year is not None
            and int(self.end_year) < int(self.start_year)
        ):
            raise ModelRangeError(
                f"Affiliation end_year ({int(self.end_year)}) cannot precede start_year ({int(self.start_year)}).",
                details={
                    "start_year": int(self.start_year),
                    "end_year": int(self.end_year),
                },
            )

    @property
    def xref_key(self) -> str:
        """Return dynamic compound index key '<organization_id>::<individual_id>::<affiliation_type>'."""
        return (
            f"{self.organization_id.value}::"
            f"{self.individual_id.value}::"
            f"{self.affiliation_type.value}"
        )

    @property
    def sort_key(self) -> tuple[str, int, int, str, str]:
        """Return deterministic ordering tuple (organization_id, start_year, end_year, individual_id, affiliation_type)."""
        s_yr = int(self.start_year) if self.start_year is not None else 9999
        e_yr = int(self.end_year) if self.end_year is not None else 9999
        return (
            self.organization_id.value,
            s_yr,
            e_yr,
            self.individual_id.value,
            self.affiliation_type.value,
        )

    @classmethod
    def create(
        cls,
        organization_id: OrganizationID | str,
        individual_id: IndividualID | str,
        org_category: OrganizationCategory | str,
        affiliation_type: AffiliationType | str = AffiliationType.MEMBER,
        membership_status: MembershipStatus | str = MembershipStatus.ACTIVE,
        start_year: HistoricalYear | int | None = None,
        end_year: HistoricalYear | int | None = None,
    ) -> IndividualOrganizationXRef:
        """Factory constructor instantiating a validated IndividualOrganizationXRef."""
        res_org = (
            organization_id
            if isinstance(organization_id, OrganizationID)
            else OrganizationID(str(organization_id).strip().upper())
        )
        res_ind = (
            individual_id
            if isinstance(individual_id, IndividualID)
            else IndividualID(str(individual_id).strip().upper())
        )
        res_cat = _parse_org_category(org_category)
        res_aff = _parse_affiliation_type(affiliation_type)
        res_status = _parse_membership_status(membership_status)
        res_start = _resolve_year(start_year)
        res_end = _resolve_year(end_year)

        return cls(
            organization_id=res_org,
            individual_id=res_ind,
            org_category=res_cat,
            affiliation_type=res_aff,
            membership_status=res_status,
            start_year=res_start,
            end_year=res_end,
        )

    @classmethod
    def from_organization(
        cls,
        organization: Organization,
        individual_id: IndividualID | str,
        affiliation_type: AffiliationType | str = AffiliationType.MEMBER,
        membership_status: MembershipStatus | str = MembershipStatus.ACTIVE,
        start_year: HistoricalYear | int | None = None,
        end_year: HistoricalYear | int | None = None,
    ) -> IndividualOrganizationXRef:
        """Construct an IndividualOrganizationXRef directly from an active Organization entity."""
        if not isinstance(organization, Organization):
            raise ModelFormatError(
                "IndividualOrganizationXRef.from_organization requires an Organization entity."
            )
        if organization.is_deprecated:
            raise ModelFormatError(
                f"Cannot index deprecated Organization '{organization.id.value}'."
            )
        return cls.create(
            organization_id=organization.id,
            individual_id=individual_id,
            org_category=organization.category,
            affiliation_type=affiliation_type,
            membership_status=membership_status,
            start_year=start_year,
            end_year=end_year,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize IndividualOrganizationXRef to a dictionary."""
        data: dict[str, Any] = {
            "organization_id": self.organization_id.value,
            "individual_id": self.individual_id.value,
            "org_category": self.org_category.value,
            "affiliation_type": self.affiliation_type.value,
            "membership_status": self.membership_status.value,
        }
        if self.start_year is not None:
            data["start_year"] = int(self.start_year)
        if self.end_year is not None:
            data["end_year"] = int(self.end_year)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> IndividualOrganizationXRef:
        """Deserialize a dictionary payload into an IndividualOrganizationXRef."""
        if not isinstance(data, dict):
            raise ModelFormatError("IndividualOrganizationXRef payload must be a dictionary.")

        oid = data.get("organization_id")
        iid = data.get("individual_id")
        cat = data.get("org_category")

        if not oid or not iid or not cat:
            raise ModelFormatError(
                "IndividualOrganizationXRef requires 'organization_id', 'individual_id', and 'org_category'."
            )

        return cls.create(
            organization_id=oid,
            individual_id=iid,
            org_category=cat,
            affiliation_type=data.get("affiliation_type", AffiliationType.MEMBER),
            membership_status=data.get("membership_status", MembershipStatus.ACTIVE),
            start_year=data.get("start_year"),
            end_year=data.get("end_year"),
        )

    def to_json(self) -> str:
        """Serialize IndividualOrganizationXRef to a JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True)

    @classmethod
    def from_json(cls, payload: str) -> IndividualOrganizationXRef:
        """Deserialize a JSON string into an IndividualOrganizationXRef."""
        try:
            data = json.loads(payload)
        except Exception as exc:
            raise ModelFormatError(
                f"Failed to parse IndividualOrganizationXRef JSON: {exc}"
            ) from exc
        return cls.from_dict(data)

    def __lt__(self, other: object) -> bool:
        """Compare IndividualOrganizationXRef instances by sort_key."""
        if not isinstance(other, IndividualOrganizationXRef):
            return NotImplemented
        return self.sort_key < other.sort_key

    def __str__(self) -> str:
        """Return concise human-readable string representation."""
        span = ""
        if self.start_year is not None or self.end_year is not None:
            s_str = str(int(self.start_year)) if self.start_year is not None else "?"
            e_str = str(int(self.end_year)) if self.end_year is not None else "?"
            span = f" [{s_str}-{e_str}]"
        return (
            f"IndividualOrganizationXRef [{self.xref_key}] "
            f"({self.org_category.value}/{self.membership_status.value}){span}"
        )

    def __repr__(self) -> str:
        return (
            f"IndividualOrganizationXRef(organization_id={self.organization_id!r}, "
            f"individual_id={self.individual_id!r}, org_category={self.org_category!r}, "
            f"affiliation_type={self.affiliation_type!r}, "
            f"membership_status={self.membership_status!r})"
        )
