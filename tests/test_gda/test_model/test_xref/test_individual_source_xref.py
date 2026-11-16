"""Path: tests/test_gda/test_model/test_xref/test_individual_source_xref.py

Comprehensive unit tests for gda.model.xref.individual_source_xref.IndividualSourceXRef.

Operational Role:
    Exercises IndividualSourceXRef creation, SourceRecordCategory and
    SourceRecordType resolution, HistoricalYear integration, optional LocationID
    and SiteID anchors, dynamic xref_key and sort_key ordering, dict/JSON
    round-trip serialization, and defensive validation boundaries.
"""

from __future__ import annotations

import pytest
from tests.test_gda.test_model.test_xref.conftest import (
    SAMPLE_SOURCE_UUID_1,
    SAMPLE_SOURCE_UUID_2,
    assert_xref_contract,
)

from gda.core.enums.core import AssociatedRole
from gda.core.enums.sources import SourceRecordCategory, SourceRecordType
from gda.core.errors import ModelFormatError, ModelPrefixMismatchError, ModelRangeError
from gda.model.atom.id import IndividualID, LocationID, SiteID, SourceID
from gda.model.atom.year import HistoricalYear
from gda.model.xref import IndividualSourceXRef

__version__ = "1.0.0+build.2"


@pytest.mark.unit
@pytest.mark.smoke
def test_individual_source_xref_roundtrip_and_ordering(
    sample_source_id: SourceID,
    sample_individual_id: IndividualID,
    sample_location_id: LocationID,
    sample_site_id: SiteID,
    sample_year: HistoricalYear,
) -> None:
    """Verify IndividualSourceXRef creation, dynamic keys, ordering, and round-trip serialization."""
    xref = IndividualSourceXRef.create(
        source_id=f"  {SAMPLE_SOURCE_UUID_1.upper()}  ",
        individual_id="  ind-000010  ",
        record_category="  church  ",
        record_type="  baptism_register  ",
        role="  witness  ",
        temporal_year=1878,
        location_id="  loc-000001  ",
        site_id="  sid-000005  ",
    )

    assert_xref_contract(xref, IndividualSourceXRef)
    assert xref.source_id == sample_source_id
    assert xref.individual_id == sample_individual_id
    assert xref.role is AssociatedRole.WITNESS
    assert xref.record_category is SourceRecordCategory.CHURCH
    assert xref.record_type is SourceRecordType.BAPTISM_REGISTER
    assert xref.is_primary_subject is False
    assert xref.temporal_year == sample_year
    assert xref.temporal_year == 1878
    assert xref.location_id == sample_location_id
    assert xref.site_id == sample_site_id
    assert xref.xref_key == f"{SAMPLE_SOURCE_UUID_1}::IND-000010::WITNESS"
    assert xref.sort_key == (
        "IND-000010",
        1878,
        "CHURCH",
        "BAPTISM_REGISTER",
        SAMPLE_SOURCE_UUID_1,
        "WITNESS",
    )
    assert (
        str(xref)
        == f"IndividualSourceXRef [{SAMPLE_SOURCE_UUID_1}::IND-000010::WITNESS] (CHURCH/BAPTISM_REGISTER)"
    )
    assert "IndividualSourceXRef(" in repr(xref)

    # Direct atom/enum instances & total ordering comparison
    earlier = IndividualSourceXRef.create(
        source_id=sample_source_id,
        individual_id=sample_individual_id,
        record_category=SourceRecordCategory.VITAL,
        record_type=SourceRecordType.BIRTH_CERTIFICATE,
        role=AssociatedRole.PRIMARY,
        is_primary_subject=True,
        temporal_year=HistoricalYear(1850),
        location_id=sample_location_id,
        site_id=SiteID("SID-000001"),
    )
    undated = IndividualSourceXRef.create(
        source_id=SAMPLE_SOURCE_UUID_2,
        individual_id="IND-000010",
        record_category=SourceRecordCategory.PROBATE,
        record_type=SourceRecordType.LAST_WILL_AND_TESTAMENT,
    )

    assert earlier < xref < undated


