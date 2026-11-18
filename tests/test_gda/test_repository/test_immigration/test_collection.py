"""Path: tests/test_gda/test_repository/test_immigration/test_collection.py

Unit and integration tests for Immigration domain collections
(src/gda/repository/immigration/collection.py).
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
from gda.model.source.immigration.manifest import (
    ImmigrationManifestRecord,
    ManifestPassenger,
)
from gda.model.source.immigration.naturalization import NaturalizationRecord
from gda.repository.immigration.collection import (
    ImmigrationManifestCollection,
    NaturalizationCollection,
)


def _audit() -> AuditStamp:
    ts = IsoTimestamp("2026-01-01T00:00:00Z")
    return AuditStamp(created_at=ts, updated_at=ts)


def test_immigration_collections_indexing_and_roundtrip(
    seeded_session: DatabaseSessionManager,
    tmp_path: Path,
) -> None:
    """Verify secondary index buckets, editing, and JSON round-tripping for Immigration collections."""
    # 1. ImmigrationManifestCollection
    man_coll = ImmigrationManifestCollection.from_database(seeded_session)
    manifest = ImmigrationManifestRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000131"),
        source_urn=SourceURN("URN:SRC:1882:US_PA:MAN_131"),
        record_type=SourceRecordType.PASSENGER_MANIFEST,
        description="Manifest",
        repository_id=RepositoryID("REP-000001"),
        audit=_audit(),
        port_of_arrival_raw="Philadelphia",
        arrival_date=EventDate.from_dict("1882-05-14"),
        manifest_locator="M425-102",
        port_of_arrival_id=LocationID("LOC-000001"),
        passengers=(
            ManifestPassenger(
                full_name="Johann Lehman",
                individual_id=IndividualID("IND-000001"),
            ),
        ),
    )
    man_coll.add(manifest)
    assert len(man_coll.find_by_passenger("IND-000001")) == 1
    assert len(man_coll.find_by_port_of_arrival("LOC-000001")) == 1

    man_coll.edit(
        manifest.source_id,
        port_of_arrival_id=None,
        passengers=(ManifestPassenger(full_name="Johann Lehman", individual_id=None),),
    )
    assert len(man_coll.find_by_passenger("IND-000001")) == 0
    assert len(man_coll.find_by_port_of_arrival("LOC-000001")) == 0
    man_coll.edit(manifest.source_id, description="Manifest None Branch")
    man_coll.add(
        dataclasses.replace(
            manifest,
            source_id=SourceID("00000000-0000-4000-8000-000000000331"),
            source_urn=SourceURN("URN:SRC:1882:US_PA:MAN_331"),
            port_of_arrival_id=None,
            passengers=(ManifestPassenger(full_name="Johann Lehman", individual_id=None),),
        )
    )
    p_man = tmp_path / "man.json"
    man_coll.export_file(p_man)
    ImmigrationManifestCollection().import_file(p_man)

    # 2. NaturalizationCollection
    nat_coll = NaturalizationCollection.from_database(seeded_session)
    nat = NaturalizationRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000132"),
        source_urn=SourceURN("URN:SRC:1888:US_PA:NAT_132"),
        record_type=SourceRecordType.PETITION_FOR_NATURALIZATION,
        description="Naturalization",
        repository_id=RepositoryID("REP-000001"),
        audit=_audit(),
        court_name="Common Pleas",
        docket_locator="Docket B, p. 44",
        applicant_name_raw="John Lehman",
        event_date=EventDate.from_dict("1888-09-10"),
        applicant_id=IndividualID("IND-000001"),
        court_location_id=LocationID("LOC-000001"),
    )
    nat_coll.add(nat)
    assert len(nat_coll.find_by_applicant("IND-000001")) == 1
    assert len(nat_coll.find_by_court_location("LOC-000001")) == 1

    nat_coll.edit(nat.source_id, applicant_id=None, court_location_id=None)
    assert len(nat_coll.find_by_applicant("IND-000001")) == 0
    assert len(nat_coll.find_by_court_location("LOC-000001")) == 0
    nat_coll.edit(nat.source_id, description="Nat None Branch")
    nat_coll.add(
        dataclasses.replace(
            nat,
            source_id=SourceID("00000000-0000-4000-8000-000000000332"),
            source_urn=SourceURN("URN:SRC:1888:US_PA:NAT_332"),
            applicant_id=None,
            court_location_id=None,
        )
    )
    p_nat = tmp_path / "nat.json"
    nat_coll.export_file(p_nat)
    NaturalizationCollection().import_file(p_nat)
