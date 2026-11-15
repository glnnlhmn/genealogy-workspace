"""Path: tests/test_gda/test_model/test_xref/conftest.py

Shared pytest fixtures and contract assertion helpers for gda.model.xref tests.

Operational Role:
    Re-exports canonical UUID constants from tests.test_gda.test_model.conftest
    and provides the assert_xref_contract() helper and sample_individual_fact
    fixture for gda.model.xref verification. Canonical AtomID and HistoricalYear
    fixtures are inherited from tests/test_gda/test_model/conftest.py.
"""

from __future__ import annotations

import dataclasses
from typing import Any

import pytest
from tests.test_gda.test_model.conftest import (
    SAMPLE_MEDIA_UUID_1,
    SAMPLE_MEDIA_UUID_2,
    SAMPLE_SOURCE_UUID_1,
    SAMPLE_SOURCE_UUID_2,
)

from gda.core.enums.core import AssociatedRole, FactType
from gda.core.errors import ModelFormatError
from gda.model.entity.fact import Fact, FactParticipant

__version__ = "1.0.0+build.2"

__all__ = [
    "SAMPLE_MEDIA_UUID_1",
    "SAMPLE_MEDIA_UUID_2",
    "SAMPLE_SOURCE_UUID_1",
    "SAMPLE_SOURCE_UUID_2",
    "assert_xref_contract",
]


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
