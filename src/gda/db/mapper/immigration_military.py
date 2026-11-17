"""Path: src/gda/db/mapper/immigration_military.py

Bidirectional and polymorphic SQLite row mappers for Immigration and Military sources.

Operational Role:
    Flattens analytical, foreign-key, and temporal columns for SQLite indexing
    while leveraging native SourceRecord.to_dict() and SourceRecord.from_dict()
    reflection and polymorphic subclass hydration for Immigration and Military
    archival source records.
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
    _opt_year,
)
from gda.model.base.source import SourceRecord
from gda.model.source.immigration.manifest import ImmigrationManifestRecord
from gda.model.source.immigration.naturalization import NaturalizationRecord
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

__version__ = "1.0.0+build.8"

__all__ = [
    "BountyLandWarrantRecordMapper",
    "ImmigrationManifestRecordMapper",
    "MilitaryAwardRecordMapper",
    "MilitaryCasualtyRecordMapper",
    "MilitaryDraftRecordMapper",
    "MilitaryPensionRecordMapper",
    "MilitaryServiceRecordMapper",
    "NaturalizationRecordMapper",
    "_CASUALTY_RECORD_REGISTRY",
    "_DRAFT_RECORD_REGISTRY",
    "_PENSION_RECORD_REGISTRY",
    "_SERVICE_RECORD_REGISTRY",
    "deserialize_military_record",
    "serialize_military_record",
]

_DRAFT_RECORD_REGISTRY: dict[str, type[MilitaryDraftRecord]] = {
    "MilitaryDraftRecord": MilitaryDraftRecord,
    "CivilWarDraftRecord": CivilWarDraftRecord,
    "ColonialMilitiaRecord": ColonialMilitiaRecord,
    "ModernSelectiveServiceRecord": ModernSelectiveServiceRecord,
    "WwiDraftCardRecord": WwiDraftCardRecord,
    "WwiiDraftCardRecord": WwiiDraftCardRecord,
}

_SERVICE_RECORD_REGISTRY: dict[str, type[MilitaryServiceRecord]] = {
    "MilitaryServiceRecord": MilitaryServiceRecord,
    "EnlistmentMusterRecord": EnlistmentMusterRecord,
    "SeparationDischargeRecord": SeparationDischargeRecord,
}

_PENSION_RECORD_REGISTRY: dict[str, type[MilitaryPensionRecord]] = {
    "MilitaryPensionRecord": MilitaryPensionRecord,
    "PensionVeteranClaimRecord": PensionVeteranClaimRecord,
    "PensionWidowDependentRecord": PensionWidowDependentRecord,
}

_CASUALTY_RECORD_REGISTRY: dict[str, type[MilitaryCasualtyRecord]] = {
    "MilitaryCasualtyRecord": MilitaryCasualtyRecord,
    "CombatCasualtyRecord": CombatCasualtyRecord,
    "MilitaryBurialRecord": MilitaryBurialRecord,
    "PrisonerOfWarRecord": PrisonerOfWarRecord,
}


def serialize_military_record(entity: SourceRecord) -> dict[str, Any]:
    """Serialize any Military SourceRecord subclass via native to_dict() reflection."""
    data = entity.to_dict()
    data["record_class"] = type(entity).__name__
    return data


def deserialize_military_record[TModel: SourceRecord](
    target_cls: type[TModel],
    data: dict[str, Any],
) -> TModel:
    """Hydrate a concrete Military SourceRecord subclass via native from_dict()."""
    return target_cls.from_dict(data)


def _hydrate_polymorphic_record[TModel: SourceRecord](
    row: sqlite3.Row | dict[str, Any],
    registry: dict[str, type[TModel]],
    domain_label: str,
) -> TModel:
    """Hydrate a polymorphic military record using the row's record_class column."""
    try:
        data = dict(row)
        cls_name = str(data.get("record_class", ""))
        target_cls = registry.get(cls_name)
        if target_cls is None:
            raise EntityMappingError(f"Unknown {domain_label} record_class: {cls_name!r}.")
        raw_json = data.get("payload_json")
        if not raw_json or not isinstance(raw_json, str):
            raise EntityMappingError(f"Missing or invalid 'payload_json' for {cls_name}.")
        payload = json.loads(raw_json)
        return target_cls.from_dict(payload)
    except EntityMappingError:
        raise
    except Exception as err:
        raise EntityMappingError(f"Failed to hydrate {domain_label} from row: {err}") from err


