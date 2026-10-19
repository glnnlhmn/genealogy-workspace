"""Path: tests/test_gda/test_model/test_entity/test_family.py

Comprehensive test suite verifying Family entity model contracts and invariants.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from gda.core.errors import ModelFormatError
from gda.enums.vital import PedigreeType, UnionDissolutionType, UnionType
from gda.model.atom.date import DateString, EventDate, IsoTimestamp
from gda.model.atom.id import FamilyID, IndividualID
from gda.model.base.audit import AuditStamp
from gda.model.base.family import ChildLink, FamilyUnion
from gda.model.base.time_period import TimePeriod
from gda.model.base.tombstone import TombstoneRecord
from gda.model.entity.family import Family

__version__ = "1.0.0+build.1"


# ==============================================================================
# FIXTURES
# ==============================================================================


@pytest.fixture
def valid_audit() -> AuditStamp:
    ts = IsoTimestamp(value="2026-10-18T12:00:00Z")
    return AuditStamp(created_at=ts, updated_at=ts)


@pytest.fixture
def valid_period() -> TimePeriod:
    marr = EventDate(date=DateString(value="1865-04-12"))
    div = EventDate(date=DateString(value="1880-09-01"))
    return TimePeriod(start_date=marr, end_date=div)


@pytest.fixture
def valid_family(valid_audit: AuditStamp, valid_period: TimePeriod) -> Family:
    p1 = IndividualID(value="IND-000101")
    p2 = IndividualID(value="IND-000102")
    c1 = ChildLink(
        child_id=IndividualID(value="IND-000201"), pedigree=PedigreeType.BIRTH
    )
    c2 = ChildLink(
        child_id=IndividualID(value="IND-000202"), pedigree=PedigreeType.ADOPTED
    )
    union = FamilyUnion(
        union_type=UnionType.MARRIED,
        dissolution_type=UnionDissolutionType.DIVORCE,
        period=valid_period,
    )

    return Family(
        id=FamilyID(value="FAM-000001"),
        audit=valid_audit,
        canonical_urn="urn:gda:fam:smith_jones_1865",
        union=union,
        partner_ids=[p1, p2],
        children=[c1, c2],
    )


# ==============================================================================
# GROUP 1: INITIALIZATION & BASELINE BEHAVIOR
# ==============================================================================


@pytest.mark.unit
def test_family_init_minimal_defaults(valid_audit: AuditStamp) -> None:
    """Verify minimal instantiation defaults and empty collection containers."""
    fam = Family(
        id=FamilyID(value="FAM-000010"),
        audit=valid_audit,
        canonical_urn="urn:gda:fam:single_parent_000010",
    )
    assert fam.id.value == "FAM-000010"
    assert fam.union.union_type == UnionType.UNKNOWN
    assert fam.union.dissolution_type is None
    assert fam.union.period is None
    assert fam.partner_ids == []
    assert fam.children == []
    assert fam.child_ids == []
    assert fam.partner_count == 0
    assert fam.child_count == 0
    assert fam.notes == []
    assert fam.is_deprecated is False


@pytest.mark.unit
def test_family_full_composition_properties(valid_family: Family) -> None:
    """Verify property accessors on populated family unit."""
    assert valid_family.partner_count == 2
    assert valid_family.child_count == 2
    assert valid_family.child_ids == [
        IndividualID(value="IND-000201"),
        IndividualID(value="IND-000202"),
    ]


@pytest.mark.unit
def test_family_str_representation(valid_family: Family) -> None:
    """Verify string rendering of family with partners, period, and union details."""
    expected = (
        "Family [MARRIED/DIVORCE] (1865-04-12 - 1880-09-01): "
        "Partners(IND-000101 & IND-000102), Children(2) (FAM-000001)"
    )
    assert str(valid_family) == expected


@pytest.mark.unit
def test_family_str_representation_no_partners(valid_audit: AuditStamp) -> None:
    """Verify string rendering when partner list is empty and union is default."""
    fam = Family(
        id=FamilyID(value="FAM-000011"),
        audit=valid_audit,
        canonical_urn="urn:gda:fam:orphan_nexus_000011",
    )
    assert str(fam) == "Family [UNKNOWN]: Partners(None), Children(0) (FAM-000011)"


# ==============================================================================
# GROUP 2: DEFENSIVE INVARIANTS & INTEGRITY BOUNDARIES
# ==============================================================================


@pytest.mark.regression
def test_family_invalid_id_type(valid_audit: AuditStamp) -> None:
    """Verify ValidationError when id is not an instance of FamilyID."""
    with pytest.raises(ValidationError):
        Family(
            id="FAM-000001",  # type: ignore[arg-type]
            audit=valid_audit,
            canonical_urn="urn:gda:fam:smith_000001",
        )


@pytest.mark.regression
def test_family_post_init_id_type_defensive(valid_family: Family) -> None:
    """Verify __post_init__ raises TypeError when self.id is not a FamilyID."""
    object.__setattr__(valid_family, "id", "NOT_A_FAMILY_ID")
    with pytest.raises(TypeError, match="must be an instance of FamilyID"):
        valid_family.__post_init__()


@pytest.mark.regression
def test_family_post_init_id_pattern_defensive(valid_family: Family) -> None:
    """Verify __post_init__ raises ModelFormatError when raw_id violates pattern."""

    class MalformedFamilyID(FamilyID):
        """Bypass subclass simulating invalid prefix format."""

        def __init__(self, value: str) -> None:
            object.__setattr__(self, "value", value)

    object.__setattr__(valid_family, "id", MalformedFamilyID("BAD-123"))
    with pytest.raises(ModelFormatError, match="Invalid FamilyID format"):
        valid_family.__post_init__()


@pytest.mark.regression
def test_family_invalid_urn_format(valid_audit: AuditStamp) -> None:
    """Verify ModelFormatError when canonical_urn syntax is malformed."""
    with pytest.raises(ModelFormatError, match="Invalid canonical_urn format"):
        Family(
            id=FamilyID(value="FAM-000001"),
            audit=valid_audit,
            canonical_urn="urn:gda:invalid:fam:pattern!",
        )


@pytest.mark.regression
def test_family_self_supersession_forbidden(valid_audit: AuditStamp) -> None:
    """Verify ModelFormatError when tombstone supersedes self."""
    fam_id = FamilyID(value="FAM-000001")
    tombstone = TombstoneRecord[FamilyID](
        is_deprecated=True,
        deprecated_at=IsoTimestamp.now_utc(),
        superseded_by=fam_id,
    )
    with pytest.raises(ModelFormatError, match="Family cannot be superseded by itself"):
        Family(
            id=fam_id,
            audit=valid_audit,
            canonical_urn="urn:gda:fam:smith_000001",
            tombstone=tombstone,
        )


@pytest.mark.regression
def test_family_duplicate_partner_ids(valid_audit: AuditStamp) -> None:
    """Verify ModelFormatError when partner_ids contains duplicates."""
    p1 = IndividualID(value="IND-000101")
    with pytest.raises(
        ModelFormatError, match="Duplicate entries found in partner_ids"
    ):
        Family(
            id=FamilyID(value="FAM-000001"),
            audit=valid_audit,
            canonical_urn="urn:gda:fam:smith_000001",
            partner_ids=[p1, p1],
        )


@pytest.mark.regression
def test_family_duplicate_children(valid_audit: AuditStamp) -> None:
    """Verify ModelFormatError when a child appears more than once in children."""
    c1 = ChildLink(
        child_id=IndividualID(value="IND-000201"), pedigree=PedigreeType.BIRTH
    )
    c1_dup = ChildLink(
        child_id=IndividualID(value="IND-000201"), pedigree=PedigreeType.STEP
    )

    with pytest.raises(ModelFormatError, match="Duplicate child entries found"):
        Family(
            id=FamilyID(value="FAM-000001"),
            audit=valid_audit,
            canonical_urn="urn:gda:fam:smith_000001",
            children=[c1, c1_dup],
        )


@pytest.mark.regression
def test_family_individual_cannot_be_both_partner_and_child(
    valid_audit: AuditStamp,
) -> None:
    """Verify ModelFormatError when an individual is registered as both partner and child."""
    shared_id = IndividualID(value="IND-000101")
    other_partner = IndividualID(value="IND-000102")
    c1 = ChildLink(child_id=shared_id, pedigree=PedigreeType.BIRTH)

    with pytest.raises(ModelFormatError, match="cannot be both a partner and a child"):
        Family(
            id=FamilyID(value="FAM-000001"),
            audit=valid_audit,
            canonical_urn="urn:gda:fam:smith_000001",
            partner_ids=[shared_id, other_partner],
            children=[c1],
        )
