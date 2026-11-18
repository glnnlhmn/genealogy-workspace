"""Path: tests/test_gda/test_repository/test_vital/test_repository.py

Unit and integration tests for Vital domain SQLite repositories
(src/gda/repository/vital/repository.py).
"""

from __future__ import annotations

from gda.core.enums.core import Sex
from gda.core.enums.sources import SourceRecordType
from gda.core.enums.vital import (
    BirthPlurality,
    DispositionType,
    DivorceDecreeType,
    MannerOfDeath,
    MaritalStatus,
    UnionType,
)
from gda.db.session import DatabaseSessionManager
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import (
    IndividualID,
    LocationID,
    OrganizationID,
    RepositoryID,
    SiteID,
    SourceID,
)
from gda.model.atom.urn import SourceURN
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate
from gda.model.base.tombstone import Tombstone
from gda.model.source.vital.baptism import BaptismRecord
from gda.model.source.vital.birth import BirthRecord
from gda.model.source.vital.death import DeathRecord
from gda.model.source.vital.divorce import DivorceRecord
from gda.model.source.vital.marriage import MarriageRecord
from gda.repository.vital.repository import (
    BaptismRepository,
    BirthRepository,
    DeathRepository,
    DivorceRepository,
    MarriageRepository,
)


def _audit() -> AuditStamp:
    ts = IsoTimestamp("2026-01-01T00:00:00Z")
    return AuditStamp(created_at=ts, updated_at=ts)


def test_vital_baptism_repository_crud_and_queries(
    seeded_session: DatabaseSessionManager,
) -> None:
    """Verify BaptismRepository CRUD and specialized lookup filters."""
    repo = BaptismRepository(session_manager=seeded_session)
    bap = BaptismRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000001"),
        source_urn=SourceURN("URN:SRC:1852:US_PA:BAP001"),
        record_type=SourceRecordType.BAPTISM_CERTIFICATE,
        description="Baptism of John Lehman",
        repository_id=RepositoryID("REP-000001"),
        audit=_audit(),
        church_name_raw="Zion Lutheran Church",
        baptized_name_raw="Johannes Lehman",
        date_of_baptism=EventDate.from_dict("1852-04-12"),
        date_of_birth=EventDate.from_dict("1852-01-03"),
        individual_id=IndividualID("IND-000001"),
        church_org_id=OrganizationID("ORG-000001"),
        church_site_id=SiteID("SID-000001"),
        location_id=LocationID("LOC-000001"),
        sex=Sex.MALE,
        denomination="Lutheran",
        father_name_raw="Daniel Lehman",
        mother_name_raw="Elizabeth",
        sponsors_or_godparents=["Jacob Lehman"],
        tombstone=Tombstone[SourceID](
            is_deprecated=True,
            deprecated_at=IsoTimestamp("2026-02-01T00:00:00Z"),
            superseded_by=SourceID("00000000-0000-4000-8000-000000000099"),
        ),
    )

    repo.upsert(bap)
    assert repo.get_or_raise("00000000-0000-4000-8000-000000000001") == bap
    assert len(repo.find_by_individual("IND-000001")) == 1
    assert len(repo.find_by_church_org("ORG-000001")) == 1
    assert len(repo.find_by_church_site("SID-000001")) == 1
    assert len(repo.find_by_location("LOC-000001")) == 1
    assert len(repo.find_by_year_range(1850, 1855)) == 1
    assert len(repo.find_by_year_range(1860, 1870)) == 0


def test_vital_birth_repository_crud_and_queries(
    seeded_session: DatabaseSessionManager,
) -> None:
    """Verify BirthRepository CRUD and specialized lookup filters."""
    repo = BirthRepository(session_manager=seeded_session)
    birth = BirthRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000002"),
        source_urn=SourceURN("URN:SRC:1852:US_PA:BIR002"),
        record_type=SourceRecordType.BIRTH_CERTIFICATE,
        description="Birth Certificate of John Lehman",
        repository_id=RepositoryID("REP-000001"),
        audit=_audit(),
        child_name_raw="John Lehman",
        date_of_birth=EventDate.from_dict("1852-01-03"),
        place_of_birth_raw="Carlisle, Cumberland County, PA",
        child_id=IndividualID("IND-000001"),
        place_of_birth_id=LocationID("LOC-000001"),
        sex=Sex.MALE,
        plurality=BirthPlurality.SINGLE,
        is_stillborn=False,
        certificate_number="BC-1852-001",
    )

    repo.upsert(birth)
    assert repo.get_or_raise(birth.source_id) == birth
    assert len(repo.find_by_child("IND-000001")) == 1
    assert len(repo.find_by_location("LOC-000001")) == 1
    assert len(repo.find_by_certificate_number("BC-1852-001")) == 1
    assert len(repo.find_by_year_range(1850, 1855)) == 1


