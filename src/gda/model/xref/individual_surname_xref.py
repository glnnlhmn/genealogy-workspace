"""Path: src/gda/model/xref/individual_surname_xref.py

Cross-reference bridge and index model linking normalized surnames to individuals.

Operational Role:
    Defines IndividualSurnameXRef (frozen Pydantic dataclass) as a derived
    relational index row linking an uppercase surname token to an IndividualID,
    capturing whether the surname is the birth surname (is_birth_surname),
    optional BirthYear and DeathYear temporal bounds, and lifespan range validation.
"""

from __future__ import annotations

import json
from functools import total_ordering
from typing import Any

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.errors import ModelFormatError, ModelRangeError
from gda.core.introspectable import IntrospectableMixin
from gda.model.atom.id import IndividualID
from gda.model.atom.year import BirthYear, DeathYear
from gda.model.entity.individual import Individual

__version__ = "1.0.0+build.2"

__all__ = [
    "IndividualSurnameXRef",
]


def _normalize_surname(raw: str) -> str:
    """Normalize a surname token to stripped uppercase and reject empty values."""
    clean = str(raw).strip().upper() if raw is not None else ""
    if not clean:
        raise ModelFormatError("IndividualSurnameXRef 'surname' cannot be empty or whitespace.")
    return clean


def _resolve_birth_year(raw: BirthYear | int | None) -> BirthYear | None:
    """Resolve BirthYear instance, strict integer year, or None."""
    if raw is None or isinstance(raw, BirthYear):
        return raw
    return BirthYear(raw)


def _resolve_death_year(raw: DeathYear | int | None) -> DeathYear | None:
    """Resolve DeathYear instance, strict integer year, or None."""
    if raw is None or isinstance(raw, DeathYear):
        return raw
    return DeathYear(raw)


