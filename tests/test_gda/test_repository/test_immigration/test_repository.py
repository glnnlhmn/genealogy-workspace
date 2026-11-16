"""Path: tests/test_gda/test_repository/test_immigration/test_repository.py

Unit and integration tests for Immigration domain SQLite repositories
(src/gda/repository/immigration/repository.py).
"""

from __future__ import annotations

from gda.core.enums.core import Sex
from gda.core.enums.immigration import ArrivalPassageClass, NaturalizationStage
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
from gda.model.source.immigration.naturalization import (
    NaturalizationRecord,
    NaturalizationWitness,
)
from gda.repository.immigration.repository import (
    ImmigrationManifestRepository,
    NaturalizationRepository,
)


def _audit() -> AuditStamp:
    ts = IsoTimestamp("2026-01-01T00:00:00Z")
    return AuditStamp(created_at=ts, updated_at=ts)


def test_immigration_manifest_and_naturalization_repositories(
    seeded_session: DatabaseSessionManager,
) -> None:
    """Verify ImmigrationManifestRepository and NaturalizationRepository CRUD and queries."""
    man_repo = ImmigrationManifestRepository(session_manager=seeded_session)
    nat_repo = NaturalizationRepository(session_manager=seeded_session)

    manifest = ImmigrationManifestRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000031"),
        source_urn=SourceURN("URN:SRC:1882:US_PA:MAN_031"),
        record_type=SourceRecordType.PASSENGER_MANIFEST,
        description="Passenger Manifest of SS Vaderland",
        repository_id=RepositoryID("REP-000001"),
        audit=_audit(),
        port_of_arrival_raw="Philadelphia, PA",
        arrival_date=EventDate.from_dict("1882-05-14"),
        manifest_locator="NARA M425 Roll 102",
        port_of_arrival_id=LocationID("LOC-000001"),
        ship_name="SS Vaderland",
        passengers=(
            ManifestPassenger(
                full_name="Johann Lehman",
                line_number=4,
                individual_id=IndividualID("IND-000001"),
                sex=Sex.MALE,
                passage_class=ArrivalPassageClass.STEERAGE,
            ),
        ),
    )

    man_repo.upsert(manifest)
    assert man_repo.get_or_raise(manifest.source_id) == manifest
    assert len(man_repo.find_by_port_of_arrival("LOC-000001")) == 1
    assert len(man_repo.find_by_ship_name("SS Vaderland")) == 1
    assert len(man_repo.find_by_arrival_year_range(1880, 1885)) == 1
    assert len(man_repo.find_by_arrival_year_range(1890, 1895)) == 0

    nat = NaturalizationRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000032"),
        source_urn=SourceURN("URN:SRC:1888:US_PA:NAT_032"),
        record_type=SourceRecordType.PETITION_FOR_NATURALIZATION,
        description="Petition for Naturalization of John Lehman",
        repository_id=RepositoryID("REP-000001"),
        audit=_audit(),
        court_name="Court of Common Pleas of Cumberland County",
        docket_locator="Nat Docket B, p. 44",
        applicant_name_raw="John Lehman",
        event_date=EventDate.from_dict("1888-09-10"),
        court_location_id=LocationID("LOC-000001"),
        applicant_id=IndividualID("IND-000001"),
        stage=NaturalizationStage.PETITION,
        witnesses=(
            NaturalizationWitness(
                name="Mary Miller",
                individual_id=IndividualID("IND-000002"),
            ),
        ),
    )

    nat_repo.upsert(nat)
    assert nat_repo.get_or_raise(nat.source_id) == nat
    assert len(nat_repo.find_by_applicant("IND-000001")) == 1
    assert len(nat_repo.find_by_court_location("LOC-000001")) == 1
    assert len(nat_repo.find_by_event_year_range(1885, 1890)) == 1
