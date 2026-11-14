"""Path: tests/test_gda/test_model/test_other/test_miscellaneous.py

Comprehensive unit tests for gda.model.other.miscellaneous.OtherMiscellaneousRecord.

Operational Role:
    Exercises OtherMiscellaneousRecord creation, URN:OTHER and URN:SRC resolution,
    category and record_type bounds, defensive custom_fields copying, dict/JSON
    round-trip serialization, and defensive deserialization boundaries.
"""

from __future__ import annotations

import pytest

from gda.core.enums.core import AssociatedRole
from gda.core.enums.sources import SourceRecordCategory, SourceRecordType
from gda.core.errors import ModelFormatError
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import IndividualID, LocationID, MediaID, RepositoryID, SourceID
from gda.model.atom.urn import ArchivalURN
from gda.model.base.association import AssociatedIndividual
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate
from gda.model.base.tombstone import Tombstone
from gda.model.other import OtherMiscellaneousRecord

__version__ = "1.0.0+build.1"

_SID = "11111111-1111-4111-8111-111111111111"
_SID_2 = "22222222-2222-4222-8222-222222222222"
_MID = "33333333-3333-4333-8333-333333333333"
_URN_OTHER = "URN:OTHER:1884:US_NH_CONCORD:MASONIC_DUES_RECEIPT_19"
_URN_SRC = "URN:SRC:1891:US_NH_CONCORD:TIN_TYPE_PORTRAIT_04"


@pytest.mark.unit
@pytest.mark.smoke
def test_other_miscellaneous_record_roundtrip() -> None:
    """Verify OtherMiscellaneousRecord full metadata, custom_fields isolation, and serialization."""
    now = IsoTimestamp("2026-11-04T10:00:00Z")
    audit = AuditStamp(created_at=now, updated_at=now)
    item_dt = EventDate.create("1884-11-10")
    tomb = Tombstone[SourceID](
        is_deprecated=True,
        deprecated_at=now,
        superseded_by=SourceID(_SID_2),
    )
    assoc = AssociatedIndividual(
        individual_id=IndividualID("IND-000001"),
        name_raw="George W. Abbott",
        role=AssociatedRole.PRIMARY,
    )
    raw_custom = {"dues_paid": "$2.50", "lodge_number": "No. 11"}

    rec = OtherMiscellaneousRecord.create(
        source_id=_SID,
        source_urn=_URN_OTHER,
        description="Blazing Star Lodge No. 11 Annual Dues Receipt for George W. Abbott.",
        repository_id="REP-000001",
        item_date=item_dt,
        record_category="fraternal",
        record_type="receipt",
        organization_or_entity_name="Blazing Star Lodge No. 11, F. & A. M.",
        organization_location_id="LOC-000001",
        custom_fields=raw_custom,
        item_note="Printed receipt signed by Lodge Secretary.",
        audit=audit,
        media_ids=[_MID],
        associated_people=[assoc],
        tombstone=tomb,
    )

    # Mutating caller dict does not mutate record state
    raw_custom["dues_paid"] = "$999.00"
    assert rec.custom_fields["dues_paid"] == "$2.50"
    assert rec.organization_location_id == LocationID("LOC-000001")
    assert (
        str(rec)
        == "OtherMiscellaneousRecord [RECEIPT] Blazing Star Lodge No. 11 Annual Dues Receipt for George W. Abbott."
    )

    payload = rec.to_dict()
    assert payload["custom_fields"]["lodge_number"] == "No. 11"

    restored = OtherMiscellaneousRecord.from_dict(payload)
    assert restored == rec

    restored_json = OtherMiscellaneousRecord.from_json(rec.to_json())
    assert restored_json == rec

    # Direct ArchivalURN, AuditStamp, and EventDate instances
    direct_urn_rec = OtherMiscellaneousRecord.create(
        source_id=_SID,
        source_urn=ArchivalURN(_URN_OTHER),
        description="Direct ArchivalURN instance check.",
        repository_id="REP-000001",
        item_date=item_dt,
    )
    assert direct_urn_rec.source_urn == ArchivalURN(_URN_OTHER)

    direct_payload = dict(payload)
    direct_payload["audit"] = audit
    direct_payload["item_date"] = item_dt
    assert OtherMiscellaneousRecord.from_dict(direct_payload) == rec


@pytest.mark.unit
@pytest.mark.integrity
def test_other_miscellaneous_validation_and_minimal_roundtrip() -> None:
    """Verify OtherMiscellaneousRecord minimal round-trip and validation error branches."""
    minimal = OtherMiscellaneousRecord.create(
        source_id=SourceID(_SID),
        source_urn=_URN_SRC,
        description="Tintype studio portrait of Mary E. Abbott.",
        repository_id=RepositoryID("REP-000001"),
        item_date="1891-06-01",
        record_category=SourceRecordCategory.EPHEMERA,
        record_type=SourceRecordType.PHOTO,
        media_ids=[MediaID(_MID)],
    )
    min_dict = minimal.to_dict()
    for opt_key in (
        "organization_or_entity_name",
        "organization_location_id",
        "item_note",
    ):
        assert opt_key not in min_dict
    assert min_dict["custom_fields"] == {}
    assert OtherMiscellaneousRecord.from_dict(min_dict) == minimal

    # Validation branches
    with pytest.raises(ModelFormatError, match="Invalid Other URN syntax"):
        OtherMiscellaneousRecord.create(
            source_id=_SID,
            source_urn="URN:OTHER:bad",
            description="Bad URN",
            repository_id="REP-000001",
            item_date="1891-06-01",
        )

    with pytest.raises(ModelFormatError, match="requires record_category in"):
        OtherMiscellaneousRecord.create(
            source_id=_SID,
            source_urn=_URN_SRC,
            description="Wrong category",
            repository_id="REP-000001",
            item_date="1891-06-01",
            record_category=SourceRecordCategory.CENSUS,
        )

    with pytest.raises(ModelFormatError, match="requires record_type in"):
        OtherMiscellaneousRecord.create(
            source_id=_SID,
            source_urn=_URN_SRC,
            description="Wrong type",
            repository_id="REP-000001",
            item_date="1891-06-01",
            record_type=SourceRecordType.BIRTH_CERTIFICATE,
        )

    with pytest.raises(ModelFormatError, match="Invalid 'item_date' payload"):
        OtherMiscellaneousRecord.create(
            source_id=_SID,
            source_urn=_URN_SRC,
            description="Bad date",
            repository_id="REP-000001",
            item_date=1891,  # type: ignore[arg-type]
        )

    # from_dict error branches
    with pytest.raises(ModelFormatError, match="must be a dictionary"):
        OtherMiscellaneousRecord.from_dict("bad")  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="requires source_id"):
        OtherMiscellaneousRecord.from_dict({"source_id": _SID})

    bad_custom = dict(min_dict)
    bad_custom["custom_fields"] = "not-a-dict"
    with pytest.raises(ModelFormatError, match="'custom_fields' must be a dictionary"):
        OtherMiscellaneousRecord.from_dict(bad_custom)

    bad_audit = dict(min_dict)
    bad_audit["audit"] = 123
    with pytest.raises(ModelFormatError, match="audit must be an AuditStamp or dictionary"):
        OtherMiscellaneousRecord.from_dict(bad_audit)
