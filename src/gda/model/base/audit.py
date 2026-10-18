"""Path: src/gda/model/base/audit.py

Core audit metadata tracking stamp using Pydantic dataclasses.

Operational Role:
    Defines the standard record lifecycle stamp ('AuditStamp') tracking created_at
    and updated_at ISO timestamps. Enforces chronological integrity and immutable
    state transitions.

Architecture:
    - AuditStamp: Pydantic dataclass validating record timestamps.
"""

from __future__ import annotations

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

from gda.core.errors import ModelFormatError
from gda.core.introspectable import IntrospectableMixin
from gda.core.logging import GDALogger
from gda.model.atom.date import IsoTimestamp

__version__ = "1.0.0+build.5"

_logger = GDALogger(__name__)


@dataclass(config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True))
class AuditStamp(IntrospectableMixin):
    """Record lifecycle audit metadata capturing creation and update timestamps."""

    created_at: IsoTimestamp
    updated_at: IsoTimestamp

    def __post_init__(self) -> None:
        if self.updated_at.value < self.created_at.value:
            err_msg = (
                f"AuditStamp updated_at ({self.updated_at.value}) cannot precede "
                f"created_at ({self.created_at.value})."
            )
            _logger.debug(
                "AuditStamp chronological violation",
                details={
                    "created_at": self.created_at.value,
                    "updated_at": self.updated_at.value,
                },
            )
            raise ModelFormatError(
                err_msg,
                details={
                    "created_at": self.created_at.value,
                    "updated_at": self.updated_at.value,
                },
            )

    def touch(self, updated_at: IsoTimestamp) -> AuditStamp:
        """Return a new AuditStamp updating only the updated_at timestamp."""
        return AuditStamp(created_at=self.created_at, updated_at=updated_at)

    def __repr__(self) -> str:
        return (
            f"AuditStamp(created_at={self.created_at!r}, "
            f"updated_at={self.updated_at!r})"
        )
