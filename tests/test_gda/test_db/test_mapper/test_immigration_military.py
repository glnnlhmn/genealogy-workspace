"""Path: tests/test_gda/test_db/test_mapper/test_immigration_military.py

Unit tests for Immigration and Military row mappers
(src/gda/db/mapper/immigration_military.py).
"""

from __future__ import annotations

import pytest

from gda.core.enums.core import AssociatedRole, Sex
from gda.core.enums.immigration import ArrivalPassageClass, NaturalizationStage
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
    WwiiDraftWave,
)
from gda.core.enums.sources import SourceRecordCategory, SourceRecordType
from gda.db.exceptions import EntityMappingError
from gda.db.mapper.immigration_military import (
    BountyLandWarrantRecordMapper,
    ImmigrationManifestRecordMapper,
    MilitaryAwardRecordMapper,
    MilitaryCasualtyRecordMapper,
    MilitaryDraftRecordMapper,
    MilitaryPensionRecordMapper,
    MilitaryServiceRecordMapper,
    NaturalizationRecordMapper,
    _coerce_military_field,
    _hydrate_polymorphic_record,
    _hydrate_single_military_record,
    _opt_year,
    _serialize_field,
)
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import (
    DraftRecordID,
    IndividualID,
    LocationID,
    MediaID,
    RepositoryID,
    ServiceRecordID,
    SourceID,
)
from gda.model.atom.urn import MilitaryDraftUrn, SourceURN
from gda.model.atom.year import HistoricalYear
from gda.model.base.association import AssociatedIndividual
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate
from gda.model.base.tombstone import Tombstone
from gda.model.source.immigration.manifest import (
    ImmigrationManifestRecord,
    ManifestPassenger,
)
from gda.model.source.immigration.naturalization import (
    NaturalizationRecord,
    NaturalizationWitness,
)
from gda.model.source.military import (
    BountyLandWarrantRecord,
    CombatCasualtyRecord,
    EnlistmentMusterRecord,
    MilitaryAwardRecord,
    PensionVeteranClaimRecord,
    WwiDraftCardRecord,
    WwiiDraftCardRecord,
    WwiiPhysicalMetrics,
    WwiPhysicalDescription,
)


def _audit() -> AuditStamp:
    ts = IsoTimestamp("2026-01-01T00:00:00Z")
    return AuditStamp(created_at=ts, updated_at=ts)


