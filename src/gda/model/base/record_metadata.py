"""Path: src/gda/model/base/record_metadata.py

Administrative source record metadata header using Pydantic dataclasses.

Operational Role:
    Defines the standardized header envelope ('RecordMetadata') required
    by historical records. Combines an immutable UUIDv4 SourceID surrogate
    with domain-resolvable source URN, category, type, and custodial repository link.

Architecture:
    - RecordMetadata: Pydantic dataclass validating record envelope headers.
"""

from __future__ import annotations

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

from gda.core.errors import ModelFormatError
from gda.core.introspectable import IntrospectableMixin
from gda.core.logging import GDALogger
from gda.model.atom.id import RepositoryID, SourceID

__version__ = "1.0.0+build.3"

_logger = GDALogger(__name__)


@dataclass(config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True))
class RecordMetadata(IntrospectableMixin):
    """Archival record header uniting surrogate UUID, semantic URN, and category."""

    source_id: SourceID
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
                err_msg = f"RecordMetadata '{field_name}' cannot be empty."
                _logger.debug(
                    "RecordMetadata validation failed",
                    details={"field": field_name},
                )
                raise ModelFormatError(err_msg, details={"field": field_name})

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(source_id={self.source_id!r}, "
            f"source_urn='{self.source_urn}', record_category='{self.record_category}', "
            f"record_type='{self.record_type}', repository_id={self.repository_id!r})"
        )
