"""Path: src/gda/model/source/enumerated/directories/base.py

City, business, farmers', and civic/voter directory enumeration models.

Operational Role:
    Models printed directories and civic voter/poll lists with per-entry
    ArchivalURN and optional SourceID GUID lookup, immutable entry replacement,
    entry flattening, and canonical dictionary/JSON serialization.
"""

from __future__ import annotations

import dataclasses
import json
from typing import Any, ClassVar, Self

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core import format_utc_timestamp
from gda.core.enums.fiscal import ResidentialStatus
from gda.core.enums.sources import SourceRecordCategory, SourceRecordType
from gda.core.errors import ModelFormatError
from gda.core.introspectable import IntrospectableMixin
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import IndividualID, LocationID, SourceID
from gda.model.atom.urn import ArchivalURN
from gda.model.source.enumerated.base import (
    EnumeratedRollRecord,
    coerce_field_value,
    serialize_primitive_value,
)

__version__ = "1.0.0+build.4"

__all__ = [
    "DirectoryEntry",
    "DirectoryRollRecord",
    "ResidentialStatus",
]

_DIRECTORY_CATEGORIES: frozenset[SourceRecordCategory] = frozenset(
    {
        SourceRecordCategory.DIRECTORY,
        SourceRecordCategory.CIVIC,
    }
)

_DIRECTORY_RECORD_TYPES: frozenset[SourceRecordType] = frozenset(
    {
        SourceRecordType.CITY_DIRECTORY,
        SourceRecordType.TELEPHONE_DIRECTORY,
        SourceRecordType.BUSINESS_DIRECTORY,
        SourceRecordType.FARMERS_DIRECTORY,
        SourceRecordType.STREET_GAZETTEER,
    }
)