@pytest.mark.unit
@pytest.mark.integrity
def test_individual_source_xref_minimal_and_validation_errors() -> None:
    """Verify minimal IndividualSourceXRef round-trip and validation error branches."""
    minimal = IndividualSourceXRef.create(
        source_id=SAMPLE_SOURCE_UUID_1,
        individual_id="IND-000099",
        record_category=SourceRecordCategory.CENSUS,
        record_type=SourceRecordType.POPULATION_SCHEDULE,
    )
    assert minimal.is_primary_subject is True
    min_dict = minimal.to_dict()
    for opt_key in ("temporal_year", "location_id", "site_id"):
        assert opt_key not in min_dict
    assert IndividualSourceXRef.from_dict(min_dict) == minimal

    with pytest.raises(ModelFormatError):
        IndividualSourceXRef.create(
            source_id="not-a-uuid",
            individual_id="IND-000001",
            record_category=SourceRecordCategory.VITAL,
            record_type=SourceRecordType.BIRTH_CERTIFICATE,
        )

    with pytest.raises(ModelPrefixMismatchError, match="expected 'IND'"):
        IndividualSourceXRef.create(
            source_id=SAMPLE_SOURCE_UUID_1,
            individual_id="FAM-000001",
            record_category=SourceRecordCategory.VITAL,
            record_type=SourceRecordType.BIRTH_CERTIFICATE,
        )

    with pytest.raises(ModelPrefixMismatchError, match="expected 'LOC'"):
        IndividualSourceXRef.create(
            source_id=SAMPLE_SOURCE_UUID_1,
            individual_id="IND-000001",
            record_category=SourceRecordCategory.VITAL,
            record_type=SourceRecordType.BIRTH_CERTIFICATE,
            location_id="SID-000001",
        )

    with pytest.raises(ModelPrefixMismatchError, match="expected 'SID'"):
        IndividualSourceXRef.create(
            source_id=SAMPLE_SOURCE_UUID_1,
            individual_id="IND-000001",
            record_category=SourceRecordCategory.VITAL,
            record_type=SourceRecordType.BIRTH_CERTIFICATE,
            site_id="LOC-000001",
        )

    with pytest.raises(ModelFormatError, match="Invalid AssociatedRole value"):
        IndividualSourceXRef.create(
            source_id=SAMPLE_SOURCE_UUID_1,
            individual_id="IND-000001",
            record_category=SourceRecordCategory.VITAL,
            record_type=SourceRecordType.BIRTH_CERTIFICATE,
            role="INVALID_ROLE",
        )

    with pytest.raises(ModelFormatError, match="Invalid SourceRecordCategory value"):
        IndividualSourceXRef.create(
            source_id=SAMPLE_SOURCE_UUID_1,
            individual_id="IND-000001",
            record_category="INVALID_CATEGORY",
            record_type=SourceRecordType.BIRTH_CERTIFICATE,
        )

    with pytest.raises(ModelFormatError, match="Invalid SourceRecordType value"):
        IndividualSourceXRef.create(
            source_id=SAMPLE_SOURCE_UUID_1,
            individual_id="IND-000001",
            record_category=SourceRecordCategory.VITAL,
            record_type="INVALID_TYPE",
        )

    with pytest.raises(ModelRangeError):
        IndividualSourceXRef.create(
            source_id=SAMPLE_SOURCE_UUID_1,
            individual_id="IND-000001",
            record_category=SourceRecordCategory.VITAL,
            record_type=SourceRecordType.BIRTH_CERTIFICATE,
            temporal_year=999,
        )

    with pytest.raises(ModelFormatError, match="requires 'source_id'"):
        IndividualSourceXRef.from_dict({"source_id": SAMPLE_SOURCE_UUID_1})
