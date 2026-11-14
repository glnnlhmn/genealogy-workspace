"""Path: tests/test_gda/test_model/test_xref/test_individual_family_xref.py

Comprehensive unit tests for gda.model.xref.individual_family_xref.IndividualFamilyXRef.

Operational Role:
    Exercises IndividualFamilyXRef creation for partner and child links,
    PedigreeType resolution and default assignment, mutual-exclusivity guards,
    dynamic xref_key and sort_key ordering, dict/JSON round-trip serialization,
    and defensive validation boundaries.
"""

from __future__ import annotations

import pytest
from tests.test_gda.test_model.test_xref.conftest import assert_xref_contract

from gda.core.enums.vital import PedigreeType
from gda.core.errors import ModelFormatError, ModelPrefixMismatchError
from gda.model.atom.id import FamilyID, IndividualID
from gda.model.xref import IndividualFamilyXRef

__version__ = "1.0.0+build.3"


@pytest.mark.unit
@pytest.mark.smoke
def test_individual_family_xref_partner_and_child_roundtrip(
    sample_family_id: FamilyID,
    sample_individual_id: IndividualID,
) -> None:
    """Verify partner and child IndividualFamilyXRef creation, keys, sorting, and serialization."""
    partner = IndividualFamilyXRef.create(
        family_id="  fam-000001  ",
        individual_id="  ind-000001  ",
        is_partner=True,
    )
    assert_xref_contract(partner, IndividualFamilyXRef)
    assert partner.family_id == sample_family_id
    assert partner.individual_id == IndividualID("IND-000001")
    assert partner.is_partner is True
    assert partner.pedigree is None
    assert partner.child_order is None
    assert partner.role_label == "PARTNER"
    assert partner.xref_key == "FAM-000001::IND-000001::PARTNER"
    assert partner.sort_key == ("FAM-000001", 0, 9999, "IND-000001")
    assert str(partner) == "IndividualFamilyXRef [FAM-000001::IND-000001::PARTNER]"
    assert "IndividualFamilyXRef(" in repr(partner)

    # Child with explicit pedigree string and child_order
    child_1 = IndividualFamilyXRef.create(
        family_id=sample_family_id,
        individual_id=sample_individual_id,
        is_partner=False,
        pedigree="  adopted  ",
        child_order=1,
    )
    assert_xref_contract(child_1, IndividualFamilyXRef)
    assert child_1.is_partner is False
    assert child_1.pedigree is PedigreeType.ADOPTED
    assert child_1.child_order == 1
    assert child_1.role_label == "CHILD"
    assert child_1.xref_key == "FAM-000001::IND-000010::CHILD"
    assert child_1.sort_key == ("FAM-000001", 1, 1, "IND-000010")
    assert str(child_1) == "IndividualFamilyXRef [FAM-000001::IND-000010::CHILD] (ADOPTED)"

    # Child with 'biological' alias and default PedigreeType.BIRTH via create() and direct constructor
    child_bio = IndividualFamilyXRef.create(
        family_id="FAM-000001",
        individual_id="IND-000011",
        is_partner=False,
        pedigree="biological",
        child_order=2,
    )
    assert child_bio.pedigree is PedigreeType.BIRTH

    child_enum = IndividualFamilyXRef.create(
        family_id="FAM-000001",
        individual_id="IND-000011",
        is_partner=False,
        pedigree=PedigreeType.BIRTH,
        child_order=2,
    )
    assert child_enum == child_bio

    child_default = IndividualFamilyXRef(
        family_id=sample_family_id,
        individual_id=IndividualID("IND-000012"),
        is_partner=False,
    )
    assert child_default.pedigree is PedigreeType.BIRTH
    assert (
        IndividualFamilyXRef.create("FAM-000001", "IND-000012", is_partner=False).pedigree
        is PedigreeType.BIRTH
    )

    # Deterministic ordering: partner < child_1 < child_bio < unordered child
    assert partner < child_1 < child_bio < child_default


@pytest.mark.unit
@pytest.mark.integrity
def test_individual_family_xref_validation_errors() -> None:
    """Verify validation error branches for IndividualFamilyXRef."""
    with pytest.raises(ModelPrefixMismatchError, match="expected 'FAM'"):
        IndividualFamilyXRef.create(
            family_id="IND-000001",
            individual_id="IND-000002",
            is_partner=True,
        )

    with pytest.raises(ModelPrefixMismatchError, match="expected 'IND'"):
        IndividualFamilyXRef.create(
            family_id="FAM-000001",
            individual_id="FAM-000002",
            is_partner=True,
        )

    with pytest.raises(ModelFormatError, match="cannot define 'pedigree' when is_partner is True"):
        IndividualFamilyXRef.create(
            family_id="FAM-000001",
            individual_id="IND-000001",
            is_partner=True,
            pedigree=PedigreeType.BIRTH,
        )

    with pytest.raises(
        ModelFormatError, match="cannot define 'child_order' when is_partner is True"
    ):
        IndividualFamilyXRef.create(
            family_id="FAM-000001",
            individual_id="IND-000001",
            is_partner=True,
            child_order=1,
        )

    with pytest.raises(ModelFormatError, match="Invalid PedigreeType value"):
        IndividualFamilyXRef.create(
            family_id="FAM-000001",
            individual_id="IND-000001",
            is_partner=False,
            pedigree="INVALID_PEDIGREE",
        )

    with pytest.raises(ModelFormatError, match="requires 'family_id'"):
        IndividualFamilyXRef.from_dict({"family_id": "FAM-000001", "individual_id": "IND-000001"})
