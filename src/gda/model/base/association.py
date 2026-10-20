"""Path: src/gda/model/base/association.py

Associated participant representation using Pydantic dataclasses.

Operational Role:
    Defines the participant record ('AssociatedIndividual') for secondary
    individuals mentioned in historical evidentiary records. Enforces resolution
    via either a canonical IndividualID or verbatim name_raw, governed by
    authoritative core role enumerations, secondary site references, and
    lightweight contextual comments.

Architecture:
    - AssociatedRole: Controlled enumeration imported from gda.enums.core.
    - AssociatedIndividual: Pydantic dataclass validating participant associations,
      primary/tertiary role exclusivity, and residence site anchoring.
"""

from __future__ import annotations

from typing import Any

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.errors import ModelFormatError
from gda.core.introspectable import IntrospectableMixin
from gda.core.logging import GDALogger
from gda.enums.core import AssociatedRole
from gda.model.atom.id import IndividualID, SiteID

__version__ = "1.0.0+build.6"

_logger = GDALogger(__name__)


# ==============================================================================
# PARTICIPANT ASSOCIATION RECORD
# ==============================================================================


@dataclass(config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True))
class AssociatedIndividual(IntrospectableMixin):
    """Secondary participant mentioned in an archival source or assertion.

    Attributes:
        role: Primary controlled classification from gda.enums.core.AssociatedRole.
        individual_id: Resolved canonical individual entity ID (preferred if known).
        name_raw: Verbatim transcribed name (mandatory if individual_id is omitted).
        role_verbatim: Original unconstrained title or relationship text.
        tertiary_roles: Supplemental controlled roles held on this record (disjoint from role).
        residence: Canonical SiteID pointing to the entity's recorded residence.
        comment: Lightweight transcription remark or collateral observation.
    """

    role: AssociatedRole = AssociatedRole.OTHER
    individual_id: IndividualID | None = None
    name_raw: str | None = None
    role_verbatim: str | None = None
    tertiary_roles: list[AssociatedRole] = Field(default_factory=list)
    residence: SiteID | None = None
    comment: str | None = None

    def __post_init__(self) -> None:
        """Enforce identity invariant and role disjointness rules."""
        has_id = self.individual_id is not None
        has_name = self.name_raw is not None and bool(self.name_raw.strip())

        if not has_id and not has_name:
            err_msg = (
                "AssociatedIndividual requires either a valid 'individual_id' "
                "or a non-empty 'name_raw'."
            )
            _logger.debug(
                "AssociatedIndividual identity validation failed",
                details={
                    "role": self.role.value,
                    "has_id": has_id,
                    "has_name": has_name,
                },
            )
            raise ModelFormatError(
                err_msg,
                details={"field": "individual_id/name_raw", "role": self.role.value},
            )

        if self.role in self.tertiary_roles:
            err_msg = (
                f"Primary role '{self.role.name}' cannot be duplicated "
                f"in tertiary_roles: {[r.name for r in self.tertiary_roles]}"
            )
            _logger.debug(
                "AssociatedIndividual role overlap detected",
                details={"role": self.role.value},
            )
            raise ModelFormatError(
                err_msg,
                details={"role": self.role.value, "field": "tertiary_roles"},
            )

        if len(self.tertiary_roles) != len(set(self.tertiary_roles)):
            err_msg = "Duplicate roles detected within tertiary_roles list."
            _logger.debug("AssociatedIndividual duplicate tertiary_roles detected")
            raise ModelFormatError(err_msg, details={"field": "tertiary_roles"})

    def __str__(self) -> str:
        label = (
            str(self.individual_id)
            if self.individual_id
            else (self.name_raw or "Unknown")
        )
        roles_summary = [self.role.value] + [r.value for r in self.tertiary_roles]
        return f"{label} ({', '.join(roles_summary)})"

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(role={self.role}, "
            f"individual_id={self.individual_id!r}, name_raw={self.name_raw!r}, "
            f"role_verbatim={self.role_verbatim!r}, tertiary_roles={self.tertiary_roles!r}, "
            f"residence={self.residence!r}, comment={self.comment!r})"
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize associated individual into a primitive dictionary representation."""
        return {
            "role": self.role.value,
            "individual_id": str(self.individual_id) if self.individual_id else None,
            "name_raw": self.name_raw,
            "role_verbatim": self.role_verbatim,
            "tertiary_roles": [r.value for r in self.tertiary_roles],
            "residence": str(self.residence) if self.residence else None,
            "comment": self.comment,
        }


__all__ = ["AssociatedIndividual"]
