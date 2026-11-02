"""Path: tests/test_gda/test_db/test_mapper.py

Atomized unit, regression, and round-trip verification test suite for EntityRowMappers.

Validates bidirectional serialization/deserialization across Location, Site,
Individual, Family, and Fact entities, defensive error translation on corrupt rows,
IntrospectableMixin public directory discovery, and full branch coverage.
"""

from __future__ import annotations

import pytest

from gda.db.exceptions import EntityMappingError
from gda.db.mapper import (
    FactRowMapper,
    FamilyRowMapper,
    IndividualRowMapper,
    LocationRowMapper,
    SiteRowMapper,
    _extract_id_str,
    _extract_year_from_text,
    get_mapper,
)
from gda.enums.archival import NoteType
from gda.enums.core import AssociatedRole, FactType
from gda.enums.vital import PedigreeType
from gda.model.atom.date import (
    DateModifier,
    DateString,
    EventDate,
    EventDateRange,
    IsoTimestamp,
)
from gda.model.atom.geo import Coordinates, Latitude, Longitude
from gda.model.atom.id import FactID, FamilyID, IndividualID, LocationID, SiteID
from gda.model.base.address import Address
from gda.model.base.audit import AuditStamp
from gda.model.base.name import HistoricVariant, NameThing
from gda.model.base.note import Note
from gda.model.base.source import SourceReference
from gda.model.base.time_period import TimePeriod
from gda.model.base.tombstone import Tombstone
from gda.model.entity.fact import Fact, FactParticipant
from gda.model.entity.family import Family
from gda.model.entity.individual import Individual
from gda.model.entity.location import JurisdictionCategory, Location
from gda.model.entity.site import Site, SiteCategory

__version__ = "1.0.0+build.20"


def _make_audit() -> AuditStamp:
    now = IsoTimestamp("2026-01-01T00:00:00Z")
    return AuditStamp(created_at=now, updated_at=now)


# ==============================================================================
# GROUP 1: MAPPER REGISTRY, HELPERS & INTROSPECTION CONTRACTS
# ==============================================================================


@pytest.mark.regression
def test_mapper_registry_resolves_all_core_entities() -> None:
    """Verify get_mapper resolves mapper instances for all 5 core entity classes."""
    assert isinstance(get_mapper(Location), LocationRowMapper)
    assert isinstance(get_mapper(Site), SiteRowMapper)
    assert isinstance(get_mapper(Individual), IndividualRowMapper)
    assert isinstance(get_mapper(Family), FamilyRowMapper)
    assert isinstance(get_mapper(Fact), FactRowMapper)


@pytest.mark.regression
def test_base_row_mapper_model_cls_property() -> None:
    """Verify BaseRowMapper exposes the bound domain model class."""
    mapper = LocationRowMapper()
    assert mapper.model_cls is Location


@pytest.mark.regression
def test_extract_id_str_utility_branches() -> None:
    """Verify _extract_id_str handles None, str, dict, AtomID, and other values."""
    assert _extract_id_str(None) is None
    assert _extract_id_str("LOC-000001") == "LOC-000001"
    assert _extract_id_str({"value": "LOC-000002"}) == "LOC-000002"
    assert _extract_id_str(LocationID("LOC-000003")) == "LOC-000003"
    assert _extract_id_str(12345) == "12345"


@pytest.mark.regression
def test_extract_year_from_text_utility() -> None:
    """Verify _extract_year_from_text parsing."""
    assert _extract_year_from_text(None) is None
    assert _extract_year_from_text("") is None
    assert _extract_year_from_text("Born in 1865 in NH") == 1865
    assert _extract_year_from_text("Circa 1905") == 1905
    assert _extract_year_from_text("Undated") is None


@pytest.mark.regression
def test_mapper_registry_unknown_class_raises_entity_mapping_error() -> None:
    """Verify requesting an unregistered class raises EntityMappingError."""

    class DummyEntity:
        pass

    with pytest.raises(EntityMappingError, match="No registered row mapper"):
        get_mapper(DummyEntity)  # type: ignore[arg-type]