class ImmigrationManifestRecordMapper(BaseRowMapper[ImmigrationManifestRecord]):
    """Bidirectional SQLite row mapper for ImmigrationManifestRecord."""

    def __init__(self) -> None:
        """Initialize ImmigrationManifestRecordMapper."""
        super().__init__(ImmigrationManifestRecord)

    def to_row(self, entity: ImmigrationManifestRecord) -> dict[str, Any]:
        """Serialize ImmigrationManifestRecord into immigration_manifests columns."""
        try:
            row = _base_source_columns(entity)
            row.update(
                {
                    "port_of_arrival_raw": entity.port_of_arrival_raw,
                    "arrival_year": _date_year(entity.arrival_date),
                    "arrival_date_sort": _date_sort(entity.arrival_date),
                    "manifest_locator": entity.manifest_locator,
                    "port_of_arrival_id": _opt_val(entity.port_of_arrival_id),
                    "port_of_departure_id": _opt_val(entity.port_of_departure_id),
                    "ship_name": entity.ship_name,
                    "shipping_line": entity.shipping_line,
                    "passenger_count": len(entity.passengers),
                }
            )
            return row
        except Exception as err:
            raise EntityMappingError(
                f"Failed to map ImmigrationManifestRecord to row: {err}"
            ) from err

    def from_row(
        self,
        row: sqlite3.Row | dict[str, Any],
    ) -> ImmigrationManifestRecord:
        """Hydrate ImmigrationManifestRecord from SQLite row."""
        return _hydrate_from_payload(row, ImmigrationManifestRecord)


class NaturalizationRecordMapper(BaseRowMapper[NaturalizationRecord]):
    """Bidirectional SQLite row mapper for NaturalizationRecord."""

    def __init__(self) -> None:
        """Initialize NaturalizationRecordMapper."""
        super().__init__(NaturalizationRecord)

    def to_row(self, entity: NaturalizationRecord) -> dict[str, Any]:
        """Serialize NaturalizationRecord into immigration_naturalizations columns."""
        try:
            row = _base_source_columns(entity)
            row.update(
                {
                    "court_name": entity.court_name,
                    "docket_locator": entity.docket_locator,
                    "applicant_name_raw": entity.applicant_name_raw,
                    "event_year": _date_year(entity.event_date),
                    "event_date_sort": _date_sort(entity.event_date),
                    "court_location_id": _opt_val(entity.court_location_id),
                    "applicant_id": _opt_val(entity.applicant_id),
                    "current_residence_id": _opt_val(entity.current_residence_id),
                    "place_of_birth_id": _opt_val(entity.place_of_birth_id),
                    "stage": _opt_val(entity.stage),
                    "certificate_stub_number": entity.certificate_stub_number,
                    "witness_count": len(entity.witnesses),
                }
            )
            return row
        except Exception as err:
            raise EntityMappingError(f"Failed to map NaturalizationRecord to row: {err}") from err

    def from_row(self, row: sqlite3.Row | dict[str, Any]) -> NaturalizationRecord:
        """Hydrate NaturalizationRecord from SQLite row."""
        return _hydrate_from_payload(row, NaturalizationRecord)


class MilitaryDraftRecordMapper(BaseRowMapper[MilitaryDraftRecord]):
    """Polymorphic SQLite row mapper for MilitaryDraftRecord and era subclasses."""

    def __init__(self) -> None:
        """Initialize MilitaryDraftRecordMapper."""
        super().__init__(MilitaryDraftRecord)

    def to_row(self, entity: MilitaryDraftRecord) -> dict[str, Any]:
        """Serialize MilitaryDraftRecord or subclass into military_draft_records columns."""
        try:
            row = _base_source_columns(entity)
            row.update(
                {
                    "record_class": type(entity).__name__,
                    "draft_record_id": str(entity.draft_record_id.value),
                    "registrant_id": str(entity.registrant_id.value),
                    "registrant_name_raw": entity.registrant_name_raw,
                    "draft_year": int(entity.draft_year.value),
                    "board_jurisdiction_raw": entity.board_jurisdiction_raw,
                    "card_tier": str(entity.card_tier.value),
                    "board_location_id": _opt_val(entity.board_location_id),
                }
            )
            return row
        except Exception as err:
            raise EntityMappingError(f"Failed to map MilitaryDraftRecord to row: {err}") from err

    def from_row(self, row: sqlite3.Row | dict[str, Any]) -> MilitaryDraftRecord:
        """Hydrate concrete MilitaryDraftRecord subclass from SQLite row."""
        return _hydrate_polymorphic_record(
            row,
            _DRAFT_RECORD_REGISTRY,
            "military draft",
        )