@total_ordering
@dataclass(repr=False, config=ConfigDict(kw_only=True, frozen=True, extra="forbid", strict=True))
class IndividualSurnameXRef(IntrospectableMixin):
    """Immutable derived index row linking an uppercase surname to an IndividualID."""

    surname: str = Field(
        ...,
        description="Normalized uppercase surname token (e.g., 'ABBOTT', 'ROLFE').",
    )
    individual_id: IndividualID = Field(
        ...,
        description="Canonical IndividualID ('IND-######') of the person carrying the surname.",
    )
    is_birth_surname: bool = Field(
        default=True,
        description="True for birth/patronymic surname; False for married or secondary surname.",
    )
    birth_year: BirthYear | None = Field(
        default=None,
        description="Optional validated 4-digit BirthYear (1000..2100) for chronological filtering.",
    )
    death_year: DeathYear | None = Field(
        default=None,
        description="Optional validated 4-digit DeathYear (1000..2100) for chronological filtering.",
    )

    def __post_init__(self) -> None:
        """Enforce uppercase surname normalization and lifespan boundary guards."""
        clean_surname = _normalize_surname(self.surname)
        if clean_surname != self.surname:
            object.__setattr__(self, "surname", clean_surname)

        if (
            self.birth_year is not None
            and self.death_year is not None
            and int(self.death_year) < int(self.birth_year)
        ):
            raise ModelRangeError(
                f"Death year ({int(self.death_year)}) cannot precede birth year ({int(self.birth_year)}).",
                details={
                    "birth_year": int(self.birth_year),
                    "death_year": int(self.death_year),
                },
            )

    @property
    def role_label(self) -> str:
        """Return 'BIRTH' when is_birth_surname is True, else 'OTHER'."""
        return "BIRTH" if self.is_birth_surname else "OTHER"

    @property
    def xref_key(self) -> str:
        """Return dynamic compound index key '<surname>::<individual_id>::<BIRTH|OTHER>'."""
        return f"{self.surname}::{self.individual_id.value}::{self.role_label}"

    @property
    def sort_key(self) -> tuple[str, int, int, int, str]:
        """Return deterministic ordering tuple (surname, birth_year, death_year, role_rank, individual_id)."""
        b_yr = int(self.birth_year) if self.birth_year is not None else 9999
        d_yr = int(self.death_year) if self.death_year is not None else 9999
        role_rank = 0 if self.is_birth_surname else 1
        return (
            self.surname,
            b_yr,
            d_yr,
            role_rank,
            self.individual_id.value,
        )

    @classmethod
    def create(
        cls,
        surname: str,
        individual_id: IndividualID | str,
        is_birth_surname: bool = True,
        birth_year: BirthYear | int | None = None,
        death_year: DeathYear | int | None = None,
    ) -> IndividualSurnameXRef:
        """Factory constructor instantiating a validated IndividualSurnameXRef."""
        clean_surname = _normalize_surname(surname)
        res_ind = (
            individual_id
            if isinstance(individual_id, IndividualID)
            else IndividualID(str(individual_id).strip().upper())
        )
        res_birth = _resolve_birth_year(birth_year)
        res_death = _resolve_death_year(death_year)

        return cls(
            surname=clean_surname,
            individual_id=res_ind,
            is_birth_surname=is_birth_surname,
            birth_year=res_birth,
            death_year=res_death,
        )

    @classmethod
    def from_individual(cls, individual: Individual) -> tuple[IndividualSurnameXRef, ...]:
        """Derive IndividualSurnameXRef rows from an active Individual entity.

        Emits a row with is_birth_surname=True for individual.surname (when present)
        and rows with is_birth_surname=False for each unique married surname.
        """
        if not isinstance(individual, Individual):
            raise ModelFormatError("from_individual requires an Individual entity instance.")

        b_yr = BirthYear(individual.birth_year) if individual.birth_year is not None else None
        d_yr = DeathYear(individual.death_year) if individual.death_year is not None else None

        rows: list[IndividualSurnameXRef] = []

        if individual.surname:
            rows.append(
                cls(
                    surname=_normalize_surname(individual.surname),
                    individual_id=individual.id,
                    is_birth_surname=True,
                    birth_year=b_yr,
                    death_year=d_yr,
                )
            )

        for married_name in individual.married_names:
            rows.append(
                cls(
                    surname=_normalize_surname(married_name),
                    individual_id=individual.id,
                    is_birth_surname=False,
                    birth_year=b_yr,
                    death_year=d_yr,
                )
            )

        return tuple(rows)

    def to_dict(self) -> dict[str, Any]:
        """Serialize IndividualSurnameXRef to a dictionary."""
        data: dict[str, Any] = {
            "surname": self.surname,
            "individual_id": self.individual_id.value,
            "is_birth_surname": self.is_birth_surname,
        }
        if self.birth_year is not None:
            data["birth_year"] = int(self.birth_year)
        if self.death_year is not None:
            data["death_year"] = int(self.death_year)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> IndividualSurnameXRef:
        """Deserialize a dictionary payload into an IndividualSurnameXRef."""
        if not isinstance(data, dict):
            raise ModelFormatError("IndividualSurnameXRef payload must be a dictionary.")

        sname = data.get("surname")
        iid = data.get("individual_id")
        is_birth = data.get("is_birth_surname", True)

        if sname is None or iid is None or type(is_birth) is not bool:
            raise ModelFormatError(
                "IndividualSurnameXRef requires 'surname', 'individual_id', "
                "and boolean 'is_birth_surname'."
            )

        return cls.create(
            surname=str(sname),
            individual_id=str(iid),
            is_birth_surname=is_birth,
            birth_year=data.get("birth_year"),
            death_year=data.get("death_year"),
        )

    def to_json(self) -> str:
        """Serialize IndividualSurnameXRef to a JSON formatted string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_json(cls, payload: str) -> IndividualSurnameXRef:
        """Deserialize a JSON string directly into an IndividualSurnameXRef."""
        try:
            data = json.loads(payload)
        except Exception as exc:
            raise ModelFormatError(
                f"Failed to parse IndividualSurnameXRef JSON string: {exc}"
            ) from exc
        return cls.from_dict(data)

    def __lt__(self, other: Any) -> bool:
        """Support deterministic surname and chronological birth-year sorting."""
        if isinstance(other, IndividualSurnameXRef):
            return self.sort_key < other.sort_key
        return NotImplemented

    def __str__(self) -> str:
        span = ""
        if self.birth_year is not None or self.death_year is not None:
            b_str = str(int(self.birth_year)) if self.birth_year is not None else "?"
            d_str = str(int(self.death_year)) if self.death_year is not None else "?"
            span = f" ({b_str}-{d_str})"
        return f"IndividualSurnameXRef [{self.xref_key}]{span}"

    def __repr__(self) -> str:
        return (
            f"IndividualSurnameXRef(surname={self.surname!r}, "
            f"individual_id={self.individual_id!r}, "
            f"is_birth_surname={self.is_birth_surname!r}, "
            f"birth_year={self.birth_year!r}, death_year={self.death_year!r})"
        )
