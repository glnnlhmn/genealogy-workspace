"""Path: src/gda/model/xref/surname_xref.py

Onomastic surname equivalence and orthographic variant expansion index model.

Operational Role:
    Defines SurnameXRef (frozen Pydantic dataclass) as a derived relational index
    row mapping a canonical surname to a variant surname spelling, capturing
    variant_name_type (HistoricNameType) and optional variant_phonetic_code.
    Enforces bi-conditional identity between HistoricNameType.PRIMARY and
    canonical_surname == variant_surname.
"""

from __future__ import annotations

import json
from functools import total_ordering
from typing import Any

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.enums.vital import HistoricNameType
from gda.core.errors import ModelFormatError
from gda.core.introspectable import IntrospectableMixin
from gda.util.enums import coerce_enum
from gda.util.text import clean_string

__version__ = "1.0.0+build.3"

__all__ = [
    "SurnameXRef",
]


def _normalize_surname(raw: str, field_name: str) -> str:
    """Normalize a surname token to stripped uppercase via clean_string and reject empty values."""
    clean = (clean_string(str(raw)) or "").upper()
    if not clean:
        raise ModelFormatError(f"SurnameXRef '{field_name}' cannot be empty or whitespace.")
    return clean


def _parse_historic_name_type(raw: HistoricNameType | str) -> HistoricNameType:
    """Resolve HistoricNameType by enum instance, exact value, or uppercase member name."""
    try:
        return coerce_enum(HistoricNameType, raw, field_name="variant_name_type")
    except ModelFormatError as err:
        raise ModelFormatError(f"Invalid HistoricNameType value: '{raw}'.") from err


