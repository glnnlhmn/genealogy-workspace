"""Path: tests/test_gda/test_db/test_mapper/test_enumerated_publications.py

Unit tests for Enumerated and Publications row mappers
(src/gda/db/mapper/enumerated_publications.py).
"""

from __future__ import annotations

import pytest

from gda.core.enums.archival import PublicationFrequency
from gda.core.enums.fiscal import ResidentialStatus, TaxpayerClassification
from gda.core.enums.sources import SourceRecordCategory, SourceRecordType
from gda.db.exceptions import EntityMappingError
from gda.db.mapper.enumerated_publications import (
    DirectoryRollRecordMapper,
    NewspaperClipRecordMapper,
    PeriodicalArticleRecordMapper,
    PopulationScheduleMapper,
    PublicationMapper,
    SupplementalScheduleMapper,
    TaxAssessmentRecordMapper,
    _hydrate_polymorphic_payload,
)
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import (
    IndividualID,
    LocationID,
    OrganizationID,
    RepositoryID,
    SourceID,
)
from gda.model.atom.urn import CensusUrn, SourceURN
from gda.model.atom.year import HistoricalYear
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate
from gda.model.base.name import NameThing
from gda.model.source.enumerated import (
    AgriculturalScheduleEntry,
    AgriculturalScheduleRecord,
    AssessedProperty,
    DirectoryEntry,
    DirectoryRollRecord,
    Population1880Entry,
    PopulationSchedule1880,
    SeptennialCensusRecord,
    TaxAssessmentRecord,
)
from gda.model.source.publications import (
    NewspaperClipRecord,
    PeriodicalArticleRecord,
    Publication,
    PublicationEntry,
)


def _audit() -> AuditStamp:
    ts = IsoTimestamp("2026-01-01T00:00:00Z")
    return AuditStamp(created_at=ts, updated_at=ts)


