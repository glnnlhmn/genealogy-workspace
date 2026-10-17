# Name: tombstone.py
# Path: src/gda/model/base/tombstone.py

"""In-place entity lifecycle and deprecation tombstone model using Pydantic dataclasses.

Operational Role:
    Defines the standardized tombstone envelope ('TombstoneRecord[ID_T]') governing
    soft-deletion, record absorption, deduplication, and supersession across the
    Genealogy Digital Archive (GDA).

Architecture:
    - TombstoneRecord[ID_T]: Generic Pydantic dataclass managing record deprecation.
"""

from __future__ import annotations

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

from gda.core.introspectable import IntrospectableMixin
from gda.core.logging import GDALogger
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.errors import AtomFormatError

__version__ = "1.0.0+build.r4"

_logger = GDALogger(__name__)


@dataclass(config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True))
class TombstoneRecord[ID_T](IntrospectableMixin):
    """Standardized record status metadata governing active vs. deprecated lifecycle."""

    is_deprecated: bool = False
    deprecated_at: IsoTimestamp | None = None
    superseded_by: ID_T | None = None

    def __post_init__(self) -> None:
        if not self.is_deprecated and (
            self.deprecated_at is not None or self.superseded_by is not None
        ):
            err_msg = (
                "Active record (is_deprecated=False) must not possess a "
                "deprecated_at timestamp or superseded_by reference."
            )
            _logger.debug("TombstoneRecord active invariant violated")
            raise AtomFormatError(
                err_msg,
                details={
                    "is_deprecated": self.is_deprecated,
                    "deprecated_at": repr(self.deprecated_at),
                    "superseded_by": repr(self.superseded_by),
                },
            )

        if self.is_deprecated and self.deprecated_at is None:
            err_msg = "Deprecated record (is_deprecated=True) must specify a deprecated_at timestamp."
            _logger.debug("TombstoneRecord deprecated timestamp missing")
            raise AtomFormatError(
                err_msg,
                details={
                    "is_deprecated": self.is_deprecated,
                    "deprecated_at": None,
                },
            )

    def retire(
        self, timestamp: IsoTimestamp, superseded_by: ID_T | None = None
    ) -> TombstoneRecord[ID_T]:
        return TombstoneRecord[ID_T](
            is_deprecated=True,
            deprecated_at=timestamp,
            superseded_by=superseded_by,
        )

    def __repr__(self) -> str:
        if not self.is_deprecated:
            return "TombstoneRecord(is_deprecated=False)"
        target_repr = (
            f", superseded_by={self.superseded_by!r}" if self.superseded_by else ""
        )
        return (
            f"TombstoneRecord(is_deprecated=True, "
            f"deprecated_at={self.deprecated_at!r}{target_repr})"
        )
