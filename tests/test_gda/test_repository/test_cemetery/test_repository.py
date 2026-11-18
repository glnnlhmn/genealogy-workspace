"""Path: tests/test_gda/test_repository/test_cemetery/test_repository.py

Unit and integration tests for Cemetery domain SQLite repositories
(src/gda/repository/cemetery/repository.py).
"""

from __future__ import annotations

from gda.core.enums.site import MarkerCondition, MarkerMaterial, MarkerType
from gda.core.enums.sources import SourceRecordType
from gda.db.session import DatabaseSessionManager
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import (
    IndividualID,
    LocationID,
    RepositoryID,
    SiteID,
    SourceID,
)
from gda.model.atom.urn import SourceURN
from gda.model.atom.year import HistoricalYear
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate
from gda.model.source.cemetery.marker import CemeteryMarkerRecord, MarkerInterment
from gda.model.source.cemetery.registry import (
    CemeteryPlotEntry,
    CemeteryRegistryRecord,
    RegistryInterment,
)
from gda.repository.cemetery.repository import (
    CemeteryMarkerRepository,
    CemeteryRegistryRepository,
)


def _audit() -> AuditStamp:
    ts = IsoTimestamp("2026-01-01T00:00:00Z")
    return AuditStamp(created_at=ts, updated_at=ts)


def test_cemetery_marker_and_registry_repositories(
    seeded_session: DatabaseSessionManager,
) -> None:
    """Verify CemeteryMarkerRepository and CemeteryRegistryRepository CRUD and queries."""
    marker_repo = CemeteryMarkerRepository(session_manager=seeded_session)
    reg_repo = CemeteryRegistryRepository(session_manager=seeded_session)

    marker = CemeteryMarkerRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000006"),
        source_urn=SourceURN("URN:SRC:2020:US_PA:MRK006"),
        record_type=SourceRecordType.CEMETERY_MARKER,
        description="Headstone of John Lehman",
        repository_id=RepositoryID("REP-000001"),
        audit=_audit(),
        cemetery_name_raw="Zion Lutheran Cemetery",
        cemetery_site_id=SiteID("SID-000001"),
        location_id=LocationID("LOC-000001"),
        plot_location="Sec A Lot 12",
        findagrave_id="FAG-123456",
        marker_type=MarkerType.UPRIGHT_HEADSTONE,
        material=MarkerMaterial.GRANITE,
        physical_condition=MarkerCondition.SOUND,
        survey_date=EventDate.from_dict("2020"),
        interments=(
            MarkerInterment(
                inscribed_name="John Lehman",
                individual_id=IndividualID("IND-000001"),
            ),
        ),
    )
    marker_repo.upsert(marker)
    assert marker_repo.get_or_raise(marker.source_id) == marker
    assert len(marker_repo.find_by_cemetery_site("SID-000001")) == 1
    assert len(marker_repo.find_by_location("LOC-000001")) == 1
    assert len(marker_repo.find_by_findagrave_id("FAG-123456")) == 1

    registry = CemeteryRegistryRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000007"),
        source_urn=SourceURN("URN:SRC:1930:US_PA:REG007"),
        record_type=SourceRecordType.REGISTER_ENTRY,
        description="Zion Lutheran Sexton Plot Ledger",
        repository_id=RepositoryID("REP-000001"),
        audit=_audit(),
        cemetery_site_id=SiteID("SID-000001"),
        cemetery_name_raw="Zion Lutheran Cemetery",
        location_id=LocationID("LOC-000001"),
        sexton_or_custodian="H. Schmidt",
        survey_date=EventDate.from_dict("1930-05"),
        plots=(
            CemeteryPlotEntry(
                plot_locator="Sec A Lot 12",
                marker_source_id=SourceID("00000000-0000-4000-8000-000000000006"),
                condition=MarkerCondition.SOUND,
                interments=(
                    RegistryInterment(
                        inscribed_name="John Lehman",
                        individual_id=IndividualID("IND-000001"),
                        birth_year=HistoricalYear(1852),
                        death_year=HistoricalYear(1922),
                    ),
                ),
            ),
        ),
    )
    reg_repo.upsert(registry)
    assert reg_repo.get_or_raise(registry.source_id) == registry
    assert len(reg_repo.find_by_cemetery_site("SID-000001")) == 1
    assert len(reg_repo.find_by_location("LOC-000001")) == 1
