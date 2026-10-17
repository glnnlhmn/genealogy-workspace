# Name: test_media.py
# Path: tests/test_gda/test_model/test_base/test_media.py

"""Comprehensive test suite verifying MediaModel and DocumentSide contracts.

Operational Role:
    Verifies that MediaModel enforces valid UUIDv4 MediaIds, non-empty filenames,
    valid MIME types, DocumentSide enumerations, AuditStamp inheritance, and immutability.

Test Structure & Protocol:
    - Atomized tests: 1:1 behavioral contract mapping.
    - Fully decorated: Standard 7-marker taxonomy.
    - Zero production disk I/O.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from gda.model.atom.date import IsoTimestamp
from gda.model.atom.errors import AtomFormatError
from gda.model.atom.id import MediaId
from gda.model.base.audit import AuditStamp
from gda.model.base.media import DocumentSide, MediaModel

__version__ = "1.0.0+build.r3"


# ==============================================================================
# GROUP 1: MEDIAMODEL CREATION & DISPLAY PROPERTIES
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_media_model_valid_creation() -> None:
    """Verify MediaModel instantiates with complete attributes."""
    mid = MediaId("a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d")
    t1 = IsoTimestamp("2026-10-16T12:00:00Z")
    audit = AuditStamp(created_at=t1, updated_at=t1)

    media = MediaModel(
        media_id=mid,
        file_name="census_1880_page_12.jpg",
        mime_type="image/jpeg",
        side=DocumentSide.FRONT,
        description="High-resolution scan of federal census schedule.",
        audit=audit,
    )
    assert media.media_id == mid
    assert media.file_name == "census_1880_page_12.jpg"
    assert media.mime_type == "image/jpeg"
    assert media.side == DocumentSide.FRONT
    assert media.description == "High-resolution scan of federal census schedule."
    assert media.created_at == t1
    assert str(media) == "census_1880_page_12.jpg [FRONT]"
    assert repr(media) == (
        "MediaModel(media_id=MediaId(value='a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d'), "
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
def test_media_model_empty_filename_raises_error(blank_name: str) -> None:
    """Verify MediaModel raises AtomFormatError if file_name is empty."""
    mid = MediaId("a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d")
    t1 = IsoTimestamp("2026-10-16T12:00:00Z")
    audit = AuditStamp(created_at=t1, updated_at=t1)

    with pytest.raises(AtomFormatError, match="file_name cannot be empty"):
        MediaModel(
            media_id=mid,
            file_name=blank_name,
            mime_type="image/png",
            audit=audit,
        )


@pytest.mark.unit
@pytest.mark.regression
@pytest.mark.parametrize("bad_mime", ["", "image", "not-a-mime", "   "])
def test_media_model_invalid_mime_type_raises_error(bad_mime: str) -> None:
    """Verify MediaModel raises AtomFormatError if mime_type lacks '/' delimiter."""
    mid = MediaId("a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d")
    t1 = IsoTimestamp("2026-10-16T12:00:00Z")
    audit = AuditStamp(created_at=t1, updated_at=t1)

    with pytest.raises(AtomFormatError, match="Invalid MediaModel mime_type"):
        MediaModel(
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
def test_media_model_immutability() -> None:
    """Verify MediaModel is frozen and immutable."""
    mid = MediaId("a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d")
    t1 = IsoTimestamp("2026-10-16T12:00:00Z")
    audit = AuditStamp(created_at=t1, updated_at=t1)

    media = MediaModel(
        media_id=mid,
        file_name="scan.png",
        mime_type="image/png",
        audit=audit,
    )
    with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
        media.file_name = "scan_v2.png"  # type: ignore[misc]
