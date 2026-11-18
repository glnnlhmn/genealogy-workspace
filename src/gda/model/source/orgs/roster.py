"""Path: src/gda/model/source/orgs/roster.py

Tabulated organization roster, lodge directory, and society roll domain models.

Operational Role:
    Defines OrganizationRosterEntry (single member row on a printed or manuscript
    roster page) and OrganizationRosterRecord (extending EnumeratedRollRecord) for
    multi-member society directories, lodge rosters, choir rolls, and church
    membership lists.
"""

from __future__ import annotations

import dataclasses
import json
from typing import Any, ClassVar, Self

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.enums.orgs import AffiliationType, MembershipStatus, OrganizationCategory
from gda.core.enums.sources import SourceRecordCategory, SourceRecordType
from gda.core.errors import ModelFormatError
from gda.core.introspectable import IntrospectableMixin
from gda.core.types import MAX_CENSUS_LINE_NUMBER
from gda.model.atom.id import IndividualID, OrganizationID, SourceID
from gda.model.atom.urn import SourceURN
from gda.model.source.enumerated.base import (
    EnumeratedRollRecord,
    coerce_field_value,
    serialize_primitive_value,
)
from gda.util.enums import coerce_enum

__version__ = "1.0.0+build.3"

__all__ = [
    "OrganizationRosterEntry",
    "OrganizationRosterRecord",
]

_ROSTER_CATEGORIES: frozenset[SourceRecordCategory] = frozenset(
    {
        SourceRecordCategory.FRATERNAL,
        SourceRecordCategory.CHURCH,
        SourceRecordCategory.CIVIC,
        SourceRecordCategory.EDUCATION,
        SourceRecordCategory.MILITARY,
        SourceRecordCategory.OTHER,
    }
)

_ROSTER_RECORD_TYPES: frozenset[SourceRecordType] = frozenset(
    {
        SourceRecordType.MEMBERSHIP_ROSTER,
        SourceRecordType.LODGE_RECORD,
        SourceRecordType.CLASS_ROSTER,
    }
)


def _coerce_org_field(field_name: str, field_type_str: str, value: Any) -> Any:
    """Coerce organization-specific atoms/enums before delegating to generic field coercion."""
    if value is None:
        return None
    if field_name == "entry_urn":
        return value if isinstance(value, SourceURN) else SourceURN(str(value))
    if field_name == "org_id":
        return value if isinstance(value, OrganizationID) else OrganizationID(str(value))
    if field_name == "org_category":
        return coerce_enum(OrganizationCategory, value, field_name="org_category")
    if field_name == "affiliation_type":
        return coerce_enum(AffiliationType, value, field_name="affiliation_type")
    if field_name == "membership_status":
        return coerce_enum(MembershipStatus, value, field_name="membership_status")
    return coerce_field_value(field_type_str, value)


