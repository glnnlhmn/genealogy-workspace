"""Path: tests/test_gda/test_model/test_base/test_association.py

Atomized behavioral test suite for AssociatedIndividual composite.

Operational Role:
    Verifies instantiation invariants, individual_id vs name_raw resolution rules,
    controlled AssociatedRole bindings, tertiary_roles disjointness, SiteID residence
    links, SID rejection boundaries, serialization, and introspection contracts.

Test Structure & Protocol:
    - Atomized tests: 1:1 behavioral contract verification.
    - Fully decorated: Pytest marker taxonomy (@pytest.mark.unit, @pytest.mark.smoke).
    - Dependencies: Synthetic in-memory fixtures with isolated basetemp execution.
"""

from __future__ import annotations

import pytest

from gda.core.errors import ModelFormatError, ModelPrefixMismatchError
from gda.enums.core import AssociatedRole
from gda.model.atom.id import IndividualID, SiteID
from gda.model.base.association import AssociatedIndividual

__version__ = "1.0.0+build.4"


# ==============================================================================
# GROUP 1: INITIALIZATION & IDENTITY INVARIANTS
# Note: Verifies resolution rules between individual_id and name_raw
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_associated_individual_init_with_name_raw_only() -> None:
    """Verify initialization when only verbatim name_raw is supplied."""
    assoc = AssociatedIndividual(name_raw="Rev. James Caldwell")
    assert assoc.name_raw == "Rev. James Caldwell"
    assert assoc.individual_id is None
    assert assoc.role == AssociatedRole.OTHER
    assert assoc.tertiary_roles == []
    assert assoc.residence is None
    assert assoc.role_verbatim is None
    assert assoc.comment is None


@pytest.mark.unit
def test_associated_individual_init_with_individual_id_only() -> None:
    """Verify initialization when only individual_id is supplied without name_raw."""
    ind_id = IndividualID("IND-000101")
    assoc = AssociatedIndividual(individual_id=ind_id)
    assert assoc.individual_id == ind_id
    assert assoc.name_raw is None
    assert assoc.role == AssociatedRole.OTHER
    assert assoc.tertiary_roles == []
    assert assoc.residence is None


@pytest.mark.unit
def test_associated_individual_init_with_both_id_and_name_raw() -> None:
    """Verify initialization when both individual_id and name_raw are provided."""
    ind_id = IndividualID("IND-000202")
    residence_id = SiteID("SID-000888")
    assoc = AssociatedIndividual(
        individual_id=ind_id,
        name_raw="Dr. Marcus Welby",
        role=AssociatedRole.PHYSICIAN,
        role_verbatim="Attending Physician",
        tertiary_roles=[AssociatedRole.WITNESS],
        residence=residence_id,
        comment="Signed affidavit on page 2",
    )
    assert assoc.individual_id == ind_id
    assert assoc.name_raw == "Dr. Marcus Welby"
    assert assoc.role == AssociatedRole.PHYSICIAN
    assert assoc.tertiary_roles == [AssociatedRole.WITNESS]
    assert assoc.residence == residence_id
    assert assoc.comment == "Signed affidavit on page 2"


# ==============================================================================
# GROUP 2: BOUNDARY, PREFIX & ROLE DISJOINTNESS VALIDATION
# Note: Verifies error handling on missing identifiers, SID misuse, and duplicate roles
# ==============================================================================


@pytest.mark.unit
@pytest.mark.regression
def test_associated_individual_missing_both_identifiers_fails() -> None:
    """Verify ModelFormatError is raised when neither individual_id nor name_raw is supplied."""
    with pytest.raises(
        ModelFormatError, match="requires either a valid 'individual_id'"
    ):
        AssociatedIndividual()


@pytest.mark.unit
@pytest.mark.regression
def test_associated_individual_empty_name_raw_without_id_fails() -> None:
    """Verify ModelFormatError is raised when name_raw is empty whitespace and no ID is provided."""
    with pytest.raises(
        ModelFormatError, match="requires either a valid 'individual_id'"
    ):
        AssociatedIndividual(name_raw="   ")


@pytest.mark.unit
@pytest.mark.regression
def test_associated_individual_empty_name_raw_with_id_succeeds() -> None:
    """Verify empty name_raw is permitted when a valid individual_id is supplied."""
    ind_id = IndividualID("IND-000303")
    assoc = AssociatedIndividual(individual_id=ind_id, name_raw="")
    assert assoc.individual_id == ind_id