def test_immigration_and_military_mappers_roundtrip() -> None:
    """Verify to_row and from_row round-trip across all 8 Immigration and Military mappers."""
    assert _opt_year(None) is None
    assert _opt_year(HistoricalYear(1918)) == 1918
    assert _serialize_field([1, 2]) == [1, 2]
    assert _coerce_military_field("UnknownType", "raw_val") == "raw_val"

    man_mapper = ImmigrationManifestRecordMapper()
    manifest = ImmigrationManifestRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000031"),
        source_urn=SourceURN("URN:SRC:1882:US_PA:MAN_031"),
        record_type=SourceRecordType.PASSENGER_MANIFEST,
        description="Passenger Manifest of SS Vaderland",
        repository_id=RepositoryID("REP-000001"),
        audit=_audit(),
        port_of_arrival_raw="Philadelphia, PA",
        arrival_date=EventDate.from_dict("1882-05-14"),
        manifest_locator="NARA M425 Roll 102",
        port_of_arrival_id=LocationID("LOC-000001"),
        ship_name="SS Vaderland",
        shipping_line="Red Star Line",
        passengers=(
            ManifestPassenger(
                full_name="Johann Lehman",
                line_number=4,
                individual_id=IndividualID("IND-000001"),
                age_raw="24",
                sex=Sex.MALE,
                passage_class=ArrivalPassageClass.STEERAGE,
            ),
        ),
    )
    assert man_mapper.from_row(man_mapper.to_row(manifest)) == manifest

    nat_mapper = NaturalizationRecordMapper()
    nat = NaturalizationRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000032"),
        source_urn=SourceURN("URN:SRC:1888:US_PA:NAT_032"),
        record_type=SourceRecordType.PETITION_FOR_NATURALIZATION,
        description="Petition for Naturalization of John Lehman",
        repository_id=RepositoryID("REP-000001"),
        audit=_audit(),
        court_name="Court of Common Pleas of Cumberland County",
        docket_locator="Nat Docket B, p. 44",
        applicant_name_raw="John Lehman",
        event_date=EventDate.from_dict("1888-09-10"),
        court_location_id=LocationID("LOC-000001"),
        applicant_id=IndividualID("IND-000001"),
        stage=NaturalizationStage.PETITION,
        witnesses=(
            NaturalizationWitness(
                name="Mary Miller",
                individual_id=IndividualID("IND-000002"),
            ),
        ),
    )
    assert nat_mapper.from_row(nat_mapper.to_row(nat)) == nat

    draft_mapper = MilitaryDraftRecordMapper()
    draft = WwiDraftCardRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000033"),
        source_urn=MilitaryDraftUrn("URN:DRAFT:1917:US_PA:DRF_033"),
        record_category=SourceRecordCategory.MILITARY,
        description="WWI Draft Registration Card of John Lehman",
        repository_id=RepositoryID("REP-000001"),
        audit=_audit(),
        media_ids=[MediaID("00000000-0000-4000-8000-000000000833")],
        associated_people=[AssociatedIndividual.create("IND-000002", AssociatedRole.WITNESS)],
        tombstone=Tombstone[SourceID](
            is_deprecated=True,
            deprecated_at=IsoTimestamp("2026-02-01T00:00:00Z"),
            superseded_by=SourceID("00000000-0000-4000-8000-000000000099"),
        ),
        draft_record_id=DraftRecordID("DRF-000001"),
        registrant_id=IndividualID("IND-000001"),
        registrant_name_raw="John Lehman",
        draft_year=HistoricalYear(1917),
        board_jurisdiction_raw="Cumberland County Local Board No. 1",
        card_tier=DraftCardTier.WWI_FIRST,
        board_location_id=LocationID("LOC-000001"),
        physical_description=WwiPhysicalDescription(
            height_description="Tall",
            build_description="Medium",
            eye_color="Blue",
            hair_color="Brown",
        ),
    )
    assert draft_mapper.from_row(draft_mapper.to_row(draft)) == draft

    wwii_draft = WwiiDraftCardRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000133"),
        source_urn=MilitaryDraftUrn("URN:DRAFT:1942:US_PA:DRF_133"),
        record_category=SourceRecordCategory.MILITARY,
        description="WWII Draft Card",
        repository_id=RepositoryID("REP-000001"),
        audit=_audit(),
        tombstone=Tombstone[SourceID](is_deprecated=False),
        draft_record_id=DraftRecordID("DRF-000002"),
        registrant_id=IndividualID("IND-000001"),
        registrant_name_raw="John Lehman",
        draft_year=HistoricalYear(1942),
        board_jurisdiction_raw="Board 1",
        card_tier=DraftCardTier.WWII_FOURTH,
        draft_wave=WwiiDraftWave.FOURTH_OLD_MANS,
        physical_metrics=WwiiPhysicalMetrics(height_inches=70, weight_lbs=175),
    )
    assert draft_mapper.from_row(draft_mapper.to_row(wwii_draft)) == wwii_draft

    srv_mapper = MilitaryServiceRecordMapper()
    service = EnlistmentMusterRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000034"),
        source_urn=SourceURN("URN:SRC:1862:US_PA:SRV_034"),
        record_category=SourceRecordCategory.MILITARY,
        description="Company Muster-In Roll, 130th PA Infantry",
        repository_id=RepositoryID("REP-000001"),
        audit=_audit(),
        service_record_id=ServiceRecordID("00000000-0000-4000-8000-000000000934"),
        veteran_id=IndividualID("IND-000001"),
        veteran_name_raw="John Lehman",
        branch=MilitaryBranch.ARMY,
        unit_designation_raw="Co. A, 130th Pennsylvania Volunteer Infantry",
        rank_raw="Private",
        enlistment_year=HistoricalYear(1862),
        separation_year=HistoricalYear(1863),
        enlistment_location_id=LocationID("LOC-000001"),
        roll_type=MusterRollType.MUSTER_IN,
    )
    assert srv_mapper.from_row(srv_mapper.to_row(service)) == service

    pen_mapper = MilitaryPensionRecordMapper()
    pension = PensionVeteranClaimRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000035"),
        source_urn=SourceURN("URN:SRC:1890:US_PA:PEN_035"),
        record_category=SourceRecordCategory.MILITARY,
        description="Civil War Invalid Pension Application",
        repository_id=RepositoryID("REP-000001"),
        audit=_audit(),
        veteran_id=IndividualID("IND-000001"),
        veteran_name_raw="John Lehman",
        claimant_id=IndividualID("IND-000001"),
        claimant_name_raw="John Lehman",
        claimant_role=PensionClaimantRole.VETERAN,
        payment_authority=PensionPaymentAuthority.US_BUREAU_OF_PENSIONS,
        application_year=HistoricalYear(1890),
        application_number_raw="SO-842110",
        application_location_id=LocationID("LOC-000001"),
        disability_description_raw="Rheumatism",
    )
    assert pen_mapper.from_row(pen_mapper.to_row(pension)) == pension

    blw_mapper = BountyLandWarrantRecordMapper()
    warrant = BountyLandWarrantRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000036"),
        source_urn=SourceURN("URN:SRC:1855:US_PA:BLW_036"),
        record_category=SourceRecordCategory.MILITARY,
        description="Bounty Land Warrant under Act of 1855",
        repository_id=RepositoryID("REP-000001"),
        audit=_audit(),
        veteran_id=IndividualID("IND-000001"),
        veteran_name_raw="John Lehman",
        warrantee_id=IndividualID("IND-000001"),
        warrantee_name_raw="John Lehman",
        claimant_role=PensionClaimantRole.VETERAN,
        bounty_act=BountyLandAct.ACT_OF_1855,
        warrant_number_raw="BLW-44210-160-55",
        acreage=160,
        warrant_year=HistoricalYear(1855),
        patent_location_id=LocationID("LOC-000001"),
    )
    assert blw_mapper.from_row(blw_mapper.to_row(warrant)) == warrant

    cas_mapper = MilitaryCasualtyRecordMapper()
    casualty = CombatCasualtyRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000037"),
        source_urn=SourceURN("URN:SRC:1862:US_PA:CAS_037"),
        record_category=SourceRecordCategory.MILITARY,
        description="Antietam Casualty Return",
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
        engagement_name_raw="Battle of Antietam",
    )
    assert cas_mapper.from_row(cas_mapper.to_row(casualty)) == casualty

    awd_mapper = MilitaryAwardRecordMapper()
    award = MilitaryAwardRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000038"),
        source_urn=SourceURN("URN:SRC:1918:US_PA:AWD_038"),
        record_category=SourceRecordCategory.MILITARY,
        description="Purple Heart Citation",
        repository_id=RepositoryID("REP-000001"),
        audit=_audit(),
        recipient_id=IndividualID("IND-000001"),
        recipient_name_raw="John Lehman",
        award_name_raw="Purple Heart",
        branch=MilitaryBranch.ARMY,
        award_tier=MilitaryAwardTier.PURPLE_HEART,
        award_scope=AwardScope.WOUND_IN_ACTION,
        award_year=HistoricalYear(1918),
        action_year=HistoricalYear(1918),
        is_posthumous=True,
        action_location_id=LocationID("LOC-000001"),
    )
    assert awd_mapper.from_row(awd_mapper.to_row(award)) == award

    award_living = MilitaryAwardRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000039"),
        source_urn=SourceURN("URN:SRC:1918:US_PA:AWD_039"),
        record_category=SourceRecordCategory.MILITARY,
        description="Bronze Star Citation",
        repository_id=RepositoryID("REP-000001"),
        audit=_audit(),
        recipient_id=IndividualID("IND-000001"),
        recipient_name_raw="John Lehman",
        award_name_raw="Bronze Star",
        branch=MilitaryBranch.ARMY,
        award_tier=MilitaryAwardTier.BRONZE_STAR,
        award_scope=AwardScope.VALOR_IN_COMBAT,
        award_year=HistoricalYear(1918),
        is_posthumous=False,
    )
    assert awd_mapper.from_row(awd_mapper.to_row(award_living)) == award_living


