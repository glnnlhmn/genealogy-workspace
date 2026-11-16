"""Path: tests/test_gda/test_db/test_mapper/test_personas.py

Unit and regression verification suite for IndividualRowMapper and FamilyRowMapper.

Operational Role:
    1:1 verification suite for src/gda/db/mapper/personas.py. Validates
    lossless round-trip mapping for Individual and Family entities and
    EntityMappingError boundaries.
"""

from __future__ import annotations

import pytest

import gda.db.mapper.personas as personas_mod
from gda.core.enums.date import DateModifier
from gda.core.enums.vital import PedigreeType, UnionDissolutionType, UnionType
from gda.db.exceptions import EntityMappingError
from gda.db.mapper.personas import FamilyRowMapper, IndividualRowMapper
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import FamilyID, IndividualID
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate, TimePeriod
from gda.model.base.family import ChildLink, FamilyUnion
from gda.model.base.name import NamePerson
from gda.model.base.tombstone import Tombstone
from gda.model.entity.family import Family
from gda.model.entity.individual import Individual

__version__ = "1.0.0+build.3"


def _make_audit() -> AuditStamp:
    now = IsoTimestamp("2026-01-01T00:00:00Z")
    return AuditStamp(created_at=now, updated_at=now)


@pytest.mark.unit
def test_personas_mapper_dunder_all() -> None:
    """Verify gda.db.mapper.personas.__all__ is sorted."""
    assert personas_mod.__all__ == ["FamilyRowMapper", "IndividualRowMapper"]


@pytest.mark.integration
def test_individual_row_mapper_full_and_sparse_round_trip() -> None:
    """Verify IndividualRowMapper round-trips full and minimal Individual entities."""
    audit = _make_audit()
    name_obj = NamePerson(
        raw="Dr. Abigail Quincy Smith Jr.",
        canonical="Abigail Quincy Smith",
        prefix="Dr.",
        given="Abigail",
        middle="Quincy",
        surname="Smith",
        suffix="Jr.",
        married=["Adams"],
        aliases=["Abby"],
        alt_spellings=["Smyth"],
        comment="First Lady",
    )
    ind = Individual.create(
        individual_id="IND-000001",
        canonical_urn="urn:gda:ind:smith_abigail",
        name=name_obj,
        gender="F",
        birth_date="1744-11-22",
        birth_place_id="LOC-000001",
        death_date="1818-10-28",
        death_place_id="SID-000001",
        is_deceased=True,
        audit=audit,
        tombstone=Tombstone(
            is_deprecated=True,
            deprecated_at=audit.updated_at,
            superseded_by=IndividualID("IND-000002"),
        ),
    )

    mapper = IndividualRowMapper()
    assert mapper.from_row(mapper.to_row(ind)) == ind

    b_between = EventDate.create(
        date="1850-01-01",
        modifier=DateModifier.BETWEEN,
        end_date="1850-12-31",
    )
    ind_sparse = Individual.create(
        individual_id="IND-000005",
        canonical_urn="urn:gda:ind:jane_smith_1850",
        name="Jane Smith",
        gender="F",
        birth_date=b_between,
        audit=audit,
    )
    sparse_row = mapper.to_row(ind_sparse)
    sparse_row["married_names_json"] = None
    sparse_row["aliases_json"] = None
    sparse_row["alt_spellings_json"] = None
    assert mapper.from_row(sparse_row) == ind_sparse


@pytest.mark.integration
def test_family_row_mapper_full_and_sparse_round_trip() -> None:
    """Verify FamilyRowMapper round-trips full and minimal Family entities."""
    audit = _make_audit()
    union = FamilyUnion.create(
        union_type=UnionType.MARRIED,
        dissolution_type=UnionDissolutionType.DEATH,
        period=TimePeriod(
            start_date=EventDate.create("1764-10-25"),
            end_date=EventDate.create("1818-10-28"),
        ),
    )
    fam = Family.create(
        family_id="FAM-000001",
        canonical_urn="urn:gda:fam:adams_smith",
        union=union,
        partner_ids=["IND-000001", "IND-000002"],
        children=[ChildLink.create("IND-000003", PedigreeType.BIRTH)],
        audit=audit,
        tombstone=Tombstone(
            is_deprecated=True,
            deprecated_at=audit.updated_at,
            superseded_by=FamilyID("FAM-000002"),
        ),
    )

    mapper = FamilyRowMapper()
    assert mapper.from_row(mapper.to_row(fam)) == fam

    fam_min = Family.create(
        family_id="FAM-000002",
        canonical_urn="urn:gda:fam:minimal",
        partner_ids=["IND-000001"],
        audit=audit,
    )
    min_row = mapper.to_row(fam_min)
    min_row["partner_ids_json"] = None
    min_row["children_json"] = None
    restored_min = mapper.from_row(min_row)
    assert restored_min.id == FamilyID("FAM-000002")
    assert restored_min.partner_ids == []
    assert restored_min.children == []


@pytest.mark.regression
def test_personas_mappers_corrupt_rows_raise_error() -> None:
    """Verify IndividualRowMapper and FamilyRowMapper raise EntityMappingError on invalid rows."""
    with pytest.raises(EntityMappingError, match="Failed to map row to Individual"):
        IndividualRowMapper().from_row({"id": None})

    with pytest.raises(EntityMappingError, match="Failed to map row to Family"):
        FamilyRowMapper().from_row({"id": None})
