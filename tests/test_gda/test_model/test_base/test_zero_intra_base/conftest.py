"""Path: tests/test_gda/test_model/test_base/test_zero_intra_base/conftest.py

Shared pytest fixtures for Batch 1 (zero intra-base dependency) value objects.

Operational Role:
    Provides canonical IsoTimestamp, AuditStamp, IndividualID, SiteID, Latitude,
    Longitude, Coordinates, and EventDate fixtures for in-memory unit and
    regression testing across gda.model.base leaf modules.
"""

from __future__ import annotations

import pytest

from gda.core.enums.date import DateModifier
from gda.model.atom.date import DateString, IsoTimestamp
from gda.model.atom.geo import Latitude, Longitude
from gda.model.atom.id import IndividualID, SiteID
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate
from gda.model.base.geo import Coordinates

__version__ = "1.0.0+build.1"


@pytest.fixture
def ts_created() -> IsoTimestamp:
    """Return canonical creation IsoTimestamp."""
    return IsoTimestamp("2026-10-16T10:00:00Z")


@pytest.fixture
def ts_updated() -> IsoTimestamp:
    """Return canonical updated IsoTimestamp strictly after ts_created."""
    return IsoTimestamp("2026-10-16T12:00:00Z")


@pytest.fixture
def sample_audit(ts_created: IsoTimestamp) -> AuditStamp:
    """Return synchronized AuditStamp."""
    return AuditStamp(created_at=ts_created, updated_at=ts_created)


@pytest.fixture
def sample_individual_id() -> IndividualID:
    """Return canonical IndividualID."""
    return IndividualID("IND-000101")


@pytest.fixture
def sample_site_id() -> SiteID:
    """Return canonical SiteID."""
    return SiteID("SID-000888")


@pytest.fixture
def sample_coordinates() -> Coordinates:
    """Return canonical WGS 84 Coordinates pair."""
    return Coordinates(latitude=Latitude(43.2081), longitude=Longitude(-71.5376))


@pytest.fixture
def event_date_1850() -> EventDate:
    """Return exact EventDate for 1850."""
    return EventDate(date=DateString("1850"), modifier=DateModifier.EXACT)


@pytest.fixture
def event_date_1910() -> EventDate:
    """Return exact EventDate for 1910."""
    return EventDate(date=DateString("1910"), modifier=DateModifier.EXACT)
