"""Path: tests/test_gda/test_repository/test_probate/test_collection.py

Unit and integration tests for Probate domain collections
(src/gda/repository/probate/collection.py).
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

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
from gda.model.source.probate.inventory import EstateInventoryRecord
from gda.model.source.probate.will import ProbateRecord
from gda.repository.probate.collection import (
    EstateInventoryCollection,
    ProbateCollection,
)


def _audit() -> AuditStamp:
    ts = IsoTimestamp("2026-01-01T00:00:00Z")
    return AuditStamp(created_at=ts, updated_at=ts)


def test_probate_collections_indexing_and_roundtrip(
    seeded_session: DatabaseSessionManager,
    tmp_path: Path,
) -> None:
    """Verify secondary index buckets, editing, and JSON round-tripping for Probate collections."""
    # 1. ProbateCollection
    prob_coll = ProbateCollection.from_database(seeded_session)
    will = ProbateRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000121"),
        source_urn=SourceURN("URN:SRC:1874:US_PA:WILL_121"),
        record_type=SourceRecordType.LAST_WILL_AND_TESTAMENT,
        description="Will of John Lehman",
        repository_id=RepositoryID("REP-000001"),
        audit=_audit(),
        court_name="Orphans' Court",
        filing_locator="Book P, p. 112",
        decedent_name_raw="John Lehman",
        decedent_id=IndividualID("IND-000001"),
        court_location_id=LocationID("LOC-000001"),
        date_probated=EventDate.from_dict("1874-05-12"),
    )
    prob_coll.add(will)
    assert len(prob_coll.find_by_decedent("IND-000001")) == 1
    assert len(prob_coll.find_by_court_location("LOC-000001")) == 1
    prob_coll.edit(will.source_id, decedent_id=None, court_location_id=None)
    assert len(prob_coll.find_by_decedent("IND-000001")) == 0
    assert len(prob_coll.find_by_court_location("LOC-000001")) == 0
    prob_coll.edit(will.source_id, description="Will None Branch")
    prob_coll.add(
        dataclasses.replace(
            will,
            source_id=SourceID("00000000-0000-4000-8000-000000000321"),
            source_urn=SourceURN("URN:SRC:1874:US_PA:WILL_321"),
            decedent_id=None,
            court_location_id=None,
        )
    )
    p_will = tmp_path / "will.json"
    prob_coll.export_file(p_will)
    ProbateCollection().import_file(p_will)

    # 2. EstateInventoryCollection
    inv_coll = EstateInventoryCollection.from_database(seeded_session)
    inv = EstateInventoryRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000122"),
        source_urn=SourceURN("URN:SRC:1874:US_PA:INV_122"),
        record_type=SourceRecordType.ESTATE_INVENTORY,
        description="Inventory of John Lehman",
        repository_id=RepositoryID("REP-000001"),
        audit=_audit(),
        court_name="Orphans' Court",
        filing_locator="Inv 1874-19",
        decedent_name_raw="John Lehman",
        decedent_id=IndividualID("IND-000001"),
        parent_probate_source_id=will.source_id,
    )
    inv_coll.add(inv)
    assert len(inv_coll.find_by_decedent("IND-000001")) == 1
    assert len(inv_coll.find_by_parent_probate_source(will.source_id)) == 1
    inv_coll.edit(
        inv.source_id,
        decedent_id=None,
        parent_probate_source_id=None,
    )
    assert len(inv_coll.find_by_decedent("IND-000001")) == 0
    assert len(inv_coll.find_by_parent_probate_source(will.source_id)) == 0
    inv_coll.edit(inv.source_id, description="Inventory None Branch")
    inv_coll.add(
        dataclasses.replace(
            inv,
            source_id=SourceID("00000000-0000-4000-8000-000000000322"),
            source_urn=SourceURN("URN:SRC:1874:US_PA:INV_322"),
            decedent_id=None,
            parent_probate_source_id=None,
        )
    )
    p_inv = tmp_path / "inv.json"
    inv_coll.export_file(p_inv)
    EstateInventoryCollection().import_file(p_inv)
