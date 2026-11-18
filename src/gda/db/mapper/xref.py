"""Path: src/gda/db/mapper/xref.py

Bidirectional SQLite row mappers for Cross-Reference (gda.model.xref) models.

Operational Role:
    Maps all 9 immutable XRef index models to their relational SQLite tables
    using xref_key as the deterministic primary key ('id') and payload_json for
    lossless hydration.
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from gda.db.exceptions import EntityMappingError
from gda.db.mapper.base import BaseRowMapper, _opt_val, _opt_year
from gda.model.xref import (
    FactParticipantXRef,
    IndividualFamilyXRef,
    IndividualOrganizationXRef,
    IndividualSourceXRef,
    IndividualSurnameXRef,
    LocationXRef,
    MediaXRef,
    SiteXRef,
    SurnameXRef,
)

__version__ = "1.0.0+build.2"

__all__ = [
    "FactParticipantXRefMapper",
    "IndividualFamilyXRefMapper",
    "IndividualOrganizationXRefMapper",
    "IndividualSourceXRefMapper",
    "IndividualSurnameXRefMapper",
    "LocationXRefMapper",
    "MediaXRefMapper",
    "SiteXRefMapper",
    "SurnameXRefMapper",
]


def _hydrate_xref[TXRef](
    row: sqlite3.Row | dict[str, Any],
    model_cls: type[TXRef],
) -> TXRef:
    """Hydrate an XRef dataclass from its row payload_json."""
    try:
        data = dict(row)
        raw_json = data.get("payload_json")
        if not raw_json or not isinstance(raw_json, str):
            raise EntityMappingError(f"Missing or invalid 'payload_json' for {model_cls.__name__}.")
        payload = json.loads(raw_json)
        return model_cls.from_dict(payload)  # type: ignore[attr-defined, no-any-return]
    except EntityMappingError:
        raise
    except Exception as err:
        raise EntityMappingError(f"Failed to hydrate {model_cls.__name__} from row: {err}") from err


class FactParticipantXRefMapper(BaseRowMapper[FactParticipantXRef]):
    """Bidirectional SQLite row mapper for FactParticipantXRef."""

    def __init__(self) -> None:
        """Initialize FactParticipantXRefMapper."""
        super().__init__(FactParticipantXRef)

    def to_row(self, entity: FactParticipantXRef) -> dict[str, Any]:
        """Serialize FactParticipantXRef into xref_fact_participants columns."""
        try:
            return {
                "id": entity.xref_key,
                "fact_id": entity.fact_id.value,
                "individual_id": entity.individual_id.value,
                "role": entity.role.value,
                "fact_type": entity.fact_type.value,
                "is_primary_subject": 1 if entity.is_primary_subject else 0,
                "temporal_year": _opt_year(entity.temporal_year),
                "location_id": _opt_val(entity.location_id),
                "site_id": _opt_val(entity.site_id),
                "payload_json": json.dumps(entity.to_dict(), sort_keys=True),
            }
        except Exception as err:
            raise EntityMappingError(f"Failed to map FactParticipantXRef to row: {err}") from err

    def from_row(
        self,
        row: sqlite3.Row | dict[str, Any],
    ) -> FactParticipantXRef:
        """Hydrate FactParticipantXRef from SQLite row."""
        return _hydrate_xref(row, FactParticipantXRef)


class IndividualFamilyXRefMapper(BaseRowMapper[IndividualFamilyXRef]):
    """Bidirectional SQLite row mapper for IndividualFamilyXRef."""

    def __init__(self) -> None:
        """Initialize IndividualFamilyXRefMapper."""
        super().__init__(IndividualFamilyXRef)

    def to_row(self, entity: IndividualFamilyXRef) -> dict[str, Any]:
        """Serialize IndividualFamilyXRef into xref_individual_families columns."""
        try:
            return {
                "id": entity.xref_key,
                "family_id": entity.family_id.value,
                "individual_id": entity.individual_id.value,
                "is_partner": 1 if entity.is_partner else 0,
                "pedigree": _opt_val(entity.pedigree),
                "child_order": entity.child_order,
                "payload_json": json.dumps(entity.to_dict(), sort_keys=True),
            }
        except Exception as err:
            raise EntityMappingError(f"Failed to map IndividualFamilyXRef to row: {err}") from err

    def from_row(
        self,
        row: sqlite3.Row | dict[str, Any],
    ) -> IndividualFamilyXRef:
        """Hydrate IndividualFamilyXRef from SQLite row."""
        return _hydrate_xref(row, IndividualFamilyXRef)


class IndividualOrganizationXRefMapper(BaseRowMapper[IndividualOrganizationXRef]):
    """Bidirectional SQLite row mapper for IndividualOrganizationXRef."""

    def __init__(self) -> None:
        """Initialize IndividualOrganizationXRefMapper."""
        super().__init__(IndividualOrganizationXRef)

    def to_row(self, entity: IndividualOrganizationXRef) -> dict[str, Any]:
        """Serialize IndividualOrganizationXRef into xref_individual_organizations columns."""
        try:
            return {
                "id": entity.xref_key,
                "organization_id": entity.organization_id.value,
                "individual_id": entity.individual_id.value,
                "org_category": entity.org_category.value,
                "affiliation_type": entity.affiliation_type.value,
                "membership_status": entity.membership_status.value,
                "start_year": _opt_year(entity.start_year),
                "end_year": _opt_year(entity.end_year),
                "payload_json": json.dumps(entity.to_dict(), sort_keys=True),
            }
        except Exception as err:
            raise EntityMappingError(
                f"Failed to map IndividualOrganizationXRef to row: {err}"
            ) from err

    def from_row(
        self,
        row: sqlite3.Row | dict[str, Any],
    ) -> IndividualOrganizationXRef:
        """Hydrate IndividualOrganizationXRef from SQLite row."""
        return _hydrate_xref(row, IndividualOrganizationXRef)


class IndividualSourceXRefMapper(BaseRowMapper[IndividualSourceXRef]):
    """Bidirectional SQLite row mapper for IndividualSourceXRef."""

    def __init__(self) -> None:
        """Initialize IndividualSourceXRefMapper."""
        super().__init__(IndividualSourceXRef)

    def to_row(self, entity: IndividualSourceXRef) -> dict[str, Any]:
        """Serialize IndividualSourceXRef into xref_individual_sources columns."""
        try:
            return {
                "id": entity.xref_key,
                "source_id": entity.source_id.value,
                "individual_id": entity.individual_id.value,
                "role": entity.role.value,
                "record_category": entity.record_category.value,
                "record_type": entity.record_type.value,
                "is_primary_subject": 1 if entity.is_primary_subject else 0,
                "temporal_year": _opt_year(entity.temporal_year),
                "location_id": _opt_val(entity.location_id),
                "site_id": _opt_val(entity.site_id),
                "payload_json": json.dumps(entity.to_dict(), sort_keys=True),
            }
        except Exception as err:
            raise EntityMappingError(f"Failed to map IndividualSourceXRef to row: {err}") from err

    def from_row(
        self,
        row: sqlite3.Row | dict[str, Any],
    ) -> IndividualSourceXRef:
        """Hydrate IndividualSourceXRef from SQLite row."""
        return _hydrate_xref(row, IndividualSourceXRef)


class IndividualSurnameXRefMapper(BaseRowMapper[IndividualSurnameXRef]):
    """Bidirectional SQLite row mapper for IndividualSurnameXRef."""

    def __init__(self) -> None:
        """Initialize IndividualSurnameXRefMapper."""
        super().__init__(IndividualSurnameXRef)

    def to_row(self, entity: IndividualSurnameXRef) -> dict[str, Any]:
        """Serialize IndividualSurnameXRef into xref_individual_surnames columns."""
        try:
            return {
                "id": entity.xref_key,
                "surname": entity.surname,
                "individual_id": entity.individual_id.value,
                "is_birth_surname": 1 if entity.is_birth_surname else 0,
                "birth_year": _opt_year(entity.birth_year),
                "death_year": _opt_year(entity.death_year),
                "payload_json": json.dumps(entity.to_dict(), sort_keys=True),
            }
        except Exception as err:
            raise EntityMappingError(f"Failed to map IndividualSurnameXRef to row: {err}") from err

    def from_row(
        self,
        row: sqlite3.Row | dict[str, Any],
    ) -> IndividualSurnameXRef:
        """Hydrate IndividualSurnameXRef from SQLite row."""
        return _hydrate_xref(row, IndividualSurnameXRef)


class LocationXRefMapper(BaseRowMapper[LocationXRef]):
    """Bidirectional SQLite row mapper for LocationXRef."""

    def __init__(self) -> None:
        """Initialize LocationXRefMapper."""
        super().__init__(LocationXRef)

    def to_row(self, entity: LocationXRef) -> dict[str, Any]:
        """Serialize LocationXRef into xref_locations columns."""
        try:
            return {
                "id": entity.xref_key,
                "location_id": entity.location_id.value,
                "target_id": entity.target_id.value,
                "payload_json": json.dumps(entity.to_dict(), sort_keys=True),
            }
        except Exception as err:
            raise EntityMappingError(f"Failed to map LocationXRef to row: {err}") from err

    def from_row(self, row: sqlite3.Row | dict[str, Any]) -> LocationXRef:
        """Hydrate LocationXRef from SQLite row."""
        return _hydrate_xref(row, LocationXRef)


class MediaXRefMapper(BaseRowMapper[MediaXRef]):
    """Bidirectional SQLite row mapper for MediaXRef."""

    def __init__(self) -> None:
        """Initialize MediaXRefMapper."""
        super().__init__(MediaXRef)

    def to_row(self, entity: MediaXRef) -> dict[str, Any]:
        """Serialize MediaXRef into xref_media columns."""
        try:
            return {
                "id": entity.xref_key,
                "media_id": entity.media_id.value,
                "target_id": entity.target_id.value,
                "payload_json": json.dumps(entity.to_dict(), sort_keys=True),
            }
        except Exception as err:
            raise EntityMappingError(f"Failed to map MediaXRef to row: {err}") from err

    def from_row(self, row: sqlite3.Row | dict[str, Any]) -> MediaXRef:
        """Hydrate MediaXRef from SQLite row."""
        return _hydrate_xref(row, MediaXRef)


class SiteXRefMapper(BaseRowMapper[SiteXRef]):
    """Bidirectional SQLite row mapper for SiteXRef."""

    def __init__(self) -> None:
        """Initialize SiteXRefMapper."""
        super().__init__(SiteXRef)

    def to_row(self, entity: SiteXRef) -> dict[str, Any]:
        """Serialize SiteXRef into xref_sites columns."""
        try:
            return {
                "id": entity.xref_key,
                "site_id": entity.site_id.value,
                "location_id": entity.location_id.value,
                "target_id": entity.target_id.value,
                "payload_json": json.dumps(entity.to_dict(), sort_keys=True),
            }
        except Exception as err:
            raise EntityMappingError(f"Failed to map SiteXRef to row: {err}") from err

    def from_row(self, row: sqlite3.Row | dict[str, Any]) -> SiteXRef:
        """Hydrate SiteXRef from SQLite row."""
        return _hydrate_xref(row, SiteXRef)


class SurnameXRefMapper(BaseRowMapper[SurnameXRef]):
    """Bidirectional SQLite row mapper for SurnameXRef."""

    def __init__(self) -> None:
        """Initialize SurnameXRefMapper."""
        super().__init__(SurnameXRef)

    def to_row(self, entity: SurnameXRef) -> dict[str, Any]:
        """Serialize SurnameXRef into xref_surnames columns."""
        try:
            return {
                "id": entity.xref_key,
                "canonical_surname": entity.canonical_surname,
                "variant_surname": entity.variant_surname,
                "variant_name_type": entity.variant_name_type.value,
                "variant_phonetic_code": entity.variant_phonetic_code,
                "payload_json": json.dumps(entity.to_dict(), sort_keys=True),
            }
        except Exception as err:
            raise EntityMappingError(f"Failed to map SurnameXRef to row: {err}") from err

    def from_row(self, row: sqlite3.Row | dict[str, Any]) -> SurnameXRef:
        """Hydrate SurnameXRef from SQLite row."""
        return _hydrate_xref(row, SurnameXRef)
