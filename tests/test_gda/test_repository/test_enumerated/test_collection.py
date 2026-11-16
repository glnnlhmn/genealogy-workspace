"""Path: tests/test_gda/test_repository/test_enumerated/test_collection.py

Unit and integration tests for Enumerated domain collections
(src/gda/repository/enumerated/collection.py).
"""

from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import Any

from gda.core.enums.fiscal import ResidentialStatus, TaxpayerClassification
from gda.core.enums.sources import SourceRecordCategory, SourceRecordType
from gda.db.session import DatabaseSessionManager
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import IndividualID, LocationID, RepositoryID, SourceID
from gda.model.atom.urn import CensusUrn, SourceURN
from gda.model.atom.year import HistoricalYear
from gda.model.base.audit import AuditStamp
from gda.model.source.enumerated import (
    AgriculturalScheduleEntry,
    AgriculturalScheduleRecord,
    DirectoryEntry,
    DirectoryRollRecord,
    HouseholdTallyEntry,
    Population1850_1870Entry,
    Population1880Entry,
    Population1900_1910Entry,
    Population1920Entry,
    PopulationLineEntry,
    PopulationSchedule1790_1840,
    PopulationSchedule1850_1870,
    PopulationSchedule1880,
    PopulationSchedule1900_1910,
    PopulationSchedule1920,
    PopulationScheduleRecord,
    SeptennialCensusRecord,
    TaxAssessmentRecord,
)
from gda.repository.enumerated.collection import (
    DirectoryRollCollection,
    PopulationScheduleCollection,
    SupplementalScheduleCollection,
    TaxAssessmentCollection,
)


def _audit() -> AuditStamp:
    ts = IsoTimestamp("2026-01-01T00:00:00Z")
    return AuditStamp(created_at=ts, updated_at=ts)


