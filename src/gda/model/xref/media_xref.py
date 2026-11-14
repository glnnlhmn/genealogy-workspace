"""Path: src/gda/model/xref/media_xref.py

Cross-reference bridge and index model linking digital media assets to entities and sources.

Operational Role:
    Defines MediaXRef (frozen Pydantic dataclass) as a derived relational index
    row linking a MediaID (UUIDv4) to a polymorphic target identifier (canonical
    SmartIDPrefix AtomID subclass or SourceID UUIDv4), exposing IDType and
    SmartIDPrefix classification properties.
"""

from __future__ import annotations

import json
from functools import total_ordering
from typing import Any

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from gda.core.enums.core import IDType, SmartIDPrefix
from gda.core.errors import ModelFormatError
from gda.core.introspectable import IntrospectableMixin
from gda.core.types import ATOM_ID_REGEX, UUID_V4_REGEX
from gda.model.atom.id import (
    AtomID,
    DraftRecordID,
    FactID,
    FamilyID,
    IndividualID,
    LocationID,
    MediaID,
    NoteID,
    OrganizationID,
    RepositoryID,
    SiteID,
    SourceID,
)

__version__ = "1.0.0+build.3"

__all__ = [
    "MediaTargetID",
    "MediaXRef",
]

type MediaTargetID = AtomID | SourceID

_ATOM_PREFIX_MAP: dict[SmartIDPrefix, type[AtomID]] = {
    SmartIDPrefix.DRF: DraftRecordID,
    SmartIDPrefix.FID: FactID,
    SmartIDPrefix.FAM: FamilyID,
    SmartIDPrefix.IND: IndividualID,
    SmartIDPrefix.LOC: LocationID,
    SmartIDPrefix.NOT: NoteID,
    SmartIDPrefix.ORG: OrganizationID,
    SmartIDPrefix.REP: RepositoryID,
    SmartIDPrefix.SID: SiteID,
}


def _resolve_target_id(raw: MediaTargetID | str) -> MediaTargetID:
    """Resolve a canonical SmartIDPrefix AtomID subclass, SourceID instance, or raw string token."""
    if isinstance(raw, SourceID):
        return raw

    if isinstance(raw, AtomID):
        try:
            prefix_enum = SmartIDPrefix(raw.prefix)
        except ValueError as exc:
            raise ModelFormatError(
                f"Unsupported SmartIDPrefix '{raw.prefix}' in target_id '{raw.value}'."
            ) from exc
        atom_cls = _ATOM_PREFIX_MAP[prefix_enum]
        return raw if type(raw) is atom_cls else atom_cls(raw.value)

    token = str(raw).strip()
    upper_token = token.upper()
    if ATOM_ID_REGEX.match(upper_token):
        raw_prefix = upper_token.split("-", 1)[0]
        try:
            prefix_enum = SmartIDPrefix(raw_prefix)
        except ValueError as exc:
            raise ModelFormatError(
                f"Unsupported SmartIDPrefix '{raw_prefix}' in target_id '{raw}'."
            ) from exc
        return _ATOM_PREFIX_MAP[prefix_enum](upper_token)

    lower_token = token.lower()
    if UUID_V4_REGEX.match(lower_token):
        return SourceID(lower_token)

    raise ModelFormatError(
        f"Invalid MediaXRef target_id: '{raw}'. Must be a canonical SmartIDPrefix AtomID "
        "('AAA-######') or lowercase RFC 4122 UUIDv4 SourceID."
    )


