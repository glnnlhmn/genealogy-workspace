"""Path: src/gda/db/mapper/base.py

Base contract and shared serialization helpers for GDA SQLite row mappers.

Operational Role:
    Defines the generic BaseRowMapper[T] abstract class and shared helper
    functions for flattening and hydrating NameThing, Note lists, Tombstone
    records, SmartIDs, and calendar years across entity row mappers.
"""

from __future__ import annotations

import json
import re
import sqlite3
from abc import ABC, abstractmethod
from typing import Any

from gda.core.introspectable import IntrospectableMixin
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import AtomID
from gda.model.base.name import HistoricVariant, NameThing
from gda.model.base.note import Note
from gda.model.base.tombstone import Tombstone

__version__ = "1.0.0+build.1"

__all__ = [
    "BaseRowMapper",
    "_deserialize_name_thing",
    "_deserialize_notes",
    "_deserialize_tombstone",
    "_extract_id_str",
    "_extract_year_from_text",
    "_serialize_name_thing",
]

_YEAR_PATTERN: re.Pattern[str] = re.compile(r"\b(\d{4})\b")


def _extract_id_str(val: Any) -> str | None:
    """Extract plain ID string from raw string, dict dump, or AtomID."""
    if val is None:
        return None
    if isinstance(val, str):
        return val
    if isinstance(val, dict):
        return str(val.get("value", ""))
    if isinstance(val, AtomID):
        return str(val.value)
    return str(val)


def _extract_year_from_text(date_text: str | None) -> int | None:
    """Extract 4-digit calendar year from date text if present."""
    if not date_text:
        return None
    match = _YEAR_PATTERN.search(date_text)
    return int(match.group(1)) if match else None


def _serialize_name_thing(name: NameThing) -> dict[str, Any]:
    """Flatten a NameThing into analytical SQLite column values."""
    return {
        "raw_name": name.raw,
        "canonical_name": name.canonical,
        "aliases_json": json.dumps(list(name.aliases), ensure_ascii=False),
        "alt_spellings_json": json.dumps(list(name.alt_spellings), ensure_ascii=False),
        "historical_names_json": json.dumps(
            [h.to_dict() for h in name.historic], ensure_ascii=False
        ),
        "name_comment": name.comment,
    }


def _deserialize_name_thing(data: dict[str, Any]) -> NameThing:
    """Reconstruct a NameThing from flattened SQLite columns."""
    aliases = json.loads(data["aliases_json"]) if data.get("aliases_json") else []
    alt_spellings = json.loads(data["alt_spellings_json"]) if data.get("alt_spellings_json") else []
    historic_raw = (
        json.loads(data["historical_names_json"]) if data.get("historical_names_json") else []
    )
    historic_objs = [HistoricVariant.from_dict(h) for h in historic_raw if isinstance(h, dict)]
    return NameThing(
        raw=data["raw_name"],
        canonical=data["canonical_name"],
        aliases=aliases,
        alt_spellings=alt_spellings,
        historic=historic_objs,
        comment=data.get("name_comment"),
    )


def _deserialize_notes(raw_json: str | None) -> list[Note]:
    """Reconstruct a list of Note objects from a JSON string column."""
    if not raw_json:
        return []
    return [Note.from_dict(n) for n in json.loads(raw_json) if isinstance(n, dict)]


def _deserialize_tombstone[IDType: AtomID](
    data: dict[str, Any],
    id_cls: type[IDType],
) -> Tombstone[IDType]:
    """Reconstruct a typed Tombstone from flattened SQLite columns."""
    is_dep = bool(data.get("is_deprecated", 0))
    if not is_dep:
        return Tombstone[id_cls]()  # type: ignore[valid-type]

    dep_raw = data.get("deprecated_at") or data.get("updated_at")
    dep_ts = IsoTimestamp(str(dep_raw)) if dep_raw else None
    sup_str = _extract_id_str(data.get("superseded_by"))
    sup_id = id_cls(sup_str) if sup_str else None
    return Tombstone[id_cls](  # type: ignore[valid-type]
        is_deprecated=True,
        deprecated_at=dep_ts,
        superseded_by=sup_id,
    )


class BaseRowMapper[T](IntrospectableMixin, ABC):
    """Abstract base contract for bidirectional SQLite row mapping."""

    def __init__(self, model_cls: type[T]) -> None:
        """Initialize row mapper with bound model class."""
        self._model_cls = model_cls

    @property
    def model_cls(self) -> type[T]:
        """Return the bound domain entity class."""
        return self._model_cls

    @abstractmethod
    def to_row(self, entity: T) -> dict[str, Any]:
        """Convert a pure domain entity into flat SQLite row parameters."""

    @abstractmethod
    def from_row(self, row: sqlite3.Row | dict[str, Any]) -> T:
        """Reconstruct a pure domain entity from a SQLite row or dictionary."""
