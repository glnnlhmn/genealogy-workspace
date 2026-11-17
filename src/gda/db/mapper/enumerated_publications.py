"""Path: src/gda/db/mapper/enumerated_publications.py

Bidirectional SQLite row mappers for Enumerated and Publications source records.

Operational Role:
    Flattens analytical, foreign-key, and temporal columns for SQLite indexing
    while preserving lossless round-trip serialization via payload_json for
    PopulationScheduleRecord, CensusScheduleRecord (supplemental schedules),
    DirectoryRollRecord, TaxAssessmentRecord (and SeptennialCensusRecord),
    Publication, NewspaperClipRecord, and PeriodicalArticleRecord.
"""

from __future__ import annotations

import json
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
from gda.model.source.enumerated import (
    AgriculturalScheduleRecord,
    CensusScheduleRecord,
    DirectoryRollRecord,
    ManufacturingScheduleRecord,
    MortalityScheduleRecord,
    PopulationSchedule1790_1840,
    PopulationSchedule1850_1870,
    PopulationSchedule1880,
    PopulationSchedule1900_1910,
    PopulationSchedule1920,
    PopulationSchedule1930,
    PopulationSchedule1940,
    PopulationSchedule1950,
    PopulationScheduleRecord,
    SeptennialCensusRecord,
    SlaveScheduleRecord,
    TaxAssessmentRecord,
    Veterans1890ScheduleRecord,
)
from gda.model.source.publications import (
    NewspaperClipRecord,
    PeriodicalArticleRecord,
    Publication,
)

__version__ = "1.0.0+build.4"

__all__ = [
    "DirectoryRollRecordMapper",
    "NewspaperClipRecordMapper",
    "PeriodicalArticleRecordMapper",
    "PopulationScheduleMapper",
    "PublicationMapper",
    "SupplementalScheduleMapper",
    "TaxAssessmentRecordMapper",
    "_POPULATION_SCHEDULE_REGISTRY",
    "_SUPPLEMENTAL_SCHEDULE_REGISTRY",
    "_TAX_RECORD_REGISTRY",
    "_hydrate_polymorphic_payload",
]

_POPULATION_SCHEDULE_REGISTRY: dict[str, type[PopulationScheduleRecord[Any]]] = {
    "PopulationScheduleRecord": PopulationScheduleRecord,
    "PopulationSchedule1790_1840": PopulationSchedule1790_1840,
    "PopulationSchedule1850_1870": PopulationSchedule1850_1870,
    "PopulationSchedule1880": PopulationSchedule1880,
    "PopulationSchedule1900_1910": PopulationSchedule1900_1910,
    "PopulationSchedule1920": PopulationSchedule1920,
    "PopulationSchedule1930": PopulationSchedule1930,
    "PopulationSchedule1940": PopulationSchedule1940,
    "PopulationSchedule1950": PopulationSchedule1950,
}

_SUPPLEMENTAL_SCHEDULE_REGISTRY: dict[str, type[CensusScheduleRecord[Any]]] = {
    "CensusScheduleRecord": CensusScheduleRecord,
    "AgriculturalScheduleRecord": AgriculturalScheduleRecord,
    "ManufacturingScheduleRecord": ManufacturingScheduleRecord,
    "MortalityScheduleRecord": MortalityScheduleRecord,
    "SlaveScheduleRecord": SlaveScheduleRecord,
    "Veterans1890ScheduleRecord": Veterans1890ScheduleRecord,
}

_TAX_RECORD_REGISTRY: dict[str, type[TaxAssessmentRecord]] = {
    "TaxAssessmentRecord": TaxAssessmentRecord,
    "SeptennialCensusRecord": SeptennialCensusRecord,
}


