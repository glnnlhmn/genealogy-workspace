"""Path: tests/test_gda/test_model/test_source/test_cemetery/test_cemetery_registry.py

Comprehensive unit tests for gda.model.source.cemetery.registry
(CemeteryRegistryRecord, CemeteryPlotEntry, and RegistryInterment).

Operational Role:
    Exercises RegistryInterment, CemeteryPlotEntry, and CemeteryRegistryRecord
    creation, plot lookup, duplicate plot_locator enforcement, flatten_interments()
    tabular projection, dict/JSON round-trip serialization, and defensive
    deserialization boundaries.
"""

from __future__ import annotations

import pytest

from gda.core.enums.core import AssociatedRole
from gda.core.enums.site import MarkerCondition
from gda.core.enums.sources import SourceRecordCategory, SourceRecordType
from gda.core.errors import ModelFormatError
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import IndividualID, LocationID, MediaID, RepositoryID, SiteID, SourceID
from gda.model.atom.urn import CemeteryPlotUrn
from gda.model.base.association import AssociatedIndividual
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate
from gda.model.base.tombstone import Tombstone
from gda.model.source.cemetery import (
    CemeteryPlotEntry,
    CemeteryRegistryRecord,
    RegistryInterment,
)

__version__ = "1.0.0+build.3"

_SID = "11111111-1111-4111-8111-111111111111"
_SID_2 = "22222222-2222-4222-8222-222222222222"
_MARKER_SID = "44444444-4444-4444-8444-444444444444"
_MID = "33333333-3333-4333-8333-333333333333"
_URN = "URN:CEM:BLOSSOM_HILL_NH:SEXTON_LEDGER_VOL_1"
_URN_MIN = "URN:SRC:1925:US_NH_CONCORD:OLD_NORTH_SURVEY"
_MARKER_URN = "URN:CEM:BLOSSOM_HILL_NH:SEC_B_LOT_142"


@pytest.mark.unit
@pytest.mark.smoke
def test_registry_plot_and_interment_roundtrip() -> None:
    """Verify RegistryInterment, CemeteryPlotEntry, and CemeteryRegistryRecord round-trip."""
    now = IsoTimestamp("2026-07-02T10:00:00Z")
    audit = AuditStamp(created_at=now, updated_at=now)
    survey = EventDate.create("1925-06-18")
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

    i1 = RegistryInterment.create(
        inscribed_name="  John H. Abbott  ",
        individual_id="IND-000001",
        birth_year=1867,
        death_year=1942,
        age_inscribed="75y 9m 9d",
        relationship_text="Lot Owner",
    )
    i2 = RegistryInterment.create(
        inscribed_name="Mary E. Colby",
        birth_year=1870,
        death_year=1948,
    )
    i3 = RegistryInterment.create(
        inscribed_name="George W. Abbott",
    )

    assert i1.inscribed_name == "John H. Abbott"
    assert str(i1) == "John H. Abbott"
    assert RegistryInterment.from_json(i1.to_json()) == i1

    i3_dict = i3.to_dict()
    for opt_key in (
        "individual_id",
        "birth_year",
        "death_year",
        "age_inscribed",
        "relationship_text",
    ):
        assert opt_key not in i3_dict
    assert RegistryInterment.from_dict(i3_dict) == i3

    plot1 = CemeteryPlotEntry.create(
        plot_locator="  Sec B, Lot 142  ",
        interments=[i1, i2],
        marker_urn=CemeteryPlotUrn(_MARKER_URN),
        marker_source_id=_MARKER_SID,
        condition="Sound",
    )
    plot2 = CemeteryPlotEntry.create(
        plot_locator="Sec A, Lot 18",
        interments=[i3],
        marker_urn="URN:SRC:1925:US_NH_CONCORD:PLOT_A18",
    )

    assert plot1.plot_locator == "Sec B, Lot 142"
    assert str(plot1) == "Plot Sec B, Lot 142 (2 interments)"
    assert CemeteryPlotEntry.from_json(plot1.to_json()) == plot1

    plot2_clean = CemeteryPlotEntry.create(plot_locator="Sec A, Lot 18", interments=[i3])
    plot2_dict = plot2_clean.to_dict()
    for opt_key in ("marker_urn", "marker_source_id", "condition"):
        assert opt_key not in plot2_dict
    assert CemeteryPlotEntry.from_dict(plot2_dict) == plot2_clean

    reg = CemeteryRegistryRecord.create(
        source_id=_SID,
        source_urn=_URN,
        description="Blossom Hill Cemetery Sexton Plot Ledger Volume 1.",
        repository_id="REP-000001",
        cemetery_site_id="SID-000001",
        cemetery_name_raw="  Blossom Hill Cemetery  ",
        plots=[plot1, plot2],
        record_type="register_entry",
        location_id="LOC-000001",
        sexton_or_custodian="Arthur W. Colby, Superintendent",
        survey_date=survey,
        audit=audit,
        media_ids=[_MID],
        associated_people=[assoc],
        tombstone=tomb,
    )

    assert reg.cemetery_name_raw == "Blossom Hill Cemetery"
    assert reg.cemetery_site_id == SiteID("SID-000001")
    assert reg.location_id == LocationID("LOC-000001")
    assert reg.plot_count == 2
    assert reg.total_interment_count == 3
    assert reg.get_plot("Sec B, Lot 142") == plot1
    assert reg.get_plot("Missing Lot") is None
    assert str(reg) == "CemeteryRegistryRecord [Blossom Hill Cemetery] (2 plots, 3 interments)"

    flat = reg.flatten_interments()
    assert len(flat) == 3
    assert flat[0]["plot_locator"] == "Sec B, Lot 142"
    assert flat[0]["inscribed_name"] == "John H. Abbott"
    assert flat[2]["plot_locator"] == "Sec A, Lot 18"
    assert flat[2]["inscribed_name"] == "George W. Abbott"

    payload = reg.to_dict()
    restored = CemeteryRegistryRecord.from_dict(payload)
    assert restored == reg

    restored_json = CemeteryRegistryRecord.from_json(reg.to_json())
    assert restored_json == reg

    # Direct AuditStamp, EventDate, MarkerCondition, and CemeteryPlotEntry instances
    direct_payload = dict(payload)
    direct_payload["audit"] = audit
    direct_payload["survey_date"] = survey
    direct_payload["plots"] = [
        CemeteryPlotEntry.create(
            plot_locator="Sec B, Lot 142",
            interments=[i1, i2],
            condition=MarkerCondition.WEATHERED,
        ),
        plot2,
    ]
    restored_direct = CemeteryRegistryRecord.from_dict(direct_payload)
    assert restored_direct.plots[0].condition is MarkerCondition.WEATHERED


