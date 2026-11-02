"""Path: src/gda/model/base/name.py

Canonical personal, jurisdictional, artifact, and historical naming representations.

Operational Role:
    Defines foundational naming models across the digital archive. Provides
    NameBase as the root dataclass for all nouns, NamePerson for genealogical personas,
    and NameThing for evolutionary jurisdictions, sites, and artifacts with multiple
    HistoricVariant name phases. Equips all models with copy-on-write mutators,
    factory constructors, and serialization parity.

Classes:
    HistoricVariant: Discrete historical name phase with verbatim text and period.
    NameLifecycleMixin: Reusable copy-on-write mutator mixin for all naming models.
    NameBase: Root dataclass for personal, place, and artifact nouns.
    NamePerson: Specialized personal name model supporting titles and married names.
    NameThing: Specialized entity name model supporting multiple historic variants.
"""

from __future__ import annotations

import json
from dataclasses import replace
from typing import Any, Self, cast

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.errors import ModelFormatError
from gda.core.introspectable import IntrospectableMixin
from gda.enums.vital import HistoricNameType, NameStatus
from gda.model.atom.date import DateModifier, DateString, EventDate
from gda.model.base.time_period import TimePeriod

__version__ = "1.1.0+build.8"

__all__ = [
    "CanonicalName",
    "HistoricNameType",
    "HistoricVariant",
    "HistoricalName",
    "NameBase",
    "NameLifecycleMixin",
    "NamePerson",
    "NameStatus",
    "NameThing",
]


