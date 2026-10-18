"""Path: tests/test_gda/test_model/test_base/test_media.py

Comprehensive test suite verifying Media and DocumentSide contracts.

Operational Role:
    Verifies that Media enforces valid UUIDv4 MediaIDs, non-empty filenames,
    valid MIME types, DocumentSide enumerations, AuditStamp composition, and immutability.

Test Structure & Protocol:
    - Atomized tests: 1:1 behavioral contract mapping.
    - Fully decorated: Standard 7-marker taxonomy.
    - Zero production disk I/O.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from gda.core.errors import ModelFormatError
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import MediaID
from gda.model.base.audit import AuditStamp
from gda.model.base.media import DocumentSide, Media

__version__ = "1.0.0+build.4"


# ==============================================================================
# GROUP 1: MEDIA CREATION & DISPLAY PROPERTIES
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_media_valid_creation() -> None:
    """Verify Media instantiates with complete attributes and audit stamp."""
    mid = MediaID("a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d")
    t1 = IsoTimestamp("2026-10-16T12:00:00Z")
    audit = AuditStamp(created_at=t1, updated_at=t1)

    media = Media(
        media_id=mid,
        file_name="census_1880_page_12.jpg",
        mime_type="image/jpeg",
        audit=audit,
        side=DocumentSide.FRONT,
        description="High-resolution scan of federal census schedule.",
    )
    assert media.media_id == mid
    assert media.file_name == "census_1880_page_12.jpg"
    assert media.mime_type == "image/jpeg"
    assert media.side == DocumentSide.FRONT
    assert media.description == "High-resolution scan of federal census schedule."
    assert media.audit == audit
    assert str(media) == "census_1880_page_12.jpg [FRONT]"
    assert repr(media) == (
        "Media(media_id=MediaID(value='a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d'), "
        "file_name='census_1880_page_12.jpg', mime_type='image/jpeg', side=FRONT, "
        "description='High-resolution scan of federal census schedule.', "
        "audit=AuditStamp(created_at=IsoTimestamp(value='2026-10-16T12:00:00Z'), "
        "updated_at=IsoTimestamp(value='2026-10-16T12:00:00Z')))"
    )


# ==============================================================================
# GROUP 2: DEFENSIVE BOUNDARIES & INVALID ATTRIBUTES
# ==============================================================================


@pytest.mark.unit
@pytest.mark.regression
@pytest.mark.parametrize("blank_name", ["", "   ", "\t\n"])
def test_media_empty_filename_raises_error(blank_name: str) -> None:
    """Verify Media raises ModelFormatError if file_name is empty."""
    mid = MediaID("a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d")
    t1 = IsoTimestamp("2026-10-16T12:00:00Z")
    audit = AuditStamp(created_at=t1, updated_at=t1)

    with pytest.raises(ModelFormatError, match="file_name cannot be empty"):
        Media(
            media_id=mid,
            file_name=blank_name,
            mime_type="image/png",
            audit=audit,
        )


@pytest.mark.unit
@pytest.mark.regression
@pytest.mark.parametrize("bad_mime", ["", "image", "not-a-mime", "   "])
def test_media_invalid_mime_type_raises_error(bad_mime: str) -> None:
    """Verify Media raises ModelFormatError if mime_type lacks '/' delimiter."""
    mid = MediaID("a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d")
    t1 = IsoTimestamp("2026-10-16T12:00:00Z")
    audit = AuditStamp(created_at=t1, updated_at=t1)

    with pytest.raises(ModelFormatError, match="Invalid Media mime_type"):
        Media(
            media_id=mid,
            file_name="doc.pdf",
            mime_type=bad_mime,
            audit=audit,
        )


@pytest.mark.unit
def test_document_side_enumeration_members() -> None:
    """Verify DocumentSide contains all physical document orientation values."""
    expected = {"FRONT", "BACK", "ENVELOPE", "ATTACHMENT", "FULL_SPREAD"}
    actual = {s.value for s in DocumentSide}
    assert actual == expected


@pytest.mark.unit
def test_media_immutability() -> None:
    """Verify Media is frozen and immutable."""
    mid = MediaID("a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d")
    t1 = IsoTimestamp("2026-10-16T12:00:00Z")
    audit = AuditStamp(created_at=t1, updated_at=t1)

    media = Media(
        media_id=mid,
        file_name="scan.png",
        mime_type="image/png",
        audit=audit,
    )
    with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
        media.file_name = "scan_v2.png"  # type: ignore[misc]
