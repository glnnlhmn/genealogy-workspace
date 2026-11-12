"""Path: src/gda/model/base/media.py

Digital media asset metadata representation using Pydantic dataclasses.

Operational Role:
    Defines the digital media asset record ('Media') for digitized scans,
    microfilm frames, photographs, and audio recordings. Directly composes
    MediaID, filename, MIME type, physical orientation (DocumentSide),
    optional description, and an AuditStamp.

Architecture:
    - DocumentSide: Authoritatively imported from gda.core.enums.archival.
    - Media: Strict immutable Pydantic dataclass validating media metadata.
"""

from __future__ import annotations

import json
from dataclasses import replace
from typing import Any

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

from gda.core.enums.archival import DocumentSide
from gda.core.errors import ModelFormatError
from gda.core.introspectable import IntrospectableMixin
from gda.core.logging import GDALogger
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import MediaID
from gda.model.base.audit import AuditStamp

__version__ = "1.1.0+build.1"

__all__ = ["DocumentSide", "Media"]

_logger = GDALogger(__name__)


@dataclass(repr=False, config=ConfigDict(frozen=True, extra="forbid", strict=True))
class Media(IntrospectableMixin):
    """Digital media file attachment metadata envelope with direct audit composition."""

    media_id: MediaID
    file_name: str
    mime_type: str
    audit: AuditStamp
    side: DocumentSide = DocumentSide.FRONT
    description: str | None = None

    def __post_init__(self) -> None:
        if not self.file_name.strip():
            err_msg = "Media file_name cannot be empty."
            _logger.debug("Media file_name validation failed")
            raise ModelFormatError(err_msg, details={"field": "file_name"})

        if not self.mime_type.strip() or "/" not in self.mime_type:
            err_msg = f"Invalid Media mime_type: '{self.mime_type}'. Must contain '/'."
            _logger.debug(
                "Media mime_type validation failed",
                details={"mime_type": self.mime_type},
            )
            raise ModelFormatError(err_msg, details={"field": "mime_type", "value": self.mime_type})

        if self.description is not None and not self.description.strip():
            raise ModelFormatError(
                "Media description cannot be blank if provided.",
                details={"field": "description"},
            )

    @classmethod
    def create(
        cls,
        media_id: MediaID | str,
        file_name: str,
        mime_type: str,
        audit: AuditStamp | None = None,
        side: DocumentSide | str = DocumentSide.FRONT,
        description: str | None = None,
    ) -> Media:
        """Factory constructor instantiating a validated Media asset."""
        resolved_id = media_id if isinstance(media_id, MediaID) else MediaID(media_id)
        if isinstance(side, DocumentSide):
            resolved_side = side
        elif isinstance(side, str):
            try:
                resolved_side = DocumentSide(side.strip().upper())
            except ValueError as exc:
                raise ModelFormatError(f"Invalid DocumentSide value: '{side}'.") from exc
        else:
            raise ModelFormatError(f"Invalid DocumentSide type: {type(side).__name__}.")

        resolved_audit = audit if audit is not None else AuditStamp.now()
        clean_desc = description.strip() if description and description.strip() else None

        return cls(
            media_id=resolved_id,
            file_name=file_name.strip() if isinstance(file_name, str) else file_name,
            mime_type=mime_type.strip().lower() if isinstance(mime_type, str) else mime_type,
            audit=resolved_audit,
            side=resolved_side,
            description=clean_desc,
        )

    def update_description(self, description: str | None, audit: AuditStamp | None = None) -> Media:
        """Return a new immutable copy with updated description and refreshed audit."""
        clean = description.strip() if description and description.strip() else None
        if clean == self.description:
            return self
        next_audit = audit if audit is not None else self.audit.touch()
        return replace(self, description=clean, audit=next_audit)

    def update_side(self, side: DocumentSide | str, audit: AuditStamp | None = None) -> Media:
        """Return a new immutable copy with updated document side and refreshed audit."""
        if isinstance(side, DocumentSide):
            resolved_side = side
        elif isinstance(side, str):
            try:
                resolved_side = DocumentSide(side.strip().upper())
            except ValueError as exc:
                raise ModelFormatError(f"Invalid DocumentSide value: '{side}'.") from exc
        else:
            raise ModelFormatError(f"Invalid DocumentSide type: {type(side).__name__}.")
        if resolved_side == self.side:
            return self
        next_audit = audit if audit is not None else self.audit.touch()
        return replace(self, side=resolved_side, audit=next_audit)

    def to_dict(self) -> dict[str, Any]:
        """Serialize Media instance to a dictionary."""
        data: dict[str, Any] = {
            "media_id": str(self.media_id),
            "file_name": self.file_name,
            "mime_type": self.mime_type,
            "side": self.side.value,
            "audit": {
                "created_at": str(self.audit.created_at),
                "updated_at": str(self.audit.updated_at),
            },
        }
        if self.description is not None:
            data["description"] = self.description
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Media:
        """Deserialize a dictionary payload into an immutable Media instance."""
        if not isinstance(data, dict):
            raise ModelFormatError("Media payload must be a dictionary.")

        required_keys = {"media_id", "file_name", "mime_type", "audit"}
        missing_keys = required_keys - set(data.keys())
        if missing_keys:
            raise ModelFormatError(
                f"Missing required fields for Media: {sorted(missing_keys)}",
                details={"missing": sorted(missing_keys)},
            )

        audit_raw = data["audit"]
        if isinstance(audit_raw, AuditStamp):
            audit_stamp = audit_raw
        elif isinstance(audit_raw, dict):
            if "created_at" not in audit_raw or "updated_at" not in audit_raw:
                raise ModelFormatError("Audit dictionary missing created_at or updated_at.")
            audit_stamp = AuditStamp(
                created_at=IsoTimestamp(audit_raw["created_at"]),
                updated_at=IsoTimestamp(audit_raw["updated_at"]),
            )
        else:
            raise ModelFormatError("Media audit must be an AuditStamp or valid dictionary payload.")

        return cls.create(
            media_id=data["media_id"],
            file_name=data["file_name"],
            mime_type=data["mime_type"],
            audit=audit_stamp,
            side=data.get("side", DocumentSide.FRONT),
            description=data.get("description"),
        )

    def to_json(self) -> str:
        """Serialize Media instance to a JSON formatted string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_json(cls, payload: str) -> Media:
        """Deserialize a JSON string directly into a Media instance."""
        try:
            data = json.loads(payload)
        except Exception as exc:
            raise ModelFormatError(f"Failed to parse Media JSON string: {exc}") from exc
        return cls.from_dict(data)

    def __str__(self) -> str:
        return f"{self.file_name} [{self.side.value}]"

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(media_id={self.media_id!r}, "
            f"file_name='{self.file_name}', mime_type='{self.mime_type}', "
            f"side={self.side}, description={self.description!r}, audit={self.audit!r})"
        )
