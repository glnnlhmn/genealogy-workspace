# Name: test_association.py
# Path: tests/test_gda/test_model/test_base/test_association.py

"""Comprehensive test suite verifying AssociatedPersonModel and AssociationRole.

Operational Role:
    Verifies that AssociatedPersonModel enforces non-empty names, associates
    controlled evidentiary AssociationRole classifications, binds optional resolved
    IndividualIDs, and guarantees immutability.

Test Structure & Protocol:
    - Atomized tests: 1:1 behavioral contract mapping.
    - Fully decorated: Standard 7-marker taxonomy.
    - Zero production disk I/O.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from gda.model.atom.errors import AtomFormatError
from gda.model.atom.id import IndividualID
from gda.model.base.association import AssociatedPersonModel, AssociationRole

__version__ = "1.0.0+build.r4"


# ==============================================================================
# GROUP 1: ASSOCIATEDPERSONMODEL CREATION & PROPERTIES
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_associated_person_valid_creation() -> None:
    """Verify AssociatedPersonModel instantiates with full attributes."""
    ind_id = IndividualID("IND-000042")
    assoc = AssociatedPersonModel(
        name_raw="Dr. H. C. Martin",
        role=AssociationRole.PHYSICIAN,
        individual_id=ind_id,
        notes="Attending physician noted on certificate of death.",
    )
    assert assoc.name_raw == "Dr. H. C. Martin"
    assert assoc.role == AssociationRole.PHYSICIAN
    assert assoc.individual_id == ind_id
    assert assoc.notes == "Attending physician noted on certificate of death."
    assert str(assoc) == "Dr. H. C. Martin (PHYSICIAN)"
    assert repr(assoc) == (
        "AssociatedPersonModel(name_raw='Dr. H. C. Martin', role=PHYSICIAN, "
        "individual_id=IndividualID(value='IND-000042'), "
        "notes='Attending physician noted on certificate of death.')"
    )


@pytest.mark.unit
@pytest.mark.smoke
def test_associated_person_defaults() -> None:
    """Verify AssociatedPersonModel default role is OTHER with None individual_id."""
    assoc = AssociatedPersonModel(name_raw="Unknown Witness")
    assert assoc.role == AssociationRole.OTHER
    assert assoc.individual_id is None
    assert assoc.notes is None


# ==============================================================================
# GROUP 2: DEFENSIVE BOUNDARIES & IMMUTABILITY
# ==============================================================================


@pytest.mark.unit
@pytest.mark.regression
@pytest.mark.parametrize("blank_name", ["", "   ", "\t\n"])
def test_associated_person_empty_name_raises_error(blank_name: str) -> None:
    """Verify AssociatedPersonModel raises AtomFormatError if name_raw is blank."""
    with pytest.raises(AtomFormatError, match="name_raw cannot be empty"):
        AssociatedPersonModel(name_raw=blank_name)


@pytest.mark.unit
def test_association_role_members() -> None:
    """Verify AssociationRole contains expected evidentiary classifications and no structural kinship."""
    expected = {
        "WITNESS",
        "INFORMANT",
        "OFFICIANT",
        "PHYSICIAN",
        "UNDERTAKER",
        "BONDSMAN",
        "CLERGY",
        "NEIGHBOR",
        "OTHER",
    }
    actual = {r.value for r in AssociationRole}
    assert actual == expected
    assert "PARENT" not in actual
    assert "CHILD" not in actual
    assert "SPOUSE" not in actual


@pytest.mark.unit
def test_associated_person_immutability() -> None:
    """Verify AssociatedPersonModel is frozen and immutable."""
    assoc = AssociatedPersonModel(name_raw="John Smith")
    with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
        assoc.name_raw = "Jane Smith"  # type: ignore[misc]


@pytest.mark.unit
def test_associated_person_introspection() -> None:
    """Verify .help() renders member directory on AssociatedPersonModel."""
    assoc = AssociatedPersonModel(name_raw="John Smith")
    help_text = assoc.help(as_str=True)
    assert help_text is not None
    assert "=== AssociatedPersonModel Public Directory ===" in help_text
