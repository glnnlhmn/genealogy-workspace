# Name: test_family.py
# Path: tests/test_gda/test_model/test_base/test_family.py

"""Comprehensive test suite verifying BaseFamilyModel, FamilyChildModel, and family enums.

Operational Role:
    Verifies that BaseFamilyModel and FamilyChildModel enforce valid FamilyID and
    IndividualID identifiers, track partner and child collections, support UnionType
    and PedigreeLinkType classifications, bind optional union dates, and guarantee
    immutability and runtime introspection.

Test Structure & Protocol:
    - Atomized tests: 1:1 behavioral contract mapping.
    - Fully decorated: Standard 7-marker taxonomy.
    - Zero production disk I/O.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from gda.model.atom.date import DateModifier, DateString, EventDate, IsoTimestamp
from gda.model.atom.id import FamilyID, IndividualID, NoteID
from gda.model.base.audit import AuditStamp
from gda.model.base.family import (
    BaseFamilyModel,
    FamilyChildModel,
    PedigreeLinkType,
    UnionType,
)
from gda.model.base.tombstone import TombstoneRecord

__version__ = "1.0.0+build.r4"


# ==============================================================================
# GROUP 1: FAMILYCHILDMODEL CREATION & PROPERTIES
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_family_child_model_valid_creation() -> None:
    """Verify FamilyChildModel instantiates with default BIRTH pedigree and custom attributes."""
    child_id = IndividualID("IND-000010")
    child_default = FamilyChildModel(individual_id=child_id)
    assert child_default.individual_id == child_id
    assert child_default.pedigree_type == PedigreeLinkType.BIRTH
    assert child_default.notes is None

    child_custom = FamilyChildModel(
        individual_id=child_id,
        pedigree_type=PedigreeLinkType.ADOPTED,
        notes="Adopted in Merrimack County court.",
    )
    assert child_custom.pedigree_type == PedigreeLinkType.ADOPTED
    assert child_custom.notes == "Adopted in Merrimack County court."
    assert repr(child_custom) == (
        "FamilyChildModel(individual_id=IndividualID(value='IND-000010'), "
        "pedigree_type=ADOPTED, notes='Adopted in Merrimack County court.')"
    )


# ==============================================================================
# GROUP 2: BASEFAMILYMODEL CREATION & GRAPH AGGREGATION
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_base_family_model_valid_creation() -> None:
    """Verify BaseFamilyModel instantiates with partners, children, and union date."""
    fam_id = FamilyID("FAM-000001")
    t1 = IsoTimestamp("2026-10-16T12:00:00Z")
    audit = AuditStamp(created_at=t1, updated_at=t1)

    p1 = IndividualID("IND-000001")
    p2 = IndividualID("IND-000002")
    c1 = FamilyChildModel(individual_id=IndividualID("IND-000003"))
    u_date = EventDate(date=DateString("14 APR 1865"), modifier=DateModifier.EXACT)

    family = BaseFamilyModel(
        id=fam_id,
        audit=audit,
        partners=[p1, p2],
        children=[c1],
        union_type=UnionType.MARRIED,
        union_date=u_date,
    )

    assert family.id == fam_id
    assert family.audit == audit
    assert family.partners == [p1, p2]
    assert family.children == [c1]
    assert family.partner_count == 2
    assert family.child_count == 1
    assert family.union_type == UnionType.MARRIED
    assert family.union_date == u_date
    assert family.is_deprecated is False
    assert repr(family) == (
        "BaseFamilyModel(id=FamilyID(value='FAM-000001'), "
        "partners=[IndividualID(value='IND-000001'), IndividualID(value='IND-000002')], "
        "children=[FamilyChildModel(individual_id=IndividualID(value='IND-000003'), "
        "pedigree_type=BIRTH, notes=None)], union_type=MARRIED, "
        "union_date=EventDate(date=DateString(value='14 APR 1865'), modifier=EXACT), "
        "audit=AuditStamp(created_at=IsoTimestamp(value='2026-10-16T12:00:00Z'), "
        "updated_at=IsoTimestamp(value='2026-10-16T12:00:00Z')), "
        "tombstone=TombstoneRecord(is_deprecated=False), notes=[])"
    )


@pytest.mark.unit
@pytest.mark.smoke
def test_base_family_model_defaults() -> None:
    """Verify BaseFamilyModel defaults partners and children to empty lists with UNKNOWN union."""
    fam_id = FamilyID("FAM-000002")
    t1 = IsoTimestamp("2026-10-16T12:00:00Z")
    audit = AuditStamp(created_at=t1, updated_at=t1)

    family = BaseFamilyModel(id=fam_id, audit=audit)
    assert family.partners == []
    assert family.children == []
    assert family.partner_count == 0
    assert family.child_count == 0
    assert family.union_type == UnionType.UNKNOWN
    assert family.union_date is None


# ==============================================================================
# GROUP 3: DEFENSIVE BOUNDARIES & ENUMERATIONS
# ==============================================================================


@pytest.mark.unit
def test_union_type_enumeration_members() -> None:
    """Verify UnionType contains all standard partnership classifications."""
    expected = {
        "MARRIED",
        "COMMON_LAW",
        "CIVIL_UNION",
        "SEPARATED",
        "DIVORCED",
        "ANNULLED",
        "UNKNOWN",
    }
    assert {u.value for u in UnionType} == expected


@pytest.mark.unit
def test_pedigree_link_type_enumeration_members() -> None:
    """Verify PedigreeLinkType contains all standard lineage classifications."""
    expected = {"BIRTH", "ADOPTED", "FOSTER", "STEP", "GUARDIAN", "UNKNOWN"}
    assert {p.value for p in PedigreeLinkType} == expected


@pytest.mark.unit
@pytest.mark.regression
def test_base_family_superseded_by_type_mismatch_raises_type_error() -> None:
    """Verify BaseFamilyModel raises TypeError if superseded_by is not a FamilyID."""
    fam_id = FamilyID("FAM-000001")
    t1 = IsoTimestamp("2026-10-16T12:00:00Z")
    audit = AuditStamp(created_at=t1, updated_at=t1)
    wrong_id = IndividualID("IND-000002")

    tombstone = TombstoneRecord(
        is_deprecated=True,
        deprecated_at=t1,
        superseded_by=wrong_id,  # type: ignore[arg-type]
    )

    with pytest.raises(TypeError, match="superseded_by type mismatch"):
        BaseFamilyModel(id=fam_id, audit=audit, tombstone=tombstone)


# ==============================================================================
# GROUP 4: IMMUTABILITY & INTROSPECTION
# ==============================================================================


@pytest.mark.unit
def test_family_child_immutability() -> None:
    """Verify FamilyChildModel is frozen and immutable."""
    child = FamilyChildModel(individual_id=IndividualID("IND-000005"))
    with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
        child.pedigree_type = PedigreeLinkType.FOSTER  # type: ignore[misc]


@pytest.mark.unit
def test_base_family_immutability() -> None:
    """Verify BaseFamilyModel is frozen and immutable."""
    fam_id = FamilyID("FAM-000001")
    t1 = IsoTimestamp("2026-10-16T12:00:00Z")
    family = BaseFamilyModel(id=fam_id, audit=AuditStamp(created_at=t1, updated_at=t1))
    with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
        family.notes = [NoteID("NOT-000001")]  # type: ignore[misc]


@pytest.mark.unit
def test_family_models_introspection() -> None:
    """Verify .help() renders on FamilyChildModel and BaseFamilyModel."""
    child = FamilyChildModel(individual_id=IndividualID("IND-000005"))
    assert child.help(as_str=True) is not None

    family = BaseFamilyModel(
        id=FamilyID("FAM-000001"),
        audit=AuditStamp(
            created_at=IsoTimestamp("2026-10-16T12:00:00Z"),
            updated_at=IsoTimestamp("2026-10-16T12:00:00Z"),
        ),
    )
    help_text = family.help(as_str=True)
    assert help_text is not None
    assert "=== BaseFamilyModel Public Directory ===" in help_text
    assert "partner_count" in help_text
    assert "child_count" in help_text
