"""Path: tests/test_gda/test_model/test_entity/test_location.py

Comprehensive test suite verifying Location and jurisdictional primitives.

Operational Role:
    Verifies Location behavioral contracts including temporal sequence composition,
    self-referential boundary guards, LocationID enforcement, URN formatting,
    embedded Note container operations (add_note, update_note, delete_note, get_note, find_notes),
    NameThing integration, copy-on-write naming mutators, full field mutators,
    dirty tracking (_dirty, is_dirty, mark_clean, mark_dirty), sorting properties,
    and immutability invariants with 100% statement and branch coverage.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest
from pydantic import ValidationError

from gda.core.errors import ModelFormatError
from gda.enums.archival import NoteType
from gda.enums.location import JurisdictionCategory
from gda.enums.vital import HistoricNameType
from gda.model.atom.date import (
    DateModifier,
    DateString,
    EventDate,
)
from gda.model.atom.geo import Coordinates, Latitude, Longitude
from gda.model.atom.id import FactID, LocationID, NoteID, SiteID
from gda.model.base.audit import AuditStamp
from gda.model.base.name import HistoricVariant, NameThing
from gda.model.base.note import Note
from gda.model.base.time_period import TimePeriod
from gda.model.base.tombstone import Tombstone
from gda.model.entity.location import Location

__version__ = "1.0.0+build.34"


# ==============================================================================
# GROUP 1: FIXTURES & BASE INSTANCES
# Note: Verification of instantiation, property delegation, and embedded notes
# ==============================================================================


@pytest.fixture
def sample_period() -> TimePeriod:
    """Fixture providing a standard bounded temporal period."""
    return TimePeriod(
        start_date=EventDate(date=DateString("1727"), modifier=DateModifier.EXACT),
        end_date=EventDate(date=DateString("1900"), modifier=DateModifier.EXACT),
    )


@pytest.fixture
def sample_coords() -> Coordinates:
    """Fixture providing standard benchmark spatial coordinates."""
    return Coordinates(latitude=Latitude(43.1319), longitude=Longitude(-71.5497))


@pytest.fixture
def sample_location(
    golden_audit: AuditStamp, sample_period: TimePeriod, sample_coords: Coordinates
) -> Location:
    """Fixture providing a complete standard Location instance with NameThing."""
    hv = HistoricVariant.create(
        raw="Bow Mills",
        name="Bow Mills",
        historic_name_type=HistoricNameType.COLLOQUIAL,
    )
    name_obj = NameThing.create(
        raw="Bow",
        canonical="Bow",
        aliases=["Bow Town"],
        alt_spellings=["Bowe"],
        historic=[hv],
    )
    return Location(
        id=LocationID("LOC-000004"),
        audit=golden_audit,
        name=name_obj,
        category=JurisdictionCategory.CIVIL_TOWNSHIP,
        canonical_urn="urn:gda:loc:us:nh:merrimack:bow",
        parent_id=LocationID("LOC-000003"),
        is_primary_local_authority=True,
        is_unincorporated=False,
        period=sample_period,
        coordinates=sample_coords,
    )


# ==============================================================================
# GROUP 2: ENUMERATIONS & JURISDICTION RANKINGS
# Note: Verification of administrative rank ordering
# ==============================================================================


@pytest.mark.unit
def test_jurisdiction_category_members_and_ranks() -> None:
    """Verify JurisdictionCategory enum values and hierarchical administrative rank ordering."""
    assert JurisdictionCategory.COUNTRY.administrative_rank == 10
    assert JurisdictionCategory.STATOID.administrative_rank == 20
    assert JurisdictionCategory.COUNTY_EQUIVALENT.administrative_rank == 30
    assert JurisdictionCategory.CIVIL_TOWNSHIP.administrative_rank == 40
    assert JurisdictionCategory.MUNICIPALITY.administrative_rank == 40
    assert JurisdictionCategory.UNINCORPORATED_PLACE.administrative_rank == 50
    assert JurisdictionCategory.SPECIAL_DISTRICT.administrative_rank == 60


# ==============================================================================
# GROUP 3: LOCATION CREATION & ATTRIBUTES
# Note: Verification of minimal and complete instantiation contracts
# ==============================================================================


@pytest.mark.unit
def test_location_valid_creation(
    sample_location: Location, golden_audit: AuditStamp, sample_period: TimePeriod
) -> None:
    """Verify Location instantiates with complete domain attributes and delegated properties."""
    loc = sample_location
    assert loc.id == LocationID("LOC-000004")
    assert loc.audit == golden_audit
    assert loc.created_at == golden_audit.created_at
    assert loc.updated_at == golden_audit.updated_at
    assert loc.canonical_name == "Bow"
    assert loc.name.canonical == "Bow"
    assert loc.name.raw == "Bow"
    assert loc.category == JurisdictionCategory.CIVIL_TOWNSHIP
    assert loc.canonical_urn == "urn:gda:loc:us:nh:merrimack:bow"
    assert loc.parent_id == LocationID("LOC-000003")
    assert len(loc.historical_names) == 1
    assert loc.historical_names[0].raw == "Bow Mills"
    assert loc.aliases == ["Bow Town"]
    assert loc.alternate_names == ["Bow Town"]
    assert loc.is_primary_local_authority is True
    assert loc.is_unincorporated is False
    assert loc.period == sample_period
    assert loc.coordinates is not None
    assert loc.is_deprecated is False
    assert loc.is_dirty is False
    assert loc.category_rank == 40
    assert loc.sort_key == (40, "bow")


@pytest.mark.unit
def test_location_factory_string_name_support(golden_audit: AuditStamp) -> None:
    """Verify Location.create accepts simple string names and wraps them in NameThing."""
    loc = Location.create(
        location_id="LOC-000010",
        name="Concord",
        category=JurisdictionCategory.MUNICIPALITY,
        canonical_urn="urn:gda:loc:us:nh:concord",
        audit=golden_audit,
    )
    assert loc.id == LocationID("LOC-000010")
    assert isinstance(loc.name, NameThing)
    assert loc.canonical_name == "Concord"
    assert loc.aliases == []
    assert loc.historical_names == []
    assert loc.is_dirty is False


@pytest.mark.unit
def test_location_factory_name_thing_instance_support(golden_audit: AuditStamp) -> None:
    """Verify Location.create accepts a pre-constructed NameThing instance directly."""
    name_obj = NameThing.create(raw="City of Concord", canonical="Concord")
    loc = Location.create(
        location_id="LOC-000010",
        name=name_obj,
        category=JurisdictionCategory.MUNICIPALITY,
        canonical_urn="urn:gda:loc:us:nh:concord",
        audit=golden_audit,
    )
    assert loc.name is name_obj
    assert loc.canonical_name == "Concord"


@pytest.mark.unit
def test_location_factory_string_relations_resolution(golden_audit: AuditStamp) -> None:
    """Verify Location.create resolves string IDs and defaults cleanly."""
    loc = Location.create(
        location_id="LOC-000010",
        name="Concord",
        category="MUNICIPALITY",
        canonical_urn="urn:gda:loc:us:nh:concord",
        audit=golden_audit,
        parent_id="LOC-000003",
        predecessor_ids=["LOC-000001", "LOC-000002"],
        successor_ids=["LOC-000005"],
    )
    assert loc.parent_id == LocationID("LOC-000003")
    assert loc.predecessor_ids == [LocationID("LOC-000001"), LocationID("LOC-000002")]
    assert loc.successor_ids == [LocationID("LOC-000005")]

    loc_defaults = Location.create(
        location_id="LOC-000011",
        name="Hopkinton",
        category="CIVIL_TOWNSHIP",
        canonical_urn="urn:gda:loc:us:nh:hopkinton",
        predecessor_ids=None,
        successor_ids=None,
    )
    assert loc_defaults.predecessor_ids == []
    assert loc_defaults.successor_ids == []
    assert loc_defaults.audit is not None
    assert loc_defaults.notes == []
    assert loc_defaults.is_deprecated is False


@pytest.mark.unit
def test_location_string_representation(sample_location: Location) -> None:
    """Verify Location renders concise human-readable string representation."""
    assert str(sample_location) == "Bow [CIVIL_TOWNSHIP] (LOC-000004)"


# ==============================================================================
# GROUP 4: COPY-ON-WRITE NAMING & ATTRIBUTE MUTATORS
# Note: Verification of alias, historic variants, and full field mutations
# ==============================================================================


@pytest.mark.regression
def test_location_naming_mutators(
    sample_location: Location, golden_time_period: TimePeriod
) -> None:
    """Verify Location copy-on-write naming mutators update underlying NameThing."""
    original = sample_location
    assert original.aliases == ["Bow Town"]
    assert len(original.historical_names) == 1
    assert original.is_dirty is False

    # add_alias
    with_alias = original.add_alias("Bow Mills Village")
    assert with_alias is not original
    assert "Bow Mills Village" in with_alias.aliases
    assert "Bow Town" in with_alias.aliases
    assert with_alias.is_dirty is True

    # remove_alias (and no-op removal)
    with_removed_alias = with_alias.remove_alias("Bow Town")
    assert with_removed_alias is not with_alias
    assert "Bow Town" not in with_removed_alias.aliases
    assert "Bow Mills Village" in with_removed_alias.aliases
    assert with_removed_alias.remove_alias("NONEXISTENT") is with_removed_alias

    # add_historic_variant
    with_variant = with_removed_alias.add_historic_variant(
        raw="Suncook",
        name="Suncook Plantation",
        historic_name_type=HistoricNameType.COLONIAL,
        valid_period=golden_time_period,
        comment="Early colonial grant.",
    )
    assert with_variant is not with_removed_alias
    assert len(with_variant.historical_names) == 2
    assert with_variant.historical_names[1].raw == "Suncook"
    assert with_variant.is_dirty is True

    # remove_historic_variant (and no-op removal)
    with_removed_variant = with_variant.remove_historic_variant("Bow Mills")
    assert with_removed_variant is not with_variant
    assert len(with_removed_variant.historical_names) == 1
    assert with_removed_variant.historical_names[0].raw == "Suncook"
    assert (
        with_removed_variant.remove_historic_variant("NONEXISTENT")
        is with_removed_variant
    )


@pytest.mark.regression
def test_location_full_field_mutators_and_dirty_flag(
    sample_location: Location, golden_time_period: TimePeriod
) -> None:
    """Verify all domain field mutators update state, touch audit, and toggle dirty flag."""
    loc = sample_location
    assert loc.is_dirty is False

    # mark_dirty and mark_clean
    marked_dirty = loc.mark_dirty()
    assert marked_dirty.is_dirty is True
    assert marked_dirty.mark_dirty() is marked_dirty  # idempotent
    marked_clean = marked_dirty.mark_clean()
    assert marked_clean.is_dirty is False
    assert marked_clean.mark_clean() is marked_clean  # idempotent

    new_coords = Coordinates(latitude=Latitude(43.2081), longitude=Longitude(-71.5376))

    # update_coordinates
    loc_coords = loc.update_coordinates(new_coords)
    assert loc_coords is not loc
    assert loc_coords.coordinates == new_coords
    assert loc_coords.is_dirty is True

    # update_period
    loc_period = loc.update_period(golden_time_period)
    assert loc_period is not loc
    assert loc_period.period == golden_time_period
    assert loc_period.is_dirty is True

    # update_category
    loc_cat = loc.update_category(JurisdictionCategory.MUNICIPALITY)
    assert loc_cat is not loc
    assert loc_cat.category == JurisdictionCategory.MUNICIPALITY
    assert loc_cat.is_dirty is True

    # update_parent
    loc_parent = loc.update_parent("LOC-000099")
    assert loc_parent is not loc
    assert loc_parent.parent_id == LocationID("LOC-000099")
    assert loc_parent.is_dirty is True

    # update_urn
    loc_urn = loc.update_urn("urn:gda:loc:us:nh:bow:updated")
    assert loc_urn is not loc
    assert loc_urn.canonical_urn == "urn:gda:loc:us:nh:bow:updated"
    assert loc_urn.is_dirty is True

    # update_authority & update_unincorporated
    loc_auth = loc.update_authority(False)
    assert loc_auth.is_primary_local_authority is False
    assert loc_auth.is_dirty is True

    loc_uninc = loc.update_unincorporated(True)
    assert loc_uninc.is_unincorporated is True
    assert loc_uninc.is_dirty is True

    # add_predecessor & remove_predecessor (with idempotency and no-op)
    with_pred = loc.add_predecessor("LOC-000001")
    assert with_pred is not loc
    assert LocationID("LOC-000001") in with_pred.predecessor_ids
    assert with_pred.is_dirty is True
    assert with_pred.add_predecessor("LOC-000001") is with_pred

    with_rem_pred = with_pred.remove_predecessor("LOC-000001")
    assert with_rem_pred is not with_pred
    assert LocationID("LOC-000001") not in with_rem_pred.predecessor_ids
    assert with_rem_pred.remove_predecessor("LOC-000001") is with_rem_pred

    # add_successor & remove_successor (with idempotency and no-op)
    with_succ = loc.add_successor("LOC-000002")
    assert with_succ is not loc
    assert LocationID("LOC-000002") in with_succ.successor_ids
    assert with_succ.is_dirty is True
    assert with_succ.add_successor("LOC-000002") is with_succ

    with_rem_succ = with_succ.remove_successor("LOC-000002")
    assert with_rem_succ is not with_succ
    assert LocationID("LOC-000002") not in with_rem_succ.successor_ids
    assert with_rem_succ.remove_successor("LOC-000002") is with_rem_succ

    # update_name with NameThing and str
    loc_new_name_thing = loc.update_name(NameThing.create(raw="Greater Bow"))
    assert loc_new_name_thing is not loc
    assert loc_new_name_thing.canonical_name == "Greater Bow"
    assert loc_new_name_thing.is_dirty is True

    loc_new_name_str = loc.update_name("Bow Municipality")
    assert loc_new_name_str is not loc
    assert loc_new_name_str.canonical_name == "Bow Municipality"
    assert loc_new_name_str.is_dirty is True


@pytest.mark.regression
def test_location_attribute_mutators_defensive_errors(
    sample_location: Location,
) -> None:
    """Verify Location attribute mutators enforce domain invariants."""
    loc = sample_location

    with pytest.raises(ModelFormatError, match="cannot be its own parent"):
        loc.update_parent(loc.id)

    with pytest.raises(ModelFormatError, match="cannot be empty or whitespace"):
        loc.update_name("   ")

    with pytest.raises(TypeError, match="must be an instance of NameThing or str"):
        loc.update_name(999)  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="Invalid canonical_urn format"):
        loc.update_urn("invalid_urn")

    with pytest.raises(
        ModelFormatError, match="cannot reference itself in predecessor_ids"
    ):
        loc.add_predecessor(loc.id)

    with pytest.raises(
        ModelFormatError, match="cannot reference itself in successor_ids"
    ):
        loc.add_successor(loc.id)


# ==============================================================================
# GROUP 5: EMBEDDED NOTE CONTAINER & UPDATE OPERATIONS
# Note: Verification of inherited EntityLifecycleMixin and update_note mutators
# ==============================================================================


@pytest.mark.regression
def test_location_add_and_delete_embedded_note(sample_location: Location) -> None:
    """Verify Location inherits copy-on-write add_note and delete_note mutators."""
    loc = sample_location
    assert loc.has_notes is False
    assert loc.note_count == 0

    with_note = loc.add_note(
        text="Town established from Merrimack territory in 1727.",
        note_type=NoteType.RESEARCH,
        title="Charter History",
        tags=["charter", "merrimack"],
    )

    assert with_note is not loc
    assert with_note.note_count == 1
    assert with_note.has_notes is True
    assert with_note.name == loc.name
    assert with_note.category == loc.category
    assert with_note.canonical_urn == loc.canonical_urn
    assert with_note.notes[0].note_id == NoteID("NOT-000001")
    assert with_note.notes[0].title == "Charter History"
    assert with_note.updated_at.value >= loc.updated_at.value

    deleted = with_note.delete_note("NOT-000001")
    assert deleted is not with_note
    assert deleted.note_count == 0
    assert deleted.has_notes is False
    assert deleted.name == loc.name


@pytest.mark.regression
def test_location_update_embedded_note(sample_location: Location) -> None:
    """Verify Location update_note mutator modifies note text, title, type, and tags individually."""
    loc = sample_location.add_note(
        text="Initial observation.",
        note_type=NoteType.GENERAL,
        title="Initial",
        tags=["raw"],
    )
    note_id = loc.notes[0].note_id

    # Update all fields simultaneously
    updated_all = loc.update_note(
        note_id=note_id,
        text="Corrected archival observation.",
        title="Corrected Title",
        note_type=NoteType.RESEARCH,
        tags=["verified", "charter"],
    )
    assert updated_all is not loc
    assert updated_all.is_dirty is True
    target = updated_all.get_note(note_id)
    assert target is not None
    assert target.text == "Corrected archival observation."
    assert target.title == "Corrected Title"
    assert target.note_type == NoteType.RESEARCH
    assert target.tags == ["verified", "charter"]

    # Partial updates: text only
    up_text = loc.update_note(note_id=note_id, text="Only text updated")
    assert up_text.get_note(note_id).text == "Only text updated"
    assert up_text.get_note(note_id).title == "Initial"

    # Partial updates: title only
    up_title = loc.update_note(note_id=note_id, title="Only title updated")
    assert up_title.get_note(note_id).title == "Only title updated"

    # Partial updates: type only
    up_type = loc.update_note(note_id=note_id, note_type=NoteType.PROOF)
    assert up_type.get_note(note_id).note_type == NoteType.PROOF

    # Partial updates: tags only
    up_tags = loc.update_note(note_id=note_id, tags=["new_tag"])
    assert up_tags.get_note(note_id).tags == ["new_tag"]

    # No-op when note_id is absent
    assert loc.update_note(note_id="NOT-999999", text="No-op") is loc


@pytest.mark.regression
def test_location_find_notes_filtering_and_sorting(
    sample_location: Location, six_note_bundle: list[Note]
) -> None:
    """Verify Location searches and sorts across embedded notes."""
    loc = Location(
        id=sample_location.id,
        audit=sample_location.audit,
        name=sample_location.name,
        category=sample_location.category,
        canonical_urn=sample_location.canonical_urn,
        notes=six_note_bundle,
    )

    assert loc.note_count == 6
    assert len(loc.find_notes(note_type=NoteType.RESEARCH)) == 3
    assert len(loc.find_notes(note_type=NoteType.DISCREPANCY)) == 2
    assert len(loc.find_notes(note_type=NoteType.PROOF)) == 1

    sorted_by_title = loc.find_notes(sort_by="title")
    assert sorted_by_title[0].title == "Birth Year Conflict"
    assert sorted_by_title[-1].title == "Surname Spelling Variance"


# ==============================================================================
# GROUP 6: DEFENSIVE BOUNDARIES & VALIDATIONS
# Note: Verification of validation rules, ID regex, acyclicity, and type safety
# ==============================================================================


@pytest.mark.regression
@pytest.mark.parametrize(
    "bad_id_str",
    [
        "LOC-12345",
        "LOC-1234567",
        "LOC-ABCDEF",
        "000001",
        "",
    ],
)
def test_location_invalid_location_id_raises_format_error(
    bad_id_str: str, golden_audit: AuditStamp
) -> None:
    """Verify malformed LocationID values raise ModelFormatError when constructed."""
    try:
        bad_id = LocationID(bad_id_str)
        with pytest.raises(ModelFormatError, match="Invalid LocationID format"):
            Location(
                id=bad_id,
                audit=golden_audit,
                name=NameThing.create(raw="Invalid ID Town"),
                category=JurisdictionCategory.CIVIL_TOWNSHIP,
                canonical_urn="urn:gda:loc:us:nh:invalid",
            )
    except ModelFormatError:
        pass


@pytest.mark.regression
def test_location_conflicting_atom_id_type_raises_error(
    golden_audit: AuditStamp,
) -> None:
    """Verify Location rejects foreign AtomID subclasses assigned to id."""
    wrong_id = FactID("FID-000001")
    with pytest.raises((TypeError, ValidationError)):
        Location(
            id=wrong_id,  # type: ignore[arg-type]
            audit=golden_audit,
            name=NameThing.create(raw="Mismatched ID Town"),
            category=JurisdictionCategory.CIVIL_TOWNSHIP,
            canonical_urn="urn:gda:loc:us:nh:wrong_id",
        )


@pytest.mark.regression
def test_location_invalid_name_type_raises_error(golden_audit: AuditStamp) -> None:
    """Verify Location constructor rejects non-NameThing instances assigned to name."""
    with pytest.raises((TypeError, ValidationError)):
        Location(
            id=LocationID("LOC-000001"),
            audit=golden_audit,
            name="Raw String Not Allowed In Direct Constructor",  # type: ignore[arg-type]
            category=JurisdictionCategory.COUNTRY,
            canonical_urn="urn:gda:loc:us",
        )

    with pytest.raises(TypeError, match="must be an instance of NameThing or str"):
        Location.create(
            location_id=LocationID("LOC-000001"),
            audit=golden_audit,
            name=12345,  # type: ignore[arg-type]
            category=JurisdictionCategory.COUNTRY,
            canonical_urn="urn:gda:loc:us",
        )


@pytest.mark.regression
@pytest.mark.parametrize("blank_name", ["", " ", "\t\n"])
def test_location_blank_name_raises_format_error(
    blank_name: str, golden_audit: AuditStamp
) -> None:
    """Verify Location.create raises ModelFormatError if name string is blank."""
    with pytest.raises(
        ModelFormatError, match="Location 'name' cannot be empty or whitespace"
    ):
        Location.create(
            location_id=LocationID("LOC-000001"),
            audit=golden_audit,
            name=blank_name,
            category=JurisdictionCategory.COUNTRY,
            canonical_urn="urn:gda:loc:us",
        )


@pytest.mark.regression
@pytest.mark.parametrize(
    "invalid_urn",
    [
        "",
        " ",
        "urn:gda:site:us:nh:bow",
        "urn:loc:us:nh:bow",
        "URN:GDA:LOC:US:NH",
        "urn:gda:loc:invalid char",
    ],
)
def test_location_invalid_urn_raises_format_error(
    invalid_urn: str, golden_audit: AuditStamp
) -> None:
    """Verify Location raises ModelFormatError when canonical_urn is malformed."""
    with pytest.raises(ModelFormatError, match="Invalid canonical_urn format"):
        Location(
            id=LocationID("LOC-000001"),
            audit=golden_audit,
            name=NameThing.create(raw="United States"),
            category=JurisdictionCategory.COUNTRY,
            canonical_urn=invalid_urn,
        )


@pytest.mark.regression
def test_location_self_parent_raises_format_error(golden_audit: AuditStamp) -> None:
    """Verify Location raises ModelFormatError if parent_id equals id."""
    loc_id = LocationID("LOC-000001")
    with pytest.raises(ModelFormatError, match="cannot be its own parent"):
        Location(
            id=loc_id,
            audit=golden_audit,
            name=NameThing.create(raw="Circular State"),
            category=JurisdictionCategory.STATOID,
            canonical_urn="urn:gda:loc:us:cs",
            parent_id=loc_id,
        )


@pytest.mark.regression
def test_location_foreign_parent_id_type_raises_error(golden_audit: AuditStamp) -> None:
    """Verify Location raises TypeError or ValidationError if parent_id is not a LocationID."""
    wrong_parent = SiteID("SID-000001")
    with pytest.raises((TypeError, ValidationError)):
        Location(
            id=LocationID("LOC-000001"),
            audit=golden_audit,
            name=NameThing.create(raw="Child Town"),
            category=JurisdictionCategory.CIVIL_TOWNSHIP,
            canonical_urn="urn:gda:loc:us:nh:ct",
            parent_id=wrong_parent,  # type: ignore[arg-type]
        )


@pytest.mark.regression
def test_location_self_referential_predecessor_ids_raises_format_error(
    golden_audit: AuditStamp,
) -> None:
    """Verify Location rejects self-references in predecessor_ids."""
    loc_id = LocationID("LOC-000005")
    with pytest.raises(
        ModelFormatError, match="cannot reference itself in predecessor_ids"
    ):
        Location(
            id=loc_id,
            audit=golden_audit,
            name=NameThing.create(raw="Boundary Town"),
            category=JurisdictionCategory.CIVIL_TOWNSHIP,
            canonical_urn="urn:gda:loc:us:nh:bt",
            predecessor_ids=[loc_id],
        )


@pytest.mark.regression
def test_location_self_referential_successor_ids_raises_format_error(
    golden_audit: AuditStamp,
) -> None:
    """Verify Location rejects self-references in successor_ids."""
    loc_id = LocationID("LOC-000005")
    with pytest.raises(
        ModelFormatError, match="cannot reference itself in successor_ids"
    ):
        Location(
            id=loc_id,
            audit=golden_audit,
            name=NameThing.create(raw="Boundary Town"),
            category=JurisdictionCategory.CIVIL_TOWNSHIP,
            canonical_urn="urn:gda:loc:us:nh:bt",
            successor_ids=[loc_id],
        )


@pytest.mark.regression
def test_location_duplicate_predecessors_or_successors_raises_format_error(
    golden_audit: AuditStamp,
) -> None:
    """Verify Location rejects duplicate IDs in predecessor_ids or successor_ids."""
    dup_id = LocationID("LOC-000006")
    with pytest.raises(
        ModelFormatError, match="Duplicate entries found in predecessor_ids"
    ):
        Location(
            id=LocationID("LOC-000005"),
            audit=golden_audit,
            name=NameThing.create(raw="Boundary Town"),
            category=JurisdictionCategory.CIVIL_TOWNSHIP,
            canonical_urn="urn:gda:loc:us:nh:bt",
            predecessor_ids=[dup_id, dup_id],
        )

    with pytest.raises(
        ModelFormatError, match="Duplicate entries found in successor_ids"
    ):
        Location(
            id=LocationID("LOC-000005"),
            audit=golden_audit,
            name=NameThing.create(raw="Boundary Town"),
            category=JurisdictionCategory.CIVIL_TOWNSHIP,
            canonical_urn="urn:gda:loc:us:nh:bt",
            successor_ids=[dup_id, dup_id],
        )


@pytest.mark.regression
def test_location_self_supersession_raises_format_error(
    golden_audit: AuditStamp,
) -> None:
    """Verify Location raises ModelFormatError if tombstone supersedes itself."""
    loc_id = LocationID("LOC-000001")
    tombstone = Tombstone[LocationID](
        is_deprecated=True,
        deprecated_at=golden_audit.updated_at,
        superseded_by=loc_id,
    )
    with pytest.raises(
        ModelFormatError, match="Location cannot be superseded by itself"
    ):
        Location(
            id=loc_id,
            audit=golden_audit,
            name=NameThing.create(raw="Deprecated Town"),
            category=JurisdictionCategory.MUNICIPALITY,
            canonical_urn="urn:gda:loc:us:nh:dt",
            tombstone=tombstone,
        )


@pytest.mark.regression
def test_location_lifecycle_deprecate_and_restore(sample_location: Location) -> None:
    """Verify Location executes soft-deprecation and restoration lifecycles."""
    loc = sample_location
    assert loc.is_deprecated is False

    deprecated = loc.deprecate(superseded_by=LocationID("LOC-000099"))
    assert deprecated.is_deprecated is True
    assert deprecated.superseded_by == LocationID("LOC-000099")

    restored = deprecated.restore()
    assert restored.is_deprecated is False
    assert restored.superseded_by is None


# ==============================================================================
# GROUP 7: IMMUTABILITY & INTROSPECTION
# Note: Verification of frozen immutability and introspection directory
# ==============================================================================


@pytest.mark.regression
def test_location_immutability(sample_location: Location) -> None:
    """Verify Location fields cannot be mutated in place."""
    with pytest.raises((FrozenInstanceError, TypeError)):
        sample_location.canonical_urn = "urn:gda:loc:mutated"  # type: ignore[misc]

    with pytest.raises((FrozenInstanceError, TypeError)):
        sample_location.name = NameThing.create(raw="New Bow")  # type: ignore[misc]


@pytest.mark.regression
def test_location_introspection(sample_location: Location) -> None:
    """Verify .help() execution renders public members on Location."""
    help_text = sample_location.help(as_str=True)
    assert help_text is not None
    assert "=== Location Public Directory ===" in help_text
    assert "add_note" in help_text
    assert "update_note" in help_text
    assert "delete_note" in help_text
    assert "find_notes" in help_text
    assert "add_alias" in help_text
    assert "remove_alias" in help_text
    assert "add_historic_variant" in help_text
    assert "remove_historic_variant" in help_text
    assert "update_urn" in help_text
    assert "update_authority" in help_text
    assert "update_unincorporated" in help_text
    assert "add_predecessor" in help_text
    assert "remove_predecessor" in help_text
    assert "add_successor" in help_text
    assert "remove_successor" in help_text
    assert "mark_dirty" in help_text
    assert "mark_clean" in help_text
    assert "is_dirty" in help_text
    assert "category_rank" in help_text
    assert "sort_key" in help_text
