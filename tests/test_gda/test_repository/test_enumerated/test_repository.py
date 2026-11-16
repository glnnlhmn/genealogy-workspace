"""Path: tests/test_gda/test_repository/test_enumerated/test_repository.py

Unit and integration tests for Enumerated domain SQLite repositories
(src/gda/repository/enumerated/repository.py).
"""

from __future__ import annotations

from gda.core.enums.fiscal import ResidentialStatus, TaxpayerClassification
from gda.core.enums.sources import SourceRecordCategory, SourceRecordType
from gda.db.session import DatabaseSessionManager
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import (
    IndividualID,
    LocationID,
    RepositoryID,
    SourceID,
)
from gda.model.atom.urn import CensusUrn, SourceURN
from gda.model.atom.year import HistoricalYear
from gda.model.base.audit import AuditStamp
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
from gda.repository.enumerated.repository import (
    DirectoryRollRepository,
    PopulationScheduleRepository,
    SupplementalScheduleRepository,
    TaxAssessmentRepository,
)


def _audit() -> AuditStamp:
    ts = IsoTimestamp("2026-01-01T00:00:00Z")
    return AuditStamp(created_at=ts, updated_at=ts)


def test_population_and_supplemental_schedule_repositories(
    seeded_session: DatabaseSessionManager,
) -> None:
    """Verify PopulationScheduleRepository and SupplementalScheduleRepository CRUD and queries."""
    pop_repo = PopulationScheduleRepository(session_manager=seeded_session)
    supp_repo = SupplementalScheduleRepository(session_manager=seeded_session)

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

    pop_repo.upsert(pop_1880)
    loaded_pop = pop_repo.get_or_raise(pop_1880.source_id)
    assert isinstance(loaded_pop, PopulationSchedule1880)
    assert loaded_pop == pop_1880
    assert len(pop_repo.find_by_year(1880)) == 1
    assert len(pop_repo.find_by_jurisdiction("LOC-000001")) == 1
    assert len(pop_repo.find_by_state_and_county("PA", "Cumberland")) == 1

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

    supp_repo.upsert(ag_1880)
    loaded_ag = supp_repo.get_or_raise(ag_1880.source_id)
    assert isinstance(loaded_ag, AgriculturalScheduleRecord)
    assert loaded_ag == ag_1880
    assert len(supp_repo.find_by_year(1880)) == 1
    assert len(supp_repo.find_by_schedule_class("AgriculturalScheduleRecord")) == 1
    assert len(supp_repo.find_by_jurisdiction("LOC-000001")) == 1


def test_directory_and_tax_repositories(
    seeded_session: DatabaseSessionManager,
) -> None:
    """Verify DirectoryRollRepository and TaxAssessmentRepository CRUD and queries."""
    dir_repo = DirectoryRollRepository(session_manager=seeded_session)
    tax_repo = TaxAssessmentRepository(session_manager=seeded_session)

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

    dir_repo.upsert(directory)
    assert dir_repo.get_or_raise(directory.source_id) == directory
    assert len(dir_repo.find_by_year(1890)) == 1
    assert len(dir_repo.find_by_jurisdiction("LOC-000001")) == 1
    assert len(dir_repo.find_by_publication_title("Boyd's Cumberland County Directory")) == 1

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

    tax_repo.upsert_many([tax, septennial])
    assert tax_repo.get_or_raise(tax.source_id) == tax
    loaded_sept = tax_repo.get_or_raise(septennial.source_id)
    assert isinstance(loaded_sept, SeptennialCensusRecord)
    assert loaded_sept == septennial
    assert len(tax_repo.find_by_year(1835)) == 1
    assert len(tax_repo.find_by_taxpayer("IND-000001")) == 2
    assert len(tax_repo.find_by_jurisdiction("LOC-000001")) == 2
