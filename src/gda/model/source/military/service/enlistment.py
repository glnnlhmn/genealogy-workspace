"""Path: src/gda/model/source/military/service/enlistment.py

Enlistment contracts, muster rolls, and Compiled Military Service Records (CMSR).

Operational Role:
    Extends MilitaryServiceRecord to represent evidentiary enlistment contracts,
    muster-in/muster-out rolls, descriptive rolls, and compiled military service
    record jackets. Validates term lengths, bounties, and muster roll types.
"""

from __future__ import annotations

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.enums.military import MusterRollType
from gda.core.errors import ModelFormatError
from gda.core.types import MAX_ENLISTMENT_TERM_MONTHS, MIN_ENLISTMENT_TERM_MONTHS
from gda.model.atom.id import IndividualID
from gda.model.source.military.service.base import MilitaryServiceRecord

__version__ = "1.0.0+build.2"

__all__ = [
    "EnlistmentMusterRecord",
    "MusterRollType",
]


@dataclass(
    repr=False,
    config=ConfigDict(frozen=True, extra="forbid", strict=True),
    kw_only=True,
)
class EnlistmentMusterRecord(MilitaryServiceRecord):
    """Evidentiary military enlistment or muster roll record."""

    roll_type: MusterRollType = Field(
        ...,
        description="Administrative muster roll or CMSR card jacket type.",
    )
    enlistment_term_months: int | None = Field(
        default=None,
        ge=MIN_ENLISTMENT_TERM_MONTHS,
        le=MAX_ENLISTMENT_TERM_MONTHS,
        description="Term of enlistment or service obligation in months (e.g. 3, 9, 36).",
    )
    muster_officer_raw: str | None = Field(
        default=None,
        description="Verbatim commanding or inspecting officer administering the muster.",
    )
    bounty_paid_usd: float | None = Field(
        default=None,
        ge=0.0,
        description="Federal, state, or municipal cash bounty paid upon enlistment.",
    )
    bounty_due_usd: float | None = Field(
        default=None,
        ge=0.0,
        description="Remaining bounty payment due upon completion of enlistment.",
    )
    credited_town_or_ward_raw: str | None = Field(
        default=None,
        description="Civil jurisdiction credited toward troop quota allocations.",
    )
    substitute_for_id: IndividualID | None = Field(
        default=None,
        description="Canonical IndividualID of the principal if servicemember served as substitute.",
    )
    substitute_for_name_raw: str | None = Field(
        default=None,
        description="Verbatim name of the drafted principal for whom servicemember substituted.",
    )

    def __post_init__(self) -> None:
        """Enforce muster text sanitization and substitute linkage consistency."""
        super().__post_init__()

        if self.substitute_for_id is not None or self.substitute_for_name_raw is not None:
            name_raw = self.substitute_for_name_raw.strip() if self.substitute_for_name_raw else ""
            if not name_raw and self.substitute_for_id is None:
                raise ModelFormatError(
                    "EnlistmentMusterRecord requires non-empty substitute_for_name_raw "
                    "or substitute_for_id when specifying substitute service."
                )
            normalized_name = name_raw or None
            if normalized_name != self.substitute_for_name_raw:
                object.__setattr__(self, "substitute_for_name_raw", normalized_name)
