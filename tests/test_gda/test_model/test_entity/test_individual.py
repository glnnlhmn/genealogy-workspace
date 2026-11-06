"""Path: tests/test_gda/test_model/test_entity/test_individual.py

Comprehensive test suite verifying Individual entity model contracts and mutators.

Operational Role:
    Verifies Individual behavioral contracts, BaseEntity inheritance, foreign key
    LocationID/SiteID validation, URN formatting, GenderAtom integration,
    NamePerson integration, copy-on-write naming and field mutators, embedded note
    management, serialization round trips, dirty tracking (_dirty, is_dirty, mark_clean, mark_dirty),
    and immutability invariants with 100% statement and branch coverage.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest
from pydantic import ValidationError

from gda.core.errors import ModelFormatError, ModelRangeError
from gda.enums.archival import NoteType
from gda.model.atom.date import (
    DateModifier,
    EventDate,
    EventDateRange,
    IsoTimestamp,
)
from gda.model.atom.gender import GenderAtom
from gda.model.atom.id import FactID, IndividualID, LocationID, NoteID, SiteID
from gda.model.base.audit import AuditStamp
from gda.model.base.name import NamePerson
from gda.model.base.note import Note
from gda.model.base.tombstone import Tombstone
from gda.model.entity.individual import Individual

__version__ = "1.0.0+build.12"


# ==============================================================================
# FIXTURES
# Note: Verification of instantiation, property delegation, and embedded notes
# ==============================================================================


@pytest.fixture
def valid_audit() -> AuditStamp:
    """Fixture providing a standard test audit stamp."""
    ts = IsoTimestamp(value="2026-10-18T12:00:00Z")
    return AuditStamp(created_at=ts, updated_at=ts)


@pytest.fixture
def valid_name() -> NamePerson:
    """Fixture providing a structured NamePerson instance."""
    return NamePerson.create(
        raw="Johnathan Edward Smith",
        given="Johnathan",
        middle="Edward",
        surname="Smith",
        aliases=["Johnny"],
        married=["Jones"],
    )


@pytest.fixture
def point_birth_date() -> EventDate:
    """Fixture providing a standard point birth date."""
    return EventDate.create("1842-05-12")


@pytest.fixture
def point_death_date() -> EventDate:
    """Fixture providing a standard point death date."""
    return EventDate.create("1910-10-15")


@pytest.fixture
def range_death_date() -> EventDateRange:
    """Fixture providing a bounded death date range."""
    return EventDateRange.create("1910-01-01", "1912-12-31", DateModifier.BETWEEN)


@pytest.fixture
def valid_individual(
    valid_audit: AuditStamp,
    valid_name: NamePerson,
    point_birth_date: EventDate,
    range_death_date: EventDateRange,
) -> Individual:
    """Fixture providing a complete standard Individual instance with NamePerson."""
    return Individual(
        id=IndividualID(value="IND-000101"),
        audit=valid_audit,
        name=valid_name,
        canonical_urn="urn:gda:ind:smith_johnathan_1842",
        gender=GenderAtom("M"),
        birth_date=point_birth_date,
        death_date=range_death_date,
        birth_place_id=LocationID(value="LOC-000010"),
        death_place_id=SiteID(value="SID-000020"),
    )


# ==============================================================================
# GROUP 1: INITIALIZATION & BASELINE BEHAVIOR
# Note: Verification of minimal, complete, and factory creation contracts
# ==============================================================================


@pytest.mark.regression
def test_individual_init_minimal_defaults(valid_audit: AuditStamp, valid_name: NamePerson) -> None:
    """Verify minimal instantiation defaults and unpopulated fields."""
    ind = Individual(
        id=IndividualID(value="IND-000001"),
        audit=valid_audit,
        name=valid_name,
        canonical_urn="urn:gda:ind:smith_johnathan_000001",
    )
    assert ind.id.value == "IND-000001"
    assert ind.gender.value == "U"
    assert ind.sex == "U"
    assert ind.birth_date is None
    assert ind.death_date is None
    assert ind.birth_place_id is None
    assert ind.death_place_id is None
    assert ind.is_deceased is True
    assert ind.aliases == ["Johnny"]
    assert ind.alternate_names == ["Johnny"]
    assert ind.married_names == ["Jones"]
    assert ind.notes == []
    assert ind.is_deprecated is False
    assert ind.is_dirty is False
    assert ind.birth_year is None
    assert ind.death_year is None
    assert ind.approximate_age is None


@pytest.mark.regression
def test_individual_flexible_place_ids(valid_audit: AuditStamp, valid_name: NamePerson) -> None:
    """Verify birth_place_id and death_place_id accept both LocationID and SiteID."""
    loc_id = LocationID(value="LOC-000001")
    sid_id = SiteID(value="SID-000002")

    ind = Individual(
        id=IndividualID(value="IND-000001"),
        audit=valid_audit,
        name=valid_name,
        canonical_urn="urn:gda:ind:smith_000001",
        birth_place_id=sid_id,
        death_place_id=loc_id,
    )
    assert ind.birth_place_id == sid_id
    assert ind.death_place_id == loc_id


@pytest.mark.regression
def test_individual_factory_create_string_conversions(golden_audit: AuditStamp) -> None:
    """Verify Individual.create resolves string name, gender tokens, and string place IDs."""
    ind = Individual.create(
        individual_id="IND-000050",
        name="Mary Ann Evans",
        canonical_urn="urn:gda:ind:evans_mary_1819",
        gender="Female",
        birth_date="1819-11-22",
        death_date="1880-12-22",
        birth_place_id="LOC-000004",
        death_place_id="SID-000001",
        audit=golden_audit,
    )
    assert ind.id == IndividualID("IND-000050")
    assert ind.full_name == "Mary Ann Evans"
    assert ind.canonical_name == "Mary Ann Evans"
    assert ind.gender.value == "F"
    assert ind.sex == "F"
    assert ind.birth_year == 1819
    assert ind.death_year == 1880
    assert ind.approximate_age == 61
    assert ind.birth_place_id == LocationID("LOC-000004")
    assert ind.death_place_id == SiteID("SID-000001")
    assert ind.is_deceased is True
    assert ind.is_dirty is False

    # Test living individual with SiteID for birth_place and NO death_place_id
    ind_living = Individual.create(
        individual_id="IND-000052",
        name="Living Individual",
        canonical_urn="urn:gda:ind:living_individual",
        birth_place_id="SID-000005",
        is_deceased=False,
    )
    assert ind_living.birth_place_id == SiteID("SID-000005")
    assert ind_living.death_place_id is None
    assert ind_living.is_deceased is False


@pytest.mark.regression
def test_individual_factory_create_name_person_and_defaults() -> None:
    """Verify Individual.create accepts NamePerson instance and defaults audit/deceased."""
    np = NamePerson.create(raw="Robert Frost", given="Robert", surname="Frost")
    loc_id = LocationID("LOC-000001")
    sid_id = SiteID("SID-000002")

    ind = Individual.create(
        individual_id="IND-000051",
        name=np,
        canonical_urn="urn:gda:ind:frost_robert_1874",
        gender=GenderAtom("M"),
        birth_place_id=loc_id,
        death_place_id=sid_id,
    )
    assert ind.name is np
    assert ind.birth_place_id == loc_id
    assert ind.death_place_id == sid_id
    assert ind.audit is not None
    assert ind.created_at is not None
    assert ind.is_deceased is True
    assert ind.is_dirty is False


@pytest.mark.regression
def test_individual_str_representation_range_death(
    valid_individual: Individual,
) -> None:
    """Verify string formatting renders vitals with an EventDateRange death date."""
    expected = (
        "Johnathan Edward Smith [M] (b. 1842-05-12, d. BET 1910-01-01 AND 1912-12-31) (IND-000101)"
    )
    assert str(valid_individual) == expected


@pytest.mark.regression
def test_individual_str_representation_point_death(
    valid_audit: AuditStamp,
    valid_name: NamePerson,
    point_birth_date: EventDate,
    point_death_date: EventDate,
) -> None:
    """Verify string formatting renders vitals with a point EventDate death date."""
    ind = Individual(
        id=IndividualID(value="IND-000102"),
        audit=valid_audit,
        name=valid_name,
        canonical_urn="urn:gda:ind:smith_johnathan_1842",
        gender=GenderAtom("M"),
        birth_date=point_birth_date,
        death_date=point_death_date,
    )
    assert str(ind) == "Johnathan Edward Smith [M] (b. 1842-05-12, d. 1910-10-15) (IND-000102)"


@pytest.mark.regression
def test_individual_str_living(
    valid_audit: AuditStamp, valid_name: NamePerson, point_birth_date: EventDate
) -> None:
    """Verify string formatting renders living status when is_deceased is False."""
    ind = Individual(
        id=IndividualID(value="IND-000002"),
        audit=valid_audit,
        name=valid_name,
        canonical_urn="urn:gda:ind:smith_living_000002",
        gender=GenderAtom("F"),
        birth_date=point_birth_date,
        is_deceased=False,
    )
    assert str(ind) == "Johnathan Edward Smith [F] (b. 1842-05-12, living) (IND-000002)"


@pytest.mark.regression
def test_individual_str_deceased_unknown_death(
    valid_audit: AuditStamp, valid_name: NamePerson, point_birth_date: EventDate
) -> None:
    """Verify string formatting renders 'd. unk' when deceased but death_date is None."""
    ind = Individual(
        id=IndividualID(value="IND-000003"),
        audit=valid_audit,
        name=valid_name,
        canonical_urn="urn:gda:ind:smith_000003",
        gender=GenderAtom("U"),
        birth_date=point_birth_date,
        is_deceased=True,
    )
    assert str(ind) == "Johnathan Edward Smith [U] (b. 1842-05-12, d. unk) (IND-000003)"


@pytest.mark.regression
def test_individual_str_death_only(
    valid_audit: AuditStamp, valid_name: NamePerson, point_death_date: EventDate
) -> None:
    """Verify string formatting when only death_date is present."""
    ind = Individual(
        id=IndividualID(value="IND-000006"),
        audit=valid_audit,
        name=valid_name,
        canonical_urn="urn:gda:ind:smith_000006",
        gender=GenderAtom("U"),
        death_date=point_death_date,
        is_deceased=True,
    )
    assert str(ind) == "Johnathan Edward Smith [U] (d. 1910-10-15) (IND-000006)"


@pytest.mark.regression
def test_individual_str_no_dates(valid_audit: AuditStamp, valid_name: NamePerson) -> None:
    """Verify string formatting when no dates are present."""
    ind = Individual(
        id=IndividualID(value="IND-000004"),
        audit=valid_audit,
        name=valid_name,
        canonical_urn="urn:gda:ind:smith_000004",
    )
    assert str(ind) == "Johnathan Edward Smith [U] (IND-000004)"


# ==============================================================================
# GROUP 2: YEARS, AGE CALCULATION & REGISTER SORTING
# Note: Verification of lower-bound year extraction, age, and sorting keys
# ==============================================================================


@pytest.mark.regression
def test_individual_year_extraction_and_age(valid_individual: Individual) -> None:
    """Verify lower-bound year extraction and approximate age calculation."""
    assert valid_individual.full_name == "Johnathan Edward Smith"
    assert valid_individual.given == "Johnathan"
    assert valid_individual.surname == "Smith"
    assert valid_individual.birth_year == 1842
    assert valid_individual.death_year == 1910
    assert valid_individual.approximate_age == 68


@pytest.mark.regression
def test_individual_approximate_age_missing_one_bound(
    valid_audit: AuditStamp, valid_name: NamePerson, point_birth_date: EventDate
) -> None:
    """Verify approximate_age evaluates to None if only birth_date is present."""
    ind = Individual(
        id=IndividualID(value="IND-000005"),
        audit=valid_audit,
        name=valid_name,
        canonical_urn="urn:gda:ind:smith_000005",
        birth_date=point_birth_date,
    )
    assert ind.birth_year == 1842
    assert ind.death_year is None
    assert ind.approximate_age is None


@pytest.mark.regression
def test_individual_register_sort_key(
    valid_audit: AuditStamp,
    valid_individual: Individual,
) -> None:
    """Verify deterministic register sort key uses lower-bound year and tiebreakers."""
    assert valid_individual.sort_key == ("smith", "johnathan", 1842, "IND-000101")

    older_smith = Individual(
        id=IndividualID(value="IND-000090"),
        audit=valid_audit,
        name=NamePerson.create(raw="Aaron Smith", given="Aaron", surname="Smith"),
        canonical_urn="urn:gda:ind:smith_aaron_000090",
        birth_date=EventDate.create("1820-01-01"),
    )
    undated_smith = Individual(
        id=IndividualID(value="IND-000095"),
        audit=valid_audit,
        name=NamePerson.create(raw="Zachary Smith", given="Zachary", surname="Smith"),
        canonical_urn="urn:gda:ind:smith_zachary_000095",
    )

    records = [undated_smith, valid_individual, older_smith]
    sorted_records = sorted(records, key=lambda ind: ind.sort_key)

    assert sorted_records == [older_smith, valid_individual, undated_smith]
    assert undated_smith.sort_key == ("smith", "zachary", 9999, "IND-000095")


@pytest.mark.regression
def test_individual_sort_key_missing_name_components(valid_audit: AuditStamp) -> None:
    """Verify sort_key handles None surname or given gracefully."""
    ind = Individual(
        id=IndividualID(value="IND-000099"),
        audit=valid_audit,
        name=NamePerson.create(raw="Anonymous"),
        canonical_urn="urn:gda:ind:anonymous_000099",
    )
    assert ind.sort_key == ("", "", 9999, "IND-000099")


# ==============================================================================
# GROUP 3: COPY-ON-WRITE NAMING & ATTRIBUTE MUTATORS
# Note: Verification of alias, married names, vitals, and dirty state
# ==============================================================================


@pytest.mark.regression
def test_individual_naming_mutators(valid_individual: Individual) -> None:
    """Verify copy-on-write alias and married surname mutators."""
    ind = valid_individual
    assert ind.aliases == ["Johnny"]
    assert ind.married_names == ["Jones"]
    assert ind.is_dirty is False

    # add_alias & remove_alias
    with_alias = ind.add_alias("Jack")
    assert with_alias is not ind
    assert "Jack" in with_alias.aliases
    assert with_alias.is_dirty is True
    assert with_alias.add_alias("Jack") is with_alias

    rem_alias = with_alias.remove_alias("Johnny")
    assert rem_alias is not with_alias
    assert "Johnny" not in rem_alias.aliases
    assert rem_alias.remove_alias("NONEXISTENT") is rem_alias

    # add_married & remove_married
    with_married = ind.add_married("Miller")
    assert with_married is not ind
    assert "Miller" in with_married.married_names
    assert with_married.is_dirty is True
    assert with_married.add_married("Miller") is with_married

    rem_married = with_married.remove_married("Jones")
    assert rem_married is not with_married
    assert "Jones" not in rem_married.married_names
    assert rem_married.remove_married("NONEXISTENT") is rem_married


@pytest.mark.regression
def test_individual_full_field_mutators_and_dirty_flag(
    valid_individual: Individual,
    point_birth_date: EventDate,
    point_death_date: EventDate,
) -> None:
    """Verify all domain field mutators update state, touch audit, and toggle dirty flag."""
    ind = valid_individual
    assert ind.is_dirty is False

    # mark_dirty and mark_clean
    marked_dirty = ind.mark_dirty()
    assert marked_dirty.is_dirty is True
    assert marked_dirty.mark_dirty() is marked_dirty
    marked_clean = marked_dirty.mark_clean()
    assert marked_clean.is_dirty is False
    assert marked_clean.mark_clean() is marked_clean

    # update_name with NamePerson and str
    up_name_obj = ind.update_name(NamePerson.create(raw="Jonathan Smith"))
    assert up_name_obj is not ind
    assert up_name_obj.full_name == "Jonathan Smith"
    assert up_name_obj.is_dirty is True

    up_name_str = ind.update_name("J. E. Smith")
    assert up_name_str is not ind
    assert up_name_str.full_name == "J. E. Smith"
    assert up_name_str.is_dirty is True

    # update_gender
    up_gender = ind.update_gender(GenderAtom("U"))
    assert up_gender is not ind
    assert up_gender.gender.value == "U"
    assert up_gender.is_dirty is True

    up_gender_str = ind.update_gender("Female")
    assert up_gender_str.gender.value == "F"

    # update_birth with string date, string place, SiteID, and defaults
    new_birth_str = "1843-01-01"
    up_birth = ind.update_birth(birth_date=new_birth_str, birth_place_id="LOC-000005")
    assert up_birth is not ind
    assert up_birth.birth_date == EventDate.create("1843-01-01")
    assert up_birth.birth_place_id == LocationID("LOC-000005")
    assert up_birth.is_dirty is True

    up_birth_sid = ind.update_birth(birth_place_id=SiteID("SID-000001"))
    assert up_birth_sid.birth_place_id == SiteID("SID-000001")

    up_birth_sid_str = ind.update_birth(birth_place_id="SID-000003")
    assert up_birth_sid_str.birth_place_id == SiteID("SID-000003")

    up_birth_keep_place = ind.update_birth(birth_date="1844-01-01", birth_place_id=None)
    assert up_birth_keep_place.birth_place_id == ind.birth_place_id

    # update_death with string date, string place, SiteID, and defaults
    new_death_str = "1911-05-05"
    up_death = ind.update_death(death_date=new_death_str, death_place_id="LOC-000006")
    assert up_death is not ind
    assert up_death.death_date == EventDate.create("1911-05-05")
    assert up_death.death_place_id == LocationID("LOC-000006")
    assert up_death.is_deceased is True
    assert up_death.is_dirty is True

    up_death_sid = ind.update_death(death_place_id=SiteID("SID-000002"))
    assert up_death_sid.death_place_id == SiteID("SID-000002")

    up_death_sid_str = ind.update_death(death_place_id="SID-000004")
    assert up_death_sid_str.death_place_id == SiteID("SID-000004")

    up_death_keep_place = ind.update_death(death_date="1912-01-01", death_place_id=None)
    assert up_death_keep_place.death_place_id == ind.death_place_id

    # update_urn
    up_urn = ind.update_urn("urn:gda:ind:smith_johnathan_updated")
    assert up_urn is not ind
    assert up_urn.canonical_urn == "urn:gda:ind:smith_johnathan_updated"
    assert up_urn.is_dirty is True


@pytest.mark.regression
def test_individual_attribute_mutators_defensive_errors(
    valid_individual: Individual,
) -> None:
    """Verify Individual attribute mutators enforce domain invariants."""
    ind = valid_individual

    with pytest.raises(ModelFormatError, match="cannot be empty or whitespace"):
        ind.update_name("   ")

    with pytest.raises(TypeError, match="must be an instance of NamePerson or str"):
        ind.update_name(999)  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="Invalid canonical_urn format"):
        ind.update_urn("invalid_urn")


# ==============================================================================
# GROUP 4: EMBEDDED NOTE CONTAINER & UPDATE OPERATIONS
# Note: Verification of inherited EntityLifecycleMixin and update_note mutators
# ==============================================================================


@pytest.mark.regression
def test_individual_add_and_delete_embedded_note(valid_individual: Individual) -> None:
    """Verify Individual inherits copy-on-write add_note and delete_note mutators."""
    ind = valid_individual
    assert ind.has_notes is False
    assert ind.note_count == 0

    with_note = ind.add_note(
        text="Birth record confirmed in Merrimack county vital records.",
        note_type=NoteType.RESEARCH,
        title="Vital Registration",
        tags=["vital", "merrimack"],
    )

    assert with_note is not ind
    assert with_note.note_count == 1
    assert with_note.has_notes is True
    assert with_note.canonical_name == ind.canonical_name
    assert with_note.notes[0].note_id == NoteID("NOT-000001")
    assert with_note.notes[0].title == "Vital Registration"
    assert with_note.updated_at.value >= ind.updated_at.value

    deleted = with_note.delete_note("NOT-000001")
    assert deleted is not with_note
    assert deleted.note_count == 0
    assert deleted.has_notes is False


@pytest.mark.regression
def test_individual_update_embedded_note(valid_individual: Individual) -> None:
    """Verify Individual update_note mutator modifies note text, title, type, and tags individually."""
    ind = valid_individual.add_note(
        text="Initial baptism observation.",
        note_type=NoteType.GENERAL,
        title="Initial",
        tags=["raw"],
    )
    note_id = ind.notes[0].note_id

    # Update all fields simultaneously
    updated_all = ind.update_note(
        note_id=note_id,
        text="Corrected church record observation.",
        title="Corrected Church Entry",
        note_type=NoteType.RESEARCH,
        tags=["verified", "parish"],
    )
    assert updated_all is not ind
    assert updated_all.is_dirty is True
    target = updated_all.get_note(note_id)
    assert target is not None
    assert target.text == "Corrected church record observation."
    assert target.title == "Corrected Church Entry"
    assert target.note_type == NoteType.RESEARCH
    assert target.tags == ["verified", "parish"]

    # Partial updates: text only
    up_text = ind.update_note(note_id=note_id, text="Only text updated")
    assert up_text.get_note(note_id).text == "Only text updated"
    assert up_text.get_note(note_id).title == "Initial"

    # Partial updates: title only
    up_title = ind.update_note(note_id=note_id, title="Only title updated")
    assert up_title.get_note(note_id).title == "Only title updated"

    # Partial updates: type only
    up_type = ind.update_note(note_id=note_id, note_type=NoteType.PROOF)
    assert up_type.get_note(note_id).note_type == NoteType.PROOF

    # Partial updates: tags only
    up_tags = ind.update_note(note_id=note_id, tags=["new_tag"])
    assert up_tags.get_note(note_id).tags == ["new_tag"]

    # No-op when note_id is absent
    assert ind.update_note(note_id="NOT-999999", text="No-op") is ind


@pytest.mark.regression
def test_individual_find_notes_filtering_and_sorting(
    valid_individual: Individual, six_note_bundle: list[Note]
) -> None:
    """Verify Individual searches and sorts across embedded notes."""
    ind = Individual(
        id=valid_individual.id,
        audit=valid_individual.audit,
        name=valid_individual.name,
        canonical_urn=valid_individual.canonical_urn,
        notes=six_note_bundle,
    )

    assert ind.note_count == 6
    assert len(ind.find_notes(note_type=NoteType.RESEARCH)) == 3
    assert len(ind.find_notes(note_type=NoteType.DISCREPANCY)) == 2
    assert len(ind.find_notes(note_type=NoteType.PROOF)) == 1

    sorted_by_title = ind.find_notes(sort_by="title")
    assert sorted_by_title[0].title == "Birth Year Conflict"
    assert sorted_by_title[-1].title == "Surname Spelling Variance"


# ==============================================================================
# GROUP 5: SERIALIZATION & ROUND TRIPS
# Note: Verification of dictionary and JSON string payload conversions
# ==============================================================================


@pytest.mark.integration
def test_individual_to_dict_and_from_dict_round_trip(
    valid_individual: Individual,
) -> None:
    """Verify Individual dictionary serialization and deserialization."""
    ind_with_notes = valid_individual.add_note(
        text="Census verification.", title="Census Note", note_type=NoteType.RESEARCH
    )
    data = ind_with_notes.to_dict()

    assert data["id"] == "IND-000101"
    assert data["gender"] == "M"
    assert data["canonical_urn"] == "urn:gda:ind:smith_johnathan_1842"
    assert data["is_deceased"] is True
    assert data["birth_place_id"] == "LOC-000010"
    assert data["death_place_id"] == "SID-000020"
    assert data["birth_date"] == {"date": "1842-05-12"}
    assert "start_date" in data["death_date"]
    assert len(data["notes"]) == 1

    restored = Individual.from_dict(data)
    assert restored.id == ind_with_notes.id
    assert restored.full_name == ind_with_notes.full_name
    assert restored.gender == ind_with_notes.gender
    assert restored.canonical_urn == ind_with_notes.canonical_urn
    assert restored.birth_date == ind_with_notes.birth_date
    assert restored.death_date == ind_with_notes.death_date
    assert restored.birth_place_id == ind_with_notes.birth_place_id
    assert restored.death_place_id == ind_with_notes.death_place_id
    assert restored.note_count == 1


@pytest.mark.integration
def test_individual_to_dict_minimal_omits_none_fields() -> None:
    """Verify Individual.to_dict omits optional fields."""
    minimal = Individual.create(
        individual_id="IND-000300",
        name="Bare Individual",
        canonical_urn="urn:gda:ind:bare_ind",
    )
    data = minimal.to_dict()
    assert "birth_date" not in data
    assert "death_date" not in data
    assert "birth_place_id" not in data
    assert "death_place_id" not in data

    restored = Individual.from_dict(data)
    assert restored.id == minimal.id
    assert restored.birth_date is None
    assert restored.death_date is None


@pytest.mark.integration
def test_individual_from_dict_minimal_and_string_name() -> None:
    """Verify Individual.from_dict parses dictionary without audit or tombstone."""
    data = {
        "id": "IND-000200",
        "name": "Jane Eyre",
        "canonical_urn": "urn:gda:ind:eyre_jane",
        "birth_date": {"date": "1820-04-21"},
    }
    restored = Individual.from_dict(data)
    assert restored.id == IndividualID("IND-000200")
    assert restored.full_name == "Jane Eyre"
    assert restored.birth_date == EventDate.create("1820-04-21")
    assert restored.death_date is None
    assert restored.audit is not None
    assert restored.is_deprecated is False


@pytest.mark.integration
def test_individual_json_round_trip(valid_individual: Individual) -> None:
    """Verify Individual JSON serialization round trip."""
    json_str = valid_individual.to_json()
    assert "IND-000101" in json_str
    assert "Johnathan Edward Smith" in json_str

    restored = Individual.from_json(json_str)
    assert restored.id == valid_individual.id
    assert restored.full_name == valid_individual.full_name
    assert restored.gender == valid_individual.gender


@pytest.mark.regression
def test_individual_deserialization_defensive_errors() -> None:
    """Verify Individual deserialization defensive error boundaries."""
    with pytest.raises(ModelFormatError, match="must be a dictionary"):
        Individual.from_dict("not-a-dict")  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="Missing required field 'id'"):
        Individual.from_dict({"name": "No ID"})

    with pytest.raises(ModelFormatError, match="Missing required field 'name'"):
        Individual.from_dict({"id": "IND-000001"})

    with pytest.raises(ModelFormatError, match="Failed to parse Individual JSON string"):
        Individual.from_json("{broken-json")


# ==============================================================================
# GROUP 6: DEFENSIVE BOUNDARIES & VALIDATIONS
# Note: Verification of validation rules, ID regex, and type safety
# ==============================================================================


@pytest.mark.regression
@pytest.mark.parametrize(
    "bad_id_str",
    [
        "IND-12345",
        "IND-ABCDEF",
        "000001",
        "",
    ],
)
def test_individual_invalid_id_format(
    bad_id_str: str, valid_audit: AuditStamp, valid_name: NamePerson
) -> None:
    """Verify malformed IndividualID values raise ModelFormatError when constructed."""
    try:
        bad_id = IndividualID(bad_id_str)
        with pytest.raises(ModelFormatError, match="Invalid IndividualID format"):
            Individual(
                id=bad_id,
                audit=valid_audit,
                name=valid_name,
                canonical_urn="urn:gda:ind:smith_invalid",
            )
    except ModelFormatError:
        pass


@pytest.mark.regression
def test_individual_conflicting_atom_id_type_raises_error(
    valid_audit: AuditStamp, valid_name: NamePerson
) -> None:
    """Verify Individual rejects foreign AtomID subclasses assigned to id."""
    wrong_id = FactID("FID-000001")
    with pytest.raises((TypeError, ValidationError)):
        Individual(
            id=wrong_id,  # type: ignore[arg-type]
            audit=valid_audit,
            name=valid_name,
            canonical_urn="urn:gda:ind:smith_wrong_id",
        )


@pytest.mark.regression
def test_individual_post_init_id_pattern_defensive(
    valid_individual: Individual,
) -> None:
    """Verify Individual.__post_init__ raises ModelFormatError if id pattern fails (line 101)."""

    class MalformedIndividualID(IndividualID):
        """Subclass bypassing AtomID.__post_init__ format enforcement."""

        def __init__(self, value: str) -> None:
            object.__setattr__(self, "value", value)
            object.__setattr__(self, "expected_prefix", "IND")

    object.__setattr__(valid_individual, "id", MalformedIndividualID("IND-12"))
    with pytest.raises(ModelFormatError, match="Invalid IndividualID format"):
        valid_individual.__post_init__()


@pytest.mark.regression
def test_individual_invalid_name_type_raises_error(valid_audit: AuditStamp) -> None:
    """Verify Individual constructor rejects non-NamePerson instances assigned to name."""
    with pytest.raises((TypeError, ValidationError)):
        Individual(
            id=IndividualID("IND-000001"),
            audit=valid_audit,
            name="Raw String Not Allowed In Direct Constructor",  # type: ignore[arg-type]
            canonical_urn="urn:gda:ind:smith_000001",
        )

    with pytest.raises(TypeError, match="must be an instance of NamePerson or str"):
        Individual.create(
            individual_id=IndividualID("IND-000001"),
            audit=valid_audit,
            name=12345,  # type: ignore[arg-type]
            canonical_urn="urn:gda:ind:smith_000001",
        )


@pytest.mark.regression
@pytest.mark.parametrize("blank_name", ["", "   ", "\t\n"])
def test_individual_blank_name_raises_format_error(
    blank_name: str, valid_audit: AuditStamp
) -> None:
    """Verify Individual.create raises ModelFormatError if name is blank."""
    with pytest.raises(ModelFormatError, match="Individual 'name' cannot be empty or whitespace"):
        Individual.create(
            individual_id=IndividualID("IND-000001"),
            audit=valid_audit,
            name=blank_name,
            canonical_urn="urn:gda:ind:smith_000001",
        )


@pytest.mark.regression
@pytest.mark.parametrize(
    "invalid_urn",
    [
        "",
        "   ",
        "urn:gda:loc:us:nh:bow",
        "urn:ind:smith_000001",
        "URN:GDA:IND:SMITH",
        "urn:gda:ind:invalid space",
    ],
)
def test_individual_invalid_urn_format(
    invalid_urn: str, valid_audit: AuditStamp, valid_name: NamePerson
) -> None:
    """Verify Individual raises ModelFormatError when canonical_urn is malformed."""
    with pytest.raises(ModelFormatError, match="Invalid canonical_urn format"):
        Individual(
            id=IndividualID(value="IND-000001"),
            audit=valid_audit,
            name=valid_name,
            canonical_urn=invalid_urn,
        )


@pytest.mark.regression
def test_individual_self_supersession_forbidden(
    valid_audit: AuditStamp, valid_name: NamePerson
) -> None:
    """Verify ModelFormatError when tombstone supersedes self."""
    ind_id = IndividualID(value="IND-000001")
    tombstone = Tombstone[IndividualID](
        is_deprecated=True,
        deprecated_at=IsoTimestamp.now_utc(),
        superseded_by=ind_id,
    )
    with pytest.raises(ModelFormatError, match="Individual cannot be superseded by itself"):
        Individual(
            id=ind_id,
            audit=valid_audit,
            name=valid_name,
            canonical_urn="urn:gda:ind:smith_000001",
            tombstone=tombstone,
        )


@pytest.mark.regression
def test_individual_superseded_by_other_allowed(
    valid_audit: AuditStamp, valid_name: NamePerson
) -> None:
    """Verify tombstone with valid superseded_by does not raise error."""
    ind_id = IndividualID(value="IND-000001")
    other_id = IndividualID(value="IND-000002")
    tombstone = Tombstone[IndividualID](
        is_deprecated=True,
        deprecated_at=IsoTimestamp.now_utc(),
        superseded_by=other_id,
    )
    ind = Individual(
        id=ind_id,
        audit=valid_audit,
        name=valid_name,
        canonical_urn="urn:gda:ind:smith_000001",
        tombstone=tombstone,
    )
    assert ind.is_deprecated is True
    assert ind.superseded_by == other_id


@pytest.mark.regression
def test_individual_living_cannot_possess_death_data(
    valid_audit: AuditStamp,
    valid_name: NamePerson,
    range_death_date: EventDateRange,
) -> None:
    """Verify ModelFormatError when living individual possesses death date or place."""
    with pytest.raises(ModelFormatError, match="death_date while is_deceased is False"):
        Individual(
            id=IndividualID(value="IND-000001"),
            audit=valid_audit,
            name=valid_name,
            canonical_urn="urn:gda:ind:smith_000001",
            death_date=range_death_date,
            is_deceased=False,
        )

    with pytest.raises(ModelFormatError, match="death_place_id while is_deceased is False"):
        Individual(
            id=IndividualID(value="IND-000001"),
            audit=valid_audit,
            name=valid_name,
            canonical_urn="urn:gda:ind:smith_000001",
            death_place_id=SiteID(value="SID-000001"),
            is_deceased=False,
        )


@pytest.mark.regression
def test_individual_death_year_preceding_birth_year(
    valid_audit: AuditStamp, valid_name: NamePerson
) -> None:
    """Verify ModelRangeError when death year precedes birth year."""
    b_date = EventDate.create("1920-05-10")
    d_date = EventDate.create("1890-01-01")

    with pytest.raises(ModelRangeError, match="Death year.*cannot precede birth year"):
        Individual(
            id=IndividualID(value="IND-000001"),
            audit=valid_audit,
            name=valid_name,
            canonical_urn="urn:gda:ind:smith_000001",
            birth_date=b_date,
            death_date=d_date,
        )


@pytest.mark.regression
def test_individual_lifecycle_deprecate_and_restore(
    valid_individual: Individual,
) -> None:
    """Verify Individual executes soft-deprecation and restoration lifecycles."""
    ind = valid_individual
    assert ind.is_deprecated is False

    deprecated = ind.deprecate(superseded_by=IndividualID("IND-000099"))
    assert deprecated.is_deprecated is True
    assert deprecated.superseded_by == IndividualID("IND-000099")

    restored = deprecated.restore()
    assert restored.is_deprecated is False
    assert restored.superseded_by is None


# ==============================================================================
# GROUP 7: IMMUTABILITY & INTROSPECTION
# Note: Verification of frozen immutability and introspection directory
# ==============================================================================


@pytest.mark.regression
def test_individual_immutability(valid_individual: Individual) -> None:
    """Verify Individual instances are frozen and immutable."""
    with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
        valid_individual.canonical_urn = "urn:gda:ind:mutated"  # type: ignore[misc]

    with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
        valid_individual.name = NamePerson.create(raw="New Name")  # type: ignore[misc]


@pytest.mark.regression
def test_individual_introspection(valid_individual: Individual) -> None:
    """Verify .help() introspection renders member directory on Individual."""
    help_text = valid_individual.help(as_str=True)
    assert help_text is not None
    assert "=== Individual Public Directory ===" in help_text
    assert "add_note" in help_text
    assert "update_note" in help_text
    assert "delete_note" in help_text
    assert "find_notes" in help_text
    assert "add_alias" in help_text
    assert "remove_alias" in help_text
    assert "add_married" in help_text
    assert "remove_married" in help_text
    assert "update_name" in help_text
    assert "update_gender" in help_text
    assert "update_birth" in help_text
    assert "update_death" in help_text
    assert "update_urn" in help_text
    assert "to_dict" in help_text
    assert "from_dict" in help_text
    assert "to_json" in help_text
    assert "from_json" in help_text
    assert "mark_dirty" in help_text
    assert "mark_clean" in help_text
    assert "is_dirty" in help_text
    assert "birth_year" in help_text
    assert "death_year" in help_text
    assert "approximate_age" in help_text
    assert "sort_key" in help_text
