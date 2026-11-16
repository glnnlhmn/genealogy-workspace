"""Path: tests/test_gda/test_repository/test_military/test_repository.py

Unit and integration tests for Military domain SQLite repositories
(src/gda/repository/military/repository.py).
"""

from __future__ import annotations

from gda.core.enums.military import (
    AwardScope,
    BountyLandAct,
    CasualtyCategory,
    DraftCardTier,
    MilitaryAwardTier,
    MilitaryBranch,
    MusterRollType,
    PensionClaimantRole,
    PensionPaymentAuthority,
)
from gda.core.enums.sources import SourceRecordCategory
from gda.db.session import DatabaseSessionManager
from gda.model.atom.date import IsoTimestamp
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
    CombatCasualtyRecord,
    EnlistmentMusterRecord,
    MilitaryAwardRecord,
    PensionVeteranClaimRecord,
    WwiDraftCardRecord,
)
from gda.repository.military.repository import (
    BountyLandWarrantRepository,
    MilitaryAwardRepository,
    MilitaryCasualtyRepository,
    MilitaryDraftRepository,
    MilitaryPensionRepository,
    MilitaryServiceRepository,
)


def _audit() -> AuditStamp:
    ts = IsoTimestamp("2026-01-01T00:00:00Z")
    return AuditStamp(created_at=ts, updated_at=ts)


