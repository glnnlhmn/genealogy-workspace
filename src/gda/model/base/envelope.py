"""Path: src/gda/model/base/envelope.py

Administrative collection envelope using Pydantic dataclasses.

Operational Role:
    Defines the top-level container envelope ('RegistryEnvelope[T]') for master
    entity datasets. Enforces schema version tracking, audit modification
    timestamps, and strict item-count integrity.

Architecture:
    - RegistryEnvelope[T]: Generic Pydantic dataclass validating dataset envelopes.
"""

from __future__ import annotations

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

from gda.core.errors import ModelFormatError
from gda.core.introspectable import IntrospectableMixin
from gda.core.logging import GDALogger
from gda.model.atom.date import IsoTimestamp

__version__ = "1.0.0+build.3"

_logger = GDALogger(__name__)


@dataclass(config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True))
class RegistryEnvelope[T](IntrospectableMixin):
    """Top-level serialization envelope for master registries and indices."""

    schema_version: str
    last_modified: IsoTimestamp
    total_count: int
    records: list[T]

    def __post_init__(self) -> None:
        if not self.schema_version.strip():
            err_msg = "RegistryEnvelope schema_version cannot be empty."
            _logger.debug("RegistryEnvelope validation failed: empty schema_version")
            raise ModelFormatError(err_msg, details={"field": "schema_version"})

        if self.total_count != len(self.records):
            err_msg = (
                f"RegistryEnvelope total_count mismatch: declared {self.total_count}, "
                f"actual record count is {len(self.records)}."
            )
            _logger.debug(
                "RegistryEnvelope total_count mismatch",
                details={"declared": self.total_count, "actual": len(self.records)},
            )
            raise ModelFormatError(
                err_msg,
                details={"declared": self.total_count, "actual": len(self.records)},
            )

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(version='{self.schema_version}', "
            f"count={self.total_count}, modified={self.last_modified!r})"
        )
