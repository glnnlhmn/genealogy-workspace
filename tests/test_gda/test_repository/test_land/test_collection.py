"""Path: tests/test_gda/test_repository/test_land/test_collection.py

Unit and integration tests for Land domain collections
(src/gda/repository/land/collection.py).
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

from gda.core.enums.land import DeedPartyRole
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
from gda.model.source.land.deed import DeedParty, LandDeedRecord, LandParcel
from gda.model.source.land.grant import LandGrantRecord
from gda.repository.land.collection import (
    LandDeedCollection,
    LandGrantCollection,
)


def _audit() -> AuditStamp:
    ts = IsoTimestamp("2026-01-01T00:00:00Z")
    return AuditStamp(created_at=ts, updated_at=ts)


def test_land_collections_indexing_and_roundtrip(
    seeded_session: DatabaseSessionManager,
    tmp_path: Path,
) -> None:
    """Verify secondary index buckets, editing, and JSON round-tripping for Land collections."""
    # 1. LandDeedCollection
    deed_coll = LandDeedCollection.from_database(seeded_session)
    deed = LandDeedRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000123"),
        source_urn=SourceURN("URN:SRC:1860:US_PA:DEED_123"),
        record_type=SourceRecordType.DEED_INDENTURE,
        description="Deed",
        repository_id=RepositoryID("REP-000001"),
        audit=_audit(),
        office_title="Recorder of Deeds",
        recording_locator="Book 2Z, p. 410",
        date_written=EventDate.from_dict("1860-04-01"),
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
            location_raw="South Middleton Township",
            location_id=LocationID("LOC-000001"),
        ),
    )
    deed_coll.add(deed)
    assert len(deed_coll.find_by_party("IND-000001")) == 1
    assert len(deed_coll.find_by_party("IND-000002")) == 1
    assert len(deed_coll.find_by_parcel_location("LOC-000001")) == 1

    # Edit deed to unlinked parties and unlinked parcel
    deed_coll.edit(
        deed.source_id,
        grantors=(DeedParty(full_name="John Lehman", party_role=DeedPartyRole.GRANTOR),),
        grantees=(DeedParty(full_name="Mary Miller", party_role=DeedPartyRole.GRANTEE),),
        parcel=LandParcel(location_raw="South Middleton Township", location_id=None),
    )
    assert len(deed_coll.find_by_party("IND-000001")) == 0
    assert len(deed_coll.find_by_parcel_location("LOC-000001")) == 0
    deed_coll.edit(deed.source_id, description="Deed None Branch")
    deed_coll.add(
        dataclasses.replace(
            deed,
            source_id=SourceID("00000000-0000-4000-8000-000000000323"),
            source_urn=SourceURN("URN:SRC:1860:US_PA:DEED_323"),
            grantors=(DeedParty(full_name="John Lehman", party_role=DeedPartyRole.GRANTOR),),
            grantees=(DeedParty(full_name="Mary Miller", party_role=DeedPartyRole.GRANTEE),),
            parcel=LandParcel(location_raw="South Middleton Township", location_id=None),
        )
    )
    p_deed = tmp_path / "deed.json"
    deed_coll.export_file(p_deed)
    LandDeedCollection().import_file(p_deed)

    # 2. LandGrantCollection
    grant_coll = LandGrantCollection.from_database(seeded_session)
    grant = LandGrantRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000124"),
        source_urn=SourceURN("URN:SRC:1795:US_PA:PAT_124"),
        record_type=SourceRecordType.PATENT,
        description="Patent",
        repository_id=RepositoryID("REP-000001"),
        audit=_audit(),
        issuing_authority="Commonwealth of Pennsylvania",
        instrument_locator="Patent Book P-26, p. 88",
        patentee_name_raw="John Lehman",
        patentee_id=IndividualID("IND-000001"),
        parcel=LandParcel(
            location_raw="Cumberland County",
            location_id=LocationID("LOC-000001"),
        ),
    )
    grant_coll.add(grant)
    assert len(grant_coll.find_by_patentee("IND-000001")) == 1
    assert len(grant_coll.find_by_parcel_location("LOC-000001")) == 1

    grant_coll.edit(
        grant.source_id,
        patentee_id=None,
        parcel=LandParcel(location_raw="Cumberland County", location_id=None),
    )
    assert len(grant_coll.find_by_patentee("IND-000001")) == 0
    assert len(grant_coll.find_by_parcel_location("LOC-000001")) == 0
    grant_coll.edit(grant.source_id, description="Grant None Branch")
    grant_coll.add(
        dataclasses.replace(
            grant,
            source_id=SourceID("00000000-0000-4000-8000-000000000324"),
            source_urn=SourceURN("URN:SRC:1795:US_PA:PAT_324"),
            patentee_id=None,
            parcel=LandParcel(location_raw="Cumberland County", location_id=None),
        )
    )
    p_grant = tmp_path / "grant.json"
    grant_coll.export_file(p_grant)
    LandGrantCollection().import_file(p_grant)
