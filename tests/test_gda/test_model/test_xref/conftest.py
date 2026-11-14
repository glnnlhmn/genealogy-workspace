"""Path: tests/test_gda/test_model/test_xref/conftest.py

Shared pytest fixtures and contract assertion helpers for gda.model.xref tests.

Operational Role:
    Provides canonical AtomID, UUIDv4, HistoricalYear, and Fact fixtures along
    with a reusable assert_xref_contract() helper that verifies immutability,
    dynamic xref_key/sort_key invariants, total ordering, and dict/JSON
    round-trip parity across all XRef models.
"""

from __future__ import annotations

import dataclasses
from typing import Any

import pytest

from gda.core.enums.core import AssociatedRole, FactType
from gda.core.errors import ModelFormatError
from gda.model.atom.id import (
    FactID,
    FamilyID,
    IndividualID,
    LocationID,
    MediaID,
    SiteID,
    SourceID,
)
from gda.model.atom.year import BirthYear, DeathYear, HistoricalYear
from gda.model.entity.fact import Fact, FactParticipant

__version__ = "1.0.0+build.1"

SAMPLE_SOURCE_UUID_1 = "11111111-1111-4111-8111-111111111111"
SAMPLE_SOURCE_UUID_2 = "22222222-2222-4222-8222-222222222222"
SAMPLE_MEDIA_UUID_1 = "aaaa1111-1111-4111-8111-111111111111"
SAMPLE_MEDIA_UUID_2 = "bbbb2222-2222-4222-8222-222222222222"


def assert_xref_contract(xref_instance: Any, xref_cls: type[Any]) -> None:
    """Assert standard frozen dataclass, round-trip, and ordering contracts for an XRef."""
    assert dataclasses.is_dataclass(xref_cls)
    assert xref_cls.__dataclass_params__.frozen is True  # type: ignore[attr-defined]
    assert isinstance(xref_instance.xref_key, str) and "::" in xref_instance.xref_key
    assert isinstance(xref_instance.sort_key, tuple)

    payload = xref_instance.to_dict()
    assert "xref_key" not in payload
    assert xref_cls.from_dict(payload) == xref_instance
    assert xref_cls.from_json(xref_instance.to_json()) == xref_instance
    assert xref_instance.__lt__("not-an-xref") is NotImplemented

    with pytest.raises(ModelFormatError, match="must be a dictionary"):
        xref_cls.from_dict("bad")  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="Failed to parse"):
        xref_cls.from_json("{bad-json")


@pytest.fixture
def sample_fact_id() -> FactID:
    """Return canonical FactID('FID-000104')."""
    return FactID("FID-000104")


@pytest.fixture
def sample_individual_id() -> IndividualID:
    """Return canonical IndividualID('IND-000010')."""
    return IndividualID("IND-000010")


@pytest.fixture
def sample_family_id() -> FamilyID:
    """Return canonical FamilyID('FAM-000001')."""
    return FamilyID("FAM-000001")


@pytest.fixture
def sample_location_id() -> LocationID:
    """Return canonical LocationID('LOC-000001')."""
    return LocationID("LOC-000001")


@pytest.fixture
def sample_site_id() -> SiteID:
    """Return canonical SiteID('SID-000005')."""
    return SiteID("SID-000005")


@pytest.fixture
def sample_source_id() -> SourceID:
    """Return canonical SourceID UUIDv4."""
    return SourceID(SAMPLE_SOURCE_UUID_1)


@pytest.fixture
def sample_media_id() -> MediaID:
    """Return canonical MediaID UUIDv4."""
    return MediaID(SAMPLE_MEDIA_UUID_1)


@pytest.fixture
def sample_year() -> HistoricalYear:
    """Return canonical HistoricalYear(1878)."""
    return HistoricalYear(1878)


@pytest.fixture
def sample_birth_year() -> BirthYear:
    """Return canonical BirthYear(1844)."""
    return BirthYear(1844)


@pytest.fixture
def sample_death_year() -> DeathYear:
    """Return canonical DeathYear(1912)."""
    return DeathYear(1912)


@pytest.fixture
def sample_individual_fact() -> Fact:
    """Return an active individual-anchored Fact entity with secondary participants."""
    return Fact.create(
        fact_id="FID-000010",
        canonical_urn="urn:gda:fact:abbott_birth_1844",
        fact_type=FactType.BIRTH,
        title="Birth of George W. Abbott",
        primary_subject_id="IND-000001",
        date="1844-05-12",
        location_id="LOC-000001",
        site_id="SID-000002",
        participants=[
            FactParticipant.create("IND-000002", AssociatedRole.INFORMANT),
            FactParticipant.create("IND-000003", AssociatedRole.WITNESS),
        ],
    )
