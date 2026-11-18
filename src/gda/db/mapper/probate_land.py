"""Path: src/gda/db/mapper/probate_land.py

Bidirectional SQLite row mappers for Probate and Land archival source records.

Operational Role:
    Flattens analytical, foreign-key, and temporal columns for SQLite indexing
    while preserving lossless round-trip serialization via payload_json for
    ProbateRecord, EstateInventoryRecord, LandDeedRecord, and LandGrantRecord.
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
    _opt_bool_int,
    _opt_val,
)
from gda.model.source.land.deed import LandDeedRecord
from gda.model.source.land.grant import LandGrantRecord
from gda.model.source.probate.inventory import EstateInventoryRecord
from gda.model.source.probate.will import ProbateRecord

__version__ = "1.0.0+build.3"

__all__ = [
    "EstateInventoryRecordMapper",
    "LandDeedRecordMapper",
    "LandGrantRecordMapper",
    "ProbateRecordMapper",
    "_opt_bool_int",
]


class ProbateRecordMapper(BaseRowMapper[ProbateRecord]):
    """Bidirectional SQLite row mapper for ProbateRecord (wills & estates)."""

    def __init__(self) -> None:
        """Initialize ProbateRecordMapper."""
        super().__init__(ProbateRecord)

    def to_row(self, entity: ProbateRecord) -> dict[str, Any]:
        """Serialize ProbateRecord into probate_wills table columns."""
        try:
            row = _base_source_columns(entity)
            row.update(
                {
                    "court_name": entity.court_name,
                    "filing_locator": entity.filing_locator,
                    "decedent_name_raw": entity.decedent_name_raw,
                    "court_location_id": _opt_val(entity.court_location_id),
                    "estate_file_number": entity.estate_file_number,
                    "book_and_page": entity.book_and_page,
                    "decedent_id": _opt_val(entity.decedent_id),
                    "decedent_residence_id": _opt_val(entity.decedent_residence_id),
                    "written_year": _date_year(entity.date_written),
                    "written_date_sort": _date_sort(entity.date_written),
                    "probated_year": _date_year(entity.date_probated),
                    "probated_date_sort": _date_sort(entity.date_probated),
                    "letters_year": _date_year(entity.date_letters_granted),
                    "bequest_count": len(entity.bequests),
                }
            )
            return row
        except Exception as err:
            raise EntityMappingError(f"Failed to map ProbateRecord to row: {err}") from err

    def from_row(self, row: sqlite3.Row | dict[str, Any]) -> ProbateRecord:
        """Hydrate ProbateRecord from SQLite row."""
        return _hydrate_from_payload(row, ProbateRecord)


class EstateInventoryRecordMapper(BaseRowMapper[EstateInventoryRecord]):
    """Bidirectional SQLite row mapper for EstateInventoryRecord."""

    def __init__(self) -> None:
        """Initialize EstateInventoryRecordMapper."""
        super().__init__(EstateInventoryRecord)

    def to_row(self, entity: EstateInventoryRecord) -> dict[str, Any]:
        """Serialize EstateInventoryRecord into probate_inventories table columns."""
        try:
            row = _base_source_columns(entity)
            row.update(
                {
                    "court_name": entity.court_name,
                    "filing_locator": entity.filing_locator,
                    "decedent_name_raw": entity.decedent_name_raw,
                    "court_location_id": _opt_val(entity.court_location_id),
                    "estate_file_number": entity.estate_file_number,
                    "book_and_page": entity.book_and_page,
                    "decedent_id": _opt_val(entity.decedent_id),
                    "parent_probate_source_id": _opt_val(entity.parent_probate_source_id),
                    "appraised_year": _date_year(entity.date_appraised_or_accounted),
                    "appraised_date_sort": _date_sort(entity.date_appraised_or_accounted),
                    "total_appraised_value_numeric": (entity.total_appraised_value_numeric),
                    "currency_code": entity.currency_code,
                    "item_count": len(entity.items),
                    "ledger_entry_count": len(entity.ledger_entries),
                }
            )
            return row
        except Exception as err:
            raise EntityMappingError(f"Failed to map EstateInventoryRecord to row: {err}") from err

    def from_row(
        self,
        row: sqlite3.Row | dict[str, Any],
    ) -> EstateInventoryRecord:
        """Hydrate EstateInventoryRecord from SQLite row."""
        return _hydrate_from_payload(row, EstateInventoryRecord)


class LandDeedRecordMapper(BaseRowMapper[LandDeedRecord]):
    """Bidirectional SQLite row mapper for LandDeedRecord."""

    def __init__(self) -> None:
        """Initialize LandDeedRecordMapper."""
        super().__init__(LandDeedRecord)

    def to_row(self, entity: LandDeedRecord) -> dict[str, Any]:
        """Serialize LandDeedRecord into land_deeds table columns."""
        try:
            row = _base_source_columns(entity)
            primary_grantor = (
                _opt_val(entity.grantors[0].individual_id) if entity.grantors else None
            )
            primary_grantee = (
                _opt_val(entity.grantees[0].individual_id) if entity.grantees else None
            )
            row.update(
                {
                    "office_title": entity.office_title,
                    "recording_locator": entity.recording_locator,
                    "written_year": _date_year(entity.date_written),
                    "written_date_sort": _date_sort(entity.date_written),
                    "recorded_year": _date_year(entity.date_recorded),
                    "recorded_date_sort": _date_sort(entity.date_recorded),
                    "office_location_id": _opt_val(entity.office_location_id),
                    "parcel_location_id": _opt_val(entity.parcel.location_id),
                    "primary_grantor_id": primary_grantor,
                    "primary_grantee_id": primary_grantee,
                    "deed_book": entity.deed_book,
                    "page_number": entity.page_number,
                    "instrument_number": entity.instrument_number,
                    "acreage_numeric": entity.parcel.acreage_numeric,
                    "dower_relinquished": _opt_bool_int(entity.dower_relinquished),
                }
            )
            return row
        except Exception as err:
            raise EntityMappingError(f"Failed to map LandDeedRecord to row: {err}") from err

    def from_row(self, row: sqlite3.Row | dict[str, Any]) -> LandDeedRecord:
        """Hydrate LandDeedRecord from SQLite row."""
        return _hydrate_from_payload(row, LandDeedRecord)


class LandGrantRecordMapper(BaseRowMapper[LandGrantRecord]):
    """Bidirectional SQLite row mapper for LandGrantRecord."""

    def __init__(self) -> None:
        """Initialize LandGrantRecordMapper."""
        super().__init__(LandGrantRecord)

    def to_row(self, entity: LandGrantRecord) -> dict[str, Any]:
        """Serialize LandGrantRecord into land_grants table columns."""
        try:
            row = _base_source_columns(entity)
            row.update(
                {
                    "issuing_authority": entity.issuing_authority,
                    "instrument_locator": entity.instrument_locator,
                    "patentee_name_raw": entity.patentee_name_raw,
                    "office_location_id": _opt_val(entity.office_location_id),
                    "parcel_location_id": _opt_val(entity.parcel.location_id),
                    "patent_or_warrant_number": entity.patent_or_warrant_number,
                    "certificate_or_entry_number": (entity.certificate_or_entry_number),
                    "grant_basis": _opt_val(entity.grant_basis),
                    "patentee_id": _opt_val(entity.patentee_id),
                    "assignee_id": _opt_val(entity.assignee_id),
                    "warrant_year": _date_year(entity.date_warrant_or_entry),
                    "surveyed_year": _date_year(entity.date_surveyed),
                    "patented_year": _date_year(entity.date_patented),
                    "patented_date_sort": _date_sort(entity.date_patented),
                    "acreage_numeric": entity.parcel.acreage_numeric,
                }
            )
            return row
        except Exception as err:
            raise EntityMappingError(f"Failed to map LandGrantRecord to row: {err}") from err

    def from_row(self, row: sqlite3.Row | dict[str, Any]) -> LandGrantRecord:
        """Hydrate LandGrantRecord from SQLite row."""
        return _hydrate_from_payload(row, LandGrantRecord)
