"""Path: src/gda/db/mapper/vital_cemetery.py

Bidirectional SQLite row mappers for Vital and Cemetery archival source records.

Operational Role:
    Flattens analytical, foreign-key, and temporal columns for SQLite indexing
    while preserving lossless round-trip serialization via payload_json for
    BaptismRecord, BirthRecord, DeathRecord, DivorceRecord, MarriageRecord,
    CemeteryMarkerRecord, and CemeteryRegistryRecord.
"""

from __future__ import annotations

import sqlite3
from typing import Any

from gda.db.exceptions import EntityMappingError
from gda.db.mapper.base import (
    BaseRowMapper,
    _base_source_columns,
    _date_sort,
    _date_year,
    _hydrate_from_payload,
    _opt_val,
)
from gda.model.source.cemetery.marker import CemeteryMarkerRecord
from gda.model.source.cemetery.registry import CemeteryRegistryRecord
from gda.model.source.vital.baptism import BaptismRecord
from gda.model.source.vital.birth import BirthRecord
from gda.model.source.vital.death import DeathRecord
from gda.model.source.vital.divorce import DivorceRecord
from gda.model.source.vital.marriage import MarriageRecord

__version__ = "1.0.0+build.6"

__all__ = [
    "BaptismRecordMapper",
    "BirthRecordMapper",
    "CemeteryMarkerRecordMapper",
    "CemeteryRegistryRecordMapper",
    "DeathRecordMapper",
    "DivorceRecordMapper",
    "MarriageRecordMapper",
]


class BaptismRecordMapper(BaseRowMapper[BaptismRecord]):
    """Bidirectional SQLite row mapper for BaptismRecord."""

    def __init__(self) -> None:
        """Initialize BaptismRecordMapper."""
        super().__init__(BaptismRecord)

    def to_row(self, entity: BaptismRecord) -> dict[str, Any]:
        """Serialize BaptismRecord into vital_baptisms table columns."""
        try:
            row = _base_source_columns(entity)
            row.update(
                {
                    "church_name_raw": entity.church_name_raw,
                    "baptized_name_raw": entity.baptized_name_raw,
                    "baptism_year": _date_year(entity.date_of_baptism),
                    "baptism_date_sort": _date_sort(entity.date_of_baptism),
                    "birth_year": _date_year(entity.date_of_birth),
                    "individual_id": _opt_val(entity.individual_id),
                    "church_org_id": _opt_val(entity.church_org_id),
                    "church_site_id": _opt_val(entity.church_site_id),
                    "location_id": _opt_val(entity.location_id),
                    "sex": _opt_val(entity.sex),
                    "denomination": entity.denomination,
                    "father_name_raw": entity.father_name_raw,
                    "mother_name_raw": entity.mother_name_raw,
                }
            )
            return row
        except Exception as err:
            raise EntityMappingError(f"Failed to map BaptismRecord to row: {err}") from err

    def from_row(self, row: sqlite3.Row | dict[str, Any]) -> BaptismRecord:
        """Hydrate BaptismRecord from SQLite row."""
        return _hydrate_from_payload(row, BaptismRecord)


class BirthRecordMapper(BaseRowMapper[BirthRecord]):
    """Bidirectional SQLite row mapper for BirthRecord."""

    def __init__(self) -> None:
        """Initialize BirthRecordMapper."""
        super().__init__(BirthRecord)

    def to_row(self, entity: BirthRecord) -> dict[str, Any]:
        """Serialize BirthRecord into vital_births table columns."""
        try:
            row = _base_source_columns(entity)
            row.update(
                {
                    "child_name_raw": entity.child_name_raw,
                    "birth_year": _date_year(entity.date_of_birth),
                    "birth_date_sort": _date_sort(entity.date_of_birth),
                    "place_of_birth_raw": entity.place_of_birth_raw,
                    "child_id": _opt_val(entity.child_id),
                    "place_of_birth_id": _opt_val(entity.place_of_birth_id),
                    "sex": _opt_val(entity.sex),
                    "plurality": _opt_val(entity.plurality),
                    "is_stillborn": 1 if entity.is_stillborn else 0,
                    "certificate_number": entity.certificate_number,
                    "registration_district": entity.registration_district,
                    "father_name_raw": entity.father_name_raw,
                    "mother_maiden_name_raw": entity.mother_maiden_name_raw,
                }
            )
            return row
        except Exception as err:
            raise EntityMappingError(f"Failed to map BirthRecord to row: {err}") from err

    def from_row(self, row: sqlite3.Row | dict[str, Any]) -> BirthRecord:
        """Hydrate BirthRecord from SQLite row."""
        return _hydrate_from_payload(row, BirthRecord)


