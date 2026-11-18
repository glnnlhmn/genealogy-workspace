"""Path: src/gda/repository/enumerated/collection.py

In-memory collections for Enumerated archival source records.
"""

from __future__ import annotations

import json
from collections import defaultdict
from typing import Any

from gda.db.mapper.enumerated_publications import (
    _POPULATION_SCHEDULE_REGISTRY,
    _SUPPLEMENTAL_SCHEDULE_REGISTRY,
)
from gda.db.session import DatabaseSessionManager
from gda.model.atom.id import IndividualID, LocationID, SourceID
from gda.model.source.enumerated import (
    CensusScheduleRecord,
    DirectoryRollRecord,
    PopulationScheduleRecord,
    SeptennialCensusRecord,
    TaxAssessmentRecord,
)
from gda.repository.collection import BaseSourceCollection
from gda.repository.enumerated.repository import (
    DirectoryRollRepository,
    PopulationScheduleRepository,
    SupplementalScheduleRepository,
    TaxAssessmentRepository,
)
from gda.util.ids import normalize_id

__version__ = "1.0.0+build.5"

__all__ = [
    "DirectoryRollCollection",
    "PopulationScheduleCollection",
    "SupplementalScheduleCollection",
    "TaxAssessmentCollection",
]


class PopulationScheduleCollection(
    BaseSourceCollection[PopulationScheduleRecord[Any], PopulationScheduleRepository]
):
    """In-memory collection for decennial US population census schedules."""

    def __init__(
        self,
        repository: PopulationScheduleRepository | None = None,
    ) -> None:
        """Initialize PopulationScheduleCollection with year and jurisdiction buckets."""
        self._by_year: dict[int, set[SourceID]] = defaultdict(set)
        self._by_jurisdiction: dict[str, set[SourceID]] = defaultdict(set)
        super().__init__(repository=repository)

    def _create_default_repository(
        self,
        session_manager: DatabaseSessionManager | None = None,
    ) -> PopulationScheduleRepository:
        return PopulationScheduleRepository(session_manager=session_manager)

    def _deserialize_record(
        self,
        data: dict[str, Any],
    ) -> PopulationScheduleRecord[Any]:
        year = int(data.get("enumeration_year", 0))
        if 1790 <= year <= 1840:
            cls = _POPULATION_SCHEDULE_REGISTRY["PopulationSchedule1790_1840"]
            normalized_entries = [
                {
                    **entry,
                    "age_bracket_tallies": (
                        json.loads(entry["age_bracket_tallies"])
                        if isinstance(entry.get("age_bracket_tallies"), str)
                        else entry.get("age_bracket_tallies", {})
                    ),
                }
                for entry in data.get("entries", [])
            ]
            data = {**data, "entries": normalized_entries}
        elif 1850 <= year <= 1870:
            cls = _POPULATION_SCHEDULE_REGISTRY["PopulationSchedule1850_1870"]
        elif year == 1880:
            cls = _POPULATION_SCHEDULE_REGISTRY["PopulationSchedule1880"]
        elif year in (1900, 1910):
            cls = _POPULATION_SCHEDULE_REGISTRY["PopulationSchedule1900_1910"]
        elif year in (1920, 1930, 1940, 1950):
            cls = _POPULATION_SCHEDULE_REGISTRY[f"PopulationSchedule{year}"]
        else:
            cls = PopulationScheduleRecord
        return cls.from_dict(data)

    def _index_domain_fields(self, record: PopulationScheduleRecord[Any]) -> None:
        self._by_year[int(record.enumeration_year.value)].add(record.source_id)
        if record.jurisdiction_id is not None:
            self._by_jurisdiction[record.jurisdiction_id.value].add(record.source_id)

    def _unindex_domain_fields(self, record: PopulationScheduleRecord[Any]) -> None:
        self._by_year[int(record.enumeration_year.value)].discard(record.source_id)
        if record.jurisdiction_id is not None:
            self._by_jurisdiction[record.jurisdiction_id.value].discard(record.source_id)

    def find_by_year(
        self,
        enumeration_year: int,
    ) -> list[PopulationScheduleRecord[Any]]:
        """Return active population schedules for a census year."""
        return self._records_for_ids(self._by_year.get(enumeration_year, set()))

    def find_by_jurisdiction(
        self,
        jurisdiction_id: LocationID | str,
    ) -> list[PopulationScheduleRecord[Any]]:
        """Return active population schedules for a jurisdiction LocationID."""
        return self._records_for_ids(
            self._by_jurisdiction.get(normalize_id(jurisdiction_id), set())
        )


