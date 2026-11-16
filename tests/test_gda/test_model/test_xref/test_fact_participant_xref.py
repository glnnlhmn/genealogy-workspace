"""Path: tests/test_gda/test_model/test_xref/test_fact_participant_xref.py

Comprehensive unit tests for gda.model.xref.fact_participant_xref.FactParticipantXRef.

Operational Role:
    Exercises FactParticipantXRef creation, HistoricalYear integration,
    optional LocationID and SiteID anchors, dynamic xref_key and sort_key
    properties, FactParticipantXRef.from_fact() derivation, dict/JSON
    round-trip serialization, and defensive validation boundaries.
"""

from __future__ import annotations

import pytest
from tests.test_gda.test_model.test_xref.conftest import assert_xref_contract

from gda.core.enums.core import AssociatedRole, FactType
from gda.core.errors import ModelFormatError, ModelPrefixMismatchError, ModelRangeError
from gda.model.atom.id import FactID, FamilyID, IndividualID, LocationID, SiteID
from gda.model.atom.year import HistoricalYear
from gda.model.entity.fact import Fact, FactParticipant
from gda.model.xref import FactParticipantXRef

__version__ = "1.0.0+build.3"


@pytest.mark.unit
@pytest.mark.smoke
def test_fact_participant_xref_roundtrip_and_ordering(
    sample_fact_id: FactID,
    sample_individual_id: IndividualID,
    sample_location_id: LocationID,
    sample_site_id: SiteID,
    sample_year: HistoricalYear,
) -> None:
    """Verify FactParticipantXRef creation, dynamic keys, ordering, and round-trip serialization."""
    xref = FactParticipantXRef.create(
        fact_id="  fid-000104  ",
        individual_id="  ind-000010  ",
        fact_type="  marriage  ",
        role="  witness  ",
        temporal_year=1878,
        location_id="  loc-000001  ",
        site_id="  sid-000005  ",
    )

    assert_xref_contract(xref, FactParticipantXRef)
    assert xref.fact_id == sample_fact_id
    assert xref.individual_id == sample_individual_id
    assert xref.role is AssociatedRole.WITNESS
    assert xref.fact_type is FactType.MARRIAGE
    assert xref.is_primary_subject is False
    assert xref.temporal_year == sample_year
    assert xref.temporal_year == 1878
    assert xref.location_id == sample_location_id
    assert xref.site_id == sample_site_id
    assert xref.xref_key == "FID-000104::IND-000010::WITNESS"
    assert xref.sort_key == ("IND-000010", 1878, "MARRIAGE", "FID-000104", "WITNESS")
    assert str(xref) == "FactParticipantXRef [FID-000104::IND-000010::WITNESS] (MARRIAGE)"
    assert "FactParticipantXRef(" in repr(xref)

    # Direct atom/enum instances & total ordering comparison
    earlier = FactParticipantXRef.create(
        fact_id=FactID("FID-000001"),
        individual_id=sample_individual_id,
        fact_type=FactType.BIRTH,
        role=AssociatedRole.PRIMARY,
        is_primary_subject=True,
        temporal_year=HistoricalYear(1850),
        location_id=sample_location_id,
        site_id=SiteID("SID-000001"),
    )
    undated = FactParticipantXRef.create(
        fact_id="FID-000200",
        individual_id="IND-000010",
        fact_type=FactType.RESIDENCE,
    )

    assert earlier < xref < undated


