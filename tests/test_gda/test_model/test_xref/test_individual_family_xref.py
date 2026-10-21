"""Path: tests/test_gda/test_model/test_xref/test_individual_family_xref.py

Atomized unit and regression test suite for IndividualFamilyXRef.

Operational Role:
    Verifies behavioral invariants, compound primary key minting, frozen
    immutability, whitespace stripping, and boundary validation for IndividualFamilyXRef.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest
from pydantic import ValidationError

from gda.core.errors import ModelFormatError
from gda.enums.core import AssociatedRole
from gda.enums.vital import PedigreeType
from gda.model.atom.id import FamilyID, IndividualID
from gda.model.xref.individual_family_xref import IndividualFamilyXRef

__version__ = "1.0.0+build.1"


# ==============================================================================
# GROUP 1: IndividualFamilyXRef Creation & Immutability
# ==============================================================================


@pytest.mark.unit
def test_individual_family_xref_valid_creation() -> None:
    """Verify frozen immutability and attribute preservation on IndividualFamilyXRef."""
    p1 = IndividualID("IND-000001")
    f1 = FamilyID("FAM-000001")
    key = IndividualFamilyXRef.create_key(p1, "PARTNER", f1)

    edge = IndividualFamilyXRef(
        xref_id=key,
        subject_id=p1,
        target_id=f1,
        relation_type="PARTNER",
        role=AssociatedRole.SPOUSE,
        display_label="Spousal Partner",
    )

    assert edge.xref_id == "IND-000001::PARTNER::FAM-000001"
    assert edge.subject_id == p1
    assert edge.target_id == f1
    assert edge.relation_type == "PARTNER"
    assert edge.role == AssociatedRole.SPOUSE
    assert edge.display_label == "Spousal Partner"
    assert edge.compiled_at.value is not None

    with pytest.raises((FrozenInstanceError, ValidationError)):
        edge.relation_type = "CHILD"  # type: ignore[misc]


@pytest.mark.unit
def test_create_key_formatting_combinations() -> None:
    """Verify deterministic compound key formatting with enums and raw strings."""
    p1 = IndividualID("IND-000001")
    f1 = FamilyID("FAM-000001")

    assert (
        IndividualFamilyXRef.create_key(p1, "PARTNER", f1)
        == "IND-000001::PARTNER::FAM-000001"
    )
    assert (
        IndividualFamilyXRef.create_key(p1, "CHILD", f1, PedigreeType.ADOPTED)
        == "IND-000001::CHILD::FAM-000001::Adopted"
    )
    assert (
        IndividualFamilyXRef.create_key(p1, "PARTNER", f1, "SPOUSE")
        == "IND-000001::PARTNER::FAM-000001::SPOUSE"
    )


# ==============================================================================
# GROUP 2: Validation Boundaries & Defensive Constraints
# ==============================================================================


@pytest.mark.regression
def test_individual_family_xref_whitespace_stripping() -> None:
    """Verify string fields automatically strip leading and trailing whitespace."""
    p1 = IndividualID("IND-000001")
    f1 = FamilyID("FAM-000001")

    edge = IndividualFamilyXRef(
        xref_id="  IND-000001::PARTNER::FAM-000001  ",
        subject_id=p1,
        target_id=f1,
        relation_type="  PARTNER  ",
        display_label="  Primary Spouse  ",
    )
    assert edge.xref_id == "IND-000001::PARTNER::FAM-000001"
    assert edge.relation_type == "PARTNER"
    assert edge.display_label == "Primary Spouse"


@pytest.mark.regression
def test_individual_family_xref_empty_strings_rejected() -> None:
    """Verify empty or whitespace-only keys raise ModelFormatError."""
    p1 = IndividualID("IND-000001")
    f1 = FamilyID("FAM-000001")

    with pytest.raises(ModelFormatError, match="xref_id"):
        IndividualFamilyXRef(
            xref_id="   ", subject_id=p1, target_id=f1, relation_type="PARTNER"
        )

    with pytest.raises(ModelFormatError, match="relation_type"):
        IndividualFamilyXRef(
            xref_id="KEY", subject_id=p1, target_id=f1, relation_type="   "
        )


@pytest.mark.regression
def test_individual_family_xref_forbids_extra_fields() -> None:
    """Verify Pydantic rejects extra undeclared attributes."""
    p1 = IndividualID("IND-000001")
    f1 = FamilyID("FAM-000001")

    with pytest.raises(ValidationError):
        IndividualFamilyXRef(  # type: ignore[call-arg]
            xref_id="KEY",
            subject_id=p1,
            target_id=f1,
            relation_type="PARTNER",
            extra="UNALLOWED",
        )