@dataclass(
    repr=False,
    config=ConfigDict(frozen=True, extra="forbid", strict=True),
    kw_only=True,
)
class OrganizationRosterEntry(IntrospectableMixin):
    """Single enumerated member row on an organization roster or society directory page."""

    entry_urn: SourceURN = Field(
        ...,
        description="Mandatory canonical SourceURN uniquely identifying this roster row.",
    )
    entry_id: SourceID | None = Field(
        default=None,
        description="Optional surrogate UUIDv4 SourceID GUID for direct row lookup.",
    )
    line_number: int = Field(
        ...,
        ge=1,
        le=MAX_CENSUS_LINE_NUMBER,
        description="Enumerated line or sequence number on the roster page.",
    )
    member_name_verbatim: str = Field(
        ...,
        description="Verbatim transcribed name of the listed member or officer.",
    )
    individual_id: IndividualID | None = Field(
        default=None,
        description="Resolved canonical IndividualID if linked to a person entity.",
    )
    affiliation_type: AffiliationType = Field(
        default=AffiliationType.MEMBER,
        description="Functional capacity in which the member appears on the roster.",
    )
    membership_status: MembershipStatus = Field(
        default=MembershipStatus.ACTIVE,
        description="Standing or lifecycle status indicated on the roster.",
    )
    role_or_title_raw: str | None = Field(
        default=None,
        description="Verbatim office, committee, or voice part listed next to the member.",
    )
    degree_or_rank_raw: str | None = Field(
        default=None,
        description="Verbatim degree, rank, or class designation listed on the roster.",
    )
    admission_date_raw: str | None = Field(
        default=None,
        description="Verbatim initiation, admission, or class year notation.",
    )
    residence_raw: str | None = Field(
        default=None,
        description="Verbatim street address or town printed in the society roster.",
    )
    remarks_raw: str | None = Field(
        default=None,
        description="Verbatim marginalia, demit/death annotations, or committee notes.",
    )

    def __post_init__(self) -> None:
        """Enforce non-empty verbatim member name hygiene."""
        cleaned = self.member_name_verbatim.strip()
        if not cleaned:
            raise ModelFormatError(
                "OrganizationRosterEntry 'member_name_verbatim' cannot be empty or whitespace.",
                details={"entry_urn": str(self.entry_urn), "line_number": self.line_number},
            )
        if cleaned != self.member_name_verbatim:
            object.__setattr__(self, "member_name_verbatim", cleaned)

    def to_dict(self) -> dict[str, Any]:
        """Serialize OrganizationRosterEntry fields to a dictionary."""
        return {
            f.name: serialize_primitive_value(getattr(self, f.name))
            for f in dataclasses.fields(self)
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Deserialize a dictionary payload into an immutable OrganizationRosterEntry."""
        if not isinstance(data, dict):
            raise ModelFormatError(f"{cls.__name__} payload must be a dictionary.")

        kwargs: dict[str, Any] = {}
        for f in dataclasses.fields(cls):
            if f.name not in data:
                continue
            kwargs[f.name] = _coerce_org_field(f.name, str(f.type), data[f.name])
        return cls(**kwargs)

    def to_json(self) -> str:
        """Serialize entry to a JSON formatted string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_json(cls, payload: str) -> Self:
        """Deserialize a JSON string directly into an OrganizationRosterEntry."""
        try:
            data = json.loads(payload)
        except Exception as exc:
            raise ModelFormatError(f"Failed to parse {cls.__name__} JSON string: {exc}") from exc
        return cls.from_dict(data)

    def __str__(self) -> str:
        return f"Line {self.line_number}: {self.member_name_verbatim} ({self.entry_urn})"

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(line_number={self.line_number!r}, "
            f"member_name_verbatim={self.member_name_verbatim!r}, entry_urn={self.entry_urn!r})"
        )


@dataclass(
    repr=False,
    config=ConfigDict(frozen=True, extra="forbid", strict=True),
    kw_only=True,
)
class OrganizationRosterRecord(EnumeratedRollRecord):
    """Evidentiary composite representing a printed or manuscript organization roster page."""

    record_category: SourceRecordCategory = Field(
        default=SourceRecordCategory.FRATERNAL,
        description="High-level archival domain category (FRATERNAL, CHURCH, CIVIC, etc.).",
    )
    record_type: SourceRecordType = Field(
        default=SourceRecordType.MEMBERSHIP_ROSTER,
        description="Specific roster document type (MEMBERSHIP_ROSTER, LODGE_RECORD, CLASS_ROSTER).",
    )
    organization_name_raw: str = Field(
        ...,
        description="Verbatim organization, lodge, choir, or congregation heading on the roster.",
    )
    org_id: OrganizationID | None = Field(
        default=None,
        description="Resolved canonical OrganizationID if linked to a master Organization entity.",
    )
    org_category: OrganizationCategory = Field(
        default=OrganizationCategory.OTHER,
        description="Taxonomic classification of the organization.",
    )
    roster_title: str | None = Field(
        default=None,
        description="Heading or section title (e.g., 'Officers and Past Masters', 'Roll of Communicants').",
    )
    page_number: str | None = Field(
        default=None,
        description="Printed page or folio designation in the roster booklet or register.",
    )
    entries: tuple[OrganizationRosterEntry, ...] = Field(
        ...,
        min_length=1,
        description="Immutable ordered tuple of enumerated member entries on this roster page.",
    )

    ALLOWED_CATEGORIES: ClassVar[frozenset[SourceRecordCategory]] = _ROSTER_CATEGORIES
    ALLOWED_RECORD_TYPES: ClassVar[frozenset[SourceRecordType]] = _ROSTER_RECORD_TYPES

    def __post_init__(self) -> None:
        """Enforce category/type bounds, organization heading hygiene, and row uniqueness."""
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

        clean_org_name = self.organization_name_raw.strip()
        if not clean_org_name:
            raise ModelFormatError(
                f"{self.__class__.__name__} 'organization_name_raw' cannot be empty or whitespace."
            )
        if clean_org_name != self.organization_name_raw:
            object.__setattr__(self, "organization_name_raw", clean_org_name)

        self._validate_unique_entries()

    def _validate_unique_entries(self) -> None:
        """Enforce unique entry_urn, unique non-null entry_id GUID, and unique line_number."""
        seen_urns: set[str] = set()
        seen_ids: set[str] = set()
        seen_lines: set[int] = set()

        for entry in self.entries:
            urn_str = str(entry.entry_urn)
            if urn_str in seen_urns:
                raise ModelFormatError(
                    f"Duplicate OrganizationRosterEntry entry_urn '{urn_str}' within roster."
                )
            seen_urns.add(urn_str)

            if entry.entry_id is not None:
                id_str = str(entry.entry_id)
                if id_str in seen_ids:
                    raise ModelFormatError(
                        f"Duplicate OrganizationRosterEntry entry_id '{id_str}' within roster."
                    )
                seen_ids.add(id_str)

            if entry.line_number in seen_lines:
                raise ModelFormatError(
                    f"Duplicate OrganizationRosterEntry line_number {entry.line_number} within roster."
                )
            seen_lines.add(entry.line_number)

    @property
    def entry_count(self) -> int:
        """Return the count of populated member entries on this roster page."""
        return len(self.entries)

    def get_entry(self, identifier: SourceURN | SourceID | str) -> OrganizationRosterEntry | None:
        """Retrieve a roster entry by either its SourceURN or its SourceID GUID."""
        target = str(identifier).strip()
        if not target:
            return None

        for entry in self.entries:
            if str(entry.entry_urn) == target:
                return entry
            if entry.entry_id is not None and str(entry.entry_id) == target:
                return entry
        return None

    def require_entry(self, identifier: SourceURN | SourceID | str) -> OrganizationRosterEntry:
        """Retrieve a roster entry by URN or GUID, raising ModelFormatError if absent."""
        found = self.get_entry(identifier)
        if found is None:
            raise ModelFormatError(
                f"No roster entry matching identifier '{identifier}' in {self.source_urn}.",
                details={"identifier": str(identifier), "source_urn": str(self.source_urn)},
            )
        return found

    def flatten_entries(self) -> tuple[dict[str, Any], ...]:
        """Flatten roster header context with every member entry into tabular dictionaries."""
        header_context: dict[str, Any] = {
            "source_id": str(self.source_id),
            "source_urn": str(self.source_urn),
            "record_category": self.record_category.value,
            "record_type": self.record_type.value,
            "enumeration_year": self.enumeration_year.value,
            "jurisdiction_raw": self.jurisdiction_raw,
            "jurisdiction_id": str(self.jurisdiction_id) if self.jurisdiction_id else None,
            "enumerator_or_assessor_raw": self.enumerator_or_assessor_raw,
            "organization_name_raw": self.organization_name_raw,
            "org_id": str(self.org_id) if self.org_id else None,
            "org_category": self.org_category.value,
            "roster_title": self.roster_title,
            "page_number": self.page_number,
        }
        return tuple({**header_context, **entry.to_dict()} for entry in self.entries)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Deserialize a dictionary payload into an immutable OrganizationRosterRecord."""
        kwargs = cls._parse_base_source_kwargs(data)
        base_keys = set(kwargs.keys())

        for f in dataclasses.fields(cls):
            if f.name in base_keys or f.name not in data:
                continue
            if f.name == "entries":
                raw_entries = data["entries"]
                if not isinstance(raw_entries, (list, tuple)):
                    raise ModelFormatError(f"{cls.__name__} 'entries' must be a list or tuple.")
                kwargs["entries"] = tuple(
                    e
                    if isinstance(e, OrganizationRosterEntry)
                    else OrganizationRosterEntry.from_dict(e)
                    for e in raw_entries
                )
            else:
                kwargs[f.name] = _coerce_org_field(f.name, str(f.type), data[f.name])

        return cls(**kwargs)
