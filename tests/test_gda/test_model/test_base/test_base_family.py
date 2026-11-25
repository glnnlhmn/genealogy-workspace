"""Path: tests/test_gda/test_model/test_base/test_base_family.py

Comprehensive test suite verifying ChildLink and FamilyUnion composites.

Operational Role:
    Verifies pedigree normalization, ChildLink total ordering and mutators,
    FamilyUnion inception/dissolution/date mutators, strict validation, and
    JSON/dict serialization round-trips with 100% statement and branch coverage.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from gda.core.enums.vital import PedigreeType, UnionDissolutionType, UnionType
from gda.core.errors import ModelFormatError
from gda.model.atom.id import IndividualID
from gda.model.base.date import EventDate, TimePeriod
from gda.model.base.family import ChildLink, FamilyUnion

__version__ = "1.0.0+build.3"


# ==============================================================================
# GROUP 1: CHILDLINK CREATION, ORDERING, MUTATORS & SERIALIZATION
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_child_link_creation_ordering_and_mutators(sample_individual_id: IndividualID) -> None:
    """Verify ChildLink instantiation, total ordering, mutators, and strict mode."""
    c1 = ChildLink.create("IND-000101", pedigree="biological")
    c2 = ChildLink.create(sample_individual_id, pedigree=PedigreeType.ADOPTED)
    c3 = ChildLink.create("IND-000202", pedigree=PedigreeType.STEP)

    assert c1.child_id == sample_individual_id
    assert c1.pedigree == PedigreeType.BIRTH
    assert str(c1) == "IND-000101 (BIRTH)"
    assert "ChildLink(" in repr(c1)

    # Total ordering by child_id then pedigree.value
    assert sorted([c3, c1, c2]) == [c2, c1, c3]
    with pytest.raises(TypeError):
        _ = c1 < "not-a-child-link"  # type: ignore[operator]

    # update_pedigree
    updated = c1.update_pedigree("foster")
    assert updated is not c1
    assert updated.pedigree == PedigreeType.FOSTER
    assert updated.update_pedigree(PedigreeType.FOSTER) is updated

    with pytest.raises(ModelFormatError, match="Cannot normalize"):
        ChildLink.create("IND-000101", pedigree="INVALID")
    with pytest.raises(ModelFormatError, match="Invalid PedigreeType type"):
        ChildLink.create("IND-000101", pedigree=123)  # type: ignore[arg-type]
    with pytest.raises(ValidationError):
        ChildLink(child_id="IND-000101")  # type: ignore[arg-type]


@pytest.mark.unit
def test_child_link_serialization_round_trip(sample_individual_id: IndividualID) -> None:
    """Verify ChildLink to_dict, from_dict, to_json, and from_json round-trip fidelity."""
    link = ChildLink.create("IND-000101", pedigree="adopted")
    payload = link.to_dict()
    assert payload == {"child_id": "IND-000101", "pedigree": "ADOPTED"}
    assert ChildLink.from_dict(payload) == link
    assert ChildLink.from_dict({"child_id": sample_individual_id}).child_id == sample_individual_id
    assert ChildLink.from_json(link.to_json()) == link

    with pytest.raises(ModelFormatError, match="ChildLink payload must be a dictionary"):
        ChildLink.from_dict("bad")  # type: ignore[arg-type]
    with pytest.raises(ModelFormatError, match="Missing required field 'child_id'"):
        ChildLink.from_dict({"pedigree": "BIRTH"})
    with pytest.raises(ModelFormatError, match="Failed to parse ChildLink JSON"):
        ChildLink.from_json("{bad-json")


# ==============================================================================
# GROUP 2: FAMILYUNION CREATION, MUTATORS & SERIALIZATION
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_family_union_creation_mutators_and_dates(golden_time_period: TimePeriod) -> None:
    """Verify FamilyUnion factory, mutators, marriage/dissolution dates, and validation."""
    union = FamilyUnion.create(
        union_type=UnionType.MARRIED,
        dissolution_type=UnionDissolutionType.DIVORCE,
        period=golden_time_period,
    )
    assert union.union_type == UnionType.MARRIED
    assert union.dissolution_type == UnionDissolutionType.DIVORCE
    assert "Type: MARRIED" in str(union)
    assert "Dissolved: DIVORCE" in str(union)
    assert "Period: 1751 - 1810" in str(union)
    assert "FamilyUnion(" in repr(union)

    # Minimal union without dissolution_type or period
    blank = FamilyUnion()
    assert str(blank) == "Type: UNKNOWN"
    assert blank.update_period(None) is blank

    # update_type & update_dissolution
    up_type = union.update_type("civil_union")
    assert up_type.union_type == UnionType.CIVIL_UNION
    assert up_type.update_type(UnionType.CIVIL_UNION) is up_type

    up_diss = up_type.update_dissolution("separation")
    assert up_diss.dissolution_type == UnionDissolutionType.SEPARATION
    cleared_diss = up_diss.update_dissolution(None)
    assert cleared_diss.dissolution_type is None
    assert cleared_diss.update_dissolution(None) is cleared_diss

    # update_marriage_date & update_dissolution_date
    with_m = blank.update_marriage_date("1880-06-15")
    assert with_m.period is not None
    assert with_m.period.start_date == EventDate.create("1880-06-15")

    with_both = with_m.update_dissolution_date("1910-03-01")
    assert with_both.period is not None
    assert with_both.period.is_bounded is True

    cleared_end = with_both.update_dissolution_date(None)
    assert cleared_end.period is not None
    assert cleared_end.period.end_date is None

    cleared_all = cleared_end.update_marriage_date(None)
    assert cleared_all.period is None

    cleared_from_end_only = blank.update_dissolution_date("1900").update_dissolution_date(None)
    assert cleared_from_end_only.period is None

    with pytest.raises(ModelFormatError, match="Cannot normalize"):
        FamilyUnion.create(union_type="BAD_UNION")
    with pytest.raises(ModelFormatError, match="Invalid UnionType type"):
        FamilyUnion.create(union_type=123)  # type: ignore[arg-type]
    with pytest.raises(ModelFormatError, match="Cannot normalize"):
        FamilyUnion.create(dissolution_type="BAD_DISSOLUTION")
    with pytest.raises(ModelFormatError, match="Invalid UnionDissolutionType type"):
        FamilyUnion.create(dissolution_type=123)  # type: ignore[arg-type]


@pytest.mark.unit
def test_family_union_serialization_round_trip(golden_time_period: TimePeriod) -> None:
    """Verify FamilyUnion to_dict, from_dict, to_json, and from_json round-trip fidelity."""
    minimal = FamilyUnion()
    assert minimal.to_dict() == {"union_type": "UNKNOWN"}
    assert FamilyUnion.from_dict(minimal.to_dict()) == minimal

    union = FamilyUnion.create(
        union_type="married",
        dissolution_type="death",
        period=golden_time_period,
    )
    payload = union.to_dict()
    assert payload == {
        "union_type": "MARRIED",
        "dissolution_type": "DEATH",
        "period": {
            "start_date": {"date": "1751", "modifier": "EXACT"},
            "end_date": {"date": "1810", "modifier": "EXACT"},
        },
    }
    assert FamilyUnion.from_dict(payload) == union
    assert (
        FamilyUnion.from_dict({"union_type": "INFORMAL", "period": golden_time_period}).period
        == golden_time_period
    )
    assert FamilyUnion.from_json(union.to_json()) == union

    with pytest.raises(ModelFormatError, match="FamilyUnion payload must be a dictionary"):
        FamilyUnion.from_dict("bad")  # type: ignore[arg-type]
    with pytest.raises(ModelFormatError, match="Failed to parse FamilyUnion JSON"):
        FamilyUnion.from_json("{bad-json")
