"""Path: src/gda/db/mapper/education_manuscripts_orgs_other.py

Bidirectional SQLite row mappers for Education, Manuscripts, Orgs, and Other
Miscellaneous archival source records.

Operational Role:
    Flattens analytical, foreign-key, and temporal columns for SQLite indexing
    while preserving lossless round-trip serialization via payload_json for
    AcademicCredentialRecord, FamilyBibleRecord, NarrativeManuscriptRecord,
    OrganizationMembershipRecord, OrganizationRosterRecord, and
    OtherMiscellaneousRecord.
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
from gda.model.source.education.credential import AcademicCredentialRecord
from gda.model.source.manuscripts.bible import FamilyBibleRecord
from gda.model.source.manuscripts.narrative import NarrativeManuscriptRecord
from gda.model.source.orgs.membership import OrganizationMembershipRecord
from gda.model.source.orgs.roster import OrganizationRosterRecord
from gda.model.source.other.miscellaneous import OtherMiscellaneousRecord

__version__ = "1.0.0+build.2"

__all__ = [
    "AcademicCredentialRecordMapper",
    "FamilyBibleRecordMapper",
    "NarrativeManuscriptRecordMapper",
    "OrganizationMembershipRecordMapper",
    "OrganizationRosterRecordMapper",
    "OtherMiscellaneousRecordMapper",
]


class AcademicCredentialRecordMapper(BaseRowMapper[AcademicCredentialRecord]):
    """Bidirectional SQLite row mapper for AcademicCredentialRecord."""

    def __init__(self) -> None:
        """Initialize AcademicCredentialRecordMapper."""
        super().__init__(AcademicCredentialRecord)

    def to_row(self, entity: AcademicCredentialRecord) -> dict[str, Any]:
        """Serialize AcademicCredentialRecord into education_credentials columns."""
        try:
            row = _base_source_columns(entity)
            row.update(
                {
                    "institution_name_raw": entity.institution_name_raw,
                    "subject_name_raw": entity.subject_name_raw,
                    "issued_year": _date_year(entity.date_issued_or_published),
                    "issued_date_sort": _date_sort(entity.date_issued_or_published),
                    "education_level": _opt_val(entity.education_level),
                    "institution_location_id": _opt_val(entity.institution_location_id),
                    "subject_id": _opt_val(entity.subject_id),
                    "degree_or_credential": entity.degree_or_credential,
                    "graduation_year": entity.graduation_year,
                    "publication_title": entity.publication_title,
                }
            )
            return row
        except Exception as err:
            raise EntityMappingError(
                f"Failed to map AcademicCredentialRecord to row: {err}"
            ) from err

    def from_row(
        self,
        row: sqlite3.Row | dict[str, Any],
    ) -> AcademicCredentialRecord:
        """Hydrate AcademicCredentialRecord from SQLite row."""
        return _hydrate_from_payload(row, AcademicCredentialRecord)


class FamilyBibleRecordMapper(BaseRowMapper[FamilyBibleRecord]):
    """Bidirectional SQLite row mapper for FamilyBibleRecord."""

    def __init__(self) -> None:
        """Initialize FamilyBibleRecordMapper."""
        super().__init__(FamilyBibleRecord)

    def to_row(self, entity: FamilyBibleRecord) -> dict[str, Any]:
        """Serialize FamilyBibleRecord into manuscripts_family_bibles columns."""
        try:
            row = _base_source_columns(entity)
            row.update(
                {
                    "family_surname": entity.family_surname,
                    "edition_imprint": entity.edition_imprint,
                    "publication_year": entity.publication_year,
                    "original_owner_raw": entity.original_owner_raw,
                    "original_owner_id": _opt_val(entity.original_owner_id),
                    "entry_count": len(entity.entries),
                }
            )
            return row
        except Exception as err:
            raise EntityMappingError(f"Failed to map FamilyBibleRecord to row: {err}") from err

    def from_row(self, row: sqlite3.Row | dict[str, Any]) -> FamilyBibleRecord:
        """Hydrate FamilyBibleRecord from SQLite row."""
        return _hydrate_from_payload(row, FamilyBibleRecord)


class NarrativeManuscriptRecordMapper(BaseRowMapper[NarrativeManuscriptRecord]):
    """Bidirectional SQLite row mapper for NarrativeManuscriptRecord."""

    def __init__(self) -> None:
        """Initialize NarrativeManuscriptRecordMapper."""
        super().__init__(NarrativeManuscriptRecord)

    def to_row(self, entity: NarrativeManuscriptRecord) -> dict[str, Any]:
        """Serialize NarrativeManuscriptRecord into manuscripts_narratives columns."""
        try:
            row = _base_source_columns(entity)
            row.update(
                {
                    "title_or_subject": entity.title_or_subject,
                    "author_or_sender_raw": entity.author_or_sender_raw,
                    "author_or_sender_id": _opt_val(entity.author_or_sender_id),
                    "recipient_raw": entity.recipient_raw,
                    "recipient_id": _opt_val(entity.recipient_id),
                    "collection_name": entity.collection_name,
                    "origin_place_id": _opt_val(entity.origin_place_id),
                    "destination_place_id": _opt_val(entity.destination_place_id),
                    "written_year": _date_year(entity.date_written_or_published),
                    "written_date_sort": _date_sort(entity.date_written_or_published),
                }
            )
            return row
        except Exception as err:
            raise EntityMappingError(
                f"Failed to map NarrativeManuscriptRecord to row: {err}"
            ) from err

    def from_row(
        self,
        row: sqlite3.Row | dict[str, Any],
    ) -> NarrativeManuscriptRecord:
        """Hydrate NarrativeManuscriptRecord from SQLite row."""
        return _hydrate_from_payload(row, NarrativeManuscriptRecord)


class OrganizationMembershipRecordMapper(BaseRowMapper[OrganizationMembershipRecord]):
    """Bidirectional SQLite row mapper for OrganizationMembershipRecord."""

    def __init__(self) -> None:
        """Initialize OrganizationMembershipRecordMapper."""
        super().__init__(OrganizationMembershipRecord)

    def to_row(self, entity: OrganizationMembershipRecord) -> dict[str, Any]:
        """Serialize OrganizationMembershipRecord into orgs_memberships columns."""
        try:
            row = _base_source_columns(entity)
            row.update(
                {
                    "individual_id": str(entity.individual_id.value),
                    "organization_name_raw": entity.organization_name_raw,
                    "org_id": _opt_val(entity.org_id),
                    "org_category": str(entity.org_category.value),
                    "affiliation_type": str(entity.affiliation_type.value),
                    "membership_status": str(entity.membership_status.value),
                    "role_or_title_raw": entity.role_or_title_raw,
                    "degree_or_rank_raw": entity.degree_or_rank_raw,
                }
            )
            return row
        except Exception as err:
            raise EntityMappingError(
                f"Failed to map OrganizationMembershipRecord to row: {err}"
            ) from err

    def from_row(
        self,
        row: sqlite3.Row | dict[str, Any],
    ) -> OrganizationMembershipRecord:
        """Hydrate OrganizationMembershipRecord from SQLite row."""
        return _hydrate_from_payload(row, OrganizationMembershipRecord)


class OrganizationRosterRecordMapper(BaseRowMapper[OrganizationRosterRecord]):
    """Bidirectional SQLite row mapper for OrganizationRosterRecord."""

    def __init__(self) -> None:
        """Initialize OrganizationRosterRecordMapper."""
        super().__init__(OrganizationRosterRecord)

    def to_row(self, entity: OrganizationRosterRecord) -> dict[str, Any]:
        """Serialize OrganizationRosterRecord into orgs_rosters columns."""
        try:
            row = _base_source_columns(entity)
            row.update(
                {
                    "enumeration_year": int(entity.enumeration_year.value),
                    "jurisdiction_raw": entity.jurisdiction_raw,
                    "jurisdiction_id": _opt_val(entity.jurisdiction_id),
                    "organization_name_raw": entity.organization_name_raw,
                    "org_id": _opt_val(entity.org_id),
                    "org_category": str(entity.org_category.value),
                    "roster_title": entity.roster_title,
                    "entry_count": len(entity.entries),
                }
            )
            return row
        except Exception as err:
            raise EntityMappingError(
                f"Failed to map OrganizationRosterRecord to row: {err}"
            ) from err

    def from_row(
        self,
        row: sqlite3.Row | dict[str, Any],
    ) -> OrganizationRosterRecord:
        """Hydrate OrganizationRosterRecord from SQLite row."""
        return _hydrate_from_payload(row, OrganizationRosterRecord)


class OtherMiscellaneousRecordMapper(BaseRowMapper[OtherMiscellaneousRecord]):
    """Bidirectional SQLite row mapper for OtherMiscellaneousRecord."""

    def __init__(self) -> None:
        """Initialize OtherMiscellaneousRecordMapper."""
        super().__init__(OtherMiscellaneousRecord)

    def to_row(self, entity: OtherMiscellaneousRecord) -> dict[str, Any]:
        """Serialize OtherMiscellaneousRecord into other_miscellaneous_records columns."""
        try:
            row = _base_source_columns(entity)
            row.update(
                {
                    "item_year": _date_year(entity.item_date),
                    "item_date_sort": _date_sort(entity.item_date),
                    "organization_or_entity_name": (entity.organization_or_entity_name),
                    "organization_location_id": _opt_val(entity.organization_location_id),
                }
            )
            return row
        except Exception as err:
            raise EntityMappingError(
                f"Failed to map OtherMiscellaneousRecord to row: {err}"
            ) from err

    def from_row(
        self,
        row: sqlite3.Row | dict[str, Any],
    ) -> OtherMiscellaneousRecord:
        """Hydrate OtherMiscellaneousRecord from SQLite row."""
        return _hydrate_from_payload(row, OtherMiscellaneousRecord)
