"""Path: tests/test_gda/test_model/test_xref/test_location_xref.py

Comprehensive unit tests for gda.model.xref.location_xref.LocationXRef.

Operational Role:
    Exercises LocationXRef creation for both SmartIDPrefix AtomID entity targets
    and SourceID UUIDv4 targets, IDType and SmartIDPrefix properties, self-reference
    guards, dynamic xref_key and sort_key ordering, dict/JSON round-trip
    serialization, and defensive validation boundaries.
"""

from __future__ import annotations

import pytest
from tests.test_gda.test_model.test_xref.conftest import (
    SAMPLE_SOURCE_UUID_1,
    assert_xref_contract,
)

from gda.core.enums.core import IDType, SmartIDPrefix
from gda.core.errors import ModelFormatError, ModelPrefixMismatchError
from gda.model.atom.id import (
    AtomID,
    FactID,
    FamilyID,
    IndividualID,
    LocationID,
    RepositoryID,
    SiteID,
    SourceID,
)
from gda.model.xref import LocationXRef

__version__ = "1.0.0+build.1"


@pytest.mark.unit
@pytest.mark.smoke
def test_location_xref_atom_and_source_targets_roundtrip(
    sample_location_id: LocationID,
    sample_individual_id: IndividualID,
    sample_source_id: SourceID,
) -> None:
    """Verify LocationXRef creation for AtomID and SourceID targets, enums, and serialization."""
    xref_ind = LocationXRef.create(
        location_id="  loc-000001  ",
        target_id="  ind-000010  ",
    )

    assert_xref_contract(xref_ind, LocationXRef)
    assert xref_ind.location_id == sample_location_id
    assert xref_ind.target_id == sample_individual_id
    assert isinstance(xref_ind.target_id, IndividualID)
    assert xref_ind.is_source_target is False
    assert xref_ind.target_id_type is IDType.SMART_ID
    assert xref_ind.target_prefix is SmartIDPrefix.IND
    assert xref_ind.xref_key == "LOC-000001::IND-000010"
    assert xref_ind.sort_key == ("LOC-000001", "IND-000010")
    assert str(xref_ind) == "LocationXRef [LOC-000001::IND-000010] (IND)"
    assert "LocationXRef(" in repr(xref_ind)

    # SourceID target via string and direct SourceID instance
    xref_src = LocationXRef.create(
        location_id=sample_location_id,
        target_id=f"  {SAMPLE_SOURCE_UUID_1.upper()}  ",
    )
    assert_xref_contract(xref_src, LocationXRef)
    assert xref_src.target_id == sample_source_id
    assert isinstance(xref_src.target_id, SourceID)
    assert xref_src.is_source_target is True
    assert xref_src.target_id_type is IDType.UUID
    assert xref_src.target_prefix is None
    assert str(xref_src) == f"LocationXRef [LOC-000001::{SAMPLE_SOURCE_UUID_1}] (UUID)"
    assert (
        LocationXRef.create(location_id=sample_location_id, target_id=sample_source_id).target_id
        == sample_source_id
    )

    # Direct typed instances and base AtomID coercion to concrete subclass
    xref_fam = LocationXRef.create(location_id="LOC-000001", target_id=FamilyID("FAM-000001"))
    xref_fact = LocationXRef.create(location_id="LOC-000001", target_id=AtomID("FID-000001"))
    xref_rep = LocationXRef(location_id=sample_location_id, target_id=AtomID("REP-000001"))
    xref_site = LocationXRef.create(location_id="LOC-000001", target_id="SID-000005")

    assert isinstance(xref_fam.target_id, FamilyID)
    assert isinstance(xref_fact.target_id, FactID)
    assert isinstance(xref_rep.target_id, RepositoryID)
    assert isinstance(xref_site.target_id, SiteID)

    # Deterministic ordering
    assert xref_src < xref_fam < xref_fact < xref_ind < xref_rep < xref_site


@pytest.mark.unit
@pytest.mark.integrity
def test_location_xref_validation_errors(sample_location_id: LocationID) -> None:
    """Verify validation error branches for LocationXRef."""
    with pytest.raises(ModelPrefixMismatchError, match="expected 'LOC'"):
        LocationXRef.create(location_id="SID-000001", target_id="IND-000001")

    with pytest.raises(ModelFormatError, match="Invalid LocationXRef target_id"):
        LocationXRef.create(location_id="LOC-000001", target_id="invalid-target")

    with pytest.raises(ModelFormatError, match="Unsupported SmartIDPrefix 'XYZ'"):
        LocationXRef.create(location_id="LOC-000001", target_id="XYZ-000001")

    with pytest.raises(ModelFormatError, match="Unsupported SmartIDPrefix 'XYZ'"):
        LocationXRef.create(location_id="LOC-000001", target_id=AtomID("XYZ-000001"))

    with pytest.raises(ModelFormatError, match="Unsupported SmartIDPrefix 'XYZ'"):
        LocationXRef(location_id=sample_location_id, target_id=AtomID("XYZ-000001"))

    with pytest.raises(ModelFormatError, match="cannot reference itself as target_id"):
        LocationXRef.create(location_id="LOC-000001", target_id="LOC-000001")

    with pytest.raises(ModelFormatError, match="requires 'location_id' and 'target_id'"):
        LocationXRef.from_dict({"location_id": "LOC-000001"})
