"""Path: tests/test_gda/test_model/test_xref/test_site_xref.py

Comprehensive unit tests for gda.model.xref.site_xref.SiteXRef.

Operational Role:
    Exercises SiteXRef creation for both SmartIDPrefix AtomID entity targets
    and SourceID UUIDv4 targets, governing LocationID association, IDType and
    SmartIDPrefix properties, self-reference guards, dynamic xref_key and
    sort_key ordering, dict/JSON round-trip serialization, and defensive
    validation boundaries.
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
    OrganizationID,
    SiteID,
    SourceID,
)
from gda.model.xref import SiteXRef

__version__ = "1.0.0+build.1"


@pytest.mark.unit
@pytest.mark.smoke
def test_site_xref_atom_and_source_targets_roundtrip(
    sample_site_id: SiteID,
    sample_location_id: LocationID,
    sample_individual_id: IndividualID,
    sample_source_id: SourceID,
) -> None:
    """Verify SiteXRef creation for AtomID and SourceID targets, enums, and serialization."""
    xref_ind = SiteXRef.create(
        site_id="  sid-000005  ",
        location_id="  loc-000001  ",
        target_id="  ind-000010  ",
    )

    assert_xref_contract(xref_ind, SiteXRef)
    assert xref_ind.site_id == sample_site_id
    assert xref_ind.location_id == sample_location_id
    assert xref_ind.target_id == sample_individual_id
    assert isinstance(xref_ind.target_id, IndividualID)
    assert xref_ind.is_source_target is False
    assert xref_ind.target_id_type is IDType.SMART_ID
    assert xref_ind.target_prefix is SmartIDPrefix.IND
    assert xref_ind.xref_key == "SID-000005::IND-000010"
    assert xref_ind.sort_key == ("SID-000005", "LOC-000001", "IND-000010")
    assert str(xref_ind) == "SiteXRef [SID-000005::IND-000010] (LOC-000001 / IND)"
    assert "SiteXRef(" in repr(xref_ind)

    # SourceID target via string and direct SourceID instance
    xref_src = SiteXRef.create(
        site_id=sample_site_id,
        location_id=sample_location_id,
        target_id=f"  {SAMPLE_SOURCE_UUID_1.upper()}  ",
    )
    assert_xref_contract(xref_src, SiteXRef)
    assert xref_src.target_id == sample_source_id
    assert isinstance(xref_src.target_id, SourceID)
    assert xref_src.is_source_target is True
    assert xref_src.target_id_type is IDType.UUID
    assert xref_src.target_prefix is None
    assert str(xref_src) == f"SiteXRef [SID-000005::{SAMPLE_SOURCE_UUID_1}] (LOC-000001 / UUID)"

    # Direct typed instances and base AtomID coercion to concrete subclass
    xref_fam = SiteXRef.create(
        site_id="SID-000005",
        location_id="LOC-000001",
        target_id=FamilyID("FAM-000001"),
    )
    xref_fact = SiteXRef.create(
        site_id="SID-000005",
        location_id="LOC-000001",
        target_id=AtomID("FID-000001"),
    )
    xref_org = SiteXRef(
        site_id=sample_site_id,
        location_id=sample_location_id,
        target_id=AtomID("ORG-000001"),
    )

    assert isinstance(xref_fam.target_id, FamilyID)
    assert isinstance(xref_fact.target_id, FactID)
    assert isinstance(xref_org.target_id, OrganizationID)

    # Deterministic ordering
    assert xref_src < xref_fam < xref_fact < xref_ind < xref_org


@pytest.mark.unit
@pytest.mark.integrity
def test_site_xref_validation_errors(
    sample_site_id: SiteID,
    sample_location_id: LocationID,
) -> None:
    """Verify validation error branches for SiteXRef."""
    with pytest.raises(ModelPrefixMismatchError, match="expected 'SID'"):
        SiteXRef.create(
            site_id="LOC-000001",
            location_id="LOC-000001",
            target_id="IND-000001",
        )

    with pytest.raises(ModelPrefixMismatchError, match="expected 'LOC'"):
        SiteXRef.create(
            site_id="SID-000005",
            location_id="SID-000005",
            target_id="IND-000001",
        )

    with pytest.raises(ModelFormatError, match="Unsupported SmartIDPrefix 'XYZ'"):
        SiteXRef(
            site_id=sample_site_id,
            location_id=sample_location_id,
            target_id=AtomID("XYZ-000001"),
        )

    with pytest.raises(ModelFormatError, match="cannot reference itself as target_id"):
        SiteXRef.create(
            site_id="SID-000005",
            location_id="LOC-000001",
            target_id="SID-000005",
        )

    with pytest.raises(
        ModelFormatError, match="requires 'site_id', 'location_id', and 'target_id'"
    ):
        SiteXRef.from_dict({"site_id": "SID-000005", "location_id": "LOC-000001"})
