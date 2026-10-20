"""Path: tests/test_gda/test_model/test_military/casualty/test_casualty_base.py

Atomized behavioral test suite for MilitaryCasualtyRecord domain entity.

Operational Role:
    Verifies base military casualty report instantiation, string sanitization,
    source category enforcement, and representation contracts.

Test Structure & Protocol:
    - Atomized tests: 1:1 behavioral contract verification.
    - Fully decorated: Pytest marker taxonomy (@pytest.mark.unit, @pytest.mark.smoke, @pytest.mark.regression).
    - Synthetic baselines: Pure in-memory fixtures with isolated basetemp execution.
"""

from __future__ import annotations

import pytest

from gda.core.errors import ModelFormatError
from gda.enums.sources import SourceRecordCategory
from gda.model.atom.date import HistoricalYear, IsoTimestamp
from gda.model.atom.id import (
    IndividualID,
    LocationID,
    RepositoryID,
    SourceID,
    TranscriptID,
)
from gda.model.atom.urn import SourceURN
from gda.model.base.audit import AuditStamp
from gda.model.military.casualty import CasualtyCategory
from gda.model.military.casualty.base import MilitaryCasualtyRecord
from gda.model.military.service import MilitaryBranch

__version__ = "1.0.0+build.1"


# ==============================================================================
# FIXTURES
# ==============================================================================


@pytest.fixture
def valid_audit() -> AuditStamp:
    """Return synthetic in-memory AuditStamp."""
    timestamp = IsoTimestamp("2026-01-01T00:00:00Z")
    return AuditStamp(created_at=timestamp, updated_at=timestamp)


@pytest.fixture
def valid_casualty_urn() -> SourceURN:
    """Return synthetic SourceURN."""
    return SourceURN("URN:SRC:1944:WD_AGO:CAS_REP_104")


@pytest.fixture
def valid_repo_id() -> RepositoryID:
    """Return synthetic RepositoryID."""
    return RepositoryID("REP-000001")


@pytest.fixture
def valid_source_id() -> SourceID:
    """Return synthetic SourceID."""
    return SourceID("c9a646d3-9c61-4a70-8b14-c48c8b417c8d")


