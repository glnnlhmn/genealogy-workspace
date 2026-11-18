"""Path: tests/test_gda/test_repository/test_military/test_collection.py

Unit and integration tests for Military domain collections
(src/gda/repository/military/collection.py).
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

from gda.core.enums.military import (
    AwardScope,
    BountyLandAct,
    CasualtyCategory,
    DraftCardTier,
    IntermentCemeteryType,
    MilitaryAwardTier,
    MilitaryBranch,
    ModernDraftEra,
    MusterRollType,
    PensionClaimantRole,
    PensionPaymentAuthority,
    PowCampType,
    SeparationFormType,
    WwiiDraftWave,
)
from gda.core.enums.sources import SourceRecordCategory
from gda.db.session import DatabaseSessionManager
from gda.model.atom.id import (
    DraftRecordID,
    IndividualID,
    LocationID,
    RepositoryID,
    ServiceRecordID,
    SourceID,
)
from gda.model.atom.urn import MilitaryDraftUrn, SourceURN
from gda.model.atom.year import HistoricalYear
from gda.model.base.audit import AuditStamp
from gda.model.source.military import (
    BountyLandWarrantRecord,
    CivilWarDraftRecord,
    ColonialMilitiaRecord,
    CombatCasualtyRecord,
    EnlistmentMusterRecord,
    MilitaryAwardRecord,
    MilitaryBurialRecord,
    MilitaryCasualtyRecord,
    MilitaryDraftRecord,
    MilitaryPensionRecord,
    MilitaryServiceRecord,
    ModernSelectiveServiceRecord,
    PensionVeteranClaimRecord,
    PensionWidowDependentRecord,
    PrisonerOfWarRecord,
    SeparationDischargeRecord,
    WwiDraftCardRecord,
    WwiiDraftCardRecord,
)
from gda.repository.military.collection import (
    BountyLandWarrantCollection,
    MilitaryAwardCollection,
    MilitaryCasualtyCollection,
    MilitaryDraftCollection,
    MilitaryPensionCollection,
    MilitaryServiceCollection,
)


def test_military_collections_indexing_and_roundtrip(
    seeded_session: DatabaseSessionManager,
    golden_audit: AuditStamp,
    valid_repo_id: RepositoryID,
    sample_individual_id: IndividualID,
    sample_location_id: LocationID,
    tmp_path: Path,
) -> None:
    """Verify secondary index buckets, editing, and polymorphic JSON round-tripping across all 6 Military collections."""
    # 1. MilitaryDraftCollection (all 6 polymorphic draft classes)
    draft_coll = MilitaryDraftCollection.from_database(seeded_session)
    draft_records: list[MilitaryDraftRecord] = [
        ColonialMilitiaRecord(
            source_id=SourceID("00000000-0000-4000-8000-000000000401"),
            source_urn=MilitaryDraftUrn("URN:DRAFT:1776:US_PA:DRF_401"),
            record_category=SourceRecordCategory.MILITARY,
            description="Colonial Militia",
            repository_id=valid_repo_id,
            audit=golden_audit,
            draft_record_id=DraftRecordID("DRF-000001"),
            registrant_id=sample_individual_id,
            registrant_name_raw="John Lehman",
            draft_year=HistoricalYear(1776),
            board_jurisdiction_raw="Cumberland",
            board_location_id=sample_location_id,
            colony_or_state_raw="Province of Pennsylvania",
        ),
        CivilWarDraftRecord(
            source_id=SourceID("00000000-0000-4000-8000-000000000402"),
            source_urn=MilitaryDraftUrn("URN:DRAFT:1863:US_PA:DRF_402"),
            record_category=SourceRecordCategory.MILITARY,
            description="CW Draft",
            repository_id=valid_repo_id,
            audit=golden_audit,
            draft_record_id=DraftRecordID("DRF-000002"),
            registrant_id=sample_individual_id,
            registrant_name_raw="John Lehman",
            draft_year=HistoricalYear(1863),
            board_jurisdiction_raw="15th District",
        ),
        WwiDraftCardRecord(
            source_id=SourceID("00000000-0000-4000-8000-000000000403"),
            source_urn=MilitaryDraftUrn("URN:DRAFT:1917:US_PA:DRF_403"),
            record_category=SourceRecordCategory.MILITARY,
            description="WWI Draft",
            repository_id=valid_repo_id,
            audit=golden_audit,
            draft_record_id=DraftRecordID("DRF-000003"),
            registrant_id=sample_individual_id,
            registrant_name_raw="John Lehman",
            draft_year=HistoricalYear(1917),
            board_jurisdiction_raw="Board 1",
            card_tier=DraftCardTier.WWI_FIRST,
        ),
        WwiiDraftCardRecord(
            source_id=SourceID("00000000-0000-4000-8000-000000000404"),
            source_urn=MilitaryDraftUrn("URN:DRAFT:1942:US_PA:DRF_404"),
            record_category=SourceRecordCategory.MILITARY,
            description="WWII Draft",
            repository_id=valid_repo_id,
            audit=golden_audit,
            draft_record_id=DraftRecordID("DRF-000004"),
            registrant_id=sample_individual_id,
            registrant_name_raw="John Lehman",
            draft_year=HistoricalYear(1942),
            board_jurisdiction_raw="Board 1",
            card_tier=DraftCardTier.WWII_FOURTH,
            draft_wave=WwiiDraftWave.FOURTH_OLD_MANS,
        ),
        ModernSelectiveServiceRecord(
            source_id=SourceID("00000000-0000-4000-8000-000000000405"),
            source_urn=MilitaryDraftUrn("URN:DRAFT:1970:US_PA:DRF_405"),
            record_category=SourceRecordCategory.MILITARY,
            description="Modern SSS",
            repository_id=valid_repo_id,
            audit=golden_audit,
            draft_record_id=DraftRecordID("DRF-000005"),
            registrant_id=sample_individual_id,
            registrant_name_raw="John Lehman",
            draft_year=HistoricalYear(1970),
            board_jurisdiction_raw="Board 1",
            draft_era=ModernDraftEra.VIETNAM_LOTTERY,
        ),
        MilitaryDraftRecord(
            source_id=SourceID("00000000-0000-4000-8000-000000000406"),
            source_urn=MilitaryDraftUrn("URN:DRAFT:1812:US_PA:DRF_406"),
            record_category=SourceRecordCategory.MILITARY,
            description="Base Draft",
            repository_id=valid_repo_id,
            audit=golden_audit,
            draft_record_id=DraftRecordID("DRF-000006"),
            registrant_id=sample_individual_id,
            registrant_name_raw="John Lehman",
            draft_year=HistoricalYear(1812),
            board_jurisdiction_raw="Board 1",
        ),
    ]
    for drec in draft_records:
        draft_coll.add(drec)
    assert len(draft_coll.find_by_registrant("IND-000001")) == 6
    assert len(draft_coll.find_by_board_location("LOC-000001")) == 1
    draft_coll.edit(draft_records[0].source_id, board_location_id=None)
    assert len(draft_coll.find_by_board_location("LOC-000001")) == 0
    draft_coll.edit(draft_records[0].source_id, description="Draft None Branch")
    p_drf = tmp_path / "draft.json"
    draft_coll.export_file(p_drf)
    MilitaryDraftCollection().import_file(p_drf)

    # 2. MilitaryServiceCollection (all 3 polymorphic service classes)
    srv_coll = MilitaryServiceCollection.from_database(seeded_session)
    srv_records: list[MilitaryServiceRecord] = [
        EnlistmentMusterRecord(
            source_id=SourceID("00000000-0000-4000-8000-000000000411"),
            source_urn=SourceURN("URN:SRC:1862:US_PA:SRV_411"),
            record_category=SourceRecordCategory.MILITARY,
            description="Enlistment",
            repository_id=valid_repo_id,
            audit=golden_audit,
            service_record_id=ServiceRecordID("00000000-0000-4000-8000-000000000911"),
            veteran_id=sample_individual_id,
            veteran_name_raw="John Lehman",
            branch=MilitaryBranch.ARMY,
            unit_designation_raw="130th PA",
            rank_raw="Private",
            enlistment_location_id=sample_location_id,
            roll_type=MusterRollType.MUSTER_IN,
        ),
        SeparationDischargeRecord(
            source_id=SourceID("00000000-0000-4000-8000-000000000412"),
            source_urn=SourceURN("URN:SRC:1945:US_PA:SRV_412"),
            record_category=SourceRecordCategory.MILITARY,
            description="Separation",
            repository_id=valid_repo_id,
            audit=golden_audit,
            service_record_id=ServiceRecordID("00000000-0000-4000-8000-000000000912"),
            veteran_id=sample_individual_id,
            veteran_name_raw="John Lehman",
            branch=MilitaryBranch.ARMY,
            unit_designation_raw="28th Infantry Division",
            rank_raw="Sergeant",
            separation_year=HistoricalYear(1945),
            form_type=SeparationFormType.WD_AGO_53_55,
        ),
        MilitaryServiceRecord(
            source_id=SourceID("00000000-0000-4000-8000-000000000413"),
            source_urn=SourceURN("URN:SRC:1898:US_PA:SRV_413"),
            record_category=SourceRecordCategory.MILITARY,
            description="Base Service",
            repository_id=valid_repo_id,
            audit=golden_audit,
            service_record_id=ServiceRecordID("00000000-0000-4000-8000-000000000913"),
            veteran_id=sample_individual_id,
            veteran_name_raw="John Lehman",
            branch=MilitaryBranch.ARMY,
            unit_designation_raw="8th PA Vol",
            rank_raw="Private",
        ),
    ]
    for srec in srv_records:
        srv_coll.add(srec)
    assert len(srv_coll.find_by_veteran("IND-000001")) == 3
    assert len(srv_coll.find_by_enlistment_location("LOC-000001")) == 1
    srv_coll.edit(srv_records[0].source_id, enlistment_location_id=None)
    assert len(srv_coll.find_by_enlistment_location("LOC-000001")) == 0
    srv_coll.edit(srv_records[0].source_id, description="Srv None Branch")
    p_srv = tmp_path / "srv.json"
    srv_coll.export_file(p_srv)
    MilitaryServiceCollection().import_file(p_srv)

    # 3. MilitaryPensionCollection (all 3 polymorphic pension classes)
    pen_coll = MilitaryPensionCollection.from_database(seeded_session)
    pen_records: list[MilitaryPensionRecord] = [
        PensionVeteranClaimRecord(
            source_id=SourceID("00000000-0000-4000-8000-000000000421"),
            source_urn=SourceURN("URN:SRC:1890:US_PA:PEN_421"),
            record_category=SourceRecordCategory.MILITARY,
            description="Veteran Claim",
            repository_id=valid_repo_id,
            audit=golden_audit,
            veteran_id=sample_individual_id,
            veteran_name_raw="John Lehman",
            claimant_id=sample_individual_id,
            claimant_name_raw="John Lehman",
            claimant_role=PensionClaimantRole.VETERAN,
            payment_authority=PensionPaymentAuthority.US_BUREAU_OF_PENSIONS,
            application_year=HistoricalYear(1890),
            application_location_id=sample_location_id,
            disability_description_raw="Rheumatism",
        ),
        PensionWidowDependentRecord(
            source_id=SourceID("00000000-0000-4000-8000-000000000422"),
            source_urn=SourceURN("URN:SRC:1923:US_PA:PEN_422"),
            record_category=SourceRecordCategory.MILITARY,
            description="Widow Claim",
            repository_id=valid_repo_id,
            audit=golden_audit,
            veteran_id=sample_individual_id,
            veteran_name_raw="John Lehman",
            claimant_id=IndividualID("IND-000002"),
            claimant_name_raw="Mary Lehman",
            claimant_role=PensionClaimantRole.WIDOW,
            payment_authority=PensionPaymentAuthority.US_BUREAU_OF_PENSIONS,
            application_year=HistoricalYear(1923),
            veteran_death_year=HistoricalYear(1922),
        ),
        MilitaryPensionRecord(
            source_id=SourceID("00000000-0000-4000-8000-000000000423"),
            source_urn=SourceURN("URN:SRC:1880:US_PA:PEN_423"),
            record_category=SourceRecordCategory.MILITARY,
            description="Base Pension",
            repository_id=valid_repo_id,
            audit=golden_audit,
            veteran_id=sample_individual_id,
            veteran_name_raw="John Lehman",
            claimant_id=sample_individual_id,
            claimant_name_raw="John Lehman",
            claimant_role=PensionClaimantRole.VETERAN,
            payment_authority=PensionPaymentAuthority.US_BUREAU_OF_PENSIONS,
            application_year=HistoricalYear(1880),
        ),
    ]
    for prec in pen_records:
        pen_coll.add(prec)
    assert len(pen_coll.find_by_veteran("IND-000001")) == 3
    assert len(pen_coll.find_by_application_location("LOC-000001")) == 1
    pen_coll.edit(pen_records[0].source_id, application_location_id=None)
    assert len(pen_coll.find_by_application_location("LOC-000001")) == 0
    pen_coll.edit(pen_records[0].source_id, description="Pen None Branch")
    p_pen = tmp_path / "pen.json"
    pen_coll.export_file(p_pen)
    MilitaryPensionCollection().import_file(p_pen)

    # 4. BountyLandWarrantCollection
    blw_coll = BountyLandWarrantCollection.from_database(seeded_session)
    warrant = BountyLandWarrantRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000431"),
        source_urn=SourceURN("URN:SRC:1855:US_PA:BLW_431"),
        record_category=SourceRecordCategory.MILITARY,
        description="Bounty Warrant",
        repository_id=valid_repo_id,
        audit=golden_audit,
        veteran_id=sample_individual_id,
        veteran_name_raw="John Lehman",
        warrantee_id=sample_individual_id,
        warrantee_name_raw="John Lehman",
        claimant_role=PensionClaimantRole.VETERAN,
        bounty_act=BountyLandAct.ACT_OF_1855,
        warrant_number_raw="BLW-160",
        acreage=160,
        warrant_year=HistoricalYear(1855),
        patent_location_id=sample_location_id,
    )
    blw_coll.add(warrant)
    assert len(blw_coll.find_by_veteran("IND-000001")) == 1
    assert len(blw_coll.find_by_patent_location("LOC-000001")) == 1
    blw_coll.edit(warrant.source_id, patent_location_id=None)
    assert len(blw_coll.find_by_patent_location("LOC-000001")) == 0
    blw_coll.edit(warrant.source_id, description="BLW None Branch")
    blw_coll.add(
        dataclasses.replace(
            warrant,
            source_id=SourceID("00000000-0000-4000-8000-000000000432"),
            source_urn=SourceURN("URN:SRC:1855:US_PA:BLW_432"),
            patent_location_id=None,
        )
    )
    p_blw = tmp_path / "blw.json"
    blw_coll.export_file(p_blw)
    BountyLandWarrantCollection().import_file(p_blw)

    # 5. MilitaryCasualtyCollection (all 4 polymorphic casualty classes)
    cas_coll = MilitaryCasualtyCollection.from_database(seeded_session)
    cas_records: list[MilitaryCasualtyRecord] = [
        CombatCasualtyRecord(
            source_id=SourceID("00000000-0000-4000-8000-000000000441"),
            source_urn=SourceURN("URN:SRC:1862:US_PA:CAS_441"),
            record_category=SourceRecordCategory.MILITARY,
            description="Combat Casualty",
            repository_id=valid_repo_id,
            audit=golden_audit,
            servicemember_id=sample_individual_id,
            servicemember_name_raw="John Lehman",
            branch=MilitaryBranch.ARMY,
            casualty_category=CasualtyCategory.WOUNDED_IN_ACTION,
            casualty_year=HistoricalYear(1862),
            unit_designation_raw="130th PA",
            rank_raw="Private",
            casualty_location_id=sample_location_id,
            engagement_name_raw="Antietam",
        ),
        MilitaryBurialRecord(
            source_id=SourceID("00000000-0000-4000-8000-000000000442"),
            source_urn=SourceURN("URN:SRC:1863:US_PA:CAS_442"),
            record_category=SourceRecordCategory.MILITARY,
            description="Military Burial",
            repository_id=valid_repo_id,
            audit=golden_audit,
            servicemember_id=sample_individual_id,
            servicemember_name_raw="John Lehman",
            branch=MilitaryBranch.ARMY,
            casualty_category=CasualtyCategory.KILLED_IN_ACTION,
            casualty_year=HistoricalYear(1863),
            unit_designation_raw="130th PA",
            rank_raw="Private",
            cemetery_type=IntermentCemeteryType.NATIONAL_CEMETERY,
            cemetery_name_raw="Gettysburg National Cemetery",
            interment_year=HistoricalYear(1863),
        ),
        PrisonerOfWarRecord(
            source_id=SourceID("00000000-0000-4000-8000-000000000443"),
            source_urn=SourceURN("URN:SRC:1864:US_PA:CAS_443"),
            record_category=SourceRecordCategory.MILITARY,
            description="POW Record",
            repository_id=valid_repo_id,
            audit=golden_audit,
            servicemember_id=sample_individual_id,
            servicemember_name_raw="John Lehman",
            branch=MilitaryBranch.ARMY,
            casualty_category=CasualtyCategory.PRISONER_OF_WAR,
            casualty_year=HistoricalYear(1864),
            unit_designation_raw="130th PA",
            rank_raw="Private",
            camp_type=PowCampType.CIVIL_WAR_STOCKADE,
            camp_name_raw="Andersonville",
            detaining_power_raw="Confederate States",
            capture_year=HistoricalYear(1864),
        ),
        MilitaryCasualtyRecord(
            source_id=SourceID("00000000-0000-4000-8000-000000000444"),
            source_urn=SourceURN("URN:SRC:1865:US_PA:CAS_444"),
            record_category=SourceRecordCategory.MILITARY,
            description="Base Casualty",
            repository_id=valid_repo_id,
            audit=golden_audit,
            servicemember_id=sample_individual_id,
            servicemember_name_raw="John Lehman",
            branch=MilitaryBranch.ARMY,
            casualty_category=CasualtyCategory.DIED_OF_DISEASE,
            casualty_year=HistoricalYear(1865),
            unit_designation_raw="130th PA",
            rank_raw="Private",
        ),
    ]
    for crec in cas_records:
        cas_coll.add(crec)
    assert len(cas_coll.find_by_servicemember("IND-000001")) == 4
    assert len(cas_coll.find_by_location("LOC-000001")) == 1
    cas_coll.edit(cas_records[0].source_id, casualty_location_id=None)
    assert len(cas_coll.find_by_location("LOC-000001")) == 0
    cas_coll.edit(cas_records[0].source_id, description="Cas None Branch")
    p_cas = tmp_path / "cas.json"
    cas_coll.export_file(p_cas)
    MilitaryCasualtyCollection().import_file(p_cas)

    # 6. MilitaryAwardCollection
    awd_coll = MilitaryAwardCollection.from_database(seeded_session)
    award = MilitaryAwardRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000451"),
        source_urn=SourceURN("URN:SRC:1918:US_PA:AWD_451"),
        record_category=SourceRecordCategory.MILITARY,
        description="Award",
        repository_id=valid_repo_id,
        audit=golden_audit,
        recipient_id=sample_individual_id,
        recipient_name_raw="John Lehman",
        award_name_raw="Purple Heart",
        branch=MilitaryBranch.ARMY,
        award_tier=MilitaryAwardTier.PURPLE_HEART,
        award_scope=AwardScope.WOUND_IN_ACTION,
        award_year=HistoricalYear(1918),
        action_location_id=sample_location_id,
    )
    awd_coll.add(award)
    assert len(awd_coll.find_by_recipient("IND-000001")) == 1
    assert len(awd_coll.find_by_action_location("LOC-000001")) == 1
    awd_coll.edit(award.source_id, action_location_id=None)
    assert len(awd_coll.find_by_action_location("LOC-000001")) == 0
    awd_coll.edit(award.source_id, description="Award None Branch")
    awd_coll.add(
        dataclasses.replace(
            award,
            source_id=SourceID("00000000-0000-4000-8000-000000000452"),
            source_urn=SourceURN("URN:SRC:1918:US_PA:AWD_452"),
            action_location_id=None,
        )
    )
    p_awd = tmp_path / "awd.json"
    awd_coll.export_file(p_awd, include_graveyard=False)
    MilitaryAwardCollection().import_file(p_awd)
