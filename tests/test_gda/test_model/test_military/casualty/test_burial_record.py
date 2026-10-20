"""Path: tests/test_gda/test_model/test_military/casualty/test_burial_record.py

Atomized behavioral test suite for MilitaryBurialRecord domain entity.

Operational Role:
    Verifies military cemetery burials, national cemeteries, ABMC sites,
    plot/section assignments, and interment chronological coherence.

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
from gda.model.atom.id import IndividualID, LocationID, RepositoryID, SourceID
from gda.model.atom.urn import SourceURN
from gda.model.base.audit import AuditStamp
from gda.model.military.casualty import (
    CasualtyCategory,
    IntermentCemeteryType,
    MilitaryBurialRecord,
)
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
    return SourceURN("URN:SRC:1945:VA:NAT_CEM_BURIAL_102")


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
def test_military_burial_smoke_valid_initialization(
    valid_source_id: SourceID,
    valid_casualty_urn: SourceURN,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify minimal valid instantiation of MilitaryBurialRecord."""
    rec = MilitaryBurialRecord(
        source_id=valid_source_id,
        source_urn=valid_casualty_urn,
        record_category=SourceRecordCategory.MILITARY,
        description="National Cemetery Burial Entry",
        repository_id=valid_repo_id,
        audit=valid_audit,
        servicemember_id=IndividualID("IND-000001"),
        servicemember_name_raw="Glenn D. Lehman",
        branch=MilitaryBranch.ARMY,
        casualty_category=CasualtyCategory.KILLED_IN_ACTION,
        casualty_year=HistoricalYear(1944),
        unit_designation_raw="Company C, 16th Infantry",
        rank_raw="Corporal",
        cemetery_type=IntermentCemeteryType.NATIONAL_CEMETERY,
        cemetery_name_raw="Arlington National Cemetery",
        interment_year=HistoricalYear(1948),
    )
    assert rec.cemetery_type == IntermentCemeteryType.NATIONAL_CEMETERY
    assert rec.cemetery_name_raw == "Arlington National Cemetery"
    assert rec.interment_year == HistoricalYear(1948)
    assert rec.plot_section_raw is None
    assert rec.headstone_type_raw is None


# ==============================================================================
# GROUP 2: PLOTS, HEADSTONES & LOCATIONS
# ==============================================================================


