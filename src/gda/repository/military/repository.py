"""Path: src/gda/repository/military/repository.py

SQLite repositories for Military archival source records.

Operational Role:
    Provides concrete CRUD and domain-specialized analytical repositories for
    MilitaryDraftRecord, MilitaryServiceRecord, MilitaryPensionRecord,
    BountyLandWarrantRecord, MilitaryCasualtyRecord, and MilitaryAwardRecord.
"""

from __future__ import annotations

from gda.db.mapper.immigration_military import (
    BountyLandWarrantRecordMapper,
    MilitaryAwardRecordMapper,
    MilitaryCasualtyRecordMapper,
    MilitaryDraftRecordMapper,
    MilitaryPensionRecordMapper,
    MilitaryServiceRecordMapper,
)
from gda.db.session import DatabaseSessionManager
from gda.model.atom.id import IndividualID, LocationID, SourceID
from gda.model.source.military import (
    BountyLandWarrantRecord,
    MilitaryAwardRecord,
    MilitaryCasualtyRecord,
    MilitaryDraftRecord,
    MilitaryPensionRecord,
    MilitaryServiceRecord,
)
from gda.repository.base import BaseSQLiteRepository
from gda.util.ids import normalize_id

__version__ = "1.0.0+build.2"

__all__ = [
    "BountyLandWarrantRepository",
    "MilitaryAwardRepository",
    "MilitaryCasualtyRepository",
    "MilitaryDraftRepository",
    "MilitaryPensionRepository",
    "MilitaryServiceRepository",
]


class MilitaryDraftRepository(BaseSQLiteRepository[MilitaryDraftRecord, SourceID]):
    """SQLite repository for military draft and militia enrollment records."""

    def __init__(
        self,
        session_manager: DatabaseSessionManager | None = None,
        mapper: MilitaryDraftRecordMapper | None = None,
    ) -> None:
        """Initialize MilitaryDraftRepository."""
        super().__init__(
            mapper=mapper or MilitaryDraftRecordMapper(),
            session_manager=session_manager,
        )

    @property
    def table_name(self) -> str:
        """Return target SQLite table name."""
        return "military_draft_records"

    def find_by_registrant(
        self,
        registrant_id: IndividualID | str,
    ) -> list[MilitaryDraftRecord]:
        """Find draft records for a registrant IndividualID."""
        return self.find_by(registrant_id=normalize_id(registrant_id))

    def find_by_year(self, draft_year: int) -> list[MilitaryDraftRecord]:
        """Find draft records for a specific registration year."""
        return self.find_by(draft_year=draft_year)

    def find_by_board_location(
        self,
        board_location_id: LocationID | str,
    ) -> list[MilitaryDraftRecord]:
        """Find draft records linked to a local board LocationID."""
        return self.find_by(board_location_id=normalize_id(board_location_id))


class MilitaryServiceRepository(BaseSQLiteRepository[MilitaryServiceRecord, SourceID]):
    """SQLite repository for military enlistment, muster, and separation records."""

    def __init__(
        self,
        session_manager: DatabaseSessionManager | None = None,
        mapper: MilitaryServiceRecordMapper | None = None,
    ) -> None:
        """Initialize MilitaryServiceRepository."""
        super().__init__(
            mapper=mapper or MilitaryServiceRecordMapper(),
            session_manager=session_manager,
        )

    @property
    def table_name(self) -> str:
        """Return target SQLite table name."""
        return "military_service_records"

    def find_by_veteran(
        self,
        veteran_id: IndividualID | str,
    ) -> list[MilitaryServiceRecord]:
        """Find service records for a veteran IndividualID."""
        return self.find_by(veteran_id=normalize_id(veteran_id))

    def find_by_branch(self, branch: str) -> list[MilitaryServiceRecord]:
        """Find service records for an armed branch."""
        return self.find_by(branch=branch)

    def find_by_enlistment_location(
        self,
        location_id: LocationID | str,
    ) -> list[MilitaryServiceRecord]:
        """Find service records linked to an enlistment LocationID."""
        return self.find_by(enlistment_location_id=normalize_id(location_id))