def _hydrate_polymorphic_payload[TModel](
    row: sqlite3.Row | dict[str, Any],
    registry: dict[str, type[TModel]],
    domain_label: str,
) -> TModel:
    """Hydrate a polymorphic enumerated schedule/tax record from row metadata."""
    try:
        data = dict(row)
        cls_name = str(data.get("schedule_class", ""))
        target_cls = registry.get(cls_name)
        if target_cls is None:
            raise EntityMappingError(f"Unknown {domain_label} schedule_class: {cls_name!r}.")
        raw_json = data.get("payload_json")
        if not raw_json or not isinstance(raw_json, str):
            raise EntityMappingError(f"Missing or invalid 'payload_json' for {cls_name}.")
        payload = json.loads(raw_json)
        return target_cls.from_dict(payload)  # type: ignore[attr-defined, no-any-return]
    except EntityMappingError:
        raise
    except Exception as err:
        raise EntityMappingError(f"Failed to hydrate {domain_label} from row: {err}") from err


class PopulationScheduleMapper(BaseRowMapper[PopulationScheduleRecord[Any]]):
    """Polymorphic SQLite row mapper for decennial PopulationScheduleRecord classes."""

    def __init__(self) -> None:
        """Initialize PopulationScheduleMapper."""
        super().__init__(PopulationScheduleRecord)

    def to_row(self, entity: PopulationScheduleRecord[Any]) -> dict[str, Any]:
        """Serialize PopulationScheduleRecord into enumerated_population_schedules columns."""
        try:
            row = _base_source_columns(entity)
            row.update(
                {
                    "schedule_class": type(entity).__name__,
                    "enumeration_year": int(entity.enumeration_year.value),
                    "jurisdiction_raw": entity.jurisdiction_raw,
                    "jurisdiction_id": _opt_val(entity.jurisdiction_id),
                    "state": entity.state,
                    "county": entity.county,
                    "township_or_ward": entity.township_or_ward,
                    "supervisor_district": getattr(entity, "supervisor_district", None),
                    "enumeration_district": getattr(entity, "enumeration_district", None),
                    "sheet_number": getattr(entity, "sheet_number", None),
                    "sheet_side": getattr(entity, "sheet_side", None),
                    "entry_count": len(entity.entries),
                }
            )
            return row
        except Exception as err:
            raise EntityMappingError(
                f"Failed to map PopulationScheduleRecord to row: {err}"
            ) from err

    def from_row(
        self,
        row: sqlite3.Row | dict[str, Any],
    ) -> PopulationScheduleRecord[Any]:
        """Hydrate concrete PopulationScheduleRecord subclass from SQLite row."""
        return _hydrate_polymorphic_payload(
            row,
            _POPULATION_SCHEDULE_REGISTRY,
            "population schedule",
        )


class SupplementalScheduleMapper(BaseRowMapper[CensusScheduleRecord[Any]]):
    """Polymorphic SQLite row mapper for non-population CensusScheduleRecord classes."""

    def __init__(self) -> None:
        """Initialize SupplementalScheduleMapper."""
        super().__init__(CensusScheduleRecord)

    def to_row(self, entity: CensusScheduleRecord[Any]) -> dict[str, Any]:
        """Serialize supplemental CensusScheduleRecord into enumerated_supplemental_schedules."""
        try:
            row = _base_source_columns(entity)
            row.update(
                {
                    "schedule_class": type(entity).__name__,
                    "enumeration_year": int(entity.enumeration_year.value),
                    "jurisdiction_raw": entity.jurisdiction_raw,
                    "jurisdiction_id": _opt_val(entity.jurisdiction_id),
                    "state": entity.state,
                    "county": entity.county,
                    "township_or_ward": entity.township_or_ward,
                    "enumeration_district": getattr(entity, "enumeration_district", None),
                    "sheet_number": getattr(entity, "sheet_number", None),
                    "entry_count": len(entity.entries),
                }
            )
            return row
        except Exception as err:
            raise EntityMappingError(f"Failed to map SupplementalSchedule to row: {err}") from err

    def from_row(
        self,
        row: sqlite3.Row | dict[str, Any],
    ) -> CensusScheduleRecord[Any]:
        """Hydrate concrete supplemental CensusScheduleRecord from SQLite row."""
        return _hydrate_polymorphic_payload(
            row,
            _SUPPLEMENTAL_SCHEDULE_REGISTRY,
            "supplemental schedule",
        )


