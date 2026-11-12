"""Path: tests/test_gda/test_model/test_base/conftest.py

Shared root pytest fixtures for the gda.model.base test hierarchy.

Operational Role:
    Provides foundational Tier-0 atom and Batch-1 leaf value-object fixtures
    (IsoTimestamp, AuditStamp, Coordinates, TimePeriod, and canonical IDs)
    available automatically to test_zero_intra_base, test_composites, and
    test_comp_envelopes.
"""

from __future__ import annotations

import pytest

from gda.core.enums.date import DateModifier
from gda.model.atom.date import DateString, IsoTimestamp
from gda.model.atom.geo import Latitude, Longitude
from gda.model.atom.id import IndividualID, SourceID
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate, TimePeriod
from gda.model.base.geo import Coordinates

__version__ = "1.0.0+build.1"


@pytest.fixture
def golden_timestamp() -> IsoTimestamp:
    """Return canonical creation IsoTimestamp."""
    return IsoTimestamp("2026-10-16T12:00:00Z")


@pytest.fixture
def advanced_timestamp() -> IsoTimestamp:
    """Return canonical updated IsoTimestamp strictly after golden_timestamp."""
    return IsoTimestamp("2026-10-18T14:30:00Z")


@pytest.fixture
def golden_audit(golden_timestamp: IsoTimestamp) -> AuditStamp:
    """Return synchronized AuditStamp."""
    return AuditStamp(created_at=golden_timestamp, updated_at=golden_timestamp)


@pytest.fixture
def golden_guid() -> str:
    """Return canonical UUIDv4 surrogate string."""
    return "c9a646d3-9c61-4a70-8b14-c48c8b417c8d"


@pytest.fixture
def golden_source_uuid() -> str:
    """Return primary UUIDv4 string for SourceID."""
    return "00000000-0000-4000-8000-000000000001"


@pytest.fixture
def golden_source_uuid_2() -> str:
    """Return secondary UUIDv4 string for SourceID."""
    return "00000000-0000-4000-8000-000000000002"


@pytest.fixture
def golden_source_id(golden_source_uuid: str) -> SourceID:
    """Return canonical SourceID."""
    return SourceID(golden_source_uuid)


@pytest.fixture
def sample_individual_id() -> IndividualID:
    """Return canonical IndividualID."""
    return IndividualID("IND-000101")


@pytest.fixture
def sample_coordinates() -> Coordinates:
    """Return canonical WGS 84 Coordinates pair."""
    return Coordinates(latitude=Latitude(43.2081), longitude=Longitude(-71.5376))


@pytest.fixture
def golden_time_period() -> TimePeriod:
    """Return bounded historical TimePeriod (1751 to 1810)."""
    return TimePeriod(
        start_date=EventDate(date=DateString("1751"), modifier=DateModifier.EXACT),
        end_date=EventDate(date=DateString("1810"), modifier=DateModifier.EXACT),
    )


@pytest.fixture
def failure_blank_text() -> str:
    """Return whitespace-only string for negative validation checks."""
    return "   \t\n  "
