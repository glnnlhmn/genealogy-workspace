"""Path: tests/test_gda/test_model/test_entity/test_site.py

Comprehensive test suite verifying Site entity contracts and mutators.

Operational Role:
    Verifies Site behavioral contracts, BaseEntity inheritance, foreign key
    LocationID validation, URN formatting, optional address/coordinate composition,
    NameThing integration, copy-on-write naming and field mutators, embedded note
    management, dirty tracking (_dirty, is_dirty, mark_clean, mark_dirty), and
    immutability invariants with 100% statement and branch coverage.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest
from pydantic import ValidationError

from gda.core.errors import ModelFormatError
from gda.enums.archival import NoteType
from gda.enums.site import SiteCategory, SiteType
from gda.enums.vital import HistoricNameType
from gda.model.atom.date import DateModifier, DateString, EventDate, IsoTimestamp
from gda.model.atom.geo import Coordinates, Latitude, Longitude
from gda.model.atom.id import FactID, LocationID, NoteID, SiteID
from gda.model.base.address import Address
from gda.model.base.audit import AuditStamp
from gda.model.base.name import HistoricVariant, NameThing
from gda.model.base.note import Note
from gda.model.base.time_period import TimePeriod
from gda.model.base.tombstone import Tombstone
from gda.model.entity.site import Site, SiteEntityModel

__version__ = "1.0.0+build.7"


# ==============================================================================
# FIXTURES: GOLDEN PAYLOADS & BASE INSTANCES
# Note: Verification of instantiation, property delegation, and embedded notes
# ==============================================================================


@pytest.fixture
def golden_timestamp() -> IsoTimestamp:
    """Fixture providing a standard test timestamp."""
    return IsoTimestamp("2026-10-16T12:00:00Z")


@pytest.fixture
def golden_audit(golden_timestamp: IsoTimestamp) -> AuditStamp:
    """Fixture providing a standard audit stamp."""
    return AuditStamp(created_at=golden_timestamp, updated_at=golden_timestamp)


@pytest.fixture
def golden_period() -> TimePeriod:
    """Fixture providing a standard bounded temporal period."""
    return TimePeriod(
        start_date=EventDate(date=DateString("1730"), modifier=DateModifier.EXACT),
        end_date=EventDate(date=DateString("1920"), modifier=DateModifier.ABOUT),
    )


@pytest.fixture
def golden_address() -> Address:
    """Fixture providing a structured Address instance."""
    return Address(
        address_line_1="Woodhill Hook Road",
        city="Bow",
        state="NH",
        postal_code="03304",
    )


@pytest.fixture
def golden_site(
    golden_audit: AuditStamp, golden_period: TimePeriod, golden_address: Address
) -> Site:
    """Fixture providing a complete standard Site instance with NameThing."""
    site_id = SiteID("SID-000001")
    loc_id = LocationID("LOC-000004")
    coords = Coordinates(latitude=Latitude(43.1319), longitude=Longitude(-71.5497))
    hv = HistoricVariant.create(
        raw="Center Burying Ground",
        name="Center Burying Ground",
        historic_name_type=HistoricNameType.COLLOQUIAL,
    )
    name_obj = NameThing.create(
        raw="Old Bow Center Cemetery",
        canonical="Old Bow Center Cemetery",
        aliases=["Town Hall Graveyard"],
        historic=[hv],
    )

    return Site(
        id=site_id,
        audit=golden_audit,
        name=name_obj,
        category=SiteType.CEMETERY,
        canonical_urn="urn:gda:site:us:nh:merrimack:bow:old-bow-center-cemetery",
        location_id=loc_id,
        address=golden_address,
        coordinates=coords,
        period=golden_period,
        is_active=False,
    )


# ==============================================================================
# GROUP 1: SITE CREATION & ATTRIBUTES
# Note: Verification of minimal, complete, and factory creation contracts
# ==============================================================================


@pytest.mark.regression
def test_site_valid_creation_and_alias_equivalence(
    golden_site: Site,
    golden_audit: AuditStamp,
    golden_period: TimePeriod,
    golden_address: Address,
) -> None:
    """Verify Site instantiates with complete attributes and supports backward compatibility alias."""
    site = golden_site
    assert isinstance(site, SiteEntityModel)
    assert site.id == SiteID("SID-000001")
    assert site.audit == golden_audit
    assert site.created_at == golden_audit.created_at
    assert site.updated_at == golden_audit.updated_at
    assert site.name.canonical == "Old Bow Center Cemetery"
    assert site.canonical_name == "Old Bow Center Cemetery"
    assert site.category == SiteType.CEMETERY
    assert site.category == SiteCategory.CEMETERY
    assert site.canonical_urn == "urn:gda:site:us:nh:merrimack:bow:old-bow-center-cemetery"
    assert site.location_id == LocationID("LOC-000004")
    assert site.address == golden_address
    assert site.coordinates is not None
    assert len(site.historical_names) == 1
    assert site.historical_names[0].raw == "Center Burying Ground"
    assert site.aliases == ["Town Hall Graveyard"]
    assert site.alternate_names == ["Town Hall Graveyard"]
    assert site.period == golden_period
    assert site.date_established == golden_period.start_date
    assert site.date_closed == golden_period.end_date
    assert site.is_active is False
    assert site.is_deprecated is False
    assert site.is_dirty is False
    assert str(site) == "Old Bow Center Cemetery [CEMETERY] (SID-000001)"


@pytest.mark.regression
def test_site_defaults(golden_audit: AuditStamp) -> None:
    """Verify Site defaults optional address, coordinates, and collections."""
    site = Site(
        id=SiteID("SID-000002"),
        audit=golden_audit,
        name=NameThing.create(raw="Rural Meetinghouse Marker"),
        category=SiteType.LANDMARK,
        canonical_urn="urn:gda:site:us:nh:bow:meetinghouse-marker",
        location_id=LocationID("LOC-000004"),
    )

    assert site.address is None
    assert site.coordinates is None
    assert site.historical_names == []
    assert site.aliases == []
    assert site.alternate_names == []
    assert site.period is None
    assert site.date_established is None
    assert site.date_closed is None
    assert site.is_active is True
    assert site.is_dirty is False


@pytest.mark.regression
def test_site_factory_create_string_name_and_defaults(golden_audit: AuditStamp) -> None:
    """Verify Site.create accepts string names, enum string tokens, and default values."""
    site = Site.create(
        site_id="SID-000010",
        name="Concord Public Library",
        category="REPOSITORY",
        canonical_urn="urn:gda:site:us:nh:concord:library",
        location_id="LOC-000003",
        audit=golden_audit,
    )
    assert site.id == SiteID("SID-000010")
    assert site.canonical_name == "Concord Public Library"
    assert site.category == SiteType.REPOSITORY
    assert site.location_id == LocationID("LOC-000003")
    assert site.is_active is True
    assert site.is_dirty is False
    assert site.notes == []


@pytest.mark.regression
def test_site_factory_create_with_name_thing_instance(golden_audit: AuditStamp) -> None:
    """Verify Site.create accepts a pre-constructed NameThing instance directly."""
    name_obj = NameThing.create(raw="First Parish Church", canonical="First Parish")
    site = Site.create(
        site_id="SID-000011",
        name=name_obj,
        category=SiteType.CHURCH,
        canonical_urn="urn:gda:site:us:nh:concord:first-parish",
        location_id="LOC-000003",
        audit=golden_audit,
    )
    assert site.name is name_obj
    assert site.canonical_name == "First Parish"


@pytest.mark.regression
def test_site_factory_create_defaults_audit() -> None:
    """Verify Site.create defaults baseline audit stamp when audit is omitted."""
    site = Site.create(
        site_id="SID-000012",
        name="Town Hall",
        category=SiteType.GOVERNMENT,
        canonical_urn="urn:gda:site:us:nh:bow:town-hall",
        location_id="LOC-000004",
    )
    assert site.audit is not None
    assert site.created_at is not None
    assert site.updated_at is not None
    assert site.is_dirty is False


# ==============================================================================
# GROUP 2: COPY-ON-WRITE NAMING & ATTRIBUTE MUTATORS
# Note: Verification of alias, historic variants, and full field mutations
# ==============================================================================


@pytest.mark.regression
def test_site_naming_mutators(golden_site: Site, golden_period: TimePeriod) -> None:
    """Verify Site copy-on-write naming mutators update underlying NameThing."""
    original = golden_site
    assert original.aliases == ["Town Hall Graveyard"]
    assert len(original.historical_names) == 1
    assert original.is_dirty is False

    # add_alias
    with_alias = original.add_alias("Old Bow Burying Ground")
    assert with_alias is not original
    assert "Old Bow Burying Ground" in with_alias.aliases
    assert "Town Hall Graveyard" in with_alias.aliases
    assert with_alias.is_dirty is True

    # remove_alias (and no-op removal)
    with_removed_alias = with_alias.remove_alias("Town Hall Graveyard")
    assert with_removed_alias is not with_alias
    assert "Town Hall Graveyard" not in with_removed_alias.aliases
    assert "Old Bow Burying Ground" in with_removed_alias.aliases
    assert with_removed_alias.remove_alias("NONEXISTENT") is with_removed_alias

    # add_historic_variant
    with_variant = with_removed_alias.add_historic_variant(
        raw="Meetinghouse Hill Cemetery",
        name="Meetinghouse Hill Cemetery",
        historic_name_type=HistoricNameType.COLONIAL,
        valid_period=golden_period,
        comment="Early colonial burial site.",
    )
    assert with_variant is not with_removed_alias
    assert len(with_variant.historical_names) == 2
    assert with_variant.historical_names[1].raw == "Meetinghouse Hill Cemetery"
    assert with_variant.is_dirty is True

    # remove_historic_variant (and no-op removal)
    with_removed_variant = with_variant.remove_historic_variant("Center Burying Ground")
    assert with_removed_variant is not with_variant
    assert len(with_removed_variant.historical_names) == 1
    assert with_removed_variant.historical_names[0].raw == "Meetinghouse Hill Cemetery"
    assert with_removed_variant.remove_historic_variant("NONEXISTENT") is with_removed_variant


@pytest.mark.regression
def test_site_full_field_mutators_and_dirty_flag(
    golden_site: Site, golden_period: TimePeriod, golden_address: Address
) -> None:
    """Verify all domain field mutators update state, touch audit, and toggle dirty flag."""
    site = golden_site
    assert site.is_dirty is False

    # mark_dirty and mark_clean
    marked_dirty = site.mark_dirty()
    assert marked_dirty.is_dirty is True
    assert marked_dirty.mark_dirty() is marked_dirty  # idempotent
    marked_clean = marked_dirty.mark_clean()
    assert marked_clean.is_dirty is False
    assert marked_clean.mark_clean() is marked_clean  # idempotent

    # update_name with NameThing and str
    up_name_thing = site.update_name(NameThing.create(raw="Bow Center Cemetery Modern"))
    assert up_name_thing is not site
    assert up_name_thing.canonical_name == "Bow Center Cemetery Modern"
    assert up_name_thing.is_dirty is True

    up_name_str = site.update_name("Bow Center Memorial Park")
    assert up_name_str is not site
    assert up_name_str.canonical_name == "Bow Center Memorial Park"
    assert up_name_str.is_dirty is True

    # update_category
    up_cat = site.update_category(SiteType.LANDMARK)
    assert up_cat is not site
    assert up_cat.category == SiteType.LANDMARK
    assert up_cat.is_dirty is True

    up_cat_str = site.update_category("CHURCH")
    assert up_cat_str.category == SiteType.CHURCH

    # update_location
    up_loc = site.update_location("LOC-000005")
    assert up_loc is not site
    assert up_loc.location_id == LocationID("LOC-000005")
    assert up_loc.is_dirty is True

    # update_address
    new_addr = golden_address.update_line_1("50 Woodhill Road")
    up_addr = site.update_address(new_addr)
    assert up_addr is not site
    assert up_addr.address == new_addr
    assert up_addr.is_dirty is True

    # update_coordinates
    new_coords = Coordinates(latitude=Latitude(43.2081), longitude=Longitude(-71.5376))
    up_coords = site.update_coordinates(new_coords)
    assert up_coords is not site
    assert up_coords.coordinates == new_coords
    assert up_coords.is_dirty is True

    # update_period
    up_period = site.update_period(golden_period)
    assert up_period is not site
    assert up_period.period == golden_period
    assert up_period.is_dirty is True

    # update_active
    up_active = site.update_active(True)
    assert up_active is not site
    assert up_active.is_active is True
    assert up_active.is_dirty is True

    # update_urn
    up_urn = site.update_urn("urn:gda:site:us:nh:bow:cemetery-updated")
    assert up_urn is not site
    assert up_urn.canonical_urn == "urn:gda:site:us:nh:bow:cemetery-updated"
    assert up_urn.is_dirty is True


@pytest.mark.regression
def test_site_attribute_mutators_defensive_errors(golden_site: Site) -> None:
    """Verify Site attribute mutators enforce domain invariants."""
    site = golden_site

    with pytest.raises(ModelFormatError, match="cannot be empty or whitespace"):
        site.update_name("   ")

    with pytest.raises(TypeError, match="must be an instance of NameThing or str"):
        site.update_name(999)  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="Invalid canonical_urn format"):
        site.update_urn("invalid_urn")


# ==============================================================================
# GROUP 3: EMBEDDED NOTE CONTAINER & UPDATE OPERATIONS
# Note: Verification of inherited EntityLifecycleMixin and update_note mutators
# ==============================================================================


@pytest.mark.regression
def test_site_add_and_delete_embedded_note(golden_site: Site) -> None:
    """Verify Site inherits copy-on-write add_note and delete_note mutators."""
    site = golden_site
    assert site.has_notes is False
    assert site.note_count == 0

    with_note = site.add_note(
        text="Cemetery deed confirmed in Merrimack county records.",
        note_type=NoteType.RESEARCH,
        title="Deed Research",
        tags=["deed", "merrimack"],
    )

    assert with_note is not site
    assert with_note.note_count == 1
    assert with_note.has_notes is True
    assert with_note.canonical_name == site.canonical_name
    assert with_note.notes[0].note_id == NoteID("NOT-000001")
    assert with_note.notes[0].title == "Deed Research"
    assert with_note.updated_at.value >= site.updated_at.value

    deleted = with_note.delete_note("NOT-000001")
    assert deleted is not with_note
    assert deleted.note_count == 0
    assert deleted.has_notes is False


@pytest.mark.regression
def test_site_update_embedded_note(golden_site: Site) -> None:
    """Verify Site update_note mutator modifies note text, title, type, and tags individually."""
    site = golden_site.add_note(
        text="Initial cemetery observation.",
        note_type=NoteType.GENERAL,
        title="Initial",
        tags=["survey"],
    )
    note_id = site.notes[0].note_id

    # Update all fields simultaneously
    updated_all = site.update_note(
        note_id=note_id,
        text="Corrected survey observation.",
        title="Corrected Survey",
        note_type=NoteType.RESEARCH,
        tags=["verified", "headstone"],
    )
    assert updated_all is not site
    assert updated_all.is_dirty is True
    target = updated_all.get_note(note_id)
    assert target is not None
    assert target.text == "Corrected survey observation."
    assert target.title == "Corrected Survey"
    assert target.note_type == NoteType.RESEARCH
    assert target.tags == ["verified", "headstone"]

    # Partial updates: text only
    up_text = site.update_note(note_id=note_id, text="Only text updated")
    assert up_text.get_note(note_id).text == "Only text updated"
    assert up_text.get_note(note_id).title == "Initial"

    # Partial updates: title only
    up_title = site.update_note(note_id=note_id, title="Only title updated")
    assert up_title.get_note(note_id).title == "Only title updated"

    # Partial updates: type only
    up_type = site.update_note(note_id=note_id, note_type=NoteType.PROOF)
    assert up_type.get_note(note_id).note_type == NoteType.PROOF

    # Partial updates: tags only
    up_tags = site.update_note(note_id=note_id, tags=["new_tag"])
    assert up_tags.get_note(note_id).tags == ["new_tag"]

    # No-op when note_id is absent
    assert site.update_note(note_id="NOT-999999", text="No-op") is site


@pytest.mark.regression
def test_site_find_notes_filtering_and_sorting(
    golden_site: Site, six_note_bundle: list[Note]
) -> None:
    """Verify Site searches and sorts across embedded notes."""
    site = Site(
        id=golden_site.id,
        audit=golden_site.audit,
        name=golden_site.name,
        category=golden_site.category,
        canonical_urn=golden_site.canonical_urn,
        location_id=golden_site.location_id,
        notes=six_note_bundle,
    )

    assert site.note_count == 6
    assert len(site.find_notes(note_type=NoteType.RESEARCH)) == 3
    assert len(site.find_notes(note_type=NoteType.DISCREPANCY)) == 2
    assert len(site.find_notes(note_type=NoteType.PROOF)) == 1

    sorted_by_title = site.find_notes(sort_by="title")
    assert sorted_by_title[0].title == "Birth Year Conflict"
    assert sorted_by_title[-1].title == "Surname Spelling Variance"


# ==============================================================================
# GROUP 4: DEFENSIVE BOUNDARIES & VALIDATIONS
# Note: Verification of validation rules, ID regex, and type safety
# ==============================================================================


@pytest.mark.regression
@pytest.mark.parametrize(
    "bad_id_str",
    [
        "SID-12345",
        "SID-1234567",
        "SID-ABCDEF",
        "000001",
        "",
    ],
)
def test_site_invalid_site_id_raises_format_error(
    bad_id_str: str, golden_audit: AuditStamp
) -> None:
    """Verify malformed SiteID values raise ModelFormatError when constructed."""
    try:
        bad_id = SiteID(bad_id_str)
        with pytest.raises(ModelFormatError, match="Invalid SiteID format"):
            Site(
                id=bad_id,
                audit=golden_audit,
                name=NameThing.create(raw="Invalid ID Site"),
                category=SiteType.LANDMARK,
                canonical_urn="urn:gda:site:us:nh:bow:invalid",
                location_id=LocationID("LOC-000004"),
            )
    except ModelFormatError:
        pass


@pytest.mark.regression
def test_site_conflicting_atom_id_type_raises_error(golden_audit: AuditStamp) -> None:
    """Verify Site rejects foreign AtomID subclasses assigned to id."""
    wrong_id = FactID("FID-000001")
    with pytest.raises((TypeError, ValidationError)):
        Site(
            id=wrong_id,  # type: ignore[arg-type]
            audit=golden_audit,
            name=NameThing.create(raw="Wrong ID Site"),
            category=SiteType.LANDMARK,
            canonical_urn="urn:gda:site:us:nh:bow:wrong",
            location_id=LocationID("LOC-000004"),
        )


@pytest.mark.regression
def test_site_foreign_location_id_type_raises_error(golden_audit: AuditStamp) -> None:
    """Verify Site rejects foreign AtomID subclasses assigned to location_id."""
    wrong_loc = FactID("FID-000001")
    with pytest.raises(ValidationError):
        Site(
            id=SiteID("SID-000001"),
            audit=golden_audit,
            name=NameThing.create(raw="Wrong Loc Site"),
            category=SiteType.LANDMARK,
            canonical_urn="urn:gda:site:us:nh:bow:site",
            location_id=wrong_loc,  # type: ignore[arg-type]
        )


@pytest.mark.regression
def test_site_invalid_name_type_raises_error(golden_audit: AuditStamp) -> None:
    """Verify Site constructor rejects non-NameThing instances assigned to name."""
    with pytest.raises((TypeError, ValidationError)):
        Site(
            id=SiteID("SID-000001"),
            audit=golden_audit,
            name="Raw String Not Allowed In Direct Constructor",  # type: ignore[arg-type]
            category=SiteType.LANDMARK,
            canonical_urn="urn:gda:site:us:nh:bow:site",
            location_id=LocationID("LOC-000004"),
        )

    with pytest.raises(TypeError, match="must be an instance of NameThing or str"):
        Site.create(
            site_id=SiteID("SID-000001"),
            audit=golden_audit,
            name=12345,  # type: ignore[arg-type]
            category=SiteType.LANDMARK,
            canonical_urn="urn:gda:site:us:nh:bow:site",
            location_id=LocationID("LOC-000004"),
        )


@pytest.mark.regression
@pytest.mark.parametrize("blank_name", ["", "   ", "\t\n"])
def test_site_blank_name_raises_format_error(blank_name: str, golden_audit: AuditStamp) -> None:
    """Verify Site.create raises ModelFormatError if name is blank."""
    with pytest.raises(ModelFormatError, match="Site 'name' cannot be empty or whitespace"):
        Site.create(
            site_id=SiteID("SID-000001"),
            audit=golden_audit,
            name=blank_name,
            category=SiteType.LANDMARK,
            canonical_urn="urn:gda:site:us:nh:bow:site",
            location_id=LocationID("LOC-000004"),
        )


@pytest.mark.regression
@pytest.mark.parametrize(
    "invalid_urn",
    [
        "",
        "   ",
        "urn:gda:loc:us:nh:bow",
        "urn:site:us:nh:bow",
        "URN:GDA:SITE:US:NH",
        "urn:gda:site:invalid space",
    ],
)
def test_site_invalid_urn_raises_format_error(invalid_urn: str, golden_audit: AuditStamp) -> None:
    """Verify Site raises ModelFormatError when canonical_urn is malformed."""
    with pytest.raises(ModelFormatError, match="Invalid canonical_urn format"):
        Site(
            id=SiteID("SID-000001"),
            audit=golden_audit,
            name=NameThing.create(raw="Valid Site"),
            category=SiteType.LANDMARK,
            canonical_urn=invalid_urn,
            location_id=LocationID("LOC-000004"),
        )


@pytest.mark.regression
def test_site_tombstone_self_superseded_raises_error(
    golden_audit: AuditStamp, golden_timestamp: IsoTimestamp
) -> None:
    """Verify Site rejects a tombstone where superseded_by points to itself."""
    site_id = SiteID("SID-000001")
    tombstone = Tombstone(
        is_deprecated=True,
        deprecated_at=golden_timestamp,
        superseded_by=site_id,
    )
    with pytest.raises(ModelFormatError, match="cannot be superseded by itself"):
        Site(
            id=site_id,
            audit=golden_audit,
            name=NameThing.create(raw="Demolished Site"),
            category=SiteType.LANDMARK,
            canonical_urn="urn:gda:site:us:nh:bow:demolished",
            location_id=LocationID("LOC-000004"),
            tombstone=tombstone,
        )


@pytest.mark.regression
def test_site_lifecycle_deprecate_and_restore(golden_site: Site) -> None:
    """Verify Site executes soft-deprecation and restoration lifecycles."""
    site = golden_site
    assert site.is_deprecated is False

    deprecated = site.deprecate(superseded_by=SiteID("SID-000099"))
    assert deprecated.is_deprecated is True
    assert deprecated.superseded_by == SiteID("SID-000099")

    restored = deprecated.restore()
    assert restored.is_deprecated is False
    assert restored.superseded_by is None


# ==============================================================================
# GROUP 5: IMMUTABILITY & INTROSPECTION
# Note: Verification of frozen immutability and introspection directory
# ==============================================================================


@pytest.mark.regression
def test_site_immutability(golden_site: Site) -> None:
    """Verify Site instances are frozen and immutable."""
    with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
        golden_site.name = NameThing.create(raw="Renamed Landmark")  # type: ignore[misc]

    with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
        golden_site.canonical_urn = "urn:gda:site:us:nh:bow:mutated"  # type: ignore[misc]


@pytest.mark.regression
def test_site_introspection(golden_site: Site) -> None:
    """Verify .help() introspection renders member directory on Site."""
    help_text = golden_site.help(as_str=True)
    assert help_text is not None
    assert "=== Site Public Directory ===" in help_text
    assert "add_note" in help_text
    assert "update_note" in help_text
    assert "delete_note" in help_text
    assert "find_notes" in help_text
    assert "add_alias" in help_text
    assert "remove_alias" in help_text
    assert "add_historic_variant" in help_text
    assert "remove_historic_variant" in help_text
    assert "update_name" in help_text
    assert "update_category" in help_text
    assert "update_location" in help_text
    assert "update_address" in help_text
    assert "update_coordinates" in help_text
    assert "update_period" in help_text
    assert "update_active" in help_text
    assert "update_urn" in help_text
    assert "mark_dirty" in help_text
    assert "mark_clean" in help_text
    assert "is_dirty" in help_text
    assert "date_established" in help_text
    assert "date_closed" in help_text
