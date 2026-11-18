"""Path: tests/test_gda/test_db/test_mapper/test_probate_land.py

Unit tests for Probate and Land row mappers (src/gda/db/mapper/probate_land.py).
"""

from __future__ import annotations

import pytest

from gda.core.enums.land import DeedPartyRole, LandGrantBasis
from gda.core.enums.probate import (
    BequestType,
    EstatePropertyCategory,
    ProbateLedgerEntryKind,
)
from gda.core.enums.sources import SourceRecordType
from gda.db.exceptions import EntityMappingError
from gda.db.mapper.probate_land import (
    EstateInventoryRecordMapper,
    LandDeedRecordMapper,
    LandGrantRecordMapper,
    ProbateRecordMapper,
    _opt_bool_int,
)
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import (
    IndividualID,
    LocationID,
    RepositoryID,
    SourceID,
)
from gda.model.atom.urn import SourceURN
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate
from gda.model.source.land.deed import DeedParty, LandDeedRecord, LandParcel
from gda.model.source.land.grant import LandGrantRecord
from gda.model.source.probate.inventory import (
    EstateInventoryRecord,
    InventoryLineItem,
    ProbateLedgerEntry,
)
from gda.model.source.probate.will import ProbateRecord, WillBequest


def _audit() -> AuditStamp:
    ts = IsoTimestamp("2026-01-01T00:00:00Z")
    return AuditStamp(created_at=ts, updated_at=ts)


