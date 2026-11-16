"""Path: tests/test_gda/test_model/test_entity/conftest.py

Shared pytest fixtures for the gda.model.entity verification suite.

Operational Role:
    Centralizes all domain entity test fixtures (Fact, Family, Individual,
    Location, Site, citations, names, and date bounds) in conftest.py.
    Inherits golden_timestamp, golden_audit, and golden_time_period from
    tests/test_gda/test_model/conftest.py.
"""

from __future__ import annotations

import pytest

from gda.core.enums.archival import NoteType
from gda.core.enums.core import AssociatedRole, FactType
from gda.core.enums.date import DateModifier
from gda.core.enums.location import JurisdictionCategory
from gda.core.enums.site import SiteType
from gda.core.enums.vital import HistoricNameType, PedigreeType, UnionDissolutionType, UnionType
from gda.model.atom.date import DateString
from gda.model.atom.gender import GenderAtom
from gda.model.atom.geo import Latitude, Longitude
from gda.model.atom.id import (
    FactID,
    FamilyID,
    IndividualID,
    LocationID,
    SiteID,
)
from gda.model.base.address import Address
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate, TimePeriod
from gda.model.base.family import ChildLink, FamilyUnion
from gda.model.base.geo import Coordinates
from gda.model.base.name import HistoricVariant, NamePerson, NameThing
from gda.model.base.note import Note
from gda.model.base.source import SourceReference
from gda.model.entity.fact import Fact, FactParticipant
from gda.model.entity.family import Family
from gda.model.entity.individual import Individual
from gda.model.entity.location import Location
from gda.model.entity.site import Site

__version__ = "1.0.0+build.1"


@pytest.fixture
def six_note_bundle() -> list[Note]:
    """Provide a 6-note research bundle spanning multiple NoteType categories."""
    return [
        Note.create(
            note_id="NOT-000001",
            text="Census records confirm residence in Merrimack County.",
            title="Census Residence",
            note_type=NoteType.RESEARCH,
            tags=["census", "merrimack"],
        ),
        Note.create(
            note_id="NOT-000002",
            text="Tombstone inscription lists birth year as 1841 instead of 1842.",
            title="Birth Year Conflict",
            note_type=NoteType.DISCREPANCY,
            tags=["headstone", "conflict"],
        ),
        Note.create(
            note_id="NOT-000003",
            text="Town clerk register verified in Bow archive.",
            title="Register Proof",
            note_type=NoteType.PROOF,
            tags=["bow", "vital"],
        ),
        Note.create(
            note_id="NOT-000004",
            text="Tax inventory lists 40 acres of improved land.",
            title="Tax Assessment",
            note_type=NoteType.RESEARCH,
            tags=["tax", "census"],
        ),
        Note.create(
            note_id="NOT-000005",
            text="Surname spelled Smyth on militia muster roll.",
            title="Surname Spelling Variance",
            note_type=NoteType.DISCREPANCY,
            tags=["spelling", "militia"],
        ),
        Note.create(
            note_id="NOT-000006",
            text="Probate docket names surviving spouse and children.",
            title="Probate Docket",
            note_type=NoteType.RESEARCH,
            tags=["probate"],
        ),
    ]


@pytest.fixture
def valid_citation() -> SourceReference:
    """Provide a valid synthetic SourceReference fixture matching model contracts."""
    return SourceReference.create(
        source_id="a0000000-0000-4000-8000-000000000001",
        citation_text="Page 42, Entry 15",
    )


@pytest.fixture
def valid_fact(golden_audit: AuditStamp, valid_citation: SourceReference) -> Fact:
    """Provide a fully populated Fact fixture."""
    p1 = FactParticipant.create(
        individual_id="IND-000002",
        role=AssociatedRole.INFORMANT,
        notes="Attending neighbor",
    )
    return Fact(
        id=FactID("FID-000001"),
        audit=golden_audit,
        canonical_urn="urn:gda:fact:smith_birth_1842",
        fact_type=FactType.BIRTH,
        title="Birth of John Smith",
        primary_subject_id=IndividualID("IND-000001"),
        date=EventDate.create("1842-05-12"),
        location_id=LocationID("LOC-000010"),
        site_id=SiteID("SID-000020"),
        value="Born at home",
        description="Recorded in City Register Vol. 3",
        narrative="First child born to the family.",
        participants=[p1],
        citations=[valid_citation],
    )


@pytest.fixture
def valid_period() -> TimePeriod:
    """Fixture providing a standard bounded temporal interval for marriage."""
    marr = EventDate(date=DateString(value="1865-04-12"))
    div = EventDate(date=DateString(value="1880-09-01"))
    return TimePeriod(start_date=marr, end_date=div)


@pytest.fixture
def valid_family(golden_audit: AuditStamp, valid_period: TimePeriod) -> Family:
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
        audit=golden_audit,
        canonical_urn="urn:gda:fam:smith_jones_1865",
        union=union,
        partner_ids=[p1, p2],
        children=[c1, c2],
    )


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
def range_death_date() -> EventDate:
    """Fixture providing a bounded BETWEEN death date."""
    return EventDate.create("1910-01-01", DateModifier.BETWEEN, "1912-12-31")


@pytest.fixture
def valid_individual(
    golden_audit: AuditStamp,
    valid_name: NamePerson,
    point_birth_date: EventDate,
    range_death_date: EventDate,
) -> Individual:
    """Fixture providing a complete standard Individual instance with NamePerson."""
    return Individual(
        id=IndividualID(value="IND-000101"),
        audit=golden_audit,
        name=valid_name,
        canonical_urn="urn:gda:ind:smith_johnathan_1842",
        gender=GenderAtom("M"),
        birth_date=point_birth_date,
        death_date=range_death_date,
        birth_place_id=LocationID(value="LOC-000010"),
        death_place_id=SiteID(value="SID-000020"),
    )


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