def test_vital_death_repository_crud_and_queries(
    seeded_session: DatabaseSessionManager,
) -> None:
    """Verify DeathRepository CRUD and specialized lookup filters."""
    repo = DeathRepository(session_manager=seeded_session)
    death = DeathRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000003"),
        source_urn=SourceURN("URN:SRC:1922:US_PA:DEA003"),
        record_type=SourceRecordType.DEATH_CERTIFICATE,
        description="Death Certificate of John Lehman",
        repository_id=RepositoryID("REP-000001"),
        audit=_audit(),
        decedent_name_raw="John Lehman",
        date_of_death=EventDate.from_dict("1922-11-08"),
        place_of_death_raw="Carlisle, PA",
        decedent_id=IndividualID("IND-000001"),
        place_of_death_id=LocationID("LOC-000001"),
        disposition_site_id=SiteID("SID-000001"),
        sex=Sex.MALE,
        is_stillborn=False,
        marital_status=MaritalStatus.MARRIED,
        manner_of_death=MannerOfDeath.NATURAL,
        disposition_type=DispositionType.BURIAL,
        certificate_number="DC-1922-404",
    )

    repo.upsert(death)
    assert repo.get_or_raise(death.source_id) == death
    assert len(repo.find_by_decedent("IND-000001")) == 1
    assert len(repo.find_by_location("LOC-000001")) == 1
    assert len(repo.find_by_disposition_site("SID-000001")) == 1
    assert len(repo.find_by_certificate_number("DC-1922-404")) == 1
    assert len(repo.find_by_year_range(1920, 1925)) == 1


def test_vital_divorce_repository_crud_and_queries(
    seeded_session: DatabaseSessionManager,
) -> None:
    """Verify DivorceRepository CRUD and specialized lookup filters."""
    repo = DivorceRepository(session_manager=seeded_session)
    divorce = DivorceRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000004"),
        source_urn=SourceURN("URN:SRC:1895:US_PA:DIV004"),
        record_type=SourceRecordType.DIVORCE_DECREE,
        description="Divorce Decree",
        repository_id=RepositoryID("REP-000001"),
        audit=_audit(),
        court_name="Cumberland County Court of Common Pleas",
        husband_name_raw="John Lehman",
        wife_name_raw="Mary Miller",
        date_decree_granted=EventDate.from_dict("1895-06-15"),
        husband_id=IndividualID("IND-000001"),
        wife_id=IndividualID("IND-000002"),
        jurisdiction_id=LocationID("LOC-000001"),
        docket_number="DKT-1895-77",
        decree_type=DivorceDecreeType.ABSOLUTE,
    )

    repo.upsert(divorce)
    assert repo.get_or_raise(divorce.source_id) == divorce
    assert len(repo.find_by_husband("IND-000001")) == 1
    assert len(repo.find_by_wife("IND-000002")) == 1
    assert len(repo.find_by_jurisdiction("LOC-000001")) == 1
    assert len(repo.find_by_docket_number("DKT-1895-77")) == 1
    assert len(repo.find_by_year_range(1890, 1900)) == 1


def test_vital_marriage_repository_crud_and_queries(
    seeded_session: DatabaseSessionManager,
) -> None:
    """Verify MarriageRepository CRUD and specialized lookup filters."""
    repo = MarriageRepository(session_manager=seeded_session)
    marriage = MarriageRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000005"),
        source_urn=SourceURN("URN:SRC:1875:US_PA:MAR005"),
        record_type=SourceRecordType.MARRIAGE_CERTIFICATE,
        description="Marriage of John Lehman and Mary Miller",
        repository_id=RepositoryID("REP-000001"),
        audit=_audit(),
        groom_name_raw="John Lehman",
        bride_name_raw="Mary Miller",
        union_type=UnionType.MARRIED,
        groom_id=IndividualID("IND-000001"),
        bride_id=IndividualID("IND-000002"),
        date_of_marriage=EventDate.from_dict("1875-10-20"),
        place_of_marriage_raw="Carlisle, PA",
        place_of_marriage_id=LocationID("LOC-000001"),
        license_number="ML-1875-09",
        witnesses=["Peter Lehman"],
    )

    repo.upsert(marriage)
    assert repo.get_or_raise(marriage.source_id) == marriage
    assert len(repo.find_by_groom("IND-000001")) == 1
    assert len(repo.find_by_bride("IND-000002")) == 1
    assert len(repo.find_by_location("LOC-000001")) == 1
    assert len(repo.find_by_license_number("ML-1875-09")) == 1
    assert len(repo.find_by_year_range(1870, 1880)) == 1
