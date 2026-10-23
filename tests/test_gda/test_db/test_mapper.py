"""Path: tests/test_gda/test_db/test_mapper.py

Atomized unit, regression, and round-trip verification test suite for EntityRowMappers.

Validates bidirectional serialization/deserialization across Location, Site,
Individual, Family, and Fact entities, defensive error translation on corrupt rows,
IntrospectableMixin public directory discovery, and full 100% branch coverage.
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
    get_mapper,
)
from gda.enums.core import AssociatedRole, FactType
from gda.enums.vital import PedigreeType, UnionType
from gda.model.atom.date import (
    DateModifier,
    DateString,
    EventDate,
    EventDateRange,
    IsoTimestamp,
)
from gda.model.atom.geo import Coordinates, Latitude, Longitude
from gda.model.atom.id import FactID, FamilyID, IndividualID, LocationID, NoteID, SiteID
from gda.model.base.address import Address
from gda.model.base.audit import AuditStamp
from gda.model.base.family import ChildLink, FamilyUnion
from gda.model.base.name import CanonicalName, HistoricalName
from gda.model.base.source_reference import SourceReference
from gda.model.base.time_period import TimePeriod
from gda.model.base.tombstone import TombstoneRecord
from gda.model.entity.fact import Fact, FactParticipant
from gda.model.entity.family import Family
from gda.model.entity.individual import Individual
from gda.model.entity.location import JurisdictionCategory, Location
from gda.model.entity.site import Site, SiteCategory

__version__ = "1.0.0+build.13"


def _make_audit() -> AuditStamp:
    now = IsoTimestamp("2026-01-01T00:00:00Z")
    return AuditStamp(created_at=now, updated_at=now)


# ==============================================================================
# GROUP 1: MAPPER REGISTRY, HELPERS & INTROSPECTION CONTRACTS
# ==============================================================================


@pytest.mark.unit
def test_mapper_registry_resolves_all_core_entities() -> None:
    """Verify get_mapper resolves mapper instances for all 5 core entity classes."""
    assert isinstance(get_mapper(Location), LocationRowMapper)
    assert isinstance(get_mapper(Site), SiteRowMapper)
    assert isinstance(get_mapper(Individual), IndividualRowMapper)
    assert isinstance(get_mapper(Family), FamilyRowMapper)
    assert isinstance(get_mapper(Fact), FactRowMapper)


@pytest.mark.unit
def test_base_row_mapper_model_cls_property() -> None:
    """Verify BaseRowMapper exposes the bound domain model class."""
    mapper = LocationRowMapper()
    assert mapper.model_cls is Location


@pytest.mark.unit
def test_extract_id_str_utility_branches() -> None:
    """Verify _extract_id_str handles None, str, dict, AtomID, and other values."""
    assert _extract_id_str(None) is None
    assert _extract_id_str("LOC-000001") == "LOC-000001"
    assert _extract_id_str({"value": "LOC-000002"}) == "LOC-000002"
    assert _extract_id_str(LocationID("LOC-000003")) == "LOC-000003"
    assert _extract_id_str(12345) == "12345"


@pytest.mark.regression
def test_mapper_registry_unknown_class_raises_entity_mapping_error() -> None:
    """Verify requesting an unregistered class raises EntityMappingError."""

    class DummyEntity:
        pass

    with pytest.raises(EntityMappingError, match="No registered row mapper"):
        get_mapper(DummyEntity)  # type: ignore[arg-type]


@pytest.mark.unit
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


@pytest.mark.unit
def test_location_mapper_round_trip() -> None:
    """Verify Location serializes to row params and round-trips without loss."""
    audit = _make_audit()
    coords = Coordinates(latitude=Latitude(43.13), longitude=Longitude(-71.53))
    period = TimePeriod(
        start_date=EventDate(date=DateString("1727-05-20")),
        end_date=EventDate(date=DateString("1900-01-01")),
    )
    loc = Location(
        id=LocationID("LOC-000001"),
        canonical_urn="urn:gda:loc:us:nh:bow",
        name="Bow",
        category=JurisdictionCategory.MUNICIPALITY,
        parent_id=LocationID("LOC-000002"),
        is_primary_local_authority=True,
        is_unincorporated=False,
        coordinates=coords,
        period=period,
        historical_names=[HistoricalName(raw_name="Bow Town")],
        alternate_names=["Bow Mills"],
        associated_jurisdiction_ids=[LocationID("LOC-000003")],
        predecessor_ids=[LocationID("LOC-000004")],
        successor_ids=[LocationID("LOC-000005")],
        audit=audit,
        tombstone=TombstoneRecord(is_deprecated=False),
        notes=[NoteID("NOT-000001")],
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
    assert restored == loc


# ==============================================================================
# GROUP 3: SITE ROUND-TRIP SERIALIZATION
# ==============================================================================


@pytest.mark.unit
def test_site_mapper_round_trip() -> None:
    """Verify Site serializes to row params and round-trips without loss."""
    audit = _make_audit()
    addr = Address(address_line_1="10 Woodhill Hook Rd", postal_code="03304")
    site = Site(
        id=SiteID("SID-000001"),
        canonical_urn="urn:gda:site:us:nh:bow:cemetery",
        name="Old Bow Cemetery",
        category=SiteCategory.CEMETERY,
        location_id=LocationID("LOC-000001"),
        is_active=False,
        address=addr,
        audit=audit,
        tombstone=TombstoneRecord(
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
    assert restored == site


# ==============================================================================
# GROUP 4: INDIVIDUAL ROUND-TRIP & TEMPORAL PROJECTION
# ==============================================================================


@pytest.mark.unit
def test_individual_mapper_round_trip_and_temporal_scalars() -> None:
    """Verify Individual projects birth/death years and round-trips without loss."""
    audit = _make_audit()
    ind = Individual(
        id=IndividualID("IND-000001"),
        name=CanonicalName(raw_name="John Doe", given="John", surname="Doe"),
        canonical_urn="urn:gda:ind:john_doe_1842",
        sex="M",
        birth_date=EventDate(date=DateString("1842-05-12")),
        death_date=EventDate(date=DateString("1910-11-04")),
        birth_place_id=LocationID("LOC-000001"),
        death_place_id=SiteID("SID-000001"),
        is_deceased=True,
        audit=audit,
        tombstone=TombstoneRecord(
            is_deprecated=True,
            deprecated_at=audit.updated_at,
            superseded_by=IndividualID("IND-000002"),
        ),
    )

    mapper = get_mapper(Individual)
    row_data = mapper.to_row(ind)

    assert row_data["birth_year"] == 1842
    assert row_data["birth_date_sort"] == "1842-05-12"
    assert row_data["death_year"] == 1910
    assert row_data["death_date_sort"] == "1910-11-04"
    assert row_data["surname"] == "Doe"
    assert row_data["given_name"] == "John"
    assert row_data["superseded_by"] == "IND-000002"

    restored = mapper.from_row(row_data)
    assert restored == ind


@pytest.mark.unit
def test_individual_mapper_with_start_date_range_and_site_places() -> None:
    """Verify Individual with start_date EventDateRange for birth and death."""
    audit = _make_audit()

    b_range = EventDateRange(
        start_date=EventDate(date=DateString("1850-01-01")),
        end_date=EventDate(date=DateString("1850-12-31")),
        modifier=DateModifier.BETWEEN,
    )
    d_range = EventDateRange(
        start_date=EventDate(date=DateString("1920-01-01")),
        end_date=EventDate(date=DateString("1920-12-31")),
        modifier=DateModifier.BETWEEN,
    )

    ind = Individual(
        id=IndividualID("IND-000005"),
        name=CanonicalName(raw_name="Jane Smith", surname="Smith"),
        canonical_urn="urn:gda:ind:jane_smith_1850",
        sex="F",
        birth_date=b_range,
        death_date=d_range,
        birth_place_id=SiteID("SID-000005"),
        death_place_id=LocationID("LOC-000005"),
        audit=audit,
    )
    mapper = get_mapper(Individual)
    row_data = mapper.to_row(ind)
    assert row_data["birth_year"] == 1850
    assert row_data["birth_date_sort"] == "1850-01-01"
    assert row_data["death_year"] == 1920
    assert row_data["death_date_sort"] == "1920-01-01"

    restored = mapper.from_row(row_data)
    assert restored.birth_place_id == SiteID("SID-000005")
    assert restored.death_place_id == LocationID("LOC-000005")


@pytest.mark.unit
def test_individual_mapper_without_birth_or_death_dates() -> None:
    """Verify Individual with birth_date=None and death_date=None produces None scalars."""
    audit = _make_audit()

    ind = Individual(
        id=IndividualID("IND-000006"),
        name=CanonicalName(raw_name="Living Person", given="Living", surname="Person"),
        canonical_urn="urn:gda:ind:living_person",
        sex="M",
        birth_date=None,
        death_date=None,
        is_deceased=False,
        audit=audit,
    )
    mapper = get_mapper(Individual)
    row_data = mapper.to_row(ind)
    assert row_data["birth_year"] is None
    assert row_data["birth_date_sort"] is None
    assert row_data["birth_date_json"] is None
    assert row_data["death_year"] is None
    assert row_data["death_date_sort"] is None
    assert row_data["death_date_json"] is None

    restored = mapper.from_row(row_data)
    assert restored.birth_date is None
    assert restored.death_date is None
    assert restored.is_deceased is False


# ==============================================================================
# GROUP 5: FAMILY ROUND-TRIP SERIALIZATION
# ==============================================================================


@pytest.mark.unit
def test_family_mapper_round_trip() -> None:
    """Verify Family serializes union/partners/children and round-trips without loss."""
    audit = _make_audit()
    fam = Family(
        id=FamilyID("FAM-000001"),
        canonical_urn="urn:gda:fam:doe_smith_1865",
        union=FamilyUnion(union_type=UnionType.MARRIED),
        partner_ids=[IndividualID("IND-000001"), IndividualID("IND-000002")],
        children=[
            ChildLink(
                child_id=IndividualID("IND-000003"),
                pedigree=PedigreeType.BIRTH,
            )
        ],
        audit=audit,
        tombstone=TombstoneRecord(
            is_deprecated=True,
            deprecated_at=audit.updated_at,
            superseded_by=FamilyID("FAM-000002"),
        ),
    )

    mapper = get_mapper(Family)
    row_data = mapper.to_row(fam)

    assert row_data["id"] == "FAM-000001"
    assert "MARRIED" in row_data["union_json"]
    assert row_data["superseded_by"] == "FAM-000002"

    restored = mapper.from_row(row_data)
    assert restored == fam


# ==============================================================================
# GROUP 6: FACT ROUND-TRIP SERIALIZATION, DATES & CITATIONS
# ==============================================================================


@pytest.mark.unit
def test_fact_mapper_round_trip_with_participants_and_citations() -> None:
    """Verify Fact serializes participants/citations and round-trips without loss."""
    audit = _make_audit()
    fact = Fact(
        id=FactID("FID-000001"),
        canonical_urn="urn:gda:fact:smith_marriage_1865",
        fact_type=FactType.MARRIAGE,
        title="Marriage Ceremony",
        primary_subject_id=IndividualID("IND-000001"),
        date=EventDate(date=DateString("1865-06-15")),
        location_id=LocationID("LOC-000001"),
        site_id=SiteID("SID-000001"),
        value="Ceremony solemnized by Rev. Smith",
        participants=[
            FactParticipant(
                individual_id=IndividualID("IND-000002"),
                role=AssociatedRole.SPOUSE,
            )
        ],
        citations=[
            SourceReference(citation_text="Town Marriage Records, Vol 1, p. 42")
        ],
        audit=audit,
        tombstone=TombstoneRecord(
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
    assert restored == fact


@pytest.mark.unit
def test_fact_mapper_family_subject_and_start_date_branch() -> None:
    """Verify Fact with FamilyID as primary_subject_id, TimePeriod range date, and valid year."""
    audit = _make_audit()

    period = TimePeriod(
        start_date=EventDate(date=DateString("1880-06-01")),
        end_date=EventDate(date=DateString("1880-06-30")),
    )

    fact = Fact(
        id=FactID("FID-000002"),
        canonical_urn="urn:gda:fact:census_1880",
        fact_type=FactType.CENSUS,
        title="1880 Federal Census",
        primary_subject_id=FamilyID("FAM-000001"),
        date=period,
        site_id=SiteID("SID-000002"),
        audit=audit,
    )

    mapper = get_mapper(Fact)
    row_data = mapper.to_row(fact)
    assert row_data["primary_subject_id"] == "FAM-000001"
    assert row_data["site_id"] == "SID-000002"
    assert row_data["fact_year"] == 1880
    assert row_data["fact_date_sort"] == "1880-06-01"

    restored = mapper.from_row(row_data)
    assert restored.primary_subject_id == FamilyID("FAM-000001")
    assert restored.site_id == SiteID("SID-000002")


@pytest.mark.unit
def test_fact_mapper_unparseable_date_year_branch() -> None:
    """Verify Fact handles non-numeric date strings gracefully when extracting integer year."""
    audit = _make_audit()

    fact = Fact(
        id=FactID("FID-000003"),
        canonical_urn="urn:gda:fact:unknown_year",
        fact_type=FactType.CUSTOM,
        title="Custom event with non-numeric date",
        primary_subject_id=IndividualID("IND-000001"),
        date=EventDate(date=DateString("UNKNOWN")),
        audit=audit,
    )

    mapper = get_mapper(Fact)
    row_data = mapper.to_row(fact)
    assert row_data["fact_year"] is None
    assert row_data["fact_date_sort"] == "UNKNOWN"

    restored = mapper.from_row(row_data)
    assert restored.date.date.value == "UNKNOWN"


@pytest.mark.unit
def test_fact_mapper_without_date() -> None:
    """Verify Fact with date=None produces None for fact_year and fact_date_sort."""
    audit = _make_audit()

    fact = Fact(
        id=FactID("FID-000005"),
        canonical_urn="urn:gda:fact:undated_event",
        fact_type=FactType.OCCUPATION,
        title="Blacksmith",
        primary_subject_id=IndividualID("IND-000001"),
        date=None,
        audit=audit,
    )

    mapper = get_mapper(Fact)
    row_data = mapper.to_row(fact)
    assert row_data["fact_year"] is None
    assert row_data["fact_date_sort"] is None
    assert row_data["date_json"] is None

    restored = mapper.from_row(row_data)
    assert restored.date is None


# ==============================================================================
# GROUP 7: DEFENSIVE BOUNDARIES & ERROR HANDLING
# ==============================================================================


@pytest.mark.regression
def test_mappers_corrupt_row_raises_entity_mapping_error() -> None:
    """Verify passing corrupt or incomplete row dictionaries raises EntityMappingError."""
    corrupt_row = {"id": "LOC-000001"}

    with pytest.raises(EntityMappingError, match="Failed to map row to Location"):
        LocationRowMapper().from_row(corrupt_row)

    with pytest.raises(EntityMappingError, match="Failed to map row to Site"):
        SiteRowMapper().from_row(corrupt_row)

    with pytest.raises(EntityMappingError, match="Failed to map row to Individual"):
        IndividualRowMapper().from_row(corrupt_row)

    with pytest.raises(EntityMappingError, match="Failed to map row to Family"):
        FamilyRowMapper().from_row(corrupt_row)

    with pytest.raises(EntityMappingError, match="Failed to map row to Fact"):
        FactRowMapper().from_row(corrupt_row)
