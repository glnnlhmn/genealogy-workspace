"""Path: src/gda/model/base/tombstone.py

In-place entity lifecycle and deprecation tombstone using Pydantic dataclasses.

Operational Role:
    Defines the standardized tombstone envelope ('Tombstone[ID_T]') governing
    soft-deletion, record absorption, deduplication, and supersession, along with
    domain-agnostic helper functions for inspecting and stamping tombstone state.

Architecture:
    - Tombstone[ID_T]: Strict generic Pydantic dataclass managing record deprecation.
    - is_tombstoned: Inspection predicate for entity deprecation state.
    - stamp_tombstone: Functional copy generator applying tombstone retirement metadata.
"""

from __future__ import annotations

import dataclasses
from typing import Any

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

from gda.core.dates import utc_now_iso
from gda.core.errors import ModelFormatError
from gda.core.introspectable import IntrospectableMixin
from gda.core.logging import GDALogger
from gda.model.atom.date import IsoTimestamp

__version__ = "1.1.0+build.1"

__all__ = [
    "Tombstone",
    "is_tombstoned",
    "stamp_tombstone",
]

_logger = GDALogger(__name__)


@dataclass(repr=False, config=ConfigDict(frozen=True, extra="forbid", strict=True))
class Tombstone[ID_T](IntrospectableMixin):
    """Standardized record status metadata governing active vs. deprecated lifecycle."""

    is_deprecated: bool = False
    deprecated_at: IsoTimestamp | None = None
    superseded_by: ID_T | None = None

    def __post_init__(self) -> None:
        if not self.is_deprecated and (
            self.deprecated_at is not None or self.superseded_by is not None
        ):
            err_msg = (
                "Active Tombstone (is_deprecated=False) cannot specify "
                "deprecated_at or superseded_by."
            )
            _logger.debug(
                "Active Tombstone initialized with deprecation metadata",
                details={
                    "deprecated_at": str(self.deprecated_at),
                    "superseded_by": str(self.superseded_by),
                },
            )
            raise ModelFormatError(
                err_msg,
                details={
                    "is_deprecated": False,
                    "deprecated_at": str(self.deprecated_at) if self.deprecated_at else None,
                    "superseded_by": str(self.superseded_by) if self.superseded_by else None,
                },
            )

        if self.is_deprecated and self.deprecated_at is None:
            err_msg = (
                "Deprecated record (is_deprecated=True) must specify a deprecated_at timestamp."
            )
            _logger.debug("Tombstone deprecated timestamp missing")
            raise ModelFormatError(
                err_msg,
                details={
                    "is_deprecated": self.is_deprecated,
                    "deprecated_at": None,
                },
            )

    def retire(
        self,
        timestamp: IsoTimestamp | None = None,
        superseded_by: ID_T | None = None,
    ) -> Tombstone[ID_T]:
        """Return a retired Tombstone stamped with timestamp and superseding pointer."""
        ts = timestamp if timestamp is not None else IsoTimestamp(utc_now_iso())
        return Tombstone[ID_T](
            is_deprecated=True,
            deprecated_at=ts,
            superseded_by=superseded_by,
        )

    def __str__(self) -> str:
        if not self.is_deprecated:
            return "Active"
        suffix = f" -> {self.superseded_by}" if self.superseded_by is not None else ""
        return f"Deprecated ({self.deprecated_at}{suffix})"

    def __repr__(self) -> str:
        if not self.is_deprecated:
            return "Tombstone(is_deprecated=False)"
        target_repr = (
            f", superseded_by={self.superseded_by!r}" if self.superseded_by is not None else ""
        )
        return f"Tombstone(is_deprecated=True, deprecated_at={self.deprecated_at!r}{target_repr})"


def is_tombstoned(entity: Any) -> bool:
    """Return True if the entity contains an active tombstone record."""
    tombstone = getattr(entity, "tombstone", None)
    if tombstone is None:
        return False
    return bool(getattr(tombstone, "is_deprecated", False))


def stamp_tombstone[T](
    entity: T,
    deprecated_at: IsoTimestamp | None = None,
    superseded_by: Any | None = None,
) -> T:
    """Return a new immutable dataclass copy of an entity marked as tombstoned."""
    now = deprecated_at if deprecated_at is not None else IsoTimestamp(utc_now_iso())
    tombstone = getattr(entity, "tombstone", None)

    if tombstone is None:
        raise AttributeError(
            f"Entity of type {type(entity).__name__} lacks a 'tombstone' attribute."
        )

    if not dataclasses.is_dataclass(entity) or isinstance(entity, type):
        raise TypeError(
            f"Entity of type {type(entity).__name__} must be an immutable dataclass instance."
        )

    new_tombstone = Tombstone[Any](
        is_deprecated=True,
        deprecated_at=now,
        superseded_by=superseded_by,
    )
    return dataclasses.replace(entity, tombstone=new_tombstone)
