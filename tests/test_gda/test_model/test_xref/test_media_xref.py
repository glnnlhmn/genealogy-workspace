"""Path: tests/test_gda/test_model/test_xref/test_media_xref.py

Comprehensive unit tests for gda.model.xref.media_xref.MediaXRef.

Operational Role:
    Exercises MediaXRef creation for both SmartIDPrefix AtomID entity targets
    and SourceID UUIDv4 targets, IDType and SmartIDPrefix properties, dynamic
    xref_key and sort_key ordering, dict/JSON round-trip serialization, and
    defensive validation boundaries.
"""

from __future__ import annotations

import pytest
from tests.test_gda.test_model.test_xref.conftest import (
    SAMPLE_MEDIA_UUID_1,
    SAMPLE_MEDIA_UUID_2,
    SAMPLE_SOURCE_UUID_1,
    assert_xref_contract,
)

from gda.core.enums.core import IDType, SmartIDPrefix
from gda.core.errors import ModelFormatError
from gda.model.atom.id import (
    AtomID,
    FactID,
    FamilyID,
    IndividualID,
    LocationID,
    MediaID,
    SiteID,
    SourceID,
)
from gda.model.xref import MediaXRef

__version__ = "1.0.0+build.3"


@pytest.mark.unit
@pytest.mark.smoke
def test_media_xref_atom_and_source_targets_roundtrip(
    sample_media_id: MediaID,
    sample_individual_id: IndividualID,
    sample_source_id: SourceID,
) -> None:
    """Verify MediaXRef creation for AtomID and SourceID targets, enums, and serialization."""
    xref_ind = MediaXRef.create(
        media_id=f"  {SAMPLE_MEDIA_UUID_1.upper()}  ",
        target_id="  ind-000010  ",
    )

    assert_xref_contract(xref_ind, MediaXRef)
    assert xref_ind.media_id == sample_media_id
    assert xref_ind.target_id == sample_individual_id
    assert isinstance(xref_ind.target_id, IndividualID)
    assert xref_ind.is_source_target is False
    assert xref_ind.target_id_type is IDType.SMART_ID
    assert xref_ind.target_prefix is SmartIDPrefix.IND
    assert xref_ind.xref_key == f"IND-000010::{SAMPLE_MEDIA_UUID_1}"
    assert xref_ind.sort_key == ("IND-000010", SAMPLE_MEDIA_UUID_1)
    assert str(xref_ind) == f"MediaXRef [IND-000010::{SAMPLE_MEDIA_UUID_1}] (IND)"
    assert "MediaXRef(" in repr(xref_ind)

    # SourceID target via string and direct SourceID instance
    xref_src = MediaXRef.create(
        media_id=MediaID(SAMPLE_MEDIA_UUID_2),
        target_id=f"  {SAMPLE_SOURCE_UUID_1.upper()}  ",
    )
    assert_xref_contract(xref_src, MediaXRef)
    assert xref_src.target_id == sample_source_id
    assert isinstance(xref_src.target_id, SourceID)
    assert xref_src.is_source_target is True
    assert xref_src.target_id_type is IDType.UUID
    assert xref_src.target_prefix is None
    assert str(xref_src) == f"MediaXRef [{SAMPLE_SOURCE_UUID_1}::{SAMPLE_MEDIA_UUID_2}] (UUID)"
    assert (
        MediaXRef.create(media_id=sample_media_id, target_id=sample_source_id).target_id
        == sample_source_id
    )

    # Direct typed instances and base AtomID coercion to concrete subclass
    xref_fam = MediaXRef.create(media_id=SAMPLE_MEDIA_UUID_1, target_id=FamilyID("FAM-000001"))
    xref_fact = MediaXRef.create(media_id=SAMPLE_MEDIA_UUID_1, target_id=AtomID("FID-000001"))
    xref_loc = MediaXRef(media_id=sample_media_id, target_id=AtomID("LOC-000001"))
    xref_site = MediaXRef.create(media_id=SAMPLE_MEDIA_UUID_1, target_id="SID-000001")

    assert isinstance(xref_fam.target_id, FamilyID)
    assert isinstance(xref_fact.target_id, FactID)
    assert isinstance(xref_loc.target_id, LocationID)
    assert isinstance(xref_site.target_id, SiteID)

    # Deterministic ordering
    assert xref_src < xref_fam < xref_fact < xref_ind < xref_loc < xref_site


@pytest.mark.unit
@pytest.mark.integrity
def test_media_xref_validation_errors(sample_media_id: MediaID) -> None:
    """Verify validation error branches for MediaXRef."""
    with pytest.raises(ModelFormatError, match="Invalid UUIDv4 format"):
        MediaXRef.create(media_id="not-a-uuid", target_id="IND-000001")

    with pytest.raises(ModelFormatError, match="Invalid MediaXRef target_id"):
        MediaXRef.create(media_id=SAMPLE_MEDIA_UUID_1, target_id="invalid-target")

    with pytest.raises(ModelFormatError, match="Unsupported SmartIDPrefix 'XYZ'"):
        MediaXRef.create(media_id=SAMPLE_MEDIA_UUID_1, target_id="XYZ-000001")

    with pytest.raises(ModelFormatError, match="Unsupported SmartIDPrefix 'XYZ'"):
        MediaXRef.create(media_id=SAMPLE_MEDIA_UUID_1, target_id=AtomID("XYZ-000001"))

    with pytest.raises(ModelFormatError, match="Unsupported SmartIDPrefix 'XYZ'"):
        MediaXRef(media_id=sample_media_id, target_id=AtomID("XYZ-000001"))

    with pytest.raises(ModelFormatError, match="requires 'media_id' and 'target_id'"):
        MediaXRef.from_dict({"media_id": SAMPLE_MEDIA_UUID_1})
