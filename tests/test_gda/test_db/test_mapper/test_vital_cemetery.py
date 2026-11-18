"""Path: tests/test_gda/test_db/test_mapper/test_vital_cemetery.py

Unit tests for Vital and Cemetery row mappers (src/gda/db/mapper/vital_cemetery.py).
"""

from __future__ import annotations

import pytest

from gda.core.enums.core import Sex
from gda.core.enums.site import MarkerCondition, MarkerMaterial, MarkerType
from gda.core.enums.sources import SourceRecordType
from gda.core.enums.vital import (
    BirthPlurality,
    DispositionType,
    DivorceDecreeType,
    MannerOfDeath,
    MaritalStatus,
    UnionType,
)
from gda.db.exceptions import EntityMappingError
from gda.db.mapper.vital_cemetery import (
    BaptismRecordMapper,
    BirthRecordMapper,
    CemeteryMarkerRecordMapper,
    CemeteryRegistryRecordMapper,
    DeathRecordMapper,
    DivorceRecordMapper,
    MarriageRecordMapper,
    _date_sort,
    _date_year,
    _hydrate_from_payload,
    _opt_val,
)
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import (
    IndividualID,
    LocationID,
    OrganizationID,
    RepositoryID,
    SiteID,
    SourceID,
)
from gda.model.atom.urn import SourceURN
from gda.model.atom.year import HistoricalYear
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate
from gda.model.base.tombstone import Tombstone
from gda.model.source.cemetery.marker import CemeteryMarkerRecord, MarkerInterment
from gda.model.source.cemetery.registry import (
    CemeteryPlotEntry,
    CemeteryRegistryRecord,
    RegistryInterment,
)
from gda.model.source.vital.baptism import BaptismRecord
from gda.model.source.vital.birth import BirthRecord
from gda.model.source.vital.death import DeathRecord
from gda.model.source.vital.divorce import DivorceRecord
from gda.model.source.vital.marriage import MarriageRecord


def _audit() -> AuditStamp:
    ts = IsoTimestamp("2026-01-01T00:00:00Z")
    return AuditStamp(created_at=ts, updated_at=ts)


