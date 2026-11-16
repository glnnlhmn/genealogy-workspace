"""Path: src/gda/db/mapper/immigration_military.py

Bidirectional and polymorphic SQLite row mappers for Immigration and Military sources.

Operational Role:
    Flattens analytical, foreign-key, and temporal columns for SQLite indexing
    while supporting full dataclass reflection serialization and polymorphic
    subclass hydration for Immigration and Military source records.
"""

from __future__ import annotations

import dataclasses
import json
import sqlite3
from enum import Enum
from typing import Any

from gda.core.enums.military import (
    AwardScope,
    BountyLandAct,
    CasualtyCategory,
    CivilWarConscriptionAllegiance,
    CivilWarEnrollmentClass,
    ColonialMilitiaClass,
    ColonialWarPeriod,
    DraftCardTier,
    IntermentCemeteryType,
    MilitaryAwardTier,
    MilitaryBranch,
    ModernDraftEra,
    MusterRollType,
    PensionClaimantRole,
    PensionPaymentAuthority,
    PowCampType,
    SeparationCharacter,
    SeparationFormType,
    ServiceComponent,
    SssClassification,
    WwiCitizenshipStatus,
    WwiiDraftWave,
)
from gda.core.enums.sources import SourceRecordCategory
from gda.db.exceptions import EntityMappingError
from gda.db.mapper.base import BaseRowMapper
from gda.db.mapper.vital_cemetery import (
    _base_source_columns,
    _date_sort,
    _date_year,
    _hydrate_from_payload,
    _opt_val,
)
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import (
    DraftRecordID,
    IndividualID,
    LocationID,
    MediaID,
    RepositoryID,
    ServiceRecordID,
    SourceID,
    TranscriptID,
)
from gda.model.atom.urn import ArchivalURN, MilitaryDraftUrn, SourceURN
from gda.model.atom.year import HistoricalYear
from gda.model.base.association import AssociatedIndividual
from gda.model.base.audit import AuditStamp
from gda.model.base.source import SourceRecord
from gda.model.base.tombstone import Tombstone
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
    WwiiPhysicalMetrics,
    WwiPhysicalDescription,
)

__version__ = "1.0.0+build.6"

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

_MILITARY_ENUM_MAP: dict[str, type[Enum]] = {
    "AwardScope": AwardScope,
    "BountyLandAct": BountyLandAct,
    "CasualtyCategory": CasualtyCategory,
    "CivilWarConscriptionAllegiance": CivilWarConscriptionAllegiance,
    "CivilWarEnrollmentClass": CivilWarEnrollmentClass,
    "ColonialMilitiaClass": ColonialMilitiaClass,
    "ColonialWarPeriod": ColonialWarPeriod,
    "DraftCardTier": DraftCardTier,
    "IntermentCemeteryType": IntermentCemeteryType,
    "MilitaryAwardTier": MilitaryAwardTier,
    "MilitaryBranch": MilitaryBranch,
    "ModernDraftEra": ModernDraftEra,
    "MusterRollType": MusterRollType,
    "PensionClaimantRole": PensionClaimantRole,
    "PensionPaymentAuthority": PensionPaymentAuthority,
    "PowCampType": PowCampType,
    "SeparationCharacter": SeparationCharacter,
    "SeparationFormType": SeparationFormType,
    "ServiceComponent": ServiceComponent,
    "SourceRecordCategory": SourceRecordCategory,
    "SssClassification": SssClassification,
    "WwiCitizenshipStatus": WwiCitizenshipStatus,
    "WwiiDraftWave": WwiiDraftWave,
}

_MILITARY_ATOM_MAP: dict[str, type[Any]] = {
    "DraftRecordID": DraftRecordID,
    "IndividualID": IndividualID,
    "LocationID": LocationID,
    "RepositoryID": RepositoryID,
    "ServiceRecordID": ServiceRecordID,
    "SourceID": SourceID,
    "TranscriptID": TranscriptID,
}

_MILITARY_NESTED_MAP: dict[str, type[Any]] = {
    "WwiPhysicalDescription": WwiPhysicalDescription,
    "WwiiPhysicalMetrics": WwiiPhysicalMetrics,
}


def _opt_year(val: Any) -> int | None:
    """Extract optional integer year from a HistoricalYear or None."""
    if val is None:
        return None
    return int(val.value)


def _serialize_field(val: Any) -> Any:
    """Convert a military dataclass field value into a JSON-serializable primitive."""
    if hasattr(val, "value"):
        return val.value
    if val is None or isinstance(val, (bool, int, float, str)):
        return val
    if dataclasses.is_dataclass(val) and not isinstance(val, type):
        return {f.name: _serialize_field(getattr(val, f.name)) for f in dataclasses.fields(val)}
    return val


def serialize_military_record(entity: SourceRecord) -> dict[str, Any]:
    """Serialize any Military SourceRecord subclass and all its dataclass fields."""
    data = entity.to_dict()
    base_keys = set(data.keys())
    for f in dataclasses.fields(entity):
        if f.name not in base_keys:
            data[f.name] = _serialize_field(getattr(entity, f.name))
    data["record_class"] = type(entity).__name__
    return data


