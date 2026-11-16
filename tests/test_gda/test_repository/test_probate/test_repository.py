"""Path: tests/test_gda/test_repository/test_probate/test_repository.py

Unit and integration tests for Probate domain SQLite repositories
(src/gda/repository/probate/repository.py).
"""

from __future__ import annotations

from gda.core.enums.probate import (
    BequestType,
    EstatePropertyCategory,
    ProbateLedgerEntryKind,
)
from gda.core.enums.sources import SourceRecordType
from gda.db.session import DatabaseSessionManager
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
from gda.model.source.probate.inventory import (
    EstateInventoryRecord,
    InventoryLineItem,
    ProbateLedgerEntry,
)
from gda.model.source.probate.will import ProbateRecord, WillBequest
from gda.repository.probate.repository import (
    EstateInventoryRepository,
    ProbateRepository,
)


def _audit() -> AuditStamp:
    ts = IsoTimestamp("2026-01-01T00:00:00Z")
    return AuditStamp(created_at=ts, updated_at=ts)


def test_probate_and_inventory_repositories(
    seeded_session: DatabaseSessionManager,
) -> None:
    """Verify ProbateRepository and EstateInventoryRepository CRUD and specialized queries."""
    prob_repo = ProbateRepository(session_manager=seeded_session)
    inv_repo = EstateInventoryRepository(session_manager=seeded_session)

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
        decedent_id=IndividualID("IND-000001"),
        date_written=EventDate.from_dict("1873-11-04"),
        date_probated=EventDate.from_dict("1874-05-12"),
        bequests=(
            WillBequest(
                item_number=1,
                beneficiary_name_raw="Mary Lehman",
                property_or_amount_raw="Homestead farm",
                beneficiary_id=IndividualID("IND-000002"),
                bequest_type=BequestType.REAL_ESTATE,
            ),
        ),
    )

    prob_repo.upsert(will)
    assert prob_repo.get_or_raise(will.source_id) == will
    assert len(prob_repo.find_by_decedent("IND-000001")) == 1
    assert len(prob_repo.find_by_court_location("LOC-000001")) == 1
    assert len(prob_repo.find_by_estate_file_number("EST-1874-19")) == 1
    assert len(prob_repo.find_by_probated_year_range(1870, 1875)) == 1
    assert len(prob_repo.find_by_probated_year_range(1880, 1890)) == 0

    inv = EstateInventoryRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000022"),
        source_urn=SourceURN("URN:SRC:1874:US_PA:INV_022"),
        record_type=SourceRecordType.ESTATE_INVENTORY,
        description="Inventory of John Lehman Estate",
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
                item_description_raw="Two bay mares",
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

    inv_repo.upsert(inv)
    assert inv_repo.get_or_raise(inv.source_id) == inv
    assert len(inv_repo.find_by_decedent("IND-000001")) == 1
    assert len(inv_repo.find_by_parent_probate_source(will.source_id)) == 1
    assert len(inv_repo.find_by_court_location("LOC-000001")) == 1
    assert len(inv_repo.find_by_year_range(1870, 1875)) == 1