class MilitaryPensionRepository(BaseSQLiteRepository[MilitaryPensionRecord, SourceID]):
    """SQLite repository for veteran and widow/dependent pension records."""

    def __init__(
        self,
        session_manager: DatabaseSessionManager | None = None,
        mapper: MilitaryPensionRecordMapper | None = None,
    ) -> None:
        """Initialize MilitaryPensionRepository."""
        super().__init__(
            mapper=mapper or MilitaryPensionRecordMapper(),
            session_manager=session_manager,
        )

    @property
    def table_name(self) -> str:
        """Return target SQLite table name."""
        return "military_pension_records"

    def find_by_veteran(
        self,
        veteran_id: IndividualID | str,
    ) -> list[MilitaryPensionRecord]:
        """Find pension records linked to a veteran IndividualID."""
        return self.find_by(veteran_id=normalize_id(veteran_id))

    def find_by_claimant(
        self,
        claimant_id: IndividualID | str,
    ) -> list[MilitaryPensionRecord]:
        """Find pension records linked to a claimant IndividualID."""
        return self.find_by(claimant_id=normalize_id(claimant_id))

    def find_by_application_year(
        self,
        application_year: int,
    ) -> list[MilitaryPensionRecord]:
        """Find pension records filed in a specific calendar year."""
        return self.find_by(application_year=application_year)


class BountyLandWarrantRepository(BaseSQLiteRepository[BountyLandWarrantRecord, SourceID]):
    """SQLite repository for military bounty land warrants."""

    def __init__(
        self,
        session_manager: DatabaseSessionManager | None = None,
        mapper: BountyLandWarrantRecordMapper | None = None,
    ) -> None:
        """Initialize BountyLandWarrantRepository."""
        super().__init__(
            mapper=mapper or BountyLandWarrantRecordMapper(),
            session_manager=session_manager,
        )

    @property
    def table_name(self) -> str:
        """Return target SQLite table name."""
        return "military_bounty_land_warrants"

    def find_by_veteran(
        self,
        veteran_id: IndividualID | str,
    ) -> list[BountyLandWarrantRecord]:
        """Find bounty land warrants linked to a veteran IndividualID."""
        return self.find_by(veteran_id=normalize_id(veteran_id))

    def find_by_warrantee(
        self,
        warrantee_id: IndividualID | str,
    ) -> list[BountyLandWarrantRecord]:
        """Find bounty land warrants linked to a warrantee IndividualID."""
        return self.find_by(warrantee_id=normalize_id(warrantee_id))

    def find_by_warrant_year(
        self,
        warrant_year: int,
    ) -> list[BountyLandWarrantRecord]:
        """Find bounty land warrants issued in a specific year."""
        return self.find_by(warrant_year=warrant_year)


class MilitaryCasualtyRepository(BaseSQLiteRepository[MilitaryCasualtyRecord, SourceID]):
    """SQLite repository for combat casualties, military burials, and POW records."""

    def __init__(
        self,
        session_manager: DatabaseSessionManager | None = None,
        mapper: MilitaryCasualtyRecordMapper | None = None,
    ) -> None:
        """Initialize MilitaryCasualtyRepository."""
        super().__init__(
            mapper=mapper or MilitaryCasualtyRecordMapper(),
            session_manager=session_manager,
        )

    @property
    def table_name(self) -> str:
        """Return target SQLite table name."""
        return "military_casualty_records"

    def find_by_servicemember(
        self,
        servicemember_id: IndividualID | str,
    ) -> list[MilitaryCasualtyRecord]:
        """Find casualty records for a servicemember IndividualID."""
        return self.find_by(servicemember_id=normalize_id(servicemember_id))

    def find_by_year(self, casualty_year: int) -> list[MilitaryCasualtyRecord]:
        """Find casualty records for a specific calendar year."""
        return self.find_by(casualty_year=casualty_year)

    def find_by_location(
        self,
        location_id: LocationID | str,
    ) -> list[MilitaryCasualtyRecord]:
        """Find casualty records linked to a casualty LocationID."""
        return self.find_by(casualty_location_id=normalize_id(location_id))


class MilitaryAwardRepository(BaseSQLiteRepository[MilitaryAwardRecord, SourceID]):
    """SQLite repository for military awards, medals, and decorations."""

    def __init__(
        self,
        session_manager: DatabaseSessionManager | None = None,
        mapper: MilitaryAwardRecordMapper | None = None,
    ) -> None:
        """Initialize MilitaryAwardRepository."""
        super().__init__(
            mapper=mapper or MilitaryAwardRecordMapper(),
            session_manager=session_manager,
        )

    @property
    def table_name(self) -> str:
        """Return target SQLite table name."""
        return "military_award_records"

    def find_by_recipient(
        self,
        recipient_id: IndividualID | str,
    ) -> list[MilitaryAwardRecord]:
        """Find military award records for a recipient IndividualID."""
        return self.find_by(recipient_id=normalize_id(recipient_id))

    def find_by_award_year(
        self,
        award_year: int,
    ) -> list[MilitaryAwardRecord]:
        """Find military awards conferred in a specific year."""
        return self.find_by(award_year=award_year)

    def find_by_award_tier(
        self,
        award_tier: str,
    ) -> list[MilitaryAwardRecord]:
        """Find military awards matching an AwardTier value."""
        return self.find_by(award_tier=award_tier)