def test_vital_and_cemetery_mappers_roundtrip() -> None:
    """Verify to_row and from_row round-trip across all 7 Vital and Cemetery mappers."""
    bap_mapper = BaptismRecordMapper()
    bap = BaptismRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000001"),
        source_urn=SourceURN("URN:SRC:1852:US_PA:BAP001"),
        record_type=SourceRecordType.BAPTISM_CERTIFICATE,
        description="Baptism of John Lehman",
        repository_id=RepositoryID("REP-000001"),
        audit=_audit(),
        church_name_raw="Zion Lutheran Church",
        baptized_name_raw="Johannes Lehman",
        date_of_baptism=EventDate.from_dict("1852-04-12"),
        date_of_birth=EventDate.from_dict("1852-01-03"),
        individual_id=IndividualID("IND-000001"),
        church_org_id=OrganizationID("ORG-000001"),
        church_site_id=SiteID("SID-000001"),
        location_id=LocationID("LOC-000001"),
        sex=Sex.MALE,
        denomination="Lutheran",
        father_name_raw="Daniel Lehman",
        mother_name_raw="Elizabeth",
        sponsors_or_godparents=["Jacob Lehman"],
        tombstone=Tombstone[SourceID](
            is_deprecated=True,
            deprecated_at=IsoTimestamp("2026-02-01T00:00:00Z"),
            superseded_by=SourceID("00000000-0000-4000-8000-000000000099"),
        ),
    )
    assert bap_mapper.from_row(bap_mapper.to_row(bap)) == bap

    birth_mapper = BirthRecordMapper()
    birth = BirthRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000002"),
        source_urn=SourceURN("URN:SRC:1852:US_PA:BIR002"),
        record_type=SourceRecordType.BIRTH_CERTIFICATE,
        description="Birth Certificate of John Lehman",
        repository_id=RepositoryID("REP-000001"),
        audit=_audit(),
        child_name_raw="John Lehman",
        date_of_birth=EventDate.from_dict("1852-01-03"),
        place_of_birth_raw="Carlisle, Cumberland County, PA",
        child_id=IndividualID("IND-000001"),
        place_of_birth_id=LocationID("LOC-000001"),
        sex=Sex.MALE,
        plurality=BirthPlurality.SINGLE,
        is_stillborn=False,
        certificate_number="BC-1852-001",
    )
    assert birth_mapper.from_row(birth_mapper.to_row(birth)) == birth

    death_mapper = DeathRecordMapper()
    death = DeathRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000003"),
        source_urn=SourceURN("URN:SRC:1922:US_PA:DEA003"),
        record_type=SourceRecordType.DEATH_CERTIFICATE,
        description="Death Certificate of John Lehman",
        repository_id=RepositoryID("REP-000001"),
        audit=_audit(),
        decedent_name_raw="John Lehman",
        date_of_death=EventDate.from_dict("1922-11-08"),
        place_of_death_raw="Carlisle, PA",
        decedent_id=IndividualID("IND-000001"),
        place_of_death_id=LocationID("LOC-000001"),
        disposition_site_id=SiteID("SID-000001"),
        sex=Sex.MALE,
        is_stillborn=False,
        marital_status=MaritalStatus.MARRIED,
        manner_of_death=MannerOfDeath.NATURAL,
        disposition_type=DispositionType.BURIAL,
        certificate_number="DC-1922-404",
    )
    assert death_mapper.from_row(death_mapper.to_row(death)) == death

    divorce_mapper = DivorceRecordMapper()
    divorce = DivorceRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000004"),
        source_urn=SourceURN("URN:SRC:1895:US_PA:DIV004"),
        record_type=SourceRecordType.DIVORCE_DECREE,
        description="Divorce Decree",
        repository_id=RepositoryID("REP-000001"),
        audit=_audit(),
        court_name="Cumberland County Court of Common Pleas",
        husband_name_raw="John Lehman",
        wife_name_raw="Mary Miller",
        date_decree_granted=EventDate.from_dict("1895-06-15"),
        husband_id=IndividualID("IND-000001"),
        wife_id=IndividualID("IND-000002"),
        jurisdiction_id=LocationID("LOC-000001"),
        docket_number="DKT-1895-77",
        decree_type=DivorceDecreeType.ABSOLUTE,
    )
    assert divorce_mapper.from_row(divorce_mapper.to_row(divorce)) == divorce

    marriage_mapper = MarriageRecordMapper()
    marriage = MarriageRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000005"),
        source_urn=SourceURN("URN:SRC:1875:US_PA:MAR005"),
        record_type=SourceRecordType.MARRIAGE_CERTIFICATE,
        description="Marriage of John Lehman and Mary Miller",
        repository_id=RepositoryID("REP-000001"),
        audit=_audit(),
        groom_name_raw="John Lehman",
        bride_name_raw="Mary Miller",
        union_type=UnionType.MARRIED,
        groom_id=IndividualID("IND-000001"),
        bride_id=IndividualID("IND-000002"),
        date_of_marriage=EventDate.from_dict("1875-10-20"),
        place_of_marriage_raw="Carlisle, PA",
        place_of_marriage_id=LocationID("LOC-000001"),
        license_number="ML-1875-09",
        witnesses=["Peter Lehman"],
    )
    assert marriage_mapper.from_row(marriage_mapper.to_row(marriage)) == marriage

    marker_mapper = CemeteryMarkerRecordMapper()
    marker = CemeteryMarkerRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000006"),
        source_urn=SourceURN("URN:SRC:2020:US_PA:MRK006"),
        record_type=SourceRecordType.CEMETERY_MARKER,
        description="Headstone of John Lehman",
        repository_id=RepositoryID("REP-000001"),
        audit=_audit(),
        cemetery_name_raw="Zion Lutheran Cemetery",
        cemetery_site_id=SiteID("SID-000001"),
        location_id=LocationID("LOC-000001"),
        plot_location="Sec A Lot 12",
        findagrave_id="FAG-123456",
        marker_type=MarkerType.UPRIGHT_HEADSTONE,
        material=MarkerMaterial.GRANITE,
        physical_condition=MarkerCondition.SOUND,
        survey_date=EventDate.from_dict("2020"),
        interments=(
            MarkerInterment(
                inscribed_name="John Lehman",
                individual_id=IndividualID("IND-000001"),
            ),
        ),
    )
    assert marker_mapper.from_row(marker_mapper.to_row(marker)) == marker

    registry_mapper = CemeteryRegistryRecordMapper()
    registry = CemeteryRegistryRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000007"),
        source_urn=SourceURN("URN:SRC:1930:US_PA:REG007"),
        record_type=SourceRecordType.REGISTER_ENTRY,
        description="Zion Lutheran Sexton Plot Ledger",
        repository_id=RepositoryID("REP-000001"),
        audit=_audit(),
        cemetery_site_id=SiteID("SID-000001"),
        cemetery_name_raw="Zion Lutheran Cemetery",
        location_id=LocationID("LOC-000001"),
        sexton_or_custodian="H. Schmidt",
        survey_date=EventDate.from_dict("1930-05"),
        plots=(
            CemeteryPlotEntry(
                plot_locator="Sec A Lot 12",
                marker_source_id=SourceID("00000000-0000-4000-8000-000000000006"),
                condition=MarkerCondition.SOUND,
                interments=(
                    RegistryInterment(
                        inscribed_name="John Lehman",
                        individual_id=IndividualID("IND-000001"),
                        birth_year=HistoricalYear(1852),
                        death_year=HistoricalYear(1922),
                    ),
                ),
            ),
        ),
    )
    assert registry_mapper.from_row(registry_mapper.to_row(registry)) == registry


def test_vital_cemetery_mapper_helpers_and_error_branches() -> None:
    """Verify date/value helpers and EntityMappingError handling across all 7 mappers."""
    assert _opt_val(None) is None
    assert _opt_val("plain") == "plain"
    assert _date_year(None) is None
    assert _date_sort(None) is None
    assert _date_sort(EventDate.from_dict("1880")) == "1880"

    for mapper in (
        BaptismRecordMapper(),
        BirthRecordMapper(),
        DeathRecordMapper(),
        DivorceRecordMapper(),
        MarriageRecordMapper(),
        CemeteryMarkerRecordMapper(),
        CemeteryRegistryRecordMapper(),
    ):
        with pytest.raises(EntityMappingError):
            mapper.to_row(object())  # type: ignore[arg-type]

        with pytest.raises(EntityMappingError, match="Missing or invalid 'payload_json'"):
            mapper.from_row({"id": "00000000-0000-4000-8000-000000000001", "payload_json": ""})

        with pytest.raises(EntityMappingError, match="Failed to hydrate"):
            mapper.from_row(
                {"id": "00000000-0000-4000-8000-000000000001", "payload_json": "{not-valid-json"}
            )

    with pytest.raises(EntityMappingError):
        _hydrate_from_payload({"payload_json": None}, BirthRecord)
