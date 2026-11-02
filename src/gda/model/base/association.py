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

import json
from dataclasses import replace
from typing import Any, Self

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.errors import ModelFormatError
from gda.core.introspectable import IntrospectableMixin
from gda.core.logging import GDALogger
from gda.enums.core import AssociatedRole
from gda.model.atom.id import IndividualID, SiteID

__version__ = "1.0.0+build.7"

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

    @classmethod
    def create(
        cls,
        individual_id: IndividualID | str | None = None,
        name_raw: str | None = None,
        role: AssociatedRole | str = AssociatedRole.OTHER,
        role_verbatim: str | None = None,
        tertiary_roles: list[AssociatedRole | str] | None = None,
        residence: SiteID | str | None = None,
        comment: str | None = None,
    ) -> AssociatedIndividual:
        """Factory constructor instantiating a validated AssociatedIndividual."""
        resolved_id = (
            individual_id
            if (individual_id is None or isinstance(individual_id, IndividualID))
            else IndividualID(individual_id)
        )
        resolved_role = (
            role if isinstance(role, AssociatedRole) else AssociatedRole(role)
        )
        resolved_tertiary = [
            r if isinstance(r, AssociatedRole) else AssociatedRole(r)
            for r in (tertiary_roles or [])
        ]
        resolved_residence = (
            residence
            if (residence is None or isinstance(residence, SiteID))
            else SiteID(residence)
        )
        clean_name = name_raw.strip() if name_raw is not None else None
        clean_comment = comment.strip() if comment is not None else None
        clean_verbatim = role_verbatim.strip() if role_verbatim is not None else None

        return cls(
            role=resolved_role,
            individual_id=resolved_id,
            name_raw=clean_name,
            role_verbatim=clean_verbatim,
            tertiary_roles=resolved_tertiary,
            residence=resolved_residence,
            comment=clean_comment,
        )

    def update_role(self, role: AssociatedRole | str) -> Self:
        """Return a new immutable copy with updated primary role."""
        resolved_role = (
            role if isinstance(role, AssociatedRole) else AssociatedRole(role)
        )
        if resolved_role == self.role:
            return self
        return replace(self, role=resolved_role)

    def update_residence(self, residence: SiteID | str | None) -> Self:
        """Return a new immutable copy with updated residence anchor."""
        resolved = (
            residence
            if (residence is None or isinstance(residence, SiteID))
            else SiteID(residence)
        )
        if resolved == self.residence:
            return self
        return replace(self, residence=resolved)

    def update_comment(self, comment: str | None) -> Self:
        """Return a new immutable copy with updated commentary."""
        clean = comment.strip() if comment is not None else None
        if clean == self.comment:
            return self
        return replace(self, comment=clean)

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

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AssociatedIndividual:
        """Deserialize a dictionary payload into an immutable AssociatedIndividual."""
        if not isinstance(data, dict):
            raise ModelFormatError("AssociatedIndividual payload must be a dictionary.")
        return cls.create(
            role=data.get("role", AssociatedRole.OTHER),
            individual_id=data.get("individual_id"),
            name_raw=data.get("name_raw"),
            role_verbatim=data.get("role_verbatim"),
            tertiary_roles=data.get("tertiary_roles"),
            residence=data.get("residence"),
            comment=data.get("comment"),
        )

    def to_json(self) -> str:
        """Serialize AssociatedIndividual to a JSON formatted string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_json(cls, payload: str) -> AssociatedIndividual:
        """Deserialize a JSON string directly into an AssociatedIndividual instance."""
        try:
            data = json.loads(payload)
        except Exception as exc:
            raise ModelFormatError(
                f"Failed to parse AssociatedIndividual JSON: {exc}"
            ) from exc
        return cls.from_dict(data)

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


__all__ = ["AssociatedIndividual"]
