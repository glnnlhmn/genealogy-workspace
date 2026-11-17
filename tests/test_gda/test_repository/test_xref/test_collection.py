"""Path: tests/test_gda/test_repository/test_xref/test_collection.py

Unit and integration tests for BaseXRefCollection and all 9 XRef collections
(src/gda/repository/xref/collection.py).
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from gda.core.enums.core import AssociatedRole, FactType
from gda.core.enums.orgs import (
    AffiliationType,
    MembershipStatus,
    OrganizationCategory,
)
from gda.core.enums.sources import SourceRecordCategory, SourceRecordType
from gda.core.enums.vital import HistoricNameType, PedigreeType
from gda.db.session import DatabaseSessionManager
from gda.io.json import GDAJsonIO
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
from gda.repository.errors import (
    DuplicateRecordError,
    RecordNotFoundError,
    RepositoryError,
)
from gda.repository.xref.collection import (
    FactParticipantXRefCollection,
    IndividualFamilyXRefCollection,
    IndividualOrganizationXRefCollection,
    IndividualSourceXRefCollection,
    IndividualSurnameXRefCollection,
    LocationXRefCollection,
    MediaXRefCollection,
    SiteXRefCollection,
    SurnameXRefCollection,
)


def test_base_xref_collection_lifecycle_db_and_json_io(
    seeded_session: DatabaseSessionManager,
    tmp_path: Path,
) -> None:
    """Verify BaseXRefCollection CRUD, dirty tracking, SQLite sync, and JSON export/import."""

    class _BoundFactXRefCollection(FactParticipantXRefCollection):
        def _create_default_repository(self, session_manager=None):
            return super()._create_default_repository(session_manager or seeded_session)

    _ = _BoundFactXRefCollection.from_database()
    coll = FactParticipantXRefCollection.from_database(session_manager=seeded_session)
    assert len(coll) == 0
    assert coll.table_name == "xref_fact_participants"
    assert isinstance(coll.repository, object)
    assert coll.is_dirty is False

    fp1 = FactParticipantXRef(
        fact_id=FactID("FID-000001"),
        individual_id=IndividualID("IND-000001"),
        role=AssociatedRole.PRIMARY,
        fact_type=FactType.BIRTH,
        is_primary_subject=True,
        temporal_year=HistoricalYear(1852),
        location_id=LocationID("LOC-000001"),
        site_id=SiteID("SID-000001"),
    )
    fp2 = FactParticipantXRef(
        fact_id=FactID("FID-000001"),
        individual_id=IndividualID("IND-000002"),
        role=AssociatedRole.WITNESS,
        fact_type=FactType.BIRTH,
        is_primary_subject=False,
    )

    coll.add(fp1)
    coll.add(fp2)
    assert len(coll) == 2
    assert len(list(coll)) == 2
    assert len(list(coll.iter_all())) == 2
    assert coll.is_dirty is True
    assert len(coll.dirty_records()) == 2
    assert coll.dirty_entities() == coll.dirty_records()

    assert fp1.xref_key in coll
    assert 12345 not in coll
    assert "MISSING" not in coll
    assert coll[fp1.xref_key] == fp1
    assert coll.get(fp1.xref_key) == fp1
    assert coll.get("MISSING") is None

    with pytest.raises(RecordNotFoundError):
        _ = coll["MISSING"]
    with pytest.raises(DuplicateRecordError):
        coll.add(fp1)

    fp1_updated = dataclasses.replace(fp1, temporal_year=HistoricalYear(1853))
    coll.update(fp1_updated)
    assert coll[fp1.xref_key].temporal_year == HistoricalYear(1853)

    with pytest.raises(RecordNotFoundError):
        coll.update(
            FactParticipantXRef(
                fact_id=FactID("FID-000099"),
                individual_id=IndividualID("IND-000099"),
                role=AssociatedRole.OTHER,
                fact_type=FactType.DEATH,
            )
        )

    assert len(coll.find_by_fact("FID-000001")) == 2
    assert len(coll.find_by_individual("IND-000001")) == 1

    assert coll.remove(fp2.xref_key) is True
    assert coll.remove("MISSING") is False
    assert len(coll) == 1

    coll.add(fp2)
    assert coll.save_to_db(session_manager=seeded_session, dirty_only=True) == 2
    assert coll.is_dirty is False
    assert coll.save_to_db() == 2

    reloaded = FactParticipantXRefCollection.from_database(session_manager=seeded_session)
    assert reloaded.load_from_db(session_manager=seeded_session) == 2
    assert reloaded.refresh() == 2

    json_path = tmp_path / "xref_fp.json"
    assert reloaded.export_file(json_path, create_backup=False) == 2

    fresh = FactParticipantXRefCollection(repository=reloaded.repository)
    assert fresh.import_file(json_path, mark_dirty=False) == 2
    assert fresh.is_dirty is False
    assert fresh.import_file(json_path, mark_dirty=False) == 2
    assert fresh.is_dirty is False
    assert fresh.import_file(json_path, mark_dirty=True) == 2
    assert fresh.is_dirty is True

    bad_json = tmp_path / "bad_xref.json"
    GDAJsonIO.write(bad_json, {"invalid": True})
    with pytest.raises(RepositoryError, match="Invalid XRef export payload"):
        fresh.import_file(bad_json)


def test_all_nine_xref_collections_domain_buckets_and_roundtrip(
    seeded_session: DatabaseSessionManager,
    tmp_path: Path,
) -> None:
    """Verify secondary index buckets and JSON round-trip across the remaining 8 XRef collections."""
    # 1. IndividualFamilyXRefCollection
    if_coll = IndividualFamilyXRefCollection.from_database(seeded_session)
    ifam = IndividualFamilyXRef(
        family_id=FamilyID("FAM-000001"),
        individual_id=IndividualID("IND-000001"),
        is_partner=False,
        pedigree=PedigreeType.BIRTH,
        child_order=1,
    )
    if_coll.add(ifam)
    assert len(if_coll.find_by_family("FAM-000001")) == 1
    assert len(if_coll.find_by_individual("IND-000001")) == 1
    p_if = tmp_path / "ifam.json"
    if_coll.export_file(p_if)
    IndividualFamilyXRefCollection().import_file(p_if)
    if_coll.clear()

    # 2. IndividualOrganizationXRefCollection
    io_coll = IndividualOrganizationXRefCollection.from_database(seeded_session)
    iorg = IndividualOrganizationXRef(
        organization_id=OrganizationID("ORG-000001"),
        individual_id=IndividualID("IND-000001"),
        org_category=OrganizationCategory.RELIGIOUS,
        affiliation_type=AffiliationType.MEMBER,
        membership_status=MembershipStatus.ACTIVE,
    )
    io_coll.add(iorg)
    assert len(io_coll.find_by_organization("ORG-000001")) == 1
    assert len(io_coll.find_by_individual("IND-000001")) == 1
    p_io = tmp_path / "iorg.json"
    io_coll.export_file(p_io)
    IndividualOrganizationXRefCollection().import_file(p_io)
    io_coll.clear()

    # 3. IndividualSourceXRefCollection
    is_coll = IndividualSourceXRefCollection.from_database(seeded_session)
    isrc = IndividualSourceXRef(
        source_id=SourceID("00000000-0000-4000-8000-000000000001"),
        individual_id=IndividualID("IND-000001"),
        role=AssociatedRole.PRIMARY,
        record_category=SourceRecordCategory.VITAL,
        record_type=SourceRecordType.BIRTH_CERTIFICATE,
    )
    is_coll.add(isrc)
    assert len(is_coll.find_by_source("00000000-0000-4000-8000-000000000001")) == 1
    assert len(is_coll.find_by_individual("IND-000001")) == 1
    p_is = tmp_path / "isrc.json"
    is_coll.export_file(p_is)
    IndividualSourceXRefCollection().import_file(p_is)
    is_coll.clear()

    # 4. IndividualSurnameXRefCollection
    isur_coll = IndividualSurnameXRefCollection.from_database(seeded_session)
    isur = IndividualSurnameXRef(
        surname="LEHMAN",
        individual_id=IndividualID("IND-000001"),
        is_birth_surname=True,
        birth_year=BirthYear(1852),
        death_year=DeathYear(1922),
    )
    isur_coll.add(isur)
    assert len(isur_coll.find_by_surname("lehman")) == 1
    assert len(isur_coll.find_by_individual("IND-000001")) == 1
    p_isur = tmp_path / "isur.json"
    isur_coll.export_file(p_isur)
    IndividualSurnameXRefCollection().import_file(p_isur)
    isur_coll.clear()

    # 5. LocationXRefCollection
    loc_coll = LocationXRefCollection.from_database(seeded_session)
    loc_x = LocationXRef(
        location_id=LocationID("LOC-000001"),
        target_id=IndividualID("IND-000001"),
    )
    loc_coll.add(loc_x)
    assert len(loc_coll.find_by_location("LOC-000001")) == 1
    assert len(loc_coll.find_by_target("IND-000001")) == 1
    p_loc = tmp_path / "loc_x.json"
    loc_coll.export_file(p_loc)
    LocationXRefCollection().import_file(p_loc)
    loc_coll.clear()

    # 6. MediaXRefCollection
    med_coll = MediaXRefCollection.from_database(seeded_session)
    med_x = MediaXRef(
        media_id=MediaID("00000000-0000-4000-8000-000000000801"),
        target_id=SourceID("00000000-0000-4000-8000-000000000001"),
    )
    med_coll.add(med_x)
    assert len(med_coll.find_by_media("00000000-0000-4000-8000-000000000801")) == 1
    assert len(med_coll.find_by_target("00000000-0000-4000-8000-000000000001")) == 1
    p_med = tmp_path / "med_x.json"
    med_coll.export_file(p_med)
    MediaXRefCollection().import_file(p_med)
    med_coll.clear()

    # 7. SiteXRefCollection
    site_coll = SiteXRefCollection.from_database(seeded_session)
    site_x = SiteXRef(
        site_id=SiteID("SID-000001"),
        location_id=LocationID("LOC-000001"),
        target_id=IndividualID("IND-000001"),
    )
    site_coll.add(site_x)
    assert len(site_coll.find_by_site("SID-000001")) == 1
    assert len(site_coll.find_by_location("LOC-000001")) == 1
    assert len(site_coll.find_by_target("IND-000001")) == 1
    p_site = tmp_path / "site_x.json"
    site_coll.export_file(p_site)
    SiteXRefCollection().import_file(p_site)
    site_coll.clear()

    # 8. SurnameXRefCollection
    sur_coll = SurnameXRefCollection.from_database(seeded_session)
    sur_x = SurnameXRef(
        canonical_surname="LEHMAN",
        variant_surname="LEHMANN",
        variant_name_type=HistoricNameType.HISTORICAL,
        variant_phonetic_code="L550",
    )
    sur_coll.add(sur_x)
    assert len(sur_coll.find_by_canonical_surname("lehman")) == 1
    assert len(sur_coll.find_by_variant_surname("lehmann")) == 1
    p_sur = tmp_path / "sur_x.json"
    sur_coll.export_file(p_sur)
    SurnameXRefCollection().import_file(p_sur)
    sur_coll.clear()
