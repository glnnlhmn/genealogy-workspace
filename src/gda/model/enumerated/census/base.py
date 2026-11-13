"""Path: src/gda/model/enumerated/census/base.py

Foundational census schedule and row-level line entry domain models.

Operational Role:
    Defines CensusLineEntry (with mandatory per-row CensusUrn and optional
    SourceID GUID) and CensusScheduleRecord (extending EnumeratedRollRecord).
    Enforces page-level uniqueness of row URNs, GUIDs, and line numbers while
    exposing dual-path row lookup, immutable entry replacement, entry flattening,
    and canonical dictionary/JSON serialization.
"""

from __future__ import annotations

import dataclasses
import json
from typing import Any, ClassVar, Self, get_args, get_origin

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core import format_utc_timestamp
from gda.core.enums.sources import SourceRecordCategory, SourceRecordType
from gda.core.errors import ModelFormatError
from gda.core.introspectable import IntrospectableMixin
from gda.core.types import CENSUS_SHEET_SIDES, MAX_CENSUS_LINE_NUMBER
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import IndividualID, SourceID
from gda.model.atom.urn import CensusUrn
from gda.model.base.audit import AuditStamp
from gda.model.enumerated.base import (
    EnumeratedRollRecord,
    coerce_field_value,
    serialize_primitive_value,
)

__version__ = "1.0.0+build.4"

__all__ = [
    "CensusLineEntry",
    "CensusScheduleRecord",
]

_CENSUS_RECORD_TYPES: frozenset[SourceRecordType] = frozenset(
    {
        SourceRecordType.POPULATION_SCHEDULE,
        SourceRecordType.MORTALITY_SCHEDULE,
        SourceRecordType.AGRICULTURAL_SCHEDULE,
        SourceRecordType.MANUFACTURING_SCHEDULE,
        SourceRecordType.SLAVE_SCHEDULE,
        SourceRecordType.VETERANS_SCHEDULE,
    }
)