@pytest.mark.unit
@pytest.mark.integrity
def test_registry_validation_and_minimal_roundtrip() -> None:
    """Verify CemeteryRegistryRecord minimal round-trip and validation error branches."""
    minimal = CemeteryRegistryRecord.create(
        source_id=SourceID(_SID),
        source_urn=_URN_MIN,
        description="Old North Cemetery Gravestone Survey.",
        repository_id=RepositoryID("REP-000001"),
        cemetery_site_id=SiteID("SID-000002"),
        cemetery_name_raw="Old North Cemetery",
        plots=[
            {"plot_locator": "Row 1, Grave 4", "interments": [{"inscribed_name": "Hannah Kimball"}]}
        ],
        media_ids=[MediaID(_MID)],
    )
    min_dict = minimal.to_dict()
    for opt_key in ("location_id", "sexton_or_custodian", "survey_date"):
        assert opt_key not in min_dict
    assert CemeteryRegistryRecord.from_dict(min_dict) == minimal

    # Direct constructor trims cemetery_name_raw and validates non-empty plots
    direct = CemeteryRegistryRecord(
        source_id=SourceID(_SID),
        source_urn=minimal.source_urn,
        description="Direct trim test",
        repository_id=RepositoryID("REP-000001"),
        audit=minimal.audit,
        cemetery_site_id=SiteID("SID-000002"),
        cemetery_name_raw="  Trimmed Registry Cemetery  ",
        plots=minimal.plots,
    )
    assert direct.cemetery_name_raw == "Trimmed Registry Cemetery"

    with pytest.raises(ModelFormatError, match="requires at least one CemeteryPlotEntry"):
        CemeteryRegistryRecord(
            source_id=SourceID(_SID),
            source_urn=minimal.source_urn,
            description="Empty plots",
            repository_id=RepositoryID("REP-000001"),
            audit=minimal.audit,
            cemetery_site_id=SiteID("SID-000002"),
            cemetery_name_raw="Old North Cemetery",
            plots=(),
        )

    # RegistryInterment error branches
    with pytest.raises(ModelFormatError, match="inscribed_name"):
        RegistryInterment.create(inscribed_name="   ")

    with pytest.raises(ModelFormatError, match="must be a dictionary"):
        RegistryInterment.from_dict("bad")  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="requires 'inscribed_name'"):
        RegistryInterment.from_dict({})

    with pytest.raises(ModelFormatError, match="Failed to parse RegistryInterment JSON"):
        RegistryInterment.from_json("{bad-json")

    # CemeteryPlotEntry error branches
    with pytest.raises(ModelFormatError, match="plot_locator"):
        CemeteryPlotEntry.create(
            plot_locator="   ",
            interments=[{"inscribed_name": "Hannah Kimball"}],
        )

    with pytest.raises(ModelFormatError, match="requires at least one RegistryInterment"):
        CemeteryPlotEntry(plot_locator="Row 1", interments=())

    with pytest.raises(ModelFormatError, match="Invalid MarkerCondition value"):
        CemeteryPlotEntry.create(
            plot_locator="Row 1",
            interments=[{"inscribed_name": "Hannah Kimball"}],
            condition="DESTROYED",
        )

    with pytest.raises(ModelFormatError, match="must be a dictionary"):
        CemeteryPlotEntry.from_dict("bad")  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="requires 'plot_locator' and 'interments'"):
        CemeteryPlotEntry.from_dict({"plot_locator": "Row 1"})

    with pytest.raises(ModelFormatError, match="'interments' must be a list or tuple"):
        CemeteryPlotEntry.from_dict({"plot_locator": "Row 1", "interments": "bad"})

    with pytest.raises(ModelFormatError, match="Failed to parse CemeteryPlotEntry JSON"):
        CemeteryPlotEntry.from_json("{bad-json")

    # CemeteryRegistryRecord validation branches
    with pytest.raises(ModelFormatError, match="requires record_category CEMETERY"):
        CemeteryRegistryRecord(
            source_id=SourceID(_SID),
            source_urn=minimal.source_urn,
            record_category=SourceRecordCategory.VITAL,
            description="Wrong category",
            repository_id=RepositoryID("REP-000001"),
            audit=minimal.audit,
            cemetery_site_id=SiteID("SID-000002"),
            cemetery_name_raw="Old North Cemetery",
            plots=minimal.plots,
        )

    with pytest.raises(ModelFormatError, match="requires record_type in"):
        CemeteryRegistryRecord.create(
            source_id=_SID,
            source_urn=_URN_MIN,
            description="Wrong type",
            repository_id="REP-000001",
            cemetery_site_id="SID-000002",
            cemetery_name_raw="Old North Cemetery",
            plots=minimal.plots,
            record_type=SourceRecordType.BIRTH_CERTIFICATE,
        )

    with pytest.raises(ModelFormatError, match="cemetery_name_raw"):
        CemeteryRegistryRecord.create(
            source_id=_SID,
            source_urn=_URN_MIN,
            description="Empty cemetery",
            repository_id="REP-000001",
            cemetery_site_id="SID-000002",
            cemetery_name_raw="   ",
            plots=minimal.plots,
        )

    with pytest.raises(ModelFormatError, match="Duplicate CemeteryPlotEntry plot_locator"):
        CemeteryRegistryRecord.create(
            source_id=_SID,
            source_urn=_URN_MIN,
            description="Duplicate plots",
            repository_id="REP-000001",
            cemetery_site_id="SID-000002",
            cemetery_name_raw="Old North Cemetery",
            plots=[
                {"plot_locator": "Lot 1", "interments": [{"inscribed_name": "Person A"}]},
                {"plot_locator": "Lot 1", "interments": [{"inscribed_name": "Person B"}]},
            ],
        )

    with pytest.raises(ModelFormatError, match="Invalid 'survey_date' payload"):
        CemeteryRegistryRecord.create(
            source_id=_SID,
            source_urn=_URN_MIN,
            description="Bad date",
            repository_id="REP-000001",
            cemetery_site_id="SID-000002",
            cemetery_name_raw="Old North Cemetery",
            plots=minimal.plots,
            survey_date=1925,  # type: ignore[arg-type]
        )

    # from_dict error branches
    with pytest.raises(ModelFormatError, match="must be a dictionary"):
        CemeteryRegistryRecord.from_dict("bad")  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="requires source_id"):
        CemeteryRegistryRecord.from_dict({"source_id": _SID})

    wrong_cat = dict(min_dict)
    wrong_cat["record_category"] = "LEGAL"
    with pytest.raises(ModelFormatError, match="requires record_category CEMETERY"):
        CemeteryRegistryRecord.from_dict(wrong_cat)

    bad_plots = dict(min_dict)
    bad_plots["plots"] = "not-a-list"
    with pytest.raises(ModelFormatError, match="'plots' must be a list or tuple"):
        CemeteryRegistryRecord.from_dict(bad_plots)

    bad_audit = dict(min_dict)
    bad_audit["audit"] = 999
    with pytest.raises(ModelFormatError, match="audit must be an AuditStamp or dictionary"):
        CemeteryRegistryRecord.from_dict(bad_audit)