def test_probate_and_land_mappers_roundtrip() -> None:
    """Verify to_row and from_row round-trip across all 4 Probate and Land mappers."""
    assert _opt_bool_int(None) is None
    assert _opt_bool_int(True) == 1
    assert _opt_bool_int(False) == 0

    prob_mapper = ProbateRecordMapper()
    will = ProbateRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000021"),
        source_urn=SourceURN("URN:SRC:1874:US_PA:WILL_021"),
        record_type=SourceRecordType.LAST_WILL_AND_TESTAMENT,
        description="Last Will and Testament of John Lehman",
        repository_id=RepositoryID("REP-000001"),
        audit=_audit(),
        court_name="Cumberland County Orphans' Court",
        filing_locator="Will Book P, Page 112",
        decedent_name_raw="John Lehman",
        court_location_id=LocationID("LOC-000001"),
        estate_file_number="EST-1874-19",
        book_and_page="Book P, p. 112",
        decedent_id=IndividualID("IND-000001"),
        decedent_residence_id=LocationID("LOC-000001"),
        date_written=EventDate.from_dict("1873-11-04"),
        date_probated=EventDate.from_dict("1874-05-12"),
        date_letters_granted=EventDate.from_dict("1874-05-15"),
        bequests=(
            WillBequest(
                item_number=1,
                beneficiary_name_raw="Mary Lehman",
                property_or_amount_raw="Homestead farm of 120 acres",
                beneficiary_id=IndividualID("IND-000002"),
                relationship_raw="beloved wife",
                bequest_type=BequestType.REAL_ESTATE,
            ),
        ),
    )
    assert prob_mapper.from_row(prob_mapper.to_row(will)) == will

    inv_mapper = EstateInventoryRecordMapper()
    inv = EstateInventoryRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000022"),
        source_urn=SourceURN("URN:SRC:1874:US_PA:INV_022"),
        record_type=SourceRecordType.ESTATE_INVENTORY,
        description="Inventory and Appraisement of John Lehman Estate",
        repository_id=RepositoryID("REP-000001"),
        audit=_audit(),
        court_name="Cumberland County Orphans' Court",
        filing_locator="Inventory File 1874-19",
        decedent_name_raw="John Lehman",
        court_location_id=LocationID("LOC-000001"),
        estate_file_number="EST-1874-19",
        decedent_id=IndividualID("IND-000001"),
        parent_probate_source_id=will.source_id,
        date_appraised_or_accounted=EventDate.from_dict("1874-06-01"),
        total_appraised_value_numeric=1450.50,
        items=(
            InventoryLineItem(
                line_number=1,
                item_description_raw="Two bay mares and harness",
                property_category=EstatePropertyCategory.LIVESTOCK,
                appraised_value_numeric=220.0,
            ),
        ),
        ledger_entries=(
            ProbateLedgerEntry(
                line_number=1,
                party_name_raw="Dr. Samuel Brandt",
                entry_kind=ProbateLedgerEntryKind.DEBT_PAID,
                amount_numeric=18.50,
            ),
        ),
    )
    assert inv_mapper.from_row(inv_mapper.to_row(inv)) == inv

    deed_mapper = LandDeedRecordMapper()
    deed = LandDeedRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000023"),
        source_urn=SourceURN("URN:SRC:1860:US_PA:DEED_023"),
        record_type=SourceRecordType.DEED_INDENTURE,
        description="Deed from John Lehman to Mary Miller",
        repository_id=RepositoryID("REP-000001"),
        audit=_audit(),
        office_title="Recorder of Deeds, Cumberland County",
        recording_locator="Deed Book 2Z, Page 410",
        date_written=EventDate.from_dict("1860-04-01"),
        date_recorded=EventDate.from_dict("1860-04-15"),
        office_location_id=LocationID("LOC-000001"),
        deed_book="2Z",
        page_number="410",
        dower_relinquished=True,
        grantors=(
            DeedParty(
                full_name="John Lehman",
                party_role=DeedPartyRole.GRANTOR,
                individual_id=IndividualID("IND-000001"),
            ),
        ),
        grantees=(
            DeedParty(
                full_name="Mary Miller",
                party_role=DeedPartyRole.GRANTEE,
                individual_id=IndividualID("IND-000002"),
            ),
        ),
        parcel=LandParcel(
            location_raw="South Middleton Township, Cumberland County",
            location_id=LocationID("LOC-000001"),
            acreage_numeric=85.5,
        ),
    )
    assert deed_mapper.from_row(deed_mapper.to_row(deed)) == deed

    grant_mapper = LandGrantRecordMapper()
    grant = LandGrantRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000024"),
        source_urn=SourceURN("URN:SRC:1795:US_PA:PAT_024"),
        record_type=SourceRecordType.PATENT,
        description="Commonwealth of Pennsylvania Land Patent to John Lehman",
        repository_id=RepositoryID("REP-000001"),
        audit=_audit(),
        issuing_authority="Commonwealth of Pennsylvania",
        instrument_locator="Patent Book P-26, Page 88",
        patentee_name_raw="John Lehman",
        office_location_id=LocationID("LOC-000001"),
        patent_or_warrant_number="W-1794-102",
        grant_basis=LandGrantBasis.PROPRIETARY_GRANT,
        patentee_id=IndividualID("IND-000001"),
        assignee_id=IndividualID("IND-000002"),
        date_warrant_or_entry=EventDate.from_dict("1794-03-10"),
        date_surveyed=EventDate.from_dict("1794-09-22"),
        date_patented=EventDate.from_dict("1795-05-01"),
        parcel=LandParcel(
            location_raw="Cumberland County, PA",
            location_id=LocationID("LOC-000001"),
            tract_name="Lehman's Delight",
            acreage_numeric=212.0,
        ),
    )
    assert grant_mapper.from_row(grant_mapper.to_row(grant)) == grant


def test_probate_and_land_mapper_error_branches() -> None:
    """Verify EntityMappingError branches across all 4 Batch 3A mappers."""
    for mapper in (
        ProbateRecordMapper(),
        EstateInventoryRecordMapper(),
        LandDeedRecordMapper(),
        LandGrantRecordMapper(),
    ):
        with pytest.raises(EntityMappingError):
            mapper.to_row(object())  # type: ignore[arg-type]

        with pytest.raises(EntityMappingError, match="Missing or invalid 'payload_json'"):
            mapper.from_row({"id": "00000000-0000-4000-8000-000000000021", "payload_json": ""})

        with pytest.raises(EntityMappingError, match="Failed to hydrate"):
            mapper.from_row(
                {"id": "00000000-0000-4000-8000-000000000021", "payload_json": "{bad-json"}
            )