@pytest.mark.unit
def test_military_burial_full_attributes(
    valid_source_id: SourceID,
    valid_casualty_urn: SourceURN,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify MilitaryBurialRecord preserves plot, headstone, and location identifiers."""
    loc_id = LocationID("LOC-000112")
    rec = MilitaryBurialRecord(
        source_id=valid_source_id,
        source_urn=valid_casualty_urn,
        record_category=SourceRecordCategory.MILITARY,
        description="ABMC Overseas Military Cemetery Register",
        repository_id=valid_repo_id,
        audit=valid_audit,
        servicemember_id=IndividualID("IND-000001"),
        servicemember_name_raw="Glenn Lehman",
        branch=MilitaryBranch.ARMY,
        casualty_category=CasualtyCategory.KILLED_IN_ACTION,
        casualty_year=HistoricalYear(1944),
        unit_designation_raw="116th Infantry Regiment, 29th Division",
        rank_raw="Sergeant",
        cemetery_type=IntermentCemeteryType.ABMC_OVERSEAS,
        cemetery_name_raw="Normandy American Cemetery",
        interment_year=HistoricalYear(1944),
        plot_section_raw="Plot D, Row 12, Grave 28",
        headstone_type_raw="Latin Cross (White Marble)",
        cemetery_location_id=loc_id,
    )
    assert rec.plot_section_raw == "Plot D, Row 12, Grave 28"
    assert rec.headstone_type_raw == "Latin Cross (White Marble)"
    assert rec.cemetery_location_id == loc_id


# ==============================================================================
# GROUP 3: BOUNDARY & VALIDATION REJECTIONS
# ==============================================================================


@pytest.mark.unit
@pytest.mark.regression
def test_military_burial_non_deceased_category_fails(
    valid_source_id: SourceID,
    valid_casualty_urn: SourceURN,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify ModelFormatError raised if casualty_category represents living servicemember."""
    with pytest.raises(ModelFormatError, match="requires deceased casualty_category"):
        MilitaryBurialRecord(
            source_id=valid_source_id,
            source_urn=valid_casualty_urn,
            record_category=SourceRecordCategory.MILITARY,
            description="Living wounded soldier burial attempt",
            repository_id=valid_repo_id,
            audit=valid_audit,
            servicemember_id=IndividualID("IND-000001"),
            servicemember_name_raw="Glenn Lehman",
            branch=MilitaryBranch.ARMY,
            casualty_category=CasualtyCategory.WOUNDED_IN_ACTION,
            casualty_year=HistoricalYear(1944),
            unit_designation_raw="Co. C",
            rank_raw="Private",
            cemetery_type=IntermentCemeteryType.NATIONAL_CEMETERY,
            cemetery_name_raw="Arlington",
            interment_year=HistoricalYear(1948),
        )


@pytest.mark.unit
@pytest.mark.regression
def test_military_burial_interment_precedes_casualty_fails(
    valid_source_id: SourceID,
    valid_casualty_urn: SourceURN,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify ModelFormatError raised if interment_year precedes casualty_year."""
    with pytest.raises(ModelFormatError, match="cannot precede casualty_year"):
        MilitaryBurialRecord(
            source_id=valid_source_id,
            source_urn=valid_casualty_urn,
            record_category=SourceRecordCategory.MILITARY,
            description="Inverted burial year",
            repository_id=valid_repo_id,
            audit=valid_audit,
            servicemember_id=IndividualID("IND-000001"),
            servicemember_name_raw="Glenn Lehman",
            branch=MilitaryBranch.ARMY,
            casualty_category=CasualtyCategory.KILLED_IN_ACTION,
            casualty_year=HistoricalYear(1944),
            unit_designation_raw="Co. C",
            rank_raw="Private",
            cemetery_type=IntermentCemeteryType.NATIONAL_CEMETERY,
            cemetery_name_raw="Arlington",
            interment_year=HistoricalYear(1943),
        )


@pytest.mark.unit
@pytest.mark.regression
def test_military_burial_empty_strings_fail(
    valid_source_id: SourceID,
    valid_casualty_urn: SourceURN,
    valid_repo_id: RepositoryID,
    valid_audit: AuditStamp,
) -> None:
    """Verify ModelFormatError raised if cemetery_name_raw or plot_section_raw is whitespace."""
    with pytest.raises(ModelFormatError, match="cemetery_name_raw.*cannot be empty"):
        MilitaryBurialRecord(
            source_id=valid_source_id,
            source_urn=valid_casualty_urn,
            record_category=SourceRecordCategory.MILITARY,
            description="Empty cemetery name",
            repository_id=valid_repo_id,
            audit=valid_audit,
            servicemember_id=IndividualID("IND-000001"),
            servicemember_name_raw="Glenn Lehman",
            branch=MilitaryBranch.ARMY,
            casualty_category=CasualtyCategory.KILLED_IN_ACTION,
            casualty_year=HistoricalYear(1944),
            unit_designation_raw="Co. C",
            rank_raw="Private",
            cemetery_type=IntermentCemeteryType.NATIONAL_CEMETERY,
            cemetery_name_raw="   ",
            interment_year=HistoricalYear(1944),
        )

    with pytest.raises(ModelFormatError, match="plot_section_raw.*cannot be empty"):
        MilitaryBurialRecord(
            source_id=valid_source_id,
            source_urn=valid_casualty_urn,
            record_category=SourceRecordCategory.MILITARY,
            description="Empty plot section",
            repository_id=valid_repo_id,
            audit=valid_audit,
            servicemember_id=IndividualID("IND-000001"),
            servicemember_name_raw="Glenn Lehman",
            branch=MilitaryBranch.ARMY,
            casualty_category=CasualtyCategory.KILLED_IN_ACTION,
            casualty_year=HistoricalYear(1944),
            unit_designation_raw="Co. C",
            rank_raw="Private",
            cemetery_type=IntermentCemeteryType.NATIONAL_CEMETERY,
            cemetery_name_raw="Arlington",
            interment_year=HistoricalYear(1944),
            plot_section_raw="   ",
        )
