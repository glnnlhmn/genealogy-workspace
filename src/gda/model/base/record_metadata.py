# Name: record_metadata.py
# Path: src/gda/model/base/record_metadata.py

"""Administrative source record metadata model using Pydantic dataclasses.

Operational Role:
    Defines the standardized header envelope ('RecordMetadataModel') required
    by every historical record in the Genealogy Digital Archive (GDA). Combines
    an immutable UUIDv4 SourceId surrogate with the domain-resolvable source_urn,
    controlled category, record type, and custodial repository link.

Architecture:
    - RecordMetadataModel: Pydantic dataclass validating record envelope headers.
"""

from __future__ import annotations

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

from gda.core.introspectable import IntrospectableMixin
from gda.core.logging import GDALogger
from gda.model.atom.errors import AtomFormatError
from gda.model.atom.id import RepositoryID, SourceId

__version__ = "1.0.0+build.r2"

_logger = GDALogger(__name__)


@dataclass(config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True))
class RecordMetadataModel(IntrospectableMixin):
    """Archival record header uniting surrogate UUID, semantic URN, and category."""

    source_id: SourceId
    source_urn: str
    record_category: str
    record_type: str
    repository_id: RepositoryID | None = None

    def __post_init__(self) -> None:
        for field_name, value in (
            ("source_urn", self.source_urn),
            ("record_category", self.record_category),
            ("record_type", self.record_type),
        ):
            if not value.strip():
                err_msg = f"RecordMetadataModel '{field_name}' cannot be empty."
                _logger.debug(
                    "RecordMetadataModel validation failed",
                    details={"field": field_name},
                )
                raise AtomFormatError(err_msg, details={"field": field_name})

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(source_id={self.source_id!r}, "
            f"source_urn='{self.source_urn}', record_category='{self.record_category}', "
            f"record_type='{self.record_type}', repository_id={self.repository_id!r})"
        )