@dataclass(
    repr=False,
    config=ConfigDict(frozen=True, extra="forbid", strict=True),
    kw_only=True,
)
class DirectoryEntry(IntrospectableMixin):
    """Single enumerated person or household listing in a directory or civic roll."""

    entry_urn: ArchivalURN = Field(
        ...,
        description="Mandatory ArchivalURN uniquely identifying this directory listing.",
    )
    entry_id: SourceID | None = Field(
        default=None,
        description="Optional surrogate UUIDv4 SourceID GUID for direct row lookup.",
    )
    name_verbatim: str = Field(
        ...,
        description="Verbatim name as printed in the directory or roll.",
    )
    individual_id: IndividualID | None = Field(
        default=None,
        description="Resolved canonical IndividualID of the listed person.",
    )
    spouse_name_raw: str | None = Field(
        default=None,
        description="Spouse name or widow-of notation printed in parentheses (e.g., '(wid John)').",
    )
    occupation_verbatim: str | None = Field(
        default=None,
        description="Verbatim occupation or trade abbreviation.",
    )
    employer_or_business_raw: str | None = Field(
        default=None,
        description="Employer, firm name, or business address.",
    )
    residence_address_raw: str | None = Field(
        default=None,
        description="Verbatim street address or rural route residence.",
    )
    residential_status: ResidentialStatus | None = Field(
        default=None,
        description="Normalized residential tenure ('Householder', 'Boarder', 'Rooms', 'Widow').",
    )
    residence_location_id: LocationID | None = Field(
        default=None,
        description="Resolved civil jurisdiction LocationID for the residence.",
    )

    def __post_init__(self) -> None:
        """Enforce non-empty name_verbatim hygiene."""
        cleaned = self.name_verbatim.strip()
        if not cleaned:
            raise ModelFormatError(
                "DirectoryEntry 'name_verbatim' cannot be empty or whitespace.",
                details={"entry_urn": str(self.entry_urn)},
            )
        if cleaned != self.name_verbatim:
            object.__setattr__(self, "name_verbatim", cleaned)

    def to_dict(self) -> dict[str, Any]:
        """Serialize DirectoryEntry fields to a dictionary."""
        return {
            f.name: serialize_primitive_value(getattr(self, f.name))
            for f in dataclasses.fields(self)
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Deserialize a dictionary payload into an immutable DirectoryEntry."""
        if not isinstance(data, dict):
            raise ModelFormatError("DirectoryEntry payload must be a dictionary.")
        kwargs: dict[str, Any] = {}
        for f in dataclasses.fields(cls):
            if f.name not in data:
                continue
            kwargs[f.name] = coerce_field_value(str(f.type), data[f.name])
        return cls(**kwargs)

    def to_json(self) -> str:
        """Serialize DirectoryEntry to a JSON formatted string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_json(cls, payload: str) -> Self:
        """Deserialize a JSON string directly into a DirectoryEntry."""
        try:
            data = json.loads(payload)
        except Exception as exc:
            raise ModelFormatError(f"Failed to parse DirectoryEntry JSON string: {exc}") from exc
        return cls.from_dict(data)

    def __str__(self) -> str:
        return f"{self.name_verbatim} ({self.entry_urn})"

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(name_verbatim={self.name_verbatim!r}, "
            f"entry_urn={self.entry_urn!r})"
        )


@dataclass(
    repr=False,
    config=ConfigDict(frozen=True, extra="forbid", strict=True),
    kw_only=True,
)
class DirectoryRollRecord(EnumeratedRollRecord):
    """Evidentiary composite for printed directory pages or civic voter/poll lists."""

    record_category: SourceRecordCategory = Field(
        default=SourceRecordCategory.DIRECTORY,
        description="High-level DIRECTORY or CIVIC source category.",
    )
    record_type: SourceRecordType = Field(
        default=SourceRecordType.CITY_DIRECTORY,
        description="Specific directory or gazetteer classification.",
    )
    publication_title_raw: str = Field(
        ...,
        description="Verbatim title of the directory or civic roll.",
    )
    page_number_raw: str | None = Field(
        default=None,
        description="Printed page or column number within the directory.",
    )
    entries: tuple[DirectoryEntry, ...] = Field(
        ...,
        min_length=1,
        description="Immutable ordered tuple of enumerated directory entries.",
    )

    ALLOWED_CATEGORIES: ClassVar[frozenset[SourceRecordCategory]] = _DIRECTORY_CATEGORIES
    ALLOWED_RECORD_TYPES: ClassVar[frozenset[SourceRecordType]] = _DIRECTORY_RECORD_TYPES

    def __post_init__(self) -> None:
        """Enforce directory category/type, publication title hygiene, and entry uniqueness."""
        super().__post_init__()

        if self.record_category not in self.ALLOWED_CATEGORIES:
            raise ModelFormatError(
                f"DirectoryRollRecord requires record_category in "
                f"{sorted(c.value for c in self.ALLOWED_CATEGORIES)}, got '{self.record_category.value}'."
            )

        if self.record_type not in self.ALLOWED_RECORD_TYPES:
            raise ModelFormatError(
                f"DirectoryRollRecord requires record_type in "
                f"{sorted(t.value for t in self.ALLOWED_RECORD_TYPES)}, got '{self.record_type.value}'."
            )

        pub = self.publication_title_raw.strip()
        if not pub:
            raise ModelFormatError(
                "DirectoryRollRecord 'publication_title_raw' cannot be empty or whitespace."
            )
        if pub != self.publication_title_raw:
            object.__setattr__(self, "publication_title_raw", pub)

        seen_urns: set[str] = set()
        seen_ids: set[str] = set()
        for entry in self.entries:
            urn_str = str(entry.entry_urn)
            if urn_str in seen_urns:
                raise ModelFormatError(
                    f"Duplicate DirectoryEntry entry_urn '{urn_str}' within directory page."
                )
            seen_urns.add(urn_str)

            if entry.entry_id is not None:
                id_str = str(entry.entry_id)
                if id_str in seen_ids:
                    raise ModelFormatError(
                        f"Duplicate DirectoryEntry entry_id '{id_str}' within directory page."
                    )
                seen_ids.add(id_str)

    @property
    def entry_count(self) -> int:
        """Return count of directory entries on this page."""
        return len(self.entries)

    def get_entry(self, identifier: ArchivalURN | SourceID | str) -> DirectoryEntry | None:
        """Retrieve a directory entry by either its ArchivalURN or its SourceID GUID."""
        target = str(identifier).strip()
        if not target:
            return None

        for entry in self.entries:
            if str(entry.entry_urn) == target:
                return entry
            if entry.entry_id is not None and str(entry.entry_id) == target:
                return entry
        return None

    def require_entry(self, identifier: ArchivalURN | SourceID | str) -> DirectoryEntry:
        """Retrieve a directory entry by URN or GUID, raising ModelFormatError if absent."""
        found = self.get_entry(identifier)
        if found is None:
            raise ModelFormatError(
                f"No directory entry matching identifier '{identifier}' in {self.source_urn}.",
                details={"identifier": str(identifier), "source_urn": str(self.source_urn)},
            )
        return found

    def replace_entry(self, updated_entry: DirectoryEntry) -> Self:
        """Return a new immutable directory page with a corrected entry swapped in by URN or GUID."""
        target_urn = str(updated_entry.entry_urn)
        target_id = str(updated_entry.entry_id) if updated_entry.entry_id is not None else None

        replaced = False
        new_entries: list[DirectoryEntry] = []
        for entry in self.entries:
            matches_urn = str(entry.entry_urn) == target_urn
            matches_guid = (
                target_id is not None
                and entry.entry_id is not None
                and str(entry.entry_id) == target_id
            )
            if not replaced and (matches_urn or matches_guid):
                new_entries.append(updated_entry)
                replaced = True
            else:
                new_entries.append(entry)

        if not replaced:
            raise ModelFormatError(
                f"Cannot replace entry '{target_urn}': no matching URN or GUID found in {self.source_urn}.",
                details={"entry_urn": target_urn, "source_urn": str(self.source_urn)},
            )

        new_audit = self.audit.touch(IsoTimestamp(format_utc_timestamp()))
        return dataclasses.replace(self, entries=tuple(new_entries), audit=new_audit)

    def flatten_entries(self) -> tuple[dict[str, Any], ...]:
        """Flatten directory page header context with every listing into tabular dictionaries."""
        header_context: dict[str, Any] = {
            "source_id": str(self.source_id),
            "source_urn": str(self.source_urn),
            "record_category": self.record_category.value,
            "record_type": self.record_type.value,
            "enumeration_year": self.enumeration_year.value,
            "jurisdiction_raw": self.jurisdiction_raw,
            "jurisdiction_id": str(self.jurisdiction_id) if self.jurisdiction_id else None,
            "publication_title_raw": self.publication_title_raw,
            "page_number_raw": self.page_number_raw,
        }
        return tuple({**header_context, **entry.to_dict()} for entry in self.entries)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Deserialize a dictionary payload into an immutable DirectoryRollRecord."""
        kwargs = cls._parse_base_source_kwargs(data)
        base_keys = set(kwargs.keys())

        for f in dataclasses.fields(cls):
            if f.name in base_keys or f.name not in data:
                continue
            if f.name == "entries":
                raw_entries = data["entries"]
                if not isinstance(raw_entries, (list, tuple)):
                    raise ModelFormatError("DirectoryRollRecord 'entries' must be a list or tuple.")
                kwargs["entries"] = tuple(
                    e if isinstance(e, DirectoryEntry) else DirectoryEntry.from_dict(e)
                    for e in raw_entries
                )
            else:
                kwargs[f.name] = coerce_field_value(str(f.type), data[f.name])

        return cls(**kwargs)