def test_enumerated_collections_indexing_and_roundtrip(
    seeded_session: DatabaseSessionManager,
    tmp_path: Path,
) -> None:
    """Verify secondary index buckets, editing, and JSON round-tripping across all 4 Enumerated collections."""
    # 1. PopulationScheduleCollection
    pop_coll = PopulationScheduleCollection.from_database(seeded_session)
    schedules: list[PopulationScheduleRecord[Any]] = [
        PopulationSchedule1790_1840(
            source_id=SourceID("00000000-0000-4000-8000-000000000201"),
            source_urn=CensusUrn("URN:CENSUS:1800:US_PA:S1"),
            record_category=SourceRecordCategory.CENSUS,
            description="1800",
            repository_id=RepositoryID("REP-000001"),
            audit=_audit(),
            enumeration_year=HistoricalYear(1800),
            jurisdiction_raw="PA",
            jurisdiction_id=LocationID("LOC-000001"),
            state="PA",
            county="Cumberland",
            entries=(
                HouseholdTallyEntry(
                    entry_urn=CensusUrn("URN:CENSUS:1800:US_PA:S1_L1"),
                    line_number=1,
                    name_verbatim="John Lehman",
                ),
            ),
        ),
        PopulationSchedule1850_1870(
            source_id=SourceID("00000000-0000-4000-8000-000000000202"),
            source_urn=CensusUrn("URN:CENSUS:1860:US_PA:S2"),
            record_category=SourceRecordCategory.CENSUS,
            description="1860",
            repository_id=RepositoryID("REP-000001"),
            audit=_audit(),
            enumeration_year=HistoricalYear(1860),
            jurisdiction_raw="PA",
            state="PA",
            county="Cumberland",
            entries=(
                Population1850_1870Entry(
                    entry_urn=CensusUrn("URN:CENSUS:1860:US_PA:S2_L1"),
                    line_number=1,
                    name_verbatim="John Lehman",
                ),
            ),
        ),
        PopulationSchedule1880(
            source_id=SourceID("00000000-0000-4000-8000-000000000203"),
            source_urn=CensusUrn("URN:CENSUS:1880:US_PA:S3"),
            record_category=SourceRecordCategory.CENSUS,
            description="1880",
            repository_id=RepositoryID("REP-000001"),
            audit=_audit(),
            enumeration_year=HistoricalYear(1880),
            jurisdiction_raw="PA",
            state="PA",
            county="Cumberland",
            entries=(
                Population1880Entry(
                    entry_urn=CensusUrn("URN:CENSUS:1880:US_PA:S3_L1"),
                    line_number=1,
                    name_verbatim="John Lehman",
                ),
            ),
        ),
        PopulationSchedule1900_1910(
            source_id=SourceID("00000000-0000-4000-8000-000000000204"),
            source_urn=CensusUrn("URN:CENSUS:1900:US_PA:S4"),
            record_category=SourceRecordCategory.CENSUS,
            description="1900",
            repository_id=RepositoryID("REP-000001"),
            audit=_audit(),
            enumeration_year=HistoricalYear(1900),
            jurisdiction_raw="PA",
            state="PA",
            county="Cumberland",
            entries=(
                Population1900_1910Entry(
                    entry_urn=CensusUrn("URN:CENSUS:1900:US_PA:S4_L1"),
                    line_number=1,
                    name_verbatim="John Lehman",
                ),
            ),
        ),
        PopulationSchedule1920(
            source_id=SourceID("00000000-0000-4000-8000-000000000205"),
            source_urn=CensusUrn("URN:CENSUS:1920:US_PA:S5"),
            record_category=SourceRecordCategory.CENSUS,
            description="1920",
            repository_id=RepositoryID("REP-000001"),
            audit=_audit(),
            enumeration_year=HistoricalYear(1920),
            jurisdiction_raw="PA",
            state="PA",
            county="Cumberland",
            entries=(
                Population1920Entry(
                    entry_urn=CensusUrn("URN:CENSUS:1920:US_PA:S5_L1"),
                    line_number=1,
                    name_verbatim="John Lehman",
                ),
            ),
        ),
        PopulationScheduleRecord(
            source_id=SourceID("00000000-0000-4000-8000-000000000206"),
            source_urn=CensusUrn("URN:CENSUS:1890:US_PA:S6"),
            record_category=SourceRecordCategory.CENSUS,
            description="1890 Generic",
            repository_id=RepositoryID("REP-000001"),
            audit=_audit(),
            enumeration_year=HistoricalYear(1890),
            jurisdiction_raw="PA",
            state="PA",
            county="Cumberland",
            entries=(
                PopulationLineEntry(
                    entry_urn=CensusUrn("URN:CENSUS:1890:US_PA:S6_L1"),
                    line_number=1,
                    name_verbatim="John Lehman",
                ),
            ),
        ),
    ]
    for sch in schedules:
        pop_coll.add(sch)
    assert len(pop_coll.find_by_year(1800)) == 1
    assert len(pop_coll.find_by_jurisdiction("LOC-000001")) == 1
    pop_coll.edit(schedules[0].source_id, jurisdiction_id=None)
    assert len(pop_coll.find_by_jurisdiction("LOC-000001")) == 0
    pop_coll.edit(schedules[0].source_id, description="Pop None Branch")
    p_pop = tmp_path / "pop.json"
    pop_coll.export_file(p_pop)
    pop_imported = PopulationScheduleCollection()
    pop_imported.import_file(p_pop)
    raw_1800 = schedules[0].to_dict()
    raw_1800["entries"][0]["age_bracket_tallies"] = {}
    pop_imported._deserialize_record(raw_1800)

    # 2. SupplementalScheduleCollection
    supp_coll = SupplementalScheduleCollection.from_database(seeded_session)
    ag = AgriculturalScheduleRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000207"),
        source_urn=CensusUrn("URN:CENSUS:1880:US_PA:AG1"),
        record_category=SourceRecordCategory.CENSUS,
        description="Ag",
        repository_id=RepositoryID("REP-000001"),
        audit=_audit(),
        enumeration_year=HistoricalYear(1880),
        jurisdiction_raw="PA",
        jurisdiction_id=LocationID("LOC-000001"),
        state="PA",
        county="Cumberland",
        entries=(
            AgriculturalScheduleEntry(
                entry_urn=CensusUrn("URN:CENSUS:1880:US_PA:AG1_L1"),
                line_number=1,
                name_verbatim="John Lehman",
            ),
        ),
    )
    supp_coll.add(ag)
    assert len(supp_coll.find_by_year(1880)) == 1
    assert len(supp_coll.find_by_jurisdiction("LOC-000001")) == 1
    supp_coll.edit(ag.source_id, jurisdiction_id=None)
    assert len(supp_coll.find_by_jurisdiction("LOC-000001")) == 0
    supp_coll.edit(ag.source_id, description="Supp None Branch")
    supp_coll.add(
        dataclasses.replace(
            ag,
            source_id=SourceID("00000000-0000-4000-8000-000000000307"),
            source_urn=CensusUrn("URN:CENSUS:1880:US_PA:AG307"),
            jurisdiction_id=None,
        )
    )
    p_supp = tmp_path / "supp.json"
    supp_coll.export_file(p_supp)
    SupplementalScheduleCollection().import_file(p_supp)

    # 3. DirectoryRollCollection
    dir_coll = DirectoryRollCollection.from_database(seeded_session)
    drec = DirectoryRollRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000208"),
        source_urn=SourceURN("URN:SRC:1890:US_PA:DIR208"),
        record_category=SourceRecordCategory.DIRECTORY,
        record_type=SourceRecordType.CITY_DIRECTORY,
        description="Dir",
        repository_id=RepositoryID("REP-000001"),
        audit=_audit(),
        enumeration_year=HistoricalYear(1890),
        jurisdiction_raw="Carlisle",
        jurisdiction_id=LocationID("LOC-000001"),
        publication_title_raw="Boyd's",
        entries=(
            DirectoryEntry(
                entry_urn=SourceURN("URN:SRC:1890:US_PA:DIR208_E1"),
                name_verbatim="Lehman, John",
                residential_status=ResidentialStatus.HOUSEHOLDER,
            ),
        ),
    )
    dir_coll.add(drec)
    assert len(dir_coll.find_by_year(1890)) == 1
    assert len(dir_coll.find_by_jurisdiction("LOC-000001")) == 1
    dir_coll.edit(drec.source_id, jurisdiction_id=None)
    assert len(dir_coll.find_by_jurisdiction("LOC-000001")) == 0
    dir_coll.edit(drec.source_id, description="Dir None Branch")
    dir_coll.add(
        dataclasses.replace(
            drec,
            source_id=SourceID("00000000-0000-4000-8000-000000000308"),
            source_urn=SourceURN("URN:SRC:1890:US_PA:DIR308"),
            jurisdiction_id=None,
        )
    )
    p_dir = tmp_path / "dir.json"
    dir_coll.export_file(p_dir)
    DirectoryRollCollection().import_file(p_dir)

    # 4. TaxAssessmentCollection (Tax + Septennial)
    tax_coll = TaxAssessmentCollection.from_database(seeded_session)
    trec = TaxAssessmentRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000209"),
        source_urn=SourceURN("URN:SRC:1835:US_PA:TAX209"),
        record_category=SourceRecordCategory.TAX,
        record_type=SourceRecordType.REAL_ESTATE_TAX,
        description="Tax",
        repository_id=RepositoryID("REP-000001"),
        audit=_audit(),
        enumeration_year=HistoricalYear(1835),
        jurisdiction_raw="Carlisle",
        roll_locator_raw="Vol 1",
        taxpayer_id=IndividualID("IND-000001"),
        taxpayer_name_raw="John Lehman",
        classification=TaxpayerClassification.FREEHOLDER,
    )
    srec = SeptennialCensusRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000210"),
        source_urn=SourceURN("URN:SRC:1800:US_PA:SEP210"),
        description="Septennial",
        repository_id=RepositoryID("REP-000001"),
        audit=_audit(),
        enumeration_year=HistoricalYear(1800),
        jurisdiction_raw="Carlisle",
        roll_locator_raw="Roll 1",
        taxpayer_name_raw="John Lehman",
    )
    tax_coll.add(trec)
    tax_coll.add(srec)
    assert len(tax_coll.find_by_year(1835)) == 1
    assert len(tax_coll.find_by_taxpayer("IND-000001")) == 1
    tax_coll.edit(trec.source_id, taxpayer_id=None)
    assert len(tax_coll.find_by_taxpayer("IND-000001")) == 0
    tax_coll.edit(trec.source_id, description="Tax None Branch")
    p_tax = tmp_path / "tax.json"
    tax_coll.export_file(p_tax)
    TaxAssessmentCollection().import_file(p_tax)