@dataclass(config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True))
class HistoricVariant(IntrospectableMixin):
    """Discrete historical naming phase for an evolutionary place, site, or artifact."""

    raw: str = Field(..., description="Verbatim historical name as recorded in source.")
    name: str = Field(
        ..., description="Standardized or normalized historical name form."
    )
    historic_name_type: HistoricNameType = Field(
        default=HistoricNameType.HISTORICAL,
        description="Classification of historical name variant.",
    )
    valid_period: TimePeriod | None = Field(
        default=None, description="Optional temporal bounds when this name applied."
    )
    comment: str | None = Field(
        default=None, description="Etymological or provenance notes on this name phase."
    )

    def __post_init__(self) -> None:
        """Enforce non-empty string boundaries."""
        if not self.raw or not self.raw.strip():
            raise ModelFormatError(
                "HistoricVariant 'raw' cannot be empty or whitespace."
            )
        if not self.name or not self.name.strip():
            raise ModelFormatError(
                "HistoricVariant 'name' cannot be empty or whitespace."
            )

    @classmethod
    def create(
        cls,
        raw: str,
        name: str | None = None,
        historic_name_type: HistoricNameType | str = HistoricNameType.HISTORICAL,
        valid_period: TimePeriod | None = None,
        comment: str | None = None,
    ) -> HistoricVariant:
        """Factory constructor instantiating a validated HistoricVariant."""
        res_type = (
            historic_name_type
            if isinstance(historic_name_type, HistoricNameType)
            else HistoricNameType(historic_name_type)
        )
        norm_name = name.strip() if name and name.strip() else raw.strip()
        return cls(
            raw=raw.strip(),
            name=norm_name,
            historic_name_type=res_type,
            valid_period=valid_period,
            comment=comment.strip() if comment else None,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize HistoricVariant to a dictionary."""
        data: dict[str, Any] = {
            "raw": self.raw,
            "name": self.name,
            "historic_name_type": self.historic_name_type.value,
        }
        if self.valid_period is not None:
            start_str = (
                str(self.valid_period.start_date)
                if self.valid_period.start_date
                else None
            )
            end_str = (
                str(self.valid_period.end_date) if self.valid_period.end_date else None
            )
            data["valid_period"] = {
                "start_date": start_str,
                "end_date": end_str,
            }
        if self.comment is not None:
            data["comment"] = self.comment
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HistoricVariant:
        """Deserialize a dictionary payload into an immutable HistoricVariant."""
        if not isinstance(data, dict):
            raise ModelFormatError("HistoricVariant payload must be a dictionary.")

        raw_val = data.get("raw")
        if not raw_val or not str(raw_val).strip():
            raise ModelFormatError("Missing required field 'raw' for HistoricVariant.")

        name_val = data.get("name") or raw_val

        raw_period = data.get("valid_period")
        period_obj: TimePeriod | None = None
        if isinstance(raw_period, dict):
            start_str = raw_period.get("start_date")
            end_str = raw_period.get("end_date")
            start_ev = (
                EventDate(date=DateString(str(start_str)), modifier=DateModifier.EXACT)
                if start_str
                else None
            )
            end_ev = (
                EventDate(date=DateString(str(end_str)), modifier=DateModifier.EXACT)
                if end_str
                else None
            )
            if start_ev is not None or end_ev is not None:
                period_obj = TimePeriod(start_date=start_ev, end_date=end_ev)
        elif isinstance(raw_period, TimePeriod):
            period_obj = raw_period

        return cls.create(
            raw=str(raw_val),
            name=str(name_val),
            historic_name_type=data.get(
                "historic_name_type", HistoricNameType.HISTORICAL
            ),
            valid_period=period_obj,
            comment=data.get("comment"),
        )


class NameLifecycleMixin(IntrospectableMixin):
    """Reusable copy-on-write mutators for naming models."""

    def update_raw(self, raw: str) -> Self:
        """Return a new immutable copy with updated verbatim raw text."""
        clean = raw.strip() if raw else ""
        if not clean:
            raise ModelFormatError("Raw name cannot be empty or whitespace.")
        return cast(Self, replace(cast(Any, self), raw=clean))

    def update_canonical(self, canonical: str) -> Self:
        """Return a new immutable copy with updated canonical display name."""
        clean = canonical.strip() if canonical else ""
        if not clean:
            raise ModelFormatError("Canonical name cannot be empty or whitespace.")
        return cast(Self, replace(cast(Any, self), canonical=clean))

    def add_alias(self, alias: str) -> Self:
        """Return a new immutable copy with unique alias appended."""
        clean = alias.strip() if alias else ""
        if not clean:
            raise ModelFormatError("Alias cannot be empty or whitespace.")
        current_aliases: list[str] = getattr(self, "aliases", [])
        if clean in current_aliases:
            return self
        return cast(Self, replace(cast(Any, self), aliases=[*current_aliases, clean]))

    def remove_alias(self, alias: str) -> Self:
        """Return a new immutable copy with target alias removed."""
        clean = alias.strip() if alias else ""
        current_aliases: list[str] = getattr(self, "aliases", [])
        filtered = [a for a in current_aliases if a != clean]
        if len(filtered) == len(current_aliases):
            return self
        return cast(Self, replace(cast(Any, self), aliases=filtered))

    def add_spelling(self, spelling: str) -> Self:
        """Return a new immutable copy with unique alternate spelling appended."""
        clean = spelling.strip() if spelling else ""
        if not clean:
            raise ModelFormatError("Alternate spelling cannot be empty or whitespace.")
        current_spellings: list[str] = getattr(self, "alt_spellings", [])
        if clean in current_spellings:
            return self
        return cast(
            Self, replace(cast(Any, self), alt_spellings=[*current_spellings, clean])
        )

    def remove_spelling(self, spelling: str) -> Self:
        """Return a new immutable copy with target alternate spelling removed."""
        clean = spelling.strip() if spelling else ""
        current_spellings: list[str] = getattr(self, "alt_spellings", [])
        filtered = [s for s in current_spellings if s != clean]
        if len(filtered) == len(current_spellings):
            return self
        return cast(Self, replace(cast(Any, self), alt_spellings=filtered))

    def update_comment(self, comment: str | None) -> Self:
        """Return a new immutable copy with updated contextual comment."""
        clean = comment.strip() if comment is not None else None
        return cast(Self, replace(cast(Any, self), comment=clean))


@dataclass(
    config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True),
    kw_only=True,
)
class NameBase(NameLifecycleMixin):
    """Root dataclass representing foundational noun naming attributes."""

    raw: str = Field(..., description="Verbatim raw name as recorded in source.")
    canonical: str = Field(..., description="Authoritative formal modern display name.")
    aliases: list[str] = Field(
        default_factory=list, description="Vernacular monikers or colloquial nicknames."
    )
    alt_spellings: list[str] = Field(
        default_factory=list, description="Orthographic or phonetic variations."
    )
    comment: str | None = Field(
        default=None, description="Free-form etymological or transcription notes."
    )

    def __post_init__(self) -> None:
        """Enforce base noun invariants."""
        if not self.raw or not self.raw.strip():
            raise ModelFormatError(f"{self.__class__.__name__} 'raw' cannot be empty.")
        if not self.canonical or not self.canonical.strip():
            raise ModelFormatError(
                f"{self.__class__.__name__} 'canonical' cannot be empty."
            )
        if len(self.aliases) != len(set(self.aliases)):
            raise ModelFormatError("Duplicate entries found in aliases.")
        if len(self.alt_spellings) != len(set(self.alt_spellings)):
            raise ModelFormatError("Duplicate entries found in alt_spellings.")


@dataclass(
    config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True),
    kw_only=True,
)
class NamePerson(NameBase):
    """Specialized persona noun model supporting discrete titles, parts, and married names."""

    prefix: str | None = Field(
        default=None, description="Title, rank, or honorific style."
    )
    given: str | None = Field(default=None, description="First or given name.")
    middle: str | None = Field(default=None, description="Middle name(s) or initials.")
    surname: str | None = Field(
        default=None, description="Birth surname (patronymic/matronymic)."
    )
    suffix: str | None = Field(
        default=None, description="Generational or post-nominal suffix."
    )
    married: list[str] = Field(
        default_factory=list, description="Searchable list of all married surnames."
    )

    def __post_init__(self) -> None:
        """Enforce persona invariants."""
        super().__post_init__()
        if len(self.married) != len(set(self.married)):
            raise ModelFormatError("Duplicate entries found in married.")

    @property
    def full_name(self) -> str:
        """Construct structured personal name from present components."""
        candidate_parts = (
            self.prefix,
            self.given,
            self.middle,
            self.surname,
            self.suffix,
        )
        parts: list[str] = [
            p for p in candidate_parts if isinstance(p, str) and p.strip()
        ]
        return " ".join(parts) if parts else self.canonical

    @classmethod
    def create(
        cls,
        raw: str,
        canonical: str | None = None,
        prefix: str | None = None,
        given: str | None = None,
        middle: str | None = None,
        surname: str | None = None,
        suffix: str | None = None,
        married: list[str] | None = None,
        aliases: list[str] | None = None,
        alt_spellings: list[str] | None = None,
        comment: str | None = None,
    ) -> NamePerson:
        """Factory constructor instantiating a validated NamePerson."""
        clean_married: list[str] = []
        if married:
            for m in married:
                c = m.strip() if m else ""
                if c and c not in clean_married:
                    clean_married.append(c)

        clean_aliases: list[str] = []
        if aliases:
            for a in aliases:
                c = a.strip() if a else ""
                if c and c not in clean_aliases:
                    clean_aliases.append(c)

        clean_spellings: list[str] = []
        if alt_spellings:
            for s in alt_spellings:
                c = s.strip() if s else ""
                if c and c not in clean_spellings:
                    clean_spellings.append(c)

        computed_canonical = (
            canonical.strip() if canonical and canonical.strip() else None
        )
        if not computed_canonical:
            name_parts = [
                p
                for p in (prefix, given, middle, surname, suffix)
                if isinstance(p, str) and p.strip()
            ]
            computed_canonical = " ".join(name_parts) if name_parts else raw.strip()

        kwargs: dict[str, Any] = {
            "raw": raw.strip(),
            "canonical": computed_canonical,
            "prefix": prefix.strip() if prefix else None,
            "given": given.strip() if given else None,
            "middle": middle.strip() if middle else None,
            "surname": surname.strip() if surname else None,
            "suffix": suffix.strip() if suffix else None,
            "married": clean_married,
            "aliases": clean_aliases,
            "alt_spellings": clean_spellings,
            "comment": comment.strip() if comment else None,
        }
        return cls(**kwargs)

    def add_married(self, married_name: str) -> NamePerson:
        """Return a new immutable copy with unique married surname appended."""
        clean = married_name.strip() if married_name else ""
        if not clean:
            raise ModelFormatError("Married name cannot be empty or whitespace.")
        if clean in self.married:
            return self
        return replace(self, married=[*self.married, clean])

    def remove_married(self, married_name: str) -> NamePerson:
        """Return a new immutable copy with target married surname removed."""
        clean = married_name.strip() if married_name else ""
        filtered = [m for m in self.married if m != clean]
        if len(filtered) == len(self.married):
            return self
        return replace(self, married=filtered)

    def update_parts(
        self,
        prefix: str | None = None,
        given: str | None = None,
        middle: str | None = None,
        surname: str | None = None,
        suffix: str | None = None,
    ) -> NamePerson:
        """Return a new immutable copy with updated personal onomastic components."""
        return replace(
            self,
            prefix=prefix.strip() if prefix is not None else self.prefix,
            given=given.strip() if given is not None else self.given,
            middle=middle.strip() if middle is not None else self.middle,
            surname=surname.strip() if surname is not None else self.surname,
            suffix=suffix.strip() if suffix is not None else self.suffix,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize NamePerson instance to a dictionary."""
        data: dict[str, Any] = {
            "raw": self.raw,
            "canonical": self.canonical,
            "aliases": list(self.aliases),
            "alt_spellings": list(self.alt_spellings),
            "married": list(self.married),
        }
        if self.prefix is not None:
            data["prefix"] = self.prefix
        if self.given is not None:
            data["given"] = self.given
        if self.middle is not None:
            data["middle"] = self.middle
        if self.surname is not None:
            data["surname"] = self.surname
        if self.suffix is not None:
            data["suffix"] = self.suffix
        if self.comment is not None:
            data["comment"] = self.comment
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> NamePerson:
        """Deserialize a dictionary payload into an immutable NamePerson."""
        if not isinstance(data, dict):
            raise ModelFormatError("NamePerson payload must be a dictionary.")

        raw_val = data.get("raw")
        if not raw_val:
            raw_val = data.get("raw_name")
        if not raw_val or not str(raw_val).strip():
            raise ModelFormatError("Missing required field 'raw' for NamePerson.")

        can_val = data.get("canonical")
        if not can_val:
            can_val = data.get("canonical_name")

        married_list = data.get("married")
        if married_list is None:
            married_list = data.get("married_names", [])

        alt_spellings_list = data.get("alt_spellings")
        if alt_spellings_list is None:
            alt_spellings_list = data.get("alternate_spellings")

        comment_val = data.get("comment")
        if comment_val is None:
            comment_val = data.get("notes")

        return cls.create(
            raw=str(raw_val),
            canonical=str(can_val) if can_val else None,
            prefix=data.get("prefix"),
            given=data.get("given"),
            middle=data.get("middle"),
            surname=data.get("surname"),
            suffix=data.get("suffix"),
            married=married_list,
            aliases=data.get("aliases"),
            alt_spellings=alt_spellings_list,
            comment=comment_val,
        )

    def to_json(self) -> str:
        """Serialize NamePerson instance to a JSON formatted string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_json(cls, payload: str) -> NamePerson:
        """Deserialize a JSON string directly into a NamePerson instance."""
        try:
            data = json.loads(payload)
        except Exception as exc:
            raise ModelFormatError(
                f"Failed to parse NamePerson JSON string: {exc}"
            ) from exc
        return cls.from_dict(data)

    def __str__(self) -> str:
        """Return full structured personal name representation."""
        return self.full_name


@dataclass(
    config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True),
    kw_only=True,
)
class NameThing(NameBase):
    """Specialized entity name model supporting multiple historic variants."""

    historic: list[HistoricVariant] = Field(
        default_factory=list,
        description="Chronological or evolutionary historical naming variants.",
    )

    def __post_init__(self) -> None:
        """Enforce thing invariants."""
        super().__post_init__()

    @classmethod
    def create(
        cls,
        raw: str,
        canonical: str | None = None,
        aliases: list[str] | None = None,
        alt_spellings: list[str] | None = None,
        historic: list[HistoricVariant] | None = None,
        comment: str | None = None,
    ) -> NameThing:
        """Factory constructor instantiating a validated NameThing."""
        clean_aliases: list[str] = []
        if aliases:
            for a in aliases:
                c = a.strip() if a else ""
                if c and c not in clean_aliases:
                    clean_aliases.append(c)

        clean_spellings: list[str] = []
        if alt_spellings:
            for s in alt_spellings:
                c = s.strip() if s else ""
                if c and c not in clean_spellings:
                    clean_spellings.append(c)

        computed_can = (
            canonical.strip() if canonical and canonical.strip() else raw.strip()
        )

        kwargs: dict[str, Any] = {
            "raw": raw.strip(),
            "canonical": computed_can,
            "aliases": clean_aliases,
            "alt_spellings": clean_spellings,
            "historic": list(historic) if historic else [],
            "comment": comment.strip() if comment else None,
        }
        return cls(**kwargs)

    def add_historic_variant(
        self,
        raw: str,
        name: str | None = None,
        historic_name_type: HistoricNameType | str = HistoricNameType.HISTORICAL,
        valid_period: TimePeriod | None = None,
        comment: str | None = None,
    ) -> NameThing:
        """Return a new immutable copy appending a HistoricVariant."""
        variant = HistoricVariant.create(
            raw=raw,
            name=name,
            historic_name_type=historic_name_type,
            valid_period=valid_period,
            comment=comment,
        )
        return replace(self, historic=[*self.historic, variant])

    def remove_historic_variant(self, raw: str) -> NameThing:
        """Return a new immutable copy removing matching HistoricVariants by raw text."""
        clean = raw.strip() if raw else ""
        filtered = [v for v in self.historic if v.raw != clean]
        if len(filtered) == len(self.historic):
            return self
        return replace(self, historic=filtered)

    def to_dict(self) -> dict[str, Any]:
        """Serialize NameThing instance to a dictionary."""
        data: dict[str, Any] = {
            "raw": self.raw,
            "canonical": self.canonical,
            "aliases": list(self.aliases),
            "alt_spellings": list(self.alt_spellings),
            "historic": [v.to_dict() for v in self.historic],
        }
        if self.comment is not None:
            data["comment"] = self.comment
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> NameThing:
        """Deserialize a dictionary payload into an immutable NameThing."""
        if not isinstance(data, dict):
            raise ModelFormatError("NameThing payload must be a dictionary.")

        raw_val = data.get("raw")
        if not raw_val:
            raw_val = data.get("raw_name")
        if not raw_val or not str(raw_val).strip():
            raise ModelFormatError("Missing required field 'raw' for NameThing.")

        can_val = data.get("canonical")
        if not can_val:
            can_val = data.get("canonical_name")

        raw_historic = data.get("historic", [])
        variants: list[HistoricVariant] = []
        if isinstance(raw_historic, list):
            for item in raw_historic:
                if isinstance(item, dict):
                    variants.append(HistoricVariant.from_dict(item))
                elif hasattr(item, "raw") and hasattr(item, "historic_name_type"):
                    variants.append(cast(HistoricVariant, item))
                else:
                    continue

        alt_spellings_list = data.get("alt_spellings")
        if alt_spellings_list is None:
            alt_spellings_list = data.get("alternate_spellings")

        comment_val = data.get("comment")
        if comment_val is None:
            comment_val = data.get("notes")

        return cls.create(
            raw=str(raw_val),
            canonical=str(can_val) if can_val else None,
            aliases=data.get("aliases"),
            alt_spellings=alt_spellings_list,
            historic=variants,
            comment=comment_val,
        )

    def to_json(self) -> str:
        """Serialize NameThing instance to a JSON formatted string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_json(cls, payload: str) -> NameThing:
        """Deserialize a JSON string directly into a NameThing instance."""
        try:
            data = json.loads(payload)
        except Exception as exc:
            raise ModelFormatError(
                f"Failed to parse NameThing JSON string: {exc}"
            ) from exc
        return cls.from_dict(data)

    def __str__(self) -> str:
        """Render concise human-readable title representation."""
        return self.canonical


# ==============================================================================
# BACKWARD COMPATIBILITY ALIASES
# ==============================================================================
CanonicalName = NamePerson
HistoricalName = NameThing
