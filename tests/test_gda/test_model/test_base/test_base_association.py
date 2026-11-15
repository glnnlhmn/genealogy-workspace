"""Path: tests/test_gda/test_model/test_base/test_base_association.py

Atomized behavioral test suite for AssociatedIndividual composite.

Operational Role:
    Verifies instantiation invariants, individual_id vs name_raw resolution rules,
    controlled AssociatedRole bindings, tertiary_roles disjointness, SiteID residence
    links, strict mode boundaries, serialization, copy-on-write mutators,
    and introspection contracts with 100% statement and branch coverage.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from gda.core.enums.core import AssociatedRole
from gda.core.errors import ModelFormatError
from gda.model.atom.id import IndividualID, SiteID
from gda.model.base.association import AssociatedIndividual

__version__ = "1.0.0+build.2"


# ==============================================================================
# GROUP 1: INITIALIZATION & IDENTITY INVARIANTS
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
@pytest.mark.smoke
def test_associated_individual_init_with_individual_id_only(
    sample_individual_id: IndividualID,
) -> None:
    """Verify initialization when only individual_id is supplied without name_raw."""
    assoc = AssociatedIndividual(individual_id=sample_individual_id)
    assert assoc.individual_id == sample_individual_id
    assert assoc.name_raw is None
    assert assoc.role == AssociatedRole.OTHER
    assert assoc.tertiary_roles == []
    assert assoc.residence is None


@pytest.mark.unit
def test_associated_individual_init_with_both_id_and_name_raw(
    sample_individual_id: IndividualID,
    sample_site_id: SiteID,
) -> None:
    """Verify initialization when both individual_id and name_raw are provided."""
    assoc = AssociatedIndividual(
        individual_id=sample_individual_id,
        name_raw="Dr. Marcus Welby",
        role=AssociatedRole.PHYSICIAN,
        role_verbatim="Attending Physician",
        tertiary_roles=[AssociatedRole.WITNESS],
        residence=sample_site_id,
        comment="Signed affidavit on page 2",
    )
    assert assoc.individual_id == sample_individual_id
    assert assoc.name_raw == "Dr. Marcus Welby"
    assert assoc.role == AssociatedRole.PHYSICIAN
    assert assoc.tertiary_roles == [AssociatedRole.WITNESS]
    assert assoc.residence == sample_site_id
    assert assoc.comment == "Signed affidavit on page 2"


@pytest.mark.unit
def test_associated_individual_factory_create_and_mutators() -> None:
    """Verify factory constructor, string normalization, and copy-on-write mutators."""
    assoc = AssociatedIndividual.create(
        individual_id="IND-000101",
        role="clergy",
        tertiary_roles=["witness"],
        residence="SID-000001",
        comment="  Initial comment  ",
    )
    assert assoc.individual_id == IndividualID("IND-000101")
    assert assoc.role == AssociatedRole.CLERGY
    assert assoc.tertiary_roles == [AssociatedRole.WITNESS]
    assert assoc.residence == SiteID("SID-000001")
    assert assoc.comment == "Initial comment"

    # update_role
    up_role = assoc.update_role("informant")
    assert up_role is not assoc
    assert up_role.role == AssociatedRole.INFORMANT
    assert up_role.update_role(AssociatedRole.INFORMANT) is up_role

    with pytest.raises(ModelFormatError, match="Invalid AssociatedRole value"):
        assoc.update_role("NOT_A_ROLE")

    # update_residence
    up_res = assoc.update_residence("SID-000002")
    assert up_res is not assoc
    assert up_res.residence == SiteID("SID-000002")
    assert up_res.update_residence(SiteID("SID-000002")) is up_res
    assert up_res.update_residence(None).residence is None

    # update_comment
    up_com = assoc.update_comment("  Updated note  ")
    assert up_com is not assoc
    assert up_com.comment == "Updated note"
    assert up_com.update_comment("Updated note") is up_com
    assert up_com.update_comment("   ").comment is None


# ==============================================================================
# GROUP 2: BOUNDARY, STRICT MODE & ROLE DISJOINTNESS VALIDATION
# ==============================================================================


@pytest.mark.unit
@pytest.mark.regression
def test_associated_individual_missing_both_identifiers_fails() -> None:
    """Verify ModelFormatError is raised when neither individual_id nor name_raw is supplied."""
    with pytest.raises(ModelFormatError, match="requires either a valid 'individual_id'"):
        AssociatedIndividual()


@pytest.mark.unit
@pytest.mark.regression
def test_associated_individual_empty_name_raw_without_id_fails() -> None:
    """Verify ModelFormatError is raised when name_raw is empty whitespace and no ID is provided."""
    with pytest.raises(ModelFormatError, match="requires either a valid 'individual_id'"):
        AssociatedIndividual(name_raw=" ")


@pytest.mark.unit
@pytest.mark.regression
def test_associated_individual_empty_name_raw_with_id_succeeds(
    sample_individual_id: IndividualID,
) -> None:
    """Verify empty name_raw is permitted when a valid individual_id is supplied."""
    assoc = AssociatedIndividual(individual_id=sample_individual_id, name_raw="")
    assert assoc.individual_id == sample_individual_id


@pytest.mark.unit
@pytest.mark.regression
def test_associated_individual_strict_and_invalid_role_errors() -> None:
    """Verify strict=True rejects raw strings on direct init and .create() rejects invalid roles."""
    with pytest.raises(ValidationError):
        AssociatedIndividual(individual_id="IND-000101")  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="Invalid AssociatedRole value"):
        AssociatedIndividual.create(name_raw="John Doe", role="INVALID_ROLE")


@pytest.mark.unit
@pytest.mark.regression
def test_associated_individual_primary_role_in_tertiary_roles_fails() -> None:
    """Verify ModelFormatError is raised when primary role is duplicated in tertiary_roles."""
    with pytest.raises(ModelFormatError, match="cannot be duplicated in tertiary_roles"):
        AssociatedIndividual(
            name_raw="John Doe",
            role=AssociatedRole.EMPLOYER,
            tertiary_roles=[AssociatedRole.EMPLOYER],
        )


@pytest.mark.unit
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


@pytest.mark.unit
def test_associated_individual_str_and_repr_formatting(
    sample_individual_id: IndividualID,
) -> None:
    """Verify __str__ and __repr__ format names, IDs, and roles accurately."""
    assoc_name = AssociatedIndividual(
        name_raw="Eleanor Vance",
        role=AssociatedRole.WITNESS,
        tertiary_roles=[AssociatedRole.NEXT_OF_KIN],
    )
    expected = f"Eleanor Vance ({AssociatedRole.WITNESS.value}, {AssociatedRole.NEXT_OF_KIN.value})"
    assert str(assoc_name) == expected

    assoc_id = AssociatedIndividual(
        individual_id=sample_individual_id, role=AssociatedRole.INFORMANT
    )
    assert str(assoc_id) == f"IND-000101 ({AssociatedRole.INFORMANT.value})"

    repr_str = repr(assoc_name)
    assert repr_str.startswith(f"AssociatedIndividual(role={AssociatedRole.WITNESS}")
    assert "Eleanor Vance" in repr_str


@pytest.mark.unit
def test_associated_individual_serialization_round_trip(
    sample_individual_id: IndividualID,
    sample_site_id: SiteID,
) -> None:
    """Verify to_dict, from_dict, to_json, and from_json round-trip fidelity."""
    assoc = AssociatedIndividual(
        individual_id=sample_individual_id,
        name_raw="Arthur Hastings",
        role=AssociatedRole.OTHER,
        role_verbatim="Companion",
        tertiary_roles=[AssociatedRole.WITNESS],
        residence=sample_site_id,
        comment="Traveled together",
    )
    data = assoc.to_dict()
    assert data == {
        "role": AssociatedRole.OTHER.value,
        "individual_id": "IND-000101",
        "name_raw": "Arthur Hastings",
        "role_verbatim": "Companion",
        "tertiary_roles": [AssociatedRole.WITNESS.value],
        "residence": "SID-000888",
        "comment": "Traveled together",
    }

    assert AssociatedIndividual.from_dict(data) == assoc

    json_str = assoc.to_json()
    assert AssociatedIndividual.from_json(json_str) == assoc

    with pytest.raises(ModelFormatError, match="must be a dictionary"):
        AssociatedIndividual.from_dict("not-a-dict")  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="Failed to parse AssociatedIndividual JSON"):
        AssociatedIndividual.from_json("{broken-json")


@pytest.mark.unit
def test_associated_individual_introspectable_execution() -> None:
    """Verify IntrospectableMixin .help() executes cleanly."""
    assoc = AssociatedIndividual(name_raw="Test Subject")
    help_text = assoc.help(as_str=True)
    assert help_text is not None
    assert "=== AssociatedIndividual Public Directory ===" in help_text