class DeathRecordMapper(BaseRowMapper[DeathRecord]):
    """Bidirectional SQLite row mapper for DeathRecord."""

    def __init__(self) -> None:
        """Initialize DeathRecordMapper."""
        super().__init__(DeathRecord)

    def to_row(self, entity: DeathRecord) -> dict[str, Any]:
        """Serialize DeathRecord into vital_deaths table columns."""
        try:
            row = _base_source_columns(entity)
            row.update(
                {
                    "decedent_name_raw": entity.decedent_name_raw,
                    "death_year": _date_year(entity.date_of_death),
                    "death_date_sort": _date_sort(entity.date_of_death),
                    "birth_year": _date_year(entity.date_of_birth),
                    "place_of_death_raw": entity.place_of_death_raw,
                    "decedent_id": _opt_val(entity.decedent_id),
                    "place_of_death_id": _opt_val(entity.place_of_death_id),
                    "disposition_site_id": _opt_val(entity.disposition_site_id),
                    "sex": _opt_val(entity.sex),
                    "is_stillborn": 1 if entity.is_stillborn else 0,
                    "marital_status": _opt_val(entity.marital_status),
                    "manner_of_death": _opt_val(entity.manner_of_death),
                    "cause_of_death_raw": entity.cause_of_death_raw,
                    "certificate_number": entity.certificate_number,
                    "father_name_raw": entity.father_name_raw,
                    "mother_maiden_name_raw": entity.mother_maiden_name_raw,
                }
            )
            return row
        except Exception as err:
            raise EntityMappingError(f"Failed to map DeathRecord to row: {err}") from err

    def from_row(self, row: sqlite3.Row | dict[str, Any]) -> DeathRecord:
        """Hydrate DeathRecord from SQLite row."""
        return _hydrate_from_payload(row, DeathRecord)


class DivorceRecordMapper(BaseRowMapper[DivorceRecord]):
    """Bidirectional SQLite row mapper for DivorceRecord."""

    def __init__(self) -> None:
        """Initialize DivorceRecordMapper."""
        super().__init__(DivorceRecord)

    def to_row(self, entity: DivorceRecord) -> dict[str, Any]:
        """Serialize DivorceRecord into vital_divorces table columns."""
        try:
            row = _base_source_columns(entity)
            row.update(
                {
                    "court_name": entity.court_name,
                    "husband_name_raw": entity.husband_name_raw,
                    "wife_name_raw": entity.wife_name_raw,
                    "decree_year": _date_year(entity.date_decree_granted),
                    "decree_date_sort": _date_sort(entity.date_decree_granted),
                    "marriage_year": _date_year(entity.date_of_marriage),
                    "husband_id": _opt_val(entity.husband_id),
                    "wife_id": _opt_val(entity.wife_id),
                    "jurisdiction_id": _opt_val(entity.jurisdiction_id),
                    "docket_number": entity.docket_number,
                    "state_file_number": entity.state_file_number,
                    "decree_type": _opt_val(entity.decree_type),
                }
            )
            return row
        except Exception as err:
            raise EntityMappingError(f"Failed to map DivorceRecord to row: {err}") from err

    def from_row(self, row: sqlite3.Row | dict[str, Any]) -> DivorceRecord:
        """Hydrate DivorceRecord from SQLite row."""
        return _hydrate_from_payload(row, DivorceRecord)


