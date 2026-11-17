"""Path: src/gda/model/base/tombstone.py

Generic soft-deletion and record-supersession tombstone lifecycle primitives.

Operational Role:
    Defines the generic Tombstone[ID_T] container and structural helpers
    (stamp_tombstone, is_tombstoned) governing soft-deprecation and record
    merge/supersession pointers across entities and documentary sources.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from dataclasses import replace
from typing import Any, Self, cast

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

from gda.core.dates import utc_now_iso
from gda.core.errors import ModelFormatError
from gda.core.introspectable import IntrospectableMixin
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import AtomID, UUIDv4Str

__version__ = "1.0.0+build.7"

__all__ = [
    "Tombstone",
    "is_tombstoned",
    "stamp_tombstone",
]


@dataclass(repr=False, config=ConfigDict(frozen=True, extra="forbid", strict=True))
class Tombstone[ID_T: AtomID | UUIDv4Str | str](IntrospectableMixin):
    """Immutable deprecation and supersession state container.

    Attributes:
        is_deprecated: True if the record has been retired/deprecated.
        deprecated_at: Optional UTC timestamp when deprecation occurred.
        superseded_by: Optional strongly-typed identifier of the replacement record.
    """

    is_deprecated: bool = False
    deprecated_at: IsoTimestamp | None = None
    superseded_by: ID_T | None = None

    def __post_init__(self) -> None:
        """Enforce consistency between is_deprecated flag and deprecation metadata."""
        if not self.is_deprecated and (
            self.deprecated_at is not None or self.superseded_by is not None
        ):
            raise ModelFormatError(
                "Active Tombstone (is_deprecated=False) cannot specify deprecated_at or superseded_by.",
                error_code="ERR_MODEL_FORMAT",
                details={
                    "is_deprecated": self.is_deprecated,
                    "deprecated_at": str(self.deprecated_at),
                    "superseded_by": str(self.superseded_by),
                },
            )

    def retire(
        self,
        superseded_by: ID_T | None = None,
        timestamp: IsoTimestamp | str | None = None,
    ) -> Tombstone[ID_T]:
        """Transition an active Tombstone to the deprecated state.

        Args:
            superseded_by: Optional identifier of the superseding record.
            timestamp: Optional explicit IsoTimestamp or ISO string; defaults to utc_now_iso().

        Returns:
            New deprecated Tombstone instance.

        Raises:
            ModelFormatError: If the Tombstone is already deprecated.
        """
        if self.is_deprecated:
            raise ModelFormatError(
                "Record is already deprecated and cannot be retired again.",
                error_code="ERR_MODEL_FORMAT",
                details={"deprecated_at": str(self.deprecated_at)},
            )

        if timestamp is None:
            resolved_ts = IsoTimestamp(utc_now_iso())
        elif isinstance(timestamp, IsoTimestamp):
            resolved_ts = timestamp
        else:
            resolved_ts = IsoTimestamp(timestamp)

        return Tombstone(
            is_deprecated=True,
            deprecated_at=resolved_ts,
            superseded_by=superseded_by,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize Tombstone into a JSON-compatible dictionary.

        Returns:
            Dictionary with 'is_deprecated', 'deprecated_at', and 'superseded_by'.
        """
        return {
            "is_deprecated": self.is_deprecated,
            "deprecated_at": self.deprecated_at.value if self.deprecated_at is not None else None,
            "superseded_by": str(self.superseded_by) if self.superseded_by is not None else None,
        }

    @classmethod
    def from_dict(
        cls,
        data: Any,
        *,
        id_cls: Callable[[Any], ID_T] | None = None,
    ) -> Self:
        """Rehydrate a Tombstone from a dictionary or existing Tombstone instance.

        Args:
            data: Existing Tombstone or mapping containing tombstone fields.
            id_cls: Optional callable/class used to wrap a raw 'superseded_by' string.

        Returns:
            Validated Tombstone instance.

        Raises:
            ModelFormatError: If data is not a mapping or contains invalid field types.
        """
        if isinstance(data, cls):
            return data
        if not isinstance(data, Mapping):
            raise ModelFormatError(
                f"Tombstone.from_dict expected dict, got {type(data).__name__}.",
                error_code="ERR_MODEL_FORMAT",
                details={"data": repr(data)},
            )

        raw_flag = data.get("is_deprecated", False)
        if not isinstance(raw_flag, bool):
            raise ModelFormatError(
                f"Tombstone 'is_deprecated' must be a boolean, got {type(raw_flag).__name__}.",
                error_code="ERR_MODEL_FORMAT",
                details={"is_deprecated": repr(raw_flag)},
            )

        raw_dt = data.get("deprecated_at")
        resolved_dt: IsoTimestamp | None
        if raw_dt is None or isinstance(raw_dt, IsoTimestamp):
            resolved_dt = raw_dt
        elif isinstance(raw_dt, str):
            resolved_dt = IsoTimestamp(raw_dt)
        else:
            raise ModelFormatError(
                f"Invalid Tombstone 'deprecated_at': {raw_dt!r}",
                error_code="ERR_MODEL_FORMAT",
            )

        raw_sup = data.get("superseded_by")
        resolved_sup: Any
        if raw_sup is None or isinstance(raw_sup, (AtomID, UUIDv4Str)):
            resolved_sup = raw_sup
        elif id_cls is not None:
            resolved_sup = id_cls(raw_sup)
        else:
            raise ModelFormatError(
                "Tombstone 'superseded_by' requires an id_cls wrapper when provided as a raw value.",
                error_code="ERR_MODEL_FORMAT",
                details={"superseded_by": repr(raw_sup)},
            )

        return cls(
            is_deprecated=raw_flag,
            deprecated_at=resolved_dt,
            superseded_by=resolved_sup,
        )

    def to_json(self) -> str:
        """Serialize Tombstone to a deterministic JSON string.

        Returns:
            Sorted-key JSON string representation.
        """
        return json.dumps(self.to_dict(), sort_keys=True)

    @classmethod
    def from_json(
        cls,
        raw_json: str,
        *,
        id_cls: Callable[[Any], ID_T] | None = None,
    ) -> Self:
        """Deserialize a Tombstone from a JSON string.

        Args:
            raw_json: JSON string representation of a Tombstone.
            id_cls: Optional callable/class used to wrap a raw 'superseded_by' string.

        Returns:
            Validated Tombstone instance.

        Raises:
            ModelFormatError: If raw_json is not a valid JSON object string.
        """
        if not isinstance(raw_json, str):
            raise ModelFormatError(
                f"Tombstone.from_json expected str, got {type(raw_json).__name__}.",
                error_code="ERR_MODEL_FORMAT",
            )
        try:
            parsed = json.loads(raw_json)
        except json.JSONDecodeError as err:
            raise ModelFormatError(
                f"Invalid Tombstone JSON: {err}",
                error_code="ERR_MODEL_FORMAT",
            ) from err
        return cls.from_dict(parsed, id_cls=id_cls)

    def __str__(self) -> str:
        if not self.is_deprecated:
            return "Active"
        base = f"Deprecated at {self.deprecated_at.value if self.deprecated_at else 'Unknown'}"
        if self.superseded_by is not None:
            return f"{base} (Superseded by {self.superseded_by})"
        return base

    def __repr__(self) -> str:
        if not self.is_deprecated:
            return "Tombstone(is_deprecated=False)"
        dt_str = f"'{self.deprecated_at.value}'" if self.deprecated_at else "None"
        sup_str = f"'{self.superseded_by}'" if self.superseded_by is not None else "None"
        return f"Tombstone(is_deprecated=True, deprecated_at={dt_str}, superseded_by={sup_str})"