def test_military_repositories_crud_and_queries(
    seeded_session: DatabaseSessionManager,
) -> None:
    """Verify all 6 Military repositories CRUD and specialized query methods."""
    draft_repo = MilitaryDraftRepository(session_manager=seeded_session)
    srv_repo = MilitaryServiceRepository(session_manager=seeded_session)
    pen_repo = MilitaryPensionRepository(session_manager=seeded_session)
    blw_repo = BountyLandWarrantRepository(session_manager=seeded_session)
    cas_repo = MilitaryCasualtyRepository(session_manager=seeded_session)
    awd_repo = MilitaryAwardRepository(session_manager=seeded_session)

    draft = WwiDraftCardRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000033"),
        source_urn=MilitaryDraftUrn("URN:DRAFT:1917:US_PA:DRF_033"),
        record_category=SourceRecordCategory.MILITARY,
        description="WWI Draft Card",
        repository_id=RepositoryID("REP-000001"),
        audit=_audit(),
        draft_record_id=DraftRecordID("DRF-000001"),
        registrant_id=IndividualID("IND-000001"),
        registrant_name_raw="John Lehman",
        draft_year=HistoricalYear(1917),
        board_jurisdiction_raw="Cumberland Board 1",
        card_tier=DraftCardTier.WWI_FIRST,
        board_location_id=LocationID("LOC-000001"),
    )
    draft_repo.upsert(draft)
    assert draft_repo.get_or_raise(draft.source_id) == draft
    assert len(draft_repo.find_by_registrant("IND-000001")) == 1
    assert len(draft_repo.find_by_year(1917)) == 1
    assert len(draft_repo.find_by_board_location("LOC-000001")) == 1

    service = EnlistmentMusterRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000034"),
        source_urn=SourceURN("URN:SRC:1862:US_PA:SRV_034"),
        record_category=SourceRecordCategory.MILITARY,
        description="Muster Roll",
        repository_id=RepositoryID("REP-000001"),
        audit=_audit(),
        service_record_id=ServiceRecordID("00000000-0000-4000-8000-000000000934"),
        veteran_id=IndividualID("IND-000001"),
        veteran_name_raw="John Lehman",
        branch=MilitaryBranch.ARMY,
        unit_designation_raw="130th PA Infantry",
        rank_raw="Private",
        enlistment_year=HistoricalYear(1862),
        enlistment_location_id=LocationID("LOC-000001"),
        roll_type=MusterRollType.MUSTER_IN,
    )
    srv_repo.upsert(service)
    assert srv_repo.get_or_raise(service.source_id) == service
    assert len(srv_repo.find_by_veteran("IND-000001")) == 1
    assert len(srv_repo.find_by_branch("ARMY")) == 1
    assert len(srv_repo.find_by_enlistment_location("LOC-000001")) == 1

    pension = PensionVeteranClaimRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000035"),
        source_urn=SourceURN("URN:SRC:1890:US_PA:PEN_035"),
        record_category=SourceRecordCategory.MILITARY,
        description="Invalid Pension",
        repository_id=RepositoryID("REP-000001"),
        audit=_audit(),
        veteran_id=IndividualID("IND-000001"),
        veteran_name_raw="John Lehman",
        claimant_id=IndividualID("IND-000001"),
        claimant_name_raw="John Lehman",
        claimant_role=PensionClaimantRole.VETERAN,
        payment_authority=PensionPaymentAuthority.US_BUREAU_OF_PENSIONS,
        application_year=HistoricalYear(1890),
        application_location_id=LocationID("LOC-000001"),
        disability_description_raw="Rheumatism",
    )
    pen_repo.upsert(pension)
    assert pen_repo.get_or_raise(pension.source_id) == pension
    assert len(pen_repo.find_by_veteran("IND-000001")) == 1
    assert len(pen_repo.find_by_claimant("IND-000001")) == 1
    assert len(pen_repo.find_by_application_year(1890)) == 1

    warrant = BountyLandWarrantRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000036"),
        source_urn=SourceURN("URN:SRC:1855:US_PA:BLW_036"),
        record_category=SourceRecordCategory.MILITARY,
        description="Bounty Warrant",
        repository_id=RepositoryID("REP-000001"),
        audit=_audit(),
        veteran_id=IndividualID("IND-000001"),
        veteran_name_raw="John Lehman",
        warrantee_id=IndividualID("IND-000001"),
        warrantee_name_raw="John Lehman",
        claimant_role=PensionClaimantRole.VETERAN,
        bounty_act=BountyLandAct.ACT_OF_1855,
        warrant_number_raw="BLW-160-55",
        acreage=160,
        warrant_year=HistoricalYear(1855),
        patent_location_id=LocationID("LOC-000001"),
    )
    blw_repo.upsert(warrant)
    assert blw_repo.get_or_raise(warrant.source_id) == warrant
    assert len(blw_repo.find_by_veteran("IND-000001")) == 1
    assert len(blw_repo.find_by_warrantee("IND-000001")) == 1
    assert len(blw_repo.find_by_warrant_year(1855)) == 1

    casualty = CombatCasualtyRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000037"),
        source_urn=SourceURN("URN:SRC:1862:US_PA:CAS_037"),
        record_category=SourceRecordCategory.MILITARY,
        description="Casualty Return",
        repository_id=RepositoryID("REP-000001"),
        audit=_audit(),
        servicemember_id=IndividualID("IND-000001"),
        servicemember_name_raw="John Lehman",
        branch=MilitaryBranch.ARMY,
        casualty_category=CasualtyCategory.WOUNDED_IN_ACTION,
        casualty_year=HistoricalYear(1862),
        unit_designation_raw="130th PA Infantry",
        rank_raw="Private",
        casualty_location_id=LocationID("LOC-000001"),
        engagement_name_raw="Antietam",
    )
    cas_repo.upsert(casualty)
    assert cas_repo.get_or_raise(casualty.source_id) == casualty
    assert len(cas_repo.find_by_servicemember("IND-000001")) == 1
    assert len(cas_repo.find_by_year(1862)) == 1
    assert len(cas_repo.find_by_location("LOC-000001")) == 1

    award = MilitaryAwardRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000038"),
        source_urn=SourceURN("URN:SRC:1918:US_PA:AWD_038"),
        record_category=SourceRecordCategory.MILITARY,
        description="Purple Heart",
        repository_id=RepositoryID("REP-000001"),
        audit=_audit(),
        recipient_id=IndividualID("IND-000001"),
        recipient_name_raw="John Lehman",
        award_name_raw="Purple Heart",
        branch=MilitaryBranch.ARMY,
        award_tier=MilitaryAwardTier.PURPLE_HEART,
        award_scope=AwardScope.WOUND_IN_ACTION,
        award_year=HistoricalYear(1918),
        action_location_id=LocationID("LOC-000001"),
    )
    awd_repo.upsert(award)
    assert awd_repo.get_or_raise(award.source_id) == award
    assert len(awd_repo.find_by_recipient("IND-000001")) == 1
    assert len(awd_repo.find_by_award_year(1918)) == 1
    assert len(awd_repo.find_by_award_tier("PURPLE_HEART")) == 1
