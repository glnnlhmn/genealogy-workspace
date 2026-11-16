"""Path: tests/test_gda/test_repository/test_cemetery/test_collection.py

Unit and integration tests for Cemetery domain collections
(src/gda/repository/cemetery/collection.py).
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

from gda.core.enums.site import MarkerCondition, MarkerMaterial, MarkerType
from gda.core.enums.sources import SourceRecordType
from gda.db.session import DatabaseSessionManager
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import LocationID, RepositoryID, SiteID, SourceID
from gda.model.atom.urn import SourceURN
from gda.model.base.audit import AuditStamp
from gda.model.source.cemetery.marker import CemeteryMarkerRecord, MarkerInterment
from gda.model.source.cemetery.registry import (
    CemeteryPlotEntry,
    CemeteryRegistryRecord,
    RegistryInterment,
)
from gda.repository.cemetery.collection import (
    CemeteryMarkerCollection,
    CemeteryRegistryCollection,
)


def _audit() -> AuditStamp:
    ts = IsoTimestamp("2026-01-01T00:00:00Z")
    return AuditStamp(created_at=ts, updated_at=ts)


def test_cemetery_collections_indexing_and_roundtrip(
    seeded_session: DatabaseSessionManager,
    tmp_path: Path,
) -> None:
    """Verify secondary index buckets, editing, and JSON round-tripping for Cemetery collections."""
    # 1. CemeteryMarkerCollection
    mrk_coll = CemeteryMarkerCollection.from_database(seeded_session)
    mrk = CemeteryMarkerRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000105"),
        source_urn=SourceURN("URN:SRC:2020:US_PA:MRK105"),
        record_type=SourceRecordType.CEMETERY_MARKER,
        description="Marker",
        repository_id=RepositoryID("REP-000001"),
        audit=_audit(),
        cemetery_name_raw="Zion",
        cemetery_site_id=SiteID("SID-000001"),
        location_id=LocationID("LOC-000001"),
        marker_type=MarkerType.UPRIGHT_HEADSTONE,
        material=MarkerMaterial.GRANITE,
        physical_condition=MarkerCondition.SOUND,
        interments=(MarkerInterment.create(inscribed_name="John Lehman"),),
    )
    mrk_coll.add(mrk)
    assert len(mrk_coll.find_by_cemetery_site("SID-000001")) == 1
    assert len(mrk_coll.find_by_location("LOC-000001")) == 1
    mrk_coll.edit(mrk.source_id, cemetery_site_id=None, location_id=None)
    assert len(mrk_coll.find_by_cemetery_site("SID-000001")) == 0
    mrk_coll.edit(mrk.source_id, description="Marker None Branch")
    mrk_coll.add(
        dataclasses.replace(
            mrk,
            source_id=SourceID("00000000-0000-4000-8000-000000000305"),
            source_urn=SourceURN("URN:SRC:2020:US_PA:MRK305"),
            cemetery_site_id=None,
            location_id=None,
        )
    )
    p_mrk = tmp_path / "mrk.json"
    mrk_coll.export_file(p_mrk)
    CemeteryMarkerCollection().import_file(p_mrk)

    # 2. CemeteryRegistryCollection
    reg_coll = CemeteryRegistryCollection.from_database(seeded_session)
    reg = CemeteryRegistryRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000106"),
        source_urn=SourceURN("URN:SRC:1930:US_PA:REG106"),
        record_type=SourceRecordType.REGISTER_ENTRY,
        description="Registry",
        repository_id=RepositoryID("REP-000001"),
        audit=_audit(),
        cemetery_site_id=SiteID("SID-000001"),
        cemetery_name_raw="Zion",
        location_id=LocationID("LOC-000001"),
        plots=(
            CemeteryPlotEntry(
                plot_locator="Lot 1",
                interments=(RegistryInterment(inscribed_name="John Lehman"),),
            ),
        ),
    )
    reg_coll.add(reg)
    assert len(reg_coll.find_by_cemetery_site("SID-000001")) == 1
    assert len(reg_coll.find_by_location("LOC-000001")) == 1
    reg_coll.edit(reg.source_id, location_id=None)
    assert len(reg_coll.find_by_location("LOC-000001")) == 0
    reg_coll.edit(reg.source_id, description="Registry None Branch")
    reg_coll.add(
        dataclasses.replace(
            reg,
            source_id=SourceID("00000000-0000-4000-8000-000000000306"),
            source_urn=SourceURN("URN:SRC:1930:US_PA:REG306"),
            location_id=None,
        )
    )
    p_reg = tmp_path / "reg.json"
    reg_coll.export_file(p_reg)
    CemeteryRegistryCollection().import_file(p_reg)