class SupplementalScheduleCollection(
    BaseSourceCollection[CensusScheduleRecord[Any], SupplementalScheduleRepository]
):
    """In-memory collection for supplemental/non-population census schedules."""

    def __init__(
        self,
        repository: SupplementalScheduleRepository | None = None,
    ) -> None:
        """Initialize SupplementalScheduleCollection with year and jurisdiction buckets."""
        self._by_year: dict[int, set[SourceID]] = defaultdict(set)
        self._by_jurisdiction: dict[str, set[SourceID]] = defaultdict(set)
        super().__init__(repository=repository)

    def _create_default_repository(
        self,
        session_manager: DatabaseSessionManager | None = None,
    ) -> SupplementalScheduleRepository:
        return SupplementalScheduleRepository(session_manager=session_manager)

    def _deserialize_record(self, data: dict[str, Any]) -> CensusScheduleRecord[Any]:
        rec_type = str(data.get("record_type", ""))
        type_map = {
            "AGRICULTURAL_SCHEDULE": "AgriculturalScheduleRecord",
            "MANUFACTURING_SCHEDULE": "ManufacturingScheduleRecord",
            "MORTALITY_SCHEDULE": "MortalityScheduleRecord",
            "SLAVE_SCHEDULE": "SlaveScheduleRecord",
            "VETERANS_SCHEDULE": "Veterans1890ScheduleRecord",
        }
        cls_name = type_map.get(rec_type, "AgriculturalScheduleRecord")
        return _SUPPLEMENTAL_SCHEDULE_REGISTRY[cls_name].from_dict(data)

    def _index_domain_fields(self, record: CensusScheduleRecord[Any]) -> None:
        self._by_year[int(record.enumeration_year.value)].add(record.source_id)
        if record.jurisdiction_id is not None:
            self._by_jurisdiction[record.jurisdiction_id.value].add(record.source_id)

    def _unindex_domain_fields(self, record: CensusScheduleRecord[Any]) -> None:
        self._by_year[int(record.enumeration_year.value)].discard(record.source_id)
        if record.jurisdiction_id is not None:
            self._by_jurisdiction[record.jurisdiction_id.value].discard(record.source_id)

    def find_by_year(self, enumeration_year: int) -> list[CensusScheduleRecord[Any]]:
        """Return active supplemental schedules for a census year."""
        return self._records_for_ids(self._by_year.get(enumeration_year, set()))

    def find_by_jurisdiction(
        self,
        jurisdiction_id: LocationID | str,
    ) -> list[CensusScheduleRecord[Any]]:
        """Return active supplemental schedules for a jurisdiction LocationID."""
        return self._records_for_ids(
            self._by_jurisdiction.get(normalize_id(jurisdiction_id), set())
        )


class DirectoryRollCollection(BaseSourceCollection[DirectoryRollRecord, DirectoryRollRepository]):
    """In-memory collection for city, business, and civic directories."""

    def __init__(self, repository: DirectoryRollRepository | None = None) -> None:
        """Initialize DirectoryRollCollection with year and jurisdiction buckets."""
        self._by_year: dict[int, set[SourceID]] = defaultdict(set)
        self._by_jurisdiction: dict[str, set[SourceID]] = defaultdict(set)
        super().__init__(repository=repository)

    def _create_default_repository(
        self,
        session_manager: DatabaseSessionManager | None = None,
    ) -> DirectoryRollRepository:
        return DirectoryRollRepository(session_manager=session_manager)

    def _deserialize_record(self, data: dict[str, Any]) -> DirectoryRollRecord:
        return DirectoryRollRecord.from_dict(data)

    def _index_domain_fields(self, record: DirectoryRollRecord) -> None:
        self._by_year[int(record.enumeration_year.value)].add(record.source_id)
        if record.jurisdiction_id is not None:
            self._by_jurisdiction[record.jurisdiction_id.value].add(record.source_id)

    def _unindex_domain_fields(self, record: DirectoryRollRecord) -> None:
        self._by_year[int(record.enumeration_year.value)].discard(record.source_id)
        if record.jurisdiction_id is not None:
            self._by_jurisdiction[record.jurisdiction_id.value].discard(record.source_id)

    def find_by_year(self, enumeration_year: int) -> list[DirectoryRollRecord]:
        """Return active directory roll records for a publication year."""
        return self._records_for_ids(self._by_year.get(enumeration_year, set()))

    def find_by_jurisdiction(
        self,
        jurisdiction_id: LocationID | str,
    ) -> list[DirectoryRollRecord]:
        """Return active directory roll records for a jurisdiction LocationID."""
        return self._records_for_ids(
            self._by_jurisdiction.get(normalize_id(jurisdiction_id), set())
        )


class TaxAssessmentCollection(BaseSourceCollection[TaxAssessmentRecord, TaxAssessmentRepository]):
    """In-memory collection for tax assessments and PA Septennial census rolls."""

    def __init__(self, repository: TaxAssessmentRepository | None = None) -> None:
        """Initialize TaxAssessmentCollection with year and taxpayer buckets."""
        self._by_year: dict[int, set[SourceID]] = defaultdict(set)
        self._by_taxpayer: dict[str, set[SourceID]] = defaultdict(set)
        super().__init__(repository=repository)

    def _create_default_repository(
        self,
        session_manager: DatabaseSessionManager | None = None,
    ) -> TaxAssessmentRepository:
        return TaxAssessmentRepository(session_manager=session_manager)

    def _deserialize_record(self, data: dict[str, Any]) -> TaxAssessmentRecord:
        if "deaf_dumb_or_blind_note" in data or (data.get("record_category") == "CENSUS"):
            return SeptennialCensusRecord.from_dict(data)
        return TaxAssessmentRecord.from_dict(data)

    def _index_domain_fields(self, record: TaxAssessmentRecord) -> None:
        self._by_year[int(record.enumeration_year.value)].add(record.source_id)
        if record.taxpayer_id is not None:
            self._by_taxpayer[record.taxpayer_id.value].add(record.source_id)

    def _unindex_domain_fields(self, record: TaxAssessmentRecord) -> None:
        self._by_year[int(record.enumeration_year.value)].discard(record.source_id)
        if record.taxpayer_id is not None:
            self._by_taxpayer[record.taxpayer_id.value].discard(record.source_id)

    def find_by_year(self, enumeration_year: int) -> list[TaxAssessmentRecord]:
        """Return active tax assessment records for an assessment year."""
        return self._records_for_ids(self._by_year.get(enumeration_year, set()))

    def find_by_taxpayer(
        self,
        taxpayer_id: IndividualID | str,
    ) -> list[TaxAssessmentRecord]:
        """Return active tax assessment records for a taxpayer IndividualID."""
        return self._records_for_ids(self._by_taxpayer.get(normalize_id(taxpayer_id), set()))
