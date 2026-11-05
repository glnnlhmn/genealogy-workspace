"""Path: src/gda/util/tombstone.py

Domain-agnostic utility functions for managing immutable TombstoneRecord states.

Operational Role:
    Provides pure helper routines to stamp deprecation metadata onto immutable
    domain entities bearing a Tombstone attribute.
"""

from __future__ import annotations

import dataclasses
from typing import Any

from gda.model.atom.date import IsoTimestamp
from gda.model.base.tombstone import Tombstone

__version__ = "1.0.0+build.4"

__all__ = ["is_tombstoned", "stamp_tombstone"]


def is_tombstoned(entity: Any) -> bool:
    """Return True if the entity contains an active tombstone record."""
    tombstone = getattr(entity, "tombstone", None)
    if tombstone is None:
        return False
    return bool(getattr(tombstone, "is_deprecated", False))


def stamp_tombstone[T](
    entity: T,
    reason: str | None = None,
    deprecated_at: IsoTimestamp | None = None,
    superseded_by: Any | None = None,
) -> T:
    """Return a new immutable copy of an entity marked as tombstoned."""
    now = deprecated_at or IsoTimestamp.now_utc()
    tombstone = getattr(entity, "tombstone", None)

    if tombstone is None:
        raise AttributeError(
            f"Entity of type {type(entity).__name__} lacks a 'tombstone' attribute."
        )

    # Transition tombstone state via retire() if supported, or via model/dataclass replacement
    if hasattr(tombstone, "retire"):
        new_tombstone = tombstone.retire(timestamp=now, superseded_by=superseded_by)
    elif hasattr(tombstone, "model_copy"):
        new_tombstone = tombstone.model_copy(
            update={
                "is_deprecated": True,
                "deprecated_at": now,
                "superseded_by": superseded_by,
            }
        )
    elif dataclasses.is_dataclass(tombstone):
        fields = {f.name for f in dataclasses.fields(tombstone)}
        changes: dict[str, Any] = {
            "is_deprecated": True,
            "deprecated_at": now,
            "superseded_by": superseded_by,
        }
        if "reason" in fields and reason is not None:
            changes["reason"] = reason
        new_tombstone = dataclasses.replace(
            tombstone,
            **{k: v for k, v in changes.items() if k in fields},
        )
    else:
        new_tombstone = Tombstone[Any]().retire(timestamp=now, superseded_by=superseded_by)

    if hasattr(entity, "model_copy"):
        return entity.model_copy(update={"tombstone": new_tombstone})
    if dataclasses.is_dataclass(entity):
        return dataclasses.replace(entity, tombstone=new_tombstone)

    raise TypeError(
        f"Entity of type {type(entity).__name__} does not support immutable copy mechanisms."
    )