@pytest.mark.unit
@pytest.mark.integrity
def test_fact_participant_xref_from_fact_derivation(
    sample_individual_fact: Fact,
) -> None:
    """Verify FactParticipantXRef.from_fact() for individual facts and family facts."""
    rows = FactParticipantXRef.from_fact(sample_individual_fact)
    assert len(rows) == 3
    assert rows[0].individual_id == IndividualID("IND-000001")
    assert rows[0].role is AssociatedRole.PRIMARY
    assert rows[0].is_primary_subject is True
    assert rows[0].temporal_year == HistoricalYear(1844)
    assert rows[0].location_id == LocationID("LOC-000001")
    assert rows[0].site_id == SiteID("SID-000002")

    assert rows[1].individual_id == IndividualID("IND-000002")
    assert rows[1].role is AssociatedRole.INFORMANT
    assert rows[1].is_primary_subject is False

    assert rows[2].individual_id == IndividualID("IND-000003")
    assert rows[2].role is AssociatedRole.WITNESS
    assert rows[2].is_primary_subject is False

    # Family-anchored Fact with spouse projection and duplicate guard
    fam_fact = Fact.create(
        fact_id="FID-000020",
        canonical_urn="urn:gda:fact:abbott_marriage_1868",
        fact_type=FactType.MARRIAGE,
        title="Marriage of George W. Abbott and Mary E. Rolfe",
        primary_subject_id=FamilyID("FAM-000001"),
        participants=[
            FactParticipant.create("IND-000010", AssociatedRole.OFFICIANT),
            FactParticipant.create("IND-000001", AssociatedRole.PRIMARY),
        ],
    )
    fam_rows = FactParticipantXRef.from_fact(
        fam_fact,
        family_spouse_ids=(
            IndividualID("IND-000001"),
            IndividualID("IND-000002"),
            IndividualID("IND-000001"),
        ),
    )
    assert len(fam_rows) == 3
    assert fam_rows[0].individual_id == IndividualID("IND-000001")
    assert fam_rows[0].is_primary_subject is True
    assert fam_rows[0].temporal_year is None
    assert fam_rows[1].individual_id == IndividualID("IND-000002")
    assert fam_rows[1].is_primary_subject is True
    assert fam_rows[2].individual_id == IndividualID("IND-000010")
    assert fam_rows[2].role is AssociatedRole.OFFICIANT
    assert fam_rows[2].is_primary_subject is False

    with pytest.raises(ModelFormatError, match="requires a Fact entity instance"):
        FactParticipantXRef.from_fact("not-a-fact")  # type: ignore[arg-type]


@pytest.mark.unit
@pytest.mark.integrity
def test_fact_participant_xref_minimal_and_validation_errors() -> None:
    """Verify minimal FactParticipantXRef round-trip and validation error branches."""
    minimal = FactParticipantXRef.create(
        fact_id="FID-000099",
        individual_id="IND-000099",
        fact_type=FactType.CENSUS,
    )
    min_dict = minimal.to_dict()
    for opt_key in ("temporal_year", "location_id", "site_id"):
        assert opt_key not in min_dict
    assert FactParticipantXRef.from_dict(min_dict) == minimal

    with pytest.raises(ModelPrefixMismatchError, match="expected 'FID'"):
        FactParticipantXRef.create(
            fact_id="FCT-000001",
            individual_id="IND-000001",
            fact_type=FactType.BIRTH,
        )

    with pytest.raises(ModelPrefixMismatchError, match="expected 'IND'"):
        FactParticipantXRef.create(
            fact_id="FID-000001",
            individual_id="ORG-000001",
            fact_type=FactType.BIRTH,
        )

    with pytest.raises(ModelPrefixMismatchError, match="expected 'LOC'"):
        FactParticipantXRef.create(
            fact_id="FID-000001",
            individual_id="IND-000001",
            fact_type=FactType.BIRTH,
            location_id="SID-000001",
        )

    with pytest.raises(ModelPrefixMismatchError, match="expected 'SID'"):
        FactParticipantXRef.create(
            fact_id="FID-000001",
            individual_id="IND-000001",
            fact_type=FactType.BIRTH,
            site_id="LOC-000001",
        )

    with pytest.raises(ModelFormatError, match="Invalid AssociatedRole value"):
        FactParticipantXRef.create(
            fact_id="FID-000001",
            individual_id="IND-000001",
            fact_type=FactType.BIRTH,
            role="INVALID_ROLE",
        )

    with pytest.raises(ModelFormatError, match="Invalid FactType value"):
        FactParticipantXRef.create(
            fact_id="FID-000001",
            individual_id="IND-000001",
            fact_type="INVALID_FACT",
        )

    with pytest.raises(ModelRangeError):
        FactParticipantXRef.create(
            fact_id="FID-000001",
            individual_id="IND-000001",
            fact_type=FactType.BIRTH,
            temporal_year=999,
        )

    with pytest.raises(ModelFormatError, match="requires 'fact_id'"):
        FactParticipantXRef.from_dict({"fact_id": "FID-000001"})