class MilitaryServiceRecordMapper(BaseRowMapper[MilitaryServiceRecord]):
    """Polymorphic SQLite row mapper for MilitaryServiceRecord and subclasses."""

    def __init__(self) -> None:
        """Initialize MilitaryServiceRecordMapper."""
        super().__init__(MilitaryServiceRecord)

    def to_row(self, entity: MilitaryServiceRecord) -> dict[str, Any]:
        """Serialize MilitaryServiceRecord into military_service_records columns."""
        try:
            row = _base_source_columns(entity)
            row.update(
                {
                    "record_class": type(entity).__name__,
                    "service_record_id": str(entity.service_record_id.value),
                    "veteran_id": str(entity.veteran_id.value),
                    "veteran_name_raw": entity.veteran_name_raw,
                    "branch": str(entity.branch.value),
                    "service_component": str(entity.service_component.value),
                    "unit_designation_raw": entity.unit_designation_raw,
                    "rank_raw": entity.rank_raw,
                    "service_number_raw": entity.service_number_raw,
                    "enlistment_year": _opt_year(entity.enlistment_year),
                    "separation_year": _opt_year(entity.separation_year),
                    "separation_character": str(entity.separation_character.value),
                    "enlistment_location_id": _opt_val(entity.enlistment_location_id),
                }
            )
            return row
        except Exception as err:
            raise EntityMappingError(f"Failed to map MilitaryServiceRecord to row: {err}") from err

    def from_row(
        self,
        row: sqlite3.Row | dict[str, Any],
    ) -> MilitaryServiceRecord:
        """Hydrate concrete MilitaryServiceRecord subclass from SQLite row."""
        return _hydrate_polymorphic_record(
            row,
            _SERVICE_RECORD_REGISTRY,
            "military service",
        )


class MilitaryPensionRecordMapper(BaseRowMapper[MilitaryPensionRecord]):
    """Polymorphic SQLite row mapper for MilitaryPensionRecord and subclasses."""

    def __init__(self) -> None:
        """Initialize MilitaryPensionRecordMapper."""
        super().__init__(MilitaryPensionRecord)

    def to_row(self, entity: MilitaryPensionRecord) -> dict[str, Any]:
        """Serialize MilitaryPensionRecord into military_pension_records columns."""
        try:
            row = _base_source_columns(entity)
            row.update(
                {
                    "record_class": type(entity).__name__,
                    "veteran_id": str(entity.veteran_id.value),
                    "veteran_name_raw": entity.veteran_name_raw,
                    "claimant_id": str(entity.claimant_id.value),
                    "claimant_name_raw": entity.claimant_name_raw,
                    "claimant_role": str(entity.claimant_role.value),
                    "payment_authority": str(entity.payment_authority.value),
                    "application_year": int(entity.application_year.value),
                    "application_number_raw": entity.application_number_raw,
                    "certificate_number_raw": entity.certificate_number_raw,
                    "application_location_id": _opt_val(entity.application_location_id),
                }
            )
            return row
        except Exception as err:
            raise EntityMappingError(f"Failed to map MilitaryPensionRecord to row: {err}") from err

    def from_row(
        self,
        row: sqlite3.Row | dict[str, Any],
    ) -> MilitaryPensionRecord:
        """Hydrate concrete MilitaryPensionRecord subclass from SQLite row."""
        return _hydrate_polymorphic_record(
            row,
            _PENSION_RECORD_REGISTRY,
            "military pension",
        )


