"""Path: tests/test_gda/test_repository/test_entity/test_repository.py

Unit and integration tests for the 6 core entity SQLite repositories
(src/gda/repository/entity/repository.py).
"""

from __future__ import annotations

from gda.core.enums.core import FactType
from gda.core.enums.location import JurisdictionCategory
from gda.core.enums.orgs import OrganizationCategory
from gda.core.enums.site import SiteType
from gda.core.enums.vital import UnionType
from gda.db.session import DatabaseSessionManager
from gda.model.atom.gender import GenderAtom
from gda.model.atom.id import (
    FactID,
    FamilyID,
    IndividualID,
    LocationID,
    OrganizationID,
    SiteID,
)
from gda.model.base.audit import AuditStamp
from gda.model.base.family import ChildLink, FamilyUnion
from gda.model.base.name import NamePerson, NameThing
from gda.model.entity.fact import Fact
from gda.model.entity.family import Family
from gda.model.entity.individual import Individual
from gda.model.entity.location import Location
from gda.model.entity.organization import Organization
from gda.model.entity.site import Site
from gda.repository.entity.repository import (
    FactRepository,
    FamilyRepository,
    IndividualRepository,
    LocationRepository,
    OrganizationRepository,
    SiteRepository,
)


def test_core_entity_repositories_crud_and_queries(
    seeded_session: DatabaseSessionManager,
    golden_audit: AuditStamp,
) -> None:
    """Verify Location, Site, Organization, Individual, Family, and Fact repositories."""
    loc_repo = LocationRepository(session_manager=seeded_session)
    loc = Location(
        id=LocationID("LOC-000010"),
        audit=golden_audit,
        name=NameThing.create("Carlisle Borough"),
        category=JurisdictionCategory.MUNICIPALITY,
        canonical_urn="urn:gda:loc:us:pa:cumberland:carlisle",
        parent_id=LocationID("LOC-000001"),
    )
    loc_repo.upsert(loc)
    assert loc_repo.get_or_raise("LOC-000010") == loc
    assert len(loc_repo.find_by_parent("LOC-000001")) == 1
    assert len(loc_repo.find_by_category("MUNICIPALITY")) == 1

    site_repo = SiteRepository(session_manager=seeded_session)
    site = Site(
        id=SiteID("SID-000010"),
        audit=golden_audit,
        name=NameThing.create("Old Graveyard"),
        category=SiteType.CEMETERY,
        canonical_urn="urn:gda:site:us:pa:carlisle:old_graveyard",
        location_id=LocationID("LOC-000010"),
    )
    site_repo.upsert(site)
    assert site_repo.get_or_raise("SID-000010") == site
    assert len(site_repo.find_by_location("LOC-000010")) == 1
    assert len(site_repo.find_by_category("CEMETERY")) >= 1

    org_repo = OrganizationRepository(session_manager=seeded_session)
    org = Organization(
        id=OrganizationID("ORG-000010"),
        audit=golden_audit,
        name=NameThing.create("First Presbyterian Church"),
        category=OrganizationCategory.RELIGIOUS,
        canonical_urn="urn:gda:org:us:pa:carlisle:first_presbyterian",
        location_id=LocationID("LOC-000010"),
        meeting_site_id=SiteID("SID-000010"),
    )
    org_repo.upsert(org)
    assert org_repo.get_or_raise("ORG-000010") == org
    assert len(org_repo.find_by_location("LOC-000010")) == 1
    assert len(org_repo.find_by_category("RELIGIOUS")) >= 1

    ind_repo = IndividualRepository(session_manager=seeded_session)
    ind = Individual(
        id=IndividualID("IND-000010"),
        audit=golden_audit,
        name=NamePerson(
            raw="Daniel Lehman",
            canonical="Daniel Lehman",
            given="Daniel",
            surname="Lehman",
        ),
        canonical_urn="urn:gda:ind:lehman_daniel_1820",
        gender=GenderAtom("M"),
    )
    ind_repo.upsert(ind)
    assert ind_repo.get_or_raise("IND-000010") == ind
    assert len(ind_repo.find_by_surname("Lehman")) >= 1

    fam_repo = FamilyRepository(session_manager=seeded_session)
    fam = Family(
        id=FamilyID("FAM-000010"),
        audit=golden_audit,
        canonical_urn="urn:gda:fam:lehman_miller_1875",
        union=FamilyUnion(union_type=UnionType.MARRIED),
        partner_ids=[IndividualID("IND-000001"), IndividualID("IND-000002")],
        children=[ChildLink(child_id=IndividualID("IND-000010"))],
    )
    fam_repo.upsert(fam)
    assert fam_repo.get_or_raise("FAM-000010") == fam
    assert len(fam_repo.find_by_union_type("MARRIED")) == 1

    fact_repo = FactRepository(session_manager=seeded_session)
    fact = Fact(
        id=FactID("FID-000010"),
        audit=golden_audit,
        canonical_urn="urn:gda:fact:lehman_occupation_1880",
        fact_type=FactType.OCCUPATION,
        title="Blacksmith in Carlisle",
        primary_subject_id=IndividualID("IND-000001"),
        location_id=LocationID("LOC-000010"),
        value="Blacksmith",
    )
    fact_repo.upsert(fact)
    assert fact_repo.get_or_raise("FID-000010") == fact
    assert len(fact_repo.find_by_primary_subject("IND-000001")) == 1
    assert len(fact_repo.find_by_fact_type("OCCUPATION")) == 1
