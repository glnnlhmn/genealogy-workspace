"""Path: tests/test_gda/test_model/test_entity/test_entity_site.py

Comprehensive test suite verifying Site entity contracts and mutators.

Operational Role:
    Verifies Site behavioral contracts, BaseEntity inheritance, foreign key
    LocationID validation, URN formatting, optional address/coordinate composition,
    NameThing integration, copy-on-write naming and field mutators, embedded note
    management, serialization round trips, dirty tracking (_dirty, is_dirty, mark_clean, mark_dirty),
    and immutability invariants with 100% statement and branch coverage.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest
from pydantic import ValidationError

from gda.core.enums.archival import NoteType
from gda.core.enums.site import SiteType
from gda.core.enums.vital import HistoricNameType
from gda.core.errors import ModelFormatError
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.geo import Latitude, Longitude
from gda.model.atom.id import FactID, LocationID, NoteID, SiteID
from gda.model.base.address import Address
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate, TimePeriod
from gda.model.base.geo import Coordinates
from gda.model.base.name import NameThing
from gda.model.base.note import Note
from gda.model.base.tombstone import Tombstone
from gda.model.entity.site import Site, SiteEntityModel

__version__ = "1.0.0+build.4"


# ==============================================================================
# FIXTURES: GOLDEN PAYLOADS & BASE INSTANCES
# ==============================================================================


# ==============================================================================
# GROUP 1: SITE CREATION & ATTRIBUTES
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
    assert "Site(" in repr(site)


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
# ==============================================================================


@pytest.mark.regression
def test_site_naming_mutators(golden_site: Site, golden_period: TimePeriod) -> None:
    """Verify Site copy-on-write naming mutators update underlying NameThing."""
    original = golden_site
    assert original.aliases == ["Town Hall Graveyard"]
    assert len(original.historical_names) == 1
    assert original.is_dirty is False

    with_alias = original.add_alias("Old Bow Burying Ground")
    assert with_alias is not original
    assert "Old Bow Burying Ground" in with_alias.aliases
    assert "Town Hall Graveyard" in with_alias.aliases
    assert with_alias.is_dirty is True
    assert with_alias.add_alias("Old Bow Burying Ground") is with_alias

    with_removed_alias = with_alias.remove_alias("Town Hall Graveyard")
    assert with_removed_alias is not with_alias
    assert "Town Hall Graveyard" not in with_removed_alias.aliases
    assert "Old Bow Burying Ground" in with_removed_alias.aliases
    assert with_removed_alias.remove_alias("NONEXISTENT") is with_removed_alias

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

    with_removed_variant = with_variant.remove_historic_variant("Center Burying Ground")
    assert with_removed_variant is not with_variant
    assert len(with_removed_variant.historical_names) == 1
    assert with_removed_variant.historical_names[0].raw == "Meetinghouse Hill Cemetery"
    assert with_removed_variant.remove_historic_variant("NONEXISTENT") is with_removed_variant


@pytest.mark.regression
def test_site_full_field_mutators_and_dirty_flag(
    golden_site: Site, golden_address: Address
) -> None:
    """Verify all domain field mutators update state, touch audit, and toggle dirty flag."""
    site = golden_site
    assert site.is_dirty is False

    marked_dirty = site.mark_dirty()
    assert marked_dirty.is_dirty is True
    assert marked_dirty.mark_dirty() is marked_dirty
    marked_clean = marked_dirty.mark_clean()
    assert marked_clean.is_dirty is False
    assert marked_clean.mark_clean() is marked_clean

    up_name_thing = site.update_name(NameThing.create(raw="Bow Center Cemetery Modern"))
    assert up_name_thing is not site
    assert up_name_thing.canonical_name == "Bow Center Cemetery Modern"
    assert up_name_thing.is_dirty is True
    assert up_name_thing.update_name(up_name_thing.name) is up_name_thing

    up_name_str = site.update_name("Bow Center Memorial Park")
    assert up_name_str is not site
    assert up_name_str.canonical_name == "Bow Center Memorial Park"
    assert up_name_str.is_dirty is True

    up_cat = site.update_category(SiteType.LANDMARK)
    assert up_cat is not site
    assert up_cat.category == SiteType.LANDMARK
    assert up_cat.is_dirty is True
    assert up_cat.update_category(SiteType.LANDMARK) is up_cat

    up_cat_str = site.update_category("CHURCH")
    assert up_cat_str.category == SiteType.CHURCH

    up_loc = site.update_location("LOC-000005")
    assert up_loc is not site
    assert up_loc.location_id == LocationID("LOC-000005")
    assert up_loc.is_dirty is True
    assert up_loc.update_location("LOC-000005") is up_loc

    new_addr = golden_address.update_line_1("50 Woodhill Road")
    up_addr = site.update_address(new_addr)
    assert up_addr is not site
    assert up_addr.address == new_addr
    assert up_addr.is_dirty is True
    assert up_addr.update_address(new_addr) is up_addr

    new_coords = Coordinates(latitude=Latitude(43.2081), longitude=Longitude(-71.5376))
    up_coords = site.update_coordinates(new_coords)
    assert up_coords is not site
    assert up_coords.coordinates == new_coords
    assert up_coords.is_dirty is True
    assert up_coords.update_coordinates(new_coords) is up_coords

    new_period = TimePeriod(start_date=EventDate.create("1750"))
    up_period = site.update_period(new_period)
    assert up_period is not site
    assert up_period.period == new_period
    assert up_period.is_dirty is True
    assert up_period.update_period(new_period) is up_period

    up_active = site.update_active(True)
    assert up_active is not site
    assert up_active.is_active is True
    assert up_active.is_dirty is True
    assert up_active.update_active(True) is up_active

    up_urn = site.update_urn("urn:gda:site:us:nh:bow:cemetery-updated")
    assert up_urn is not site
    assert up_urn.canonical_urn == "urn:gda:site:us:nh:bow:cemetery-updated"
    assert up_urn.is_dirty is True
    assert up_urn.update_urn("urn:gda:site:us:nh:bow:cemetery-updated") is up_urn


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
    """Verify Site update_note mutator modifies embedded notes and toggles dirty flag."""
    site = golden_site.add_note(
        text="Initial cemetery observation.",
        note_type=NoteType.GENERAL,
        title="Initial",
        tags=["survey"],
    )
    note_id = site.notes[0].note_id

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
    assert sorted_by_title[-1].title == "Tax Assessment"


# ==============================================================================
# GROUP 4: SERIALIZATION & ROUND TRIPS
# ==============================================================================


@pytest.mark.integration
def test_site_serialization_round_trip(golden_site: Site) -> None:
    """Verify Site dictionary and JSON serialization round trips."""
    site = golden_site.add_note(
        text="Monument inscription verified.",
        title="Inscription",
        note_type=NoteType.RESEARCH,
    )
    data = site.to_dict()

    assert data["id"] == "SID-000001"
    assert data["category"] == "CEMETERY"
    assert data["canonical_urn"] == "urn:gda:site:us:nh:merrimack:bow:old-bow-center-cemetery"
    assert data["location_id"] == "LOC-000004"
    assert data["is_active"] is False
    assert "address" in data
    assert "coordinates" in data
    assert "period" in data
    assert len(data["notes"]) == 1

    restored = Site.from_dict(data)
    assert restored.id == site.id
    assert restored.canonical_name == site.canonical_name
    assert restored.category == site.category
    assert restored.location_id == site.location_id
    assert restored.address == site.address
    assert restored.coordinates == site.coordinates
    assert restored.period == site.period
    assert restored.note_count == 1

    json_str = site.to_json()
    assert "SID-000001" in json_str
    assert "CEMETERY" in json_str

    restored_json = Site.from_json(json_str)
    assert restored_json.id == site.id
    assert restored_json.canonical_name == site.canonical_name


@pytest.mark.integration
def test_site_from_dict_minimal_and_string_name(
    golden_audit: AuditStamp, golden_period: TimePeriod, golden_address: Address
) -> None:
    """Verify Site.from_dict parses minimal dictionary payload, tombstones, and instances."""
    data = {
        "id": "SID-000050",
        "name": "Meetinghouse Marker",
        "category": "LANDMARK",
        "canonical_urn": "urn:gda:site:us:nh:bow:marker",
        "location_id": "LOC-000004",
    }
    restored = Site.from_dict(data)
    assert restored.id == SiteID("SID-000050")
    assert restored.canonical_name == "Meetinghouse Marker"
    assert restored.category == SiteType.LANDMARK
    assert restored.location_id == LocationID("LOC-000004")
    assert restored.address is None
    assert restored.coordinates is None
    assert restored.period is None
    assert restored.is_active is True
    assert restored.is_deprecated is False

    data_min = restored.to_dict()
    assert "address" not in data_min
    assert "coordinates" not in data_min
    assert "period" not in data_min

    coords = Coordinates(latitude=Latitude(43.0), longitude=Longitude(-71.0))
    data_with_instances = {
        **data,
        "address": golden_address,
        "period": golden_period,
        "coordinates": coords,
        "tombstone": {
            "is_deprecated": True,
            "deprecated_at": str(golden_audit.updated_at),
            "superseded_by": "SID-000051",
        },
    }
    restored_inst = Site.from_dict(data_with_instances)
    assert restored_inst.address == golden_address
    assert restored_inst.coordinates == coords
    assert restored_inst.period == golden_period
    assert restored_inst.is_deprecated is True
    assert restored_inst.superseded_by == SiteID("SID-000051")
    assert restored_inst.to_dict()["tombstone"]["superseded_by"] == "SID-000051"

    restored_empty_period = Site.from_dict(
        {
            **data,
            "period": {},
            "tombstone": {
                "is_deprecated": True,
                "deprecated_at": str(golden_audit.updated_at),
            },
        }
    )
    assert restored_empty_period.period is None
    assert restored_empty_period.superseded_by is None


@pytest.mark.regression
def test_site_deserialization_defensive_errors() -> None:
    """Verify Site.from_dict and from_json reject malformed payloads."""
    with pytest.raises(ModelFormatError, match="must be a dictionary"):
        Site.from_dict("not-a-dict")  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="Missing required field 'id'"):
        Site.from_dict({"name": "Site", "category": "CEMETERY", "location_id": "LOC-000001"})

    with pytest.raises(ModelFormatError, match="Missing required field 'name'"):
        Site.from_dict({"id": "SID-000001", "category": "CEMETERY", "location_id": "LOC-000001"})

    with pytest.raises(ModelFormatError, match="Missing required field 'category'"):
        Site.from_dict({"id": "SID-000001", "name": "Site", "location_id": "LOC-000001"})

    with pytest.raises(ModelFormatError, match="Missing required field 'location_id'"):
        Site.from_dict({"id": "SID-000001", "name": "Site", "category": "CEMETERY"})

    with pytest.raises(ModelFormatError, match="Failed to parse Site JSON string"):
        Site.from_json("{broken json")


# ==============================================================================
# GROUP 5: DEFENSIVE BOUNDARIES & VALIDATIONS
# ==============================================================================


@pytest.mark.regression
@pytest.mark.parametrize(
    "bad_id_str",
    [
        "SID-12345",
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
def test_site_post_init_defensive_branches(golden_site: Site) -> None:
    """Verify Site.__post_init__ defensive checks for id type, pattern, and untrimmed URN."""
    object.__setattr__(golden_site, "canonical_urn", "  urn:gda:site:us:nh:bow:cemetery  ")
    golden_site.__post_init__()
    assert golden_site.canonical_urn == "urn:gda:site:us:nh:bow:cemetery"

    class MalformedSiteID(SiteID):
        """Subclass bypassing AtomID.__post_init__ regex enforcement."""

        def __init__(self, value: str) -> None:
            object.__setattr__(self, "value", value)
            object.__setattr__(self, "expected_prefix", "SID")

    object.__setattr__(golden_site, "id", MalformedSiteID("SID-12"))
    with pytest.raises(ModelFormatError, match="Invalid SiteID format"):
        golden_site.__post_init__()

    object.__setattr__(golden_site, "id", "NOT_A_SITE_ID")
    with pytest.raises(TypeError, match="must be an instance of SiteID"):
        golden_site.__post_init__()


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
# GROUP 6: IMMUTABILITY & INTROSPECTION
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
    assert "to_dict" in help_text
    assert "from_dict" in help_text
    assert "to_json" in help_text
    assert "from_json" in help_text
    assert "mark_dirty" in help_text
    assert "mark_clean" in help_text
    assert "is_dirty" in help_text
    assert "date_established" in help_text
    assert "date_closed" in help_text
