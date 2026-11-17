"""Path: src/gda/repository/military/collection.py

In-memory collections for Military archival source records.

Operational Role:
    Provides indexed in-memory collection managers for MilitaryDraftRecord,
    MilitaryServiceRecord, MilitaryPensionRecord, BountyLandWarrantRecord,
    MilitaryCasualtyRecord, and MilitaryAwardRecord with polymorphic JSON
    deserialization, editing, graveyard lifecycle, and SQLite persistence.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from gda.db.session import DatabaseSessionManager
from gda.model.atom.id import IndividualID, LocationID, SourceID
from gda.model.source.military import (
    BountyLandWarrantRecord,
    CivilWarDraftRecord,
    ColonialMilitiaRecord,
    CombatCasualtyRecord,
    EnlistmentMusterRecord,
    MilitaryAwardRecord,
    MilitaryBurialRecord,
    MilitaryCasualtyRecord,
    MilitaryDraftRecord,
    MilitaryPensionRecord,
    MilitaryServiceRecord,
    ModernSelectiveServiceRecord,
    PensionVeteranClaimRecord,
    PensionWidowDependentRecord,
    PrisonerOfWarRecord,
    SeparationDischargeRecord,
    WwiDraftCardRecord,
    WwiiDraftCardRecord,
)
from gda.repository.base import _normalize_id
from gda.repository.collection import BaseSourceCollection
from gda.repository.military.repository import (
    BountyLandWarrantRepository,
    MilitaryAwardRepository,
    MilitaryCasualtyRepository,
    MilitaryDraftRepository,
    MilitaryPensionRepository,
    MilitaryServiceRepository,
)

__version__ = "1.0.0+build.4"

__all__ = [
    "BountyLandWarrantCollection",
    "MilitaryAwardCollection",
    "MilitaryCasualtyCollection",
    "MilitaryDraftCollection",
    "MilitaryPensionCollection",
    "MilitaryServiceCollection",
]


class MilitaryDraftCollection(BaseSourceCollection[MilitaryDraftRecord, MilitaryDraftRepository]):
    """In-memory collection for MilitaryDraftRecord and era-specific subclasses."""

    def __init__(
        self,
        repository: MilitaryDraftRepository | None = None,
    ) -> None:
        """Initialize MilitaryDraftCollection with registrant and board_location buckets."""
        self._by_registrant: dict[str, set[SourceID]] = defaultdict(set)
        self._by_board_location: dict[str, set[SourceID]] = defaultdict(set)
        super().__init__(repository=repository)

    def _create_default_repository(
        self,
        session_manager: DatabaseSessionManager | None = None,
    ) -> MilitaryDraftRepository:
        return MilitaryDraftRepository(session_manager=session_manager)

    def _deserialize_record(self, data: dict[str, Any]) -> MilitaryDraftRecord:
        if "colony_or_state_raw" in data:
            return ColonialMilitiaRecord.from_dict(data)
        if "enrollment_class" in data:
            return CivilWarDraftRecord.from_dict(data)
        if "citizenship" in data:
            return WwiDraftCardRecord.from_dict(data)
        if "draft_wave" in data:
            return WwiiDraftCardRecord.from_dict(data)
        if "draft_era" in data:
            return ModernSelectiveServiceRecord.from_dict(data)
        return MilitaryDraftRecord.from_dict(data)

    def _index_domain_fields(self, record: MilitaryDraftRecord) -> None:
        self._by_registrant[record.registrant_id.value].add(record.source_id)
        if record.board_location_id is not None:
            self._by_board_location[record.board_location_id.value].add(record.source_id)

    def _unindex_domain_fields(self, record: MilitaryDraftRecord) -> None:
        self._by_registrant[record.registrant_id.value].discard(record.source_id)
        if record.board_location_id is not None:
            self._by_board_location[record.board_location_id.value].discard(record.source_id)

    def find_by_registrant(
        self,
        registrant_id: IndividualID | str,
    ) -> list[MilitaryDraftRecord]:
        """Return active draft records for a registrant IndividualID."""
        return self._records_for_ids(self._by_registrant.get(_normalize_id(registrant_id), set()))

    def find_by_board_location(
        self,
        board_location_id: LocationID | str,
    ) -> list[MilitaryDraftRecord]:
        """Return active draft records for a local board LocationID."""
        return self._records_for_ids(
            self._by_board_location.get(_normalize_id(board_location_id), set())
        )


class MilitaryServiceCollection(
    BaseSourceCollection[MilitaryServiceRecord, MilitaryServiceRepository]
):
    """In-memory collection for MilitaryServiceRecord and subclasses."""

    def __init__(
        self,
        repository: MilitaryServiceRepository | None = None,
    ) -> None:
        """Initialize MilitaryServiceCollection with veteran and location buckets."""
        self._by_veteran: dict[str, set[SourceID]] = defaultdict(set)
        self._by_location: dict[str, set[SourceID]] = defaultdict(set)
        super().__init__(repository=repository)

    def _create_default_repository(
        self,
        session_manager: DatabaseSessionManager | None = None,
    ) -> MilitaryServiceRepository:
        return MilitaryServiceRepository(session_manager=session_manager)

    def _deserialize_record(self, data: dict[str, Any]) -> MilitaryServiceRecord:
        if "roll_type" in data:
            return EnlistmentMusterRecord.from_dict(data)
        if "form_type" in data:
            return SeparationDischargeRecord.from_dict(data)
        return MilitaryServiceRecord.from_dict(data)

    def _index_domain_fields(self, record: MilitaryServiceRecord) -> None:
        self._by_veteran[record.veteran_id.value].add(record.source_id)
        if record.enlistment_location_id is not None:
            self._by_location[record.enlistment_location_id.value].add(record.source_id)

    def _unindex_domain_fields(self, record: MilitaryServiceRecord) -> None:
        self._by_veteran[record.veteran_id.value].discard(record.source_id)
        if record.enlistment_location_id is not None:
            self._by_location[record.enlistment_location_id.value].discard(record.source_id)

    def find_by_veteran(
        self,
        veteran_id: IndividualID | str,
    ) -> list[MilitaryServiceRecord]:
        """Return active service records for a veteran IndividualID."""
        return self._records_for_ids(self._by_veteran.get(_normalize_id(veteran_id), set()))

    def find_by_enlistment_location(
        self,
        location_id: LocationID | str,
    ) -> list[MilitaryServiceRecord]:
        """Return active service records for an enlistment LocationID."""
        return self._records_for_ids(self._by_location.get(_normalize_id(location_id), set()))


class MilitaryPensionCollection(
    BaseSourceCollection[MilitaryPensionRecord, MilitaryPensionRepository]
):
    """In-memory collection for MilitaryPensionRecord and subclasses."""

    def __init__(
        self,
        repository: MilitaryPensionRepository | None = None,
    ) -> None:
        """Initialize MilitaryPensionCollection with veteran and location buckets."""
        self._by_veteran: dict[str, set[SourceID]] = defaultdict(set)
        self._by_location: dict[str, set[SourceID]] = defaultdict(set)
        super().__init__(repository=repository)

    def _create_default_repository(
        self,
        session_manager: DatabaseSessionManager | None = None,
    ) -> MilitaryPensionRepository:
        return MilitaryPensionRepository(session_manager=session_manager)

    def _deserialize_record(self, data: dict[str, Any]) -> MilitaryPensionRecord:
        if "disability_description_raw" in data or "examining_surgeon_raw" in data:
            return PensionVeteranClaimRecord.from_dict(data)
        if "veteran_death_year" in data or "minor_children_count" in data:
            return PensionWidowDependentRecord.from_dict(data)
        return MilitaryPensionRecord.from_dict(data)

    def _index_domain_fields(self, record: MilitaryPensionRecord) -> None:
        self._by_veteran[record.veteran_id.value].add(record.source_id)
        if record.application_location_id is not None:
            self._by_location[record.application_location_id.value].add(record.source_id)

    def _unindex_domain_fields(self, record: MilitaryPensionRecord) -> None:
        self._by_veteran[record.veteran_id.value].discard(record.source_id)
        if record.application_location_id is not None:
            self._by_location[record.application_location_id.value].discard(record.source_id)

    def find_by_veteran(
        self,
        veteran_id: IndividualID | str,
    ) -> list[MilitaryPensionRecord]:
        """Return active pension records for a veteran IndividualID."""
        return self._records_for_ids(self._by_veteran.get(_normalize_id(veteran_id), set()))

    def find_by_application_location(
        self,
        location_id: LocationID | str,
    ) -> list[MilitaryPensionRecord]:
        """Return active pension records for an application LocationID."""
        return self._records_for_ids(self._by_location.get(_normalize_id(location_id), set()))


class BountyLandWarrantCollection(
    BaseSourceCollection[BountyLandWarrantRecord, BountyLandWarrantRepository]
):
    """In-memory collection for BountyLandWarrantRecord sources."""

    def __init__(
        self,
        repository: BountyLandWarrantRepository | None = None,
    ) -> None:
        """Initialize BountyLandWarrantCollection with veteran and location buckets."""
        self._by_veteran: dict[str, set[SourceID]] = defaultdict(set)
        self._by_patent_location: dict[str, set[SourceID]] = defaultdict(set)
        super().__init__(repository=repository)

    def _create_default_repository(
        self,
        session_manager: DatabaseSessionManager | None = None,
    ) -> BountyLandWarrantRepository:
        return BountyLandWarrantRepository(session_manager=session_manager)

    def _deserialize_record(
        self,
        data: dict[str, Any],
    ) -> BountyLandWarrantRecord:
        return BountyLandWarrantRecord.from_dict(data)

    def _index_domain_fields(self, record: BountyLandWarrantRecord) -> None:
        self._by_veteran[record.veteran_id.value].add(record.source_id)
        if record.patent_location_id is not None:
            self._by_patent_location[record.patent_location_id.value].add(record.source_id)

    def _unindex_domain_fields(self, record: BountyLandWarrantRecord) -> None:
        self._by_veteran[record.veteran_id.value].discard(record.source_id)
        if record.patent_location_id is not None:
            self._by_patent_location[record.patent_location_id.value].discard(record.source_id)

    def find_by_veteran(
        self,
        veteran_id: IndividualID | str,
    ) -> list[BountyLandWarrantRecord]:
        """Return active bounty land warrants for a veteran IndividualID."""
        return self._records_for_ids(self._by_veteran.get(_normalize_id(veteran_id), set()))

    def find_by_patent_location(
        self,
        location_id: LocationID | str,
    ) -> list[BountyLandWarrantRecord]:
        """Return active bounty land warrants for a patent LocationID."""
        return self._records_for_ids(
            self._by_patent_location.get(_normalize_id(location_id), set())
        )


class MilitaryCasualtyCollection(
    BaseSourceCollection[MilitaryCasualtyRecord, MilitaryCasualtyRepository]
):
    """In-memory collection for MilitaryCasualtyRecord and subclasses."""

    def __init__(
        self,
        repository: MilitaryCasualtyRepository | None = None,
    ) -> None:
        """Initialize MilitaryCasualtyCollection with servicemember and location buckets."""
        self._by_servicemember: dict[str, set[SourceID]] = defaultdict(set)
        self._by_location: dict[str, set[SourceID]] = defaultdict(set)
        super().__init__(repository=repository)

    def _create_default_repository(
        self,
        session_manager: DatabaseSessionManager | None = None,
    ) -> MilitaryCasualtyRepository:
        return MilitaryCasualtyRepository(session_manager=session_manager)

    def _deserialize_record(
        self,
        data: dict[str, Any],
    ) -> MilitaryCasualtyRecord:
        if "cemetery_type" in data:
            return MilitaryBurialRecord.from_dict(data)
        if "camp_type" in data:
            return PrisonerOfWarRecord.from_dict(data)
        if "engagement_name_raw" in data or "died_of_wounds_year" in data:
            return CombatCasualtyRecord.from_dict(data)
        return MilitaryCasualtyRecord.from_dict(data)

    def _index_domain_fields(self, record: MilitaryCasualtyRecord) -> None:
        self._by_servicemember[record.servicemember_id.value].add(record.source_id)
        if record.casualty_location_id is not None:
            self._by_location[record.casualty_location_id.value].add(record.source_id)

    def _unindex_domain_fields(self, record: MilitaryCasualtyRecord) -> None:
        self._by_servicemember[record.servicemember_id.value].discard(record.source_id)
        if record.casualty_location_id is not None:
            self._by_location[record.casualty_location_id.value].discard(record.source_id)

    def find_by_servicemember(
        self,
        servicemember_id: IndividualID | str,
    ) -> list[MilitaryCasualtyRecord]:
        """Return active casualty records for a servicemember IndividualID."""
        return self._records_for_ids(
            self._by_servicemember.get(_normalize_id(servicemember_id), set())
        )

    def find_by_location(
        self,
        location_id: LocationID | str,
    ) -> list[MilitaryCasualtyRecord]:
        """Return active casualty records for a casualty LocationID."""
        return self._records_for_ids(self._by_location.get(_normalize_id(location_id), set()))


class MilitaryAwardCollection(BaseSourceCollection[MilitaryAwardRecord, MilitaryAwardRepository]):
    """In-memory collection for MilitaryAwardRecord sources."""

    def __init__(
        self,
        repository: MilitaryAwardRepository | None = None,
    ) -> None:
        """Initialize MilitaryAwardCollection with recipient and location buckets."""
        self._by_recipient: dict[str, set[SourceID]] = defaultdict(set)
        self._by_location: dict[str, set[SourceID]] = defaultdict(set)
        super().__init__(repository=repository)

    def _create_default_repository(
        self,
        session_manager: DatabaseSessionManager | None = None,
    ) -> MilitaryAwardRepository:
        return MilitaryAwardRepository(session_manager=session_manager)

    def _deserialize_record(self, data: dict[str, Any]) -> MilitaryAwardRecord:
        return MilitaryAwardRecord.from_dict(data)

    def _index_domain_fields(self, record: MilitaryAwardRecord) -> None:
        self._by_recipient[record.recipient_id.value].add(record.source_id)
        if record.action_location_id is not None:
            self._by_location[record.action_location_id.value].add(record.source_id)

    def _unindex_domain_fields(self, record: MilitaryAwardRecord) -> None:
        self._by_recipient[record.recipient_id.value].discard(record.source_id)
        if record.action_location_id is not None:
            self._by_location[record.action_location_id.value].discard(record.source_id)

    def find_by_recipient(
        self,
        recipient_id: IndividualID | str,
    ) -> list[MilitaryAwardRecord]:
        """Return active military awards for a recipient IndividualID."""
        return self._records_for_ids(self._by_recipient.get(_normalize_id(recipient_id), set()))

    def find_by_action_location(
        self,
        location_id: LocationID | str,
    ) -> list[MilitaryAwardRecord]:
        """Return active military awards for an action LocationID."""
        return self._records_for_ids(self._by_location.get(_normalize_id(location_id), set()))
