# Name: media.py
# Path: src/gda/model/base/media.py

"""Digital media attachment metadata model using Pydantic dataclasses.

Operational Role:
    Defines the digital media asset record ('MediaModel') for digitized scans,
    microfilm frames, photographs, and audio recordings. Pairs a UUIDv4 MediaId
    with filename, MIME type, physical document side, notes, and an AuditStamp.

Architecture:
    - DocumentSide: Enumeration defining physical document orientation/face.
    - MediaModel: Pydantic dataclass validating media attachment metadata.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

from gda.core.logging import GDALogger
from gda.model.atom.errors import AtomFormatError
from gda.model.atom.id import MediaId
from gda.model.base.auditable import AuditableModel

__version__ = "1.0.0+build.r2"

_logger = GDALogger(__name__)


class DocumentSide(StrEnum):
    """Controlled orientation or face of physical document media."""

    FRONT = "FRONT"
    BACK = "BACK"
    ENVELOPE = "ENVELOPE"
    ATTACHMENT = "ATTACHMENT"
    FULL_SPREAD = "FULL_SPREAD"


@dataclass(config=ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True))
class MediaModel(AuditableModel):
    """Digital media file attachment metadata envelope."""

    media_id: MediaId
    file_name: str
    mime_type: str
    side: DocumentSide = DocumentSide.FRONT
    description: str | None = None

    def __post_init__(self) -> None:
        if not self.file_name.strip():
            err_msg = "MediaModel file_name cannot be empty."
            _logger.debug("MediaModel file_name validation failed")
            raise AtomFormatError(err_msg, details={"field": "file_name"})

        if not self.mime_type.strip() or "/" not in self.mime_type:
            err_msg = (
                f"Invalid MediaModel mime_type: '{self.mime_type}'. Must contain '/'."
            )
            _logger.debug(
                "MediaModel mime_type validation failed",
                details={"mime_type": self.mime_type},
            )
            raise AtomFormatError(
                err_msg, details={"field": "mime_type", "value": self.mime_type}
            )

    def __str__(self) -> str:
        return f"{self.file_name} [{self.side.value}]"

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(media_id={self.media_id!r}, "
            f"file_name='{self.file_name}', mime_type='{self.mime_type}', "
            f"side={self.side}, description={self.description!r}, audit={self.audit!r})"
        )
