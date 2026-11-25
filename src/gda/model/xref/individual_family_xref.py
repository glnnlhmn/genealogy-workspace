"""Path: src/gda/model/xref/individual_family_xref.py

Cross-reference bridge and index model linking individuals to nuclear family units.

Operational Role:
    Defines IndividualFamilyXRef (frozen Pydantic dataclass) as a derived relational
    index row linking an IndividualID to a FamilyID as either a partner/parent
    (is_partner=True) or a child (is_partner=False), capturing PedigreeType and
    1-based child_order for children.
"""

from __future__ import annotations

import json
from functools import total_ordering
from typing import Any

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.enums import coerce_enum
from gda.core.enums.vital import PedigreeType
from gda.core.errors import ModelFormatError
from gda.core.introspectable import IntrospectableMixin
from gda.model.atom.id import FamilyID, IndividualID

__version__ = "1.0.0+build.5"

__all__ = [
    "IndividualFamilyXRef",
]

_PEDIGREE_ALIASES: dict[str, PedigreeType] = {
    "BIOLOGICAL": PedigreeType.BIRTH,
}


def _parse_pedigree(raw: PedigreeType | str) -> PedigreeType:
    """Resolve PedigreeType by enum instance, alias, exact value, or uppercase member name."""
    candidate = _PEDIGREE_ALIASES.get(raw.strip().upper(), raw) if isinstance(raw, str) else raw
    try:
        return coerce_enum(PedigreeType, candidate, field_name="pedigree")
    except ModelFormatError as err:
        raise ModelFormatError(f"Invalid PedigreeType value: '{raw}'.") from err


@total_ordering
@dataclass(
    repr=False,
    config=ConfigDict(frozen=True, extra="forbid", strict=True),
    kw_only=True,
)
class IndividualFamilyXRef(IntrospectableMixin):
    """Immutable derived index row linking an IndividualID to a FamilyID."""

    family_id: FamilyID = Field(
        ...,
        description="Canonical FamilyID ('FAM-######') of the nuclear family unit.",
    )
    individual_id: IndividualID = Field(
        ...,
        description="Canonical IndividualID ('IND-######') of the family member.",
    )
    is_partner: bool = Field(
        ...,
        description="True when the individual is a partner/parent; False when a child.",
    )
    pedigree: PedigreeType | None = Field(
        default=None,
        description="Filial pedigree classification (BIRTH, ADOPTED, STEP, FOSTER, UNKNOWN) for children; None for partners.",
    )
    child_order: int | None = Field(
        default=None,
        ge=1,
        description="Optional 1-based birth/register order within the family unit for children; None for partners.",
    )

    def __post_init__(self) -> None:
        """Enforce mutual exclusivity of partner status vs. child pedigree and child_order."""
        if self.is_partner:
            if self.pedigree is not None:
                raise ModelFormatError(
                    "IndividualFamilyXRef cannot define 'pedigree' when is_partner is True."
                )
            if self.child_order is not None:
                raise ModelFormatError(
                    "IndividualFamilyXRef cannot define 'child_order' when is_partner is True."
                )
        elif self.pedigree is None:
            object.__setattr__(self, "pedigree", PedigreeType.BIRTH)

    @property
    def role_label(self) -> str:
        """Return 'PARTNER' for partners or 'CHILD' for children."""
        return "PARTNER" if self.is_partner else "CHILD"

    @property
    def xref_key(self) -> str:
        """Return dynamic compound index key '<family_id>::<individual_id>::<PARTNER|CHILD>'."""
        return f"{self.family_id.value}::{self.individual_id.value}::{self.role_label}"

    @property
    def sort_key(self) -> tuple[str, int, int, str]:
        """Return deterministic ordering tuple (family_id, partner_first_rank, child_order, individual_id)."""
        role_rank = 0 if self.is_partner else 1
        order_rank = self.child_order if self.child_order is not None else 9999
        return (
            self.family_id.value,
            role_rank,
            order_rank,
            self.individual_id.value,
        )

    @classmethod
    def create(
        cls,
        family_id: FamilyID | str,
        individual_id: IndividualID | str,
        is_partner: bool,
        pedigree: PedigreeType | str | None = None,
        child_order: int | None = None,
    ) -> IndividualFamilyXRef:
        """Factory constructor instantiating a validated IndividualFamilyXRef."""
        res_fam = (
            family_id
            if isinstance(family_id, FamilyID)
            else FamilyID(str(family_id).strip().upper())
        )
        res_ind = (
            individual_id
            if isinstance(individual_id, IndividualID)
            else IndividualID(str(individual_id).strip().upper())
        )
        if pedigree is not None:
            res_ped: PedigreeType | None = _parse_pedigree(pedigree)
        elif not is_partner:
            res_ped = PedigreeType.BIRTH
        else:
            res_ped = None

        return cls(
            family_id=res_fam,
            individual_id=res_ind,
            is_partner=is_partner,
            pedigree=res_ped,
            child_order=child_order,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize IndividualFamilyXRef to a dictionary."""
        data: dict[str, Any] = {
            "family_id": self.family_id.value,
            "individual_id": self.individual_id.value,
            "is_partner": self.is_partner,
        }
        if self.pedigree is not None:
            data["pedigree"] = self.pedigree.value
        if self.child_order is not None:
            data["child_order"] = self.child_order
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> IndividualFamilyXRef:
        """Deserialize a dictionary payload into an IndividualFamilyXRef."""
        if not isinstance(data, dict):
            raise ModelFormatError("IndividualFamilyXRef payload must be a dictionary.")

        fid = data.get("family_id")
        iid = data.get("individual_id")
        is_part = data.get("is_partner")

        if fid is None or iid is None or type(is_part) is not bool:
            raise ModelFormatError(
                "IndividualFamilyXRef requires 'family_id', 'individual_id', and boolean 'is_partner'."
            )

        raw_order = data.get("child_order")
        return cls.create(
            family_id=str(fid),
            individual_id=str(iid),
            is_partner=is_part,
            pedigree=data.get("pedigree"),
            child_order=int(raw_order) if raw_order is not None else None,
        )

    def to_json(self) -> str:
        """Serialize IndividualFamilyXRef to a JSON formatted string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_json(cls, payload: str) -> IndividualFamilyXRef:
        """Deserialize a JSON string directly into an IndividualFamilyXRef."""
        try:
            data = json.loads(payload)
        except Exception as exc:
            raise ModelFormatError(
                f"Failed to parse IndividualFamilyXRef JSON string: {exc}"
            ) from exc
        return cls.from_dict(data)

    def __lt__(self, other: Any) -> bool:
        """Support deterministic family and birth-order sorting."""
        if isinstance(other, IndividualFamilyXRef):
            return self.sort_key < other.sort_key
        return NotImplemented

    def __str__(self) -> str:
        suffix = f" ({self.pedigree.name})" if self.pedigree is not None else ""
        return f"IndividualFamilyXRef [{self.xref_key}]{suffix}"

    def __repr__(self) -> str:
        return (
            f"IndividualFamilyXRef(family_id={self.family_id!r}, "
            f"individual_id={self.individual_id!r}, is_partner={self.is_partner!r}, "
            f"pedigree={self.pedigree!r}, child_order={self.child_order!r})"
        )
