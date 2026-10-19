"""Path: src/gda/model/entity/family.py

Genealogical family entity model representing nuclear and domestic relations.
"""

from __future__ import annotations

import re
from typing import ClassVar

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.errors import ModelFormatError
from gda.model.atom.id import FamilyID, IndividualID
from gda.model.base.entity import BaseEntity
from gda.model.base.family import ChildLink, FamilyUnion

__version__ = "1.0.0+build.1"

__all__ = ["Family"]

_FAMILY_ID_PATTERN: re.Pattern[str] = re.compile(r"^FAM-\d{6,}$")
_FAMILY_URN_PATTERN: re.Pattern[str] = re.compile(r"^urn:gda:fam:[a-z0-9_:\-]+$")


@dataclass(config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True))
class Family(BaseEntity[FamilyID]):
    """Genealogical family nexus binding partners, children, and union state."""

    canonical_urn: str = Field(
        ...,
        description="Deterministic lookup URN (e.g., 'urn:gda:fam:smith_jones_1865').",
    )
    union: FamilyUnion = Field(
        default_factory=FamilyUnion,
        description="Union characterization, dissolution details, and lifespan bounds.",
    )
    partner_ids: list[IndividualID] = Field(
        default_factory=list,
        description="Primary parental or spousal partner identifiers (0, 1, or 2).",
    )
    children: list[ChildLink] = Field(
        default_factory=list,
        description="Ordered list of child links with lineage pedigree classifications.",
    )

    _ID_PATTERN: ClassVar[re.Pattern[str]] = _FAMILY_ID_PATTERN
    _URN_PATTERN: ClassVar[re.Pattern[str]] = _FAMILY_URN_PATTERN

    def __post_init__(self) -> None:
        """Enforce domain invariants, relational uniqueness, and boundary guards."""
        super().__post_init__()

        if not isinstance(self.id, FamilyID):
            raise TypeError(
                f"Family 'id' must be an instance of FamilyID, got {type(self.id).__name__}."
            )

        raw_id = self.id.value
        if not self._ID_PATTERN.match(raw_id):
            raise ModelFormatError(
                f"Invalid FamilyID format: '{raw_id}'. Must match 'FAM-######'."
            )

        if not self._URN_PATTERN.match(self.canonical_urn):
            raise ModelFormatError(
                f"Invalid canonical_urn format: '{self.canonical_urn}'. "
                "Must match 'urn:gda:fam:<slug>'."
            )

        if (
            self.tombstone.is_deprecated
            and self.tombstone.superseded_by is not None
            and self.tombstone.superseded_by.value == raw_id
        ):
            raise ModelFormatError("Family cannot be superseded by itself.")

        if len(self.partner_ids) != len(set(self.partner_ids)):
            raise ModelFormatError("Duplicate entries found in partner_ids.")

        child_ids = [link.child_id for link in self.children]
        if len(child_ids) != len(set(child_ids)):
            raise ModelFormatError(
                "Duplicate child entries found in family children links."
            )

        partner_set = set(self.partner_ids)
        if any(c_id in partner_set for c_id in child_ids):
            raise ModelFormatError(
                "An individual cannot be both a partner and a child within the same family unit."
            )

    @property
    def child_ids(self) -> list[IndividualID]:
        """Convenience accessor returning ordered flat list of child IndividualIDs."""
        return [link.child_id for link in self.children]

    @property
    def partner_count(self) -> int:
        """Total number of registered partners in the family unit."""
        return len(self.partner_ids)

    @property
    def child_count(self) -> int:
        """Total number of registered children in the family unit."""
        return len(self.children)

    def __str__(self) -> str:
        """Render concise human-readable family summary."""
        partner_str = (
            " & ".join(p.value for p in self.partner_ids)
            if self.partner_ids
            else "None"
        )
        union_summary = f"[{self.union.union_type.value}"
        if self.union.dissolution_type:
            union_summary += f"/{self.union.dissolution_type.value}"
        union_summary += "]"

        period_str = f" ({self.union.period})" if self.union.period else ""
        return (
            f"Family {union_summary}{period_str}: "
            f"Partners({partner_str}), Children({self.child_count}) ({self.id.value})"
        )
