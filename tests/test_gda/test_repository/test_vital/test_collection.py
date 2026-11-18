"""Path: tests/test_gda/test_repository/test_vital/test_collection.py

Unit and integration tests for Vital domain collections
(src/gda/repository/vital/collection.py).
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

from gda.core.enums.core import Sex
from gda.core.enums.sources import SourceRecordType
from gda.core.enums.vital import (
    BirthPlurality,
    DispositionType,
    DivorceDecreeType,
    MannerOfDeath,
    MaritalStatus,
    UnionType,
)
from gda.db.session import DatabaseSessionManager
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import IndividualID, LocationID, RepositoryID, SourceID
from gda.model.atom.urn import SourceURN
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate
from gda.model.source.vital.baptism import BaptismRecord
from gda.model.source.vital.birth import BirthRecord
from gda.model.source.vital.death import DeathRecord
from gda.model.source.vital.divorce import DivorceRecord
from gda.model.source.vital.marriage import MarriageRecord
from gda.repository.vital.collection import (
    BaptismCollection,
    BirthCollection,
    DeathCollection,
    DivorceCollection,
    MarriageCollection,
)


def _audit() -> AuditStamp:
    ts = IsoTimestamp("2026-01-01T00:00:00Z")
    return AuditStamp(created_at=ts, updated_at=ts)


def test_vital_collections_indexing_and_roundtrip(
    seeded_session: DatabaseSessionManager,
    tmp_path: Path,
) -> None:
    """Verify secondary index buckets, editing, and JSON round-tripping across all 5 Vital collections."""
    # 1. BaptismCollection
    bap_coll = BaptismCollection.from_database(seeded_session)
    bap = BaptismRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000101"),
        source_urn=SourceURN("URN:SRC:1852:US_PA:BAP101"),
        record_type=SourceRecordType.BAPTISM_CERTIFICATE,
        description="Baptism",
        repository_id=RepositoryID("REP-000001"),
        audit=_audit(),
        church_name_raw="Zion",
        baptized_name_raw="John Lehman",
        date_of_baptism=EventDate.from_dict("1852-04-12"),
        individual_id=IndividualID("IND-000001"),
        location_id=LocationID("LOC-000001"),
    )
    bap_coll.add(bap)
    assert len(bap_coll.find_by_individual("IND-000001")) == 1
    assert len(bap_coll.find_by_location("LOC-000001")) == 1
    bap_coll.edit(bap.source_id, individual_id=None, location_id=None)
    assert len(bap_coll.find_by_individual("IND-000001")) == 0
    bap_coll.edit(bap.source_id, description="Baptism None Branch")
    bap_coll.add(
        dataclasses.replace(
            bap,
            source_id=SourceID("00000000-0000-4000-8000-000000000301"),
            source_urn=SourceURN("URN:SRC:1852:US_PA:BAP301"),
            individual_id=None,
            location_id=None,
        )
    )
    p_bap = tmp_path / "bap.json"
    bap_coll.export_file(p_bap)
    BaptismCollection().import_file(p_bap)

    # 2. BirthCollection
    bir_coll = BirthCollection.from_database(seeded_session)
    bir = BirthRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000100"),
        source_urn=SourceURN("URN:SRC:1852:US_PA:BIR100"),
        record_type=SourceRecordType.BIRTH_CERTIFICATE,
        description="Birth",
        repository_id=RepositoryID("REP-000001"),
        audit=_audit(),
        child_name_raw="John Lehman",
        date_of_birth=EventDate.from_dict("1852-01-03"),
        place_of_birth_raw="Carlisle",
        child_id=IndividualID("IND-000001"),
        place_of_birth_id=LocationID("LOC-000001"),
        sex=Sex.MALE,
        plurality=BirthPlurality.SINGLE,
        is_stillborn=False,
    )
    bir_coll.add(bir)
    assert len(bir_coll.find_by_child("IND-000001")) == 1
    assert len(bir_coll.find_by_location("LOC-000001")) == 1
    bir_coll.edit(bir.source_id, child_id=None, place_of_birth_id=None)
    assert len(bir_coll.find_by_child("IND-000001")) == 0
    bir_coll.edit(bir.source_id, description="Birth None Branch")
    bir_coll.add(
        dataclasses.replace(
            bir,
            source_id=SourceID("00000000-0000-4000-8000-000000000300"),
            source_urn=SourceURN("URN:SRC:1852:US_PA:BIR300"),
            child_id=None,
            place_of_birth_id=None,
        )
    )
    p_bir = tmp_path / "bir.json"
    bir_coll.export_file(p_bir)
    BirthCollection().import_file(p_bir)

    # 3. DeathCollection
    dea_coll = DeathCollection.from_database(seeded_session)
    dea = DeathRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000102"),
        source_urn=SourceURN("URN:SRC:1922:US_PA:DEA102"),
        record_type=SourceRecordType.DEATH_CERTIFICATE,
        description="Death",
        repository_id=RepositoryID("REP-000001"),
        audit=_audit(),
        decedent_name_raw="John Lehman",
        date_of_death=EventDate.from_dict("1922-11-08"),
        place_of_death_raw="Carlisle",
        decedent_id=IndividualID("IND-000001"),
        place_of_death_id=LocationID("LOC-000001"),
        sex=Sex.MALE,
        is_stillborn=False,
        marital_status=MaritalStatus.MARRIED,
        manner_of_death=MannerOfDeath.NATURAL,
        disposition_type=DispositionType.BURIAL,
    )
    dea_coll.add(dea)
    assert len(dea_coll.find_by_decedent("IND-000001")) == 1
    assert len(dea_coll.find_by_location("LOC-000001")) == 1
    dea_coll.edit(dea.source_id, decedent_id=None, place_of_death_id=None)
    assert len(dea_coll.find_by_decedent("IND-000001")) == 0
    dea_coll.edit(dea.source_id, description="Death None Branch")
    dea_coll.add(
        dataclasses.replace(
            dea,
            source_id=SourceID("00000000-0000-4000-8000-000000000302"),
            source_urn=SourceURN("URN:SRC:1922:US_PA:DEA302"),
            decedent_id=None,
            place_of_death_id=None,
        )
    )
    p_dea = tmp_path / "dea.json"
    dea_coll.export_file(p_dea)
    DeathCollection().import_file(p_dea)

    # 4. DivorceCollection
    div_coll = DivorceCollection.from_database(seeded_session)
    div = DivorceRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000103"),
        source_urn=SourceURN("URN:SRC:1895:US_PA:DIV103"),
        record_type=SourceRecordType.DIVORCE_DECREE,
        description="Divorce",
        repository_id=RepositoryID("REP-000001"),
        audit=_audit(),
        court_name="Court",
        husband_name_raw="John Lehman",
        wife_name_raw="Mary Miller",
        date_decree_granted=EventDate.from_dict("1895-06-15"),
        husband_id=IndividualID("IND-000001"),
        wife_id=IndividualID("IND-000002"),
        jurisdiction_id=LocationID("LOC-000001"),
        decree_type=DivorceDecreeType.ABSOLUTE,
    )
    div_coll.add(div)
    assert len(div_coll.find_by_spouse("IND-000001")) == 1
    assert len(div_coll.find_by_jurisdiction("LOC-000001")) == 1
    div_coll.edit(div.source_id, husband_id=None, wife_id=None, jurisdiction_id=None)
    assert len(div_coll.find_by_spouse("IND-000001")) == 0
    div_coll.edit(div.source_id, description="Divorce None Branch")
    div_coll.add(
        dataclasses.replace(
            div,
            source_id=SourceID("00000000-0000-4000-8000-000000000303"),
            source_urn=SourceURN("URN:SRC:1895:US_PA:DIV303"),
            husband_id=None,
            wife_id=None,
            jurisdiction_id=None,
        )
    )
    p_div = tmp_path / "div.json"
    div_coll.export_file(p_div)
    DivorceCollection().import_file(p_div)

    # 5. MarriageCollection
    mar_coll = MarriageCollection.from_database(seeded_session)
    mar = MarriageRecord(
        source_id=SourceID("00000000-0000-4000-8000-000000000104"),
        source_urn=SourceURN("URN:SRC:1875:US_PA:MAR104"),
        record_type=SourceRecordType.MARRIAGE_CERTIFICATE,
        description="Marriage",
        repository_id=RepositoryID("REP-000001"),
        audit=_audit(),
        groom_name_raw="John Lehman",
        bride_name_raw="Mary Miller",
        union_type=UnionType.MARRIED,
        groom_id=IndividualID("IND-000001"),
        bride_id=IndividualID("IND-000002"),
        place_of_marriage_id=LocationID("LOC-000001"),
    )
    mar_coll.add(mar)
    assert len(mar_coll.find_by_spouse("IND-000001")) == 1
    assert len(mar_coll.find_by_location("LOC-000001")) == 1
    mar_coll.edit(mar.source_id, groom_id=None, bride_id=None, place_of_marriage_id=None)
    assert len(mar_coll.find_by_spouse("IND-000001")) == 0
    mar_coll.edit(mar.source_id, description="Marriage None Branch")
    mar_coll.add(
        dataclasses.replace(
            mar,
            source_id=SourceID("00000000-0000-4000-8000-000000000304"),
            source_urn=SourceURN("URN:SRC:1875:US_PA:MAR304"),
            groom_id=None,
            bride_id=None,
            place_of_marriage_id=None,
        )
    )
    p_mar = tmp_path / "mar.json"
    mar_coll.export_file(p_mar)
    MarriageCollection().import_file(p_mar)
