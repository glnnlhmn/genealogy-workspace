"""Path: tests/test_gda/test_repository/test_xref/test_repository.py

Unit and integration tests for all 9 Cross-Reference SQLite repositories
(src/gda/repository/xref/repository.py).
"""

from __future__ import annotations

from gda.core.enums.core import AssociatedRole, FactType
from gda.core.enums.orgs import (
    AffiliationType,
    MembershipStatus,
    OrganizationCategory,
)
from gda.core.enums.sources import SourceRecordCategory, SourceRecordType
from gda.core.enums.vital import HistoricNameType, PedigreeType
from gda.db.session import DatabaseSessionManager
from gda.model.atom.id import (
    FactID,
    FamilyID,
    IndividualID,
    LocationID,
    MediaID,
    OrganizationID,
    SiteID,
    SourceID,
)
from gda.model.atom.year import BirthYear, DeathYear, HistoricalYear
from gda.model.xref import (
    FactParticipantXRef,
    IndividualFamilyXRef,
    IndividualOrganizationXRef,
    IndividualSourceXRef,
    IndividualSurnameXRef,
    LocationXRef,
    MediaXRef,
    SiteXRef,
    SurnameXRef,
)
from gda.repository.xref.repository import (
    FactParticipantXRefRepository,
    IndividualFamilyXRefRepository,
    IndividualOrganizationXRefRepository,
    IndividualSourceXRefRepository,
    IndividualSurnameXRefRepository,
    LocationXRefRepository,
    MediaXRefRepository,
    SiteXRefRepository,
    SurnameXRefRepository,
)


def test_xref_repositories_crud_and_queries(
    seeded_session: DatabaseSessionManager,
) -> None:
    """Verify CRUD and specialized lookup methods across all 9 XRef repositories."""
    fp_repo = FactParticipantXRefRepository(session_manager=seeded_session)
    fp = FactParticipantXRef(
        fact_id=FactID("FID-000001"),
        individual_id=IndividualID("IND-000001"),
        role=AssociatedRole.PRIMARY,
        fact_type=FactType.BIRTH,
        is_primary_subject=True,
        temporal_year=HistoricalYear(1852),
        location_id=LocationID("LOC-000001"),
        site_id=SiteID("SID-000001"),
    )
    fp_repo.upsert(fp)
    assert fp_repo.get_or_raise(fp.xref_key) == fp
    assert len(fp_repo.find_by_fact("FID-000001")) == 1
    assert len(fp_repo.find_by_individual("IND-000001")) == 1

    if_repo = IndividualFamilyXRefRepository(session_manager=seeded_session)
    ifam = IndividualFamilyXRef(
        family_id=FamilyID("FAM-000001"),
        individual_id=IndividualID("IND-000001"),
        is_partner=False,
        pedigree=PedigreeType.BIRTH,
        child_order=1,
    )
    if_repo.upsert(ifam)
    assert if_repo.get_or_raise(ifam.xref_key) == ifam
    assert len(if_repo.find_by_family("FAM-000001")) == 1
    assert len(if_repo.find_by_individual("IND-000001")) == 1

    io_repo = IndividualOrganizationXRefRepository(session_manager=seeded_session)
    iorg = IndividualOrganizationXRef(
        organization_id=OrganizationID("ORG-000001"),
        individual_id=IndividualID("IND-000001"),
        org_category=OrganizationCategory.RELIGIOUS,
        affiliation_type=AffiliationType.MEMBER,
        membership_status=MembershipStatus.ACTIVE,
    )
    io_repo.upsert(iorg)
    assert io_repo.get_or_raise(iorg.xref_key) == iorg
    assert len(io_repo.find_by_organization("ORG-000001")) == 1
    assert len(io_repo.find_by_individual("IND-000001")) == 1

    is_repo = IndividualSourceXRefRepository(session_manager=seeded_session)
    isrc = IndividualSourceXRef(
        source_id=SourceID("00000000-0000-4000-8000-000000000001"),
        individual_id=IndividualID("IND-000001"),
        role=AssociatedRole.PRIMARY,
        record_category=SourceRecordCategory.VITAL,
        record_type=SourceRecordType.BIRTH_CERTIFICATE,
    )
    is_repo.upsert(isrc)
    assert is_repo.get_or_raise(isrc.xref_key) == isrc
    assert len(is_repo.find_by_source("00000000-0000-4000-8000-000000000001")) == 1
    assert len(is_repo.find_by_individual("IND-000001")) == 1

    isur_repo = IndividualSurnameXRefRepository(session_manager=seeded_session)
    isur = IndividualSurnameXRef(
        surname="LEHMAN",
        individual_id=IndividualID("IND-000001"),
        is_birth_surname=True,
        birth_year=BirthYear(1852),
        death_year=DeathYear(1922),
    )
    isur_repo.upsert(isur)
    assert isur_repo.get_or_raise(isur.xref_key) == isur
    assert len(isur_repo.find_by_surname("lehman")) == 1
    assert len(isur_repo.find_by_individual("IND-000001")) == 1

    loc_repo = LocationXRefRepository(session_manager=seeded_session)
    loc_x = LocationXRef(
        location_id=LocationID("LOC-000001"),
        target_id=IndividualID("IND-000001"),
    )
    loc_repo.upsert(loc_x)
    assert loc_repo.get_or_raise(loc_x.xref_key) == loc_x
    assert len(loc_repo.find_by_location("LOC-000001")) == 1
    assert len(loc_repo.find_by_target("IND-000001")) == 1

    med_repo = MediaXRefRepository(session_manager=seeded_session)
    med_x = MediaXRef(
        media_id=MediaID("00000000-0000-4000-8000-000000000801"),
        target_id=SourceID("00000000-0000-4000-8000-000000000001"),
    )
    med_repo.upsert(med_x)
    assert med_repo.get_or_raise(med_x.xref_key) == med_x
    assert len(med_repo.find_by_media("00000000-0000-4000-8000-000000000801")) == 1
    assert len(med_repo.find_by_target("00000000-0000-4000-8000-000000000001")) == 1

    site_repo = SiteXRefRepository(session_manager=seeded_session)
    site_x = SiteXRef(
        site_id=SiteID("SID-000001"),
        location_id=LocationID("LOC-000001"),
        target_id=IndividualID("IND-000001"),
    )
    site_repo.upsert(site_x)
    assert site_repo.get_or_raise(site_x.xref_key) == site_x
    assert len(site_repo.find_by_site("SID-000001")) == 1
    assert len(site_repo.find_by_location("LOC-000001")) == 1

    sur_repo = SurnameXRefRepository(session_manager=seeded_session)
    sur_x = SurnameXRef(
        canonical_surname="LEHMAN",
        variant_surname="LEHMANN",
        variant_name_type=HistoricNameType.HISTORICAL,
        variant_phonetic_code="L550",
    )
    sur_repo.upsert(sur_x)
    assert sur_repo.get_or_raise(sur_x.xref_key) == sur_x
    assert len(sur_repo.find_by_canonical_surname("lehman")) == 1
    assert len(sur_repo.find_by_variant_surname("lehmann")) == 1
