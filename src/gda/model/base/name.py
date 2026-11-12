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

from gda.core.enums.vital import HistoricNameType
from gda.core.errors import ModelFormatError
from gda.core.introspectable import IntrospectableMixin
from gda.model.base.date import TimePeriod

__version__ = "1.2.0+build.2"

__all__ = [
    "CanonicalName",
    "HistoricNameType",
    "HistoricVariant",
    "HistoricalName",
    "NameBase",
    "NameLifecycleMixin",
    "NamePerson",
    "NameThing",
]

_UNSET: Any = object()


@dataclass(repr=False, config=ConfigDict(frozen=True, extra="forbid", strict=True))
class HistoricVariant(IntrospectableMixin):
    """Discrete historical naming phase for an evolutionary place, site, or artifact."""

    raw: str = Field(..., description="Verbatim historical name as recorded in source.")
    name: str = Field(..., description="Standardized or normalized historical name form.")
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
        if not self.raw.strip():
            raise ModelFormatError("HistoricVariant 'raw' cannot be empty or whitespace.")
        if not self.name.strip():
            raise ModelFormatError("HistoricVariant 'name' cannot be empty or whitespace.")
        if self.comment is not None and not self.comment.strip():
            raise ModelFormatError("HistoricVariant 'comment' cannot be blank if provided.")

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
        if not isinstance(raw, str) or not raw.strip():
            raise ModelFormatError("HistoricVariant 'raw' cannot be empty or whitespace.")

        if isinstance(historic_name_type, HistoricNameType):
            res_type = historic_name_type
        elif isinstance(historic_name_type, str):
            try:
                res_type = HistoricNameType(historic_name_type.strip().upper())
            except ValueError as exc:
                raise ModelFormatError(
                    f"Invalid HistoricNameType value: '{historic_name_type}'."
                ) from exc
        else:
            raise ModelFormatError(
                f"Invalid HistoricNameType type: {type(historic_name_type).__name__}."
            )

        norm_name = name.strip() if name and name.strip() else raw.strip()
        clean_comment = comment.strip() if comment and comment.strip() else None
        return cls(
            raw=raw.strip(),
            name=norm_name,
            historic_name_type=res_type,
            valid_period=valid_period,
            comment=clean_comment,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize HistoricVariant to a dictionary."""
        data: dict[str, Any] = {
            "raw": self.raw,
            "name": self.name,
            "historic_name_type": self.historic_name_type.value,
        }
        if self.valid_period is not None:
            data["valid_period"] = self.valid_period.to_dict()
        if self.comment is not None:
            data["comment"] = self.comment
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HistoricVariant:
        """Deserialize a dictionary payload into an immutable HistoricVariant."""
        if not isinstance(data, dict):
            raise ModelFormatError("HistoricVariant payload must be a dictionary.")

        raw_val = data.get("raw")
        if not isinstance(raw_val, str) or not raw_val.strip():
            raise ModelFormatError("Missing required field 'raw' for HistoricVariant.")

        name_val = data.get("name") or raw_val

        raw_period = data.get("valid_period")
        period_obj: TimePeriod | None = None
        if isinstance(raw_period, dict):
            period_obj = TimePeriod.from_dict(raw_period)
        elif isinstance(raw_period, TimePeriod):
            period_obj = raw_period

        return cls.create(
            raw=raw_val,
            name=str(name_val),
            historic_name_type=data.get("historic_name_type", HistoricNameType.HISTORICAL),
            valid_period=period_obj,
            comment=data.get("comment"),
        )

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return (
            f"HistoricVariant(raw={self.raw!r}, name={self.name!r}, "
            f"historic_name_type={self.historic_name_type}, "
            f"valid_period={self.valid_period!r}, comment={self.comment!r})"
        )


class NameLifecycleMixin(IntrospectableMixin):
    """Reusable copy-on-write mutators for naming models."""

    raw: str
    canonical: str
    aliases: list[str]
    alt_spellings: list[str]
    comment: str | None

    def update_raw(self, raw: str) -> Self:
        """Return a new immutable copy with updated verbatim raw text."""
        if not isinstance(raw, str) or not raw.strip():
            raise ModelFormatError("Raw name cannot be empty or whitespace.")
        clean = raw.strip()
        if clean == self.raw:
            return self
        return cast(Self, replace(cast(Any, self), raw=clean))

    def update_canonical(self, canonical: str) -> Self:
        """Return a new immutable copy with updated canonical display name."""
        if not isinstance(canonical, str) or not canonical.strip():
            raise ModelFormatError("Canonical name cannot be empty or whitespace.")
        clean = canonical.strip()
        if clean == self.canonical:
            return self
        return cast(Self, replace(cast(Any, self), canonical=clean))

    def add_alias(self, alias: str) -> Self:
        """Return a new immutable copy with unique alias appended."""
        if not isinstance(alias, str) or not alias.strip():
            raise ModelFormatError("Alias cannot be empty or whitespace.")
        clean = alias.strip()
        if clean in self.aliases:
            return self
        return cast(Self, replace(cast(Any, self), aliases=[*self.aliases, clean]))

    def remove_alias(self, alias: str) -> Self:
        """Return a new immutable copy with target alias removed."""
        clean = alias.strip() if isinstance(alias, str) else ""
        if not clean or clean not in self.aliases:
            return self
        return cast(Self, replace(cast(Any, self), aliases=[a for a in self.aliases if a != clean]))

    def add_spelling(self, spelling: str) -> Self:
        """Return a new immutable copy with unique alternate spelling appended."""
        if not isinstance(spelling, str) or not spelling.strip():
            raise ModelFormatError("Alternate spelling cannot be empty or whitespace.")
        clean = spelling.strip()
        if clean in self.alt_spellings:
            return self
        return cast(Self, replace(cast(Any, self), alt_spellings=[*self.alt_spellings, clean]))

    def remove_spelling(self, spelling: str) -> Self:
        """Return a new immutable copy with target alternate spelling removed."""
        clean = spelling.strip() if isinstance(spelling, str) else ""
        if not clean or clean not in self.alt_spellings:
            return self
        return cast(
            Self,
            replace(cast(Any, self), alt_spellings=[s for s in self.alt_spellings if s != clean]),
        )

    def update_comment(self, comment: str | None) -> Self:
        """Return a new immutable copy with updated contextual comment."""
        clean = comment.strip() if comment and comment.strip() else None
        if clean == self.comment:
            return self
        return cast(Self, replace(cast(Any, self), comment=clean))


@dataclass(
    repr=False,
    config=ConfigDict(frozen=True, extra="forbid", strict=True),
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
        if not self.raw.strip():
            raise ModelFormatError(f"{self.__class__.__name__} 'raw' cannot be empty.")
        if not self.canonical.strip():
            raise ModelFormatError(f"{self.__class__.__name__} 'canonical' cannot be empty.")
        if any(not a.strip() for a in self.aliases):
            raise ModelFormatError("aliases cannot contain empty or whitespace strings.")
        if len(self.aliases) != len(set(self.aliases)):
            raise ModelFormatError("Duplicate entries found in aliases.")
        if any(not s.strip() for s in self.alt_spellings):
            raise ModelFormatError("alt_spellings cannot contain empty or whitespace strings.")
        if len(self.alt_spellings) != len(set(self.alt_spellings)):
            raise ModelFormatError("Duplicate entries found in alt_spellings.")
        if self.comment is not None and not self.comment.strip():
            raise ModelFormatError(f"{self.__class__.__name__} 'comment' cannot be blank.")

    def __str__(self) -> str:
        return self.canonical

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(raw={self.raw!r}, canonical={self.canonical!r}, "
            f"aliases={self.aliases!r}, alt_spellings={self.alt_spellings!r}, "
            f"comment={self.comment!r})"
        )


@dataclass(
    repr=False,
    config=ConfigDict(frozen=True, extra="forbid", strict=True),
    kw_only=True,
)
class NamePerson(NameBase):
    """Specialized persona noun model supporting discrete titles, parts, and married names."""

    prefix: str | None = Field(default=None, description="Title, rank, or honorific style.")
    given: str | None = Field(default=None, description="First or given name.")
    middle: str | None = Field(default=None, description="Middle name(s) or initials.")
    surname: str | None = Field(default=None, description="Birth surname (patronymic/matronymic).")
    suffix: str | None = Field(default=None, description="Generational or post-nominal suffix.")
    married: list[str] = Field(
        default_factory=list, description="Searchable list of all married surnames."
    )

    def __post_init__(self) -> None:
        """Enforce persona invariants."""
        super().__post_init__()
        if any(not m.strip() for m in self.married):
            raise ModelFormatError("married cannot contain empty or whitespace strings.")
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
        parts: list[str] = [p for p in candidate_parts if isinstance(p, str) and p.strip()]
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
        if not isinstance(raw, str) or not raw.strip():
            raise ModelFormatError("NamePerson 'raw' cannot be empty or whitespace.")

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

        computed_canonical = canonical.strip() if canonical and canonical.strip() else None
        if not computed_canonical:
            name_parts = [
                p.strip()
                for p in (prefix, given, middle, surname, suffix)
                if isinstance(p, str) and p.strip()
            ]
            computed_canonical = " ".join(name_parts) if name_parts else raw.strip()

        return cls(
            raw=raw.strip(),
            canonical=computed_canonical,
            prefix=prefix.strip() if prefix and prefix.strip() else None,
            given=given.strip() if given and given.strip() else None,
            middle=middle.strip() if middle and middle.strip() else None,
            surname=surname.strip() if surname and surname.strip() else None,
            suffix=suffix.strip() if suffix and suffix.strip() else None,
            married=clean_married,
            aliases=clean_aliases,
            alt_spellings=clean_spellings,
            comment=comment.strip() if comment and comment.strip() else None,
        )

    def add_married(self, married_name: str) -> NamePerson:
        """Return a new immutable copy with unique married surname appended."""
        if not isinstance(married_name, str) or not married_name.strip():
            raise ModelFormatError("Married name cannot be empty or whitespace.")
        clean = married_name.strip()
        if clean in self.married:
            return self
        return replace(self, married=[*self.married, clean])

    def remove_married(self, married_name: str) -> NamePerson:
        """Return a new immutable copy with target married surname removed."""
        clean = married_name.strip() if isinstance(married_name, str) else ""
        if not clean or clean not in self.married:
            return self
        return replace(self, married=[m for m in self.married if m != clean])

    def update_parts(
        self,
        prefix: str | None = _UNSET,
        given: str | None = _UNSET,
        middle: str | None = _UNSET,
        surname: str | None = _UNSET,
        suffix: str | None = _UNSET,
    ) -> NamePerson:
        """Return a new immutable copy with updated personal onomastic components.

        Passing None or blank whitespace clears the component to None; omitting an
        argument preserves the existing component value.
        """

        def _resolve(incoming: str | None, current: str | None) -> str | None:
            if incoming is _UNSET:
                return current
            if incoming is None:
                return None
            return incoming.strip() if incoming.strip() else None

        return replace(
            self,
            prefix=_resolve(prefix, self.prefix),
            given=_resolve(given, self.given),
            middle=_resolve(middle, self.middle),
            surname=_resolve(surname, self.surname),
            suffix=_resolve(suffix, self.suffix),
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
        if not isinstance(raw_val, str) or not raw_val.strip():
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
            raw=raw_val,
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
            raise ModelFormatError(f"Failed to parse NamePerson JSON string: {exc}") from exc
        return cls.from_dict(data)

    def __str__(self) -> str:
        """Return full structured personal name representation."""
        return self.full_name

    def __repr__(self) -> str:
        return (
            f"NamePerson(raw={self.raw!r}, canonical={self.canonical!r}, "
            f"prefix={self.prefix!r}, given={self.given!r}, middle={self.middle!r}, "
            f"surname={self.surname!r}, suffix={self.suffix!r}, "
            f"married={self.married!r}, aliases={self.aliases!r}, "
            f"alt_spellings={self.alt_spellings!r}, comment={self.comment!r})"
        )


@dataclass(
    repr=False,
    config=ConfigDict(frozen=True, extra="forbid", strict=True),
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
        if not isinstance(raw, str) or not raw.strip():
            raise ModelFormatError("NameThing 'raw' cannot be empty or whitespace.")

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

        computed_can = canonical.strip() if canonical and canonical.strip() else raw.strip()

        return cls(
            raw=raw.strip(),
            canonical=computed_can,
            aliases=clean_aliases,
            alt_spellings=clean_spellings,
            historic=list(historic) if historic else [],
            comment=comment.strip() if comment and comment.strip() else None,
        )

    def add_historic_variant(
        self,
        raw: str,
        name: str | None = None,
        historic_name_type: HistoricNameType | str = HistoricNameType.HISTORICAL,
        valid_period: TimePeriod | None = None,
        comment: str | None = None,
    ) -> NameThing:
        """Return a new immutable copy appending a unique HistoricVariant."""
        variant = HistoricVariant.create(
            raw=raw,
            name=name,
            historic_name_type=historic_name_type,
            valid_period=valid_period,
            comment=comment,
        )
        if variant in self.historic:
            return self
        return replace(self, historic=[*self.historic, variant])

    def remove_historic_variant(self, raw: str) -> NameThing:
        """Return a new immutable copy removing matching HistoricVariants by raw text."""
        clean = raw.strip() if isinstance(raw, str) else ""
        if not clean:
            return self
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
        if not isinstance(raw_val, str) or not raw_val.strip():
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
                elif isinstance(item, HistoricVariant):
                    variants.append(item)

        alt_spellings_list = data.get("alt_spellings")
        if alt_spellings_list is None:
            alt_spellings_list = data.get("alternate_spellings")

        comment_val = data.get("comment")
        if comment_val is None:
            comment_val = data.get("notes")

        return cls.create(
            raw=raw_val,
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
            raise ModelFormatError(f"Failed to parse NameThing JSON string: {exc}") from exc
        return cls.from_dict(data)

    def __str__(self) -> str:
        """Render concise human-readable title representation."""
        return self.canonical

    def __repr__(self) -> str:
        return (
            f"NameThing(raw={self.raw!r}, canonical={self.canonical!r}, "
            f"aliases={self.aliases!r}, alt_spellings={self.alt_spellings!r}, "
            f"historic={self.historic!r}, comment={self.comment!r})"
        )


# ==============================================================================
# BACKWARD COMPATIBILITY ALIASES
# ==============================================================================
CanonicalName = NamePerson
HistoricalName = NameThing
