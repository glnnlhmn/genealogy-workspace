"""Path: tests/test_gda/test_model/test_entity/test_family.py

Comprehensive test suite verifying Family entity model contracts and mutators.

Operational Role:
    Verifies Family behavioral contracts, BaseEntity inheritance, partner count constraints,
    generational recursion checks, ChildLink management, FamilyUnion lifecycle mutators,
    embedded note operations, dictionary/JSON serialization round trips, dirty tracking
    (_dirty, is_dirty, mark_clean, mark_dirty), and immutability invariants with 100%
    statement and branch coverage.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest
from pydantic import ValidationError

from gda.core.errors import ModelFormatError
from gda.enums.archival import NoteType
from gda.enums.vital import PedigreeType, UnionDissolutionType, UnionType
from gda.model.atom.date import DateString, EventDate, IsoTimestamp
from gda.model.atom.id import FactID, FamilyID, IndividualID
from gda.model.base.audit import AuditStamp
from gda.model.base.family import ChildLink, FamilyUnion
from gda.model.base.time_period import TimePeriod
from gda.model.base.tombstone import Tombstone
from gda.model.entity.family import Family

__version__ = "1.0.0+build.5"


# ==============================================================================
# FIXTURES
# ==============================================================================


@pytest.fixture
def valid_audit() -> AuditStamp:
    """Fixture providing a standard test audit stamp."""
    ts = IsoTimestamp(value="2026-10-18T12:00:00Z")
    return AuditStamp(created_at=ts, updated_at=ts)


@pytest.fixture
def valid_period() -> TimePeriod:
    """Fixture providing a standard bounded temporal interval for marriage."""
    marr = EventDate(date=DateString(value="1865-04-12"))
    div = EventDate(date=DateString(value="1880-09-01"))
    return TimePeriod(start_date=marr, end_date=div)


@pytest.fixture
def valid_family(valid_audit: AuditStamp, valid_period: TimePeriod) -> Family:
    """Fixture providing a complete standard Family instance."""
    p1 = IndividualID(value="IND-000101")
    p2 = IndividualID(value="IND-000102")
    c1 = ChildLink(child_id=IndividualID(value="IND-000201"), pedigree=PedigreeType.BIRTH)
    c2 = ChildLink(child_id=IndividualID(value="IND-000202"), pedigree=PedigreeType.ADOPTED)
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
# Note: Verification of minimal, complete, factory creation, and string representations
# ==============================================================================


@pytest.mark.regression
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
    assert fam.is_dirty is False
    assert fam.marriage_date is None
    assert fam.dissolution_date is None
    assert fam.marriage_year is None


@pytest.mark.regression
def test_family_full_composition_properties(valid_family: Family) -> None:
    """Verify property accessors on populated family unit."""
    assert valid_family.partner_count == 2
    assert valid_family.child_count == 2
    assert valid_family.child_ids == [
        IndividualID(value="IND-000201"),
        IndividualID(value="IND-000202"),
    ]
    assert valid_family.union_type == UnionType.MARRIED
    assert valid_family.dissolution_type == UnionDissolutionType.DIVORCE
    assert valid_family.period is not None
    assert valid_family.marriage_year == 1865
    assert valid_family.sort_key == ("IND-000101", "IND-000102", 1865, "FAM-000001")


@pytest.mark.regression
def test_family_factory_create_and_defaults(valid_audit: AuditStamp) -> None:
    """Verify Family.create resolves string IDs, child tuples/dicts, and union dicts."""
    fam = Family.create(
        family_id="FAM-000050",
        canonical_urn="urn:gda:fam:factory_nexus",
        partner_ids=["IND-000010", "IND-000020"],
        children=[
            ("IND-000030", "Birth"),
            {"child_id": "IND-000040", "pedigree": "Adopted"},
            ChildLink.create("IND-000050", PedigreeType.FOSTER),
        ],
        union={"union_type": "MARRIED", "dissolution_type": "DEATH"},
        audit=valid_audit,
    )
    assert fam.id == FamilyID("FAM-000050")
    assert fam.partner_count == 2
    assert fam.child_count == 3
    assert fam.children[0].pedigree == PedigreeType.BIRTH
    assert fam.children[1].pedigree == PedigreeType.ADOPTED
    assert fam.children[2].pedigree == PedigreeType.FOSTER
    assert fam.union_type == UnionType.MARRIED
    assert fam.dissolution_type == UnionDissolutionType.DEATH
    assert fam.is_dirty is False

    # Minimal factory create defaults audit
    min_fam = Family.create(
        family_id="FAM-000051",
        canonical_urn="urn:gda:fam:minimal_nexus",
    )
    assert min_fam.audit is not None
    assert min_fam.created_at is not None
    assert min_fam.partner_ids == []
    assert min_fam.children == []


@pytest.mark.regression
def test_family_str_representation(valid_family: Family) -> None:
    """Verify string rendering of family with partners, period, and union details."""
    expected = (
        "Family [MARRIED/DIVORCE] (1865-04-12 - 1880-09-01): "
        "Partners(IND-000101 & IND-000102), Children(2) (FAM-000001)"
    )
    assert str(valid_family) == expected


@pytest.mark.regression
def test_family_str_representation_no_partners(valid_audit: AuditStamp) -> None:
    """Verify string rendering when partner list is empty and union is default."""
    fam = Family(
        id=FamilyID(value="FAM-000011"),
        audit=valid_audit,
        canonical_urn="urn:gda:fam:orphan_nexus_000011",
    )
    assert str(fam) == "Family [UNKNOWN]: Partners(None), Children(0) (FAM-000011)"


# ==============================================================================
# GROUP 2: COPY-ON-WRITE MUTATORS & STATE MANAGEMENT
# Note: Verification of partner, child, union mutators and dirty tracking
# ==============================================================================


@pytest.mark.regression
def test_family_dirty_flag_transitions(valid_family: Family) -> None:
    """Verify mark_dirty and mark_clean state transitions and idempotency."""
    fam = valid_family
    assert fam.is_dirty is False

    marked_dirty = fam.mark_dirty()
    assert marked_dirty is not fam
    assert marked_dirty.is_dirty is True
    assert marked_dirty.mark_dirty() is marked_dirty

    marked_clean = marked_dirty.mark_clean()
    assert marked_clean is not marked_dirty
    assert marked_clean.is_dirty is False
    assert marked_clean.mark_clean() is marked_clean


@pytest.mark.regression
def test_family_partner_mutators(valid_audit: AuditStamp) -> None:
    """Verify add_partner and remove_partner copy-on-write mutators and invariants."""
    fam = Family.create(
        family_id="FAM-000012",
        canonical_urn="urn:gda:fam:test_partners",
        audit=valid_audit,
    )
    assert fam.partner_count == 0

    # add_partner
    with_p1 = fam.add_partner("IND-000001")
    assert with_p1 is not fam
    assert with_p1.partner_ids == [IndividualID("IND-000001")]
    assert with_p1.is_dirty is True
    assert with_p1.add_partner("IND-000001") is with_p1  # idempotent no-op

    with_p2 = with_p1.add_partner(IndividualID("IND-000002"))
    assert with_p2.partner_count == 2

    # Cannot exceed 2 partners
    with pytest.raises(ModelFormatError, match="cannot exceed 2 partners"):
        with_p2.add_partner("IND-000003")

    # remove_partner
    rem_p1 = with_p2.remove_partner("IND-000001")
    assert rem_p1 is not with_p2
    assert rem_p1.partner_ids == [IndividualID("IND-000002")]
    assert rem_p1.remove_partner("IND-999999") is rem_p1  # idempotent no-op


@pytest.mark.regression
def test_family_child_mutators(valid_family: Family) -> None:
    """Verify add_child, remove_child, and update_child_pedigree mutators."""
    fam = valid_family
    assert fam.child_count == 2

    # add_child
    with_c3 = fam.add_child("IND-000203", PedigreeType.FOSTER)
    assert with_c3 is not fam
    assert with_c3.child_count == 3
    assert with_c3.children[-1].pedigree == PedigreeType.FOSTER
    assert with_c3.is_dirty is True
    assert with_c3.add_child("IND-000203", PedigreeType.FOSTER) is with_c3  # idempotent no-op

    # Error adding duplicate child ID with different pedigree
    with pytest.raises(ModelFormatError, match="already registered with a different pedigree"):
        with_c3.add_child("IND-000203", PedigreeType.STEP)

    # update_child_pedigree
    up_ped = with_c3.update_child_pedigree("IND-000203", "Step")
    assert up_ped is not with_c3
    assert up_ped.children[-1].pedigree == PedigreeType.STEP
    assert up_ped.update_child_pedigree("IND-000203", "Step") is up_ped  # idempotent no-op

    with pytest.raises(ModelFormatError, match="not found in family children"):
        with_c3.update_child_pedigree("IND-999999", "Step")

    # remove_child
    rem_c1 = with_c3.remove_child("IND-000201")
    assert rem_c1 is not with_c3
    assert rem_c1.child_count == 2
    assert rem_c1.remove_child("IND-999999") is rem_c1  # idempotent no-op


@pytest.mark.regression
def test_family_union_mutators(valid_family: Family) -> None:
    """Verify union state and date copy-on-write mutators."""
    fam = valid_family
    assert fam.union_type == UnionType.MARRIED

    # update_union_type
    with_type = fam.update_union_type("Civil_Union")
    assert with_type is not fam
    assert with_type.union_type == UnionType.CIVIL_UNION
    assert with_type.is_dirty is True
    assert with_type.update_union_type(UnionType.CIVIL_UNION) is with_type

    # update_dissolution
    with_diss = fam.update_dissolution("Annulment")
    assert with_diss is not fam
    assert with_diss.dissolution_type == UnionDissolutionType.ANNULMENT
    assert with_diss.update_dissolution(UnionDissolutionType.ANNULMENT) is with_diss

    # update_period
    new_period = TimePeriod(start_date=EventDate.create("1870-01-01"))
    with_period = fam.update_period(new_period)
    assert with_period is not fam
    assert with_period.period == new_period
    assert with_period.update_period(new_period) is with_period

    # update_marriage_date
    with_marr = fam.update_marriage_date("1866-06-01")
    assert with_marr is not fam
    assert str(with_marr.marriage_date) == "1866-06-01"
    assert with_marr.update_marriage_date(with_marr.marriage_date) is with_marr

    # update_dissolution_date
    with_diss_date = with_marr.update_dissolution_date("1885-12-31")
    assert with_diss_date is not with_marr
    assert str(with_diss_date.dissolution_date) == "1885-12-31"
    assert with_diss_date.update_dissolution_date(with_diss_date.dissolution_date) is with_diss_date

    # update_union whole object
    new_union = FamilyUnion.create(UnionType.INFORMAL)
    with_whole = fam.update_union(new_union)
    assert with_whole is not fam
    assert with_whole.union == new_union
    assert with_whole.update_union(new_union) is with_whole

    # update_urn
    with_urn = fam.update_urn("urn:gda:fam:updated_urn")
    assert with_urn is not fam
    assert with_urn.canonical_urn == "urn:gda:fam:updated_urn"

    with pytest.raises(ModelFormatError, match="Invalid canonical_urn format"):
        fam.update_urn("invalid_urn")


@pytest.mark.regression
def test_family_update_embedded_note_multi_and_partial(valid_family: Family) -> None:
    """Verify Family update_note modifies specific note and preserves others."""
    fam = valid_family.add_note(
        text="First note text.",
        title="Note 1",
        note_type=NoteType.GENERAL,
        tags=["tag1"],
    ).add_note(
        text="Second note text.",
        title="Note 2",
        note_type=NoteType.RESEARCH,
        tags=["tag2"],
    )
    assert fam.note_count == 2
    note1_id = fam.notes[0].note_id
    note2_id = fam.notes[1].note_id

    # Update note 2 only; note 1 is appended via the 'else' branch
    updated = fam.update_note(
        note_id=note2_id,
        text="Updated second text",
        title="Updated Note 2",
        note_type=NoteType.PROOF,
        tags=["verified"],
    )
    assert updated is not fam
    assert updated.notes[0].text == "First note text."
    assert updated.notes[1].text == "Updated second text"
    assert updated.notes[1].title == "Updated Note 2"
    assert updated.notes[1].note_type == NoteType.PROOF
    assert updated.notes[1].tags == ["verified"]

    # Partial updates: text only
    up_text = fam.update_note(note_id=note1_id, text="Only text")
    assert up_text.get_note(note1_id).text == "Only text"
    assert up_text.get_note(note1_id).title == "Note 1"

    # Partial updates: title only
    up_title = fam.update_note(note_id=note1_id, title="Only title")
    assert up_title.get_note(note1_id).title == "Only title"

    # Partial updates: type only
    up_type = fam.update_note(note_id=note1_id, note_type=NoteType.DISCREPANCY)
    assert up_type.get_note(note1_id).note_type == NoteType.DISCREPANCY

    # Partial updates: tags only
    up_tags = fam.update_note(note_id=note1_id, tags=["new_tag"])
    assert up_tags.get_note(note1_id).tags == ["new_tag"]

    # No-op when note_id absent
    assert fam.update_note("NOT-999999", text="No-op") is fam


# ==============================================================================
# GROUP 3: SERIALIZATION & ROUND TRIPS
# Note: Verification of dictionary and JSON string payload conversions
# ==============================================================================


@pytest.mark.integration
def test_family_serialization_round_trip(valid_family: Family) -> None:
    """Verify Family dictionary and JSON serialization round trip."""
    fam_with_notes = valid_family.add_note(
        text="Census family unit.", title="1870 Census", note_type=NoteType.RESEARCH
    )
    data = fam_with_notes.to_dict()

    assert data["id"] == "FAM-000001"
    assert data["canonical_urn"] == "urn:gda:fam:smith_jones_1865"
    assert data["partner_ids"] == ["IND-000101", "IND-000102"]
    assert len(data["children"]) == 2
    assert data["union"]["union_type"] == "MARRIED"
    assert data["union"]["dissolution_type"] == "DIVORCE"
    assert len(data["notes"]) == 1

    restored = Family.from_dict(data)
    assert restored.id == fam_with_notes.id
    assert restored.canonical_urn == fam_with_notes.canonical_urn
    assert restored.partner_ids == fam_with_notes.partner_ids
    assert restored.children == fam_with_notes.children
    assert restored.union_type == fam_with_notes.union_type
    assert restored.dissolution_type == fam_with_notes.dissolution_type
    assert restored.period == fam_with_notes.period
    assert restored.note_count == 1

    json_str = fam_with_notes.to_json()
    assert "FAM-000001" in json_str
    assert "smith_jones_1865" in json_str

    restored_json = Family.from_json(json_str)
    assert restored_json.id == fam_with_notes.id
    assert restored_json.canonical_urn == fam_with_notes.canonical_urn


@pytest.mark.integration
def test_family_from_dict_minimal_and_tombstone_variants() -> None:
    """Verify Family.from_dict parses tombstone with and without superseded_by."""
    # Superseded by populated
    data_superseded = {
        "id": "FAM-000099",
        "canonical_urn": "urn:gda:fam:deprecated_fam",
        "tombstone": {
            "is_deprecated": True,
            "deprecated_at": "2026-10-30T10:00:00Z",
            "superseded_by": "FAM-000100",
        },
    }
    restored_sup = Family.from_dict(data_superseded)
    assert restored_sup.id == FamilyID("FAM-000099")
    assert restored_sup.is_deprecated is True
    assert restored_sup.superseded_by == FamilyID("FAM-000100")

    # Superseded by omitted / None
    data_no_sup = {
        "id": "FAM-000098",
        "canonical_urn": "urn:gda:fam:deprecated_no_sup",
        "tombstone": {
            "is_deprecated": True,
            "deprecated_at": "2026-10-30T10:00:00Z",
        },
    }
    restored_no_sup = Family.from_dict(data_no_sup)
    assert restored_no_sup.is_deprecated is True
    assert restored_no_sup.superseded_by is None


@pytest.mark.integration
def test_family_from_dict_without_tombstone_or_audit() -> None:
    """Verify Family.from_dict parses payload when tombstone and audit are completely omitted."""
    data = {
        "id": "FAM-000097",
        "canonical_urn": "urn:gda:fam:no_tombstone_or_audit",
    }
    restored = Family.from_dict(data)
    assert restored.id == FamilyID("FAM-000097")
    assert restored.canonical_urn == "urn:gda:fam:no_tombstone_or_audit"
    assert restored.is_deprecated is False
    assert restored.audit is not None


@pytest.mark.regression
def test_family_deserialization_defensive_errors() -> None:
    """Verify Family deserialization defensive validation."""
    with pytest.raises(ModelFormatError, match="must be a dictionary"):
        Family.from_dict("not-a-dict")  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="Missing required field 'id'"):
        Family.from_dict({"canonical_urn": "urn:gda:fam:no_id"})

    with pytest.raises(ModelFormatError, match="Failed to parse Family JSON string"):
        Family.from_json("{broken json")

    with pytest.raises(TypeError, match="Cannot resolve child link from payload"):
        Family.create(
            family_id="FAM-000001",
            canonical_urn="urn:gda:fam:bad_child",
            children=[12345],  # type: ignore[list-item]
        )


# ==============================================================================
# GROUP 4: DEFENSIVE BOUNDARIES & INTEGRITY INVARIANTS
# Note: Verification of ID validation, URN pattern, and relational bounds
# ==============================================================================


@pytest.mark.regression
def test_family_invalid_id_type(valid_audit: AuditStamp) -> None:
    """Verify ValidationError when id is not an instance of FamilyID."""
    with pytest.raises((ValidationError, TypeError)):
        Family(
            id="FAM-000001",  # type: ignore[arg-type]
            audit=valid_audit,
            canonical_urn="urn:gda:fam:smith_000001",
        )


@pytest.mark.regression
def test_family_conflicting_atom_id_type_raises_error(valid_audit: AuditStamp) -> None:
    """Verify Family rejects foreign AtomID subclasses assigned to id."""
    wrong_id = FactID("FID-000001")
    with pytest.raises((TypeError, ValidationError)):
        Family(
            id=wrong_id,  # type: ignore[arg-type]
            audit=valid_audit,
            canonical_urn="urn:gda:fam:smith_wrong_id",
        )


@pytest.mark.regression
def test_family_post_init_id_pattern_defensive(valid_family: Family) -> None:
    """Verify __post_init__ raises ModelFormatError when raw_id violates pattern."""

    class MalformedFamilyID(FamilyID):
        """Bypass subclass simulating invalid prefix format."""

        def __init__(self, value: str) -> None:
            object.__setattr__(self, "value", value)
            object.__setattr__(self, "expected_prefix", "FAM")

    object.__setattr__(valid_family, "id", MalformedFamilyID("BAD-123"))
    with pytest.raises(ModelFormatError, match="Invalid FamilyID format"):
        valid_family.__post_init__()


@pytest.mark.regression
@pytest.mark.parametrize(
    "invalid_urn",
    [
        "",
        "   ",
        "urn:gda:ind:smith_john",
        "urn:fam:smith_jones",
        "URN:GDA:FAM:SMITH",
        "urn:gda:fam:invalid space",
    ],
)
def test_family_invalid_urn_format(invalid_urn: str, valid_audit: AuditStamp) -> None:
    """Verify ModelFormatError when canonical_urn syntax is malformed."""
    with pytest.raises(ModelFormatError, match="Invalid canonical_urn format"):
        Family(
            id=FamilyID(value="FAM-000001"),
            audit=valid_audit,
            canonical_urn=invalid_urn,
        )


@pytest.mark.regression
def test_family_self_supersession_forbidden(valid_audit: AuditStamp) -> None:
    """Verify ModelFormatError when tombstone supersedes self."""
    fam_id = FamilyID(value="FAM-000001")
    tombstone = Tombstone[FamilyID](
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
def test_family_superseded_by_other_allowed(valid_audit: AuditStamp) -> None:
    """Verify tombstone with valid superseded_by does not raise error."""
    fam_id = FamilyID(value="FAM-000001")
    other_id = FamilyID(value="FAM-000002")
    tombstone = Tombstone[FamilyID](
        is_deprecated=True,
        deprecated_at=IsoTimestamp.now_utc(),
        superseded_by=other_id,
    )
    fam = Family(
        id=fam_id,
        audit=valid_audit,
        canonical_urn="urn:gda:fam:smith_000001",
        tombstone=tombstone,
    )
    assert fam.is_deprecated is True
    assert fam.superseded_by == other_id


@pytest.mark.regression
def test_family_duplicate_partner_ids(valid_audit: AuditStamp) -> None:
    """Verify ModelFormatError when partner_ids contains duplicates."""
    p1 = IndividualID(value="IND-000101")
    with pytest.raises(ModelFormatError, match="Duplicate entries found in partner_ids"):
        Family(
            id=FamilyID(value="FAM-000001"),
            audit=valid_audit,
            canonical_urn="urn:gda:fam:smith_000001",
            partner_ids=[p1, p1],
        )


@pytest.mark.regression
def test_family_partner_count_exceeds_two_in_constructor(
    valid_audit: AuditStamp,
) -> None:
    """Verify ModelFormatError when partner_ids exceeds 2 in direct constructor."""
    p1 = IndividualID("IND-000101")
    p2 = IndividualID("IND-000102")
    p3 = IndividualID("IND-000103")
    with pytest.raises(ModelFormatError, match="cannot exceed 2 partners"):
        Family(
            id=FamilyID("FAM-000001"),
            audit=valid_audit,
            canonical_urn="urn:gda:fam:smith_000001",
            partner_ids=[p1, p2, p3],
        )


@pytest.mark.regression
def test_family_duplicate_children(valid_audit: AuditStamp) -> None:
    """Verify ModelFormatError when a child appears more than once in children."""
    c1 = ChildLink(child_id=IndividualID(value="IND-000201"), pedigree=PedigreeType.BIRTH)
    c1_dup = ChildLink(child_id=IndividualID(value="IND-000201"), pedigree=PedigreeType.STEP)

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

    # Mutator boundaries
    fam = Family.create(
        family_id="FAM-000002",
        canonical_urn="urn:gda:fam:cycle_nexus",
        partner_ids=[shared_id],
        audit=valid_audit,
    )
    with pytest.raises(ModelFormatError, match="cannot be both a partner and a child"):
        fam.add_child(shared_id)

    fam_child = Family.create(
        family_id="FAM-000003",
        canonical_urn="urn:gda:fam:cycle_nexus_child",
        children=[c1],
        audit=valid_audit,
    )
    with pytest.raises(ModelFormatError, match="cannot be both a partner and a child"):
        fam_child.add_partner(shared_id)


# ==============================================================================
# GROUP 5: IMMUTABILITY & INTROSPECTION
# Note: Verification of frozen instance enforcement and .help() directory
# ==============================================================================


@pytest.mark.regression
def test_family_immutability(valid_family: Family) -> None:
    """Verify Family instances are frozen and immutable."""
    with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
        valid_family.canonical_urn = "urn:gda:fam:mutated"  # type: ignore[misc]

    with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
        valid_family.partner_ids = []  # type: ignore[misc]


@pytest.mark.regression
def test_family_introspection(valid_family: Family) -> None:
    """Verify .help() introspection renders member directory on Family."""
    help_text = valid_family.help(as_str=True)
    assert help_text is not None
    assert "=== Family Public Directory ===" in help_text
    assert "add_partner" in help_text
    assert "remove_partner" in help_text
    assert "add_child" in help_text
    assert "remove_child" in help_text
    assert "update_child_pedigree" in help_text
    assert "update_union" in help_text
    assert "update_union_type" in help_text
    assert "update_dissolution" in help_text
    assert "update_period" in help_text
    assert "update_marriage_date" in help_text
    assert "update_dissolution_date" in help_text
    assert "update_urn" in help_text
    assert "update_note" in help_text
    assert "to_dict" in help_text
    assert "from_dict" in help_text
    assert "to_json" in help_text
    assert "from_json" in help_text
    assert "mark_dirty" in help_text
    assert "mark_clean" in help_text
    assert "is_dirty" in help_text
    assert "child_ids" in help_text
    assert "partner_count" in help_text
    assert "child_count" in help_text
    assert "marriage_year" in help_text
    assert "sort_key" in help_text
