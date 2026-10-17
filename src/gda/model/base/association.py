# Name: association.py
# Path: src/gda/model/base/association.py

"""Associated participant model using Pydantic dataclasses.

Operational Role:
    Defines the participant record ('AssociatedPersonModel') for secondary
    individuals mentioned in historical records (witnesses, physicians,
    clergy, informants, bondsmen) across the Genealogy Digital Archive (GDA).
    Preserves verbatim recorded names while linking optional resolved IndividualIDs.
    Structural kinship edges (parents, spouses, children) are managed via the
    Family entity rather than this evidentiary association record.

Architecture:
    - AssociationRole: Controlled enumeration for secondary event participants.
    - AssociatedPersonModel: Pydantic dataclass validating record associations.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

from gda.core.introspectable import IntrospectableMixin
from gda.core.logging import GDALogger
from gda.model.atom.errors import AtomFormatError
from gda.model.atom.id import IndividualID

__version__ = "1.0.0+build.r3"

_logger = GDALogger(__name__)


class AssociationRole(StrEnum):
    """Controlled classifications for secondary evidentiary record participants."""

    WITNESS = "WITNESS"
    INFORMANT = "INFORMANT"
    OFFICIANT = "OFFICIANT"
    PHYSICIAN = "PHYSICIAN"
    UNDERTAKER = "UNDERTAKER"
    BONDSMAN = "BONDSMAN"
    CLERGY = "CLERGY"
    NEIGHBOR = "NEIGHBOR"
    OTHER = "OTHER"


@dataclass(config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True))
class AssociatedPersonModel(IntrospectableMixin):
    """Secondary participant mentioned in an archival source or assertion."""

    name_raw: str
    role: AssociationRole = AssociationRole.OTHER
    individual_id: IndividualID | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        if not self.name_raw.strip():
            err_msg = "AssociatedPersonModel name_raw cannot be empty."
            _logger.debug("AssociatedPersonModel validation failed")
            raise AtomFormatError(err_msg, details={"field": "name_raw"})

    def __str__(self) -> str:
        return f"{self.name_raw} ({self.role.value})"

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(name_raw='{self.name_raw}', role={self.role}, "
            f"individual_id={self.individual_id!r}, notes={self.notes!r})"
        )