class DirectoryRollRecordMapper(BaseRowMapper[DirectoryRollRecord]):
    """Bidirectional SQLite row mapper for DirectoryRollRecord."""

    def __init__(self) -> None:
        """Initialize DirectoryRollRecordMapper."""
        super().__init__(DirectoryRollRecord)

    def to_row(self, entity: DirectoryRollRecord) -> dict[str, Any]:
        """Serialize DirectoryRollRecord into enumerated_directories columns."""
        try:
            row = _base_source_columns(entity)
            row.update(
                {
                    "enumeration_year": int(entity.enumeration_year.value),
                    "jurisdiction_raw": entity.jurisdiction_raw,
                    "jurisdiction_id": _opt_val(entity.jurisdiction_id),
                    "publication_title_raw": entity.publication_title_raw,
                    "page_number_raw": entity.page_number_raw,
                    "entry_count": len(entity.entries),
                }
            )
            return row
        except Exception as err:
            raise EntityMappingError(f"Failed to map DirectoryRollRecord to row: {err}") from err

    def from_row(
        self,
        row: sqlite3.Row | dict[str, Any],
    ) -> DirectoryRollRecord:
        """Hydrate DirectoryRollRecord from SQLite row."""
        return _hydrate_from_payload(row, DirectoryRollRecord)


class TaxAssessmentRecordMapper(BaseRowMapper[TaxAssessmentRecord]):
    """Polymorphic SQLite row mapper for TaxAssessmentRecord and SeptennialCensusRecord."""

    def __init__(self) -> None:
        """Initialize TaxAssessmentRecordMapper."""
        super().__init__(TaxAssessmentRecord)

    def to_row(self, entity: TaxAssessmentRecord) -> dict[str, Any]:
        """Serialize TaxAssessmentRecord into enumerated_tax_assessments columns."""
        try:
            row = _base_source_columns(entity)
            row.update(
                {
                    "schedule_class": type(entity).__name__,
                    "enumeration_year": int(entity.enumeration_year.value),
                    "jurisdiction_raw": entity.jurisdiction_raw,
                    "jurisdiction_id": _opt_val(entity.jurisdiction_id),
                    "roll_locator_raw": entity.roll_locator_raw,
                    "schedule_name": entity.schedule_name,
                    "line_number": entity.line_number,
                    "taxpayer_id": _opt_val(entity.taxpayer_id),
                    "taxpayer_name_raw": entity.taxpayer_name_raw,
                    "classification": _opt_val(entity.classification),
                    "stated_occupation": entity.stated_occupation,
                }
            )
            return row
        except Exception as err:
            raise EntityMappingError(f"Failed to map TaxAssessmentRecord to row: {err}") from err

    def from_row(
        self,
        row: sqlite3.Row | dict[str, Any],
    ) -> TaxAssessmentRecord:
        """Hydrate TaxAssessmentRecord or SeptennialCensusRecord from SQLite row."""
        return _hydrate_polymorphic_payload(
            row,
            _TAX_RECORD_REGISTRY,
            "tax assessment",
        )