class BountyLandWarrantRecordMapper(BaseRowMapper[BountyLandWarrantRecord]):
    """Bidirectional SQLite row mapper for BountyLandWarrantRecord."""

    def __init__(self) -> None:
        """Initialize BountyLandWarrantRecordMapper."""
        super().__init__(BountyLandWarrantRecord)

    def to_row(self, entity: BountyLandWarrantRecord) -> dict[str, Any]:
        """Serialize BountyLandWarrantRecord into military_bounty_land_warrants columns."""
        try:
            row = _base_source_columns(entity)
            row.update(
                {
                    "veteran_id": str(entity.veteran_id.value),
                    "veteran_name_raw": entity.veteran_name_raw,
                    "warrantee_id": str(entity.warrantee_id.value),
                    "warrantee_name_raw": entity.warrantee_name_raw,
                    "claimant_role": str(entity.claimant_role.value),
                    "bounty_act": str(entity.bounty_act.value),
                    "warrant_number_raw": entity.warrant_number_raw,
                    "acreage": int(entity.acreage),
                    "warrant_year": int(entity.warrant_year.value),
                    "patent_location_id": _opt_val(entity.patent_location_id),
                    "assignee_id": _opt_val(entity.assignee_id),
                }
            )
            return row
        except Exception as err:
            raise EntityMappingError(
                f"Failed to map BountyLandWarrantRecord to row: {err}"
            ) from err

    def from_row(
        self,
        row: sqlite3.Row | dict[str, Any],
    ) -> BountyLandWarrantRecord:
        """Hydrate BountyLandWarrantRecord from SQLite row."""
        return _hydrate_from_payload(row, BountyLandWarrantRecord)


class MilitaryCasualtyRecordMapper(BaseRowMapper[MilitaryCasualtyRecord]):
    """Polymorphic SQLite row mapper for MilitaryCasualtyRecord and subclasses."""

    def __init__(self) -> None:
        """Initialize MilitaryCasualtyRecordMapper."""
        super().__init__(MilitaryCasualtyRecord)

    def to_row(self, entity: MilitaryCasualtyRecord) -> dict[str, Any]:
        """Serialize MilitaryCasualtyRecord into military_casualty_records columns."""
        try:
            row = _base_source_columns(entity)
            row.update(
                {
                    "record_class": type(entity).__name__,
                    "servicemember_id": str(entity.servicemember_id.value),
                    "servicemember_name_raw": entity.servicemember_name_raw,
                    "branch": str(entity.branch.value),
                    "casualty_category": str(entity.casualty_category.value),
                    "casualty_year": int(entity.casualty_year.value),
                    "unit_designation_raw": entity.unit_designation_raw,
                    "rank_raw": entity.rank_raw,
                    "casualty_location_id": _opt_val(entity.casualty_location_id),
                }
            )
            return row
        except Exception as err:
            raise EntityMappingError(f"Failed to map MilitaryCasualtyRecord to row: {err}") from err

    def from_row(
        self,
        row: sqlite3.Row | dict[str, Any],
    ) -> MilitaryCasualtyRecord:
        """Hydrate concrete MilitaryCasualtyRecord subclass from SQLite row."""
        return _hydrate_polymorphic_record(
            row,
            _CASUALTY_RECORD_REGISTRY,
            "military casualty",
        )


class MilitaryAwardRecordMapper(BaseRowMapper[MilitaryAwardRecord]):
    """Bidirectional SQLite row mapper for MilitaryAwardRecord."""

    def __init__(self) -> None:
        """Initialize MilitaryAwardRecordMapper."""
        super().__init__(MilitaryAwardRecord)

    def to_row(self, entity: MilitaryAwardRecord) -> dict[str, Any]:
        """Serialize MilitaryAwardRecord into military_award_records columns."""
        try:
            row = _base_source_columns(entity)
            row.update(
                {
                    "recipient_id": str(entity.recipient_id.value),
                    "recipient_name_raw": entity.recipient_name_raw,
                    "award_name_raw": entity.award_name_raw,
                    "branch": str(entity.branch.value),
                    "award_tier": str(entity.award_tier.value),
                    "award_scope": str(entity.award_scope.value),
                    "award_year": int(entity.award_year.value),
                    "action_year": _opt_year(entity.action_year),
                    "is_posthumous": 1 if entity.is_posthumous else 0,
                    "action_location_id": _opt_val(entity.action_location_id),
                }
            )
            return row
        except Exception as err:
            raise EntityMappingError(f"Failed to map MilitaryAwardRecord to row: {err}") from err

    def from_row(self, row: sqlite3.Row | dict[str, Any]) -> MilitaryAwardRecord:
        """Hydrate MilitaryAwardRecord from SQLite row."""
        return _hydrate_from_payload(row, MilitaryAwardRecord)