@pytest.mark.regression
def test_mapper_introspectable_help() -> None:
    """Verify IntrospectableMixin .help() produces directory output."""
    mapper = LocationRowMapper()
    help_doc = mapper.help(as_str=True)
    assert help_doc is not None
    assert "LocationRowMapper" in help_doc
    assert "to_row" in help_doc
    assert "from_row" in help_doc


# ==============================================================================
# GROUP 2: LOCATION ROUND-TRIP SERIALIZATION
# ==============================================================================


@pytest.mark.integration
def test_location_mapper_round_trip() -> None:
    """Verify Location serializes to row params and round-trips without loss."""
    audit = _make_audit()
    coords = Coordinates(latitude=Latitude(43.13), longitude=Longitude(-71.53))
    period = TimePeriod(
        start_date=EventDate(date=DateString("1727-05-20")),
        end_date=EventDate(date=DateString("1900-01-01")),
    )
    note = Note.create(
        note_id="NOT-000001",
        note_type=NoteType.RESEARCH,
        text="Settlement founded 1727",
    )
    name_obj = NameThing.create(
        raw="Bow",
        canonical="Bow",
        aliases=["Bow Mills"],
        historic=[HistoricVariant.create(raw="Bow Town", name="Bow Town")],
    )
    loc = Location.create(
        location_id="LOC-000001",
        canonical_urn="urn:gda:loc:us:nh:bow",
        name=name_obj,
        category=JurisdictionCategory.MUNICIPALITY,
        parent_id="LOC-000002",
        is_primary_local_authority=True,
        is_unincorporated=False,
        coordinates=coords,
        period=period,
        predecessor_ids=["LOC-000004"],
        successor_ids=["LOC-000005"],
        audit=audit,
        tombstone=Tombstone(is_deprecated=False),
        notes=[note],
    )

    mapper = get_mapper(Location)
    row_data = mapper.to_row(loc)

    assert row_data["id"] == "LOC-000001"
    assert row_data["canonical_urn"] == "urn:gda:loc:us:nh:bow"
    assert row_data["name"] == "Bow"
    assert row_data["category"] == "MUNICIPALITY"
    assert row_data["parent_id"] == "LOC-000002"
    assert row_data["is_primary_local_authority"] == 1
    assert row_data["is_unincorporated"] == 0

    restored = mapper.from_row(row_data)
    assert restored.id == loc.id
    assert restored.name.canonical == loc.name.canonical
    assert restored.note_count == 1


@pytest.mark.regression
def test_location_mapper_corrupt_row_raises_error() -> None:
    """Verify LocationRowMapper raises EntityMappingError on invalid data."""
    mapper = get_mapper(Location)
    with pytest.raises(EntityMappingError, match="Failed to map row to Location"):
        mapper.from_row({"id": None})


# ==============================================================================
# GROUP 3: SITE ROUND-TRIP SERIALIZATION
# ==============================================================================


@pytest.mark.integration
def test_site_mapper_round_trip() -> None:
    """Verify Site serializes to row params and round-trips without loss."""
    audit = _make_audit()
    addr = Address(address_line_1="10 Woodhill Hook Rd", postal_code="03304")
    site = Site.create(
        site_id="SID-000001",
        canonical_urn="urn:gda:site:us:nh:bow:cemetery",
        name="Old Bow Cemetery",
        category=SiteCategory.CEMETERY,
        location_id="LOC-000001",
        is_active=False,
        address=addr,
        audit=audit,
        tombstone=Tombstone(
            is_deprecated=True,
            deprecated_at=audit.updated_at,
            superseded_by=SiteID("SID-000002"),
        ),
    )

    mapper = get_mapper(Site)
    row_data = mapper.to_row(site)

    assert row_data["id"] == "SID-000001"
    assert row_data["category"] == "CEMETERY"
    assert row_data["is_active"] == 0
    assert row_data["is_deprecated"] == 1
    assert row_data["superseded_by"] == "SID-000002"

    restored = mapper.from_row(row_data)
    assert restored.id == site.id
    assert restored.is_deprecated is True


