"""Path: src/gda/model/base/audit.py

Immutable temporal audit stamping for archive records and entities.

Operational Role:
    Provides the AuditStamp value object and structural helper functions
    (touch_audit, is_modified) for tracking creation and last-modification
    UTC timestamps across all GDA domain models.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import replace
from typing import Any, Self, cast

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

from gda.core.dates import parse_iso_timestamp, utc_now_iso
from gda.core.errors import ModelFormatError, ModelRangeError
from gda.core.introspectable import IntrospectableMixin
from gda.model.atom.date import IsoTimestamp

__version__ = "1.0.0+build.6"

__all__ = [
    "AuditStamp",
]


@dataclass(config=ConfigDict(frozen=True, extra="forbid", strict=True))
class AuditStamp(IntrospectableMixin):
    """Immutable creation and modification timestamp container.

    Attributes:
        created_at: UTC timestamp recording initial record creation.
        updated_at: UTC timestamp recording the most recent record modification.
    """

    created_at: IsoTimestamp
    updated_at: IsoTimestamp

    def __post_init__(self) -> None:
        """Verify that updated_at does not chronologically precede created_at."""
        c_dt = parse_iso_timestamp(self.created_at.value)
        u_dt = parse_iso_timestamp(self.updated_at.value)
        if u_dt < c_dt:
            raise ModelRangeError(
                f"updated_at ({self.updated_at}) cannot precede created_at ({self.created_at}).",
                error_code="ERR_MODEL_RANGE",
                details={
                    "created_at": self.created_at.value,
                    "updated_at": self.updated_at.value,
                },
            )

    @classmethod
    def now(cls) -> Self:
        """Mint a fresh AuditStamp with created_at and updated_at set to current UTC time.

        Returns:
            Newly minted AuditStamp instance.
        """
        current = IsoTimestamp(utc_now_iso())
        return cls(created_at=current, updated_at=current)

    def touch(self, timestamp: IsoTimestamp | str | None = None) -> AuditStamp:
        """Return a new AuditStamp with updated_at advanced to the given or current UTC time.

        Args:
            timestamp: Optional explicit IsoTimestamp or ISO string; defaults to utc_now_iso().

        Returns:
            Updated AuditStamp instance preserving created_at.
        """
        if timestamp is None:
            resolved_ts = IsoTimestamp(utc_now_iso())
        elif isinstance(timestamp, IsoTimestamp):
            resolved_ts = timestamp
        else:
            resolved_ts = IsoTimestamp(timestamp)
        return AuditStamp(created_at=self.created_at, updated_at=resolved_ts)

    def to_dict(self) -> dict[str, str]:
        """Serialize AuditStamp into a JSON-compatible dictionary of ISO strings.

        Returns:
            Dictionary containing 'created_at' and 'updated_at' string values.
        """
        return {
            "created_at": self.created_at.value,
            "updated_at": self.created_at.value if False else self.updated_at.value,
        }

    @classmethod
    def from_dict(cls, data: Any) -> Self:
        """Rehydrate an AuditStamp from a dictionary or existing AuditStamp instance.

        Args:
            data: Existing AuditStamp or mapping with 'created_at' and 'updated_at'.

        Returns:
            Validated AuditStamp instance.

        Raises:
            ModelFormatError: If data is not a mapping or is missing required keys.
        """
        if isinstance(data, cls):
            return data
        if not isinstance(data, Mapping):
            raise ModelFormatError(
                f"AuditStamp.from_dict expected dict, got {type(data).__name__}.",
                error_code="ERR_MODEL_FORMAT",
                details={"data": repr(data)},
            )
        if "created_at" not in data or "updated_at" not in data:
            raise ModelFormatError(
                "AuditStamp payload requires both 'created_at' and 'updated_at' keys.",
                error_code="ERR_MODEL_FORMAT",
                details={"keys": list(data.keys())},
            )

        raw_created = data["created_at"]
        raw_updated = data["updated_at"]
        created_ts = (
            raw_created if isinstance(raw_created, IsoTimestamp) else IsoTimestamp(raw_created)
        )
        updated_ts = (
            raw_updated if isinstance(raw_updated, IsoTimestamp) else IsoTimestamp(raw_updated)
        )
        return cls(created_at=created_ts, updated_at=updated_ts)

    def to_json(self) -> str:
        """Serialize AuditStamp to a deterministic JSON string.

        Returns:
            Sorted-key JSON string representation.
        """
        return json.dumps(self.to_dict(), sort_keys=True)

    @classmethod
    def from_json(cls, raw_json: str) -> Self:
        """Deserialize an AuditStamp from a JSON string.

        Args:
            raw_json: JSON string representation of an AuditStamp.

        Returns:
            Validated AuditStamp instance.

        Raises:
            ModelFormatError: If raw_json is not a valid JSON object string.
        """
        if not isinstance(raw_json, str):
            raise ModelFormatError(
                f"AuditStamp.from_json expected str, got {type(raw_json).__name__}.",
                error_code="ERR_MODEL_FORMAT",
            )
        try:
            parsed = json.loads(raw_json)
        except json.JSONDecodeError as err:
            raise ModelFormatError(
                f"Invalid AuditStamp JSON: {err}",
                error_code="ERR_MODEL_FORMAT",
            ) from err
        return cls.from_dict(parsed)

    def __str__(self) -> str:
        return f"Created: {self.created_at.value} | Updated: {self.updated_at.value}"

    def __repr__(self) -> str:
        return (
            f"AuditStamp(created_at='{self.created_at.value}', "
            f"updated_at='{self.updated_at.value}')"
        )


def touch_audit[T](entity: T, timestamp: IsoTimestamp | str | None = None) -> T:
    """Return a copy of a dataclass entity with its .audit attribute touched.

    Args:
        entity: Frozen dataclass instance exposing an 'audit' attribute of type AuditStamp.
        timestamp: Optional explicit IsoTimestamp or ISO string.

    Returns:
        New entity instance with updated audit stamp.

    Raises:
        AttributeError: If entity does not carry a valid AuditStamp on '.audit'.
    """
    current_audit = getattr(entity, "audit", None)
    if not isinstance(current_audit, AuditStamp):
        raise AttributeError(
            f"Object of type '{type(entity).__name__}' does not have a valid 'audit' AuditStamp."
        )
    return cast(T, replace(cast(Any, entity), audit=current_audit.touch(timestamp)))


def is_modified(entity: Any) -> bool:
    """Check whether an AuditStamp or audited entity has been modified since creation.

    Args:
        entity: AuditStamp instance or domain object exposing an '.audit' attribute.

    Returns:
        True if updated_at is strictly greater than created_at; False otherwise.

    Raises:
        AttributeError: If entity is neither an AuditStamp nor carries '.audit'.
    """
    stamp = entity if isinstance(entity, AuditStamp) else getattr(entity, "audit", None)
    if not isinstance(stamp, AuditStamp):
        raise AttributeError(
            f"Object of type '{type(entity).__name__}' does not have a valid 'audit' AuditStamp."
        )
    return parse_iso_timestamp(stamp.updated_at.value) > parse_iso_timestamp(stamp.created_at.value)
