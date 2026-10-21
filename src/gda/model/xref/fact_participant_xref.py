"""Path: src/gda/model/xref/fact_participant_xref.py

Associative relational edge linking individuals to facts in participant roles.

Operational Role:
    Defines the immutable relational edge ('FactParticipantXRef') capturing
    secondary participant associations (witness, informant, officiant, godparent)
    linking individuals to domain fact assertions. Enforces deterministic primary
    compound key formatting and Pydantic boundary validation.
"""

from __future__ import annotations

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.errors import ModelFormatError
from gda.enums.core import AssociatedRole
from gda.model.atom.date import EventDate, IsoTimestamp
from gda.model.atom.id import FactID, IndividualID

__version__ = "1.0.0+build.1"

__all__ = ["FactParticipantXRef"]


@dataclass(config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True))
class FactParticipantXRef:
    """Relational cross-reference edge linking an individual to a fact in an associated role."""

    xref_id: str = Field(
        ...,
        description="Deterministic compound key: '{associated_ind_id}::{role}::{fact_id}'.",
    )
    associated_ind_id: IndividualID = Field(
        ...,
        description="Secondary participant individual identifier (witness, informant, etc.).",
    )
    fact_id: FactID = Field(
        ...,
        description="Authoritative domain event assertion identifier.",
    )
    primary_subject_id: IndividualID = Field(
        ...,
        description="Focal individual persona owning the assertion.",
    )
    role: AssociatedRole = Field(
        ...,
        description="Associated participant role (e.g., WITNESS, INFORMANT, OFFICIANT).",
    )
    title: str | None = Field(
        default=None,
        description="Contextual description, event label, or narrative title.",
    )
    event_date: EventDate | None = Field(
        default=None,
        description="Genealogical event date representation for chronological sorting.",
    )
    compiled_at: IsoTimestamp = Field(
        default_factory=IsoTimestamp.now_utc,
        description="Edge generation and indexing timestamp.",
    )

    @classmethod
    def create_key(
        cls,
        associated_ind_id: IndividualID,
        role: AssociatedRole | str,
        fact_id: FactID,
    ) -> str:
        """Generate a deterministic compound key for a fact participant edge."""
        role_token = role.value if hasattr(role, "value") else str(role).strip()
        return f"{associated_ind_id.value}::{role_token}::{fact_id.value}"

    def __post_init__(self) -> None:
        """Enforce identifier boundaries and compound key consistency."""
        if not self.xref_id.strip():
            raise ModelFormatError(
                "FactParticipantXRef 'xref_id' cannot be empty or whitespace-only."
            )
