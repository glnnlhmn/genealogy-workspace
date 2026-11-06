"""Path: tests/test_gda/test_enums/conftest.py

Shared pytest fixtures for the gda.enums verification suite.

Operational Role:
    Supplies handcrafted in-memory fixtures including comprehensive enum class
    registries, alias-aware helpers, and Pydantic validation harness models for
    testing serialization, coercion, and rejection boundaries without disk I/O.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

import pytest
from pydantic import BaseModel

import gda.enums as ge

__version__ = "0.2.0+build.1"


@pytest.fixture(scope="session")
def all_enum_classes() -> tuple[type[Enum], ...]:
    """Provide a tuple of every authoritative enumeration class exported by gda.enums."""
    classes: list[type[Enum]] = []
    for name in ge.__all__:
        attr = getattr(ge, name)
        if isinstance(attr, type) and issubclass(attr, Enum):
            classes.append(attr)
    return tuple(classes)


class SampleEnumModel(BaseModel):
    """Pydantic test fixture model containing representative enum fields from each domain."""

    # Core
    sex: ge.Sex
    quay: ge.QuayScore
    fact_type: ge.FactType

    # Sources
    record_cat: ge.SourceRecordCategory
    census_year: ge.CensusYear

    # Vital
    union_type: ge.UnionType = ge.UnionType.UNKNOWN
    manner_of_death: ge.MannerOfDeath
    name_status: ge.NameStatus = ge.NameStatus.PRIMARY

    # Site
    location_type: ge.LocationType
    site_type: ge.SiteType

    # Archival
    note_type: ge.NoteType

    # Fiscal
    taxpayer_class: ge.TaxpayerClassification

    # Optional / Nullable handling
    optional_sex: ge.Sex | None = None
    optional_quay: ge.QuayScore | None = None


@pytest.fixture(scope="session")
def pydantic_enum_model_cls() -> type[BaseModel]:
    """Provide the Pydantic validation test model class."""
    return SampleEnumModel


@pytest.fixture
def valid_enum_payload() -> dict[str, Any]:
    """Provide a raw dictionary with valid strings and integers matching SampleEnumModel."""
    return {
        "sex": "M",
        "quay": 3,
        "fact_type": "BIRTH",
        "record_cat": "VITAL",
        "census_year": 1880,
        "union_type": "MARRIED",
        "manner_of_death": "Natural",
        "name_status": "PRIMARY",
        "location_type": "COUNTY",
        "site_type": "CEMETERY",
        "note_type": "RESEARCH",
        "taxpayer_class": "Freeholder",
        "optional_sex": None,
        "optional_quay": None,
    }