@pytest.mark.unit
@pytest.mark.regression
def test_associated_individual_rejects_site_id_as_individual_id() -> None:
    """Verify ModelPrefixMismatchError is raised when an SID string is supplied for individual_id."""
    with pytest.raises(ModelPrefixMismatchError, match="expected prefix 'IND'"):
        IndividualID("SID-000101")


@pytest.mark.unit
@pytest.mark.regression
def test_associated_individual_primary_role_in_tertiary_roles_fails() -> None:
    """Verify ModelFormatError is raised when primary role is duplicated in tertiary_roles."""
    with pytest.raises(
        ModelFormatError, match="cannot be duplicated in tertiary_roles"
    ):
        AssociatedIndividual(
            name_raw="John Doe",
            role=AssociatedRole.EMPLOYER,
            tertiary_roles=[AssociatedRole.EMPLOYER],
        )


@pytest.mark.unit
@pytest.mark.regression
def test_associated_individual_duplicate_tertiary_roles_fails() -> None:
    """Verify ModelFormatError is raised when duplicate roles exist within tertiary_roles."""
    with pytest.raises(
        ModelFormatError, match="Duplicate roles detected within tertiary_roles"
    ):
        AssociatedIndividual(
            name_raw="John Doe",
            role=AssociatedRole.EMPLOYER,
            tertiary_roles=[AssociatedRole.WITNESS, AssociatedRole.WITNESS],
        )


# ==============================================================================
# GROUP 3: ROLES, DICT SERIALIZATION & STRING REPRESENTATION
# Note: Verifies role enum value binding, to_dict serialization, and string outputs
# ==============================================================================


@pytest.mark.unit
def test_associated_individual_str_representation_with_multiple_roles() -> None:
    """Verify __str__ format displays name_raw and all role values correctly."""
    assoc = AssociatedIndividual(
        name_raw="Eleanor Vance",
        role=AssociatedRole.WITNESS,
        tertiary_roles=[AssociatedRole.NEXT_OF_KIN],
    )
    expected = f"Eleanor Vance ({AssociatedRole.WITNESS.value}, {AssociatedRole.NEXT_OF_KIN.value})"
    assert str(assoc) == expected


@pytest.mark.unit
def test_associated_individual_str_representation_with_id() -> None:
    """Verify __str__ format displays individual_id when name_raw is None."""
    ind_id = IndividualID("IND-000404")
    assoc = AssociatedIndividual(individual_id=ind_id, role=AssociatedRole.INFORMANT)
    assert str(assoc) == f"IND-000404 ({AssociatedRole.INFORMANT.value})"


@pytest.mark.unit
def test_associated_individual_to_dict_serialization() -> None:
    """Verify to_dict returns expected primitive dictionary structure with enum values."""
    ind_id = IndividualID("IND-000505")
    residence_id = SiteID("SID-000123")
    assoc = AssociatedIndividual(
        individual_id=ind_id,
        name_raw="Arthur Hastings",
        role=AssociatedRole.OTHER,
        role_verbatim="Companion",
        tertiary_roles=[AssociatedRole.WITNESS],
        residence=residence_id,
        comment="Traveled together",
    )
    data = assoc.to_dict()
    assert data == {
        "role": AssociatedRole.OTHER.value,
        "individual_id": "IND-000505",
        "name_raw": "Arthur Hastings",
        "role_verbatim": "Companion",
        "tertiary_roles": [AssociatedRole.WITNESS.value],
        "residence": "SID-000123",
        "comment": "Traveled together",
    }


@pytest.mark.unit
def test_associated_individual_repr_formatting() -> None:
    """Verify __repr__ formats all attributes cleanly."""
    assoc = AssociatedIndividual(name_raw="Test Subject", role=AssociatedRole.OTHER)
    repr_str = repr(assoc)
    assert "AssociatedIndividual" in repr_str
    assert "Test Subject" in repr_str


@pytest.mark.unit
def test_associated_individual_introspectable_execution(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify IntrospectableMixin help output executes without error."""
    assoc = AssociatedIndividual(name_raw="Test Subject")
    assoc.help()
    captured = capsys.readouterr()
    assert "AssociatedIndividual" in captured.out or assoc.__doc__ is not None
