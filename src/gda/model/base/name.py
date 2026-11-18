"""Path: src/gda/model/base/name.py

Onomastic domain composites for personal names and historical entity appellations.

Operational Role:
    Defines NameLifecycleMixin, NameBase, NamePerson, HistoricVariant, and
    NameThing. Provides structured personal name decomposition, phonetic-ready
    normalization, multilingual support, and temporal HistoricVariant tracking
    with copy-on-write state transitions.
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
from gda.util.enums import coerce_enum
from gda.util.text import clean_unique_strings

__version__ = "1.0.0+build.7"

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


def _coerce_historic_name_type(value: HistoricNameType | str) -> HistoricNameType:
    """Resolve a HistoricNameType enum member or string token."""
    if not isinstance(value, (HistoricNameType, str)):
        raise ModelFormatError(
            f"Invalid HistoricNameType type: expected HistoricNameType or str, got {type(value).__name__}.",
            error_code="ERR_MODEL_FORMAT",
        )
    try:
        return coerce_enum(HistoricNameType, value, field_name="historic_name_type")
    except ModelFormatError as err:
        raise ModelFormatError(
            f"Invalid HistoricNameType value: '{value}'.",
            error_code="ERR_MODEL_FORMAT",
            details={"historic_name_type": str(value)},
        ) from err


def _validate_non_empty_unique_list(items: list[str], field_label: str) -> None:
    """Enforce that a string list contains no blank entries or duplicates."""
    seen: set[str] = set()
    for entry in items:
        if not entry or not entry.strip():
            raise ModelFormatError(
                f"{field_label} cannot contain empty or whitespace strings.",
                error_code="ERR_MODEL_FORMAT",
            )
        if entry in seen:
            raise ModelFormatError(
                f"Duplicate entries found in {field_label}: '{entry}'.",
                error_code="ERR_MODEL_FORMAT",
            )
        seen.add(entry)


def _clean_optional_part(val: str | None) -> str | None:
    """Return trimmed non-empty string or None when None/blank."""
    if val is None:
        return None
    cleaned = val.strip()
    return cleaned if cleaned else None


def _assemble_person_parts(
    prefix: str | None,
    given: str | None,
    middle: str | None,
    surname: str | None,
    suffix: str | None,
    fallback: str,
) -> str:
    """Join non-empty personal name parts in canonical Western order or return fallback."""
    parts = [p for p in (prefix, given, middle, surname, suffix) if p]
    return " ".join(parts) if parts else fallback


# ==============================================================================
# SECTION 1: REUSABLE COPY-ON-WRITE NAME LIFECYCLE MIXIN
# ==============================================================================


class NameLifecycleMixin(IntrospectableMixin):
    """Copy-on-write mutator mixin for NameBase subclasses."""

    raw: str
    canonical: str
    aliases: list[str]
    alt_spellings: list[str]
    comment: str | None

    def update_raw(self, raw: str) -> Self:
        """Return a copy with updated raw name string."""
        clean = raw.strip()
        if not clean:
            raise ModelFormatError("Raw name cannot be empty or whitespace.")
        if clean == self.raw:
            return self
        return cast(Self, replace(cast(Any, self), raw=clean))

    def update_canonical(self, canonical: str) -> Self:
        """Return a copy with updated canonical name string."""
        clean = canonical.strip()
        if not clean:
            raise ModelFormatError("Canonical name cannot be empty or whitespace.")
        if clean == self.canonical:
            return self
        return cast(Self, replace(cast(Any, self), canonical=clean))

    def add_alias(self, alias: str) -> Self:
        """Append a unique alias to aliases."""
        clean = alias.strip()
        if not clean:
            raise ModelFormatError("Alias cannot be empty or whitespace.")
        if clean in self.aliases:
            return self
        return cast(Self, replace(cast(Any, self), aliases=[*self.aliases, clean]))

    def remove_alias(self, alias: str) -> Self:
        """Remove an alias from aliases if present."""
        clean = alias.strip()
        if not clean or clean not in self.aliases:
            return self
        return cast(
            Self,
            replace(cast(Any, self), aliases=[a for a in self.aliases if a != clean]),
        )

    def add_spelling(self, spelling: str) -> Self:
        """Append a unique alternate spelling to alt_spellings."""
        clean = spelling.strip()
        if not clean:
            raise ModelFormatError("Alternate spelling cannot be empty or whitespace.")
        if clean in self.alt_spellings:
            return self
        return cast(
            Self,
            replace(cast(Any, self), alt_spellings=[*self.alt_spellings, clean]),
        )

    def remove_spelling(self, spelling: str) -> Self:
        """Remove an alternate spelling from alt_spellings if present."""
        clean = spelling.strip()
        if not clean or clean not in self.alt_spellings:
            return self
        return cast(
            Self,
            replace(
                cast(Any, self),
                alt_spellings=[s for s in self.alt_spellings if s != clean],
            ),
        )

    def update_comment(self, comment: str | None) -> Self:
        """Update or clear the optional research comment."""
        clean = _clean_optional_part(comment)
        if clean == self.comment:
            return self
        return cast(Self, replace(cast(Any, self), comment=clean))


# ==============================================================================
# SECTION 2: FOUNDATIONAL NAME BASE
# ==============================================================================


@dataclass(repr=False, config=ConfigDict(frozen=True, extra="forbid", strict=True))
class NameBase(NameLifecycleMixin):
    """Foundational immutable value object for personal and institutional names."""

    raw: str = Field(..., description="Verbatim name as recorded in the source.")
    canonical: str = Field(..., description="Standardized display/index name.")
    aliases: list[str] = Field(default_factory=list, description="Known aliases or nicknames.")
    alt_spellings: list[str] = Field(
        default_factory=list,
        description="Orthographic or phonetic spelling variants.",
    )
    comment: str | None = Field(default=None, description="Optional onomastic note.")

    def __post_init__(self) -> None:
        """Validate non-empty raw/canonical strings and unique non-empty list items."""
        if not self.raw or not self.raw.strip():
            raise ModelFormatError("NameBase 'raw' cannot be empty or whitespace.")
        if not self.canonical or not self.canonical.strip():
            raise ModelFormatError("NameBase 'canonical' cannot be empty or whitespace.")

        _validate_non_empty_unique_list(self.aliases, "aliases")
        _validate_non_empty_unique_list(self.alt_spellings, "alt_spellings")

        if self.comment is not None and not self.comment.strip():
            raise ModelFormatError("NameBase 'comment' cannot be blank if provided.")

    def __str__(self) -> str:
        return self.canonical

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(raw={self.raw!r}, canonical={self.canonical!r}, "
            f"aliases={self.aliases!r}, alt_spellings={self.alt_spellings!r}, "
            f"comment={self.comment!r})"
        )


# ==============================================================================
# SECTION 3: PERSONAL ONOMASTIC COMPOSITE (NamePerson)
# ==============================================================================


@dataclass(repr=False, config=ConfigDict(frozen=True, extra="forbid", strict=True))
class NamePerson(NameBase):
    """Structured personal name model with discrete onomastic components."""

    prefix: str | None = Field(default=None, description="Honorific or title prefix.")
    given: str | None = Field(default=None, description="First or given name.")
    middle: str | None = Field(default=None, description="Middle name(s) or initial(s).")
    surname: str | None = Field(default=None, description="Family surname.")
    suffix: str | None = Field(default=None, description="Generational or professional suffix.")
    married: list[str] = Field(
        default_factory=list,
        description="Assumed married surnames.",
    )

    def __post_init__(self) -> None:
        """Validate base invariants and married surname list uniqueness."""
        super().__post_init__()
        _validate_non_empty_unique_list(self.married, "married")

    @property
    def full_name(self) -> str:
        """Assemble full display name from discrete parts or fall back to canonical."""
        return _assemble_person_parts(
            self.prefix,
            self.given,
            self.middle,
            self.surname,
            self.suffix,
            self.canonical,
        )

    @classmethod
    def create(
        cls,
        raw: str,
        canonical: str | None = None,
        *,
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
        """Factory constructor normalizing parts, computing canonical fallback, and deduplicating lists."""
        clean_raw = raw.strip() if isinstance(raw, str) else ""
        if not clean_raw:
            raise ModelFormatError("NamePerson 'raw' cannot be empty or whitespace.")

        c_prefix = _clean_optional_part(prefix)
        c_given = _clean_optional_part(given)
        c_middle = _clean_optional_part(middle)
        c_surname = _clean_optional_part(surname)
        c_suffix = _clean_optional_part(suffix)

        clean_can = _clean_optional_part(canonical) or _assemble_person_parts(
            c_prefix, c_given, c_middle, c_surname, c_suffix, clean_raw
        )

        return cls(
            raw=clean_raw,
            canonical=clean_can,
            prefix=c_prefix,
            given=c_given,
            middle=c_middle,
            surname=c_surname,
            suffix=c_suffix,
            married=clean_unique_strings(married),
            aliases=clean_unique_strings(aliases),
            alt_spellings=clean_unique_strings(alt_spellings),
            comment=_clean_optional_part(comment),
        )

    def update_parts(
        self,
        *,
        prefix: str | None = ...,  # type: ignore[assignment]
        given: str | None = ...,  # type: ignore[assignment]
        middle: str | None = ...,  # type: ignore[assignment]
        surname: str | None = ...,  # type: ignore[assignment]
        suffix: str | None = ...,  # type: ignore[assignment]
    ) -> NamePerson:
        """Update discrete name components, preserving omitted arguments."""
        new_prefix = self.prefix if prefix is ... else _clean_optional_part(prefix)
        new_given = self.given if given is ... else _clean_optional_part(given)
        new_middle = self.middle if middle is ... else _clean_optional_part(middle)
        new_surname = self.surname if surname is ... else _clean_optional_part(surname)
        new_suffix = self.suffix if suffix is ... else _clean_optional_part(suffix)

        return replace(
            self,
            prefix=new_prefix,
            given=new_given,
            middle=new_middle,
            surname=new_surname,
            suffix=new_suffix,
        )

    def add_married(self, surname: str) -> NamePerson:
        """Append a unique married surname."""
        clean = surname.strip()
        if not clean:
            raise ModelFormatError("Married name cannot be empty or whitespace.")
        if clean in self.married:
            return self
        return replace(self, married=[*self.married, clean])

    def remove_married(self, surname: str) -> NamePerson:
        """Remove a married surname if present."""
        clean = surname.strip()
        if not clean or clean not in self.married:
            return self
        return replace(self, married=[m for m in self.married if m != clean])

    def to_dict(self) -> dict[str, Any]:
        """Serialize NamePerson to a dictionary, omitting unset optional scalars."""
        data: dict[str, Any] = {
            "raw": self.raw,
            "canonical": self.canonical,
            "married": list(self.married),
            "aliases": list(self.aliases),
            "alt_spellings": list(self.alt_spellings),
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
        """Rehydrate NamePerson from a dictionary, supporting current and legacy keys."""
        if not isinstance(data, dict):
            raise ModelFormatError("NamePerson payload must be a dictionary.")

        raw_val = data.get("raw") or data.get("raw_name")
        if not isinstance(raw_val, str) or not raw_val.strip():
            raise ModelFormatError("Missing required field 'raw' in NamePerson payload.")

        can_val = data.get("canonical") or data.get("canonical_name")
        married_val = data.get("married") or data.get("married_names") or []
        alt_val = data.get("alt_spellings") or data.get("alternate_spellings") or []
        comment_val = data.get("comment") if "comment" in data else data.get("notes")

        return cls.create(
            raw=raw_val,
            canonical=can_val if isinstance(can_val, str) else None,
            prefix=data.get("prefix"),
            given=data.get("given"),
            middle=data.get("middle"),
            surname=data.get("surname"),
            suffix=data.get("suffix"),
            married=list(married_val) if isinstance(married_val, list) else None,
            aliases=list(data["aliases"]) if isinstance(data.get("aliases"), list) else None,
            alt_spellings=list(alt_val) if isinstance(alt_val, list) else None,
            comment=comment_val if isinstance(comment_val, str) else None,
        )

    def to_json(self) -> str:
        """Serialize NamePerson to a deterministic JSON string."""
        return json.dumps(self.to_dict(), sort_keys=True)

    @classmethod
    def from_json(cls, json_str: str) -> NamePerson:
        """Deserialize NamePerson from a JSON string."""
        try:
            payload = json.loads(json_str)
        except Exception as exc:
            raise ModelFormatError(f"Failed to parse NamePerson JSON string: {exc}") from exc
        return cls.from_dict(payload)

    def __str__(self) -> str:
        return self.full_name

    def __repr__(self) -> str:
        return (
            f"NamePerson(raw={self.raw!r}, canonical={self.canonical!r}, "
            f"given={self.given!r}, surname={self.surname!r})"
        )


# ==============================================================================
# SECTION 4: HISTORIC VARIANT & ENTITY APPELLATION (HistoricVariant, NameThing)
# ==============================================================================


@dataclass(repr=False, config=ConfigDict(frozen=True, extra="forbid", strict=True))
class HistoricVariant(IntrospectableMixin):
    """Historical or regional name variant with optional temporal bounding."""

    raw: str = Field(..., description="Verbatim historical name string.")
    name: str = Field(..., description="Normalized historical variant name.")
    historic_name_type: HistoricNameType = Field(
        default=HistoricNameType.HISTORICAL,
        description="Classification of the historical name variant.",
    )
    valid_period: TimePeriod | None = Field(
        default=None,
        description="Optional temporal span during which the name was active.",
    )
    comment: str | None = Field(default=None, description="Contextual historical note.")

    def __post_init__(self) -> None:
        """Validate non-empty raw and normalized name fields."""
        if not self.raw or not self.raw.strip():
            raise ModelFormatError("HistoricVariant 'raw' cannot be empty or whitespace.")
        if not self.name or not self.name.strip():
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
        """Factory constructor normalizing strings and coercing HistoricNameType."""
        clean_raw = raw.strip() if isinstance(raw, str) else ""
        if not clean_raw:
            raise ModelFormatError("HistoricVariant 'raw' cannot be empty or whitespace.")

        clean_name = _clean_optional_part(name) or clean_raw
        resolved_type = _coerce_historic_name_type(historic_name_type)
        return cls(
            raw=clean_raw,
            name=clean_name,
            historic_name_type=resolved_type,
            valid_period=valid_period,
            comment=_clean_optional_part(comment),
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
        """Rehydrate HistoricVariant from a dictionary."""
        if not isinstance(data, dict):
            raise ModelFormatError("HistoricVariant payload must be a dictionary.")

        raw_val = data.get("raw")
        if not isinstance(raw_val, str) or not raw_val.strip():
            raise ModelFormatError("Missing required field 'raw' in HistoricVariant payload.")

        raw_period = data.get("valid_period")
        resolved_period: TimePeriod | None = None
        if isinstance(raw_period, TimePeriod):
            resolved_period = raw_period
        elif isinstance(raw_period, dict):
            resolved_period = TimePeriod.from_dict(raw_period)

        return cls.create(
            raw=raw_val,
            name=data.get("name"),
            historic_name_type=data.get("historic_name_type", HistoricNameType.HISTORICAL),
            valid_period=resolved_period,
            comment=data.get("comment"),
        )

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return (
            f"HistoricVariant(raw={self.raw!r}, name={self.name!r}, "
            f"historic_name_type={self.historic_name_type!r})"
        )


@dataclass(repr=False, config=ConfigDict(frozen=True, extra="forbid", strict=True))
class NameThing(NameBase):
    """Structured appellation model for locations, sites, and organizations."""

    historic: list[HistoricVariant] = Field(
        default_factory=list,
        description="Chronological or regional historical name variants.",
    )

    @classmethod
    def create(
        cls,
        raw: str,
        canonical: str | None = None,
        *,
        aliases: list[str] | None = None,
        alt_spellings: list[str] | None = None,
        historic: list[HistoricVariant] | None = None,
        comment: str | None = None,
    ) -> NameThing:
        """Factory constructor normalizing strings and deduplicating alias/spelling lists."""
        clean_raw = raw.strip() if isinstance(raw, str) else ""
        if not clean_raw:
            raise ModelFormatError("NameThing 'raw' cannot be empty or whitespace.")

        clean_can = _clean_optional_part(canonical) or clean_raw
        return cls(
            raw=clean_raw,
            canonical=clean_can,
            aliases=clean_unique_strings(aliases),
            alt_spellings=clean_unique_strings(alt_spellings),
            historic=list(historic) if historic else [],
            comment=_clean_optional_part(comment),
        )

    def add_historic_variant(
        self,
        raw: str,
        name: str | None = None,
        historic_name_type: HistoricNameType | str = HistoricNameType.HISTORICAL,
        valid_period: TimePeriod | None = None,
        comment: str | None = None,
    ) -> NameThing:
        """Mint and append a HistoricVariant if not already present."""
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

    def remove_historic_variant(self, name_or_raw: str) -> NameThing:
        """Remove any HistoricVariant matching name or raw."""
        clean = name_or_raw.strip()
        if not clean:
            return self
        filtered = [v for v in self.historic if v.name != clean and v.raw != clean]
        if len(filtered) == len(self.historic):
            return self
        return replace(self, historic=filtered)

    def to_dict(self) -> dict[str, Any]:
        """Serialize NameThing to a dictionary."""
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
        """Rehydrate NameThing from a dictionary."""
        if not isinstance(data, dict):
            raise ModelFormatError("NameThing payload must be a dictionary.")

        raw_val = data.get("raw") or data.get("raw_name")
        if not isinstance(raw_val, str) or not raw_val.strip():
            raise ModelFormatError("Missing required field 'raw' in NameThing payload.")

        can_val = data.get("canonical") or data.get("canonical_name")
        alt_val = data.get("alt_spellings") or data.get("alternate_spellings") or []
        comment_val = data.get("comment") if "comment" in data else data.get("notes")

        raw_hist = data.get("historic", [])
        resolved_hist: list[HistoricVariant] = []
        if isinstance(raw_hist, list):
            for item in raw_hist:
                if isinstance(item, HistoricVariant):
                    resolved_hist.append(item)
                elif isinstance(item, dict):
                    resolved_hist.append(HistoricVariant.from_dict(item))

        return cls.create(
            raw=raw_val,
            canonical=can_val if isinstance(can_val, str) else None,
            aliases=list(data["aliases"]) if isinstance(data.get("aliases"), list) else None,
            alt_spellings=list(alt_val) if isinstance(alt_val, list) else None,
            historic=resolved_hist,
            comment=comment_val if isinstance(comment_val, str) else None,
        )

    def to_json(self) -> str:
        """Serialize NameThing to a deterministic JSON string."""
        return json.dumps(self.to_dict(), sort_keys=True)

    @classmethod
    def from_json(cls, json_str: str) -> NameThing:
        """Deserialize NameThing from a JSON string."""
        try:
            payload = json.loads(json_str)
        except Exception as exc:
            raise ModelFormatError(f"Failed to parse NameThing JSON string: {exc}") from exc
        return cls.from_dict(payload)


# Backward-compatible aliases
CanonicalName = NamePerson
HistoricalName = NameThing
