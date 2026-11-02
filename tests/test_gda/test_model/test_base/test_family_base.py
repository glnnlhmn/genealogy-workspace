"""Path: tests/test_gda/test_model/test_base/test_family_base.py

Comprehensive test suite verifying ChildLink and FamilyUnion base value objects.

Operational Role:
    Verifies ChildLink and FamilyUnion factory instantiation, enum token normalization,
    copy-on-write mutators, date update helpers, total ordering, dictionary/JSON
    serialization round trips, defensive error handling, and frozen immutability
    with 100% statement and branch coverage.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from gda.core.errors import ModelFormatError
from gda.enums.vital import PedigreeType, UnionDissolutionType, UnionType
from gda.model.atom.date import DateString, EventDate
from gda.model.atom.id import IndividualID
from gda.model.base.family import ChildLink, FamilyUnion
from gda.model.base.time_period import TimePeriod

__version__ = "1.0.0+build.4"


# ==============================================================================
# GROUP 1: CHILDLINK BEHAVIORS, FACTORY & MUTATORS
# Note: Verification of instantiation, factory parsing, mutators, and ordering
# ==============================================================================


@pytest.mark.regression
def test_child_link_defaults_and_explicit_instantiation() -> None:
    """Verify ChildLink defaults to PedigreeType.BIRTH and accepts explicit inputs."""
    link_default = ChildLink(child_id=IndividualID("IND-000001"))
    assert link_default.child_id.value == "IND-000001"
    assert link_default.pedigree == PedigreeType.BIRTH
    assert str(link_default) == "IND-000001 (Birth)"
    assert (
        repr(link_default)
        == "ChildLink(child_id=IndividualID(value='IND-000001'), pedigree=Birth)"
    )

    link_explicit = ChildLink(
        child_id=IndividualID("IND-000002"), pedigree=PedigreeType.ADOPTED
    )
    assert link_explicit.pedigree == PedigreeType.ADOPTED
    assert str(link_explicit) == "IND-000002 (Adopted)"


@pytest.mark.regression
@pytest.mark.parametrize(
    ("raw_pedigree", "expected_enum"),
    [
        ("Birth", PedigreeType.BIRTH),
        ("BIOLOGICAL", PedigreeType.BIRTH),
        ("Adopted", PedigreeType.ADOPTED),
        ("STEP", PedigreeType.STEP),
        ("Foster", PedigreeType.FOSTER),
        ("UNKNOWN", PedigreeType.UNKNOWN),
        (PedigreeType.ADOPTED, PedigreeType.ADOPTED),
    ],
)
def test_child_link_factory_create_normalization(
    raw_pedigree: PedigreeType | str, expected_enum: PedigreeType
) -> None:
    """Verify ChildLink.create resolves strings, aliases, and enum tokens."""
    link = ChildLink.create(child_id="IND-000005", pedigree=raw_pedigree)
    assert link.child_id == IndividualID("IND-000005")
    assert link.pedigree == expected_enum


@pytest.mark.regression
def test_child_link_mutator_and_no_op() -> None:
    """Verify ChildLink.update_pedigree returns updated copy or identical instance."""
    original = ChildLink.create("IND-000010", PedigreeType.BIRTH)
    updated = original.update_pedigree("Adopted")
    assert updated is not original
    assert updated.pedigree == PedigreeType.ADOPTED
    assert updated.child_id == original.child_id

    # Idempotent no-op check
    assert updated.update_pedigree("Adopted") is updated
    assert updated.update_pedigree(PedigreeType.ADOPTED) is updated


@pytest.mark.regression
def test_child_link_total_ordering_and_comparison() -> None:
    """Verify ChildLink total ordering comparisons by child_id and pedigree."""
    c1 = ChildLink.create("IND-000001", PedigreeType.BIRTH)
    c2 = ChildLink.create("IND-000002", PedigreeType.BIRTH)
    c1_adopted = ChildLink.create("IND-000001", PedigreeType.ADOPTED)

    assert c1 < c2
    assert c1_adopted < c1
    assert c1 == ChildLink.create("IND-000001", PedigreeType.BIRTH)

    with pytest.raises(TypeError):
        _ = c1 < "IND-000001"  # type: ignore[operator]


# ==============================================================================
# GROUP 2: FAMILYUNION BEHAVIORS, FACTORY & MUTATORS
# Note: Verification of instantiation, factory parsing, mutators, and strings
# ==============================================================================


@pytest.mark.regression
def test_family_union_defaults() -> None:
    """Verify FamilyUnion minimal instantiation defaults."""
    u = FamilyUnion()
    assert u.union_type == UnionType.UNKNOWN
    assert u.dissolution_type is None
    assert u.period is None
    assert str(u) == "Type: UNKNOWN"


@pytest.mark.regression
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


@pytest.mark.regression
def test_family_union_str_with_only_dissolution() -> None:
    """Verify string rendering with dissolution but without period."""
    u = FamilyUnion(
        union_type=UnionType.INFORMAL,
        dissolution_type=UnionDissolutionType.SEPARATION,
    )
    assert str(u) == "Type: INFORMAL, Dissolved: SEPARATION"


@pytest.mark.regression
@pytest.mark.parametrize(
    ("raw_type", "expected_type"),
    [
        ("Married", UnionType.MARRIED),
        ("MARRIAGE", UnionType.MARRIED),
        ("common_law", UnionType.COMMON_LAW),
        ("civil_union", UnionType.CIVIL_UNION),
        ("INFORMAL", UnionType.INFORMAL),
        ("UNKNOWN", UnionType.UNKNOWN),
        (UnionType.CIVIL_UNION, UnionType.CIVIL_UNION),
    ],
)
def test_family_union_factory_type_normalization(
    raw_type: UnionType | str, expected_type: UnionType
) -> None:
    """Verify FamilyUnion.create normalizes union type tokens."""
    u = FamilyUnion.create(union_type=raw_type)
    assert u.union_type == expected_type


@pytest.mark.regression
@pytest.mark.parametrize(
    ("raw_dissolution", "expected_dissolution"),
    [
        ("Divorce", UnionDissolutionType.DIVORCE),
        ("DIVORCED", UnionDissolutionType.DIVORCE),
        ("annulment", UnionDissolutionType.ANNULMENT),
        ("ANNULLED", UnionDissolutionType.ANNULMENT),
        ("separation", UnionDissolutionType.SEPARATION),
        ("SEPARATED", UnionDissolutionType.SEPARATION),
        ("death", UnionDissolutionType.DEATH),
        ("desertion", UnionDissolutionType.DESERTION),
        ("unknown", UnionDissolutionType.UNKNOWN),
        (UnionDissolutionType.DIVORCE, UnionDissolutionType.DIVORCE),
        (None, None),
    ],
)
def test_family_union_factory_dissolution_normalization(
    raw_dissolution: UnionDissolutionType | str | None,
    expected_dissolution: UnionDissolutionType | None,
) -> None:
    """Verify FamilyUnion.create normalizes dissolution type tokens."""
    u = FamilyUnion.create(
        union_type=UnionType.MARRIED, dissolution_type=raw_dissolution
    )
    assert u.dissolution_type == expected_dissolution


@pytest.mark.regression
def test_family_union_copy_on_write_mutators() -> None:
    """Verify FamilyUnion mutators produce updated copies or identical instances on no-op."""
    start = EventDate(date=DateString(value="1880-01-01"))
    period = TimePeriod(start_date=start)
    original = FamilyUnion.create(UnionType.UNKNOWN)

    # update_type
    with_type = original.update_type("Married")
    assert with_type is not original
    assert with_type.union_type == UnionType.MARRIED
    assert with_type.update_type(UnionType.MARRIED) is with_type

    # update_dissolution
    with_diss = with_type.update_dissolution("Divorce")
    assert with_diss is not with_type
    assert with_diss.dissolution_type == UnionDissolutionType.DIVORCE
    assert with_diss.update_dissolution("Divorce") is with_diss
    assert with_diss.update_dissolution(UnionDissolutionType.DIVORCE) is with_diss

    # update_period
    with_period = with_diss.update_period(period)
    assert with_period is not with_diss
    assert with_period.period == period
    assert with_period.update_period(period) is with_period


@pytest.mark.regression
def test_family_union_date_update_helpers() -> None:
    """Verify update_marriage_date and update_dissolution_date convenience methods."""
    union = FamilyUnion.create(UnionType.MARRIED)
    assert union.period is None

    # Update marriage date
    with_marr = union.update_marriage_date("1880-05-12")
    assert with_marr is not union
    assert with_marr.period is not None
    assert str(with_marr.period.start_date) == "1880-05-12"
    assert with_marr.period.end_date is None

    # Update dissolution date
    with_both = with_marr.update_dissolution_date("1905-10-15")
    assert with_both is not with_marr
    assert str(with_both.period.end_date) == "1905-10-15"

    # Clear dates
    cleared_marr = with_both.update_marriage_date(None)
    assert cleared_marr.period.start_date is None
    assert str(cleared_marr.period.end_date) == "1905-10-15"

    cleared_all = cleared_marr.update_dissolution_date(None)
    assert cleared_all.period is None

    cleared_from_empty = union.update_marriage_date(None)
    assert cleared_from_empty.period is None


# ==============================================================================
# GROUP 3: SERIALIZATION & ROUND TRIPS
# Note: Verification of dictionary and JSON string payload conversions
# ==============================================================================


@pytest.mark.integration
def test_child_link_serialization_round_trip() -> None:
    """Verify ChildLink dictionary and JSON serialization round trip."""
    link = ChildLink.create("IND-000007", PedigreeType.ADOPTED)
    data = link.to_dict()
    assert data == {"child_id": "IND-000007", "pedigree": "Adopted"}

    restored = ChildLink.from_dict(data)
    assert restored == link

    json_str = link.to_json()
    assert "IND-000007" in json_str
    assert ChildLink.from_json(json_str) == link


@pytest.mark.integration
def test_family_union_serialization_round_trip() -> None:
    """Verify FamilyUnion dictionary and JSON serialization round trip."""
    start = EventDate(date=DateString(value="1880-05-10"))
    end = EventDate(date=DateString(value="1905-11-20"))
    period = TimePeriod(start_date=start, end_date=end)

    union = FamilyUnion.create(
        union_type=UnionType.MARRIED,
        dissolution_type=UnionDissolutionType.DIVORCE,
        period=period,
    )
    data = union.to_dict()
    assert data["union_type"] == "MARRIED"
    assert data["dissolution_type"] == "DIVORCE"
    assert data["period"]["start_date"] == "1880-05-10"
    assert data["period"]["end_date"] == "1905-11-20"

    restored = FamilyUnion.from_dict(data)
    assert restored.union_type == union.union_type
    assert restored.dissolution_type == union.dissolution_type
    assert restored.period is not None
    assert str(restored.period.start_date) == "1880-05-10"
    assert str(restored.period.end_date) == "1905-11-20"

    json_str = union.to_json()
    assert FamilyUnion.from_json(json_str) == union


@pytest.mark.integration
def test_family_union_to_dict_minimal_omits_none_fields() -> None:
    """Verify FamilyUnion.to_dict omits dissolution_type and period when None (lines 239, 241)."""
    minimal = FamilyUnion.create(UnionType.INFORMAL)
    data = minimal.to_dict()
    assert data == {"union_type": "INFORMAL"}
    assert "dissolution_type" not in data
    assert "period" not in data

    restored = FamilyUnion.from_dict(data)
    assert restored.union_type == UnionType.INFORMAL
    assert restored.dissolution_type is None
    assert restored.period is None


@pytest.mark.integration
def test_family_union_from_dict_with_time_period_instance() -> None:
    """Verify FamilyUnion.from_dict handles TimePeriod instance and minimal payloads."""
    period = TimePeriod(start_date=EventDate.create("1880-01-01"))
    data = {"union_type": "MARRIED", "period": period}
    restored = FamilyUnion.from_dict(data)
    assert restored.period == period

    minimal_restored = FamilyUnion.from_dict({"union_type": "INFORMAL"})
    assert minimal_restored.union_type == UnionType.INFORMAL
    assert minimal_restored.period is None
    assert minimal_restored.dissolution_type is None


# ==============================================================================
# GROUP 4: DEFENSIVE BOUNDARIES & ERROR HANDLING
# Note: Verification of invalid token rejections, format errors, and immutability
# ==============================================================================


@pytest.mark.regression
def test_child_link_defensive_errors() -> None:
    """Verify ChildLink defensive validation and error handling."""
    with pytest.raises(ModelFormatError, match="Cannot normalize"):
        ChildLink.create("IND-000001", "ALIEN_PEDIGREE")

    with pytest.raises(ModelFormatError, match="must be a dictionary"):
        ChildLink.from_dict("not-a-dict")  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="Missing required field 'child_id'"):
        ChildLink.from_dict({"pedigree": "Birth"})

    with pytest.raises(ModelFormatError, match="Failed to parse ChildLink JSON string"):
        ChildLink.from_json("{broken-json")


@pytest.mark.regression
def test_family_union_defensive_errors() -> None:
    """Verify FamilyUnion defensive validation and error handling."""
    with pytest.raises(ModelFormatError, match="Cannot normalize 'ALIEN_UNION'"):
        FamilyUnion.create(union_type="ALIEN_UNION")

    with pytest.raises(ModelFormatError, match="Cannot normalize 'ALIEN_DISSOLUTION'"):
        FamilyUnion.create(union_type="MARRIED", dissolution_type="ALIEN_DISSOLUTION")

    with pytest.raises(ModelFormatError, match="must be a dictionary"):
        FamilyUnion.from_dict("not-a-dict")  # type: ignore[arg-type]

    with pytest.raises(
        ModelFormatError, match="Failed to parse FamilyUnion JSON string"
    ):
        FamilyUnion.from_json("{broken-json")


@pytest.mark.regression
def test_family_base_immutability_and_introspection() -> None:
    """Verify ChildLink and FamilyUnion are frozen and support .help()."""
    link = ChildLink.create("IND-000001")
    with pytest.raises((FrozenInstanceError, TypeError)):
        link.pedigree = PedigreeType.ADOPTED  # type: ignore[misc]

    union = FamilyUnion.create()
    with pytest.raises((FrozenInstanceError, TypeError)):
        union.union_type = UnionType.MARRIED  # type: ignore[misc]

    help_link = link.help(as_str=True)
    assert help_link is not None
    assert "=== ChildLink Public Directory ===" in help_link
    assert "update_pedigree" in help_link

    help_union = union.help(as_str=True)
    assert help_union is not None
    assert "=== FamilyUnion Public Directory ===" in help_union
    assert "update_type" in help_union
    assert "update_marriage_date" in help_union
    assert "update_dissolution_date" in help_union
