"""Path: tests/test_gda/test_model/test_source/test_enumerated/taxes/test_taxes.py

Atomized behavioral test suite for TaxAssessmentRecord and SeptennialCensusRecord.

Operational Role:
    Verifies real estate, personal property, poll, occupation, and Pennsylvania
    septennial tax assessment records and dict/JSON serialization round-trips.
"""

from __future__ import annotations

import pytest

from gda.core.enums.sources import SourceRecordCategory, SourceRecordType
from gda.core.errors import ModelFormatError
from gda.model.atom.id import IndividualID, RepositoryID, SourceID
from gda.model.atom.urn import SourceURN
from gda.model.atom.year import HistoricalYear
from gda.model.base.audit import AuditStamp
from gda.model.source.enumerated.taxes import (
    AssessedProperty,
    SeptennialCensusRecord,
    TaxAssessmentRecord,
    TaxpayerClassification,
)

__version__ = "1.0.0+build.3"


@pytest.mark.unit
@pytest.mark.smoke
def test_tax_assessment_and_septennial_valid_and_roundtrip(
    valid_source_id: SourceID,
    valid_tax_urn: SourceURN,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify TaxAssessmentRecord, AssessedProperty, SeptennialCensusRecord, and JSON round-trips."""
    prop = AssessedProperty(
        acres_seated=120.5,
        acres_unseated=30.0,
        horses=3,
        cattle_or_cows=4,
        mills_distilleries_taverns="1 Gristmill",
        total_valuation_raw="$1,450",
        county_tax_amount_raw="$4.35",
        state_tax_amount_raw="$1.45",
    )
    assert "AssessedProperty(" in repr(prop)
    assert AssessedProperty.from_json(prop.to_json()) == prop

    tax_rec = TaxAssessmentRecord(
        source_id=valid_source_id,
        source_urn=valid_tax_urn,
        record_category=SourceRecordCategory.TAX,
        record_type=SourceRecordType.REAL_ESTATE_TAX,
        description="1807 Hopewell Township Tax Assessment",
        repository_id=valid_repo_id,
        audit=valid_audit,
        enumeration_year=HistoricalYear(1807),
        jurisdiction_raw="Hopewell Township, Cumberland County, PA",
        roll_locator_raw="  Page 14, Line 8  ",
        schedule_name="Seated Land",
        line_number=8,
        taxpayer_id=IndividualID("IND-000001"),
        taxpayer_name_raw="  Glenn Lehman  ",
        classification=TaxpayerClassification.FREEHOLDER,
        stated_occupation="Miller",
        assessed_property=prop,
    )
    assert tax_rec.roll_locator_raw == "Page 14, Line 8"
    assert tax_rec.taxpayer_name_raw == "Glenn Lehman"
    assert tax_rec.assessed_property is prop
    assert TaxAssessmentRecord.from_json(tax_rec.to_json()) == tax_rec

    sept_clean = SeptennialCensusRecord(
        source_id=valid_source_id,
        source_urn=valid_tax_urn,
        description="1807 Pennsylvania Septennial Census Return",
        repository_id=valid_repo_id,
        audit=valid_audit,
        enumeration_year=HistoricalYear(1807),
        jurisdiction_raw="Hopewell Township, Cumberland County, PA",
        roll_locator_raw="Page 14",
        taxpayer_name_raw="Glenn Lehman",
        stated_occupation="Miller",
    )
    assert sept_clean.record_category == SourceRecordCategory.CENSUS_EQUIVALENT
    assert sept_clean.record_type == SourceRecordType.SEPTENNIAL_CENSUS
    assert SeptennialCensusRecord.from_json(sept_clean.to_json()) == sept_clean


@pytest.mark.unit
@pytest.mark.regression
def test_tax_assessment_validation_and_serialization_failures(
    valid_source_id: SourceID,
    valid_tax_urn: SourceURN,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify ModelFormatError raised on invalid category, record_type, year, blank text, and bad JSON."""
    with pytest.raises(ModelFormatError, match="AssessedProperty payload must be a dictionary"):
        AssessedProperty.from_dict("bad")  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="Failed to parse AssessedProperty JSON"):
        AssessedProperty.from_json("{bad")

    with pytest.raises(ModelFormatError, match="requires record_category in"):
        TaxAssessmentRecord(
            source_id=valid_source_id,
            source_urn=valid_tax_urn,
            record_category=SourceRecordCategory.MILITARY,
            description="Invalid category",
            repository_id=valid_repo_id,
            audit=valid_audit,
            enumeration_year=HistoricalYear(1807),
            jurisdiction_raw="Hopewell Twp, PA",
            roll_locator_raw="P. 14",
            taxpayer_name_raw="Glenn Lehman",
        )

    with pytest.raises(ModelFormatError, match="requires record_type in"):
        TaxAssessmentRecord(
            source_id=valid_source_id,
            source_urn=valid_tax_urn,
            record_category=SourceRecordCategory.TAX,
            record_type=SourceRecordType.POPULATION_SCHEDULE,
            description="Invalid record_type",
            repository_id=valid_repo_id,
            audit=valid_audit,
            enumeration_year=HistoricalYear(1807),
            jurisdiction_raw="Hopewell Twp, PA",
            roll_locator_raw="P. 14",
            taxpayer_name_raw="Glenn Lehman",
        )

    with pytest.raises(ModelFormatError, match="enumeration_year must be 1600 or later"):
        TaxAssessmentRecord(
            source_id=valid_source_id,
            source_urn=valid_tax_urn,
            record_category=SourceRecordCategory.TAX,
            description="Year before 1600",
            repository_id=valid_repo_id,
            audit=valid_audit,
            enumeration_year=HistoricalYear(1599),
            jurisdiction_raw="Hopewell Twp, PA",
            roll_locator_raw="P. 14",
            taxpayer_name_raw="Glenn Lehman",
        )

    with pytest.raises(ModelFormatError, match="'roll_locator_raw' cannot be empty"):
        TaxAssessmentRecord(
            source_id=valid_source_id,
            source_urn=valid_tax_urn,
            record_category=SourceRecordCategory.TAX,
            description="Blank locator",
            repository_id=valid_repo_id,
            audit=valid_audit,
            enumeration_year=HistoricalYear(1807),
            jurisdiction_raw="Hopewell Twp, PA",
            roll_locator_raw="   ",
            taxpayer_name_raw="Glenn Lehman",
        )

    with pytest.raises(ModelFormatError, match="'taxpayer_name_raw' cannot be empty"):
        TaxAssessmentRecord(
            source_id=valid_source_id,
            source_urn=valid_tax_urn,
            record_category=SourceRecordCategory.TAX,
            description="Blank taxpayer",
            repository_id=valid_repo_id,
            audit=valid_audit,
            enumeration_year=HistoricalYear(1807),
            jurisdiction_raw="Hopewell Twp, PA",
            roll_locator_raw="P. 14",
            taxpayer_name_raw="   ",
        )