def test_immigration_and_military_mapper_error_branches() -> None:
    """Verify EntityMappingError branches across all 8 Batch 3B mappers."""
    for mapper in (
        ImmigrationManifestRecordMapper(),
        NaturalizationRecordMapper(),
        MilitaryDraftRecordMapper(),
        MilitaryServiceRecordMapper(),
        MilitaryPensionRecordMapper(),
        BountyLandWarrantRecordMapper(),
        MilitaryCasualtyRecordMapper(),
        MilitaryAwardRecordMapper(),
    ):
        with pytest.raises(EntityMappingError):
            mapper.to_row(object())  # type: ignore[arg-type]

    for single_mapper in (
        BountyLandWarrantRecordMapper(),
        MilitaryAwardRecordMapper(),
    ):
        with pytest.raises(EntityMappingError, match="Missing or invalid 'payload_json'"):
            single_mapper.from_row({"payload_json": ""})
        with pytest.raises(EntityMappingError, match="Failed to hydrate"):
            single_mapper.from_row({"payload_json": "{bad-json"})

    for poly_mapper, valid_cls in (
        (MilitaryDraftRecordMapper(), "WwiDraftCardRecord"),
        (MilitaryServiceRecordMapper(), "EnlistmentMusterRecord"),
        (MilitaryPensionRecordMapper(), "PensionVeteranClaimRecord"),
        (MilitaryCasualtyRecordMapper(), "CombatCasualtyRecord"),
    ):
        with pytest.raises(EntityMappingError, match="Unknown"):
            poly_mapper.from_row({"record_class": "UnknownClass", "payload_json": "{}"})
        with pytest.raises(EntityMappingError, match="Missing or invalid 'payload_json'"):
            poly_mapper.from_row({"record_class": valid_cls, "payload_json": ""})
        with pytest.raises(EntityMappingError, match="Failed to hydrate"):
            poly_mapper.from_row({"record_class": valid_cls, "payload_json": "{bad-json"})

    with pytest.raises(EntityMappingError):
        _hydrate_polymorphic_record(
            {"record_class": "WwiDraftCardRecord", "payload_json": None},
            {"WwiDraftCardRecord": WwiDraftCardRecord},
            "draft",
        )
    with pytest.raises(EntityMappingError):
        _hydrate_single_military_record(
            {"payload_json": None},
            MilitaryAwardRecord,
        )