def stamp_tombstone[T](
    entity: T,
    superseded_by: Any = None,
    timestamp: IsoTimestamp | str | None = None,
) -> T:
    """Return a copy of a dataclass entity with its .tombstone retired.

    Args:
        entity: Frozen dataclass instance exposing a 'tombstone' attribute.
        superseded_by: Optional replacement entity/source identifier.
        timestamp: Optional explicit IsoTimestamp or ISO string.

    Returns:
        New entity instance with retired Tombstone.

    Raises:
        AttributeError: If entity does not carry a valid Tombstone on '.tombstone'.
    """
    current_tomb = getattr(entity, "tombstone", None)
    if not isinstance(current_tomb, Tombstone):
        raise AttributeError(
            f"Object of type '{type(entity).__name__}' does not have a valid 'tombstone' Tombstone."
        )
    return cast(
        T,
        replace(
            cast(Any, entity),
            tombstone=current_tomb.retire(superseded_by=superseded_by, timestamp=timestamp),
        ),
    )


def is_tombstoned(entity: Any) -> bool:
    """Check whether a Tombstone or domain entity is marked as deprecated.

    Args:
        entity: Tombstone instance or domain object exposing a '.tombstone' attribute.

    Returns:
        True if is_deprecated is True; False otherwise.

    Raises:
        AttributeError: If entity is neither a Tombstone nor carries '.tombstone'.
    """
    tomb = entity if isinstance(entity, Tombstone) else getattr(entity, "tombstone", None)
    if not isinstance(tomb, Tombstone):
        raise AttributeError(
            f"Object of type '{type(entity).__name__}' does not have a valid 'tombstone' Tombstone."
        )
    return tomb.is_deprecated