@pytest.mark.regression
def test_site_mapper_corrupt_row_raises_error() -> None:
    """Verify SiteRowMapper raises EntityMappingError on invalid data."""
    mapper = get_mapper(Site)
    with pytest.raises(EntityMappingError, match="Failed to map row to Site"):
        mapper.from_row({"id": None})


# ==============================================================================
# GROUP 4: INDIVIDUAL ROUND-TRIP SERIALIZATION
# ==============================================================================


@pytest.mark.integration
def test_individual_mapper_round_trip() -> None:
    """Verify Individual serializes and round-trips correctly."""
    audit = _make_audit()
    ind = Individual.create(
        individual_id="IND-000001",
        canonical_urn="urn:gda:ind:smith_john",
        name="John Smith",
        birth_date="1850-01-01",
        birth_place_id="LOC-000001",
        death_date="1920-11-04",
        death_place_id="LOC-000002",
        is_deceased=True,
        audit=audit,
        tombstone=Tombstone(
            is_deprecated=True,
            deprecated_at=audit.updated_at,
            superseded_by=IndividualID("IND-000002"),
        ),
    )

    mapper = get_mapper(Individual)
    row_data = mapper.to_row(ind)

    assert row_data["id"] == "IND-000001"
    assert row_data["birth_year"] == 1850
    assert row_data["birth_date_sort"] == "1850-01-01"
    assert row_data["death_year"] == 1920
    assert row_data["is_deprecated"] == 1
    assert row_data["superseded_by"] == "IND-000002"

    restored = mapper.from_row(row_data)
    assert restored.id == ind.id
    assert restored.birth_year == 1850
    assert restored.death_year == 1920
    assert restored.is_deprecated is True


@pytest.mark.integration
def test_individual_mapper_with_start_date_range_and_site_places() -> None:
    """Verify Individual with EventDateRange birth date and SiteID birth place."""
    audit = _make_audit()
    b_range = EventDateRange(
        start_date=EventDate.create("1850-01-01"),
        end_date=EventDate.create("1850-12-31"),
        modifier=DateModifier.BETWEEN,
    )
    ind = Individual.create(
        individual_id="IND-000005",
        canonical_urn="urn:gda:ind:jane_smith_1850",
        name="Jane Smith",
        gender="F",
        birth_date=b_range,
        birth_place_id="SID-000005",
        audit=audit,
    )

    mapper = get_mapper(Individual)
    row_data = mapper.to_row(ind)
    assert row_data["birth_year"] == 1850
    assert row_data["birth_place_id"] == "SID-000005"

    restored = mapper.from_row(row_data)
    assert restored.id == ind.id
    assert restored.birth_year == 1850


@pytest.mark.integration
def test_individual_mapper_without_birth_or_death_dates() -> None:
    """Verify Individual without birth or death dates sets null query projections."""
    audit = _make_audit()
    ind = Individual.create(
        individual_id="IND-000006",
        canonical_urn="urn:gda:ind:undated_person",
        name="Undated Person",
        audit=audit,
    )

    mapper = get_mapper(Individual)
    row_data = mapper.to_row(ind)
    assert row_data["birth_year"] is None
    assert row_data["birth_date_sort"] is None
    assert row_data["death_year"] is None
    assert row_data["death_date_sort"] is None

    restored = mapper.from_row(row_data)
    assert restored.id == ind.id
    assert restored.birth_date is None
    assert restored.death_date is None


@pytest.mark.regression
def test_individual_mapper_corrupt_row_raises_error() -> None:
    """Verify IndividualRowMapper raises EntityMappingError on invalid data."""
    mapper = get_mapper(Individual)
    with pytest.raises(EntityMappingError, match="Failed to map row to Individual"):
        mapper.from_row({"id": None})


# ==============================================================================
# GROUP 5: FAMILY ROUND-TRIP SERIALIZATION
# ==============================================================================