class PublicationMapper(BaseRowMapper[Publication]):
    """Bidirectional SQLite row mapper for Publication catalog entries."""

    def __init__(self) -> None:
        """Initialize PublicationMapper."""
        super().__init__(Publication)

    def to_row(self, entity: Publication) -> dict[str, Any]:
        """Serialize Publication into publications_catalog columns."""
        try:
            row = _base_source_columns(entity)
            row.update(
                {
                    "title_raw": entity.title.raw,
                    "pub_code": str(entity.pub_code),
                    "frequency": _opt_val(entity.frequency),
                    "publisher_raw": entity.publisher_raw,
                    "place_of_publication_raw": entity.place_of_publication_raw,
                    "location_id": _opt_val(entity.location_id),
                    "issn_or_lccn": entity.issn_or_lccn,
                    "is_active": 1 if entity.is_active else 0,
                }
            )
            return row
        except Exception as err:
            raise EntityMappingError(f"Failed to map Publication to row: {err}") from err

    def from_row(self, row: sqlite3.Row | dict[str, Any]) -> Publication:
        """Hydrate Publication from SQLite row."""
        return _hydrate_from_payload(row, Publication)


class NewspaperClipRecordMapper(BaseRowMapper[NewspaperClipRecord]):
    """Bidirectional SQLite row mapper for NewspaperClipRecord."""

    def __init__(self) -> None:
        """Initialize NewspaperClipRecordMapper."""
        super().__init__(NewspaperClipRecord)

    def to_row(self, entity: NewspaperClipRecord) -> dict[str, Any]:
        """Serialize NewspaperClipRecord into publications_newspaper_clips columns."""
        try:
            row = _base_source_columns(entity)
            row.update(
                {
                    "newspaper_name_raw": entity.newspaper_name_raw,
                    "issue_year": _date_year(entity.issue_date),
                    "issue_date_sort": _date_sort(entity.issue_date),
                    "news_category": _opt_val(entity.news_category),
                    "parent_source_id": _opt_val(entity.parent_source_id),
                    "pub_code": _opt_val(entity.pub_code),
                    "publication_location_id": _opt_val(entity.publication_location_id),
                    "headline_raw": entity.headline_raw,
                    "byline_raw": entity.byline_raw,
                    "page_column": entity.page_column,
                }
            )
            return row
        except Exception as err:
            raise EntityMappingError(f"Failed to map NewspaperClipRecord to row: {err}") from err

    def from_row(
        self,
        row: sqlite3.Row | dict[str, Any],
    ) -> NewspaperClipRecord:
        """Hydrate NewspaperClipRecord from SQLite row."""
        return _hydrate_from_payload(row, NewspaperClipRecord)


class PeriodicalArticleRecordMapper(BaseRowMapper[PeriodicalArticleRecord]):
    """Bidirectional SQLite row mapper for PeriodicalArticleRecord."""

    def __init__(self) -> None:
        """Initialize PeriodicalArticleRecordMapper."""
        super().__init__(PeriodicalArticleRecord)

    def to_row(self, entity: PeriodicalArticleRecord) -> dict[str, Any]:
        """Serialize PeriodicalArticleRecord into publications_periodical_articles columns."""
        try:
            row = _base_source_columns(entity)
            row.update(
                {
                    "publication_title_raw": entity.publication_title_raw,
                    "published_year": _date_year(entity.date_published),
                    "published_date_sort": _date_sort(entity.date_published),
                    "publication_kind": entity.publication_kind,
                    "parent_source_id": _opt_val(entity.parent_source_id),
                    "pub_code": _opt_val(entity.pub_code),
                    "institution_org_id": _opt_val(entity.institution_org_id),
                    "author_or_editor_raw": entity.author_or_editor_raw,
                    "article_or_chapter_title": entity.article_or_chapter_title,
                    "education_level": _opt_val(entity.education_level),
                    "entry_count": len(entity.entries),
                }
            )
            return row
        except Exception as err:
            raise EntityMappingError(
                f"Failed to map PeriodicalArticleRecord to row: {err}"
            ) from err

    def from_row(
        self,
        row: sqlite3.Row | dict[str, Any],
    ) -> PeriodicalArticleRecord:
        """Hydrate PeriodicalArticleRecord from SQLite row."""
        return _hydrate_from_payload(row, PeriodicalArticleRecord)
