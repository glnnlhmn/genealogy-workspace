"""Path: src/gda/model/base/family.py

Relational value objects representing domestic unions and pedigree linkages.
"""

from __future__ import annotations

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.enums.vital import PedigreeType, UnionDissolutionType, UnionType
from gda.model.atom.id import IndividualID
from gda.model.base.time_period import TimePeriod

__version__ = "1.0.0+build.1"

__all__ = ["ChildLink", "FamilyUnion"]


@dataclass(config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True))
class ChildLink:
    """Associative child relationship link within a domestic or biological family unit."""

    child_id: IndividualID = Field(
        ..., description="Canonical IndividualID of the child."
    )
    pedigree: PedigreeType = Field(
        default=PedigreeType.BIRTH,
        description="Lineage classification: Birth, Adopted, Step, Foster, Unknown.",
    )

    def __str__(self) -> str:
        """Render readable summary of the child linkage."""
        return f"{self.child_id.value} ({self.pedigree.value})"


@dataclass(config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True))
class FamilyUnion:
    """Characterization of union inception, dissolution, and temporal bounds."""

    union_type: UnionType = Field(
        default=UnionType.UNKNOWN,
        description="Classification of union formation (MARRIED, INFORMAL, etc.).",
    )
    dissolution_type: UnionDissolutionType | None = Field(
        default=None,
        description="Classification of termination (DIVORCE, SEPARATION, DEATH, etc.).",
    )
    period: TimePeriod | None = Field(
        default=None,
        description="Chronological bounds of the union (inception to termination).",
    )

    def __str__(self) -> str:
        """Render readable summary of the union state."""
        parts = [f"Type: {self.union_type.value}"]
        if self.dissolution_type:
            parts.append(f"Dissolved: {self.dissolution_type.value}")
        if self.period:
            parts.append(f"Period: {self.period}")
        return ", ".join(parts)