class MarriageRecordMapper(BaseRowMapper[MarriageRecord]):
    """Bidirectional SQLite row mapper for MarriageRecord."""

    def __init__(self) -> None:
        """Initialize MarriageRecordMapper."""
        super().__init__(MarriageRecord)

    def to_row(self, entity: MarriageRecord) -> dict[str, Any]:
        """Serialize MarriageRecord into vital_marriages table columns."""
        try:
            row = _base_source_columns(entity)
            row.update(
                {
                    "groom_name_raw": entity.groom_name_raw,
                    "bride_name_raw": entity.bride_name_raw,
                    "union_type": _opt_val(entity.union_type),
                    "groom_id": _opt_val(entity.groom_id),
                    "bride_id": _opt_val(entity.bride_id),
                    "marriage_year": _date_year(entity.date_of_marriage),
                    "marriage_date_sort": _date_sort(entity.date_of_marriage),
                    "place_of_marriage_raw": entity.place_of_marriage_raw,
                    "place_of_marriage_id": _opt_val(entity.place_of_marriage_id),
                    "license_number": entity.license_number,
                    "religious_denomination": entity.religious_denomination,
                }
            )
            return row
        except Exception as err:
            raise EntityMappingError(f"Failed to map MarriageRecord to row: {err}") from err

    def from_row(self, row: sqlite3.Row | dict[str, Any]) -> MarriageRecord:
        """Hydrate MarriageRecord from SQLite row."""
        return _hydrate_from_payload(row, MarriageRecord)


class CemeteryMarkerRecordMapper(BaseRowMapper[CemeteryMarkerRecord]):
    """Bidirectional SQLite row mapper for CemeteryMarkerRecord."""

    def __init__(self) -> None:
        """Initialize CemeteryMarkerRecordMapper."""
        super().__init__(CemeteryMarkerRecord)

    def to_row(self, entity: CemeteryMarkerRecord) -> dict[str, Any]:
        """Serialize CemeteryMarkerRecord into cemetery_markers table columns."""
        try:
            row = _base_source_columns(entity)
            row.update(
                {
                    "cemetery_name_raw": entity.cemetery_name_raw,
                    "cemetery_site_id": _opt_val(entity.cemetery_site_id),
                    "location_id": _opt_val(entity.location_id),
                    "plot_location": entity.plot_location,
                    "findagrave_id": entity.findagrave_id,
                    "billiongraves_id": entity.billiongraves_id,
                    "cemetery_grave_id": entity.cemetery_grave_id,
                    "marker_type": _opt_val(entity.marker_type),
                    "material": _opt_val(entity.material),
                    "physical_condition": _opt_val(entity.physical_condition),
                    "survey_year": _date_year(entity.survey_date),
                    "interment_count": len(entity.interments),
                }
            )
            return row
        except Exception as err:
            raise EntityMappingError(f"Failed to map CemeteryMarkerRecord to row: {err}") from err

    def from_row(self, row: sqlite3.Row | dict[str, Any]) -> CemeteryMarkerRecord:
        """Hydrate CemeteryMarkerRecord from SQLite row."""
        return _hydrate_from_payload(row, CemeteryMarkerRecord)


class CemeteryRegistryRecordMapper(BaseRowMapper[CemeteryRegistryRecord]):
    """Bidirectional SQLite row mapper for CemeteryRegistryRecord."""

    def __init__(self) -> None:
        """Initialize CemeteryRegistryRecordMapper."""
        super().__init__(CemeteryRegistryRecord)

    def to_row(self, entity: CemeteryRegistryRecord) -> dict[str, Any]:
        """Serialize CemeteryRegistryRecord into cemetery_registries table columns."""
        try:
            row = _base_source_columns(entity)
            row.update(
                {
                    "cemetery_site_id": _opt_val(entity.cemetery_site_id),
                    "cemetery_name_raw": entity.cemetery_name_raw,
                    "location_id": _opt_val(entity.location_id),
                    "sexton_or_custodian": entity.sexton_or_custodian,
                    "survey_year": _date_year(entity.survey_date),
                    "plot_count": len(entity.plots),
                }
            )
            return row
        except Exception as err:
            raise EntityMappingError(f"Failed to map CemeteryRegistryRecord to row: {err}") from err

    def from_row(self, row: sqlite3.Row | dict[str, Any]) -> CemeteryRegistryRecord:
        """Hydrate CemeteryRegistryRecord from SQLite row."""
        return _hydrate_from_payload(row, CemeteryRegistryRecord)