@pytest.mark.integration
def test_family_mapper_round_trip() -> None:
    """Verify Family serializes and round-trips correctly."""
    audit = _make_audit()
    fam = Family.create(
        family_id="FAM-000001",
        canonical_urn="urn:gda:fam:smith_jones",
        partner_ids=["IND-000001", "IND-000002"],
        children=[("IND-000003", PedigreeType.BIRTH)],
        audit=audit,
    )

    mapper = get_mapper(Family)
    row_data = mapper.to_row(fam)

    assert row_data["id"] == "FAM-000001"
    assert "IND-000001" in row_data["partner_ids_json"]

    restored = mapper.from_row(row_data)
    assert restored.id == fam.id
    assert restored.partner_count == 2
    assert restored.child_count == 1


@pytest.mark.regression
def test_family_mapper_corrupt_row_raises_error() -> None:
    """Verify FamilyRowMapper raises EntityMappingError on invalid data."""
    mapper = get_mapper(Family)
    with pytest.raises(EntityMappingError, match="Failed to map row to Family"):
        mapper.from_row({"id": None})


# ==============================================================================
# GROUP 6: FACT ROUND-TRIP SERIALIZATION, DATES & CITATIONS
# ==============================================================================


@pytest.mark.integration
def test_fact_mapper_round_trip_with_participants_and_citations() -> None:
    """Verify Fact serializes participants/citations and round-trips without loss."""
    audit = _make_audit()
    cite = SourceReference.create("Town Marriage Records, Vol 1, p. 42")
    part = FactParticipant.create("IND-000002", AssociatedRole.SPOUSE)

    fact = Fact.create(
        fact_id="FID-000001",
        canonical_urn="urn:gda:fact:smith_marriage_1865",
        fact_type=FactType.MARRIAGE,
        title="Marriage Ceremony",
        primary_subject_id="IND-000001",
        date="1865-06-15",
        location_id="LOC-000001",
        site_id="SID-000001",
        value="Ceremony solemnized by Rev. Smith",
        participants=[part],
        citations=[cite],
        audit=audit,
        tombstone=Tombstone(
            is_deprecated=True,
            deprecated_at=audit.updated_at,
            superseded_by=FactID("FID-000002"),
        ),
    )

    mapper = get_mapper(Fact)
    row_data = mapper.to_row(fact)

    assert row_data["fact_year"] == 1865
    assert row_data["fact_date_sort"] == "1865-06-15"
    assert row_data["fact_type"] == "MARRIAGE"
    assert row_data["site_id"] == "SID-000001"
    assert row_data["superseded_by"] == "FID-000002"

    restored = mapper.from_row(row_data)
    assert restored.id == fact.id
    assert restored.is_deprecated is True
    assert restored.participant_count == 1
    assert restored.citation_count == 1


@pytest.mark.integration
def test_fact_mapper_family_subject_and_start_date_branch() -> None:
    """Verify Fact with FamilyID as primary_subject_id and TimePeriod date."""
    audit = _make_audit()
    period = TimePeriod(
        start_date=EventDate.create("1880-06-01"),
        end_date=EventDate.create("1880-06-30"),
    )
    fact = Fact.create(
        fact_id="FID-000002",
        canonical_urn="urn:gda:fact:census_1880",
        fact_type=FactType.CENSUS,
        title="1880 Federal Census",
        primary_subject_id="FAM-000001",
        date=period,
        site_id="SID-000002",
        audit=audit,
    )

    mapper = get_mapper(Fact)
    row_data = mapper.to_row(fact)
    assert row_data["primary_subject_id"] == "FAM-000001"
    assert row_data["fact_year"] == 1880

    restored = mapper.from_row(row_data)
    assert restored.id == fact.id
    assert restored.primary_subject_id == FamilyID("FAM-000001")


@pytest.mark.regression
def test_fact_mapper_corrupt_row_raises_error() -> None:
    """Verify FactRowMapper raises EntityMappingError on invalid data."""
    mapper = get_mapper(Fact)
    with pytest.raises(EntityMappingError, match="Failed to map row to Fact"):
        mapper.from_row({"id": None})
