"""Path: tests/test_gda/test_model/test_source/test_cemetery/test_cemetery_marker.py

Comprehensive unit tests for gda.model.source.cemetery.marker
(CemeteryMarkerRecord and MarkerInterment).

Operational Role:
    Exercises MarkerInterment and CemeteryMarkerRecord creation, CemeteryPlotUrn
    and SourceURN coercion, MarkerType/MarkerMaterial/MarkerCondition enum parsing,
    flatten_interments() tabular projection, dict/JSON round-trip serialization,
    and defensive deserialization boundaries.
"""

from __future__ import annotations

import pytest

from gda.core.enums.core import AssociatedRole
from gda.core.enums.site import MarkerCondition, MarkerMaterial, MarkerType
from gda.core.enums.sources import SourceRecordCategory, SourceRecordType
from gda.core.errors import ModelFormatError
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import IndividualID, LocationID, MediaID, RepositoryID, SiteID, SourceID
from gda.model.atom.urn import CemeteryPlotUrn
from gda.model.base.age import Age
from gda.model.base.association import AssociatedIndividual
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate
from gda.model.base.tombstone import Tombstone
from gda.model.source.cemetery import CemeteryMarkerRecord, MarkerInterment

__version__ = "1.0.0+build.3"

_SID = "11111111-1111-4111-8111-111111111111"
_SID_2 = "22222222-2222-4222-8222-222222222222"
_MID = "33333333-3333-4333-8333-333333333333"
_URN = "URN:CEM:BLOSSOM_HILL_NH:SEC_B_LOT_142"
_URN_MIN = "URN:SRC:1945:US_NH_CONCORD:CEM_MARKER_09"


@pytest.mark.unit
@pytest.mark.smoke
def test_marker_interment_and_record_roundtrip() -> None:
    """Verify MarkerInterment and CemeteryMarkerRecord full metadata and serialization."""
    now = IsoTimestamp("2026-07-01T10:00:00Z")
    audit = AuditStamp(created_at=now, updated_at=now)
    dob = EventDate.create("1867-02-10")
    dod = EventDate.create("1942-11-19")
    survey = EventDate.create("2025-09-14")
    tomb = Tombstone[SourceID](
        is_deprecated=True,
        deprecated_at=now,
        superseded_by=SourceID(_SID_2),
    )
    assoc = AssociatedIndividual(
        individual_id=IndividualID("IND-000001"),
        name_raw="John H. Abbott",
        role=AssociatedRole.DECEASED,
    )

    m1 = MarkerInterment.create(
        inscribed_name="  John H. Abbott  ",
        individual_id="IND-000001",
        birth_date=dob,
        death_date=dod,
        age_at_death=Age(raw_text="75 yrs 9 mos", years=75, months=9, days=9),
        relationship_inscribed="Husband of Mary E. Colby",
    )
    m2 = MarkerInterment.create(
        inscribed_name="Mary E. Colby",
        age_at_death=78,
    )
    m3 = MarkerInterment.create(
        inscribed_name="Infant Abbott",
        age_at_death="2 days",
    )

    assert m1.inscribed_name == "John H. Abbott"
    assert str(m1) == "John H. Abbott"
    assert MarkerInterment.from_json(m1.to_json()) == m1
    assert m2.to_dict()["age_at_death"] == {"years": 78}
    assert m3.to_dict()["age_at_death"] == {"raw_text": "2 days"}

    rec = CemeteryMarkerRecord.create(
        source_id=_SID,
        source_urn=CemeteryPlotUrn(_URN),
        description="Abbott Family Granite Obelisk at Blossom Hill Cemetery.",
        repository_id="REP-000001",
        cemetery_name_raw="  Blossom Hill Cemetery  ",
        interments=[m1, m2],
        record_type="family_monument",
        cemetery_site_id="SID-000001",
        location_id="LOC-000001",
        plot_location="Section B, Lot 142",
        findagrave_id="10482910",
        billiongraves_id="4491021",
        cemetery_grave_id="BH-B-142",
        marker_type="Obelisk",
        material="GRANITE",
        carver="Cummings Bros., Concord, NH",
        physical_condition="Broken/Repaired",
        inscription_verbatim="ABBOTT / John H. Abbott 1867-1942 / Mary E. Colby His Wife",
        survey_date=survey,
        audit=audit,
        media_ids=[_MID],
        associated_people=[assoc],
        tombstone=tomb,
    )

    assert rec.cemetery_name_raw == "Blossom Hill Cemetery"
    assert rec.cemetery_site_id == SiteID("SID-000001")
    assert rec.location_id == LocationID("LOC-000001")
    assert rec.marker_type is MarkerType.OBELISK
    assert rec.material is MarkerMaterial.GRANITE
    assert rec.physical_condition is MarkerCondition.BROKEN_REPAIRED
    assert rec.interment_count == 2
    assert str(rec) == "CemeteryMarkerRecord [John H. Abbott (+1)] @ Blossom Hill Cemetery"

    flat = rec.flatten_interments()
    assert len(flat) == 2
    assert flat[0]["inscribed_name"] == "John H. Abbott"
    assert flat[0]["marker_type"] == "Obelisk"
    assert flat[1]["inscribed_name"] == "Mary E. Colby"

    payload = rec.to_dict()
    assert payload["marker_type"] == "Obelisk"
    assert payload["material"] == "Granite"
    assert payload["physical_condition"] == "Broken/Repaired"

    restored = CemeteryMarkerRecord.from_dict(payload)
    assert restored == rec

    restored_json = CemeteryMarkerRecord.from_json(rec.to_json())
    assert restored_json == rec

    # Direct enum instances, AuditStamp, EventDate, and MarkerInterment objects
    direct_payload = dict(payload)
    direct_payload["audit"] = audit
    direct_payload["survey_date"] = survey
    direct_payload["marker_type"] = MarkerType.OBELISK
    direct_payload["material"] = MarkerMaterial.GRANITE
    direct_payload["physical_condition"] = MarkerCondition.SOUND
    direct_payload["interments"] = [m1, m2]
    restored_direct = CemeteryMarkerRecord.from_dict(direct_payload)
    assert restored_direct.physical_condition is MarkerCondition.SOUND