def test_enumerated_and_publications_mappers_roundtrip() -> None:
    """Verify to_row and from_row round-trip across all 7 Enumerated and Publications mappers."""
    pop_mapper = PopulationScheduleMapper()
    pop_1880 = PopulationSchedule1880(
        source_id=SourceID("00000000-0000-4000-8000-000000000011"),
        source_urn=CensusUrn("URN:CENSUS:1880:US_PA:ED12_SH1"),
        record_category=SourceRecordCategory.CENSUS,
        description="1880 US Federal Census, Carlisle, PA",
        repository_id=RepositoryID("REP-000001"),
        audit=_audit(),
        enumeration_year=HistoricalYear(1880),
        jurisdiction_raw="Carlisle, Cumberland County, PA",
        jurisdiction_id=LocationID("LOC-000001"),
        state="PA",
        county="Cumberland",
        township_or_ward="Carlisle Borough",
        enumeration_district="ED-12",
        sheet_number="1A",
        entries=(
            Population1880Entry(
                entry_urn=CensusUrn("URN:CENSUS:1880:US_PA:ED12_SH1_L1"),
                line_number=1,
                name_verbatim="Lehman, John",
                individual_id=IndividualID("IND-000001"),
                age_raw="28",
                sex_raw="M",
                relationship_to_head_raw="Head",
            ),
        ),
    )
    assert pop_mapper.from_row(pop_mapper.to_row(pop_1880)) == pop_1880

    supp_mapper = SupplementalScheduleMapper()
    ag_1880 = AgriculturalScheduleRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000012"),
        source_urn=CensusUrn("URN:CENSUS:1880:US_PA:AG_ED12_SH1"),
        record_category=SourceRecordCategory.CENSUS,
        description="1880 Agricultural Schedule, Cumberland County, PA",
        repository_id=RepositoryID("REP-000001"),
        audit=_audit(),
        enumeration_year=HistoricalYear(1880),
        jurisdiction_raw="Cumberland County, PA",
        jurisdiction_id=LocationID("LOC-000001"),
        state="PA",
        county="Cumberland",
        entries=(
            AgriculturalScheduleEntry(
                entry_urn=CensusUrn("URN:CENSUS:1880:US_PA:AG_ED12_SH1_L1"),
                line_number=1,
                name_verbatim="John Lehman",
                individual_id=IndividualID("IND-000001"),
                improved_acres=120,
                farm_cash_value_usd=4500,
            ),
        ),
    )
    assert supp_mapper.from_row(supp_mapper.to_row(ag_1880)) == ag_1880

    dir_mapper = DirectoryRollRecordMapper()
    directory = DirectoryRollRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000013"),
        source_urn=SourceURN("URN:SRC:1890:US_PA:DIR_CARLISLE_P42"),
        record_category=SourceRecordCategory.DIRECTORY,
        record_type=SourceRecordType.CITY_DIRECTORY,
        description="1890 Carlisle City Directory, p. 42",
        repository_id=RepositoryID("REP-000001"),
        audit=_audit(),
        enumeration_year=HistoricalYear(1890),
        jurisdiction_raw="Carlisle, PA",
        jurisdiction_id=LocationID("LOC-000001"),
        publication_title_raw="Boyd's Cumberland County Directory",
        page_number_raw="42",
        entries=(
            DirectoryEntry(
                entry_urn=SourceURN("URN:SRC:1890:US_PA:DIR_CARLISLE_P42_E1"),
                name_verbatim="Lehman, John",
                individual_id=IndividualID("IND-000001"),
                occupation_verbatim="Blacksmith",
                residence_address_raw="114 N Hanover",
                residential_status=ResidentialStatus.HOUSEHOLDER,
                residence_location_id=LocationID("LOC-000001"),
            ),
        ),
    )
    assert dir_mapper.from_row(dir_mapper.to_row(directory)) == directory

    tax_mapper = TaxAssessmentRecordMapper()
    tax = TaxAssessmentRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000014"),
        source_urn=SourceURN("URN:SRC:1835:US_PA:TAX_CUMB_014"),
        record_category=SourceRecordCategory.TAX,
        record_type=SourceRecordType.REAL_ESTATE_TAX,
        description="1835 County Tax Roll, Carlisle",
        repository_id=RepositoryID("REP-000001"),
        audit=_audit(),
        enumeration_year=HistoricalYear(1835),
        jurisdiction_raw="Carlisle, PA",
        jurisdiction_id=LocationID("LOC-000001"),
        roll_locator_raw="Vol 4, Page 19",
        line_number=8,
        taxpayer_id=IndividualID("IND-000001"),
        taxpayer_name_raw="John Lehman",
        classification=TaxpayerClassification.FREEHOLDER,
        stated_occupation="Yeoman",
        assessed_property=AssessedProperty(acres_seated=85.0, horses=2, cattle_or_cows=4),
    )
    septennial = SeptennialCensusRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000015"),
        source_urn=SourceURN("URN:SRC:1800:US_PA:SEPT_CUMB_015"),
        description="1800 PA Septennial Census, Carlisle",
        repository_id=RepositoryID("REP-000001"),
        audit=_audit(),
        enumeration_year=HistoricalYear(1800),
        jurisdiction_raw="Carlisle, PA",
        jurisdiction_id=LocationID("LOC-000001"),
        roll_locator_raw="Septennial Roll 1800, p. 3",
        taxpayer_id=IndividualID("IND-000001"),
        taxpayer_name_raw="John Lehman",
        deaf_dumb_or_blind_note=None,
    )
    assert tax_mapper.from_row(tax_mapper.to_row(tax)) == tax
    assert tax_mapper.from_row(tax_mapper.to_row(septennial)) == septennial

    pub_mapper = PublicationMapper()
    pub = Publication(
        source_id=SourceID("00000000-0000-4000-8000-000000000016"),
        source_urn=SourceURN("URN:SRC:1850:US_PA:PUB_HERALD"),
        description="Carlisle Herald Master Entry",
        repository_id=RepositoryID("REP-000001"),
        audit=_audit(),
        title=NameThing.create("The Carlisle Herald"),
        pub_code="PA-CARL-HERALD",
        frequency=PublicationFrequency.WEEKLY,
        location_id=LocationID("LOC-000001"),
        is_active=False,
    )
    assert pub_mapper.from_row(pub_mapper.to_row(pub)) == pub

    clip_mapper = NewspaperClipRecordMapper()
    clip = NewspaperClipRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000017"),
        source_urn=SourceURN("URN:SRC:1922:US_PA:CLIP_OBIT_017"),
        record_type=SourceRecordType.MISC,
        description="Obituary of John Lehman",
        repository_id=RepositoryID("REP-000001"),
        audit=_audit(),
        newspaper_name_raw="The Carlisle Herald",
        issue_date=EventDate.from_dict("1922-11-10"),
        news_category="OBITUARY",
        parent_source_id=pub.source_id,
        pub_code="PA-CARL-HERALD",
        publication_location_id=LocationID("LOC-000001"),
        headline_raw="Lifelong Resident Passes",
    )
    assert clip_mapper.from_row(clip_mapper.to_row(clip)) == clip

    art_mapper = PeriodicalArticleRecordMapper()
    article = PeriodicalArticleRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000018"),
        source_urn=SourceURN("URN:SRC:1915:US_PA:ART_ALUMNI_018"),
        record_category=SourceRecordCategory.EDUCATION,
        record_type=SourceRecordType.CLASS_ROSTER,
        description="Dickinson Alumni Quarterly Roster",
        repository_id=RepositoryID("REP-000001"),
        audit=_audit(),
        publication_title_raw="Dickinson Alumni Quarterly",
        date_published=EventDate.from_dict("1915-06-01"),
        publication_kind="Alumni Magazine",
        parent_source_id=pub.source_id,
        pub_code="PA-DICKINSON-Q",
        institution_org_id=OrganizationID("ORG-000001"),
        entries=(
            PublicationEntry(
                line_number=1,
                subject_name_verbatim="John Lehman",
                individual_id=IndividualID("IND-000001"),
                role_or_class_raw="Class of 1874",
            ),
        ),
    )
    assert art_mapper.from_row(art_mapper.to_row(article)) == article


