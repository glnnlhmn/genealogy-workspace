"""Path: tests/test_gda/test_model/test_base/test_base_media.py

Targeted behavioral test suite verifying Media metadata value objects.

Operational Role:
    Verifies digital media attachment metadata validation, DocumentSide
    orientation members, MIME type validation boundaries, .create() factory,
    copy-on-write mutators, and JSON/dict serialization round-trips with 100%
    statement and branch coverage.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from gda.core.enums.archival import DocumentSide
from gda.core.errors import ModelFormatError
from gda.model.atom.id import MediaID
from gda.model.base.audit import AuditStamp
from gda.model.base.media import Media

__version__ = "1.0.0+build.1"

_VALID_MEDIA_UUID_1 = "a1b2c3d4-e5f6-4a1b-8c2d-3e4f5a6b7c8d"


# ==============================================================================
# GROUP 1: MEDIA CONSTRUCTION, FACTORY & MUTATORS
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_media_valid_initialization(golden_audit: AuditStamp) -> None:
    """Verify standard Media instantiation with valid parameters."""
    media = Media(
        media_id=MediaID(_VALID_MEDIA_UUID_1),
        file_name="census_1880_page_12.jpg",
        mime_type="image/jpeg",
        audit=golden_audit,
        side=DocumentSide.FRONT,
        description="1880 Federal Census scan",
    )

    assert media.media_id == MediaID(_VALID_MEDIA_UUID_1)
    assert media.file_name == "census_1880_page_12.jpg"
    assert media.mime_type == "image/jpeg"
    assert media.side == DocumentSide.FRONT
    assert media.description == "1880 Federal Census scan"
    assert media.audit == golden_audit


@pytest.mark.unit
def test_media_default_side_and_create_factory(golden_audit: AuditStamp) -> None:
    """Verify default side and Media.create() normalization and error handling."""
    media = Media(
        media_id=MediaID(_VALID_MEDIA_UUID_1),
        file_name="scan.png",
        mime_type="image/png",
        audit=golden_audit,
    )
    assert media.side == DocumentSide.FRONT
    assert media.description is None

    created = Media.create(
        media_id=_VALID_MEDIA_UUID_1,
        file_name="  scan.png  ",
        mime_type="  IMAGE/PNG  ",
        side="back",
        description="  Reverse stamp  ",
    )
    assert created.file_name == "scan.png"
    assert created.mime_type == "image/png"
    assert created.side == DocumentSide.BACK
    assert created.description == "Reverse stamp"

    with pytest.raises(ModelFormatError, match="Invalid DocumentSide value"):
        Media.create(
            media_id=_VALID_MEDIA_UUID_1,
            file_name="scan.png",
            mime_type="image/png",
            side="INVALID_SIDE",
        )

    with pytest.raises(ModelFormatError, match="Invalid DocumentSide type"):
        Media.create(
            media_id=_VALID_MEDIA_UUID_1,
            file_name="scan.png",
            mime_type="image/png",
            side=123,  # type: ignore[arg-type]
        )


@pytest.mark.unit
def test_media_copy_on_write_mutators(sample_media: Media) -> None:
    """Verify update_description and update_side copy-on-write mutators."""
    updated_desc = sample_media.update_description("  New caption  ")
    assert updated_desc is not sample_media
    assert updated_desc.description == "New caption"
    assert updated_desc.update_description("New caption") is updated_desc
    assert updated_desc.update_description(None).description is None

    updated_side = sample_media.update_side("envelope")
    assert updated_side is not sample_media
    assert updated_side.side == DocumentSide.ENVELOPE
    assert updated_side.update_side(DocumentSide.ENVELOPE) is updated_side

    with pytest.raises(ModelFormatError, match="Invalid DocumentSide value"):
        sample_media.update_side("NO_SUCH_SIDE")

    with pytest.raises(ModelFormatError, match="Invalid DocumentSide type"):
        sample_media.update_side(99)  # type: ignore[arg-type]


# ==============================================================================
# GROUP 2: DEFENSIVE VALIDATION, SERIALIZATION & REPRESENTATIONS
# ==============================================================================


@pytest.mark.unit
@pytest.mark.regression
def test_media_validation_rejections(golden_audit: AuditStamp) -> None:
    """Verify Media rejects empty file_name, invalid mime_type, blank description, and raw IDs."""
    with pytest.raises(ModelFormatError, match="Media file_name cannot be empty"):
        Media(
            media_id=MediaID(_VALID_MEDIA_UUID_1),
            file_name="   ",
            mime_type="image/jpeg",
            audit=golden_audit,
        )

    with pytest.raises(ModelFormatError, match="Invalid Media mime_type"):
        Media(
            media_id=MediaID(_VALID_MEDIA_UUID_1),
            file_name="photo.jpg",
            mime_type="invalid_mime",
            audit=golden_audit,
        )

    with pytest.raises(ModelFormatError, match="Invalid Media mime_type"):
        Media(
            media_id=MediaID(_VALID_MEDIA_UUID_1),
            file_name="photo.jpg",
            mime_type="   ",
            audit=golden_audit,
        )

    with pytest.raises(ModelFormatError, match="Media description cannot be blank"):
        Media(
            media_id=MediaID(_VALID_MEDIA_UUID_1),
            file_name="photo.jpg",
            mime_type="image/jpeg",
            audit=golden_audit,
            description="   ",
        )

    with pytest.raises(ValidationError):
        Media(
            media_id=_VALID_MEDIA_UUID_1,  # type: ignore[arg-type]
            file_name="photo.jpg",
            mime_type="image/jpeg",
            audit=golden_audit,
        )


@pytest.mark.unit
def test_media_serialization_round_trip(sample_media: Media, golden_audit: AuditStamp) -> None:
    """Verify Media to_dict, from_dict, to_json, and from_json round-trip fidelity."""
    payload = sample_media.to_dict()
    assert payload["media_id"] == _VALID_MEDIA_UUID_1
    assert payload["side"] == "FRONT"
    assert Media.from_dict(payload) == sample_media

    minimal = Media.create(
        media_id=_VALID_MEDIA_UUID_1,
        file_name="minimal.jpg",
        mime_type="image/jpeg",
        audit=golden_audit,
    )
    min_payload = minimal.to_dict()
    assert "description" not in min_payload
    assert Media.from_dict(min_payload) == minimal

    obj_payload = dict(min_payload)
    obj_payload["audit"] = golden_audit
    assert Media.from_dict(obj_payload) == minimal

    json_str = sample_media.to_json()
    assert Media.from_json(json_str) == sample_media

    with pytest.raises(ModelFormatError, match="Media payload must be a dictionary"):
        Media.from_dict("bad")  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="Missing required fields for Media"):
        Media.from_dict({"media_id": _VALID_MEDIA_UUID_1})

    with pytest.raises(ModelFormatError, match="Audit dictionary missing created_at"):
        Media.from_dict(
            {
                "media_id": _VALID_MEDIA_UUID_1,
                "file_name": "a.jpg",
                "mime_type": "image/jpeg",
                "audit": {"created_at": "2026-01-01T00:00:00Z"},
            }
        )

    with pytest.raises(ModelFormatError, match="Media audit must be an AuditStamp"):
        Media.from_dict(
            {
                "media_id": _VALID_MEDIA_UUID_1,
                "file_name": "a.jpg",
                "mime_type": "image/jpeg",
                "audit": "bad",
            }
        )

    with pytest.raises(ModelFormatError, match="Failed to parse Media JSON"):
        Media.from_json("{invalid-json")


@pytest.mark.unit
def test_media_string_repr_and_enums(golden_audit: AuditStamp) -> None:
    """Verify str(), repr(), .help(), and DocumentSide enumeration members."""
    media = Media(
        media_id=MediaID(_VALID_MEDIA_UUID_1),
        file_name="record.pdf",
        mime_type="application/pdf",
        audit=golden_audit,
        side=DocumentSide.ATTACHMENT,
        description="Will transcript",
    )
    assert str(media) == "record.pdf [ATTACHMENT]"
    repr_str = repr(media)
    assert "Media(" in repr_str
    assert "file_name='record.pdf'" in repr_str
    assert "description='Will transcript'" in repr_str
    assert media.help(as_str=True) is not None

    expected = {
        "FRONT",
        "BACK",
        "INSIDE",
        "OUTSIDE",
        "ENVELOPE",
        "ATTACHMENT",
        "FULL_SPREAD",
        "ENCLOSURE",
        "UNKNOWN",
    }
    assert {s.value for s in DocumentSide} == expected
