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

from gda.core.dates import utc_now_iso
from gda.core.errors import ModelFormatError
from gda.core.introspectable import IntrospectableMixin
from gda.core.logging import GDALogger
from gda.model.atom.date import IsoTimestamp

__version__ = "1.1.0+build.1"

__all__ = ["RegistryEnvelope"]

_logger = GDALogger(__name__)


@dataclass(repr=False, config=ConfigDict(frozen=True, extra="forbid", strict=True))
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

    @classmethod
    def create(
        cls,
        schema_version: str,
        records: list[T],
        last_modified: IsoTimestamp | str | None = None,
    ) -> RegistryEnvelope[T]:
        """Factory constructor computing total_count automatically from records."""
        if not isinstance(schema_version, str) or not schema_version.strip():
            raise ModelFormatError("RegistryEnvelope schema_version cannot be empty.")
        if last_modified is None:
            resolved_ts = IsoTimestamp(utc_now_iso())
        elif isinstance(last_modified, IsoTimestamp):
            resolved_ts = last_modified
        elif isinstance(last_modified, str):
            resolved_ts = IsoTimestamp(last_modified)
        else:
            raise ModelFormatError(
                f"Invalid last_modified type: expected IsoTimestamp or str, got {type(last_modified).__name__}."
            )
        return cls(
            schema_version=schema_version.strip(),
            last_modified=resolved_ts,
            total_count=len(records),
            records=list(records),
        )

    def __str__(self) -> str:
        return f"RegistryEnvelope v{self.schema_version} ({self.total_count} records)"

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(version={self.schema_version!r}, "
            f"count={self.total_count}, modified={self.last_modified!r})"
        )
