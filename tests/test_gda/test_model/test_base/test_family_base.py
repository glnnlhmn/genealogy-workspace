"""Path: tests/test_gda/test_model/test_base/test_family_base.py

Unit test suite verifying ChildLink and FamilyUnion base value objects.
"""

from __future__ import annotations

import pytest

from gda.enums.vital import PedigreeType, UnionDissolutionType, UnionType
from gda.model.atom.date import DateString, EventDate
from gda.model.atom.id import IndividualID
from gda.model.base.family import ChildLink, FamilyUnion
from gda.model.base.time_period import TimePeriod

__version__ = "1.0.0+build.1"


# ==============================================================================
# GROUP 1: CHILD LINK TESTS
# ==============================================================================


@pytest.mark.unit
def test_child_link_defaults() -> None:
    """Verify ChildLink minimal instantiation defaults to PedigreeType.BIRTH."""
    link = ChildLink(child_id=IndividualID(value="IND-000001"))
    assert link.child_id.value == "IND-000001"
    assert link.pedigree == PedigreeType.BIRTH
    assert str(link) == "IND-000001 (Birth)"


@pytest.mark.unit
def test_child_link_explicit_pedigree() -> None:
    """Verify ChildLink with explicit non-birth pedigree."""
    link = ChildLink(
        child_id=IndividualID(value="IND-000002"), pedigree=PedigreeType.ADOPTED
    )
    assert link.child_id.value == "IND-000002"
    assert link.pedigree == PedigreeType.ADOPTED
    assert str(link) == "IND-000002 (Adopted)"


# ==============================================================================
# GROUP 2: FAMILY UNION TESTS
# ==============================================================================


@pytest.mark.unit
def test_family_union_defaults() -> None:
    """Verify FamilyUnion minimal instantiation defaults."""
    u = FamilyUnion()
    assert u.union_type == UnionType.UNKNOWN
    assert u.dissolution_type is None
    assert u.period is None
    assert str(u) == "Type: UNKNOWN"


@pytest.mark.unit
def test_family_union_full_specification() -> None:
    """Verify FamilyUnion with full inception, dissolution, and period bounds."""
    start = EventDate(date=DateString(value="1880-05-10"))
    end = EventDate(date=DateString(value="1905-11-20"))
    period = TimePeriod(start_date=start, end_date=end)

    u = FamilyUnion(
        union_type=UnionType.MARRIED,
        dissolution_type=UnionDissolutionType.DEATH,
        period=period,
    )
    assert u.union_type == UnionType.MARRIED
    assert u.dissolution_type == UnionDissolutionType.DEATH
    assert u.period == period
    assert str(u) == "Type: MARRIED, Dissolved: DEATH, Period: 1880-05-10 - 1905-11-20"


@pytest.mark.unit
def test_family_union_str_with_only_dissolution() -> None:
    """Verify string rendering with dissolution but without period."""
    u = FamilyUnion(
        union_type=UnionType.INFORMAL,
        dissolution_type=UnionDissolutionType.SEPARATION,
    )
    assert str(u) == "Type: INFORMAL, Dissolved: SEPARATION"
