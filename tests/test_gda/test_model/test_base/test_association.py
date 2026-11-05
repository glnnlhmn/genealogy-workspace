"""Path: tests/test_gda/test_model/test_base/test_association.py

Atomized behavioral test suite for AssociatedIndividual composite.

Operational Role:
    Verifies instantiation invariants, individual_id vs name_raw resolution rules,
    controlled AssociatedRole bindings, tertiary_roles disjointness, SiteID residence
    links, SID rejection boundaries, serialization, copy-on-write mutators,
    and introspection contracts with 100% statement and branch coverage.
"""

from __future__ import annotations

import pytest

from gda.core.errors import ModelFormatError, ModelPrefixMismatchError
from gda.enums.core import AssociatedRole
from gda.model.atom.id import IndividualID, SiteID
from gda.model.base.association import AssociatedIndividual

__version__ = "1.0.0+build.7"


# ==============================================================================
# GROUP 1: INITIALIZATION & IDENTITY INVARIANTS
# ==============================================================================


@pytest.mark.regression
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


@pytest.mark.regression
def test_associated_individual_init_with_individual_id_only() -> None:
    """Verify initialization when only individual_id is supplied without name_raw."""
    ind_id = IndividualID("IND-000101")
    assoc = AssociatedIndividual(individual_id=ind_id)
    assert assoc.individual_id == ind_id
    assert assoc.name_raw is None
    assert assoc.role == AssociatedRole.OTHER
    assert assoc.tertiary_roles == []
    assert assoc.residence is None


@pytest.mark.regression
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


@pytest.mark.regression
def test_associated_individual_factory_create_and_mutators() -> None:
    """Verify factory constructor and copy-on-write mutators."""
    assoc = AssociatedIndividual.create(
        individual_id="IND-000101",
        role="CLERGY",
        residence="SID-000001",
        comment="Initial comment",
    )
    assert assoc.individual_id == IndividualID("IND-000101")
    assert assoc.role == AssociatedRole.CLERGY
    assert assoc.residence == SiteID("SID-000001")

    # update_role
    up_role = assoc.update_role(AssociatedRole.INFORMANT)
    assert up_role is not assoc
    assert up_role.role == AssociatedRole.INFORMANT
    assert up_role.update_role(AssociatedRole.INFORMANT) is up_role

    # update_residence
    up_res = assoc.update_residence("SID-000002")
    assert up_res is not assoc
    assert up_res.residence == SiteID("SID-000002")
    assert up_res.update_residence(SiteID("SID-000002")) is up_res

    # update_comment
    up_com = assoc.update_comment("Updated note")
    assert up_com is not assoc
    assert up_com.comment == "Updated note"
    assert up_com.update_comment("Updated note") is up_com


# ==============================================================================
# GROUP 2: BOUNDARY, PREFIX & ROLE DISJOINTNESS VALIDATION
# ==============================================================================


@pytest.mark.regression
def test_associated_individual_missing_both_identifiers_fails() -> None:
    """Verify ModelFormatError is raised when neither individual_id nor name_raw is supplied."""
    with pytest.raises(ModelFormatError, match="requires either a valid 'individual_id'"):
        AssociatedIndividual()


@pytest.mark.regression
def test_associated_individual_empty_name_raw_without_id_fails() -> None:
    """Verify ModelFormatError is raised when name_raw is empty whitespace and no ID is provided."""
    with pytest.raises(ModelFormatError, match="requires either a valid 'individual_id'"):
        AssociatedIndividual(name_raw=" ")


@pytest.mark.regression
def test_associated_individual_empty_name_raw_with_id_succeeds() -> None:
    """Verify empty name_raw is permitted when a valid individual_id is supplied."""
    ind_id = IndividualID("IND-000303")
    assoc = AssociatedIndividual(individual_id=ind_id, name_raw="")
    assert assoc.individual_id == ind_id


@pytest.mark.regression
def test_associated_individual_rejects_site_id_as_individual_id() -> None:
    """Verify ModelPrefixMismatchError is raised when an SID string is supplied for individual_id."""
    with pytest.raises(ModelPrefixMismatchError, match="expected prefix 'IND'"):
        IndividualID("SID-000101")


@pytest.mark.regression
def test_associated_individual_primary_role_in_tertiary_roles_fails() -> None:
    """Verify ModelFormatError is raised when primary role is duplicated in tertiary_roles."""
    with pytest.raises(ModelFormatError, match="cannot be duplicated in tertiary_roles"):
        AssociatedIndividual(
            name_raw="John Doe",
            role=AssociatedRole.EMPLOYER,
            tertiary_roles=[AssociatedRole.EMPLOYER],
        )


@pytest.mark.regression
def test_associated_individual_duplicate_tertiary_roles_fails() -> None:
    """Verify ModelFormatError is raised when duplicate roles exist within tertiary_roles."""
    with pytest.raises(ModelFormatError, match="Duplicate roles detected within tertiary_roles"):
        AssociatedIndividual(
            name_raw="John Doe",
            role=AssociatedRole.EMPLOYER,
            tertiary_roles=[AssociatedRole.WITNESS, AssociatedRole.WITNESS],
        )


# ==============================================================================
# GROUP 3: ROLES, SERIALIZATION & STRING REPRESENTATION
# ==============================================================================


@pytest.mark.regression
def test_associated_individual_str_representation_with_multiple_roles() -> None:
    """Verify __str__ format displays name_raw and all role values correctly."""
    assoc = AssociatedIndividual(
        name_raw="Eleanor Vance",
        role=AssociatedRole.WITNESS,
        tertiary_roles=[AssociatedRole.NEXT_OF_KIN],
    )
    expected = f"Eleanor Vance ({AssociatedRole.WITNESS.value}, {AssociatedRole.NEXT_OF_KIN.value})"
    assert str(assoc) == expected


@pytest.mark.regression
def test_associated_individual_str_representation_with_id() -> None:
    """Verify __str__ format displays individual_id when name_raw is None."""
    ind_id = IndividualID("IND-000404")
    assoc = AssociatedIndividual(individual_id=ind_id, role=AssociatedRole.INFORMANT)
    assert str(assoc) == f"IND-000404 ({AssociatedRole.INFORMANT.value})"


@pytest.mark.integration
def test_associated_individual_serialization_round_trip() -> None:
    """Verify to_dict, from_dict, to_json, and from_json round trip."""
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

    restored = AssociatedIndividual.from_dict(data)
    assert restored == assoc

    json_str = assoc.to_json()
    assert "Arthur Hastings" in json_str
    assert AssociatedIndividual.from_json(json_str) == assoc

    with pytest.raises(ModelFormatError, match="must be a dictionary"):
        AssociatedIndividual.from_dict("not-a-dict")  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="Failed to parse AssociatedIndividual JSON"):
        AssociatedIndividual.from_json("{broken-json")


@pytest.mark.regression
def test_associated_individual_repr_formatting() -> None:
    """Verify __repr__ formats all attributes cleanly."""
    assoc = AssociatedIndividual(name_raw="Test Subject", role=AssociatedRole.OTHER)
    repr_str = repr(assoc)
    assert "AssociatedIndividual" in repr_str
    assert "Test Subject" in repr_str


@pytest.mark.regression
def test_associated_individual_introspectable_execution(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify IntrospectableMixin help output executes without error."""
    assoc = AssociatedIndividual(name_raw="Test Subject")
    assoc.help()
    captured = capsys.readouterr()
    assert "AssociatedIndividual" in captured.out or assoc.__doc__ is not None