def test_enumerated_and_publications_mapper_error_branches() -> None:
    """Verify EntityMappingError branches across all 7 Batch 2B mappers."""
    for mapper in (
        PopulationScheduleMapper(),
        SupplementalScheduleMapper(),
        DirectoryRollRecordMapper(),
        TaxAssessmentRecordMapper(),
        PublicationMapper(),
        NewspaperClipRecordMapper(),
        PeriodicalArticleRecordMapper(),
    ):
        with pytest.raises(EntityMappingError):
            mapper.to_row(object())  # type: ignore[arg-type]

    for poly_mapper in (
        PopulationScheduleMapper(),
        SupplementalScheduleMapper(),
        TaxAssessmentRecordMapper(),
    ):
        with pytest.raises(EntityMappingError, match="Unknown"):
            poly_mapper.from_row({"schedule_class": "NonExistentClass", "payload_json": "{}"})

        first_cls = next(
            iter(
                {
                    PopulationScheduleMapper: ["PopulationSchedule1880"],
                    SupplementalScheduleMapper: ["AgriculturalScheduleRecord"],
                    TaxAssessmentRecordMapper: ["TaxAssessmentRecord"],
                }[type(poly_mapper)]
            )
        )
        with pytest.raises(EntityMappingError, match="Missing or invalid 'payload_json'"):
            poly_mapper.from_row({"schedule_class": first_cls, "payload_json": ""})

        with pytest.raises(EntityMappingError, match="Failed to hydrate"):
            poly_mapper.from_row({"schedule_class": first_cls, "payload_json": "{invalid"})

    with pytest.raises(EntityMappingError):
        _hydrate_polymorphic_payload(
            {"schedule_class": "TaxAssessmentRecord", "payload_json": None},
            {"TaxAssessmentRecord": TaxAssessmentRecord},
            "tax",
        )