# ==============================================================================
# GROUP 1: SMOKE & GOLDEN PATH
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_military_casualty_smoke_valid_initialization(
    valid_source_id: SourceID,
    valid_casualty_urn: SourceURN,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify minimal valid instantiation of MilitaryCasualtyRecord."""
    rec = MilitaryCasualtyRecord(
        source_id=valid_source_id,
        source_urn=valid_casualty_urn,
        record_category=SourceRecordCategory.MILITARY,
        description="WWII Army Casualty Telegram",
        repository_id=valid_repo_id,
        audit=valid_audit,
        servicemember_id=IndividualID("IND-000001"),
        servicemember_name_raw="Glenn D. Lehman",
        branch=MilitaryBranch.ARMY,
        casualty_category=CasualtyCategory.WOUNDED_IN_ACTION,
        casualty_year=HistoricalYear(1944),
        unit_designation_raw="Company C, 16th Infantry",
        rank_raw="Sergeant",
    )
    assert rec.servicemember_id == IndividualID("IND-000001")
    assert rec.servicemember_name_raw == "Glenn D. Lehman"
    assert rec.branch == MilitaryBranch.ARMY
    assert rec.casualty_category == CasualtyCategory.WOUNDED_IN_ACTION
    assert rec.casualty_year == HistoricalYear(1944)
    assert rec.unit_designation_raw == "Company C, 16th Infantry"
    assert rec.rank_raw == "Sergeant"
    assert rec.service_number_raw is None
    assert rec.casualty_location_id is None
    assert "WOUNDED_IN_ACTION" in str(rec)
    assert "Sergeant" in str(rec)


# ==============================================================================
# GROUP 2: OPTIONAL ATTRIBUTES & LOCATIONS
# ==============================================================================


@pytest.mark.unit
def test_military_casualty_full_attributes(
    valid_source_id: SourceID,
    valid_casualty_urn: SourceURN,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify MilitaryCasualtyRecord correctly preserves serial numbers and locations."""
    loc_id = LocationID("LOC-000088")
    trn_id = TranscriptID("e1a646d3-9c61-4a70-8b14-c48c8b417c8f")
    rec = MilitaryCasualtyRecord(
        source_id=valid_source_id,
        source_urn=valid_casualty_urn,
        record_category=SourceRecordCategory.MILITARY,
        description="Detailed casualty notification",
        repository_id=valid_repo_id,
        audit=valid_audit,
        servicemember_id=IndividualID("IND-000001"),
        servicemember_name_raw="Glenn Lehman",
        branch=MilitaryBranch.NAVY,
        casualty_category=CasualtyCategory.KILLED_IN_ACTION,
        casualty_year=HistoricalYear(1942),
        unit_designation_raw="USS Hornet (CV-8)",
        rank_raw="Aviation Machinist's Mate 2nd Class",
        service_number_raw="312-99-01",
        theater_of_operations_raw="Pacific Theater of Operations",
        casualty_location_raw="Battle of the Santa Cruz Islands",
        casualty_location_id=loc_id,
        transcript_id=trn_id,
    )
    assert rec.service_number_raw == "312-99-01"
    assert rec.theater_of_operations_raw == "Pacific Theater of Operations"
    assert rec.casualty_location_raw == "Battle of the Santa Cruz Islands"
    assert rec.casualty_location_id == loc_id
    assert rec.transcript_id == trn_id


# ==============================================================================
# GROUP 3: BOUNDARY & ERROR CONDITIONS
# ==============================================================================


@pytest.mark.unit
@pytest.mark.regression
def test_military_casualty_invalid_category_fails(
    valid_source_id: SourceID,
    valid_casualty_urn: SourceURN,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify ModelFormatError raised if record_category is not MILITARY."""
    with pytest.raises(ModelFormatError, match="requires category 'MILITARY'"):
        MilitaryCasualtyRecord(
            source_id=valid_source_id,
            source_urn=valid_casualty_urn,
            record_category=SourceRecordCategory.CENSUS,
            description="Mismatched category",
            repository_id=valid_repo_id,
            audit=valid_audit,
            servicemember_id=IndividualID("IND-000001"),
            servicemember_name_raw="Glenn Lehman",
            branch=MilitaryBranch.ARMY,
            casualty_category=CasualtyCategory.WOUNDED_IN_ACTION,
            casualty_year=HistoricalYear(1944),
            unit_designation_raw="Company C",
            rank_raw="Private",
        )


@pytest.mark.unit
@pytest.mark.regression
def test_military_casualty_empty_required_strings_fail(
    valid_source_id: SourceID,
    valid_casualty_urn: SourceURN,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify ModelFormatError raised if required text fields are empty or whitespace."""
    with pytest.raises(
        ModelFormatError, match="servicemember_name_raw.*cannot be empty"
    ):
        MilitaryCasualtyRecord(
            source_id=valid_source_id,
            source_urn=valid_casualty_urn,
            record_category=SourceRecordCategory.MILITARY,
            description="Empty name",
            repository_id=valid_repo_id,
            audit=valid_audit,
            servicemember_id=IndividualID("IND-000001"),
            servicemember_name_raw="   ",
            branch=MilitaryBranch.ARMY,
            casualty_category=CasualtyCategory.WOUNDED_IN_ACTION,
            casualty_year=HistoricalYear(1944),
            unit_designation_raw="Company C",
            rank_raw="Private",
        )

    with pytest.raises(ModelFormatError, match="unit_designation_raw.*cannot be empty"):
        MilitaryCasualtyRecord(
            source_id=valid_source_id,
            source_urn=valid_casualty_urn,
            record_category=SourceRecordCategory.MILITARY,
            description="Empty unit",
            repository_id=valid_repo_id,
            audit=valid_audit,
            servicemember_id=IndividualID("IND-000001"),
            servicemember_name_raw="Glenn Lehman",
            branch=MilitaryBranch.ARMY,
            casualty_category=CasualtyCategory.WOUNDED_IN_ACTION,
            casualty_year=HistoricalYear(1944),
            unit_designation_raw="   ",
            rank_raw="Private",
        )

    with pytest.raises(ModelFormatError, match="rank_raw.*cannot be empty"):
        MilitaryCasualtyRecord(
            source_id=valid_source_id,
            source_urn=valid_casualty_urn,
            record_category=SourceRecordCategory.MILITARY,
            description="Empty rank",
            repository_id=valid_repo_id,
            audit=valid_audit,
            servicemember_id=IndividualID("IND-000001"),
            servicemember_name_raw="Glenn Lehman",
            branch=MilitaryBranch.ARMY,
            casualty_category=CasualtyCategory.WOUNDED_IN_ACTION,
            casualty_year=HistoricalYear(1944),
            unit_designation_raw="Company C",
            rank_raw="   ",
        )


@pytest.mark.unit
@pytest.mark.regression
def test_military_casualty_empty_optional_strings_fail(
    valid_source_id: SourceID,
    valid_casualty_urn: SourceURN,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify ModelFormatError raised if optional strings are provided as whitespace."""
    with pytest.raises(ModelFormatError, match="service_number_raw.*cannot be empty"):
        MilitaryCasualtyRecord(
            source_id=valid_source_id,
            source_urn=valid_casualty_urn,
            record_category=SourceRecordCategory.MILITARY,
            description="Empty serial",
            repository_id=valid_repo_id,
            audit=valid_audit,
            servicemember_id=IndividualID("IND-000001"),
            servicemember_name_raw="Glenn Lehman",
            branch=MilitaryBranch.ARMY,
            casualty_category=CasualtyCategory.WOUNDED_IN_ACTION,
            casualty_year=HistoricalYear(1944),
            unit_designation_raw="Company C",
            rank_raw="Private",
            service_number_raw="   ",
        )

    with pytest.raises(
        ModelFormatError, match="casualty_location_raw.*cannot be empty"
    ):
        MilitaryCasualtyRecord(
            source_id=valid_source_id,
            source_urn=valid_casualty_urn,
            record_category=SourceRecordCategory.MILITARY,
            description="Empty location",
            repository_id=valid_repo_id,
            audit=valid_audit,
            servicemember_id=IndividualID("IND-000001"),
            servicemember_name_raw="Glenn Lehman",
            branch=MilitaryBranch.ARMY,
            casualty_category=CasualtyCategory.WOUNDED_IN_ACTION,
            casualty_year=HistoricalYear(1944),
            unit_designation_raw="Company C",
            rank_raw="Private",
            casualty_location_raw="   ",
        )