def _coerce_military_field(type_str: str, raw: Any) -> Any:
    """Coerce a JSON-deserialized primitive into the target Military field type."""
    if raw is None:
        return None
    clean = type_str.replace(" | None", "").replace("Optional[", "").rstrip("]").strip()
    if clean in _MILITARY_ATOM_MAP:
        atom_cls = _MILITARY_ATOM_MAP[clean]
        return raw if isinstance(raw, atom_cls) else atom_cls(str(raw))
    if clean == "HistoricalYear":
        return raw if isinstance(raw, HistoricalYear) else HistoricalYear(int(raw))
    if clean in _MILITARY_ENUM_MAP:
        enum_cls = _MILITARY_ENUM_MAP[clean]
        return raw if isinstance(raw, enum_cls) else enum_cls(str(raw))
    if clean in _MILITARY_NESTED_MAP:
        return _MILITARY_NESTED_MAP[clean](**raw)
    return raw


def deserialize_military_record[TModel: SourceRecord](
    target_cls: type[TModel],
    data: dict[str, Any],
) -> TModel:
    """Hydrate a concrete Military SourceRecord subclass from a serialized dictionary."""
    urn_str = str(data["source_urn"])
    urn_obj: ArchivalURN = (
        MilitaryDraftUrn(urn_str) if urn_str.startswith("URN:DRAFT:") else SourceURN(urn_str)
    )
    audit_raw = data["audit"]
    audit_obj = AuditStamp(
        created_at=IsoTimestamp(audit_raw["created_at"]),
        updated_at=IsoTimestamp(audit_raw["updated_at"]),
    )
    tomb_raw = data.get("tombstone")
    tomb_obj: Tombstone[SourceID] | None = None
    if isinstance(tomb_raw, dict):
        sup = tomb_raw.get("superseded_by")
        tomb_obj = Tombstone[SourceID](
            is_deprecated=bool(tomb_raw.get("is_deprecated", False)),
            deprecated_at=(
                IsoTimestamp(tomb_raw["deprecated_at"]) if tomb_raw.get("deprecated_at") else None
            ),
            superseded_by=SourceID(str(sup)) if sup else None,
        )

    kwargs: dict[str, Any] = {
        "source_id": SourceID(str(data["source_id"])),
        "source_urn": urn_obj,
        "record_category": SourceRecordCategory(str(data["record_category"])),
        "description": str(data["description"]),
        "repository_id": RepositoryID(str(data["repository_id"])),
        "audit": audit_obj,
        "media_ids": [MediaID(str(m)) for m in data.get("media_ids", [])],
        "associated_people": [
            AssociatedIndividual.from_dict(p) for p in data.get("associated_people", [])
        ],
        "tombstone": tomb_obj,
    }
    base_keys = set(kwargs.keys())
    for f in dataclasses.fields(target_cls):
        if f.name not in base_keys:
            kwargs[f.name] = _coerce_military_field(
                str(f.type),
                data.get(f.name),
            )
    return target_cls(**kwargs)


def _military_base_columns(entity: SourceRecord) -> dict[str, Any]:
    """Build base SQLite columns for a Military record with full payload_json."""
    row = _base_source_columns(entity)
    row["payload_json"] = json.dumps(
        serialize_military_record(entity),
        sort_keys=True,
    )
    return row


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
        return deserialize_military_record(target_cls, payload)
    except EntityMappingError:
        raise
    except Exception as err:
        raise EntityMappingError(f"Failed to hydrate {domain_label} from row: {err}") from err


def _hydrate_single_military_record[TModel: SourceRecord](
    row: sqlite3.Row | dict[str, Any],
    model_cls: type[TModel],
) -> TModel:
    """Hydrate a non-polymorphic military record from its row payload_json."""
    try:
        data = dict(row)
        raw_json = data.get("payload_json")
        if not raw_json or not isinstance(raw_json, str):
            raise EntityMappingError(f"Missing or invalid 'payload_json' for {model_cls.__name__}.")
        payload = json.loads(raw_json)
        return deserialize_military_record(model_cls, payload)
    except EntityMappingError:
        raise
    except Exception as err:
        raise EntityMappingError(f"Failed to hydrate {model_cls.__name__} from row: {err}") from err


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
            row = _military_base_columns(entity)
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
            row = _military_base_columns(entity)
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
            row = _military_base_columns(entity)
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
            row = _military_base_columns(entity)
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
        return _hydrate_single_military_record(row, BountyLandWarrantRecord)


class MilitaryCasualtyRecordMapper(BaseRowMapper[MilitaryCasualtyRecord]):
    """Polymorphic SQLite row mapper for MilitaryCasualtyRecord and subclasses."""

    def __init__(self) -> None:
        """Initialize MilitaryCasualtyRecordMapper."""
        super().__init__(MilitaryCasualtyRecord)

    def to_row(self, entity: MilitaryCasualtyRecord) -> dict[str, Any]:
        """Serialize MilitaryCasualtyRecord into military_casualty_records columns."""
        try:
            row = _military_base_columns(entity)
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
            row = _military_base_columns(entity)
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
        return _hydrate_single_military_record(row, MilitaryAwardRecord)