@dataclass(
    repr=False,
    config=ConfigDict(kw_only=True, frozen=True, extra="forbid", strict=True),
)
class CensusLineEntry(IntrospectableMixin):
    """Single enumerated row on a census schedule sheet with unique URN and optional GUID."""

    entry_urn: CensusUrn = Field(
        ...,
        description="Mandatory canonical CensusUrn uniquely identifying this schedule row.",
    )
    entry_id: SourceID | None = Field(
        default=None,
        description="Optional surrogate UUIDv4 SourceID GUID for direct row lookup.",
    )
    line_number: int = Field(
        ...,
        ge=1,
        le=MAX_CENSUS_LINE_NUMBER,
        description="Enumerated line number on the census sheet (1..200).",
    )
    name_verbatim: str = Field(
        ...,
        description="Verbatim transcribed name of the enumerated person, head, or proprietor.",
    )
    individual_id: IndividualID | None = Field(
        default=None,
        description="Resolved canonical IndividualID if linked to a person entity.",
    )
    age_raw: str | None = Field(
        default=None,
        description="Verbatim age notation as recorded on the schedule (e.g., '34', '6/12').",
    )
    sex_raw: str | None = Field(
        default=None,
        description="Verbatim sex/gender notation recorded on the schedule (e.g., 'M', 'F').",
    )
    remarks_raw: str | None = Field(
        default=None,
        description="Verbatim enumerator remarks, marginalia, or special notations.",
    )

    def __post_init__(self) -> None:
        """Enforce non-empty verbatim name hygiene."""
        cleaned = self.name_verbatim.strip()
        if not cleaned:
            raise ModelFormatError(
                "CensusLineEntry 'name_verbatim' cannot be empty or whitespace.",
                details={"entry_urn": str(self.entry_urn), "line_number": self.line_number},
            )
        if cleaned != self.name_verbatim:
            object.__setattr__(self, "name_verbatim", cleaned)

    def to_dict(self) -> dict[str, Any]:
        """Serialize CensusLineEntry and subclass fields to a dictionary."""
        return {
            f.name: serialize_primitive_value(getattr(self, f.name))
            for f in dataclasses.fields(self)
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Deserialize a dictionary payload into an immutable CensusLineEntry subclass."""
        if not isinstance(data, dict):
            raise ModelFormatError(f"{cls.__name__} payload must be a dictionary.")

        kwargs: dict[str, Any] = {}
        for f in dataclasses.fields(cls):
            if f.name not in data:
                continue
            kwargs[f.name] = coerce_field_value(str(f.type), data[f.name])
        return cls(**kwargs)

    def to_json(self) -> str:
        """Serialize entry to a JSON formatted string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_json(cls, payload: str) -> Self:
        """Deserialize a JSON string directly into an immutable CensusLineEntry."""
        try:
            data = json.loads(payload)
        except Exception as exc:
            raise ModelFormatError(f"Failed to parse {cls.__name__} JSON string: {exc}") from exc
        return cls.from_dict(data)

    def __str__(self) -> str:
        return f"Line {self.line_number}: {self.name_verbatim} ({self.entry_urn})"

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(line_number={self.line_number!r}, "
            f"name_verbatim={self.name_verbatim!r}, entry_urn={self.entry_urn!r})"
        )


@dataclass(
    repr=False,
    config=ConfigDict(kw_only=True, frozen=True, extra="forbid", strict=True),
)
class CensusScheduleRecord[TEntry: CensusLineEntry](EnumeratedRollRecord):
    """Base evidentiary composite representing an enumerated census schedule sheet."""

    record_type: SourceRecordType = Field(
        default=SourceRecordType.POPULATION_SCHEDULE,
        description="Specific census schedule type (POPULATION, MORTALITY, AGRICULTURAL, etc.).",
    )
    state: str = Field(
        ...,
        description="State, territory, or commonwealth name on the schedule heading.",
    )
    county: str = Field(
        ...,
        description="County, parish, or equivalent civil division on the schedule heading.",
    )
    township_or_ward: str | None = Field(
        default=None,
        description="Township, town, city ward, or precinct heading.",
    )
    supervisor_district: str | None = Field(
        default=None,
        description="Supervisor's District (S.D.) number or designation.",
    )
    enumeration_district: str | None = Field(
        default=None,
        description="Enumeration District (E.D.) number or designation.",
    )
    sheet_number: str | None = Field(
        default=None,
        description="Schedule sheet or stamped page number.",
    )
    sheet_side: str | None = Field(
        default=None,
        description="Schedule sheet face ('A' or 'B').",
    )
    line_count: int | None = Field(
        default=None,
        ge=1,
        le=MAX_CENSUS_LINE_NUMBER,
        description="Total physical lines on the census sheet.",
    )
    enumeration_date_raw: str | None = Field(
        default=None,
        description="Verbatim date the enumerator certified or canvassed the sheet.",
    )
    census_note: str | None = Field(
        default=None,
        description="Archival note regarding torn margins, illegibility, or double enumeration.",
    )
    entries: tuple[TEntry, ...] = Field(
        ...,
        min_length=1,
        description="Immutable ordered tuple of enumerated line entries on this schedule sheet.",
    )

    EXPECTED_CATEGORY: ClassVar[SourceRecordCategory] = SourceRecordCategory.CENSUS
    ALLOWED_RECORD_TYPES: ClassVar[frozenset[SourceRecordType]] = _CENSUS_RECORD_TYPES

    def __post_init__(self) -> None:
        """Enforce census category, URN specialization, sheet bounds, and row uniqueness."""
        super().__post_init__()

        if self.record_category != self.EXPECTED_CATEGORY:
            raise ModelFormatError(
                f"{self.__class__.__name__} requires category '{self.EXPECTED_CATEGORY.value}', "
                f"got '{self.record_category.value}'."
            )

        if self.record_type not in self.ALLOWED_RECORD_TYPES:
            raise ModelFormatError(
                f"{self.__class__.__name__} requires record_type in "
                f"{sorted(t.value for t in self.ALLOWED_RECORD_TYPES)}, got '{self.record_type.value}'."
            )

        if not isinstance(self.source_urn, CensusUrn):
            raise ModelFormatError(
                f"{self.__class__.__name__} 'source_urn' must be a CensusUrn, "
                f"got {type(self.source_urn).__name__}."
            )

        state_clean = self.state.strip()
        if not state_clean:
            raise ModelFormatError(
                f"{self.__class__.__name__} 'state' cannot be empty or whitespace."
            )
        if state_clean != self.state:
            object.__setattr__(self, "state", state_clean)

        county_clean = self.county.strip()
        if not county_clean:
            raise ModelFormatError(
                f"{self.__class__.__name__} 'county' cannot be empty or whitespace."
            )
        if county_clean != self.county:
            object.__setattr__(self, "county", county_clean)

        if self.sheet_side is not None and self.sheet_side not in CENSUS_SHEET_SIDES:
            raise ModelFormatError(
                f"{self.__class__.__name__} 'sheet_side' must be one of "
                f"{sorted(CENSUS_SHEET_SIDES)}, got '{self.sheet_side}'."
            )

        if self.line_count is not None and len(self.entries) > self.line_count:
            raise ModelFormatError(
                f"Entry count ({len(self.entries)}) exceeds declared sheet line_count ({self.line_count})."
            )

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
                    f"Duplicate CensusLineEntry entry_urn '{urn_str}' within schedule sheet."
                )
            seen_urns.add(urn_str)

            if entry.entry_id is not None:
                id_str = str(entry.entry_id)
                if id_str in seen_ids:
                    raise ModelFormatError(
                        f"Duplicate CensusLineEntry entry_id '{id_str}' within schedule sheet."
                    )
                seen_ids.add(id_str)

            if entry.line_number in seen_lines:
                raise ModelFormatError(
                    f"Duplicate CensusLineEntry line_number {entry.line_number} within schedule sheet."
                )
            seen_lines.add(entry.line_number)

    @property
    def entry_count(self) -> int:
        """Return the count of populated line entries on this schedule sheet."""
        return len(self.entries)

    def get_entry(self, identifier: CensusUrn | SourceID | str) -> TEntry | None:
        """Retrieve a schedule line entry by either its CensusUrn or its SourceID GUID."""
        target = str(identifier).strip()
        if not target:
            return None

        for entry in self.entries:
            if str(entry.entry_urn) == target:
                return entry
            if entry.entry_id is not None and str(entry.entry_id) == target:
                return entry
        return None

    def require_entry(self, identifier: CensusUrn | SourceID | str) -> TEntry:
        """Retrieve a schedule line entry by URN or GUID, raising ModelFormatError if absent."""
        found = self.get_entry(identifier)
        if found is None:
            raise ModelFormatError(
                f"No census line entry matching identifier '{identifier}' in {self.source_urn}.",
                details={"identifier": str(identifier), "source_urn": str(self.source_urn)},
            )
        return found

    def replace_entry(self, updated_entry: TEntry) -> Self:
        """Return a new immutable schedule with a corrected entry swapped in by URN or GUID."""
        target_urn = str(updated_entry.entry_urn)
        target_id = str(updated_entry.entry_id) if updated_entry.entry_id is not None else None

        replaced = False
        new_entries: list[TEntry] = []
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

        new_audit = AuditStamp(
            created_at=self.audit.created_at,
            updated_at=IsoTimestamp(format_utc_timestamp()),
        )
        return dataclasses.replace(self, entries=tuple(new_entries), audit=new_audit)

    def flatten_entries(self) -> tuple[dict[str, Any], ...]:
        """Flatten schedule header context with every line entry into tabular dictionaries."""
        header_context: dict[str, Any] = {
            "source_id": str(self.source_id),
            "source_urn": str(self.source_urn),
            "record_category": self.record_category.value,
            "record_type": self.record_type.value,
            "enumeration_year": self.enumeration_year.value,
            "jurisdiction_raw": self.jurisdiction_raw,
            "jurisdiction_id": str(self.jurisdiction_id) if self.jurisdiction_id else None,
            "enumerator_or_assessor_raw": self.enumerator_or_assessor_raw,
            "state": self.state,
            "county": self.county,
            "township_or_ward": self.township_or_ward,
            "supervisor_district": self.supervisor_district,
            "enumeration_district": self.enumeration_district,
            "sheet_number": self.sheet_number,
            "sheet_side": self.sheet_side,
            "enumeration_date_raw": self.enumeration_date_raw,
        }
        return tuple({**header_context, **entry.to_dict()} for entry in self.entries)

    @classmethod
    def _resolve_entry_class(cls) -> type[CensusLineEntry]:
        """Resolve concrete CensusLineEntry subclass from generic base type parameters."""
        for base in getattr(cls, "__orig_bases__", ()):
            origin = get_origin(base)
            if origin is not None and issubclass(origin, CensusScheduleRecord):
                args = get_args(base)
                if args and isinstance(args[0], type) and issubclass(args[0], CensusLineEntry):
                    return args[0]
        return CensusLineEntry

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Deserialize a dictionary payload into an immutable CensusScheduleRecord subclass."""
        kwargs = cls._parse_base_source_kwargs(data)
        base_keys = set(kwargs.keys())
        entry_cls = cls._resolve_entry_class()

        for f in dataclasses.fields(cls):
            if f.name in base_keys or f.name not in data:
                continue
            if f.name == "entries":
                raw_entries = data["entries"]
                if not isinstance(raw_entries, (list, tuple)):
                    raise ModelFormatError(f"{cls.__name__} 'entries' must be a list or tuple.")
                kwargs["entries"] = tuple(
                    e if isinstance(e, CensusLineEntry) else entry_cls.from_dict(e)
                    for e in raw_entries
                )
            else:
                kwargs[f.name] = coerce_field_value(str(f.type), data[f.name])

        return cls(**kwargs)
