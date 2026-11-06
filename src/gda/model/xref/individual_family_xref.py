"""Path: src/gda/model/xref/individual_family_xref.py

Relational kinship cross-reference edge linking individuals and family units.

Operational Role:
    Defines the immutable relational edge ('IndividualFamilyXRef') capturing
    kinship links between individuals and nuclear family units. Enforces
    deterministic primary compound key formatting and Pydantic boundary validation.
"""

from __future__ import annotations

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.errors import ModelFormatError
from gda.enums.core import AssociatedRole
from gda.enums.vital import PedigreeType
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import FamilyID, IndividualID

__version__ = "1.0.0+build.1"

__all__ = ["IndividualFamilyXRef"]


@dataclass(config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True))
class IndividualFamilyXRef:
    """Relational kinship edge linking individuals and family units."""

    xref_id: str = Field(
        ...,
        description="Deterministic compound key: '{subject_id}::{relation_type}::{target_id}'.",
    )
    subject_id: IndividualID = Field(
        ...,
        description="Originating individual identifier.",
    )
    target_id: IndividualID | FamilyID = Field(
        ...,
        description="Target family unit or self-identity identifier.",
    )
    relation_type: str = Field(
        ...,
        description="Semantic relation discriminator: 'PARTNER', 'CHILD', or 'IDENTITY'.",
    )
    role: AssociatedRole | PedigreeType | None = Field(
        default=None,
        description="Contextual kinship role or lineage pedigree classification.",
    )
    display_label: str | None = Field(
        default=None,
        description="Human-readable summary label for presentation display.",
    )
    compiled_at: IsoTimestamp = Field(
        default_factory=IsoTimestamp.now_utc,
        description="Edge generation and indexing timestamp.",
    )

    @classmethod
    def create_key(
        cls,
        subject_id: IndividualID,
        relation_type: str,
        target_id: IndividualID | FamilyID,
        role: AssociatedRole | PedigreeType | str | None = None,
    ) -> str:
        """Generate a deterministic primary compound key for a kinship edge."""
        base_key = f"{subject_id.value}::{relation_type.strip()}::{target_id.value}"
        if role is not None:
            role_token = role.value if hasattr(role, "value") else str(role).strip()
            return f"{base_key}::{role_token}"
        return base_key

    def __post_init__(self) -> None:
        """Enforce identifier boundaries and compound key consistency."""
        if not self.xref_id.strip():
            raise ModelFormatError(
                "IndividualFamilyXRef 'xref_id' cannot be empty or whitespace-only."
            )
        if not self.relation_type.strip():
            raise ModelFormatError(
                "IndividualFamilyXRef 'relation_type' cannot be empty or whitespace-only."
            )