@total_ordering
@dataclass(repr=False, config=ConfigDict(kw_only=True, frozen=True, extra="forbid", strict=True))
class MediaXRef(IntrospectableMixin):
    """Immutable derived index row linking a MediaID to a canonical AtomID or SourceID."""

    media_id: MediaID = Field(
        ...,
        description="Canonical MediaID (UUIDv4) of the digital media asset.",
    )
    target_id: AtomID | SourceID = Field(
        ...,
        description="Canonical AtomID ('AAA-######') or SourceID (UUIDv4) linked to the media asset.",
    )

    def __post_init__(self) -> None:
        """Enforce canonical SmartIDPrefix membership when target_id is an AtomID."""
        if isinstance(self.target_id, AtomID):
            try:
                prefix_enum = SmartIDPrefix(self.target_id.prefix)
            except ValueError as exc:
                raise ModelFormatError(
                    f"Unsupported SmartIDPrefix '{self.target_id.prefix}' in target_id '{self.target_id.value}'."
                ) from exc
            expected_cls = _ATOM_PREFIX_MAP[prefix_enum]
            if type(self.target_id) is not expected_cls:
                object.__setattr__(self, "target_id", expected_cls(self.target_id.value))

    @property
    def is_source_target(self) -> bool:
        """Return True when target_id is a SourceID rather than an AtomID."""
        return isinstance(self.target_id, SourceID)

    @property
    def target_id_type(self) -> IDType:
        """Return IDType.UUID for SourceID targets or IDType.SMART_ID for AtomID targets."""
        return IDType.UUID if isinstance(self.target_id, SourceID) else IDType.SMART_ID

    @property
    def target_prefix(self) -> SmartIDPrefix | None:
        """Return SmartIDPrefix for AtomID targets or None for UUID SourceID targets."""
        if isinstance(self.target_id, SourceID):
            return None
        return SmartIDPrefix(self.target_id.prefix)

    @property
    def xref_key(self) -> str:
        """Return dynamic compound index key '<target_id>::<media_id>'."""
        return f"{self.target_id.value}::{self.media_id.value}"

    @property
    def sort_key(self) -> tuple[str, str]:
        """Return deterministic ordering tuple (target_id, media_id)."""
        return (self.target_id.value, self.media_id.value)

    @classmethod
    def create(
        cls,
        media_id: MediaID | str,
        target_id: MediaTargetID | str,
    ) -> MediaXRef:
        """Factory constructor instantiating a validated MediaXRef."""
        res_media = (
            media_id if isinstance(media_id, MediaID) else MediaID(str(media_id).strip().lower())
        )
        res_target = _resolve_target_id(target_id)
        return cls(media_id=res_media, target_id=res_target)

    def to_dict(self) -> dict[str, Any]:
        """Serialize MediaXRef to a dictionary."""
        return {
            "media_id": self.media_id.value,
            "target_id": self.target_id.value,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MediaXRef:
        """Deserialize a dictionary payload into a MediaXRef."""
        if not isinstance(data, dict):
            raise ModelFormatError("MediaXRef payload must be a dictionary.")

        mid = data.get("media_id")
        tid = data.get("target_id")

        if not mid or not tid:
            raise ModelFormatError("MediaXRef requires 'media_id' and 'target_id'.")

        return cls.create(media_id=str(mid), target_id=str(tid))

    def to_json(self) -> str:
        """Serialize MediaXRef to a JSON formatted string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_json(cls, payload: str) -> MediaXRef:
        """Deserialize a JSON string directly into a MediaXRef."""
        try:
            data = json.loads(payload)
        except Exception as exc:
            raise ModelFormatError(f"Failed to parse MediaXRef JSON string: {exc}") from exc
        return cls.from_dict(data)

    def __lt__(self, other: Any) -> bool:
        """Support deterministic target and media sorting."""
        if isinstance(other, MediaXRef):
            return self.sort_key < other.sort_key
        return NotImplemented

    def __str__(self) -> str:
        label = (
            self.target_prefix.value
            if self.target_prefix is not None
            else self.target_id_type.value
        )
        return f"MediaXRef [{self.xref_key}] ({label})"

    def __repr__(self) -> str:
        return f"MediaXRef(media_id={self.media_id!r}, target_id={self.target_id!r})"
