# Name: auditable.py
# Path: src/gda/model/base/auditable.py

"""Core auditable base model using Pydantic dataclasses.

Operational Role:
    Serves as the root foundation for all timestamp-tracked models across the
    Genealogy Digital Archive (GDA). Ensures consistent encapsulation of an
    AuditStamp instance tracking created_at and updated_at temporal markers.

Architecture:
    - AuditableModel: Pydantic dataclass exposing audit stamp tracking.
"""

from __future__ import annotations

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

from gda.core.introspectable import IntrospectableMixin
from gda.core.logging import GDALogger
from gda.model.atom.date import IsoTimestamp
from gda.model.base.audit import AuditStamp

__version__ = "1.0.0+build.r3"

_logger = GDALogger(__name__)


@dataclass(config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True))
class AuditableModel(IntrospectableMixin):
    """Base model providing immutable audit tracking across entities and artifacts."""

    audit: AuditStamp

    @property
    def created_at(self) -> IsoTimestamp:
        return self.audit.created_at

    @property
    def updated_at(self) -> IsoTimestamp:
        return self.audit.updated_at
