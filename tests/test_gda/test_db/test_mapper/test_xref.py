"""Path: tests/test_gda/test_db/test_mapper/test_xref.py

Unit tests for all 9 Cross-Reference row mappers (src/gda/db/mapper/xref.py).
"""

from __future__ import annotations

import pytest

from gda.core.enums.core import AssociatedRole, FactType
from gda.core.enums.orgs import (
    AffiliationType,
    MembershipStatus,
    OrganizationCategory,
)
from gda.core.enums.sources import SourceRecordCategory, SourceRecordType
from gda.core.enums.vital import HistoricNameType, PedigreeType
from gda.db.exceptions import EntityMappingError
from gda.db.mapper.xref import (
    FactParticipantXRefMapper,
    IndividualFamilyXRefMapper,
    IndividualOrganizationXRefMapper,
    IndividualSourceXRefMapper,
    IndividualSurnameXRefMapper,
    LocationXRefMapper,
    MediaXRefMapper,
    SiteXRefMapper,
    SurnameXRefMapper,
    _hydrate_xref,
)
from gda.model.atom.id import (
    FactID,
    FamilyID,
    IndividualID,
    LocationID,
    MediaID,
    OrganizationID,
    SiteID,
    SourceID,
)
from gda.model.atom.year import BirthYear, DeathYear, HistoricalYear
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


def test_xref_mappers_roundtrip() -> None:
    """Verify to_row and from_row round-trip across all 9 XRef mappers."""
    fp_mapper = FactParticipantXRefMapper()
    fp = FactParticipantXRef(
        fact_id=FactID("FID-000001"),
        individual_id=IndividualID("IND-000001"),
        role=AssociatedRole.PRIMARY,
        fact_type=FactType.BIRTH,
        is_primary_subject=True,
        temporal_year=HistoricalYear(1852),
        location_id=LocationID("LOC-000001"),
        site_id=SiteID("SID-000001"),
    )
    assert fp_mapper.from_row(fp_mapper.to_row(fp)) == fp

    if_mapper = IndividualFamilyXRefMapper()
    ifam = IndividualFamilyXRef(
        family_id=FamilyID("FAM-000001"),
        individual_id=IndividualID("IND-000001"),
        is_partner=False,
        pedigree=PedigreeType.BIRTH,
        child_order=1,
    )
    assert if_mapper.from_row(if_mapper.to_row(ifam)) == ifam

    io_mapper = IndividualOrganizationXRefMapper()
    iorg = IndividualOrganizationXRef(
        organization_id=OrganizationID("ORG-000001"),
        individual_id=IndividualID("IND-000001"),
        org_category=OrganizationCategory.RELIGIOUS,
        affiliation_type=AffiliationType.MEMBER,
        membership_status=MembershipStatus.ACTIVE,
        start_year=HistoricalYear(1880),
        end_year=HistoricalYear(1920),
    )
    assert io_mapper.from_row(io_mapper.to_row(iorg)) == iorg

    is_mapper = IndividualSourceXRefMapper()
    isrc = IndividualSourceXRef(
        source_id=SourceID("00000000-0000-4000-8000-000000000001"),
        individual_id=IndividualID("IND-000001"),
        role=AssociatedRole.WITNESS,
        record_category=SourceRecordCategory.CHURCH,
        record_type=SourceRecordType.BAPTISM_REGISTER,
        is_primary_subject=False,
        temporal_year=HistoricalYear(1852),
        location_id=LocationID("LOC-000001"),
        site_id=SiteID("SID-000001"),
    )
    assert is_mapper.from_row(is_mapper.to_row(isrc)) == isrc

    isur_mapper = IndividualSurnameXRefMapper()
    isur = IndividualSurnameXRef(
        surname="LEHMAN",
        individual_id=IndividualID("IND-000001"),
        is_birth_surname=True,
        birth_year=BirthYear(1852),
        death_year=DeathYear(1922),
    )
    assert isur_mapper.from_row(isur_mapper.to_row(isur)) == isur

    loc_mapper = LocationXRefMapper()
    loc_x = LocationXRef(
        location_id=LocationID("LOC-000001"),
        target_id=IndividualID("IND-000001"),
    )
    assert loc_mapper.from_row(loc_mapper.to_row(loc_x)) == loc_x

    med_mapper = MediaXRefMapper()
    med_x = MediaXRef(
        media_id=MediaID("00000000-0000-4000-8000-000000000801"),
        target_id=SourceID("00000000-0000-4000-8000-000000000001"),
    )
    assert med_mapper.from_row(med_mapper.to_row(med_x)) == med_x

    site_mapper = SiteXRefMapper()
    site_x = SiteXRef(
        site_id=SiteID("SID-000001"),
        location_id=LocationID("LOC-000001"),
        target_id=IndividualID("IND-000001"),
    )
    assert site_mapper.from_row(site_mapper.to_row(site_x)) == site_x

    sur_mapper = SurnameXRefMapper()
    sur_x = SurnameXRef(
        canonical_surname="LEHMAN",
        variant_surname="LEHMANN",
        variant_name_type=HistoricNameType.HISTORICAL,
        variant_phonetic_code="L550",
    )
    assert sur_mapper.from_row(sur_mapper.to_row(sur_x)) == sur_x


def test_xref_mappers_error_branches() -> None:
    """Verify EntityMappingError branches across all 9 XRef mappers."""
    for mapper in (
        FactParticipantXRefMapper(),
        IndividualFamilyXRefMapper(),
        IndividualOrganizationXRefMapper(),
        IndividualSourceXRefMapper(),
        IndividualSurnameXRefMapper(),
        LocationXRefMapper(),
        MediaXRefMapper(),
        SiteXRefMapper(),
        SurnameXRefMapper(),
    ):
        with pytest.raises(EntityMappingError):
            mapper.to_row(object())  # type: ignore[arg-type]

        with pytest.raises(EntityMappingError, match="Missing or invalid 'payload_json'"):
            mapper.from_row({"payload_json": ""})

        with pytest.raises(EntityMappingError, match="Failed to hydrate"):
            mapper.from_row({"payload_json": "{bad-json"})

    with pytest.raises(EntityMappingError):
        _hydrate_xref({"payload_json": None}, LocationXRef)
