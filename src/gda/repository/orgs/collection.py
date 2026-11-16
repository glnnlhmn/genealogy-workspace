"""Path: src/gda/repository/orgs/collection.py

In-memory collections for Organization archival source records.

Operational Role:
    Provides indexed in-memory collection managers for
    OrganizationMembershipRecord and OrganizationRosterRecord with editing,
    graveyard lifecycle, and SQLite/JSON synchronization.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from gda.db.session import DatabaseSessionManager
from gda.model.atom.id import IndividualID, LocationID, OrganizationID, SourceID
from gda.model.source.orgs.membership import OrganizationMembershipRecord
from gda.model.source.orgs.roster import OrganizationRosterRecord
from gda.repository.base import _normalize_id
from gda.repository.collection import BaseSourceCollection
from gda.repository.orgs.repository import (
    OrganizationMembershipRepository,
    OrganizationRosterRepository,
)

__version__ = "1.0.0+build.1"

__all__ = [
    "OrganizationMembershipCollection",
    "OrganizationRosterCollection",
]


def _sorted_records[T](registry: dict[SourceID, T], sids: set[SourceID]) -> list[T]:
    return [registry[sid] for sid in sorted(sids, key=lambda s: s.value)]


class OrganizationMembershipCollection(
    BaseSourceCollection[
        OrganizationMembershipRecord,
        OrganizationMembershipRepository,
    ]
):
    """In-memory collection for OrganizationMembershipRecord sources."""

    def __init__(
        self,
        repository: OrganizationMembershipRepository | None = None,
    ) -> None:
        """Initialize OrganizationMembershipCollection with individual and org buckets."""
        self._by_individual: dict[str, set[SourceID]] = defaultdict(set)
        self._by_org: dict[str, set[SourceID]] = defaultdict(set)
        super().__init__(repository=repository)

    def _create_default_repository(
        self,
        session_manager: DatabaseSessionManager | None = None,
    ) -> OrganizationMembershipRepository:
        return OrganizationMembershipRepository(session_manager=session_manager)

    def _deserialize_record(
        self,
        data: dict[str, Any],
    ) -> OrganizationMembershipRecord:
        return OrganizationMembershipRecord.from_dict(data)

    def _index_domain_fields(
        self,
        record: OrganizationMembershipRecord,
    ) -> None:
        self._by_individual[record.individual_id.value].add(record.source_id)
        if record.org_id is not None:
            self._by_org[record.org_id.value].add(record.source_id)

    def _unindex_domain_fields(
        self,
        record: OrganizationMembershipRecord,
    ) -> None:
        self._by_individual[record.individual_id.value].discard(record.source_id)
        if record.org_id is not None:
            self._by_org[record.org_id.value].discard(record.source_id)

    def find_by_individual(
        self,
        individual_id: IndividualID | str,
    ) -> list[OrganizationMembershipRecord]:
        """Return active membership records for an IndividualID."""
        return _sorted_records(
            self._registry,
            self._by_individual.get(_normalize_id(individual_id), set()),
        )

    def find_by_organization(
        self,
        org_id: OrganizationID | str,
    ) -> list[OrganizationMembershipRecord]:
        """Return active membership records for an OrganizationID."""
        return _sorted_records(
            self._registry,
            self._by_org.get(_normalize_id(org_id), set()),
        )


class OrganizationRosterCollection(
    BaseSourceCollection[OrganizationRosterRecord, OrganizationRosterRepository]
):
    """In-memory collection for OrganizationRosterRecord sources."""

    def __init__(
        self,
        repository: OrganizationRosterRepository | None = None,
    ) -> None:
        """Initialize OrganizationRosterCollection with org and jurisdiction buckets."""
        self._by_org: dict[str, set[SourceID]] = defaultdict(set)
        self._by_jurisdiction: dict[str, set[SourceID]] = defaultdict(set)
        super().__init__(repository=repository)

    def _create_default_repository(
        self,
        session_manager: DatabaseSessionManager | None = None,
    ) -> OrganizationRosterRepository:
        return OrganizationRosterRepository(session_manager=session_manager)

    def _deserialize_record(
        self,
        data: dict[str, Any],
    ) -> OrganizationRosterRecord:
        return OrganizationRosterRecord.from_dict(data)

    def _index_domain_fields(self, record: OrganizationRosterRecord) -> None:
        if record.org_id is not None:
            self._by_org[record.org_id.value].add(record.source_id)
        if record.jurisdiction_id is not None:
            self._by_jurisdiction[record.jurisdiction_id.value].add(record.source_id)

    def _unindex_domain_fields(self, record: OrganizationRosterRecord) -> None:
        if record.org_id is not None:
            self._by_org[record.org_id.value].discard(record.source_id)
        if record.jurisdiction_id is not None:
            self._by_jurisdiction[record.jurisdiction_id.value].discard(record.source_id)

    def find_by_organization(
        self,
        org_id: OrganizationID | str,
    ) -> list[OrganizationRosterRecord]:
        """Return active roster records for an OrganizationID."""
        return _sorted_records(
            self._registry,
            self._by_org.get(_normalize_id(org_id), set()),
        )

    def find_by_jurisdiction(
        self,
        jurisdiction_id: LocationID | str,
    ) -> list[OrganizationRosterRecord]:
        """Return active roster records for a jurisdiction LocationID."""
        return _sorted_records(
            self._registry,
            self._by_jurisdiction.get(_normalize_id(jurisdiction_id), set()),
        )