@pytest.mark.unit
@pytest.mark.integrity
def test_marker_validation_and_minimal_roundtrip() -> None:
    """Verify CemeteryMarkerRecord minimal round-trip and validation error branches."""
    minimal = CemeteryMarkerRecord.create(
        source_id=SourceID(_SID),
        source_urn=_URN_MIN,
        description="Single headstone in Old North Cemetery.",
        repository_id=RepositoryID("REP-000001"),
        cemetery_name_raw="Old North Cemetery",
        interments=[{"inscribed_name": "George W. Abbott"}],
        media_ids=[MediaID(_MID)],
    )
    assert str(minimal) == "CemeteryMarkerRecord [George W. Abbott] @ Old North Cemetery"
    assert minimal.flatten_interments()[0]["marker_type"] is None

    min_dict = minimal.to_dict()
    for opt_key in (
        "cemetery_site_id",
        "location_id",
        "plot_location",
        "findagrave_id",
        "billiongraves_id",
        "cemetery_grave_id",
        "marker_type",
        "material",
        "carver",
        "physical_condition",
        "inscription_verbatim",
        "survey_date",
    ):
        assert opt_key not in min_dict
    assert CemeteryMarkerRecord.from_dict(min_dict) == minimal

    # Direct constructor trims cemetery_name_raw and validates empty interments
    direct = CemeteryMarkerRecord(
        source_id=SourceID(_SID),
        source_urn=minimal.source_urn,
        description="Direct trim test",
        repository_id=RepositoryID("REP-000001"),
        audit=minimal.audit,
        cemetery_name_raw="  Trimmed Cemetery  ",
        interments=(MarkerInterment.create(inscribed_name="Hannah Kimball"),),
    )
    assert direct.cemetery_name_raw == "Trimmed Cemetery"

    with pytest.raises(ModelFormatError, match="requires at least one MarkerInterment"):
        CemeteryMarkerRecord(
            source_id=SourceID(_SID),
            source_urn=minimal.source_urn,
            description="Empty interments",
            repository_id=RepositoryID("REP-000001"),
            audit=minimal.audit,
            cemetery_name_raw="Old North Cemetery",
            interments=(),
        )

    # MarkerInterment error branches
    with pytest.raises(ModelFormatError, match="inscribed_name"):
        MarkerInterment.create(inscribed_name="   ")

    with pytest.raises(ModelFormatError, match="Invalid 'birth_date' payload"):
        MarkerInterment.create(inscribed_name="Test", birth_date=1867)  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="Invalid 'age_at_death' payload"):
        MarkerInterment.create(inscribed_name="Test", age_at_death=True)  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="must be a dictionary"):
        MarkerInterment.from_dict("bad")  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="requires 'inscribed_name'"):
        MarkerInterment.from_dict({})

    with pytest.raises(ModelFormatError, match="Failed to parse MarkerInterment JSON"):
        MarkerInterment.from_json("{bad-json")

    # CemeteryMarkerRecord validation branches
    with pytest.raises(ModelFormatError, match="requires record_category CEMETERY"):
        CemeteryMarkerRecord(
            source_id=SourceID(_SID),
            source_urn=minimal.source_urn,
            record_category=SourceRecordCategory.VITAL,
            description="Wrong category",
            repository_id=RepositoryID("REP-000001"),
            audit=minimal.audit,
            cemetery_name_raw="Old North Cemetery",
            interments=(MarkerInterment.create(inscribed_name="Hannah Kimball"),),
        )

    with pytest.raises(ModelFormatError, match="requires record_type in"):
        CemeteryMarkerRecord.create(
            source_id=_SID,
            source_urn=_URN_MIN,
            description="Wrong type",
            repository_id="REP-000001",
            cemetery_name_raw="Old North Cemetery",
            interments=[{"inscribed_name": "Hannah Kimball"}],
            record_type=SourceRecordType.BIRTH_CERTIFICATE,
        )

    with pytest.raises(ModelFormatError, match="cemetery_name_raw"):
        CemeteryMarkerRecord.create(
            source_id=_SID,
            source_urn=_URN_MIN,
            description="Empty cemetery",
            repository_id="REP-000001",
            cemetery_name_raw="   ",
            interments=[{"inscribed_name": "Hannah Kimball"}],
        )

    with pytest.raises(ModelFormatError, match="Invalid marker_type value"):
        CemeteryMarkerRecord.create(
            source_id=_SID,
            source_urn=_URN_MIN,
            description="Bad marker_type",
            repository_id="REP-000001",
            cemetery_name_raw="Old North Cemetery",
            interments=[{"inscribed_name": "Hannah Kimball"}],
            marker_type="PYRAMID",
        )

    # from_dict error branches
    with pytest.raises(ModelFormatError, match="must be a dictionary"):
        CemeteryMarkerRecord.from_dict("bad")  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="requires source_id"):
        CemeteryMarkerRecord.from_dict({"source_id": _SID})

    wrong_cat = dict(min_dict)
    wrong_cat["record_category"] = "LEGAL"
    with pytest.raises(ModelFormatError, match="requires record_category CEMETERY"):
        CemeteryMarkerRecord.from_dict(wrong_cat)

    bad_interments = dict(min_dict)
    bad_interments["interments"] = "not-a-list"
    with pytest.raises(ModelFormatError, match="'interments' must be a list or tuple"):
        CemeteryMarkerRecord.from_dict(bad_interments)

    bad_audit = dict(min_dict)
    bad_audit["audit"] = "bad"
    with pytest.raises(ModelFormatError, match="audit must be an AuditStamp or dictionary"):
        CemeteryMarkerRecord.from_dict(bad_audit)