@total_ordering
@dataclass(
    repr=False,
    config=ConfigDict(frozen=True, extra="forbid", strict=True),
    kw_only=True,
)
class SurnameXRef(IntrospectableMixin):
    """Immutable index row mapping a canonical surname to an orthographic or historical variant."""

    canonical_surname: str = Field(
        ...,
        description="Standardized uppercase root surname (e.g., 'ABBOTT').",
    )
    variant_surname: str = Field(
        ...,
        description="Uppercase variant spelling (e.g., 'ABBOT', or 'ABBOTT' for PRIMARY).",
    )
    variant_name_type: HistoricNameType = Field(
        default=HistoricNameType.PRIMARY,
        description="Classification of the variant surname (PRIMARY, HISTORICAL, COLLOQUIAL, etc.).",
    )
    variant_phonetic_code: str | None = Field(
        default=None,
        description="Optional uppercase phonetic index code (e.g., Soundex 'A130') for the variant.",
    )

    def __post_init__(self) -> None:
        """Enforce uppercase normalization and PRIMARY equality invariants."""
        clean_canon = _normalize_surname(self.canonical_surname, "canonical_surname")
        if clean_canon != self.canonical_surname:
            object.__setattr__(self, "canonical_surname", clean_canon)

        clean_var = _normalize_surname(self.variant_surname, "variant_surname")
        if clean_var != self.variant_surname:
            object.__setattr__(self, "variant_surname", clean_var)

        if self.variant_phonetic_code is not None:
            clean_phon = self.variant_phonetic_code.strip().upper()
            if not clean_phon:
                raise ModelFormatError(
                    "SurnameXRef 'variant_phonetic_code' cannot be empty or whitespace when provided."
                )
            if clean_phon != self.variant_phonetic_code:
                object.__setattr__(self, "variant_phonetic_code", clean_phon)

        if self.variant_name_type is HistoricNameType.PRIMARY and clean_canon != clean_var:
            raise ModelFormatError(
                "SurnameXRef with variant_name_type=PRIMARY requires "
                f"canonical_surname ('{clean_canon}') == variant_surname ('{clean_var}')."
            )

        if clean_canon == clean_var and self.variant_name_type is not HistoricNameType.PRIMARY:
            raise ModelFormatError(
                "SurnameXRef where canonical_surname == variant_surname "
                f"('{clean_canon}') must use variant_name_type=PRIMARY."
            )

    @property
    def is_canonical_self(self) -> bool:
        """Return True when variant_surname equals canonical_surname (PRIMARY entry)."""
        return self.canonical_surname == self.variant_surname

    @property
    def xref_key(self) -> str:
        """Return dynamic compound index key '<canonical_surname>::<variant_surname>'."""
        return f"{self.canonical_surname}::{self.variant_surname}"

    @property
    def sort_key(self) -> tuple[str, int, str, str]:
        """Return deterministic ordering tuple (canonical_surname, primary_first_rank, variant_surname, type)."""
        primary_rank = 0 if self.is_canonical_self else 1
        return (
            self.canonical_surname,
            primary_rank,
            self.variant_surname,
            self.variant_name_type.value,
        )

    @classmethod
    def create(
        cls,
        canonical_surname: str,
        variant_surname: str | None = None,
        variant_name_type: HistoricNameType | str | None = None,
        variant_phonetic_code: str | None = None,
    ) -> SurnameXRef:
        """Factory constructor instantiating a validated SurnameXRef."""
        clean_canon = _normalize_surname(canonical_surname, "canonical_surname")
        clean_var = (
            _normalize_surname(variant_surname, "variant_surname")
            if variant_surname is not None
            else clean_canon
        )

        if variant_name_type is not None:
            res_type = _parse_historic_name_type(variant_name_type)
        elif clean_canon == clean_var:
            res_type = HistoricNameType.PRIMARY
        else:
            res_type = HistoricNameType.HISTORICAL

        return cls(
            canonical_surname=clean_canon,
            variant_surname=clean_var,
            variant_name_type=res_type,
            variant_phonetic_code=variant_phonetic_code,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize SurnameXRef to a dictionary."""
        data: dict[str, Any] = {
            "canonical_surname": self.canonical_surname,
            "variant_surname": self.variant_surname,
            "variant_name_type": self.variant_name_type.value,
        }
        if self.variant_phonetic_code is not None:
            data["variant_phonetic_code"] = self.variant_phonetic_code
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SurnameXRef:
        """Deserialize a dictionary payload into a SurnameXRef."""
        if not isinstance(data, dict):
            raise ModelFormatError("SurnameXRef payload must be a dictionary.")

        canon = data.get("canonical_surname")
        var = data.get("variant_surname")

        if canon is None or var is None:
            raise ModelFormatError(
                "SurnameXRef requires 'canonical_surname' and 'variant_surname'."
            )

        return cls.create(
            canonical_surname=str(canon),
            variant_surname=str(var),
            variant_name_type=data.get("variant_name_type"),
            variant_phonetic_code=data.get("variant_phonetic_code"),
        )

    def to_json(self) -> str:
        """Serialize SurnameXRef to a JSON formatted string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_json(cls, payload: str) -> SurnameXRef:
        """Deserialize a JSON string directly into a SurnameXRef."""
        try:
            data = json.loads(payload)
        except Exception as exc:
            raise ModelFormatError(f"Failed to parse SurnameXRef JSON string: {exc}") from exc
        return cls.from_dict(data)

    def __lt__(self, other: Any) -> bool:
        """Support deterministic surname and primary-first sorting."""
        if isinstance(other, SurnameXRef):
            return self.sort_key < other.sort_key
        return NotImplemented

    def __str__(self) -> str:
        phon = f" [{self.variant_phonetic_code}]" if self.variant_phonetic_code else ""
        return f"SurnameXRef [{self.xref_key}] ({self.variant_name_type.value}){phon}"

    def __repr__(self) -> str:
        return (
            f"SurnameXRef(canonical_surname={self.canonical_surname!r}, "
            f"variant_surname={self.variant_surname!r}, "
            f"variant_name_type={self.variant_name_type!r}, "
            f"variant_phonetic_code={self.variant_phonetic_code!r})"
        )
