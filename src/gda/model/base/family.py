# Name: family.py
# Path: src/gda/model/base/family.py

"""Core family unit structural model using Pydantic dataclasses.

Operational Role:
    Defines the structural family group representation ('BaseFamilyModel') and child
    pedigree linkage ('FamilyChildModel') across the Genealogy Digital Archive (GDA).
    Enforces relational edges between partners (spouses/parents) and children,
    qualifies union classifications and pedigree ties (birth, adoption, foster),
    and inherits standard AtomID entity lifecycle controls.

Architecture:
    - UnionType: Controlled enumeration for conjugal and domestic unions.
    - PedigreeLinkType: Controlled enumeration for child lineage/filiation types.
    - FamilyChildModel: Pydantic dataclass validating a child edge within a family unit.
    - BaseFamilyModel: Pydantic dataclass defining a family entity inheriting EntityModel[FamilyID].
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.introspectable import IntrospectableMixin
from gda.core.logging import GDALogger
from gda.model.atom.date import EventDate, EventDateRange
from gda.model.atom.id import FamilyID, IndividualID
from gda.model.base.entity import EntityModel

__version__ = "1.0.0+build.r2"

_logger = GDALogger(__name__)


class UnionType(StrEnum):
    """Controlled classifications for partner unions and domestic partnerships."""

    MARRIED = "MARRIED"
    COMMON_LAW = "COMMON_LAW"
    CIVIL_UNION = "CIVIL_UNION"
    SEPARATED = "SEPARATED"
    DIVORCED = "DIVORCED"
    ANNULLED = "ANNULLED"
    UNKNOWN = "UNKNOWN"


class PedigreeLinkType(StrEnum):
    """Controlled classifications for child lineage and parental filiation."""

    BIRTH = "BIRTH"
    ADOPTED = "ADOPTED"
    FOSTER = "FOSTER"
    STEP = "STEP"
    GUARDIAN = "GUARDIAN"
    UNKNOWN = "UNKNOWN"


@dataclass(config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True))
class FamilyChildModel(IntrospectableMixin):
    """Child linkage edge within a family unit qualifying lineage type."""

    individual_id: IndividualID
    pedigree_type: PedigreeLinkType = PedigreeLinkType.BIRTH
    notes: str | None = None

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(individual_id={self.individual_id!r}, "
            f"pedigree_type={self.pedigree_type}, notes={self.notes!r})"
        )


@dataclass(config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True))
class BaseFamilyModel(EntityModel[FamilyID]):
    """First-class structural family unit linking partners and children."""

    partners: list[IndividualID] = Field(default_factory=list)
    children: list[FamilyChildModel] = Field(default_factory=list)
    union_type: UnionType = UnionType.UNKNOWN
    union_date: EventDate | EventDateRange | None = None

    @property
    def partner_count(self) -> int:
        return len(self.partners)

    @property
    def child_count(self) -> int:
        return len(self.children)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(id={self.id!r}, partners={self.partners!r}, "
            f"children={self.children!r}, union_type={self.union_type}, "
            f"union_date={self.union_date!r}, audit={self.audit!r}, "
            f"tombstone={self.tombstone!r}, notes={self.notes!r})"
        )
